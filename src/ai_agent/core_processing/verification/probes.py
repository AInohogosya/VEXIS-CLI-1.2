"""
Verification Probes for Pre-Flight Command Validation

Probes are lightweight, deterministic checks that run before expensive commands
to fail fast on predictable errors. Target latency: <50ms per probe.
"""

import ast
import os
import re
import shlex
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ...utils.logger import get_logger


class ProbeStatus(Enum):
    """Status of a probe execution"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ProbeResult:
    """Result of a single probe execution"""
    probe_name: str
    status: ProbeStatus
    message: str
    duration_ms: float
    command: str
    metadata: Dict[str, any] = field(default_factory=dict)

    @property
    def should_block(self) -> bool:
        """Whether this result should block command execution"""
        return self.status == ProbeStatus.FAILED


@dataclass
class VerificationResult:
    """Aggregated result from all probes for a command"""
    command: str
    results: List[ProbeResult]
    total_duration_ms: float
    blocked: bool
    blocking_result: Optional[ProbeResult] = None

    @property
    def all_passed(self) -> bool:
        return not self.blocked and all(
            r.status in (ProbeStatus.PASSED, ProbeStatus.SKIPPED) for r in self.results
        )


class Probe(ABC):
    """Base class for all verification probes"""

    def __init__(self):
        self.logger = get_logger(f"verification.probe.{self.name}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this probe"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this probe checks"""
        pass

    @abstractmethod
    def applies_to(self, command: str) -> bool:
        """Check if this probe should run for the given command"""
        pass

    @abstractmethod
    def execute(self, command: str, cwd: str) -> ProbeResult:
        """Execute the probe check"""
        pass

    def _timed_execute(self, command: str, cwd: str) -> ProbeResult:
        """Wrapper to time probe execution"""
        start = time.monotonic()
        try:
            result = self.execute(command, cwd)
        except Exception as e:
            duration_ms = (time.monotonic() - start) * 1000
            self.logger.error(f"Probe {self.name} raised exception: {e}")
            result = ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.ERROR,
                message=f"Probe error: {e}",
                duration_ms=duration_ms,
                command=command,
            )
        else:
            duration_ms = (time.monotonic() - start) * 1000
            result.duration_ms = duration_ms

        if duration_ms > 50:
            self.logger.warning(
                f"Probe {self.name} exceeded 50ms target: {duration_ms:.1f}ms",
                duration_ms=duration_ms,
            )

        return result


