"""Tests for multi-format code block handler."""

from ai_agent.core_processing.code_block_handler import (
    extract_code_block,
    extract_all_code_blocks,
    has_code_block,
    remove_code_blocks,
    detect_format,
    detect_all_formats,
    CodeBlockFormat,
)


class TestExtractCodeBlock:

    def test_extract_markdown_bash(self):
        text = "Some text\n```bash\nls -la\n```\nMore text"
        assert extract_code_block(text) == "ls -la"

    def test_extract_markdown_no_language(self):
        text = "Here is the command:\n```\necho hello\n```\nDone."
        assert extract_code_block(text) == "echo hello"

    def test_extract_markdown_last_block(self):
        text = "```\nfirst\n```\nSome text\n```\nsecond\n```"
        assert extract_code_block(text) == "second"

    def test_extract_xml(self):
        text = 'Execute:\n<code>\nls -la\n</code>\nResult.'
        assert extract_code_block(text) == "ls -la"

    def test_extract_xml_with_attributes(self):
        text = 'Use:\n<code lang="bash">\ncat file.txt\n</code>\nDone.'
        assert extract_code_block(text) == "cat file.txt"

    def test_extract_bbcode(self):
        text = 'Command:\n[code]\npwd\n[/code]\nOutput.'
        assert extract_code_block(text) == "pwd"

    def test_extract_custom_delimiter(self):
        text = 'Run:\n---code---\ngit status\n---end-code---\nDone.'
        assert extract_code_block(text) == "git status"

    def test_extract_html(self):
        text = 'Code:<pre><code>\nmkdir test\n</code></pre>End.'
        assert extract_code_block(text) == "mkdir test"

    def test_extract_html_with_attributes(self):
        text = '<pre><code class="bash">\ncd /tmp\n</code></pre>'
        assert extract_code_block(text) == "cd /tmp"

    def test_extract_no_code_block(self):
        assert extract_code_block("Just some plain text") is None

    def test_extract_empty(self):
        assert extract_code_block("") is None
        assert extract_code_block(None) is None

    def test_extract_last_wins_across_formats(self):
        text = "<code>command1</code>\n```\ncommand2\n```\n[code]command3[/code]"
        assert extract_code_block(text) == "command3"

    def test_extract_mixed_formats(self):
        text = '<code>cmd1</code>\n---code---\ncmd2\n---end-code---'
        assert extract_code_block(text) == "cmd2"


class TestHasCodeBlock:

    def test_has_markdown(self):
        assert has_code_block("Text\n```\ncode\n```\nmore") is True

    def test_has_xml(self):
        assert has_code_block("Text\n<code>code\n</code>") is True

    def test_has_bbcode(self):
        assert has_code_block("Text\n[code]code\n[/code]") is True

    def test_has_custom(self):
        assert has_code_block("Text\n---code---\ncode\n---end-code---") is True

    def test_has_html(self):
        assert has_code_block("<pre><code>code</code></pre>") is True

    def test_no_code_block(self):
        assert has_code_block("Just plain text") is False
        assert has_code_block("") is False
        assert has_code_block(None) is False


class TestRemoveCodeBlocks:

    def test_remove_markdown(self):
        result = remove_code_blocks("Hello\n```\ncode\n```\nWorld")
        assert "code" not in result
        assert "Hello" in result
        assert "World" in result

    def test_remove_xml(self):
        result = remove_code_blocks("Start\n<code>\ncmd\n</code>\nEnd")
        assert "cmd" not in result
        assert "Start" in result
        assert "End" in result

    def test_remove_bbcode(self):
        result = remove_code_blocks("A\n[code]\ncmd\n[/code]\nB")
        assert "cmd" not in result
        assert "A" in result
        assert "B" in result

    def test_remove_custom(self):
        result = remove_code_blocks("X\n---code---\ncmd\n---end-code---\nY")
        assert "cmd" not in result
        assert "X" in result
        assert "Y" in result

    def test_remove_html(self):
        result = remove_code_blocks("P\n<pre><code>\ncmd\n</code></pre>\nQ")
        assert "cmd" not in result
        assert "P" in result
        assert "Q" in result

    def test_remove_all_formats(self):
        text = "A\n```\nm1\n```B\n<code>m2</code>C\n[code]m3[/code]D\n---code---\nm4\n---end-code---E\n<pre><code>m5</code></pre>F"
        result = remove_code_blocks(text)
        assert "m1" not in result
        assert "m2" not in result
        assert "m3" not in result
        assert "m4" not in result
        assert "m5" not in result
        for ch in "ABCDEF":
            assert ch in result

    def test_remove_empty(self):
        assert remove_code_blocks("") == ""
        assert remove_code_blocks(None) is None


class TestDetectFormat:

    def test_detect_markdown(self):
        assert detect_format("```\ncode\n```") == CodeBlockFormat.MARKDOWN

    def test_detect_xml(self):
        assert detect_format("<code>code</code>") == CodeBlockFormat.XML

    def test_detect_bbcode(self):
        assert detect_format("[code]code[/code]") == CodeBlockFormat.BBCODE

    def test_detect_custom(self):
        assert detect_format("---code---\ncode\n---end-code---") == CodeBlockFormat.CUSTOM_DELIMITER

    def test_detect_html(self):
        assert detect_format("<pre><code>code</code></pre>") == CodeBlockFormat.HTML

    def test_detect_no_format(self):
        assert detect_format("plain text") is None
        assert detect_format("") is None
        assert detect_format(None) is None


