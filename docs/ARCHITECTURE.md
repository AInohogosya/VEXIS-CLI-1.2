# Architecture

VEXIS-CLI is an AI-assisted terminal automation system. Its architecture separates user interaction, AI prompt orchestration, provider transport, command execution, safety/logging utilities, and optional remote control through Telegram.

## Architectural Layers

```text
User / Telegram / CLI
        |
        v
run.py or five_phase_app.py
        |
        v
FivePhaseEngine + PipelineContext
        |
        +--> ModelRunner + PromptTemplate
        |        |
        |        v
        |   MultiProviderVisionAPIClient / provider adapters / Ollama
        |
        +--> TerminalHistory command executor
        |        |
        |        v
        |   Local shell commands, stdout, stderr, return codes, timeouts
        |
        +--> TelegramBotManager notifications and remote input
        |
        +--> PlanGraph + CriticOptimizer (Phase 0)
        |
        +--> ToolPolicyEngine + ProvenanceTracker
        |
        +--> utils: config, settings, security, fallback, cost, cache, logging
```

## 8-Phase Pipeline Model

The engine models eight logical phases plus completion/failure states:

| Phase | Enum value | LLM call? | Responsibility |
| --- | --- | --- | --- |
| 0 | `phase0_critic_optimizer` | Yes (conditional) | Optionally analyze the task plan for ambiguity, risk, and optimizations before execution. Uses `PlanCritic` and `PlanOptimizer` with `PlanGraph`. |
| 1 | `phase1_initial_planning` | Yes | Convert the user instruction into a numbered `step_list` and classify the action type. The planner is asked to include alternate approaches, common failure points, and verification steps. |
| 2 | `phase2_action_generation` | Yes | Generate a single Markdown code block containing executable shell command(s) for the current step. The prompt forbids explanatory text outside the block. |
| 3 | `phase3_execution` | No | Extract shell commands programmatically from the code block and execute them through `TerminalHistory`. Supports native actions (`read_file`, `write_file`, `search`, `list_files`, `keep_text`, `keep_file`, `str_replace`, `hack`). Captures stdout, stderr, return code, timeout status, and terminal history. |
| 4 | `phase4_dynamic_update` | Yes | Evaluate the result from the AI agent's first-person perspective, emit mandatory `Summary_of_Progress [...]`, and overwrite the remaining future `step_list [...]`. |
| 5 | `phase5_verification` | Yes | Inspect the full execution log and completed steps to decide whether the original task was truly successful. If not, it can emit `original_command [...]` recovery work that returns the loop to Phase 2. |
| 6 | `phase6_summarization` | Yes | Produce the final user-facing report. The output validator rejects summaries that contain command blocks or shell-command-looking content. |
| 7 | `bot_user_review` | Yes | LLM reviews the entire conversation and final output. If the output is acceptable ("Well, I guess this is fine."), the task completes. Otherwise, correction instructions are fed back as new user prompts through Phase 2–4. |

## Action Type System

After planning, the engine classifies intent into explicit action types that gate execution:

| Action type | Behavior |
|---|---|
| `run_command` | Default — execute shell commands through the normal pipeline |
| `write_file` | Write content to files |
| `read_file` | Read file contents |
| `search` | Search file contents across the project (read-only) |
| `list_files` | List files and directories to explore structure (read-only) |
| `keep_text` | Store text in memory records (excluded from context compression) |
| `keep_file` | Store file snapshots in memory records (excluded from context compression) |
| `answer_directly` | Skip to Phase 6 and provide a direct answer |
| `ask_user` | Return a question to the caller for clarification |

## Pipeline State

`PipelineContext` is the state object carried through the engine. It stores:

- Original `user_prompt` and `action_type`.
- Phase 1 output and current `step_list`.
- `completed_steps` and `progress_summaries`.
- Current step index, current phase, iteration count, max iterations, start/end times, and error text.
- Current Markdown code block or command text in `extracted_commands`.
- Last execution result and terminal log.
- Final summary.
- Metadata, Telegram mode/user ID, conversation history, cancel event, and cancellation flag.
- `plan_graph` — Predictive Subgoal Graph built during Phase 0.
- `critic_report` — Critic & Optimizer analysis results.
- `tool_policy_engine` — Tool safety/determinism/cost scoring.
- `provenance_tracker` — Metadata on all writes and commands.
- `repository_index` — Multi-layer code index.
- `compressed_context` — Condensed execution history for long-running tasks.
- `kept_text_records` / `kept_file_records` — Preserved memory records.
- `bot_user_review_output` / `bot_user_instructions` — Bot User feedback.

This context is what allows VEXIS-CLI to keep working over many command iterations while preserving a complete explanation of what was already done.

## Main Engine Responsibilities

`FivePhaseEngine` owns the application-level execution loop:

1. Initialize config, logger, terminal history, model runner, Telegram integration, tool policy engine, provenance tracker, repository index, max iterations, timeouts, and cancellation state.
2. Create a `PipelineContext` for each instruction.
3. Run Phase 0 (optional Critic & Optimizer) to analyze the plan.
4. Run Phase 1 once to produce the initial plan and action type.
5. Route based on action type (`answer_directly`, `ask_user`, `keep_text`, `keep_file`, or `run_command`).
6. For command execution, support both DAG-based and legacy step-list execution:
   - **DAG tasks**: Execute tasks with dependency management (Phase 2→3→4 per task).
   - **Legacy loop**: Loop over Phase 2 → Phase 3 → Phase 4 until the step list is empty or iteration limits/timeouts/cancellation stop execution.