class FileExistenceProbe(Probe):
    """
    Verifies that files referenced in commands exist before execution.

    Extracts file paths from common command patterns:
    - Direct file references: cat, ls, rm, cp, mv, etc.
    - Test file references: npm test <file>, pytest <file>, etc.
    - Build references: make -f <file>, docker build -f <file>, etc.
    - Script execution: python <file>, node <file>, bash <file>, etc.
    """

    COMMANDS_WITH_FILE_ARGS = {
        "cat", "ls", "rm", "cp", "mv", "touch", "chmod", "chown",
        "head", "tail", "less", "more", "grep", "sed", "awk",
        "diff", "wc", "sort", "uniq", "cut", "tr",
        "tar", "zip", "unzip", "gzip", "gunzip",
        "curl", "wget",
        "git",
    }

    COMMANDS_WITH_FLAGGED_FILES = {
        "make": {"-f", "--file"},
        "docker": {"-f", "--file"},
        "gcc": {"-o"},
        "g++": {"-o"},
        "javac": {"-d", "-cp", "--class-path"},
        "python": {"-c"},
        "python3": {"-c"},
        "node": {"-e", "--eval"},
        "npm": {"--prefix"},
        "npx": {"--prefix"},
        "pytest": {"-c", "--confcutdir"},
        "mypy": {"--config-file"},
        "black": {"--config"},
        "flake8": {"--config"},
        "eslint": {"--config"},
        "prettier": {"--config"},
        "tsc": {"--project", "-p"},
    }

    SCRIPT_EXECUTION_COMMANDS = {
        "python", "python3", "python2",
        "node", "nodejs",
        "bash", "sh", "zsh", "fish",
        "ruby", "perl", "php",
        "java",
        "go",
    }

    TEST_COMMANDS = {
        "npm": {"test", "t", "run"},
        "npx": {"test"},
        "pytest": set(),
        "mocha": set(),
        "jest": set(),
        "vitest": set(),
        "cargo": {"test"},
        "go": {"test"},
    }

    SHELL_OPERATORS = {"&", "&&", "||", ">", ">>", "<", "<<", ";", "2>", "&>"}

    @property
    def name(self) -> str:
        return "file_existence"

    @property
    def description(self) -> str:
        return "Verifies referenced files exist before command execution"

    def applies_to(self, command: str) -> bool:
        """Check if command references any file paths"""
        stripped = command.strip()
        if not stripped:
            return False

        try:
            parts = shlex.split(stripped)
        except ValueError:
            return False

        if not parts:
            return False

        base_cmd = parts[0]

        if base_cmd in self.COMMANDS_WITH_FILE_ARGS:
            return len(parts) > 1

        if base_cmd in self.SCRIPT_EXECUTION_COMMANDS:
            return len(parts) > 1

        if base_cmd in self.COMMANDS_WITH_FLAGGED_FILES:
            return True

        if base_cmd in self.TEST_COMMANDS:
            return True

        return False

    def execute(self, command: str, cwd: str) -> ProbeResult:
        """Check that all referenced files exist"""
        try:
            parts = shlex.split(command.strip())
        except ValueError as e:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.FAILED,
                message=f"Failed to parse command: {e}",
                duration_ms=0,
                command=command,
            )

        base_cmd = parts[0]
        missing_files = []
        checked_files = []

        files_to_check = self._extract_file_paths(parts, base_cmd, cwd)

        for file_path in files_to_check:
            checked_files.append(file_path)
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        if missing_files:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.FAILED,
                message=f"File(s) not found: {', '.join(missing_files)}",
                duration_ms=0,
                command=command,
                metadata={
                    "missing_files": missing_files,
                    "checked_files": checked_files,
                },
            )

        return ProbeResult(
            probe_name=self.name,
            status=ProbeStatus.PASSED,
            message=f"All {len(checked_files)} referenced file(s) exist",
            duration_ms=0,
            command=command,
            metadata={"checked_files": checked_files},
        )

    def _extract_file_paths(self, parts: List[str], base_cmd: str, cwd: str) -> List[str]:
        """Extract file paths from command parts"""
        files = []

        if base_cmd in self.SCRIPT_EXECUTION_COMMANDS:
            skip_next = False
            for part in parts[1:]:
                if skip_next:
                    skip_next = False
                    continue
                if part.startswith("-"):
                    if part in ("-c", "-e", "-m", "--eval"):
                        skip_next = True
                    continue
                if part in self.SHELL_OPERATORS:
                    continue
                resolved = self._resolve_path(part, cwd)
                files.append(resolved)
                break

        elif base_cmd in self.TEST_COMMANDS:
            subcommands = self.TEST_COMMANDS[base_cmd]
            if not subcommands:
                for part in parts[1:]:
                    if part.startswith("-"):
                        continue
                    if part in self.SHELL_OPERATORS:
                        continue
                    if not part.startswith(".") and "/" not in part and "\\" not in part:
                        continue
                    resolved = self._resolve_path(part, cwd)
                    files.append(resolved)
            else:
                for i, part in enumerate(parts[1:], 1):
                    if part in subcommands:
                        for j in range(i + 1, len(parts)):
                            candidate = parts[j]
                            if candidate.startswith("-"):
                                continue
                            if candidate in self.SHELL_OPERATORS:
                                continue
                            resolved = self._resolve_path(candidate, cwd)
                            files.append(resolved)

        elif base_cmd in self.COMMANDS_WITH_FLAGGED_FILES:
            flags = self.COMMANDS_WITH_FLAGGED_FILES[base_cmd]
            for i, part in enumerate(parts[1:], 1):
                if part in flags and i + 1 < len(parts):
                    resolved = self._resolve_path(parts[i + 1], cwd)
                    files.append(resolved)

        elif base_cmd in self.COMMANDS_WITH_FILE_ARGS:
            for part in parts[1:]:
                if part.startswith("-"):
                    continue
                if part in self.SHELL_OPERATORS:
                    continue
                resolved = self._resolve_path(part, cwd)
                files.append(resolved)

        return files

    def _resolve_path(self, path: str, cwd: str) -> str:
        """Resolve a potentially relative path against cwd"""
        if os.path.isabs(path):
            return path
        return os.path.join(cwd, path)


