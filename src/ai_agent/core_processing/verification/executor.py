"""
Verification Executor for Pre-Flight Command Validation

Orchestrates the execution of verification probes before command execution.
Implements the short-circuit mechanism to block expensive commands when
probes fail.
"""

import time
from typing import Dict, List, Optional

from ...utils.logger import get_logger
from .probes import ProbeResult, ProbeStatus, VerificationResult
from .registry import ProbeRegistry
from .telemetry import VerificationTelemetry


class VerificationExecutor:
    """
    Executes verification probes before command execution.

    This is the main entry point for the verification layer. It:
    1. Looks up applicable probes for a command
    2. Executes them in sequence
    3. Short-circuits on first failure
    4. Logs telemetry data
    """

    def __init__(
        self,
        registry: Optional[ProbeRegistry] = None,
        telemetry: Optional[VerificationTelemetry] = None,
        enabled: bool = True,
    ):
        """
        Initialize the verification executor.

        Args:
            registry: Probe registry to use (defaults to global singleton)
            telemetry: Telemetry logger (defaults to new instance)
            enabled: Whether verification is enabled
        """
        self.logger = get_logger("verification.executor")
        self.registry = registry or ProbeRegistry()
        self.telemetry = telemetry or VerificationTelemetry()
        self.enabled = enabled

    def verify(
        self,
        command: str,
        cwd: str = "",
        fail_fast: bool = True,
    ) -> VerificationResult:
        """
        Run all applicable verification probes for a command.

        Args:
            command: The command to verify
            cwd: Current working directory for path resolution
            fail_fast: If True, stop on first failure

        Returns:
            VerificationResult with all probe results
        """
        if not self.enabled:
            return VerificationResult(
                command=command,
                results=[],
                total_duration_ms=0,
                blocked=False,
            )

        if not cwd:
            import os
            cwd = os.getcwd()

        start_time = time.monotonic()
        results: List[ProbeResult] = []
        blocking_result: Optional[ProbeResult] = None

        applicable_probes = self.registry.get_applicable(command)

        if not applicable_probes:
            total_ms = (time.monotonic() - start_time) * 1000
            return VerificationResult(
                command=command,
                results=results,
                total_duration_ms=total_ms,
                blocked=False,
            )

        self.logger.debug(
            f"Running {len(applicable_probes)} verification probe(s)",
            command=command,
            probes=[p.name for p in applicable_probes],
        )

        for probe in applicable_probes:
            result = probe._timed_execute(command, cwd)
            results.append(result)

            if result.status == ProbeStatus.FAILED:
                self.logger.info(
                    f"Probe {probe.name} FAILED - blocking command",
                    command=command,
                    reason=result.message,
                    duration_ms=result.duration_ms,
                )

                if fail_fast:
                    blocking_result = result
                    break

        total_ms = (time.monotonic() - start_time) * 1000
        blocked = blocking_result is not None

        verification_result = VerificationResult(
            command=command,
            results=results,
            total_duration_ms=total_ms,
            blocked=blocked,
            blocking_result=blocking_result,
        )

        self.telemetry.log_verification(verification_result)

        if blocked:
            self.logger.info(
                f"Command BLOCKED by verification probe",
                command=command,
                probe=blocking_result.probe_name,
                reason=blocking_result.message,
                total_duration_ms=total_ms,
            )
        else:
            self.logger.debug(
                f"Command PASSED verification",
                command=command,
                probes_run=len(results),
                total_duration_ms=total_ms,
            )

        return verification_result

    def verify_batch(
        self,
        commands: List[str],
        cwd: str = "",
        fail_fast: bool = True,
    ) -> List[VerificationResult]:
        """
        Verify a batch of commands.

        Args:
            commands: List of commands to verify
            cwd: Current working directory
            fail_fast: If True, stop on first failure

        Returns:
            List of VerificationResult, one per command
        """
        return [self.verify(cmd, cwd, fail_fast) for cmd in commands]

    def get_blocked_response(self, result: VerificationResult) -> Dict[str, any]:
        """
        Generate a structured response for a blocked command.

        This response is designed to be returned to the agent so it can
        self-correct without wasting tokens on the full execution.

        Args:
            result: The verification result that caused the block

        Returns:
            Dict with structured error information
        """
        if not result.blocked or not result.blocking_result:
            return {"blocked": False}

        blocking = result.blocking_result

        return {
            "blocked": True,
            "success": False,
            "stdout": "",
            "stderr": f"[VERIFICATION BLOCKED] {blocking.message}",
            "return_code": -1,
            "verification": {
                "probe": blocking.probe_name,
                "reason": blocking.message,
                "duration_ms": blocking.duration_ms,
                "suggestion": self._get_suggestion(blocking),
            },
        }

    def _get_suggestion(self, result: ProbeResult) -> str:
        """Generate a helpful suggestion based on the probe failure"""
        if result.probe_name == "file_existence":
            missing = result.metadata.get("missing_files", [])
            if missing:
                return f"Check that the file path(s) are correct: {', '.join(missing)}"
            return "Verify the file path in the command"

        if result.probe_name == "syntax_check":
            errors = result.metadata.get("syntax_errors", [])
            if errors:
                return f"Fix syntax error(s): {'; '.join(errors[:3])}"
            return "Check the file for syntax errors"

        if result.probe_name == "command_parse":
            return "Check for unbalanced quotes or invalid escape sequences"

        return "Review the command and try again"
