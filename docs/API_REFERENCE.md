# API Reference

This reference describes the public interfaces that matter for users extending or embedding VEXIS-CLI. For an exhaustive generated list of every Python symbol, see [MODULE_INVENTORY.md](./MODULE_INVENTORY.md).

## Core Pipeline API

### `PipelinePhase`

Enum in `src/ai_agent/core_processing/five_phase_engine.py`.

Values:

- `PHASE0_CRITIC_OPTIMIZER`
- `ACTION_TYPE_SELECTION`
- `PHASE1_INITIAL_PLANNING`
- `PHASE2_ACTION_GENERATION`
- `PHASE3_EXECUTION`
- `PHASE4_DYNAMIC_UPDATE`
- `PHASE5_VERIFICATION`
- `PHASE6_SUMMARIZATION`
- `BOT_USER_REVIEW`
- `COMPLETED`
- `FAILED`

### `ActionType`

Enum in `src/ai_agent/core_processing/five_phase_engine.py`.

Values:

- `RUN_COMMAND`
- `WRITE_FILE`
- `READ_FILE`
- `KEEP_TEXT`
- `KEEP_FILE`
- `ANSWER_DIRECTLY`
- `ASK_USER`

### `PipelineContext`

Dataclass carrying task execution state.

Important fields:

| Field | Meaning |
| --- | --- |
| `user_prompt` | Original user instruction. |
| `action_type` | Classified action type from Phase 1. |
| `ask_user_question` | Question for user when action_type is `ask_user`. |
| `phase1_output` | Raw planning output. |
| `step_list` | Remaining actionable steps. |
| `tasks` | DAG-based task list with dependencies. |
| `completed_steps` | Steps already executed. |
| `progress_summaries` | Phase 4/5 progress messages. |
| `extracted_commands` | Current generated command block/text. |
| `terminal_log` | Rendered terminal history. |
| `last_execution_result` | Structured result from command batch execution. |
| `final_summary` | Phase 6 summary. |
| `current_phase` | Current `PipelinePhase`. |
| `iteration_count`, `max_iterations` | Loop control. |
| `start_time`, `end_time` | Timing. |
| `error` | Error text if failed. |
| `conversation_history` | Telegram/conversation context. |
| `telegram_mode`, `telegram_user_id` | Telegram routing state. |
| `cancel_event`, `cancelled` | Cancellation state. |
| `compressed_context` | Condensed execution history. |
| `kept_text_records`, `kept_file_records` | Preserved memory records. |
| `plan_graph` | Predictive Subgoal Graph from Phase 0. |
| `critic_report` | Critic & Optimizer analysis results. |
| `tool_policy_engine` | Tool safety/determinism/cost scoring. |
| `provenance_tracker` | Metadata on all writes and commands. |
| `repository_index` | Multi-layer code index. |
| `bot_user_review_output`, `bot_user_instructions` | Bot User feedback. |

### `FivePhaseEngine`

Main engine class.

Constructor:

```python
FivePhaseEngine(provider=None, model=None, config=None, telegram_bot=None)
```

Key methods:

| Method | Purpose |
| --- | --- |
| `execute_instruction(user_prompt, conversation_history=None, telegram_mode=False, telegram_user_id=None, cancel_event=None)` | Run a full instruction through the phase pipeline and return `PipelineContext`. |
| `request_cancel()` | Cancel the active pipeline and foreground command. |
| `get_partial_context(conversation_history)` | Save partial progress from a cancelled task into conversation history. |
| `cleanup()` | Release resources and perform cleanup. |

Internal phase methods include `_run_phase0`, `_run_phase1`, `_run_phase2`, `_run_phase3`, `_run_phase4`, `_run_phase5`, `_run_phase6`, and `_run_bot_user_review`. They are implementation details but are useful landmarks when debugging.

## Model Runner API

### `TaskType`

Enum in `model_runner.py`:

- `PHASE0_CRITIC_OPTIMIZER`
- `PHASE1_INITIAL_PLANNING`
- `PHASE2_ACTION_GENERATION`
- `PHASE4_DYNAMIC_UPDATE`
- `PHASE5_VERIFICATION`
- `PHASE6_SUMMARIZATION`
- `BOT_USER_REVIEW`

