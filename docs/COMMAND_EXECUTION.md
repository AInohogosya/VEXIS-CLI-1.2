# Command Execution

VEXIS-CLI's command execution path is intentionally deterministic after the model generates a command block. The model proposes commands in Phase 2; Phase 3 parses and executes them without another LLM call.

## Phase 2 Output Contract

The action-generation prompt requires the model to output:

- Exactly one Markdown code block.
- ` ```vexis ` blocks are also supported and are recommended when mixing shell and native agent commands.
- Complete commands that can be executed as-is.
- No placeholders such as `<file>` or incomplete variables.
- No explanatory text outside the code block.
- Optional comments inside the code block.

The `ModelRunner` validates that Phase 2 output contains a code block.

## Native Action Formats

Phase 3 recognizes several native action formats that are handled programmatically without shell execution:

| Action | Format | Behavior |
| --- | --- | --- |
| `read_file` | `read_file("path/to/file")` | Reads and returns file contents. Validates path against sensitive directories. |
| `search` | `search("pattern", "path")` | Searches file contents under `path` for `pattern` (read-only). `path` defaults to the current directory. |
| `list_files` | `list_files("path")` | Lists files and directories under `path` (read-only). Add `"recursive"` to list the whole subtree. |
| `write_file` | `write_file("path/to/file")` | Writes subsequent content lines to a file. Creates the file if it doesn't exist; applies diff-based edit if it does. |
| `keep_text` | `keep_text("content")` | Stores text in pipeline memory records (excluded from context compression). |
| `keep_file` | `keep_file("path/to/file")` | Stores a file snapshot in pipeline memory records (excluded from context compression). |
| `str_replace` | `<str_replace><path>file</path><old>original code</old><new>replacement code</new></str_replace>` | Targeted text replacement in existing files. The old text must match exactly. |
| `hack` | `hack("custom command")` | Logs a custom command placeholder without executing it. |

### Str_replace Format

The `<str_replace>` block provides a reliable way to edit existing files:

```xml
<str_replace>
<path>path/to/file.py</path>
<old>
[the exact existing code to replace — must match verbatim]
</old>
<new>
[the new code to insert]
</new>
</str_replace>
```

This approach avoids sed/awk edge cases and preserves file encoding.

### Coding Task Guidance

When the engine detects a coding task (based on keywords like "write", "edit", "modify", "implement"), it injects additional guidance:

1. Always `read_file()` before modifying an existing file.
2. Prefer `str_replace` over `write_file` or shell commands for editing.
3. Don't use sed/awk/perl one-liners.
4. Don't output entire file contents — use targeted replacements.

## Programmatic Parsing

`FivePhaseEngine._parse_commands()` extracts executable commands from the Phase 2 Markdown content. Separately, `command_parser.py` parses VEXIS-specific command text into structured `ParsedCommand` values.

VEXIS command concepts include:

| Concept | Meaning |
| --- | --- |
| CLI command / SHELL | A shell command intended for local execution. |
| VEXIS-prefixed command | A typed command inside ` ```vexis ` such as `SHELL:`, `READ_FILE:`, `WRITE_FILE:`, `KEEP_TEXT:`, `KEEP_FILE:`, `STR_REPLACE:`, `HACK:`. |
| Native action | Function-call style commands like `read_file()`, `write_file()`, `keep_text()`, `keep_file()`. |
| End command | A signal that work is complete. |
| Regenerate step | A signal to regenerate or replace a step. |

The code avoids LLM-based command extraction in Phase 3 to make execution more predictable and auditable.

## Terminal History

`TerminalHistory` is the command execution and log system. It is responsible for:

- Recording terminal entries with type, command, output, error text, return code, timestamp, duration, and metadata.
- Executing individual commands.
- Executing batches of commands.
- Rendering terminal logs for Phase 4 and Phase 5.
- Enforcing command timeouts.
- Cancelling the foreground command when a cancellation request arrives.
- Supporting long-running/background command behavior tested by the task lifecycle tests.

Interactive mode also appends terminal outputs and recent terminal logs into conversation history between turns, so context is preserved until the user issues `/reset`.

## Batch Execution

The engine sends all parsed shell commands from a code block to `execute_commands_batch()` with:

- The parsed command list.
- The configured command timeout.
- The current pipeline cancellation event.

Native actions (`read_file`, `write_file`, etc.) are executed before shell commands and their output is prepended to the batch result.

The resulting dictionary is saved in `PipelineContext.last_execution_result` and usually includes:

- `success`
- `stdout`
- `stderr`
- `return_code`
- `failure_classification` (ifCommandFailureClassifier categorization)
- `provenance` (metadata for all writes and commands)
- timing and command metadata where available

