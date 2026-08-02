from unittest.mock import Mock

from ai_agent.core_processing.five_phase_engine import FivePhaseEngine, PipelineContext


def test_parse_commands_supports_keep_commands():
    engine = FivePhaseEngine.__new__(FivePhaseEngine)
    code = """KEEP_TEXT: remember this exactly
KEEP_FILE: /tmp/demo.txt
"""
    commands = engine._parse_commands(code)
    assert commands == [
        "keep_text('remember this exactly')",
        "keep_file('/tmp/demo.txt')",
    ]


def test_run_phase3_stores_keep_text_and_keep_file(tmp_path):
    keep_file = tmp_path / "memo.txt"
    keep_file.write_text("persistent content", encoding="utf-8")

    engine = FivePhaseEngine.__new__(FivePhaseEngine)
    engine.logger = Mock()
    engine.command_timeout = 10
    engine.terminal_history = Mock()

    context = PipelineContext(user_prompt="test")
    context.extracted_commands = f"keep_text('literal note')\nkeep_file('{keep_file}')"

    assert engine._run_phase3(context) is True
    assert context.kept_text_records == ["literal note"]
    assert str(keep_file) in context.kept_file_records
    assert context.kept_file_records[str(keep_file)] == "persistent content"
