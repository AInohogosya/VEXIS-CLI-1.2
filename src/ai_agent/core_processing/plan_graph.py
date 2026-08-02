"""
Predictive Subgoal Graph (PSG) Data Model

Replaces the linear step_list with a directed graph that tracks:
- Required artifacts (files, code, data to produce)
- Risk levels for each subgoal
- Validation commands to verify correctness
- Confidence scores for confidence-gated execution
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NodeStatus(enum.Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"


@dataclass
class Artifact:
    path: str
    artifact_type: str  # "file", "code_block", "data", "config"
    description: str = ""
    checksum: Optional[str] = None
    produced_by: Optional[str] = None  # subgoal id


@dataclass
class ValidationCommand:
    command: str
    description: str = ""
    is_lightweight: bool = True
    expected_outcome: Optional[str] = None


@dataclass
class Provenance:
    origin_phase: str
    timestamp: float = field(default_factory=time.time)
    model: Optional[str] = None
    provider: Optional[str] = None
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    confidence: float = 1.0
    source_command: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubgoalNode:
    id: str
    description: str
    action_type: str  # run_command, write_file, read_file, etc.
    risk: RiskLevel = RiskLevel.MEDIUM
    status: NodeStatus = NodeStatus.PENDING
    requires: List[str] = field(default_factory=list)  # IDs of prerequisite nodes
    produces: List[Artifact] = field(default_factory=list)
    validation_commands: List[ValidationCommand] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    confidence: float = 1.0
    provenance: Optional[Provenance] = None
    dry_run_first: bool = False
    result: Optional[str] = None
    error: Optional[str] = None

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class PlanGraph:
    nodes: Dict[str, SubgoalNode] = field(default_factory=dict)
    entry_points: List[str] = field(default_factory=list)
    goal_description: str = ""
    created_at: float = field(default_factory=time.time)
    risk_score: float = 0.0
    total_steps: int = 0

    def add_node(self, node: SubgoalNode) -> None:
        self.nodes[node.id] = node
        self.total_steps = len(self.nodes)

    def get_ready_nodes(self) -> List[SubgoalNode]:
        ready = []
        for node in self.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue
            prereqs_met = all(
                    dep_id in self.nodes
                    and self.nodes[dep_id].status == NodeStatus.COMPLETED
                    for dep_id in node.requires
            )
            if prereqs_met:
                ready.append(node)
        return ready

    def mark_completed(self, node_id: str, result: str = "") -> None:
        node = self.nodes.get(node_id)
        if node:
            node.status = NodeStatus.COMPLETED
            node.result = result

    def mark_failed(self, node_id: str, error: str = "") -> None:
        node = self.nodes.get(node_id)
        if node:
            node.status = NodeStatus.FAILED
            node.error = error

    def get_failed_nodes(self) -> List[SubgoalNode]:
        return [n for n in self.nodes.values() if n.status == NodeStatus.FAILED]

    def get_all_validation_commands(self) -> List[ValidationCommand]:
        cmds = []
        for node in self.nodes.values():
            if node.status == NodeStatus.COMPLETED:
                cmds.extend(node.validation_commands)
        return cmds

    def compute_risk_score(self) -> float:
        risk_weights = {
            RiskLevel.LOW: 0.1,
            RiskLevel.MEDIUM: 0.3,
            RiskLevel.HIGH: 0.6,
            RiskLevel.CRITICAL: 1.0,
        }
        if not self.nodes:
            return 0.0
        total = sum(risk_weights.get(n.risk, 0.3) for n in self.nodes.values())
        self.risk_score = total / len(self.nodes)
        return self.risk_score

    def find_low_confidence_nodes(self, threshold: float = 0.6) -> List[SubgoalNode]:
        return [
            n for n in self.nodes.values()
            if n.confidence < threshold and n.status == NodeStatus.PENDING
        ]

    def to_step_list(self) -> List[str]:
        ordered = []
        visited: Set[str] = set()
        pending = list(self.entry_points)

        while pending:
            nid = pending.pop(0)
            if nid in visited:
                continue
            visited.add(nid)
            node = self.nodes.get(nid)
            if node:
                risk_tag = f"[{node.risk.value.upper()}]" if node.risk != RiskLevel.MEDIUM else ""
                ordered.append(f"{risk_tag} {node.description}".strip())
                for child_id, child_node in self.nodes.items():
                    if nid in child_node.requires and child_id not in visited:
                        pending.append(child_id)

        return ordered

    @classmethod
    def from_step_list(cls, steps: List[str], goal: str = "") -> PlanGraph:
        graph = cls(goal_description=goal)
        for i, step in enumerate(steps):
            clean = step.strip()
            risk = RiskLevel.MEDIUM
            if clean.startswith("[HIGH]"):
                risk = RiskLevel.HIGH
                clean = clean.replace("[HIGH]", "").strip()
            elif clean.startswith("[CRITICAL]"):
                risk = RiskLevel.CRITICAL
                clean = clean.replace("[CRITICAL]", "").strip()
            elif clean.startswith("[LOW]"):
                risk = RiskLevel.LOW
                clean = clean.replace("[LOW]", "").strip()

            node = SubgoalNode(
                id=f"step_{i}",
                description=clean,
                action_type="run_command",
                risk=risk,
            )
            if i > 0:
                node.requires.append(f"step_{i - 1}")
            graph.add_node(node)
            if i == 0:
                graph.entry_points.append(node.id)

        graph.compute_risk_score()
        return graph