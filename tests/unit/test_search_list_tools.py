"""Tests for the search and list_files native tools.

These two read-only "basic" tools let the agent explore a project without
resorting to shell grep/ls. They are first-class action types and native
commands handled entirely in Phase 3 (no shell execution).
"""
from unittest.mock import Mock

from ai_agent.core_processing.five_phase_engine import (
    FivePhaseEngine,
    ActionType,
    PipelineContext,
)
from ai_agent.core_processing.tool_policy import ToolPolicyEngine


def _make_engine():
    engine = FivePhaseEngine.__new__(FivePhaseEngine)
    engine.logger = Mock()
    engine.command_timeout = 10
    engine.terminal_history = Mock()
    return engine


class TestSearchListActionTypes:
    def test_search_and_list_files_action_types_exist(self):
        assert ActionType.SEARCH.value == "search"
        assert ActionType.LIST_FILES.value == "list_files"

    def test_parse_vexis_commands_parses_search(self):
        engine = FivePhaseEngine.__new__(FivePhaseEngine)
        result = engine._parse_vexis_commands("action_type [search]\nstep_list [1. Find usages]")
        assert result["action_type"] == "search"

    def test_parse_vexis_commands_parses_list_files(self):
        engine = FivePhaseEngine.__new__(FivePhaseEngine)
        result = engine._parse_vexis_commands("action_type [list_files]\nstep_list [1. List src]")
        assert result["action_type"] == "list_files"


class TestParseCommandsPrefixFormat:
    def setup_method(self):
        self.engine = FivePhaseEngine.__new__(FivePhaseEngine)

    def test_parse_commands_search_prefix(self):
        commands = self.engine._parse_commands("SEARCH: def main\n")
        assert commands == ["search('def main')"]

    def test_parse_commands_list_files_prefix(self):
        commands = self.engine._parse_commands("LIST_FILES: src/ai_agent\n")
        assert commands == ["list_files('src/ai_agent')"]


class TestPhase3SearchListExecution:
    def test_run_phase3_executes_search(self, tmp_path):
        target = tmp_path / "code.py"
        target.write_text("def hello():\n    return 42\n", encoding="utf-8")

        engine = _make_engine()
        context = PipelineContext(user_prompt="test")
        context.extracted_commands = f"search('hello', '{tmp_path}')\n"

        assert engine._run_phase3(context) is True
        output = context.last_execution_result["stdout"]
        assert "hello" in output
        assert "code.py" in output

    def test_run_phase3_search_no_match_reports_empty(self, tmp_path):
        (tmp_path / "a.txt").write_text("nothing interesting here\n", encoding="utf-8")

        engine = _make_engine()
        context = PipelineContext(user_prompt="test")
        context.extracted_commands = f"search('zzz_not_found', '{tmp_path}')\n"

        assert engine._run_phase3(context) is True
        assert "no matches found" in context.last_execution_result["stdout"]

    def test_run_phase3_executes_list_files(self, tmp_path):
        (tmp_path / "one.py").write_text("", encoding="utf-8")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "two.py").write_text("", encoding="utf-8")

        engine = _make_engine()
        context = PipelineContext(user_prompt="test")
        context.extracted_commands = f"list_files('{tmp_path}')\n"

        assert engine._run_phase3(context) is True
        output = context.last_execution_result["stdout"]
        assert "one.py" in output
        # Immediate listing should not recurse into sub/ by default
        assert "two.py" not in output

    def test_run_phase3_executes_list_files_recursive(self, tmp_path):
        (tmp_path / "one.py").write_text("", encoding="utf-8")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "two.py").write_text("", encoding="utf-8")

        engine = _make_engine()
        context = PipelineContext(user_prompt="test")
        context.extracted_commands = f"list_files('{tmp_path}', 'recursive')\n"

        assert engine._run_phase3(context) is True
        output = context.last_execution_result["stdout"]
        assert "one.py" in output
        assert "two.py" in output


class TestToolPolicyScores:
    def test_search_and_list_files_are_scored_safe(self):
        engine = ToolPolicyEngine()
        search_score = engine.score_tool("search")
        list_score = engine.score_tool("list_files")
        assert search_score.safety == 1.0
        assert list_score.safety == 1.0
        assert search_score.info_gain > 0
        assert list_score.info_gain > 0
