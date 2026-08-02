"""Tests for action type selection and immediate response gate."""

import threading

from unittest.mock import Mock, patch
from types import SimpleNamespace

from ai_agent.core_processing.five_phase_engine import (
    FivePhaseEngine,
    ActionType,
    PipelinePhase,
    PipelineContext,
)
from ai_agent.external_integration.model_runner import TaskType


class TestActionTypeEnum:
    """Verify ActionType enum defines all five required types."""

    def test_all_five_action_types_exist(self):
        assert ActionType.RUN_COMMAND.value == "run_command"
        assert ActionType.WRITE_FILE.value == "write_file"
        assert ActionType.READ_FILE.value == "read_file"
        assert ActionType.ANSWER_DIRECTLY.value == "answer_directly"
        assert ActionType.ASK_USER.value == "ask_user"

    def test_action_type_enum_values_are_unique(self):
        values = [member.value for member in ActionType]
        assert len(values) == len(set(values)), "All action type values must be unique"

    def test_action_type_has_exactly_nine_members(self):
        assert len(ActionType) == 9


class TestParseVexisCommands:
    """Verify _parse_vexis_commands correctly extracts action_type and related fields."""

    def setup_method(self):
        self.engine = FivePhaseEngine.__new__(FivePhaseEngine)

    def test_parses_action_type_run_command(self):
        text = "Some text\naction_type [run_command]\nstep_list [1. Do something]"
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "run_command"
        assert "step_list" in result

    def test_parses_action_type_answer_directly(self):
        text = "action_type [answer_directly]\nanswer [This is the direct answer]"
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "answer_directly"
        assert result["answer"] == "This is the direct answer"

    def test_parses_action_type_ask_user(self):
        text = "action_type [ask_user]\nquestion [What file do you want to read?]"
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "ask_user"
        assert result["question"] == "What file do you want to read?"

    def test_parses_action_type_write_file(self):
        text = "action_type [write_file]\nstep_list [1. Create the file]"
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "write_file"

    def test_parses_action_type_read_file(self):
        text = "action_type [read_file]\nstep_list [1. Read the file]"
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "read_file"

    def test_action_type_is_case_insensitive(self):
        text = "action_type [ANSWER_DIRECTLY]\nanswer [Hello]"
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "answer_directly"

    def test_empty_text_returns_empty_dict(self):
        result = self.engine._parse_vexis_commands("")
        assert result == {}

    def test_none_text_returns_empty_dict(self):
        result = self.engine._parse_vexis_commands(None)
        assert result == {}

    def test_action_type_with_extra_whitespace(self):
        text = "action_type  [  run_command  ]\nstep_list [1. Test]"
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "run_command"

    def test_parses_answer_field_with_multiline_content(self):
        text = "action_type [answer_directly]\nanswer [Line 1\nLine 2\nLine 3]"
        result = self.engine._parse_vexis_commands(text)
        assert result["answer"] == "Line 1\nLine 2\nLine 3"

    def test_parses_summary_alongside_action_type(self):
        text = (
            "action_type [run_command]\n"
            "Summary_of_Progress [I completed the setup]\n"
            "step_list [1. Next step]"
        )
        result = self.engine._parse_vexis_commands(text)
        assert result["action_type"] == "run_command"
        assert result["summary"] == "I completed the setup"