Phase 3 is absent because execution is local and does not require an LLM call.

### `ModelRequest`

Dataclass fields:

| Field | Meaning |
| --- | --- |
| `task_type` | A `TaskType`. |
| `prompt` | Prompt or task content. |
| `image_data` | Optional image bytes. |
| `image_format` | Image format string, default `PNG`. |
| `context` | Template variables and phase context. |
| `parameters` | Provider-specific generation parameters. |
| `max_tokens` | Maximum output tokens; default 5000. |
| `temperature` | Generation temperature; default 1.0. |
| `timeout` | Request timeout; validated from 1 to 300 seconds. |

### `ModelResponse`

Dataclass fields:

| Field | Meaning |
| --- | --- |
| `success` | Whether the provider call and output validation succeeded. |
| `content` | Model output text. |
| `task_type` | Task type requested. |
| `model` | Model used. |
| `provider` | Provider used. |
| `tokens_used` | Optional token usage. |
| `cost` | Optional cost estimate. |
| `latency` | Request duration. |
| `error` | Error text when failed. |
| `metadata` | Provider-specific metadata. |

### `PromptTemplate`

Loads and returns phase-specific prompt templates. The templates encode the core VEXIS workflow, including output formats such as `step_list [...]`, `Summary_of_Progress [...]`, `original_command [...]`, and `action_type [...]`.

### `ModelRunner`

Constructor:

```python
ModelRunner(provider=None, model=None, config=None, auto_install_sdks=False)
```

Key methods:

| Method | Purpose |
| --- | --- |
| `run_model(request)` | Validate, format, call provider, validate output, and return `ModelResponse`. |
| `compress_context_data(context_data)` | Compress accumulated context data to prevent unbounded growth. |
| `install_missing_sdks(providers=None, interactive=True)` | Install missing SDKs through the provider client/dependency layer. |
| `show_sdk_status(providers=None)` | Print SDK status. |
| `get_model_runner(provider=None, model=None)` | Convenience factory function. |

## Plan Graph API

### `PlanGraph`

Dataclass in `plan_graph.py` representing a Predictive Subgoal Graph:

- `goal_description` — The overall task goal.
- `nodes` — List of `SubgoalNode` objects.
- `risk_level` — Overall risk assessment.

### `SubgoalNode`

Dataclass for individual subgoals:

- `id` — Unique node identifier.
- `description` — What this subgoal accomplishes.
- `risk_level` — `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
- `status` — `PENDING`, `EXECUTABLE`, `RUNNING`, `COMPLETED`, `FAILED`, or `BLOCKED`.
- `dependencies` — List of node IDs that must complete first.

### `PlanCritic`

Analyzes a `PlanGraph` for:
- Ambiguity in goal descriptions.
- Missing verification steps.
- High-risk operations without safeguards.
- Dependency issues.

### `PlanOptimizer`

Optimizes a `PlanGraph` by:
- Reordering steps for lower risk.
- Combining redundant steps.
- Adding verification checkpoints.
- Setting low-confidence nodes for dry-run execution.

## Tool Policy API

### `ToolPolicyEngine`

Scores commands on safety, determinism, and cost:

- `score_command(command)` — Returns a `ToolScore` with composite, safety, determinism, and cost scores.
- `get_safe_alternatives(command)` — Returns safer alternative commands.

### `ToolScore`

Dataclass with:
- `composite` — Overall score (0.0 to 1.0).
- `safety` — Safety score.
- `determinism` — Determinism score.
- `cost` — Cost score.
- `reason` — Human-readable explanation.

## Provenance API

### `ProvenanceTracker`

Maintains an audit trail of all operations:

- `start_trace(phase, model, provider)` — Start a new trace, returns trace ID.
- `record(trace_id, phase, confidence, ...)` — Record an event in the trace.
- `annotate_command(command, trace_id)` — Add provenance metadata to a command.

## Repository Index API

### `RepositoryIndex`

Multi-layer code index:

- `index_symbols(file_path)` — Index symbol definitions from a file.
- `index_tests(file_path)` — Index test-to-code mappings.
- `delta_refresh(changed_files)` — Incrementally update index after file writes.
- `search_symbols(query)` — Search for symbols by name or type.

## Unified LLM API Package

### `ProviderType`

Enum in `api/base.py`. Provider values include Google, OpenAI, Anthropic, Ollama, Groq, xAI, Meta, Mistral, Microsoft, Amazon, Cohere, DeepSeek, Together, MiniMax, ZhipuAI, and OpenRouter.

### `ResponseFormat`

Enum for response formats such as text, JSON, and Markdown.

### `GenerationConfig`

Dataclass normalizing provider generation parameters:

- `max_tokens`
- `temperature`
- `top_p`
- `stop_sequences`
- `response_format`
- `stream`
- provider-specific extras

### `LLMResponse`

Dataclass normalizing provider responses:

- `content`
- `model`
- `provider`
- token usage fields
- `finish_reason`
- `cost`
- `latency`
- `raw_response`

### `ModelInfo`

Dataclass for model metadata:

- model ID and display name
- provider
- context window
- max output tokens
- supported capabilities
- cost details

### `BaseLLM`

Abstract provider interface. Subclasses implement:

| Method | Purpose |
| --- | --- |
| `provider_type` | Return provider enum. |
| `default_model` | Return default model ID. |
| `_initialize_client` | Initialize SDK/client. |
| `generate(prompt, config=None, **kwargs)` | Generate one complete response. |
| `generate_stream(prompt, config=None, **kwargs)` | Stream response chunks where supported. |
| `generate_async(...)` | Async generation wrapper/implementation. |
| `generate_stream_async(...)` | Async streaming wrapper/implementation. |
| `list_models()` | Return provider model list. |
| `get_model_info(model_id)` | Return metadata for a model. |
| `count_tokens(text, model=None)` | Count or estimate tokens. |
| `is_available()` | Return whether SDK/credentials are available. |

### `LLMFactory`

Factory and registry for `BaseLLM` subclasses.

```python
client = LLMFactory.create(ProviderType.GOOGLE, api_key="...")
response = client.generate("Hello")
```

Convenience functions in `api/__init__.py`:

```python
create_client(provider: str, api_key: str, **kwargs)
get_available_providers()
```

## Configuration API

The main dataclasses are:

- `LoggingConfig`
- `APIConfig`
- `SecurityConfig`
- `PerformanceConfig`
- `EngineConfig`
- `TelegramConfig`
- `ExecutionConfig`
- `CacheConfig`
- `CostConfig`
- `UserConfig`
- `PlatformConfig`
- `Config`
- `ConfigManager`

`Config.get("a.b.c", default)` performs dot-notation lookup.

## Security API

| Class/function | Purpose |
| --- | --- |
| `SecurityCheckResult` | Dataclass describing command safety result. |
| `SensitiveDataMasker` | Masks secrets in strings/dicts. |
| `CommandSecurityChecker` | Checks commands against configured blocking/warning rules. |
| `SandboxManager` | Detects and wraps commands with sandbox tools. |
| `SecurityManager` | Combines checks, masking, and sandbox preparation. |
| `get_security_config_from_env()` | Build security config from environment variables. |
| `get_security_manager(...)` | Create configured security manager. |
| `mask_sensitive_data(text)` | Convenience redaction function. |
| `check_command_safety(command, config=None)` | Convenience command safety function. |
| `create_secure_config(...)` | Create strict/permissive security config. |

## Cost API

`CostManager` supports:

- Cost estimation by provider/model/token counts.
- Daily, monthly, and per-request budget checks.
- Cheaper alternative suggestions.
- Warning and critical budget alerts.
- Usage tracking and persistence.

## Plugin API

Plugins can implement hook methods such as:

- `vexis_initialize(config)`
- `vexis_pre_execute(command, context)`
- `vexis_post_execute(command, result, context)`
- `vexis_pre_phase(phase, context)`
- `vexis_on_error(error, context)`
- `vexis_get_commands()`

The plugin manager can register/unregister plugins, execute hooks, collect custom commands, and expose a global singleton.

## Telegram API

The Telegram layer provides:

- Bot startup/shutdown.
- Authorized message handling.
- Bounded outbound queue.
- Conversation history.
- Overlapping task cancellation.
- Restart callback support.
- Output recipient routing.
- Message callback for processing incoming instructions.
