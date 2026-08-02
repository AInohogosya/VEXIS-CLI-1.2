"""
VEXIS-CLI-3 - Next-Generation AI Agent System for Terminal Automation

Version Note: VEXIS-CLI-3 uses semantic versioning (3.0.0)
with the Next-Gen 8-Phase Architecture:
Phase 0: Critic & Optimizer -> Phase 1: Initial Planning -> Phase 2: Action Generation ->
Phase 3: Execution -> Phase 4: Dynamic Update & Progress Reporting -> Phase 5: Verification ->
Phase 6: Summarization -> Phase 7: Bot User Review

Key enhancements:
- Predictive Subgoal Graph (PSG) replacing linear step lists
- Critic & Optimizer pre-phase for lower-risk plans
- Multi-Layer Repository Index (symbols, test deps, doc-to-code)
- Tool Policy Engine with safety/determinism/cost scoring
- Provenance metadata on all writes and commands
- Confidence-gated execution with automatic dry-runs
- Delta-aware index refresh after writes
- Verification-First Execution with lightweight probes
- Self-tuning command macros with guardrails
"""

__version__ = "3.0.0"
__author__ = "AInohogosya"
__email__ = "AInohogosya@proton.me"
__description__ = "VEXIS-CLI-3 - Next-Gen AI-powered terminal automation system"

from .core_processing.five_phase_engine import FivePhaseEngine, PipelinePhase, PipelineContext
from .platform_abstraction.platform_detector import PlatformDetector
from .external_integration.vision_api_client import VisionAPIClient
from .external_integration.model_runner import ModelRunner, TaskType

__all__ = [
    "FivePhaseEngine",
    "PipelinePhase",
    "PipelineContext",
    "PlatformDetector",
    "VisionAPIClient",
    "ModelRunner",
    "TaskType",
]