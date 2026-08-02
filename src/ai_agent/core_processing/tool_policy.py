"""
Tool Policy Engine

Scores tools based on:
- Safety: How destructive or risky the tool is
- Determinism: Whether the tool produces reproducible results
- Cost: Computational or monetary cost of the tool
- Expected info gain: How much useful information the tool returns

Provides policy-based tool selection, self-tuning command macros,
and verification-first execution support.
"""

from __future__ import annotations

import enum
import os
import re
import time
import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from ..utils.logger import get_logger

logger = get_logger("tool_policy")


class ToolSafety(enum.Enum):
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    DESTRUCTIVE = "destructive"


class ToolDeterminism(enum.Enum):
    DETERMINISTIC = "deterministic"
    MOSTLY_DETERMINISTIC = "mostly_deterministic"
    NON_DETERMINISTIC = "non_deterministic"


class ToolCost(enum.Enum):
    FREE = "free"
    CHEAP = "cheap"
    MODERATE = "moderate"
    EXPENSIVE = "expensive"


@dataclass
class ToolScore:
    safety: float = 1.0  # 0.0 (destructive) to 1.0 (safe)
    determinism: float = 1.0  # 0.0 to 1.0
    cost: float = 1.0  # 0.0 (expensive) to 1.0 (free)
    info_gain: float = 0.5  # 0.0 to 1.0
    composite: float = 0.0

    def compute_composite(self) -> float:
        weights = {"safety": 0.35, "determinism": 0.15, "cost": 0.20, "info_gain": 0.30}
        self.composite = (
            self.safety * weights["safety"]
            + self.determinism * weights["determinism"]
            + self.cost * weights["cost"]
            + self.info_gain * weights["info_gain"]
        )
        return self.composite


@dataclass
class ToolMacro:
    name: str
    commands: List[str]
    guardrails: List[str] = field(default_factory=list)
    description: str = ""
    risk_level: ToolSafety = ToolSafety.LOW_RISK
    use_count: int = 0
    last_used: float = 0.0


@dataclass
class ProbeCommand:
    command: str
    probe_type: str  # "existence", "schema", "readiness", "syntax"
    expected_success: bool = True
    timeout_ms: int = 1000


TOOL_SCORES: Dict[str, ToolScore] = {
    "read_file": ToolScore(safety=1.0, determinism=1.0, cost=1.0, info_gain=0.9),
    "run_command:read": ToolScore(safety=0.9, determinism=0.9, cost=0.8, info_gain=0.7),
    "run_command:list": ToolScore(safety=0.9, determinism=0.9, cost=0.8, info_gain=0.5),
    "run_command:build": ToolScore(safety=0.6, determinism=0.7, cost=0.3, info_gain=0.8),
    "run_command:test": ToolScore(safety=0.7, determinism=0.8, cost=0.3, info_gain=0.9),
    "run_command:write": ToolScore(safety=0.3, determinism=0.6, cost=0.6, info_gain=0.4),
    "run_command:delete": ToolScore(safety=0.1, determinism=0.9, cost=0.7, info_gain=0.2),
    "write_file": ToolScore(safety=0.4, determinism=1.0, cost=0.7, info_gain=0.6),
    "str_replace": ToolScore(safety=0.5, determinism=0.9, cost=0.7, info_gain=0.7),
    "keep_text": ToolScore(safety=1.0, determinism=1.0, cost=1.0, info_gain=0.1),
    "keep_file": ToolScore(safety=1.0, determinism=1.0, cost=1.0, info_gain=0.2),
    "search": ToolScore(safety=1.0, determinism=1.0, cost=1.0, info_gain=0.9),
    "list_files": ToolScore(safety=1.0, determinism=1.0, cost=1.0, info_gain=0.6),
    "ask_user": ToolScore(safety=1.0, determinism=0.3, cost=0.1, info_gain=0.8),
    "answer_directly": ToolScore(safety=1.0, determinism=0.5, cost=0.1, info_gain=0.5),
    "hack": ToolScore(safety=0.2, determinism=0.5, cost=0.5, info_gain=0.6),
}

COMMAND_CATEGORY_PATTERNS: List[Tuple[str, str]] = [
    (r"^\s*(cat|head|tail|less|more|wc|grep|find|ls|echo|pwd|which|whoami|date|env)\b", "run_command:read"),
    (r"^\s*(ls|dir|find)\b", "run_command:list"),
    (r"^\s*(make|npm run|npm build|npx (build|vite));?.*", "run_command:build"),
    (r"^\s*(pytest|jest|vitest|mocha|npm test|npx (jest|vitest|mocha)|go test|cargo test)\b", "run_command:test"),
    (r"^\s*(rm|rmdir|del|rd)\b", "run_command:delete"),
    (r"^\s*(touch|mkdir|echo.*>|cp|mv|chmod|chown|install|write)\b", "run_command:write"),
    (r"^\s*(curl|wget|ping|nc|ssh|telnet)\b", "run_command:read"),
]