class TestDetectAllFormats:

    def test_detect_single(self):
        assert detect_all_formats("```\ncode\n```") == [CodeBlockFormat.MARKDOWN]

    def test_detect_multiple(self):
        text = "```\na\n```\n<code>b</code>"
        formats = detect_all_formats(text)
        assert CodeBlockFormat.MARKDOWN in formats
        assert CodeBlockFormat.XML in formats

    def test_detect_none(self):
        assert detect_all_formats("plain") == []


class TestExtractAll:

    def test_extract_all_ordered(self):
        text = "<code>first</code>\n```\nsecond\n```"
        blocks = extract_all_code_blocks(text)
        assert len(blocks) == 2
        assert blocks[0][0] == "first"
        assert blocks[0][1] == CodeBlockFormat.XML
        assert blocks[1][0] == "second"
        assert blocks[1][1] == CodeBlockFormat.MARKDOWN

    def test_extract_all_empty(self):
        assert extract_all_code_blocks("") == []
        assert extract_all_code_blocks(None) == []


class TestFivePhaseEngineIntegration:

    def test_markdown_via_engine(self):
        from ai_agent.core_processing.five_phase_engine import FivePhaseEngine
        engine = FivePhaseEngine()
        assert engine._extract_code_block("```bash\nls -la\n```") == "ls -la"

    def test_xml_via_engine(self):
        from ai_agent.core_processing.five_phase_engine import FivePhaseEngine
        engine = FivePhaseEngine()
        assert engine._extract_code_block("<code>\nls -la\n</code>") == "ls -la"

    def test_bbcode_via_engine(self):
        from ai_agent.core_processing.five_phase_engine import FivePhaseEngine
        engine = FivePhaseEngine()
        assert engine._extract_code_block("[code]\nls -la\n[/code]") == "ls -la"

    def test_custom_via_engine(self):
        from ai_agent.core_processing.five_phase_engine import FivePhaseEngine
        engine = FivePhaseEngine()
        assert engine._extract_code_block("---code---\nls -la\n---end-code---") == "ls -la"

    def test_html_via_engine(self):
        from ai_agent.core_processing.five_phase_engine import FivePhaseEngine
        engine = FivePhaseEngine()
        assert engine._extract_code_block("<pre><code>\nls -la\n</code></pre>") == "ls -la"

    def test_has_and_remove_via_engine(self):
        from ai_agent.core_processing.five_phase_engine import FivePhaseEngine
        engine = FivePhaseEngine()
        assert engine._has_code_block("<code>c</code>") is True
        assert engine._has_code_block("plain") is False
        text = "A\n```\ncode\n```\nB\n<code>x</code>\nC"
        result = engine._remove_code_blocks(text)
        assert "code" not in result
        assert "x" not in result


class TestModelRunnerValidationIntegration:

    def _make_runner(self):
        from ai_agent.external_integration.model_runner import ModelRunner, TaskType
        return ModelRunner(provider="test", model="test"), TaskType

    def test_phase2_accepts_markdown(self):
        runner, TT = self._make_runner()
        assert runner._validate_output_format("```\nls\n```", TT.PHASE2_ACTION_GENERATION)[0] is True

    def test_phase2_accepts_xml(self):
        runner, TT = self._make_runner()
        assert runner._validate_output_format("<code>\nls\n</code>", TT.PHASE2_ACTION_GENERATION)[0] is True

    def test_phase2_accepts_bbcode(self):
        runner, TT = self._make_runner()
        assert runner._validate_output_format("[code]\nls\n[/code]", TT.PHASE2_ACTION_GENERATION)[0] is True

    def test_phase2_accepts_custom(self):
        runner, TT = self._make_runner()
        assert runner._validate_output_format("---code---\nls\n---end-code---", TT.PHASE2_ACTION_GENERATION)[0] is True

    def test_phase2_accepts_html(self):
        runner, TT = self._make_runner()
        assert runner._validate_output_format("<pre><code>\nls\n</code></pre>", TT.PHASE2_ACTION_GENERATION)[0] is True

    def test_phase2_rejects_no_block(self):
        runner, TT = self._make_runner()
        assert runner._validate_output_format("just run ls", TT.PHASE2_ACTION_GENERATION)[0] is False

    def test_phase6_rejects_all_formats(self):
        runner, TT = self._make_runner()
        for text in ["```\nbad\n```", "<code>bad</code>", "[code]bad[/code]",
                     "---code---\nbad\n---end-code---", "<pre><code>bad</code></pre>"]:
            assert runner._validate_output_format(text, TT.PHASE6_SUMMARIZATION)[0] is False


class TestCommandParserIntegration:

    def test_markdown_cleanup(self):
        from ai_agent.core_processing.command_parser import CommandParser
        parser = CommandParser()
        result = parser._clean_command_text("```bash\nls -la\n```")
        assert result is not None

    def test_xml_cleanup(self):
        from ai_agent.core_processing.command_parser import CommandParser
        parser = CommandParser()
        result = parser._clean_command_text('<code>ls -la</code>')
        assert result is not None

    def test_bbcode_cleanup(self):
        from ai_agent.core_processing.command_parser import CommandParser
        parser = CommandParser()
        result = parser._clean_command_text('[code]ls -la[/code]')
        assert result is not None