## Failure Classification

When a command fails, `CommandFailureClassifier` categorizes the error:

- `COMMAND_NOT_FOUND` — The executable was not found (triggers automatic recovery with package installation).
- `PERMISSION_DENIED` — Insufficient permissions.
- `TIMEOUT` — Command exceeded the configured timeout.
- `VALIDATION_ERROR` — Command output indicates a logic error.
- `RESOURCE_ERROR` — Out of memory, disk space, etc.

Automatic recovery injects an installation step when "command not found" or "permission denied" errors are detected.

## Timeouts

Timeouts exist at several levels:

| Level | Configuration |
| --- | --- |
| Package CLI command timeout | `--command-timeout`; default 600 seconds in `five_phase_app.py`. |
| Package CLI task timeout | `--task-timeout`; parser default is 5400 seconds in `five_phase_app.py`. |
| Config execution command timeout | `execution.command_timeout`; example 1800 seconds. |
| Config execution task timeout | `execution.task_timeout`; example 2700 seconds. |
| Engine fallback defaults | `FivePhaseEngine` constructor defaults to command timeout 1800 and task timeout 7200 when not supplied by caller config. |
| Model request timeout | `ModelRequest.timeout`, validated from 1 to 300 seconds. |

Timeout results are surfaced to Phase 4 and, in Telegram mode, can trigger a timeout notification. The `/KG` command allows resuming a timed-out task with doubled timeout.

## Cancellation

`FivePhaseEngine.request_cancel()` sets the active cancellation event and asks `TerminalHistory` to cancel the current command when supported. Telegram mode uses this to cancel an overlapping task when a user sends a newer request.

Cancellation state is stored in `PipelineContext.cancel_event` and `PipelineContext.cancelled`.

When a task is cancelled by a newer user request, `get_partial_context()` saves completed steps into conversation history so the next task has full context.

## Safety Checks

Command safety is handled by `security.py`:

- `CommandSecurityChecker.check_command()` returns `SecurityCheckResult` with `is_safe`, `requires_confirmation`, `blocked_commands`, `warning_commands`, `masked_output`, and `reason`.
- Blocking is controlled by `SecurityConfig.enable_command_blocking`.
- Confirmation warnings are controlled by `enable_confirmation_prompts`.
- `sudo` warnings are controlled by `enable_sudo_warning`.
- Pipe-to-shell warnings are controlled by `enable_shell_pipe_warning`.
- Empty commands are always unsafe.

## File Path Validation

The engine validates file paths before read/write operations:

- Resolves relative paths to absolute paths.
- Checks against sensitive system directories (`/etc`, `/var`, `/usr`, `/bin`, `/sbin`, `/lib`, `/lib64`, `/opt`, `/sys`, `/proc`, `/dev`, `/boot`, `/root`).
- Verifies parent directory read access.
- Returns descriptive error messages for blocked paths.

## Sensitive Data Masking

`SensitiveDataMasker` masks likely secrets in logs and dictionaries. It is designed to redact:

- API keys.
- Passwords.
- Tokens.
- Secrets.
- AWS access keys.
- GitHub tokens.

Use `mask_sensitive_data(text)` for quick masking.

## Sandboxing

`SandboxManager` detects available sandbox tools in this order:

1. `firejail`
2. `nsjail`
3. `bubblewrap`
4. `chroot`

If a tool is available and sandboxing is enabled, commands can be wrapped for best-effort isolation. If no tool exists, the project logs a warning and runs commands unrestricted.

## Provenance Tracking

Every command execution and file write is tracked by `ProvenanceProvider`:

- Trace IDs link related operations.
- File writes record old/new line counts and content hashes.
- Provider calls record model, provider, confidence scores.
- Annotated commands carry metadata for debugging and replay.

## Work Logs and Save Command

`save_command.py` provides persistent work-log support:

- `SaveContentType` identifies content categories.
- `SaveEntry` records saved content and metadata.
- `WorkLog` tracks a session.
- `SaveCommand.save()` stores content.
- The manager can return previous saves, recent saves, failure coordinates, extracted information, and can load or end sessions.

This is separate from terminal command history and is intended for durable task artifacts.

## Practical Execution Guidelines

For safe and predictable operation:

1. Prefer non-destructive instructions.
2. Enable security blocking and confirmation prompts for untrusted use.
3. Use local test directories when trying file-modification tasks.
4. Keep command timeouts high enough for package installation/build tasks.
5. Use Telegram authorization lists if running a bot.
6. Review terminal logs when Phase 5 reports failure or incomplete verification.
7. Use `str_replace` format for precise file edits instead of shell commands.