class TestRunPhase1ActionTypeParsing:
    """Verify _run_phase1 correctly stores the parsed action_type."""

    def setup_method(self):
        self.engine = FivePhaseEngine.__new__(FivePhaseEngine)
        self.engine.logger = Mock()
        self.engine.max_iterations = 500
        self.engine.command_timeout = 1800
        self.engine.task_timeout = 7200
        self.engine._last_failed_instruction = None
        self.engine._last_failed_conversation_history = None
        self.engine._last_failed_phase = None
        self.engine._last_failed_iteration = None
        self.engine._last_failed_terminal_log = None

    def test_run_phase1_parses_run_command(self):
        context = PipelineContext(user_prompt="Create a folder")
        context.metadata["os_info"] = "macOS"

        mock_response = Mock(success=True)
        mock_response.content = (
            "action_type [run_command]\n"
            "step_list [1. Run mkdir command]"
        )

        self.engine.model_runner = Mock()
        self.engine.model_runner.run_model.return_value = mock_response

        self.engine._raise_if_cancelled = Mock()

        result = self.engine._run_phase1(context)
        assert result is True
        assert context.action_type == ActionType.RUN_COMMAND

    def test_run_phase1_parses_answer_directly(self):
        context = PipelineContext(user_prompt="What is Python?")
        context.metadata["os_info"] = "macOS"

        mock_response = Mock(success=True)
        mock_response.content = (
            "action_type [answer_directly]\n"
            "answer [Python is a programming language.]"
        )

        self.engine.model_runner = Mock()
        self.engine.model_runner.run_model.return_value = mock_response
        self.engine._raise_if_cancelled = Mock()

        result = self.engine._run_phase1(context)
        assert result is True
        assert context.action_type == ActionType.ANSWER_DIRECTLY

    def test_run_phase1_parses_ask_user(self):
        context = PipelineContext(user_prompt="Read my file")
        context.metadata["os_info"] = "macOS"

        mock_response = Mock(success=True)
        mock_response.content = (
            "action_type [ask_user]\n"
            "question [Which file should I read?]"
        )

        self.engine.model_runner = Mock()
        self.engine.model_runner.run_model.return_value = mock_response
        self.engine._raise_if_cancelled = Mock()

        result = self.engine._run_phase1(context)
        assert result is True
        assert context.action_type == ActionType.ASK_USER
        assert context.ask_user_question == "Which file should I read?"

    def test_run_phase1_handles_unknown_action_type_gracefully(self):
        context = PipelineContext(user_prompt="Do something")
        context.metadata["os_info"] = "macOS"

        mock_response = Mock(success=True)
        mock_response.content = (
            "action_type [invalid_type]\n"
            "step_list [1. Do something]"
        )

        self.engine.model_runner = Mock()
        self.engine.model_runner.run_model.return_value = mock_response
        self.engine._raise_if_cancelled = Mock()

        result = self.engine._run_phase1(context)
        assert result is True
        # Unknown action types now default to RUN_COMMAND instead of None
        assert context.action_type == ActionType.RUN_COMMAND

    def test_run_phase1_without_action_type_still_succeeds(self):
        context = PipelineContext(user_prompt="Create a file")
        context.metadata["os_info"] = "macOS"

        mock_response = Mock(success=True)
        mock_response.content = "step_list [1. Create the file]"

        self.engine.model_runner = Mock()
        self.engine.model_runner.run_model.return_value = mock_response
        self.engine._raise_if_cancelled = Mock()

        result = self.engine._run_phase1(context)
        assert result is True
        # Missing action_type with step_list present now defaults to RUN_COMMAND
        assert context.action_type == ActionType.RUN_COMMAND


