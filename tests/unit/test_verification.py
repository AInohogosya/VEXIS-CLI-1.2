"""
Unit tests for Verification-First Execution Layer

Tests the probe registry, individual probes, verification executor,
and telemetry logging.
"""

import os
import tempfile
import time
from pathlib import Path

import pytest

from src.ai_agent.core_processing.verification import (
    ProbeRegistry,
    ProbeResult,
    ProbeStatus,
    VerificationResult,
    FileExistenceProbe,
    SyntaxCheckProbe,
    CommandParseProbe,
    VerificationExecutor,
    VerificationTelemetry,
)


class TestProbeResult:
    """Test ProbeResult dataclass"""

    def test_should_block_on_failed(self):
        result = ProbeResult(
            probe_name="test",
            status=ProbeStatus.FAILED,
            message="File not found",
            duration_ms=1.0,
            command="cat missing.txt",
        )
        assert result.should_block is True

    def test_should_not_block_on_passed(self):
        result = ProbeResult(
            probe_name="test",
            status=ProbeStatus.PASSED,
            message="OK",
            duration_ms=1.0,
            command="cat file.txt",
        )
        assert result.should_block is False

    def test_should_not_block_on_skipped(self):
        result = ProbeResult(
            probe_name="test",
            status=ProbeStatus.SKIPPED,
            message="Skipped",
            duration_ms=0,
            command="echo hello",
        )
        assert result.should_block is False


class TestVerificationResult:
    """Test VerificationResult dataclass"""

    def test_all_passed_when_no_failures(self):
        results = [
            ProbeResult("p1", ProbeStatus.PASSED, "OK", 1.0, "cmd"),
            ProbeResult("p2", ProbeStatus.PASSED, "OK", 1.0, "cmd"),
        ]
        vr = VerificationResult(
            command="cmd", results=results, total_duration_ms=2.0, blocked=False
        )
        assert vr.all_passed is True

    def test_not_all_passed_when_blocked(self):
        results = [
            ProbeResult("p1", ProbeStatus.FAILED, "Error", 1.0, "cmd"),
        ]
        vr = VerificationResult(
            command="cmd",
            results=results,
            total_duration_ms=1.0,
            blocked=True,
            blocking_result=results[0],
        )
        assert vr.all_passed is False


class TestProbeRegistry:
    """Test ProbeRegistry singleton"""

    def setup_method(self):
        """Reset registry before each test"""
        registry = ProbeRegistry()
        registry.reset()

    def test_singleton_pattern(self):
        r1 = ProbeRegistry()
        r2 = ProbeRegistry()
        assert r1 is r2

    def test_default_probes_registered(self):
        registry = ProbeRegistry()
        assert registry.count == 3
        assert "file_existence" in registry
        assert "syntax_check" in registry
        assert "command_parse" in registry

    def test_register_custom_probe(self):
        registry = ProbeRegistry()

        class CustomProbe(CommandParseProbe):
            @property
            def name(self):
                return "custom_test"

        registry.register(CustomProbe())
        assert "custom_test" in registry
        assert registry.count == 4

    def test_unregister_probe(self):
        registry = ProbeRegistry()
        removed = registry.unregister("file_existence")
        assert removed is not None
        assert "file_existence" not in registry
        assert registry.count == 2

    def test_get_applicable_probes(self):
        registry = ProbeRegistry()
        probes = registry.get_applicable("cat file.txt")
        probe_names = [p.name for p in probes]
        assert "file_existence" in probe_names
        assert "command_parse" in probe_names

    def test_list_probes(self):
        registry = ProbeRegistry()
        probes = registry.list_probes()
        assert len(probes) == 3
        names = [p["name"] for p in probes]
        assert "file_existence" in names
        assert "syntax_check" in names
        assert "command_parse" in names


