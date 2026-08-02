"""
Secure secret resolution for VEXIS-CLI-3.

Secrets are *never* required to live in config files and are *never* written to
logs. Resolution order (most specific wins):

    1. Explicit runtime value            (e.g. a CLI flag / in-process override)
    2. Environment variable            (provider-specific, see ProviderRegistry)
    3. ``.env`` file                  (loaded via python-dotenv)
    4. OS keyring (optional)         (only if the ``keyring`` package is present)

The module-level :func:`redact` helper is used by log records and the CLI so a
secret can never be leaked through ``print``/logging by accident.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception:  # pragma: no cover - python-dotenv is a declared dependency
    _HAS_DOTENV = False

from ..utils.exceptions import ConfigurationError
from .providers import ProviderRegistry

_MASK = "•" * 8


def redact(value: Optional[str]) -> str:
    """Return a safe, non-revealing representation of a secret value."""
    if not value:
        return "<unset>"
    return _MASK


class SecretStore:
    """Resolves and (safely) reports provider credentials."""

    def __init__(self, dotenv_path: Optional[str] = None) -> None:
        if _HAS_DOTENV:
            try:
                load_dotenv(dotenv_path, override=False)
            except Exception:
                # A malformed .env must not crash startup.
                pass
        self._explicit: Dict[str, Optional[str]] = {}
        self._keyring = None
        try:
            import keyring  # type: ignore
            self._keyring = keyring
        except Exception:
            self._keyring = None

    # -- mutators -------------------------------------------------------- #
    def set_explicit(self, provider: str, value: Optional[str]) -> None:
        """Register a value provided explicitly at runtime (highest precedence)."""
        self._explicit[provider.lower()] = value

    # -- accessors ------------------------------------------------------- #
    def get(self, provider: str) -> Optional[str]:
        spec = ProviderRegistry.get(provider)
        if spec is None:
            raise ConfigurationError(f"Unknown provider for secret lookup: {provider}")

        # 1. explicit runtime value
        if provider.lower() in self._explicit and self._explicit[provider.lower()]:
            return self._explicit[provider.lower()]

        # 2. environment variable(s)
        for env_var in spec.env_vars:
            val = os.getenv(env_var)
            if val:
                return val

        # 3. OS keyring (service "vexis", username = provider)
        if self._keyring is not None:
            try:
                val = self._keyring.get_password("vexis", provider.lower())
                if val:
                    return val
            except Exception:
                pass

        return None

    def has(self, provider: str) -> bool:
        try:
            return bool(self.get(provider))
        except ConfigurationError:
            return False

    def redacted(self, provider: str) -> str:
        return redact(self.get(provider))
