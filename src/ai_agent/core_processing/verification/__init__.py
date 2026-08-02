"""
Verification-First Execution Layer for VEXIS-CLI

Provides lightweight pre-flight verification probes that run before expensive
shell commands to fail fast on predictable errors (missing files, syntax errors, etc.).
"""

from .probes import (
    Probe,
    ProbeResult,
    ProbeStatus,
    VerificationResult,
    FileExistenceProbe,
    SyntaxCheckProbe,
    CommandParseProbe,
)
from .registry import ProbeRegistry
from .executor import VerificationExecutor
from .telemetry import VerificationTelemetry

__all__ = [
    "Probe",
    "ProbeResult",
    "ProbeStatus",
    "VerificationResult",
    "FileExistenceProbe",
    "SyntaxCheckProbe",
    "CommandParseProbe",
    "ProbeRegistry",
    "VerificationExecutor",
    "VerificationTelemetry",
]
