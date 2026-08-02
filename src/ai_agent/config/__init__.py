"""
VEXIS-CLI-3 configuration subsystem.

Public, stable entry points used by the rest of the application (CLI, core
engine adapters, tests). Everything else in this package is implementation detail.
"""
from __future__ import annotations

from .loader import (
    ConfigLoader,
    get_app_config,
    get_model_settings,
    get_provider_registry,
    get_secret_store,
    load_app_config,
)
from .models import (
    APISection,
    AppConfig,
    CostSection,
    EngineSection,
    ExecutionSection,
    GenerationParams,
    LoggingSection,
    PerformanceSection,
    ProviderName,
    ResponseFormat,
    SecuritySection,
    UserSection,
)
from .providers import AuthScheme, ProviderRegistry, ProviderSpec
from .secrets import SecretStore, redact

__all__ = [
    # loaders / accessors
    "ConfigLoader",
    "load_app_config",
    "get_app_config",
    "get_secret_store",
    "get_provider_registry",
    "get_model_settings",
    # models
    "AppConfig",
    "APISection",
    "SecuritySection",
    "LoggingSection",
    "ExecutionSection",
    "EngineSection",
    "PerformanceSection",
    "CostSection",
    "UserSection",
    "GenerationParams",
    "ProviderName",
    "ResponseFormat",
    # providers / secrets
    "ProviderRegistry",
    "ProviderSpec",
    "AuthScheme",
    "SecretStore",
    "redact",
]