class ToolPolicyEngine:
    """
    Evaluates tool policies and scores tools for the agent.
    """

    def __init__(self):
        self._macros: Dict[str, ToolMacro] = {}
        self._usage_stats: Dict[str, int] = {}
        self._probe_cache: Dict[str, ProbeResult] = {}

    def score_command(self, command: str) -> ToolScore:
        category = self._categorize_command(command)
        score = self._lookup_score(category)
        score.compute_composite()
        return score

    def score_tool(self, tool_name: str, context: Optional[Dict[str, Any]] = None) -> ToolScore:
        base = TOOL_SCORES.get(tool_name, ToolScore())
        if context:
            base = self._apply_context_modifiers(base, context)
        base.compute_composite()
        return base

    def get_safe_alternatives(self, command: str) -> List[str]:
        score = self.score_command(command)
        if score.composite >= 0.5:
            return []

        alternatives: List[str] = []

        if re.match(r"^\s*(rm|rmdir|del)\b", command):
            alt = re.sub(r"^(rm|rmdir|del)\s+(-rf?\s+)?(.+)", r"ls -la \3", command)
            if alt != command:
                alternatives.append(alt)

        if re.match(r"^\s*(mv|cp)\s", command):
            alt = re.sub(r"^(mv|cp)\s", r"cp -n ", command)
            if alt != command:
                alternatives.append(alt)

        return alternatives

    def suggest_lightweight_probe(self, command: str) -> Optional[ProbeCommand]:
        stripped = command.strip()
        if re.match(r"^\s*(cat|head|tail|ls|echo|pwd|which)\b", stripped):
            return ProbeCommand(
                command=f"echo '[probe] lightweight check passed'",
                probe_type="readiness",
            )
        file_refs = re.findall(r'[\w./\\]+\.(\w+)', stripped)
        for ref in file_refs:
            ext = ref.lower()
            if ext in ("py", "js", "ts", "json", "yaml", "yml", "sh"):
                return ProbeCommand(
                    command=f"test -f {ref}" if "/" in ref or "\\" in ref else f"echo '[probe] file check'",
                    probe_type="existence",
                )
        return None

    def register_macro(self, macro: ToolMacro) -> None:
        self._macros[macro.name] = macro

    def get_macro(self, name: str) -> Optional[ToolMacro]:
        return self._macros.get(name)

    def record_usage(self, macro_name: str) -> None:
        macro = self._macros.get(macro_name)
        if macro:
            macro.use_count += 1
            macro.last_used = time.time()
        self._usage_stats[macro_name] = self._usage_stats.get(macro_name, 0) + 1

    def get_usage_stats(self) -> Dict[str, int]:
        return dict(self._usage_stats)

    def _categorize_command(self, command: str) -> str:
        for pattern, category in COMMAND_CATEGORY_PATTERNS:
            if re.match(pattern, command.strip()):
                return category

        for known_tool in ["read_file", "write_file", "str_replace", "keep_text", "keep_file", "hack", "search", "list_files"]:
            if command.strip().startswith(known_tool):
                return known_tool

        return "run_command:read"

    def _lookup_score(self, category: str) -> ToolScore:
        score = TOOL_SCORES.get(category)
        if score:
            return ToolScore(**{k: getattr(score, k) for k in ToolScore.__dataclass_fields__ if k != "composite"})
        return ToolScore()

    def _apply_context_modifiers(self, base: ToolScore, context: Dict[str, Any]) -> ToolScore:
        score = ToolScore(**{k: getattr(base, k) for k in ToolScore.__dataclass_fields__ if k != "composite"})

        if context.get("dry_run"):
            score.safety = min(1.0, score.safety + 0.2)

        if context.get("has_verification"):
            score.safety = min(1.0, score.safety + 0.15)

        target_dir = context.get("target_dir", "")
        if target_dir and "/etc" in target_dir:
            score.safety = max(0.0, score.safety - 0.3)

        return score


@dataclass
class ProbeResult:
    passed: bool
    duration_ms: float
    detail: str = ""


def run_probe_command(command: str, probe: ProbeCommand) -> ProbeResult:
    """Run a lightweight probe before executing an expensive action."""
    import subprocess

    start = time.monotonic()
    try:
        result = subprocess.run(
            probe.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=probe.timeout_ms / 1000,
        )
        elapsed = (time.monotonic() - start) * 1000
        passed = (result.returncode == 0) == probe.expected_success
        return ProbeResult(
            passed=passed,
            duration_ms=elapsed,
            detail=f"exit={result.returncode}: {result.stdout.strip()[:100]}",
        )
    except subprocess.TimeoutExpired:
        elapsed = (time.monotonic() - start) * 1000
        return ProbeResult(passed=False, duration_ms=elapsed, detail="timeout")
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        return ProbeResult(passed=False, duration_ms=elapsed, detail=str(e))


def get_default_policy_engine() -> ToolPolicyEngine:
    """Get a pre-configured policy engine with built-in macros."""
    engine = ToolPolicyEngine()

    engine.register_macro(ToolMacro(
        name="read_and_understand",
        commands=["read_file({path})"],
        guardrails=["path must be absolute", "path must exist"],
        description="Read a file to understand its contents before editing",
        risk_level=ToolSafety.SAFE,
    ))

    engine.register_macro(ToolMacro(
        name="safe_file_edit",
        commands=["read_file({path})", "<str_replace>...</str_replace>"],
        guardrails=["always read before edit", "use str_replace over write_file"],
        description="Edit a file safely by reading first then applying targeted edits",
        risk_level=ToolSafety.LOW_RISK,
    ))

    engine.register_macro(ToolMacro(
        name="run_tests",
        commands=["cd {project_dir} && {test_command}"],
        guardrails=["verify project_dir exists", "check test file exists first"],
        description="Run project tests with pre-flight checks",
        risk_level=ToolSafety.LOW_RISK,
    ))

    return engine