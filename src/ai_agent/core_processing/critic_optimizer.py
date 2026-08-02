"""
Critic & Optimizer Pre-Phase Module

An optional pre-phase that runs before Phase 1 to:
- Critic: Analyze the plan graph for ambiguity, risk, missing steps
- Optimizer: Rewrite the plan for lower risk and fewer commands

This reduces wasted iterations and expensive LLM calls downstream.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logger import get_logger
from .plan_graph import PlanGraph, RiskLevel, SubgoalNode, ValidationCommand

logger = get_logger("critic_optimizer")


class CriticIssueType:
    AMBIGUOUS_DESCRIPTION = "ambiguous_description"
    MISSING_ARTIFACT = "missing_artifact"
    MISSING_VALIDATION = "missing_validation"
    EXCESSIVE_RISK = "excessive_risk"
    UNNECESSARY_STEP = "unnecessary_step"
    MISSING_DEPENDENCY = "missing_dependency"
    CIRCULAR_DEPENDENCY = "circular_dependency"


@dataclass
class CriticIssue:
    issue_type: str
    node_id: Optional[str]
    description: str
    severity: float  # 0.0 to 1.0
    suggestion: str


@dataclass
class CriticReport:
    issues: List[CriticIssue] = field(default_factory=list)
    risk_score: float = 0.0
    ambiguity_score: float = 0.0
    passes: bool = True
    optimizations_applied: int = 0

    @property
    def total_severity(self) -> float:
        return sum(i.severity for i in self.issues)


class PlanCritic:
    """Analyzes a PlanGraph for ambiguity, risk, and missing elements."""

    AMBIGUITY_KEYWORDS = {
        "something", "whatever", "as needed", "maybe", "possibly",
        "appropriate", "suitable", "some", "stuff", "things",
        "later", "eventually", "somehow", "fix", "tweak", "adjust",
    }

    def analyze(self, graph: PlanGraph) -> CriticReport:
        report = CriticReport()

        for node in graph.nodes.values():
            self._check_ambiguity(node, report)
            self._check_risk(node, report)
            self._check_validation(node, report)
            self._check_dependencies(graph, node, report)

        self._check_graph_structure(graph, report)

        report.risk_score = graph.risk_score
        if report.issues:
            report.ambiguity_score = sum(
                i.severity for i in report.issues
                if i.issue_type == CriticIssueType.AMBIGUOUS_DESCRIPTION
            )

        issue_weight = report.total_severity / max(len(report.issues), 1)
        report.passes = issue_weight < 0.4 and report.risk_score < 0.5

        return report

    def _check_ambiguity(self, node: SubgoalNode, report: CriticReport) -> None:
        desc_lower = node.description.lower()
        found = [kw for kw in self.AMBIGUITY_KEYWORDS if kw in desc_lower]
        if found:
            report.issues.append(CriticIssue(
                issue_type=CriticIssueType.AMBIGUOUS_DESCRIPTION,
                node_id=node.id,
                description=f"Ambiguous language in step '{node.description[:60]}': {', '.join(found)}",
                severity=0.5,
                suggestion="Replace vague terms with specific, actionable instructions",
            ))

        action = node.action_type.lower()
        if action == "run_command" and not node.commands:
            report.issues.append(CriticIssue(
                issue_type=CriticIssueType.AMBIGUOUS_DESCRIPTION,
                node_id=node.id,
                description=f"Step uses run_command but has no concrete commands defined",
                severity=0.6,
                suggestion="Add explicit commands to execute in this step",
            ))

    def _check_risk(self, node: SubgoalNode, report: CriticReport) -> None:
        if node.risk == RiskLevel.CRITICAL:
            if not node.validation_commands:
                report.issues.append(CriticIssue(
                    issue_type=CriticIssueType.MISSING_VALIDATION,
                    node_id=node.id,
                    description=f"Critical-risk step '{node.description[:60]}' has no validation commands",
                    severity=0.8,
                    suggestion="Add validation commands to verify this critical step",
                ))
            if len(node.produces) == 0:
                report.issues.append(CriticIssue(
                    issue_type=CriticIssueType.MISSING_ARTIFACT,
                    node_id=node.id,
                    description=f"Critical-risk step does not declare produced artifacts",
                    severity=0.6,
                    suggestion="Declare what artifacts this step produces for traceability",
                ))

    def _check_validation(self, node: SubgoalNode, report: CriticReport) -> None:
        if node.status != SubgoalNode:
            return
        if node.risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) and not node.validation_commands:
            report.issues.append(CriticIssue(
                issue_type=CriticIssueType.MISSING_VALIDATION,
                node_id=node.id,
                description=f"Step '{node.description[:60]}' is high/critical risk but lacks validation",
                severity=0.7,
                suggestion="Add probes or verification commands for this step",
            ))

    def _check_dependencies(self, graph: PlanGraph, node: SubgoalNode, report: CriticReport) -> None:
        for req in node.requires:
            if req not in graph.nodes:
                report.issues.append(CriticIssue(
                    issue_type=CriticIssueType.MISSING_DEPENDENCY,
                    node_id=node.id,
                    description=f"Step depends on '{req}' which does not exist in the graph",
                    severity=0.9,
                    suggestion=f"Add missing step '{req}' or remove the dependency",
                ))

    def _check_graph_structure(self, graph: PlanGraph, report: CriticReport) -> None:
        visited: set = set()
        path: set = set()

        def has_cycle(nid: str) -> bool:
            if nid in path:
                return True
            if nid in visited:
                return False
            path.add(nid)
            visited.add(nid)
            node = graph.nodes.get(nid)
            if node:
                for req in node.requires:
                    if has_cycle(req):
                        return True
            path.discard(nid)
            return False

        for nid in graph.nodes:
            if nid not in visited:
                if has_cycle(nid):
                    report.issues.append(CriticIssue(
                        issue_type=CriticIssueType.CIRCULAR_DEPENDENCY,
                        node_id=nid,
                        description=f"Circular dependency detected involving step '{nid}'",
                        severity=1.0,
                        suggestion="Break the cycle by removing or reordering dependencies",
                    ))
                    return


class PlanOptimizer:
    """Rewrites plans for lower risk and fewer commands."""

    def optimize(self, graph: PlanGraph, report: CriticReport) -> Tuple[PlanGraph, int]:
        optimizations = 0

        if report.risk_score > 0.5:
            optimizations += self._split_high_risk_nodes(graph)

        optimizations += self._prune_redundant_nodes(graph)
        optimizations += self._add_validation_stubs(graph)

        if graph.entry_points and len(graph.entry_points) == 0:
            ready = graph.get_ready_nodes()
            if ready:
                graph.entry_points = [n.id for n in ready]

        graph.compute_risk_score()
        return graph, optimizations

    def _split_high_risk_nodes(self, graph: PlanGraph) -> int:
        splits = 0
        to_split = [
            n for n in graph.nodes.values()
            if n.risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)
            and len(n.commands or []) > 3
        ]

        for node in to_split:
            original_commands = list(node.commands or [])
            mid = len(original_commands) // 2

            node.commands = original_commands[:mid]
            node.risk = RiskLevel.HIGH

            split_id = f"{node.id}_split"
            split_node = SubgoalNode(
                id=split_id,
                description=f"[auto-split] {node.description} (cont.)",
                action_type=node.action_type,
                risk=RiskLevel.HIGH,
                requires=[node.id],
                commands=original_commands[mid:],
                provenance=node.provenance,
            )
            graph.add_node(split_node)

            for child_id, child_node in graph.nodes.items():
                if node.id in child_node.requires and child_id != split_id:
                    child_node.requires.append(split_id)

            splits += 1

        return splits

    def _prune_redundant_nodes(self, graph: PlanGraph) -> int:
        pruned = 0
        to_remove: List[str] = []

        for node in graph.nodes.values():
            desc_lower = node.description.lower()
            if any(phrase in desc_lower for phrase in ["do nothing", "skip", "noop"]):
                to_remove.append(node.id)

        for nid in to_remove:
            node = graph.nodes.get(nid)
            if node:
                for child_id, child_node in graph.nodes.items():
                    if nid in child_node.requires:
                        child_node.requires.remove(nid)
                        child_node.requires.extend(node.requires)
                del graph.nodes[nid]
                graph.total_steps = len(graph.nodes)
                pruned += 1

        return pruned

    def _add_validation_stubs(self, graph: PlanGraph) -> int:
        added = 0
        for node in graph.nodes.values():
            if node.risk == RiskLevel.CRITICAL and not node.validation_commands:
                most_recent_id = node.id
                validation_node = SubgoalNode(
                    id=f"{node.id}_validate",
                    description=f"Validate: {node.description[:50]}",
                    action_type="run_command",
                    risk=RiskLevel.LOW,
                    requires=[most_recent_id],
                    validation_commands=[],
                    dry_run_first=True,
                )
                graph.add_node(validation_node)
                added += 1

        return added


def run_critic_optimizer(
    graph: PlanGraph,
    enable_critic: bool = True,
    enable_optimizer: bool = True,
) -> Tuple[PlanGraph, CriticReport]:
    critic = PlanCritic()
    optimizer = PlanOptimizer()
    report = critic.analyze(graph)

    if not report.passes and enable_optimizer:
        graph, n_opt = optimizer.optimize(graph, report)
        report.optimizations_applied = n_opt

        if n_opt > 0:
            report = critic.analyze(graph)

    return graph, report