class SyntaxCheckProbe(Probe):
    """
    Performs fast syntax validation for supported file types before
    executing commands that would invoke a full compiler/interpreter.

    Supported languages:
    - Python (.py) - using ast.parse
    - JavaScript (.js, .mjs, .cjs) - using node --check
    - TypeScript (.ts, .tsx) - using tsc --noEmit (if available)
    - JSON (.json) - using json.loads
    - YAML (.yaml, .yml) - using yaml.safe_load
    - Shell scripts (.sh, .bash) - using bash -n
    - Dockerfile - using dockerfile-parse (if available)
    """

    PYTHON_EXTENSIONS = {".py", ".pyw", ".pyi"}
    JAVASCRIPT_EXTENSIONS = {".js", ".mjs", ".cjs", ".jsx"}
    TYPESCRIPT_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts"}
    JSON_EXTENSIONS = {".json"}
    YAML_EXTENSIONS = {".yaml", ".yml"}
    SHELL_EXTENSIONS = {".sh", ".bash", ".zsh", ".ksh"}

    @property
    def name(self) -> str:
        return "syntax_check"

    @property
    def description(self) -> str:
        return "Performs fast syntax validation for supported file types"

    def applies_to(self, command: str) -> bool:
        """Check if command references a file with a supported extension"""
        stripped = command.strip()
        if not stripped:
            return False

        try:
            parts = shlex.split(stripped)
        except ValueError:
            return False

        for part in parts:
            if part.startswith("-"):
                continue
            ext = os.path.splitext(part)[1].lower()
            if ext in self.PYTHON_EXTENSIONS:
                return True
            if ext in self.JAVASCRIPT_EXTENSIONS:
                return True
            if ext in self.TYPESCRIPT_EXTENSIONS:
                return True
            if ext in self.JSON_EXTENSIONS:
                return True
            if ext in self.YAML_EXTENSIONS:
                return True
            if ext in self.SHELL_EXTENSIONS:
                return True
            if part.endswith("Dockerfile") or part == "Dockerfile":
                return True

        return False

    def execute(self, command: str, cwd: str) -> ProbeResult:
        """Run syntax check on referenced files"""
        try:
            parts = shlex.split(command.strip())
        except ValueError as e:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.FAILED,
                message=f"Failed to parse command: {e}",
                duration_ms=0,
                command=command,
            )

        files_to_check = []
        for part in parts:
            if part.startswith("-"):
                continue
            resolved = self._resolve_path(part, cwd)
            if os.path.exists(resolved):
                files_to_check.append(resolved)

        if not files_to_check:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.SKIPPED,
                message="No existing files to check syntax for",
                duration_ms=0,
                command=command,
            )

        errors = []
        for file_path in files_to_check:
            ext = os.path.splitext(file_path)[1].lower()
            basename = os.path.basename(file_path)

            try:
                if ext in self.PYTHON_EXTENSIONS:
                    error = self._check_python_syntax(file_path)
                elif ext in self.JAVASCRIPT_EXTENSIONS:
                    error = self._check_javascript_syntax(file_path)
                elif ext in self.TYPESCRIPT_EXTENSIONS:
                    error = self._check_typescript_syntax(file_path)
                elif ext in self.JSON_EXTENSIONS:
                    error = self._check_json_syntax(file_path)
                elif ext in self.YAML_EXTENSIONS:
                    error = self._check_yaml_syntax(file_path)
                elif ext in self.SHELL_EXTENSIONS:
                    error = self._check_shell_syntax(file_path)
                elif basename == "Dockerfile" or basename.endswith("Dockerfile"):
                    error = self._check_dockerfile_syntax(file_path)
                else:
                    continue

                if error:
                    errors.append(f"{file_path}: {error}")

            except Exception as e:
                errors.append(f"{file_path}: Unexpected error during syntax check: {e}")

        if errors:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.FAILED,
                message=f"Syntax error(s) found: {'; '.join(errors)}",
                duration_ms=0,
                command=command,
                metadata={"syntax_errors": errors},
            )

        return ProbeResult(
            probe_name=self.name,
            status=ProbeStatus.PASSED,
            message=f"Syntax check passed for {len(files_to_check)} file(s)",
            duration_ms=0,
            command=command,
            metadata={"checked_files": files_to_check},
        )

    def _resolve_path(self, path: str, cwd: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.join(cwd, path)

    def _check_python_syntax(self, file_path: str) -> Optional[str]:
        """Check Python syntax using ast.parse"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
            ast.parse(source, filename=file_path)
            return None
        except SyntaxError as e:
            return f"Line {e.lineno}: {e.msg}"

    def _check_javascript_syntax(self, file_path: str) -> Optional[str]:
        """Check JavaScript syntax using node --check"""
        try:
            result = subprocess.run(
                ["node", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return result.stderr.strip().split("\n")[0] if result.stderr.strip() else "Syntax error"
            return None
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return None

    def _check_typescript_syntax(self, file_path: str) -> Optional[str]:
        """Check TypeScript syntax using tsc --noEmit"""
        try:
            result = subprocess.run(
                ["tsc", "--noEmit", "--skipLibCheck", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                first_error = result.stdout.strip().split("\n")[0] if result.stdout.strip() else ""
                return first_error if first_error else "TypeScript compilation error"
            return None
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return None

    def _check_json_syntax(self, file_path: str) -> Optional[str]:
        """Check JSON syntax"""
        import json
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                json.load(f)
            return None
        except json.JSONDecodeError as e:
            return f"Line {e.lineno}: {e.msg}"

    def _check_yaml_syntax(self, file_path: str) -> Optional[str]:
        """Check YAML syntax"""
        try:
            import yaml
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                yaml.safe_load(f)
            return None
        except ImportError:
            return None
        except yaml.YAMLError as e:
            return str(e)

    def _check_shell_syntax(self, file_path: str) -> Optional[str]:
        """Check shell script syntax using bash -n"""
        try:
            result = subprocess.run(
                ["bash", "-n", file_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return result.stderr.strip().split("\n")[0] if result.stderr.strip() else "Shell syntax error"
            return None
        except FileNotFoundError:
            return None
        except subprocess.TimeoutExpired:
            return None

    def _check_dockerfile_syntax(self, file_path: str) -> Optional[str]:
        """Basic Dockerfile syntax check"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            valid_instructions = {
                "FROM", "RUN", "CMD", "LABEL", "MAINTAINER", "EXPOSE",
                "ENV", "ADD", "COPY", "ENTRYPOINT", "VOLUME", "USER",
                "WORKDIR", "ARG", "ONBUILD", "STOPSIGNAL", "HEALTHCHECK",
                "SHELL",
            }

            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts = stripped.split()
                if parts and parts[0].upper() not in valid_instructions:
                    if not parts[0].startswith("#"):
                        return f"Line {i}: Unknown instruction '{parts[0]}'"

            return None
        except Exception as e:
            return str(e)


class CommandParseProbe(Probe):
    """
    Validates that a command can be properly parsed and is structurally sound
    before attempting execution. Catches common issues like:
    - Unbalanced quotes
    - Invalid escape sequences
    - Empty commands after parsing
    """

    @property
    def name(self) -> str:
        return "command_parse"

    @property
    def description(self) -> str:
        return "Validates command can be properly parsed"

    def applies_to(self, command: str) -> bool:
        """Always applies to any non-empty command"""
        return bool(command and command.strip())

    def execute(self, command: str, cwd: str) -> ProbeResult:
        """Validate command parsing"""
        stripped = command.strip()

        if not stripped:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.FAILED,
                message="Empty command",
                duration_ms=0,
                command=command,
            )

        try:
            parts = shlex.split(stripped)
        except ValueError as e:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.FAILED,
                message=f"Parse error: {e}",
                duration_ms=0,
                command=command,
            )

        if not parts:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.FAILED,
                message="Command parsed to empty argument list",
                duration_ms=0,
                command=command,
            )

        return ProbeResult(
            probe_name=self.name,
            status=ProbeStatus.PASSED,
            message=f"Command parsed successfully ({len(parts)} parts)",
            duration_ms=0,
            command=command,
            metadata={"parsed_parts": parts},
        )
