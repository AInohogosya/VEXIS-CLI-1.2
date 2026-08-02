"""
Backward-compatible configuration adapter for the AI Agent System.

This module is now a *thin facade* over the modern, Pydantic-based
:mod:`ai_agent.config` subsystem. It preserves the legacy public surface
(``load_config()`` returning a ``Config`` dataclass, ``ConfigManager``,
the ``*Config`` dataclasses and ``Config.get/set``) so the **core agent**,
``security.py`` and the interactive menus keep working unchanged.

The real source of truth -- validation, secrets, providers, model settings --
lives in :mod:`ai_agent.config`. No configuration I/O happens here.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .exceptions import ConfigurationError, ValidationError


def _default_ollama_model() -> str:
    """Best-effort default local model (no I/O, no import cycle)."""
    return "llama3.2:3b"


# --------------------------------------------------------------------------- #
# Legacy dataclass shapes (preserved for the core / security / menus)          #
# --------------------------------------------------------------------------- #

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: Optional[str] = None
    json_format: bool = False
    console: bool = True
    max_file_size: int = 10 * 1024 * 1024
    backup_count: int = 5


@dataclass
class APIConfig:
    local_endpoint: str = "http://localhost:11434"
    local_model: str = field(default_factory=_default_ollama_model)
    openrouter_api_key: str = ""
    api_keys: Dict[str, str] = field(default_factory=dict)
    models: Dict[str, str] = field(default_factory=dict)
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    preferred_provider: str = "ollama"
    compression_enabled: bool = True
    compression_threshold: int = 6000
    compression_target_ratio: int = 50
    compression_max_tokens: int = 4000
    compression_model: str = ""


@dataclass
class SecurityConfig:
    allowed_commands: list = field(default_factory=lambda: ["cli_command", "end", "regenerate_step"])
    sanitize_text_input: bool = True
    validate_file_paths: bool = True
    max_text_length: int = 1000
    command_timeout: int = 600
    enable_command_blocking: bool = False
    enable_confirmation_prompts: bool = False
    enable_sudo_warning: bool = False
    enable_shell_pipe_warning: bool = False
    enable_sandbox: bool = True


@dataclass
class PerformanceConfig:
    max_concurrent_tasks: int = 1
    task_timeout: int = 7200
    command_timeout: int = 600
    api_timeout: int = 30
    memory_limit_mb: int = 1024


@dataclass
class EngineConfig:
    click_delay: float = 0.1
    typing_delay: float = 0.05
    scroll_duration: float = 0.5
    drag_duration: float = 0.3
    screenshot_quality: int = 95
    screenshot_format: str = "PNG"
    max_task_retries: int = 3
    max_command_retries: int = 3
    command_timeout: int = 600
    task_timeout: int = 7200
    max_rebuilds_per_session: int = 3
    max_iterations: int = 500


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = ""
    bot_username: str = ""
    api_id: int = 0
    api_hash: str = ""
    session_name: str = ""
    contacts: list = field(default_factory=list)
    authorized_users: list = field(default_factory=list)
    output_recipients: list = field(default_factory=list)
    enable_input_listener: bool = False
    send_phase2_end_updates: bool = False
    allowed_user_ids: list = field(default_factory=list)
    max_history_length: int = 50


@dataclass
class ExecutionConfig:
    mode: str = "auto"
    safety_mode: bool = True
    dry_run: bool = False
    verify_commands: bool = True
    command_timeout: int = 600
    task_timeout: int = 7200
    max_iterations: int = 500
    auto_recovery: bool = True


@dataclass
class CacheConfig:
    enabled: bool = True
    max_size: int = 1000
    ttl: int = 3600
    persist_to_disk: bool = True


@dataclass
class CostConfig:
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    per_request_budget: Optional[float] = None
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95


@dataclass
class UserConfig:
    name: str = ""
    preferred_style: str = "detailed"
    auto_confirm: bool = False
    show_progress: bool = True


@dataclass
class Config:
    """Legacy main configuration class (adapter facade)."""
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    api: APIConfig = field(default_factory=APIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    engine: EngineConfig = field(default_factory=EngineConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    cost: CostConfig = field(default_factory=CostConfig)
    user: UserConfig = field(default_factory=UserConfig)

    platform: Dict[str, Any] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)
    custom_system_prompt: str = ""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key (navigates this object)."""
        keys = key.split('.')
        value: Any = self
        try:
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except (AttributeError, KeyError):
            return default


