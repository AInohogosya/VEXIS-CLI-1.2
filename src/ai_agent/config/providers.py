"""
Provider registry -- the extensibility backbone for multi-provider support.

This is the SoC boundary between the *core agent* (which only needs a provider
name + model string) and the *provider plumbing* (auth, SDKs, defaults).

Adding a new provider is a single ``ProviderRegistry.register(...)`` call; no other
code (core, CLI, loaders) needs to change. The registry is the single place
that knows each provider's auth scheme, env-var name, default model and
capabilities, which keeps :mod:`ai_agent.config.secrets` and the model-settings
system DRY and consistent.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .models import ProviderName


class AuthScheme(str, enum.Enum):
    NONE = "none"        # local / no auth (e.g. Ollama)
    API_KEY = "api_key"  # single bearer / api key
    AWS = "aws"          # access key + secret (+ optional session token)


@dataclass
class ProviderSpec:
    """Immutable description of a single provider."""

    name: ProviderName
    display_name: str
    auth_scheme: AuthScheme = AuthScheme.API_KEY
    env_vars: List[str] = field(default_factory=list)   # candidate env var names
    aliases: List[str] = field(default_factory=list)    # e.g. "gemini" -> google
    default_model: str = ""
    sdk_required: bool = False        # True if an extra SDK package is needed
    default_base_url: Optional[str] = None
    supports_streaming: bool = True
    supports_vision: bool = False
    description: str = ""


class ProviderRegistry:
    """Process-wide registry of :class:`ProviderSpec` objects."""

    _providers: Dict[str, ProviderSpec] = {}
    _aliases: Dict[str, ProviderName] = {}

    # -- registration ------------------------------------------------------ #
    @classmethod
    def register(cls, spec: ProviderSpec) -> None:
        cls._providers[spec.name.value] = spec
        for alias in spec.aliases:
            cls._aliases[alias.lower()] = spec.name

    # -- lookup ----------------------------------------------------------- #
    @classmethod
    def get(cls, name_or_alias: str) -> Optional[ProviderSpec]:
        key = (name_or_alias or "").lower()
        if key in cls._providers:
            return cls._providers[key]
        canonical = cls._aliases.get(key)
        if canonical is not None:
            return cls._providers.get(canonical.value)
        return None

    @classmethod
    def resolve(cls, name_or_alias: str) -> ProviderName:
        spec = cls.get(name_or_alias)
        if spec is None:
            raise KeyError(f"Unknown provider: {name_or_alias}")
        return spec.name

    @classmethod
    def all(cls) -> List[ProviderSpec]:
        return list(cls._providers.values())

    @classmethod
    def names(cls) -> List[str]:
        return list(cls._providers.keys())

    @classmethod
    def env_var_for(cls, name_or_alias: str) -> Optional[str]:
        spec = cls.get(name_or_alias)
        return spec.env_vars[0] if spec and spec.env_vars else None


def _register_defaults() -> None:
    """Idempotently seed the registry with the built-in providers."""
    if ProviderRegistry.names():
        return

    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.OLLAMA, display_name="Ollama (local)",
        auth_scheme=AuthScheme.NONE, aliases=["local"],
        default_model="llama3.2:3b", supports_vision=True,
        description="Local, open-weight models served by Ollama.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.GOOGLE, display_name="Google Gemini",
        auth_scheme=AuthScheme.API_KEY, env_vars=["GOOGLE_API_KEY"],
        aliases=["gemini"], default_model="gemini-3.1-pro-preview",
        supports_vision=True, description="Google's Gemini family of models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.OPENAI, display_name="OpenAI",
        auth_scheme=AuthScheme.API_KEY, env_vars=["OPENAI_API_KEY"],
        aliases=["gpt"], default_model="gpt-4o", supports_vision=True,
        description="OpenAI GPT models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.ANTHROPIC, display_name="Anthropic Claude",
        auth_scheme=AuthScheme.API_KEY, env_vars=["ANTHROPIC_API_KEY"],
        aliases=["claude"], default_model="claude-3.5-sonnet-20241022",
        description="Anthropic Claude models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.XAI, display_name="xAI Grok",
        auth_scheme=AuthScheme.API_KEY, env_vars=["XAI_API_KEY"],
        aliases=["grok"], default_model="grok-2",
        description="xAI Grok models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.META, display_name="Meta Llama",
        auth_scheme=AuthScheme.API_KEY, env_vars=["META_API_KEY"],
        aliases=["llama"], default_model="llama-3.1-70b-instruct",
        description="Meta's Llama family models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.MISTRAL, display_name="Mistral AI",
        auth_scheme=AuthScheme.API_KEY, env_vars=["MISTRAL_API_KEY"],
        aliases=["mistral"], default_model="mistral-large-latest",
        description="Mistral AI models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.MICROSOFT, display_name="Microsoft Azure OpenAI",
        auth_scheme=AuthScheme.API_KEY, env_vars=["AZURE_API_KEY"],
        aliases=["azure"], default_model="gpt-4o",
        description="Azure-hosted OpenAI models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.AMAZON, display_name="AWS Bedrock",
        auth_scheme=AuthScheme.AWS,
        env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        aliases=["aws", "bedrock"],
        default_model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        description="Amazon Bedrock hosted models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.COHERE, display_name="Cohere",
        auth_scheme=AuthScheme.API_KEY, env_vars=["COHERE_API_KEY"],
        aliases=["cohere"], default_model="command-r-plus",
        description="Cohere Command models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.DEEPSEEK, display_name="DeepSeek",
        auth_scheme=AuthScheme.API_KEY, env_vars=["DEEPSEEK_API_KEY"],
        aliases=["deepseek"], default_model="deepseek-chat",
        description="DeepSeek models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.GROQ, display_name="Groq",
        auth_scheme=AuthScheme.API_KEY, env_vars=["GROQ_API_KEY"],
        aliases=["groq"], default_model="llama-3.3-70b-versatile",
        description="Groq high-speed inference.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.TOGETHER, display_name="Together AI",
        auth_scheme=AuthScheme.API_KEY, env_vars=["TOGETHER_API_KEY"],
        aliases=["together"],
        default_model="meta-llama/Llama-3.1-70B-Instruct-Turbo",
        description="Together AI hosted open models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.MINIMAX, display_name="MiniMax",
        auth_scheme=AuthScheme.API_KEY, env_vars=["MINIMAX_API_KEY"],
        aliases=["minimax"], default_model="minimax-text-01",
        description="MiniMax text models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.ZHIPUAI, display_name="Zhipu AI GLM",
        auth_scheme=AuthScheme.API_KEY, env_vars=["ZHIPUAI_API_KEY"],
        aliases=["zhipu", "glm"], default_model="glm-4",
        description="Zhipu AI GLM models.",
    ))
    ProviderRegistry.register(ProviderSpec(
        name=ProviderName.OPENROUTER, display_name="OpenRouter",
        auth_scheme=AuthScheme.API_KEY, env_vars=["OPENROUTER_API_KEY"],
        aliases=["open-router"], default_model="openai/gpt-oss-120b",
        supports_vision=True, description="Unified gateway to many models.",
    ))


_register_defaults()