class TestFileExistenceProbe:
    """Test FileExistenceProbe"""

    def setup_method(self):
        self.probe = FileExistenceProbe()
        self.tmpdir = tempfile.mkdtemp()
        self.existing_file = os.path.join(self.tmpdir, "test.txt")
        with open(self.existing_file, "w") as f:
            f.write("test content")

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_applies_to_cat_command(self):
        assert self.probe.applies_to("cat file.txt") is True

    def test_applies_to_python_command(self):
        assert self.probe.applies_to("python script.py") is True

    def test_applies_to_node_command(self):
        assert self.probe.applies_to("node app.js") is True

    def test_does_not_apply_to_echo(self):
        assert self.probe.applies_to("echo hello") is False

    def test_does_not_apply_to_empty(self):
        assert self.probe.applies_to("") is False

    def test_passes_for_existing_file(self):
        result = self.probe.execute(f"cat {self.existing_file}", self.tmpdir)
        assert result.status == ProbeStatus.PASSED
        assert "exist" in result.message

    def test_fails_for_missing_file(self):
        result = self.probe.execute("cat /nonexistent/path/file.txt", self.tmpdir)
        assert result.status == ProbeStatus.FAILED
        assert "not found" in result.message
        assert "/nonexistent/path/file.txt" in result.metadata["missing_files"]

    def test_fails_for_missing_script(self):
        result = self.probe.execute("python missing_script.py", self.tmpdir)
        assert result.status == ProbeStatus.FAILED
        assert "missing_script.py" in result.message

    def test_passes_for_pytest_with_existing_file(self):
        result = self.probe.execute(f"pytest {self.existing_file}", self.tmpdir)
        assert result.status == ProbeStatus.PASSED

    def test_fails_for_pytest_with_missing_file(self):
        result = self.probe.execute("pytest tests/missing_test.py", self.tmpdir)
        assert result.status == ProbeStatus.FAILED

    def test_resolves_relative_paths(self):
        result = self.probe.execute("cat test.txt", self.tmpdir)
        assert result.status == ProbeStatus.PASSED

    def test_handles_multiple_files(self):
        second_file = os.path.join(self.tmpdir, "test2.txt")
        with open(second_file, "w") as f:
            f.write("content")
        result = self.probe.execute(f"cp {self.existing_file} {second_file}", self.tmpdir)
        assert result.status == ProbeStatus.PASSED

    def test_flags_missing_in_multiple_files(self):
        result = self.probe.execute(
            f"cp {self.existing_file} /nonexistent/file.txt", self.tmpdir
        )
        assert result.status == ProbeStatus.FAILED
        assert "/nonexistent/file.txt" in result.metadata["missing_files"]