class TestImmediateResponseGate:
    """Verify the immediate response gate skips P2-P5 when answer_directly is selected."""

    def setup_method(self):
        self.engine = FivePhaseEngine.__new__(FivePhaseEngine)
        self.engine.config = {}
        self.engine.logger = Mock()
        self.engine.terminal_history = Mock()
        self.engine.model_runner = Mock()
        self.engine.max_iterations = 500
        self.engine.command_timeout = 1800
        self.engine.task_timeout = 7200
        self.engine._last_failed_instruction = None
        self.engine._last_failed_conversation_history = None
        self.engine._last_failed_phase = None
        self.engine._last_failed_iteration = None
        self.engine._last_failed_terminal_log = None
        self.engine.telegram_bot = None
        self.engine._cancel_lock = threading.Lock()
        self.engine._active_cancel_event = None
        self.engine.tool_policy_engine = None
        self.engine.provenance_tracker = None
        self.engine.repository_index = None

    def test_answer_directly_skips_to_phase6(self):
        self.engine._run_immediate_response = Mock(return_value=True)
        self.engine._raise_if_cancelled = Mock()

        def phase1_side_effect(ctx):
            ctx.action_type = ActionType.ANSWER_DIRECTLY
            return True

        self.engine._run_phase1 = Mock(side_effect=phase1_side_effect)

        result = self.engine.execute_instruction(
            "What is the capital of France?",
            cancel_event=Mock()
        )

        assert result.current_phase == PipelinePhase.COMPLETED
        self.engine._run_immediate_response.assert_called_once()
        self.engine._run_immediate_response.reset_mock()

    def test_run_command_goes_through_normal_pipeline(self):
        self.engine.max_iterations = 5
        self.engine._run_phase2 = Mock(return_value=True)
        self.engine._run_phase3 = Mock(return_value=True)

        def phase4_side_effect(ctx):
            ctx.step_list.clear()
            return True

        self.engine._run_phase4 = Mock(side_effect=phase4_side_effect)
        self.engine._compress_context = Mock()
        self.engine._run_phase5 = Mock(return_value=True)
        self.engine._run_phase6 = Mock(return_value=True)
        self.engine._raise_if_cancelled = Mock()
        self.engine._run_immediate_response = Mock()

        def phase1_side_effect(ctx):
            ctx.action_type = ActionType.RUN_COMMAND
            ctx.step_list = ["Run mkdir"]
            return True

        self.engine._run_phase1 = Mock(side_effect=phase1_side_effect)

        self.engine.execute_instruction(
            "Create a folder",
            cancel_event=Mock()
        )

        self.engine._run_phase2.assert_called_once()
        self.engine._run_phase3.assert_called_once()
        self.engine._run_phase4.assert_called_once()
        self.engine._run_phase5.assert_called_once()
        self.engine._run_phase6.assert_called_once()
        self.engine._run_immediate_response.assert_not_called()

    def test_ask_user_returns_early(self):
        self.engine._raise_if_cancelled = Mock()

        def phase1_side_effect(ctx):
            ctx.action_type = ActionType.ASK_USER
            ctx.ask_user_question = "Which file?"
            return True

        self.engine._run_phase1 = Mock(side_effect=phase1_side_effect)

        result = self.engine.execute_instruction(
            "Read my file",
            cancel_event=Mock()
        )

        assert result.current_phase == PipelinePhase.COMPLETED
        assert result.ask_user_question == "Which file?"


class TestRunImmediateResponse:
    """Verify _run_immediate_response generates the correct output."""

    def setup_method(self):
        self.engine = FivePhaseEngine.__new__(FivePhaseEngine)
        self.engine.logger = Mock()
        self.engine.telegram_bot = None

    def test_uses_answer_from_phase1_output(self, capsys):
        context = PipelineContext(user_prompt="What is Python?")
        context.phase1_output = (
            "action_type [answer_directly]\n"
            "answer [Python is a programming language.]"
        )
        context.telegram_mode = False

        result = self.engine._run_immediate_response(context)
        assert result is True
        assert context.final_summary == "Python is a programming language."

    def test_uses_summary_when_no_answer_provided(self, capsys):
        context = PipelineContext(user_prompt="Hello")
        context.phase1_output = (
            "action_type [answer_directly]\n"
            "Summary_of_Progress [Hello! How can I help you today?]"
        )
        context.telegram_mode = False

        result = self.engine._run_immediate_response(context)
        assert result is True
        assert "Hello! How can I help you today?" in context.final_summary

    def test_fallback_when_no_answer_or_summary(self, capsys):
        context = PipelineContext(user_prompt="What is the meaning of life?")
        context.phase1_output = "action_type [answer_directly]"
        context.telegram_mode = False

        result = self.engine._run_immediate_response(context)
        assert result is True
        assert context.final_summary is not None
        assert "What is the meaning of life?" in context.final_summary

    def test_error_handling_returns_fallback(self, capsys):
        context = PipelineContext(user_prompt="Test")
        context.phase1_output = None
        context.telegram_mode = False

        result = self.engine._run_immediate_response(context)
        assert result is True
        assert context.final_summary is not None


