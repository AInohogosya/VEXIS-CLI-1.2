"""
Settings manager adapter for VEXIS-CLI-3.

Thin facade over the modern configuration subsystem
(:mod:`ai_agent.config`). It preserves the legacy
``SettingsManager`` / ``APISettings`` / ``get_settings_manager()`` surface so the
core (multi-provider clients, ollama selector) keeps working unchanged.

All secrets resolve at runtime via :class:`ai_agent.config.secrets.SecretStore`
(env -> ``.env`` -> keyring); nothing is persisted to disk.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..config import (
    ProviderName,
    get_app_config,
    get_model_settings,
    get_provider_registry,
    get_secret_store,
)
from .logger import get_logger


@dataclass
class APISettings:
    """Legacy snapshot of API keys + per-provider model selection."""
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None
    meta_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    microsoft_api_key: Optional[str] = None
    amazon_access_key: Optional[str] = None
    amazon_secret_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    together_api_key: Optional[str] = None
    minimax_api_key: Optional[str] = None
    zhipuai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    preferred_provider: str = "ollama"
    google_model: str = "gemini-3.1-pro-preview"
    groq_model: str = "llama-3.3-70b-versatile"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-3.5-sonnet-20241022"
    xai_model: str = "grok-2"
    meta_model: str = "llama-3.1-70b-instruct"
    mistral_model: str = "mistral-large-latest"
    microsoft_model: str = "gpt-4o"
    amazon_model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    cohere_model: str = "command-r-plus"
    deepseek_model: str = "deepseek-chat"
    together_model: str = "meta-llama/Llama-3.1-70B-Instruct-Turbo"
    minimax_model: str = "minimax-text-01"
    zhipuai_model: str = "glm-4"
    openrouter_model: str = "openai/gpt-oss-120b"
    ollama_model: str = "llama3.2:3b"


class SettingsManager:
    """Manages application settings and API keys (facade over ai_agent.config)."""

    def __init__(self):
        self.logger = get_logger("settings_manager")
        self._app = get_app_config()
        self._secrets = get_secret_store()
        self._registry = get_provider_registry()
        self._model_settings = get_model_settings(self._app)

    # -- low-level helpers --------------------------------------------- #
    def _resolve_provider(self, provider: str) -> str:
        try:
            return self._registry.resolve(provider).value
        except KeyError:
            return provider.lower()

    def get_api_key(self, provider: str) -> Optional[str]:
        return self._secrets.get(provider)

    def set_api_key(self, provider: str, api_key: Optional[str]) -> None:
        self._secrets.set_explicit(provider, api_key)
        if provider == "openrouter":
            self._app.api.openrouter_api_key = api_key or ""

    def get_model(self, provider: str) -> str:
        return self._model_settings.default_model_for(provider) or ""

    def set_model(self, provider: str, model: str) -> None:
        self._app.api.models[provider] = model

    def get_preferred_provider(self) -> str:
        return self._app.preferred_provider_str

    def set_preferred_provider(self, provider: str) -> None:
        self._app.api.preferred_provider = ProviderName(self._resolve_provider(provider))

    # -- ollama ------------------------------------------------------- #
    def get_ollama_model(self) -> str:
        return self._app.api.local_model or "llama3.2:3b"

    def set_ollama_model(self, model: str) -> None:
        self._app.api.local_model = model
        self.logger.info(f"Ollama model set to: {model}")

    # -- snapshot ----------------------------------------------------- #
    def get_settings(self) -> APISettings:
        return APISettings(
            google_api_key=self.get_api_key("google"),
            groq_api_key=self.get_api_key("groq"),
            openai_api_key=self.get_api_key("openai"),
            anthropic_api_key=self.get_api_key("anthropic"),
            xai_api_key=self.get_api_key("xai"),
            meta_api_key=self.get_api_key("meta"),
            mistral_api_key=self.get_api_key("mistral"),
            microsoft_api_key=self.get_api_key("microsoft"),
            amazon_access_key=self.get_api_key("amazon"),
            amazon_secret_key=self.get_api_key("amazon"),
            cohere_api_key=self.get_api_key("cohere"),
            deepseek_api_key=self.get_api_key("deepseek"),
            together_api_key=self.get_api_key("together"),
            minimax_api_key=self.get_api_key("minimax"),
            zhipuai_api_key=self.get_api_key("zhipuai"),
            openrouter_api_key=self.get_api_key("openrouter"),
            preferred_provider=self.get_preferred_provider(),
            google_model=self.get_model("google"),
            groq_model=self.get_model("groq"),
            openai_model=self.get_model("openai"),
            anthropic_model=self.get_model("anthropic"),
            xai_model=self.get_model("xai"),
            meta_model=self.get_model("meta"),
            mistral_model=self.get_model("mistral"),
            microsoft_model=self.get_model("microsoft"),
            amazon_model=self.get_model("amazon"),
            cohere_model=self.get_model("cohere"),
            deepseek_model=self.get_model("deepseek"),
            together_model=self.get_model("together"),
            minimax_model=self.get_model("minimax"),
            zhipuai_model=self.get_model("zhipuai"),
            openrouter_model=self.get_model("openrouter"),
            ollama_model=self.get_ollama_model(),
        )

    def get_available_providers(self) -> List[str]:
        return self._registry.names()


# --------------------------------------------------------------------------- #
# Generate the legacy per-provider accessor methods (DRY).                     #
# The core expects e.g. ``get_google_api_key()``, ``set_groq_model(m)``.     #
# --------------------------------------------------------------------------- #

def _make_get_key(provider: str):
    def _get(self) -> Optional[str]:
        return self.get_api_key(provider)
    _get.__name__ = f"get_{provider}_api_key"
    return _get


def _make_set_key(provider: str):
    def _set(self, api_key: Optional[str]) -> None:
        self.set_api_key(provider, api_key)
        self.logger.info(f"{provider.title()} API key updated")
    _set.__name__ = f"set_{provider}_api_key"
    return _set


def _make_get_model(provider: str):
    def _get(self) -> str:
        return self.get_model(provider)
    _get.__name__ = f"get_{provider}_model"
    return _get


def _make_set_model(provider: str):
    def _set(self, model: str) -> None:
        self.set_model(provider, model)
        self.logger.info(f"{provider.title()} model set to: {model}")
    _set.__name__ = f"set_{provider}_model"
    return _set


for _p in (
    "google", "groq", "openai", "anthropic", "xai", "meta", "mistral",
    "microsoft", "amazon", "cohere", "deepseek", "together", "minimax",
    "zhipuai", "openrouter",
):
    setattr(SettingsManager, f"get_{_p}_api_key", _make_get_key(_p))
    setattr(SettingsManager, f"set_{_p}_api_key", _make_set_key(_p))
    setattr(SettingsManager, f"get_{_p}_model", _make_get_model(_p))
    setattr(SettingsManager, f"set_{_p}_model", _make_set_model(_p))


def _get_amazon_access_key(self) -> Optional[str]:
    return self.get_api_key("amazon")


SettingsManager.get_amazon_access_key = _get_amazon_access_key


# Global settings manager instance
_settings_manager = None


def get_settings_manager():
    """Get global settings manager instance (singleton)."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
