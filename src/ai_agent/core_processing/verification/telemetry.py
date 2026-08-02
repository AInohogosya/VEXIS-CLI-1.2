"""
Telemetry for Verification-First Execution

Logs instances where commands were successfully blocked by verification probes
to measure token and time savings.
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ...utils.logger import get_logger


@dataclass
class TelemetryEntry:
    """Single telemetry event for a verification check"""
    timestamp: float
    command: str
    blocked: bool
    probe_name: str
    reason: str
    duration_ms: float
    estimated_tokens_saved: int = 0
    estimated_time_saved_ms: float = 0


@dataclass
class TelemetryStats:
    """Aggregated telemetry statistics"""
    total_verifications: int = 0
    total_blocked: int = 0
    total_passed: int = 0
    total_errors: int = 0
    total_time_ms: float = 0
    estimated_tokens_saved: int = 0
    estimated_time_saved_ms: float = 0
    blocks_by_probe: Dict[str, int] = field(default_factory=dict)

    @property
    def block_rate(self) -> float:
        """Percentage of commands that were blocked"""
        if self.total_verifications == 0:
            return 0.0
        return (self.total_blocked / self.total_verifications) * 100

    @property
    def avg_verification_time_ms(self) -> float:
        """Average time spent on verification"""
        if self.total_verifications == 0:
            return 0.0
        return self.total_time_ms / self.total_verifications


class VerificationTelemetry:
    """
    Telemetry logger for verification events.

    Tracks:
    - Number of commands verified
    - Number of commands blocked
    - Which probes are most effective
    - Estimated token and time savings
    """

    DEFAULT_LOG_DIR = "./verification_telemetry"
    DEFAULT_MAX_ENTRIES = 10000

    def __init__(
        self,
        log_dir: Optional[str] = None,
        enabled: bool = True,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        """
        Initialize telemetry.

        Args:
            log_dir: Directory for telemetry log files
            enabled: Whether telemetry is enabled
            max_entries: Maximum number of entries to keep in memory
        """
        self.logger = get_logger("verification.telemetry")
        self.enabled = enabled
        self.log_dir = Path(log_dir or self.DEFAULT_LOG_DIR)
        self.max_entries = max_entries
        self._entries: List[TelemetryEntry] = []
        self._stats = TelemetryStats()
        self._lock = threading.Lock()

        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_verification(self, result) -> None:
        """
        Log a verification result.

        Args:
            result: VerificationResult from the executor
        """
        if not self.enabled:
            return

        with self._lock:
            self._stats.total_verifications += 1
            self._stats.total_time_ms += result.total_duration_ms

            if result.blocked and result.blocking_result:
                self._stats.total_blocked += 1
                probe_name = result.blocking_result.probe_name
                self._stats.blocks_by_probe[probe_name] = (
                    self._stats.blocks_by_probe.get(probe_name, 0) + 1
                )

                estimated_tokens = self._estimate_tokens_saved(result)
                estimated_time = self._estimate_time_saved(result)
                self._stats.estimated_tokens_saved += estimated_tokens
                self._stats.estimated_time_saved_ms += estimated_time

                entry = TelemetryEntry(
                    timestamp=time.time(),
                    command=result.command,
                    blocked=True,
                    probe_name=probe_name,
                    reason=result.blocking_result.message,
                    duration_ms=result.total_duration_ms,
                    estimated_tokens_saved=estimated_tokens,
                    estimated_time_saved_ms=estimated_time,
                )
            else:
                self._stats.total_passed += 1
                entry = TelemetryEntry(
                    timestamp=time.time(),
                    command=result.command,
                    blocked=False,
                    probe_name="",
                    reason="",
                    duration_ms=result.total_duration_ms,
                )

            self._entries.append(entry)

            if len(self._entries) > self.max_entries:
                self._entries = self._entries[-self.max_entries:]

        self._persist_entry(entry)

    def _estimate_tokens_saved(self, result) -> int:
        """
        Estimate tokens saved by blocking this command.

        Based on typical LLM response patterns for failed commands:
        - Error output: ~200-500 tokens
        - Retry attempt: ~500-1000 tokens
        - Self-correction: ~300-800 tokens
        """
        base_savings = 500

        if result.blocking_result:
            if result.blocking_result.probe_name == "file_existence":
                base_savings = 800
            elif result.blocking_result.probe_name == "syntax_check":
                base_savings = 1000
            elif result.blocking_result.probe_name == "command_parse":
                base_savings = 600

        return base_savings

    def _estimate_time_saved(self, result) -> float:
        """
        Estimate time saved in milliseconds by blocking this command.

        Based on typical command execution times:
        - File not found: ~100-500ms
        - Syntax error: ~500-2000ms
        - Parse error: ~50-200ms
        """
        base_savings = 200

        if result.blocking_result:
            if result.blocking_result.probe_name == "file_existence":
                base_savings = 300
            elif result.blocking_result.probe_name == "syntax_check":
                base_savings = 1000
            elif result.blocking_result.probe_name == "command_parse":
                base_savings = 100

        return base_savings

    def _persist_entry(self, entry: TelemetryEntry) -> None:
        """Persist a telemetry entry to disk"""
        try:
            date_str = time.strftime("%Y-%m-%d", time.localtime(entry.timestamp))
            log_file = self.log_dir / f"telemetry_{date_str}.jsonl"

            entry_dict = {
                "timestamp": entry.timestamp,
                "command": entry.command[:200],
                "blocked": entry.blocked,
                "probe_name": entry.probe_name,
                "reason": entry.reason[:200],
                "duration_ms": round(entry.duration_ms, 2),
                "estimated_tokens_saved": entry.estimated_tokens_saved,
                "estimated_time_saved_ms": round(entry.estimated_time_saved_ms, 2),
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry_dict) + "\n")

        except Exception as e:
            self.logger.error(f"Failed to persist telemetry entry: {e}")

    def get_stats(self) -> TelemetryStats:
        """Get current telemetry statistics"""
        with self._lock:
            return TelemetryStats(
                total_verifications=self._stats.total_verifications,
                total_blocked=self._stats.total_blocked,
                total_passed=self._stats.total_passed,
                total_errors=self._stats.total_errors,
                total_time_ms=self._stats.total_time_ms,
                estimated_tokens_saved=self._stats.estimated_tokens_saved,
                estimated_time_saved_ms=self._stats.estimated_time_saved_ms,
                blocks_by_probe=dict(self._stats.blocks_by_probe),
            )

    def get_recent_entries(self, count: int = 100) -> List[TelemetryEntry]:
        """Get recent telemetry entries"""
        with self._lock:
            return self._entries[-count:]

    def reset(self) -> None:
        """Reset all telemetry data"""
        with self._lock:
            self._entries.clear()
            self._stats = TelemetryStats()

    def generate_report(self) -> str:
        """Generate a human-readable telemetry report"""
        stats = self.get_stats()

        lines = [
            "=" * 60,
            "VERIFICATION TELEMETRY REPORT",
            "=" * 60,
            "",
            f"Total Verifications:    {stats.total_verifications}",
            f"Commands Blocked:       {stats.total_blocked} ({stats.block_rate:.1f}%)",
            f"Commands Passed:        {stats.total_passed}",
            f"Verification Errors:    {stats.total_errors}",
            "",
            f"Avg Verification Time:  {stats.avg_verification_time_ms:.2f}ms",
            f"Estimated Tokens Saved: {stats.estimated_tokens_saved}",
            f"Estimated Time Saved:   {stats.estimated_time_saved_ms:.0f}ms",
            "",
        ]

        if stats.blocks_by_probe:
            lines.append("Blocks by Probe:")
            for probe, count in sorted(
                stats.blocks_by_probe.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"  {probe}: {count}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