class TestSyntaxCheckProbe:
    """Test SyntaxCheckProbe"""

    def setup_method(self):
        self.probe = SyntaxCheckProbe()
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_file(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_applies_to_python_file(self):
        assert self.probe.applies_to("python script.py") is True

    def test_applies_to_json_file(self):
        assert self.probe.applies_to("cat config.json") is True

    def test_does_not_apply_to_plain_text(self):
        assert self.probe.applies_to("echo hello") is False

    def test_python_syntax_valid(self):
        path = self._write_file("valid.py", "x = 1\nprint(x)\n")
        result = self.probe.execute(f"python {path}", self.tmpdir)
        assert result.status == ProbeStatus.PASSED

    def test_python_syntax_invalid(self):
        path = self._write_file("invalid.py", "x = 1\nprint(\n")
        result = self.probe.execute(f"python {path}", self.tmpdir)
        assert result.status == ProbeStatus.FAILED
        assert "syntax" in result.message.lower() or "SyntaxError" in result.message

    def test_json_syntax_valid(self):
        path = self._write_file("valid.json", '{"key": "value"}')
        result = self.probe.execute(f"cat {path}", self.tmpdir)
        assert result.status == ProbeStatus.PASSED

    def test_json_syntax_invalid(self):
        path = self._write_file("invalid.json", '{"key": value}')
        result = self.probe.execute(f"cat {path}", self.tmpdir)
        assert result.status == ProbeStatus.FAILED

    def test_skips_nonexistent_file(self):
        result = self.probe.execute("python nonexistent.py", self.tmpdir)
        assert result.status == ProbeStatus.SKIPPED

    def test_yaml_syntax_valid(self):
        path = self._write_file("valid.yaml", "key: value\n")
        result = self.probe.execute(f"cat {path}", self.tmpdir)
        assert result.status in (ProbeStatus.PASSED, ProbeStatus.SKIPPED)

    def test_shell_syntax_valid(self):
        path = self._write_file("valid.sh", "#!/bin/bash\necho hello\n")
        result = self.probe.execute(f"bash {path}", self.tmpdir)
        assert result.status in (ProbeStatus.PASSED, ProbeStatus.SKIPPED)


class TestCommandParseProbe:
    """Test CommandParseProbe"""

    def setup_method(self):
        self.probe = CommandParseProbe()

    def test_applies_to_any_command(self):
        assert self.probe.applies_to("ls -la") is True

    def test_does_not_apply_to_empty(self):
        assert self.probe.applies_to("") is False

    def test_does_not_apply_to_whitespace(self):
        assert self.probe.applies_to("   ") is False

    def test_passes_for_valid_command(self):
        result = self.probe.execute("ls -la /tmp", "/tmp")
        assert result.status == ProbeStatus.PASSED
        assert "parsed successfully" in result.message

    def test_fails_for_unbalanced_quotes(self):
        result = self.probe.execute('echo "hello', "/tmp")
        assert result.status == ProbeStatus.FAILED
        assert "parse" in result.message.lower()

    def test_handles_complex_command(self):
        result = self.probe.execute(
            "grep -r 'pattern' /path --include='*.py'", "/tmp"
        )
        assert result.status == ProbeStatus.PASSED


class TestVerificationExecutor:
    """Test VerificationExecutor"""

    def setup_method(self):
        self.registry = ProbeRegistry()
        self.registry.reset()
        self.telemetry = VerificationTelemetry(enabled=False)
        self.executor = VerificationExecutor(
            registry=self.registry,
            telemetry=self.telemetry,
            enabled=True,
        )
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_verify_passes_for_safe_command(self):
        result = self.executor.verify("echo hello", self.tmpdir)
        assert result.blocked is False

    def test_verify_blocks_missing_file(self):
        result = self.executor.verify("cat /nonexistent/file.txt", self.tmpdir)
        assert result.blocked is True
        assert result.blocking_result.probe_name == "file_existence"

    def test_verify_blocks_syntax_error(self):
        path = os.path.join(self.tmpdir, "bad.py")
        with open(path, "w") as f:
            f.write("def foo(\n")
        result = self.executor.verify(f"python {path}", self.tmpdir)
        assert result.blocked is True
        assert result.blocking_result.probe_name == "syntax_check"

    def test_verify_blocks_parse_error(self):
        result = self.executor.verify('echo "unbalanced', self.tmpdir)
        assert result.blocked is True
        assert result.blocking_result.probe_name == "command_parse"

    def test_verify_disabled(self):
        executor = VerificationExecutor(enabled=False)
        result = executor.verify("cat /nonexistent/file.txt", self.tmpdir)
        assert result.blocked is False

    def test_get_blocked_response(self):
        result = self.executor.verify("cat /nonexistent/file.txt", self.tmpdir)
        response = self.executor.get_blocked_response(result)
        assert response["blocked"] is True
        assert response["success"] is False
        assert "VERIFICATION BLOCKED" in response["stderr"]
        assert "verification" in response

    def test_get_blocked_response_for_passed(self):
        result = self.executor.verify("echo hello", self.tmpdir)
        response = self.executor.get_blocked_response(result)
        assert response["blocked"] is False

    def test_verify_batch(self):
        results = self.executor.verify_batch(
            ["echo hello", "cat /nonexistent/file.txt", "ls -la"],
            self.tmpdir,
        )
        assert len(results) == 3
        assert results[0].blocked is False
        assert results[1].blocked is True
        assert results[2].blocked is False

    def test_short_circuits_on_first_failure(self):
        path = os.path.join(self.tmpdir, "bad.py")
        with open(path, "w") as f:
            f.write("def foo(\n")
        result = self.executor.verify(f"python {path}", self.tmpdir)
        assert result.blocked is True
        assert len(result.results) >= 1

    def test_suggestion_for_file_existence(self):
        result = self.executor.verify("cat /nonexistent/file.txt", self.tmpdir)
        response = self.executor.get_blocked_response(result)
        suggestion = response["verification"]["suggestion"]
        assert "file path" in suggestion.lower() or "check" in suggestion.lower()


class TestVerificationTelemetry:
    """Test VerificationTelemetry"""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.telemetry = VerificationTelemetry(
            log_dir=self.tmpdir, enabled=True
        )

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_result(self, command, blocked, probe_name="", reason=""):
        results = []
        blocking = None
        if blocked:
            blocking = ProbeResult(
                probe_name=probe_name,
                status=ProbeStatus.FAILED,
                message=reason,
                duration_ms=1.0,
                command=command,
            )
            results.append(blocking)
        return VerificationResult(
            command=command,
            results=results,
            total_duration_ms=1.0,
            blocked=blocked,
            blocking_result=blocking,
        )

    def test_log_blocked_verification(self):
        result = self._make_result(
            "cat missing.txt", True, "file_existence", "File not found"
        )
        self.telemetry.log_verification(result)
        stats = self.telemetry.get_stats()
        assert stats.total_verifications == 1
        assert stats.total_blocked == 1
        assert stats.total_passed == 0

    def test_log_passed_verification(self):
        result = self._make_result("echo hello", False)
        self.telemetry.log_verification(result)
        stats = self.telemetry.get_stats()
        assert stats.total_verifications == 1
        assert stats.total_passed == 1
        assert stats.total_blocked == 0

    def test_block_rate_calculation(self):
        for _ in range(3):
            self.telemetry.log_verification(
                self._make_result("cat missing.txt", True, "file_existence", "x")
            )
        for _ in range(7):
            self.telemetry.log_verification(self._make_result("echo hello", False))
        stats = self.telemetry.get_stats()
        assert stats.block_rate == 30.0

    def test_estimated_tokens_saved(self):
        result = self._make_result(
            "cat missing.txt", True, "file_existence", "File not found"
        )
        self.telemetry.log_verification(result)
        stats = self.telemetry.get_stats()
        assert stats.estimated_tokens_saved > 0

    def test_blocks_by_probe(self):
        self.telemetry.log_verification(
            self._make_result("cat missing.txt", True, "file_existence", "x")
        )
        self.telemetry.log_verification(
            self._make_result("python bad.py", True, "syntax_check", "x")
        )
        self.telemetry.log_verification(
            self._make_result("cat missing2.txt", True, "file_existence", "x")
        )
        stats = self.telemetry.get_stats()
        assert stats.blocks_by_probe["file_existence"] == 2
        assert stats.blocks_by_probe["syntax_check"] == 1

    def test_reset(self):
        self.telemetry.log_verification(
            self._make_result("cat missing.txt", True, "file_existence", "x")
        )
        self.telemetry.reset()
        stats = self.telemetry.get_stats()
        assert stats.total_verifications == 0

    def test_generate_report(self):
        self.telemetry.log_verification(
            self._make_result("cat missing.txt", True, "file_existence", "x")
        )
        report = self.telemetry.generate_report()
        assert "VERIFICATION TELEMETRY REPORT" in report
        assert "Total Verifications" in report

    def test_disabled_telemetry(self):
        telemetry = VerificationTelemetry(enabled=False)
        result = self._make_result(
            "cat missing.txt", True, "file_existence", "x"
        )
        telemetry.log_verification(result)
        stats = telemetry.get_stats()
        assert stats.total_verifications == 0


class TestProbePerformance:
    """Test that probes meet the <50ms latency target"""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.file_probe = FileExistenceProbe()
        self.syntax_probe = SyntaxCheckProbe()
        self.parse_probe = CommandParseProbe()

        self.existing_file = os.path.join(self.tmpdir, "test.txt")
        with open(self.existing_file, "w") as f:
            f.write("test content")

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_file_existence_probe_latency(self):
        start = time.monotonic()
        self.file_probe.execute(f"cat {self.existing_file}", self.tmpdir)
        duration_ms = (time.monotonic() - start) * 1000
        assert duration_ms < 50, f"FileExistenceProbe took {duration_ms:.1f}ms (target: <50ms)"

    def test_command_parse_probe_latency(self):
        start = time.monotonic()
        self.parse_probe.execute("ls -la /tmp", self.tmpdir)
        duration_ms = (time.monotonic() - start) * 1000
        assert duration_ms < 50, f"CommandParseProbe took {duration_ms:.1f}ms (target: <50ms)"

    def test_syntax_probe_skips_nonexistent(self):
        start = time.monotonic()
        self.syntax_probe.execute("python nonexistent.py", self.tmpdir)
        duration_ms = (time.monotonic() - start) * 1000
        assert duration_ms < 50, f"SyntaxCheckProbe took {duration_ms:.1f}ms (target: <50ms)"


class TestIntegration:
    """Integration tests for the full verification pipeline"""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.registry = ProbeRegistry()
        self.registry.reset()
        self.telemetry = VerificationTelemetry(
            log_dir=os.path.join(self.tmpdir, "telemetry"), enabled=True
        )
        self.executor = VerificationExecutor(
            registry=self.registry,
            telemetry=self.telemetry,
            enabled=True,
        )

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_full_pipeline_blocks_missing_file(self):
        result = self.executor.verify(
            "python /nonexistent/script.py", self.tmpdir
        )
        assert result.blocked is True
        assert result.blocking_result.probe_name == "file_existence"

        response = self.executor.get_blocked_response(result)
        assert response["success"] is False
        assert "VERIFICATION BLOCKED" in response["stderr"]

        stats = self.telemetry.get_stats()
        assert stats.total_blocked == 1

    def test_full_pipeline_blocks_syntax_error(self):
        bad_py = os.path.join(self.tmpdir, "bad.py")
        with open(bad_py, "w") as f:
            f.write("def broken(\n")

        result = self.executor.verify(f"python {bad_py}", self.tmpdir)
        assert result.blocked is True
        assert result.blocking_result.probe_name == "syntax_check"

    def test_full_pipeline_allows_valid_command(self):
        good_py = os.path.join(self.tmpdir, "good.py")
        with open(good_py, "w") as f:
            f.write("print('hello')\n")

        result = self.executor.verify(f"python {good_py}", self.tmpdir)
        assert result.blocked is False

        stats = self.telemetry.get_stats()
        assert stats.total_passed == 1

    def test_batch_verification_stops_at_first_failure(self):
        results = self.executor.verify_batch(
            [
                "echo safe",
                "python /nonexistent/script.py",
                "echo never reached",
            ],
            self.tmpdir,
        )
        assert results[0].blocked is False
        assert results[1].blocked is True
        assert results[2].blocked is False

    def test_multiple_probes_can_apply(self):
        bad_py = os.path.join(self.tmpdir, "bad.py")
        with open(bad_py, "w") as f:
            f.write("def broken(\n")

        result = self.executor.verify(f"python {bad_py}", self.tmpdir)
        assert result.blocked is True
        assert len(result.results) >= 1
