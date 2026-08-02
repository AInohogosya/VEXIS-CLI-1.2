# Runtime Flow

This document describes how VEXIS-CLI-3 starts, parses options, chooses providers, executes instructions, and exits.

## User-Facing Startup Paths

### `python3 run.py "instruction"`

`run.py` is the recommended path for users. It performs zero-configuration setup:

1. Handles `--help`, `--check`, and `--fix` before virtual environment setup.
2. Detects whether Python is already running inside a virtual environment.
3. If not, finds or creates `venv/`.
4. Installs dependencies into that virtual environment.
5. Re-executes itself using the virtual environment Python.
6. Adds `src/` to `sys.path`.
7. Restores provider/model/API-key values from restart environment variables when `/restart` or runtime restart is used.
8. Handles SDK management flags.
9. Selects execution mode: `normal`, `telegram`, or config-driven/interactive auto selection.
10. Selects provider/model/API key unless `--no-prompt` or saved settings supply them.
11. Creates and runs the agent.

### `vexis-cli "instruction"`

The package console script points to `ai_agent.user_interface.five_phase_app:main`. It assumes dependencies and import paths are already set up.

### `python -m ai_agent.user_interface.five_phase_app "instruction"`

This is equivalent to the console script when the package is importable.

## `run.py` Flags

| Flag | Behavior |
| --- | --- |
| `--help`, `-h` | Show help and exit. |
| `--check`, `-c` | Run environment check without automatic fixes. |
| `--fix` | Run environment check with auto-fix behavior. |
| `--install-sdks` | Run SDK installation for missing AI provider SDKs. |
| `--sdk-status` | Show provider SDK installation status. |
| `--debug` | Enable debug mode in the runner. |
| `--no-prompt` | Use saved provider/mode/model settings instead of interactive prompts where possible. |
| `--max-iterations N` | Override maximum iteration budget used by the execution loop (planning/execution/verification cycle). |

`run.py` filters flags out of `sys.argv` to construct the natural-language instruction from remaining positional words.

## Package CLI Flags

`five_phase_app.py` exposes a conventional `argparse` interface:

| Flag | Behavior |
| --- | --- |
| positional `instruction` | Natural-language instruction to execute. |
| `--config PATH` | Load a specific configuration file. |
| `--output`, `-o PATH` | Save execution results as JSON. |
| `--quiet`, `-q` | Suppress non-error output. |
| `--verbose`, `-v` | Enable verbose logging. |
| `--log-file PATH` | Write logs to a specified file. |
| `--max-iterations N` | Maximum loop iterations accepted by the package CLI parser; default is 10 (engine config may override at runtime). |
| `--command-timeout SECONDS` | Per-command timeout; default in the CLI wrapper is 600 seconds. |
| `--task-timeout SECONDS` | Whole-task timeout; default in the CLI wrapper is 5400 seconds. |
| `--validate-only` | Load and validate configuration, then exit. |

Argument validation rejects empty instructions, missing config files, invalid output/log directories, non-positive timeouts, and max iterations below 1.

## Normal Mode Execution

The practical loop is `Phase 2 -> Phase 3 -> Phase 4`, followed by Phase 5 verification; verification may emit follow-up work and route back into Phase 2 before final Phase 6 summarization and Phase 7 Bot User Review.

In normal mode:

1. The selected provider/model is loaded from settings or chosen interactively.
2. The engine receives the user instruction.
3. Phase 0 (optional) analyzes the plan with Critic & Optimizer.
4. Phase 1 asks the model for a step list and classifies the action type.
5. The action type gate routes to the appropriate path:
   - `answer_directly` — goes directly to Phase 6.
   - `ask_user` — returns a question to the user.
   - `keep_text` / `keep_file` — stores data and completes.
   - `run_command` — enters the execution loop.
6. For command execution, the engine loops over current steps:
   - Phase 2 generates command code block.
   - Phase 3 executes the command batch locally (or native actions).
   - Phase 4 summarizes progress and rewrites remaining steps.
7. Phase 5 verifies true success.
8. If verification found issues, steps are added and the loop continues.
9. Phase 6 summarizes final results.
10. Phase 7 Bot User Review evaluates the output; corrections may loop back to Phase 2.
11. Exit code and total execution time are printed unless quiet mode is enabled.

## Interactive Mode

When run without an instruction argument, VEXIS-CLI-3 enters an interactive loop:

1. Prompts the user for an instruction.
2. Executes the instruction through the full pipeline.
3. Maintains conversation history between turns.
4. Supports special commands:
   - `quit` / `exit` / `q` — Exit the program.
   - `/reset` — Clear conversation history and terminal logs.
   - `/restart` — Restart the process while preserving current provider/model settings.
   - `/KG` — Keep Going: resume a timed-out task with doubled timeout.
5. While a task is running, the user can type a new prompt to cancel the current task and switch to the latest instruction. Partial progress is preserved in conversation history.

## Telegram Mode Execution

In Telegram mode:

1. Telegram config is loaded from `config.yaml`.
2. Bot/session credentials and authorized users are validated.
3. The bot manager listens for incoming messages.
4. Each authorized instruction starts or replaces an engine task.
5. If a new instruction arrives for the same user, the active task can be cancelled.
6. The bot sends progress, command, timeout, completion, correction, and restart messages depending on config.
7. The `/restart` command from Telegram restarts the process while preserving settings.

## Restart Preservation

`run.py` uses `VEXIS_RESTART_*` environment variables to preserve runtime choices across process replacement:

| Variable | Purpose |
| --- | --- |
| `VEXIS_RESTART_MODE` | `normal` or `telegram`. |
| `VEXIS_RESTART_PROVIDER` | Selected provider. |
| `VEXIS_RESTART_MODEL` | Selected model. |
| `VEXIS_RESTART_API_KEY` | Selected provider API key for the restarted process. |

It also maps selected provider keys into provider-specific environment variables such as `OPENAI_API_KEY` or `GROQ_API_KEY`.

## Exit Behavior

- Configuration/argument failures return non-zero status.
- Engine-level task failures return non-zero status through the app wrapper.
- `KeyboardInterrupt` and cancellation are routed through the engine cleanup path when possible.
- Telegram restart can re-exec the process while preserving selected runtime settings.

## Action Type Gate (Before Main Loop)

After planning, the engine classifies the action type which determines the execution path:

- `run_command` — Full pipeline execution (Phases 2–7).
- `answer_directly` — Skip to Phase 6 (Summarization) and Phase 7 (Bot User Review).
- `ask_user` — Return a clarification question to the caller.
- `keep_text` — Store text in memory records and complete.
- `keep_file` — Store file snapshot in memory records and complete.

## Context Compression

For long-running tasks, the engine automatically compresses accumulated context every 10 iterations:

- Terminal logs, completed steps, and progress summaries are condensed via LLM.
- Kept text and file records are explicitly excluded from compression.
- The compressed context is used in subsequent LLM prompts to prevent context window overflow.
