# Project Structure

This document explains every major file and folder in VEXIS-CLI so readers can understand what the repository contains without opening the source.

## Top-Level Files

| Path | Purpose |
| --- | --- |
| `README.md` | Marketing/user-facing overview, feature list, installation notes, usage examples, and provider highlights. |
| `DETAILED_GUIDE.md` | Longer user guide with usage and setup material. |
| `pyproject.toml` | Package metadata for `vexis-cli` version `3.0.0`, dependency declarations, optional extras, pytest configuration, coverage configuration, package discovery, and console scripts. |
| `requirements.txt` | Main requirements list for runtime and common integrations. |
| `requirements-core.txt` | Smaller core dependency list. |
| `requirements-optional.txt` | Optional provider or feature dependencies. |
| `config.example.yaml` | Complete example configuration covering API providers, security, execution, logging, cache, cost, performance, user preferences, Telegram, and custom prompts. |
| `run.py` | Main zero-configuration runner with virtual environment bootstrap, dependency install, provider/model selection, SDK management flags, restart preservation, normal mode, and Telegram mode. |
| `agent_core.py` | Older minimal autonomous loop prototype that loads YAML config, logs messages, and executes generated commands. |
| `manage_sdks.py` | SDK installation/status utility for optional AI providers. |
| `check_models.py` | Utility for checking configured models/provider availability. |
| `check_environment.py` | Environment validation helper. |
| `system_check.py` | Comprehensive system validation script that checks Python, virtual environment, dependencies, Ollama, project structure, config, imports, and permissions. |
| `example_usage.py` | Basic example of using the system. |
| `test_*.py` at repository root | Script-style checks for cloud model errors, prompt templates, `/KG` command support, and fixes. |
| `VEXIS-CLI-3.png`, `Choose_model.png` | Images used by the README and user-facing documentation. |
| `LICENSE` | MIT license. |
| `test_instruction/test_instruction.txt` | Sample instruction fixture. |

## `src/ai_agent/` Package

The `src/ai_agent` package contains the primary application implementation.

### `src/ai_agent/core_processing/`

| File | Purpose |
| --- | --- |
| `five_phase_engine.py` | Main pipeline engine. Defines `PipelinePhase`, `PipelineContext`, `PipelineCancelledError`, `ActionType`, `Task`, `TaskStatus`, and `FivePhaseEngine`. Handles all 8 phases, DAG task execution, cancellation, Telegram notifications, and cleanup. |
| `terminal_history.py` | Terminal command execution and logging subsystem. Records entries, executes commands individually and in batches, supports timeouts, cancellation, foreground/background handling, and terminal log rendering. |
| `command_parser.py` | Parses VEXIS command text into structured command types such as CLI commands, end commands, and regenerate-step commands. |
| `command_output.py` | Defines structured command output and formatting helpers. |
| `code_block_handler.py` | Robust extraction/normalization of command blocks from model responses, including fence handling and cleanup heuristics. Supports Markdown, XML, BBCode, and HTML formats. |
| `task_robustness_manager.py` | Tracks task attempts, failures, retry decisions, and robust execution policies. |
| `save_command.py` | Implements work-log persistence for saved content, failure coordinates, extracted information, recent saves, and session loading. |
| `plan_graph.py` | Predictive Subgoal Graph (PSG) with `SubgoalNode`, `RiskLevel`, and `NodeStatus`. Represents task plans as directed acyclic graphs. |
| `critic_optimizer.py` | `PlanCritic` and `PlanOptimizer` for Phase 0 pre-execution analysis. Analyzes plans for ambiguity, risk, and optimization opportunities. |
| `repo_index.py` | `RepositoryIndex` and `IndexManager` for multi-layer code indexing (symbols, test deps, doc-to-code). Supports delta-aware refresh after writes. |
| `tool_policy.py` | `ToolPolicyEngine` and `ToolScore` for scoring commands on safety, determinism, and cost. Can suggest safer alternatives. |
| `provenance.py` | `ProvenanceTracker` and `ProvenanceRecord` for maintaining an audit trail of all operations, writes, and provider calls. |
| `__init__.py` | Package marker. |