def app_config_to_legacy(app) -> Config:
    """Translate a validated :class:`ai_agent.config.AppConfig` into the
    legacy :class:`Config` dataclass consumed by the core."""
    api = app.api
    return Config(
        logging=LoggingConfig(
            level=app.logging.level, file=app.logging.file,
            json_format=app.logging.json_format, console=app.logging.console,
            max_file_size=app.logging.max_file_size, backup_count=app.logging.backup_count,
        ),
        api=APIConfig(
            local_endpoint=api.local_endpoint,
            local_model=api.local_model,
            openrouter_api_key=api.openrouter_api_key or "",
            api_keys=dict(api.api_keys),
            models=dict(api.models),
            timeout=api.timeout, max_retries=api.max_retries, retry_delay=api.retry_delay,
            preferred_provider=app.preferred_provider_str,
            compression_enabled=api.compression_enabled,
            compression_threshold=api.compression_threshold,
            compression_target_ratio=api.compression_target_ratio,
            compression_max_tokens=api.compression_max_tokens,
            compression_model=api.compression_model,
        ),
        security=SecurityConfig(
            allowed_commands=list(api_security_allowed(app)),
            sanitize_text_input=app.security.sanitize_text_input,
            validate_file_paths=app.security.validate_file_paths,
            max_text_length=app.security.max_text_length,
            command_timeout=app.security.command_timeout,
            enable_command_blocking=app.security.enable_command_blocking,
            enable_confirmation_prompts=app.security.enable_confirmation_prompts,
            enable_sudo_warning=app.security.enable_sudo_warning,
            enable_shell_pipe_warning=app.security.enable_shell_pipe_warning,
            enable_sandbox=app.security.enable_sandbox,
        ),
        performance=PerformanceConfig(
            max_concurrent_tasks=app.performance.max_concurrent_tasks,
            task_timeout=app.performance.task_timeout,
            command_timeout=app.performance.command_timeout,
            api_timeout=app.performance.api_timeout,
            memory_limit_mb=app.performance.memory_limit_mb,
        ),
        engine=EngineConfig(
            click_delay=app.engine.click_delay, typing_delay=app.engine.typing_delay,
            scroll_duration=app.engine.scroll_duration, drag_duration=app.engine.drag_duration,
            screenshot_quality=app.engine.screenshot_quality,
            screenshot_format=app.engine.screenshot_format,
            max_task_retries=app.engine.max_task_retries,
            max_command_retries=app.engine.max_command_retries,
            command_timeout=app.engine.command_timeout, task_timeout=app.engine.task_timeout,
            max_rebuilds_per_session=app.engine.max_rebuilds_per_session,
            max_iterations=app.engine.max_iterations,
        ),
        telegram=TelegramConfig(
            enabled=app.telegram.enabled, bot_token=app.telegram.bot_token,
            bot_username=app.telegram.bot_username, api_id=app.telegram.api_id,
            api_hash=app.telegram.api_hash, session_name=app.telegram.session_name,
            contacts=list(app.telegram.contacts),
            authorized_users=list(app.telegram.authorized_users),
            output_recipients=list(app.telegram.output_recipients),
            enable_input_listener=app.telegram.enable_input_listener,
            send_phase2_end_updates=app.telegram.send_phase2_end_updates,
            allowed_user_ids=list(app.telegram.allowed_user_ids),
            max_history_length=app.telegram.max_history_length,
        ),
        execution=ExecutionConfig(
            mode=app.execution.mode, safety_mode=app.execution.safety_mode,
            dry_run=app.execution.dry_run, verify_commands=app.execution.verify_commands,
            command_timeout=app.execution.command_timeout,
            task_timeout=app.execution.task_timeout,
            max_iterations=app.execution.max_iterations,
            auto_recovery=app.execution.auto_recovery,
        ),
        cache=CacheConfig(
            enabled=app.cache.enabled, max_size=app.cache.max_size,
            ttl=app.cache.ttl, persist_to_disk=app.cache.persist_to_disk,
        ),
        cost=CostConfig(
            daily_budget=app.cost.daily_budget, monthly_budget=app.cost.monthly_budget,
            per_request_budget=app.cost.per_request_budget,
            warning_threshold=app.cost.warning_threshold,
            critical_threshold=app.cost.critical_threshold,
        ),
        user=UserConfig(
            name=app.user.name, preferred_style=app.user.preferred_style,
            auto_confirm=app.user.auto_confirm, show_progress=app.user.show_progress,
        ),
        platform=dict(app.platform), custom=dict(app.custom),
        custom_system_prompt=app.custom_system_prompt,
    )


def api_security_allowed(app) -> list:
    vals = app.security.allowed_commands
    return list(vals) if isinstance(vals, (list, tuple)) else []
class ConfigManager:
    """Backward-compatible config manager (facade over :mod:`ai_agent.config`)."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else None
        self._config: Optional[Config] = None

    def load_config(self) -> Config:
        """Load (and cache) the configuration as the legacy ``Config`` object."""
        if self._config is None:
            # Lazy import avoids a circular import with ``ai_agent.config``.
            from ..config.loader import load_app_config

            app = load_app_config(
                self.config_path, force_reload=bool(self.config_path)
            )
            self._config = app_config_to_legacy(app)
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        if not self._config:
            self.load_config()
        assert self._config is not None
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if not self._config:
            self.load_config()
        assert self._config is not None
        self._config.set(key, value) if hasattr(self._config, "set") else None
        keys = key.split(".")
        config_obj: Any = self._config
        for k in keys[:-1]:
            if hasattr(config_obj, k):
                config_obj = getattr(config_obj, k)
            elif isinstance(config_obj, dict):
                if k not in config_obj:
                    config_obj[k] = {}
                config_obj = config_obj[k]
        final_key = keys[-1]
        if hasattr(config_obj, final_key):
            setattr(config_obj, final_key, value)
        elif isinstance(config_obj, dict):
            config_obj[final_key] = value

    def save_config(self, config_path: Optional[Union[str, Path]] = None):
        """Settings are not persisted (security: secrets never written to disk)."""
        pass  # No-op

    def _validate_config(self):
        """Validation now happens in Pydantic inside :mod:`ai_agent.config`."""
        pass


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def load_config(
    config_path: Optional[Union[str, Path]] = None, force_reload: bool = False
) -> Config:
    """Load configuration (singleton pattern).

    Delegates to the modern, validated loader and returns the legacy ``Config``
    so existing callers (core, security, menus) are unaffected.
    """
    global _config_manager
    if _config_manager is None or force_reload:
        _config_manager = ConfigManager(config_path)
    return _config_manager.load_config()


def get_config_manager() -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def save_config(config_path: Optional[Union[str, Path]] = None):
    """Save configuration is disabled - settings are not persisted."""
    pass  # No-op - configuration is not saved to file

