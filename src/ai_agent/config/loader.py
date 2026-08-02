"""
Configuration loader -- layered, validated, cached.

Precedence (highest wins):
    1. Runtime overrides (dict)            e.g. CLI flags
    2. Environment variables               ``AI_AGENT_*`` + provider keys
    3. Config file (YAML / JSON)
    4. Built-in defaults                  (in :mod:`ai_agent.config.models`)

The loader always produces a validated :class:`AppConfig` (Pydantic). Secrets
are resolved separately by :class:`SecretStore` and *injected* into the
``api.api_keys`` mapping so legacy adapters can read them -- the raw secret is
never persisted to disk through this object.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from ..utils.exceptions import ConfigurationError
from .models import AppConfig
from .providers import ProviderRegistry
from .secrets import SecretStore

_ENV_MAP = {
    "AI_AGENT_LOG_LEVEL": ("logging", "level"),
    "AI_AGENT_LOG_FILE": ("logging", "file"),
    "AI_AGENT_LOG_JSON": ("logging", "json_format"),
    "AI_AGENT_LOCAL_ENDPOINT": ("api", "local_endpoint"),
    "AI_AGENT_LOCAL_MODEL": ("api", "local_model"),
    "AI_AGENT_PREFERRED_PROVIDER": ("api", "preferred_provider"),
    "AI_AGENT_API_TIMEOUT": ("api", "timeout"),
    "AI_AGENT_API_MAX_RETRIES": ("api", "max_retries"),
    "AI_AGENT_COMMAND_TIMEOUT": ("security", "command_timeout"),
    "AI_AGENT_MAX_CONCURRENT_TASKS": ("performance", "max_concurrent_tasks"),
    "AI_AGENT_TASK_TIMEOUT": ("performance", "task_timeout"),
}

_CONFIG_FILENAME_CANDIDATES = ["config.yaml", "config.yml", "config.json"]


def _coerce(value: str, target_type: type) -> Any:
    if target_type is bool:
        return value.lower() in ("1", "true", "yes", "on")
    if target_type is int:
        return int(value)
    if target_type is float:
        return float(value)
    return value


class ConfigLoader:
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        dotenv_path: Optional[str] = None,
    ) -> None:
        self._config_path = self._resolve_path(config_path)
        self._overrides = overrides or {}
        self._secret_store = SecretStore(dotenv_path)
        self._app_config: Optional[AppConfig] = None

    @staticmethod
    def _resolve_path(config_path: Optional[Union[str, Path]]) -> Optional[Path]:
        if config_path:
            p = Path(config_path)
            if not p.exists():
                raise ConfigurationError(f"Config file not found: {config_path}")
            return p
        for cand in _CONFIG_FILENAME_CANDIDATES:
            if Path(cand).exists():
                return Path(cand)
        env_root = os.getenv("VEXIS_CONFIG_DIR")
        if env_root:
            for cand in _CONFIG_FILENAME_CANDIDATES:
                p = Path(env_root) / cand
                if p.exists():
                    return p
        return None

    def _load_file(self) -> Dict[str, Any]:
        if not self._config_path:
            return {}
        try:
            text = self._config_path.read_text(encoding="utf-8")
            suffix = self._config_path.suffix.lower()
            if suffix in (".yaml", ".yml"):
                data = yaml.safe_load(text) or {}
            elif suffix == ".json":
                data = json.loads(text) or {}
            else:
                raise ConfigurationError(
                    f"Unsupported config format: {self._config_path.suffix}"
                )
            if not isinstance(data, dict):
                raise ConfigurationError("Top-level config must be a mapping")
            return data
        except ConfigurationError:
            raise
        except Exception as e:  # pragma: no cover - defensive
            raise ConfigurationError(f"Failed to parse config file: {e}")

    def _apply_env(self, data: Dict[str, Any]) -> None:
        for env_var, (section, key) in _ENV_MAP.items():
            value = os.getenv(env_var)
            if value is None:
                continue
            section_data = data.setdefault(section, {})
            if not isinstance(section_data, dict):
                section_data = data[section] = {}
            current = section_data.get(key)
            target_type = type(current) if current is not None else str
            try:
                section_data[key] = _coerce(value, target_type)
            except ValueError:
                section_data[key] = value

    def _apply_overrides(self, data: Dict[str, Any]) -> None:
        for dotted, value in self._overrides.items():
            if value is None:
                continue
            parts = dotted.split(".")
            node: Any = data
            for part in parts[:-1]:
                if not isinstance(node.get(part), dict):
                    node[part] = {}
                node = node[part]
            node[parts[-1]] = value

    def _resolve_secrets_into(self, cfg: AppConfig) -> None:
        for spec in ProviderRegistry.all():
            if spec.auth_scheme is spec.auth_scheme.NONE:
                continue
            key = self._secret_store.get(spec.name.value)
            if key:
                cfg.api.api_keys[spec.name.value] = key

    def load(self) -> AppConfig:
        data: Dict[str, Any] = {}
        data.update(self._load_file())
        self._apply_env(data)
        self._apply_overrides(data)
        try:
            cfg = AppConfig(**data)
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
        self._resolve_secrets_into(cfg)
        self._app_config = cfg
        return cfg

    def secret_store(self) -> SecretStore:
        return self._secret_store
    def validate(self) -> AppConfig:
        """Validate the configuration; returns the config or raises."""
        return self.load()


# --------------------------------------------------------------------------- #
# Module-level convenience (process-wide singleton)                             #
# --------------------------------------------------------------------------- #

_app_config_singleton: Optional[AppConfig] = None
_loader_singleton: Optional[ConfigLoader] = None


def load_app_config(
    config_path: Optional[Union[str, Path]] = None,
    overrides: Optional[Dict[str, Any]] = None,
    force_reload: bool = False,
) -> AppConfig:
    global _app_config_singleton, _loader_singleton
    if _app_config_singleton is None or force_reload or overrides:
        _loader_singleton = ConfigLoader(config_path, overrides=overrides)
        _app_config_singleton = _loader_singleton.load()
    return _app_config_singleton


def get_app_config() -> AppConfig:
    if _app_config_singleton is None:
        return load_app_config()
    return _app_config_singleton


def get_secret_store() -> SecretStore:
    if _loader_singleton is None:
        load_app_config()
    assert _loader_singleton is not None
    return _loader_singleton.secret_store()


def get_provider_registry():
    return ProviderRegistry


def get_model_settings(config: Optional[AppConfig] = None):
    from .model_settings import ModelSettingsManager

    return ModelSettingsManager(config or get_app_config())
