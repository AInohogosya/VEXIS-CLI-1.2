"""
Pydantic-based configuration *models* for VEXIS-CLI-3.

This module is the single source of truth for *how configuration is shaped*.
It is deliberately free of I/O and framework side effects so it can be imported
anywhere (CLI, core engine, tests) without triggering file access or network.

Design goals
---------------
* Strong, declarative validation (ranges, option sets, required shapes).
* ``extra="allow"`` on section models so older/forward-compatible keys never
  crash the loader -- we fail loudly only on *wrong* values, never on
  *unknown* keys.
* Secrets are typed but never required to live in the config object; they are
  resolved at runtime by :mod:`ai_agent.config.secrets`.
"""
from __future__ import annotations

import enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProviderName(str, enum.Enum):
    """Canonical provider identifiers. ``str``-based so they serialize cleanly."""

    OLLAMA = "ollama"
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    XAI = "xai"
    META = "meta"
    MISTRAL = "mistral"
    MICROSOFT = "microsoft"
    AMAZON = "amazon"
    COHERE = "cohere"
    DEEPSEEK = "deepseek"
    GROQ = "groq"
    TOGETHER = "together"
    MINIMAX = "minimax"
    ZHIPUAI = "zhipuai"
    OPENROUTER = "openrouter"

    @classmethod
    def values(cls) -> List[str]:
        return [p.value for p in cls]


class ResponseFormat(str, enum.Enum):
    TEXT = "text"
    JSON = "json"
    STREAM = "stream"


class GenerationParams(BaseModel):
    """Validated generation / sampling hyperparameters shared across providers.

    Used both by the model-settings system (validation) and as the bridge type
    into the legacy :class:`api.base.GenerationConfig` consumed by the core.
    """

    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    stop_sequences: Optional[List[str]] = None
    seed: Optional[int] = None
    repetition_penalty: Optional[float] = Field(default=None, gt=0.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    response_format: ResponseFormat = ResponseFormat.TEXT
    system_instruction: Optional[str] = None
    timeout: int = Field(default=60, gt=0)

    def to_api_kwargs(self) -> Dict[str, object]:
        """Return only the populated (non-``None``) parameters for SDK calls."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class APISection(BaseModel):
    model_config = ConfigDict(extra="allow")

    preferred_provider: ProviderName = ProviderName.OLLAMA
    local_endpoint: str = "http://localhost:11434"
    local_model: str = "llama3.2:3b"

    # Secrets are intentionally optional here; resolved at runtime via SecretStore.
    api_keys: Dict[str, Optional[str]] = Field(default_factory=dict)
    models: Dict[str, str] = Field(default_factory=dict)

    timeout: int = Field(default=60, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0.0)

    # OpenRouter is an aggregator; tracked separately for convenience.
    openrouter_api_key: Optional[str] = None

    # Prompt compression
    compression_enabled: bool = True
    compression_threshold: int = Field(default=6000, gt=0)
    compression_target_ratio: int = Field(default=50, ge=1, le=100)
    compression_max_tokens: int = Field(default=4000, gt=0)
    compression_model: str = ""


class SecuritySection(BaseModel):
    model_config = ConfigDict(extra="allow")

    allowed_commands: List[str] = Field(
        default_factory=lambda: ["cli_command", "end", "regenerate_step"]
    )
    sanitize_text_input: bool = True
    validate_file_paths: bool = True
    max_text_length: int = Field(default=1000, gt=0)
    command_timeout: int = Field(default=600, gt=0)
    enable_command_blocking: bool = False
    enable_confirmation_prompts: bool = False
    enable_sudo_warning: bool = False
    enable_shell_pipe_warning: bool = False
    enable_sandbox: bool = True


class LoggingSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    level: str = "INFO"
    file: Optional[str] = None
    json_format: bool = False
    console: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5


class ExecutionSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    mode: str = "auto"  # "auto", "normal", or "telegram"
    safety_mode: bool = True
    dry_run: bool = False
    verify_commands: bool = True
    command_timeout: int = Field(default=600, gt=0)
    task_timeout: int = Field(default=7200, gt=0)
    max_iterations: int = Field(default=500, gt=0)
    auto_recovery: bool = True


class EngineSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    click_delay: float = 0.1
    typing_delay: float = 0.05
    scroll_duration: float = 0.5
    drag_duration: float = 0.3
    screenshot_quality: int = Field(default=95, ge=1, le=100)
    screenshot_format: str = "PNG"
    max_task_retries: int = Field(default=3, ge=0)
    max_command_retries: int = Field(default=3, ge=0)
    command_timeout: int = Field(default=600, gt=0)
    task_timeout: int = Field(default=7200, gt=0)
    max_rebuilds_per_session: int = Field(default=3, ge=0)
    max_iterations: int = Field(default=500, gt=0)


class PerformanceSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    max_concurrent_tasks: int = Field(default=1, ge=1)
    task_timeout: int = Field(default=7200, gt=0)
    command_timeout: int = Field(default=600, gt=0)
    api_timeout: int = Field(default=30, gt=0)
    memory_limit_mb: int = Field(default=1024, gt=0)


class CacheSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = True
    max_size: int = Field(default=1000, gt=0)
    ttl: int = Field(default=3600, gt=0)
    persist_to_disk: bool = True


class CostSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    daily_budget: Optional[float] = Field(default=None, ge=0.0)
    monthly_budget: Optional[float] = Field(default=None, ge=0.0)
    per_request_budget: Optional[float] = Field(default=None, ge=0.0)
    warning_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    critical_threshold: float = Field(default=0.95, ge=0.0, le=1.0)


class UserSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = ""
    preferred_style: str = "detailed"  # concise, detailed, friendly
    auto_confirm: bool = False
    show_progress: bool = True


class TelegramSection(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = False
    bot_token: str = ""
    bot_username: str = ""
    api_id: int = 0
    api_hash: str = ""
    session_name: str = ""
    contacts: List[dict] = Field(default_factory=list)
    authorized_users: List[object] = Field(default_factory=list)
    output_recipients: List[object] = Field(default_factory=list)
    enable_input_listener: bool = False
    send_phase2_end_updates: bool = False
    allowed_user_ids: List[object] = Field(default_factory=list)
    max_history_length: int = Field(default=50, gt=0)


class AppConfig(BaseModel):
    """Root application configuration -- the source of truth for the whole app."""

    model_config = ConfigDict(extra="allow", validate_assignment=False)

    api: APISection = Field(default_factory=APISection)
    security: SecuritySection = Field(default_factory=SecuritySection)
    logging: LoggingSection = Field(default_factory=LoggingSection)
    execution: ExecutionSection = Field(default_factory=ExecutionSection)
    engine: EngineSection = Field(default_factory=EngineSection)
    performance: PerformanceSection = Field(default_factory=PerformanceSection)
    cache: CacheSection = Field(default_factory=CacheSection)
    cost: CostSection = Field(default_factory=CostSection)
    user: UserSection = Field(default_factory=UserSection)
    telegram: TelegramSection = Field(default_factory=TelegramSection)

    platform: Dict[str, object] = Field(default_factory=dict)
    custom: Dict[str, object] = Field(default_factory=dict)
    custom_system_prompt: str = ""

    @property
    def preferred_provider_str(self) -> str:
        return (
            self.api.preferred_provider.value
            if isinstance(self.api.preferred_provider, ProviderName)
            else str(self.api.preferred_provider)
        )