### `src/ai_agent/external_integration/`

| File | Purpose |
| --- | --- |
| `model_runner.py` | Phase-specific prompt templates, `TaskType`, `ModelRequest`, `ModelResponse`, `PromptTemplate`, `ModelRunner`, prompt formatting, output validation, context compression, and SDK status helpers. |
| `multi_provider_vision_client.py` | Unified multi-provider API client used by `ModelRunner`. Handles API requests, provider selection, SDK availability, and model invocation. |
| `ollama_provider.py` | Simple Ollama HTTP provider with cloud-model detection and local-model error guidance. |
| `openrouter_provider.py` | OpenRouter provider implementation. |
| `google_provider.py` | Google/Gemini provider implementation. |
| `vision_api_client.py` | Vision-capable API client utilities. |
| `telegram_bot.py` | Telegram bot manager, message queue, conversation history, command handling, cancellation of overlapping tasks, and restart callback integration. |
| `__init__.py` | Package marker. |

### `src/ai_agent/user_interface/`

| File | Purpose |
| --- | --- |
| `five_phase_app.py` | Console application wrapper. Loads config, initializes `FivePhaseEngine`, parses CLI flags, validates arguments, handles `ask_user` clarification prompts, and returns process exit codes. |
| `__init__.py` | Package marker. |

### `src/ai_agent/utils/`

| File | Purpose |
| --- | --- |
| `config.py` | Dataclass-based configuration system, config loading/saving, validation, singleton manager, and dot-notation config access. |
| `settings_manager.py` | Persistent user/provider/model/API-key settings helper used by `run.py` and provider selection. |
| `model_definitions.py` | Provider and model catalog used for selection and recommendations. |
| `dependency_checker.py` | Detects installed/missing provider SDKs and can install them. |
| `sdk_installer.py` | SDK installation primitives. |
| `cost_manager.py` | Cost estimation, budget checks, usage tracking, provider/model cost accounting, alerts, and persistence. |
| `provider_fallback.py` | Provider health, circuit-breaker state, fallback order, and retry/fallback execution. |
| `prompt_cache.py` | Prompt/response caching with TTL, size limit, optional disk persistence, and cache stats. |
| `security.py` | Sensitive-data masking, command safety checks, environment-driven security config, sandbox wrapping, and `SecurityManager`. |
| `exceptions.py` | Exception classes, categories, retryability, exponential backoff, and centralized error handling. |
| `logger.py` | Basic project logger helpers. |
| `structured_logger.py` | JSON structured logging and telemetry metrics collection. |
| `environment_detector.py` | Operating system, shell, environment, capability, and package-manager detection. |
| `ollama_manager.py` | Ollama installation/status/model management. |
| `ollama_error_handler.py` | User-focused Ollama error diagnosis and recovery suggestions. |
| `ollama_model_selector.py` | Ollama model selection helper. |
| `interactive_menu.py`, `curses_menu.py` | Terminal UI menu implementations. |
| `yellow_selection/` | Yellow-highlighted selection UI package with clean and fallback menus, hierarchical model selector, config, and demo functions. |
| `__init__.py` | Package marker. |

### `src/ai_agent/platform_abstraction/`

| File | Purpose |
| --- | --- |
| `platform_detector.py` | Detects OS, architecture, shell, Python environment, display server, package managers, paths, and command availability. |
| `__init__.py` | Package marker. |

### `src/ai_agent/plugins/`

| File | Purpose |
| --- | --- |
| `__init__.py` | Plugin manager, hook specifications, singleton access, plugin registration, hook execution, custom command discovery, and error hook behavior. |
| `example_plugin.py` | Example plugin implementing lifecycle hooks such as initialize, pre/post execute, pre-phase, error handling, and custom commands. |

## `api/` Unified LLM Adapter Package

The `api/` directory is a separate unified adapter layer. It exposes a consistent `BaseLLM` interface for 17 providers and can be used independently of the command-execution pipeline.

