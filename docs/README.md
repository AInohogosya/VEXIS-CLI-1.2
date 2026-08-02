# VEXIS-CLI-3 Documentation

This folder is the self-contained technical documentation set for VEXIS-CLI-3. A reader should be able to understand the repository layout, runtime behavior, configuration surface, provider integrations, command execution model, deployment options, and development workflow from these Markdown files without opening the implementation.

## What VEXIS-CLI-3 Is

VEXIS-CLI-3 is a Python 3.8+ terminal automation agent. It accepts a natural-language instruction, asks a configured AI provider to plan and generate shell commands, executes those commands, evaluates the result, and produces a final summary. The current implementation is branded in several places as a “5-phase” system, but the core engine implements an optimized **6-phase** loop:

1. Initial planning.
2. Action generation.
3. Programmatic command extraction and execution.
4. Dynamic update and progress reporting.
5. Verification.
6. Summarization.

The project also includes a unified LLM API adapter package, local Ollama support, cloud provider support, Telegram mode, SDK management, cost tracking, prompt caching, security helpers, Docker examples, and a test suite.

## Documentation Map

> Note: `MODULE_INVENTORY.md` may contain legacy docstrings copied from source files. Treat `ARCHITECTURE.md`, `RUNTIME_FLOW.md`, and `API_REFERENCE.md` as canonical behavior docs for phase semantics.

| Document | Purpose |
| --- | --- |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | End-to-end architecture, phase loop, components, and data flow. |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Repository tree explained file by file and directory by directory. |
| [RUNTIME_FLOW.md](./RUNTIME_FLOW.md) | Startup, CLI flags, virtual environment bootstrap, normal mode, and Telegram mode flow. |
| [API_REFERENCE.md](./API_REFERENCE.md) | Public classes, dataclasses, enums, functions, and provider adapter interfaces. |
| [MODULE_INVENTORY.md](./MODULE_INVENTORY.md) | Generated inventory of every Python module and top-level class/function. |
| [CONFIGURATION.md](./CONFIGURATION.md) | `config.yaml`, environment variables, settings, timeouts, security, cache, cost, and Telegram options. |
| [PROVIDERS.md](./PROVIDERS.md) | Supported AI providers, SDKs, API keys, model selection, Ollama, OpenRouter, and fallback behavior. |
| [COMMAND_EXECUTION.md](./COMMAND_EXECUTION.md) | Command parsing, batch execution, terminal history, security checks, cancellation, and persistence. |
| [TELEGRAM.md](./TELEGRAM.md) | Telegram bot behavior, queueing, authorization, restart command, and conversation history. |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | Local setup, tests, quality checks, and how to extend the codebase. |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Native, pip-style, Docker, and operational deployment notes. |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Diagnosis and fixes for setup, provider, command, timeout, and Telegram problems. |
| [ERROR_HANDLING.md](./ERROR_HANDLING.md) | Exception taxonomy, retry rules, fallback strategy, logging, and user-facing errors. |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Contribution workflow and review expectations. |
| [OLLAMA_INTEGRATION.md](./OLLAMA_INTEGRATION.md) | Local Ollama setup and behavior. |
| [PHASE_1_INITIAL_PLANNING_SUMMARY.md](./PHASE_1_INITIAL_PLANNING_SUMMARY.md) | Detailed summary of Phase 1 planning/action-gate behavior. |
| [PHASE_2_ACTION_GENERATION_SUMMARY.md](./PHASE_2_ACTION_GENERATION_SUMMARY.md) | Detailed summary of Phase 2 command generation contract. |
| [PHASE_3_EXECUTION_SUMMARY.md](./PHASE_3_EXECUTION_SUMMARY.md) | Detailed summary of deterministic command execution. |
| [PHASE_4_DYNAMIC_UPDATE_SUMMARY.md](./PHASE_4_DYNAMIC_UPDATE_SUMMARY.md) | Detailed summary of adaptive plan updates and progress output. |
| [PHASE_5_VERIFICATION_SUMMARY.md](./PHASE_5_VERIFICATION_SUMMARY.md) | Detailed summary of completion verification and recovery loop. |
| [PHASE_6_FINAL_SUMMARY.md](./PHASE_6_FINAL_SUMMARY.md) | Detailed summary of final summarization and completion criteria. |
| [AI_AGENT_ARCHITECTURE_ENHANCEMENT_PROPOSAL.md](./AI_AGENT_ARCHITECTURE_ENHANCEMENT_PROPOSAL.md) | Forward-looking architecture improvements proposal. |

## Primary Entry Points

| Entry point | Role |
| --- | --- |
| `run.py` | Zero-configuration runner. Creates or reuses `venv`, installs requirements, prompts for mode/provider/model, then launches the agent. |
| `src/ai_agent/user_interface/five_phase_app.py` | Package console entry point for `vexis-cli` and `vexis-cli-enhanced`. Parses CLI flags and runs the engine. |
| `src/ai_agent/core_processing/five_phase_engine.py` | Main optimized pipeline engine. Despite the filename and some legacy text, it implements the 6-phase workflow. |
| `src/ai_agent/external_integration/model_runner.py` | Formats prompts for each phase, calls the multi-provider client, validates model responses, and injects custom Phase 1 system prompts. |
| `src/ai_agent/core_processing/terminal_history.py` | Executes shell commands, records terminal history, handles cancellation, timeout, and log display. |
| `api/` | Unified provider adapter package for direct LLM client usage outside the pipeline. |

## Quick Start

```bash
git clone <repository-url>
cd VEXIS-CLI-3
python3 run.py "list the files in this directory"
```

For package-style usage after installing dependencies:

```bash
python -m ai_agent.user_interface.five_phase_app "list files"
vexis-cli "list files"
```

## Important Implementation Notes

- The documentation intentionally reflects the current repository, including legacy names such as `FivePhaseEngine` and `five_phase_app.py` even when the engine behavior is now 6-phase.
- Security command blocking is configurable and disabled by default, while sandbox wrapping is enabled by default when a supported sandbox tool exists.
- `run.py` is the most user-friendly entry point because it bootstraps the virtual environment and dependencies automatically.
- Cloud provider SDKs are optional. Missing SDKs can be installed with `python3 manage_sdks.py install` or `python3 run.py --install-sdks`.
- The generated [MODULE_INVENTORY.md](./MODULE_INVENTORY.md) is the most exhaustive symbol-level index.

## 2026-05-23 Consistency Revision Scope

All Markdown files in `docs/` were reviewed against the current implementation in:
- `src/ai_agent/core_processing/five_phase_engine.py`
- `src/ai_agent/user_interface/five_phase_app.py`
- `src/ai_agent/external_integration/model_runner.py`
- `src/ai_agent/core_processing/terminal_history.py`

Additional new documentation files were added for each of the six active execution phases and a forward-looking architecture proposal.
