"""Tests for the concise VEXIS system prompt."""

from types import SimpleNamespace

from ai_agent.external_integration import model_runner
from ai_agent.external_integration.model_runner import ModelRunner, TaskType


def test_system_instructions_are_concise_and_keep_core_rules(monkeypatch):
    """System instructions should stay short while retaining essential behavior."""
    monkeypatch.setattr(
        model_runner,
        "load_config",
        lambda: SimpleNamespace(custom_system_prompt=""),
    )

    runner = ModelRunner.__new__(ModelRunner)
    instructions = runner._get_system_instructions(TaskType.PHASE1_INITIAL_PLANNING)

    assert len(instructions) < 3500
    assert "5-phase workflow" in instructions
    assert "Follow the phase prompt's required output format exactly" in instructions
    assert "Prefer safe commands" in instructions
    assert "actual output, not just exit codes" in instructions
    assert "Behavioral Guidelines" not in instructions
    assert "Quality Assurance" not in instructions
    assert "read_file" in instructions
    assert "TEMPORARY ERROR" in instructions
    assert "FUNDAMENTAL MISUNDERSTANDING" in instructions
    assert "ENVIRONMENT ERROR" in instructions
