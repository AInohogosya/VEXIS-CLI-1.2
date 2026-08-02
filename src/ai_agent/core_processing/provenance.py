"""
Provenance Metadata Tracking for VEXIS-CLI

Attaches machine-checkable provenance to all writes and commands:
- trace_id: unique identifier for the execution trace
- confidence: how confident the system is in the correctness
- source: where the command originated (phase, model, etc.)
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProvenanceRecord:
    trace_id: str
    phase: str
    timestamp: float = field(default_factory=time.time)
    model: Optional[str] = None
    provider: Optional[str] = None
    confidence: float = 1.0
    source_command: Optional[str] = None
    iteration: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "phase": self.phase,
            "timestamp": self.timestamp,
            "model": self.model,
            "provider": self.provider,
            "confidence": self.confidence,
            "source_command": self.source_command,
            "iteration": self.iteration,
            "metadata": dict(self.metadata),
        }


class ProvenanceTracker:
    """Tracks provenance for all operations in the pipeline."""

    def __init__(self):
        self._records: Dict[str, ProvenanceRecord] = {}
        self._session_id: str = uuid.uuid4().hex[:12]

    def start_trace(self, phase: str, model: Optional[str] = None,
                    provider: Optional[str] = None) -> str:
        trace_id = f"{self._session_id}_{uuid.uuid4().hex[:8]}"
        self._records[trace_id] = ProvenanceRecord(
            trace_id=trace_id,
            phase=phase,
            model=model,
            provider=provider,
        )
        return trace_id

    def record(self, trace_id: str, phase: str, confidence: float = 1.0,
               source_command: Optional[str] = None, iteration: int = 0,
               metadata: Optional[Dict[str, Any]] = None) -> None:
        self._records[trace_id] = ProvenanceRecord(
            trace_id=trace_id,
            phase=phase,
            timestamp=time.time(),
            confidence=confidence,
            source_command=source_command,
            iteration=iteration,
            metadata=metadata or {},
        )

    def get(self, trace_id: str) -> Optional[ProvenanceRecord]:
        return self._records.get(trace_id)

    def get_all(self) -> Dict[str, ProvenanceRecord]:
        return dict(self._records)

    def annotate_command(self, command: str, trace_id: str) -> Dict[str, Any]:
        record = self._records.get(trace_id)
        if not record:
            return {"command": command, "provenance": {}}
        return {
            "command": command,
            "provenance": {
                "trace_id": trace_id,
                "session_id": self._session_id,
                "phase": record.phase,
                "confidence": record.confidence,
                "timestamp": record.timestamp,
            },
        }

    def annotate_write(self, file_path: str, content: str, trace_id: str) -> Dict[str, Any]:
        record = self._records.get(trace_id)
        if not record:
            return {"file_path": file_path, "provenance": {}}
        return {
            "file_path": file_path,
            "size": len(content),
            "provenance": {
                "trace_id": trace_id,
                "session_id": self._session_id,
                "phase": record.phase,
                "confidence": record.confidence,
                "timestamp": record.timestamp,
            },
        }

    @property
    def session_id(self) -> str:
        return self._session_id