| File | Purpose |
| --- | --- |
| `base.py` | Core abstractions: `ProviderType`, `ResponseFormat`, `GenerationConfig`, `LLMResponse`, `ModelInfo`, `BaseLLM`, `LLMFactory`, and cost estimation. |
| `__init__.py` | Imports provider clients, registers available providers, and exposes `create_client()` and `get_available_providers()`. |
| `openai_client.py` | OpenAI adapter. |
| `google_client.py` | Google Gemini adapter, including Vertex-style project/location options. |
| `anthropic_client.py` | Anthropic Claude adapter. |
| `groq_client.py` | Groq adapter using OpenAI-compatible APIs. |
| `xai_client.py` | xAI/Grok adapter. |
| `meta_client.py` | Meta Llama API adapter. |
| `mistral_client.py` | Mistral adapter. |
| `microsoft_client.py` | Azure OpenAI adapter. |
| `amazon_client.py` | Amazon Bedrock adapter. |
| `cohere_client.py` | Cohere adapter. |
| `deepseek_client.py` | DeepSeek adapter. |
| `together_client.py` | Together AI adapter. |
| `minimax_client.py` | MiniMax adapter. |
| `zhipuai_client.py` | ZhipuAI/GLM adapter. |
| `integration_example.py` | Examples for integrating the unified API with application code. |
| `usage_example.py` | Standalone usage examples. |
| `README.md` | API package documentation. |

## `Groq/`

| File | Purpose |
| --- | --- |
| `groq_models.py` | Groq model catalog with production/preview filters, capability lookup, and model info lookup. |
| `provider.py` | Groq API key prompt and model selection helper. |
| `groq_hello.py` | Interactive progressive Groq model selection and simple Groq request example. |
| `README.md` | Groq-specific guide. |

## `docker/`

| Path | Purpose |
| --- | --- |
| `docker/README.md` | Docker build/run guide. |
| `docker/docker-compose.yml` | Multi-service compose setup with profiles/volumes/environment examples. |
| `docker/ubuntu/Dockerfile`, `docker/ubuntu/entrypoint.sh` | Ubuntu image and entrypoint. |
| `docker/alpine/Dockerfile` | Alpine image. |
| `docker/centos/Dockerfile` | CentOS image. |
| `docker/macos/Dockerfile` | macOS-like container target. |
| `docker/windows/Dockerfile`, `docker/windows/entrypoint.ps1` | Windows container target and PowerShell entrypoint. |

## `tests/`

| Path | Purpose |
| --- | --- |
| `tests/conftest.py` | Shared pytest fixtures for temp directories, mock model responses, mock API errors, sample prompts/logs, and singleton reset. |
| `tests/unit/test_task_lifecycle.py` | Long-running command handling, background detachment, foreground timeout, config timeout loading, and runtime option application. |
| `tests/unit/test_telegram_queue.py` | Telegram queue retry limits, delayed retry behavior, overlapping task cancellation, and restart command callback. |
| `tests/unit/test_security.py` | Sensitive-data masking, security config, environment-variable config, command safety checks, and result structure. |
| `tests/unit/test_cost_manager.py` | Cost estimation, budget enforcement, alternatives, alerts, usage tracking, and persistence. |
| `tests/unit/test_exceptions.py` | Error categorization, retry decisions, backoff, execution errors, timeout/resource/validation errors. |
| `tests/unit/test_plugins.py` | Plugin manager lifecycle, hook execution, custom commands, and singleton behavior. |
| `tests/unit/test_action_types.py` | Command action-type parsing and classification behavior. |
| `tests/unit/test_code_block_handler.py` | Code-block extraction robustness tests for varied model output formats. |
| `tests/unit/test_model_runner_system_prompt.py` | Phase-1 system prompt loading/override behavior in `ModelRunner`. |
| `tests/unit/test_verification.py` | Phase 5 verification logic and recovery step generation. |
| `tests/unit/test_keep_commands.py` | `keep_text` and `keep_file` native action handling. |
| `tests/unit/__init__.py` | Test package marker. |
| `tests/test_dag_execution.py` | DAG-based task execution with dependency management. |

## Generated Reference

For a symbol-level listing of every Python file, see [MODULE_INVENTORY.md](./MODULE_INVENTORY.md).
