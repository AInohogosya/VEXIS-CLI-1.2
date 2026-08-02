"""
Model settings manager -- the "model settings system".

Responsibilities
----------------
* Parse and **validate** sampling hyperparameters via :class:`GenerationParams`
  (Pydantic), so invalid values are caught early with a clear message.
* Provide **modular, data-driven** per-task-type hyperparameter presets.
* **Resolve** ``(provider, model, GenerationParams)`` from config + CLI overrides.
* Expose **capability** checks (vision / streaming) via the provider registry.
* Bridge validated params into the legacy :class:`api.base.GenerationConfig`
  consumed by the core agent's LLM clients -- the integration glue.

This module keeps the *core* agnostic: it only ever receives provider/model
strings and a ``GenerationConfig``; all validation/normalization lives here.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from ..utils.exceptions import ValidationError
from .models import AppConfig, GenerationParams, ProviderName, ResponseFormat
from .providers import ProviderRegistry


class ModelSettingsManager:
    # Per-task-type hyperparameter presets. Extend by adding an entry.
    TASK_PRESETS: Dict[str, GenerationParams] = {
        "planning": GenerationParams(temperature=0.2, top_p=0.9, max_tokens=4000),
        "action": GenerationParams(temperature=0.3, top_p=0.95, max_tokens=2000),
        "verification": GenerationParams(temperature=0.0, top_p=1.0, max_tokens=1500),
        "summarization": GenerationParams(temperature=0.4, top_p=0.9, max_tokens=2000),
        "compression": GenerationParams(temperature=0.1, top_p=0.9, max_tokens=4000),
        "default": GenerationParams(temperature=1.0, top_p=0.95, max_tokens=5000),
    }

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    # -- parsing / validation -------------------------------------------- #
    def parse_params(self, raw: Optional[Dict[str, object]]) -> GenerationParams:
        if not raw:
            return GenerationParams()
        try:
            return GenerationParams(**{k: v for k, v in raw.items() if v is not None})
        except Exception as e:  # pydantic raises ValueError / ValidationError
            raise ValidationError(f"Invalid generation parameters: {e}")

    def default_params(self, task_type: str = "default") -> GenerationParams:
        return self.TASK_PRESETS.get(task_type, self.TASK_PRESETS["default"])

    def register_preset(self, task_type: str, params: GenerationParams) -> None:
        """Allow callers to register or override a task-specific preset."""
        self.TASK_PRESETS[task_type] = params

    # -- resolution ------------------------------------------------------ #
    def resolve(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        task_type: str = "default",
    ) -> Tuple[str, str, GenerationParams]:
        api = self._config.api
        prov = provider or self._config.preferred_provider_str
        spec = ProviderRegistry.get(prov)
        if spec is None:
            raise ValidationError(f"Unknown provider: {prov}")
        resolved_model = (
            model
            or api.models.get(prov)
            or api.models.get(spec.name.value)
            or spec.default_model
            or ""
        )
        return prov, resolved_model, self.default_params(task_type)

    # -- capabilities ---------------------------------------------------- #
    def supports_vision(self, provider: str) -> bool:
        spec = ProviderRegistry.get(provider)
        return bool(spec and spec.supports_vision)

    def supports_streaming(self, provider: str) -> bool:
        spec = ProviderRegistry.get(provider)
        return bool(spec and spec.supports_streaming)

    def default_model_for(self, provider: str) -> Optional[str]:
        spec = ProviderRegistry.get(provider)
        if spec is None:
            return None
        api = self._config.api
        return api.models.get(prov := spec.name.value) or spec.default_model or None

    # -- bridge to core api.base.GenerationConfig ------------------------- #
    def to_generation_config(
        self,
        params: GenerationParams,
        system_instruction: Optional[str] = None,
        model: str = "",
        provider: str = "",
    ):
        """Convert validated params into the core's :class:`api.base.GenerationConfig`."""
        from api.base import GenerationConfig, ResponseFormat as _LegacyRF

        rf_map = {
            ResponseFormat.TEXT: _LegacyRF.TEXT,
            ResponseFormat.JSON: _LegacyRF.JSON,
            ResponseFormat.STREAM: _LegacyRF.STREAM,
        }
        return GenerationConfig(
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
            top_k=params.top_k,
            stop_sequences=params.stop_sequences,
            seed=params.seed,
            response_format=rf_map[params.response_format],
            system_instruction=system_instruction or params.system_instruction,
            timeout=params.timeout,
        )