7. Run Phase 5 verification. If verification identifies more work, append/rewrite steps and return to Phase 2.
8. Run Phase 6 summarization.
9. Run Phase 7 Bot User Review. If corrections are provided, execute them through Phase 2–4 and re-summarize.
10. Save final state, report success/failure, and notify Telegram when applicable.

## Model Orchestration

`ModelRunner` is the bridge between pipeline phases and provider APIs.

- `TaskType` defines the phase-specific model tasks.
- `ModelRequest` carries task type, prompt, optional image bytes/format, context values, generation parameters, max tokens, temperature, and timeout.
- `PromptTemplate` contains the exact phase prompts and fills variables such as current step, OS info, terminal logs, completed steps, remaining steps, progress summaries, and custom system prompt.
- `ModelRunner.run_model()` validates the request, formats the prompt, adds system instructions, calls the multi-provider client, measures latency, and validates output shape.
- Output validation is phase-aware: Phase 2 must include a code block, Phase 4/5 must include `Summary_of_Progress`, and Phase 6 must not include shell commands.

## Provider Architecture

There are two provider layers:

1. **Runtime provider path** used by the pipeline:
   - `ModelRunner` calls `MultiProviderVisionAPIClient`.
   - Local Ollama, Google, OpenRouter, and 14 other configured providers can be selected by config or runtime prompts.
   - SDK availability can be checked/installed through dependency utilities.

2. **Standalone unified API package** in `api/`:
   - `BaseLLM` defines a consistent interface.
   - 17 provider clients normalize calls into `LLMResponse`.
   - `LLMFactory` registers and creates provider clients by `ProviderType`.
   - This package is useful for direct application integrations and examples.

## Command Execution Architecture

Phase 3 deliberately avoids an LLM call. It uses deterministic parsing and execution:

1. Extract commands from the Phase 2 Markdown code block.
2. Recognize native action formats (`read_file`, `write_file`, `search`, `list_files`, `keep_text`, `keep_file`, `<str_replace>`, `hack`).
3. Run shell commands as a batch through `TerminalHistory`.
4. Enforce per-command timeout and cancellation event.
5. Record stdout, stderr, return code, timestamps, and command metadata.
6. Record provenance metadata for all writes and commands.
7. Render recent terminal history for later AI phases.

This design reduces hallucination risk in command execution and keeps execution auditable.

## DAG-Based Task Execution

The engine supports directed acyclic graph task structures:

- Tasks declare dependencies via `waiting_for` lists.
- The scheduler finds executable tasks (no unmet dependencies).
- On task completion, dependent tasks become unblocked.
- On task failure, all transitively dependent tasks are blocked.
- Deadlock detection identifies circular unresolvable dependencies.

## Security and Safety Architecture

Security is configurable rather than hard-blocked by default.

- `SensitiveDataMasker` redacts API keys, tokens, passwords, AWS keys, GitHub tokens, and similar secrets before logs are exposed.
- `CommandSecurityChecker` can block known dangerous commands, require confirmation for risky commands, warn on `sudo`, and warn on pipe-to-shell patterns.
- `SandboxManager` detects tools such as `firejail`, `nsjail`, `bubblewrap`, or `chroot` and can wrap commands when enabled.
- `SecurityManager` combines safety checks, warnings, masking, and sandbox wrapping.
- `ToolPolicyEngine` scores commands on safety, determinism, and cost, and can suggest safer alternatives.
- File path validation prevents access to sensitive system directories.
- Environment variables can enable or disable the major security features.

## Provenance Architecture

`ProvenanceTracker` maintains an audit trail:

- Every command execution is recorded with trace IDs.
- File writes include old/new line counts and content hashes.
- Provider calls record model, provider, confidence scores, and iteration context.
- All provenance data is available for debugging and replay.

## Telegram Architecture

Telegram mode allows remote interaction:

- `TelegramBotManager` maintains a bounded message queue.
- Messages from the same user can cancel an overlapping running task and start the latest request.
- Conversation history is stored and injected into prompts.
- The engine can send Phase 2 command updates, progress summaries, timeout notifications, final summaries, correction feedback, and restart acknowledgements.
- Authorized user IDs and output recipients are configured in `config.yaml`.

## Persistence and State

VEXIS-CLI persists several kinds of state:

| State | Location / owner | Purpose |
| --- | --- | --- |
| User config | `config.yaml` via `ConfigManager` | Provider, model, timeouts, security, Telegram, cache, cost, custom prompts. |
| Runtime settings | `SettingsManager` | Saved provider/model/API-key choices used by `run.py`. |
| Prompt cache | `PromptCache` | Avoid repeated model calls for identical prompts when enabled. |
| Cost usage | `CostManager` | Track provider/model usage and budget thresholds. |
| Terminal history | `TerminalHistory` | In-memory and rendered command logs for phase evaluation. |
| Work logs | `SaveCommand` | Saved content, extracted information, failure coordinates, and session replay. |
| Repository index | `RepositoryIndex` | Symbol definitions, test mappings, doc-to-code relationships. |

## Error Handling Architecture

The exception layer classifies errors by category and retryability. The engine and utilities use this metadata to decide whether to retry, back off, switch provider, report validation failure, or stop. See [ERROR_HANDLING.md](./ERROR_HANDLING.md) for the full taxonomy.

## Context Compression

To prevent unbounded context growth in long-running tasks:

- Every 10 iterations, accumulated context (terminal log, completed steps, progress summaries) is compressed via LLM.
- Kept text and file records are explicitly excluded from compression.
- The compressed context replaces earlier history in subsequent LLM prompts.