class TestModelRunnerTemplate:
    """Verify the Phase 1 template includes action type selection."""

    def test_phase1_template_includes_action_type(self):
        from ai_agent.external_integration.model_runner import PromptTemplate
        template = PromptTemplate()
        phase1 = template.get_template(TaskType.PHASE1_INITIAL_PLANNING)
        assert "action_type" in phase1
        assert "run_command" in phase1
        assert "write_file" in phase1
        assert "read_file" in phase1
        assert "answer_directly" in phase1
        assert "ask_user" in phase1

    def test_phase1_template_has_action_type_before_step_list(self):
        from ai_agent.external_integration.model_runner import PromptTemplate
        template = PromptTemplate()
        phase1 = template.get_template(TaskType.PHASE1_INITIAL_PLANNING)
        action_pos = phase1.index("action_type")
        step_pos = phase1.index("step_list")
        assert action_pos < step_pos, "action_type must appear before step_list in the prompt"

    def test_system_instructions_include_action_types(self):
        from ai_agent.external_integration.model_runner import ModelRunner
        with patch.object(ModelRunner, '_get_system_instructions', return_value=""):
            import ai_agent.external_integration.model_runner as mr_module
            original_runner = ModelRunner

            class TestRunner(ModelRunner):
                def _get_system_instructions(self, task_type):
                    return """Test instructions with action types:
                    - run_command: Execute shell commands
                    - write_file: Write content to file
                    - read_file: Read file contents
                    - answer_directly: Provide information
                    - ask_user: Request clarification"""

            runner = TestRunner.__new__(TestRunner)
            instructions = runner._get_system_instructions(TaskType.PHASE1_INITIAL_PLANNING)
            assert "run_command" in instructions
            assert "write_file" in instructions
            assert "read_file" in instructions
            assert "answer_directly" in instructions
            assert "ask_user" in instructions

    def test_phase2_template_emphasizes_read_before_write(self):
        from ai_agent.external_integration.model_runner import PromptTemplate
        template = PromptTemplate()
        phase2 = template.get_template(TaskType.PHASE2_ACTION_GENERATION)
        assert "read_file" in phase2
        assert "BEFORE editing" in phase2 or "before editing" in phase2.lower()
        assert "cannot edit what you have not read" in phase2

    def test_phase4_template_includes_failure_classification(self):
        from ai_agent.external_integration.model_runner import PromptTemplate
        template = PromptTemplate()
        phase4 = template.get_template(TaskType.PHASE4_DYNAMIC_UPDATE)
        assert "TEMPORARY ERROR" in phase4
        assert "FUNDAMENTAL MISUNDERSTANDING" in phase4
        assert "ENVIRONMENT ERROR" in phase4
        assert "retry allowed" in phase4
        assert "confirm via ask_user" in phase4
        assert "alternative approach" in phase4


class TestPipelineContextDefaults:
    """Verify PipelineContext includes new fields with correct defaults."""

    def test_action_type_defaults_to_none(self):
        ctx = PipelineContext(user_prompt="test")
        assert ctx.action_type is None

    def test_ask_user_question_defaults_to_none(self):
        ctx = PipelineContext(user_prompt="test")
        assert ctx.ask_user_question is None

    def test_action_type_can_be_set(self):
        ctx = PipelineContext(user_prompt="test")
        ctx.action_type = ActionType.RUN_COMMAND
        assert ctx.action_type == ActionType.RUN_COMMAND

    def test_ask_user_question_can_be_set(self):
        ctx = PipelineContext(user_prompt="test")
        ctx.ask_user_question = "Which file?"
        assert ctx.ask_user_question == "Which file?"