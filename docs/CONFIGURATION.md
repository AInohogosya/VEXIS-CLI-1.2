# Configuration

VEXIS-CLI configuration is primarily YAML-based. Copy `config.example.yaml` to `config.yaml` and adjust the values you need.

```bash
cp config.example.yaml config.yaml
```

The application also reads environment variables for provider credentials and some security toggles.

## Configuration Loading

The configuration system is implemented with dataclasses in `src/ai_agent/utils/config.py`. The main `Config` object contains these sections:

- `logging`
- `api`
- `security`
- `performance`
- `engine`
- `telegram`
- `execution`
- `cache`
- `cost`
- `user`
- `platform`
- `custom`
- `custom_system_prompt`

Values can be accessed by dot notation through `Config.get("section.key", default)`.

## `api` Section

| Key | Type | Default / Example | Meaning |
| --- | --- | --- | --- |
| `preferred_provider` | string | `ollama` in example, empty in dataclass default | Provider chosen by default. Supported values include `ollama`, `groq`, `google`, `openai`, `anthropic`, `xai`, `meta`, `mistral`, `microsoft`, `amazon`, `cohere`, `deepseek`, `together`, `minimax`, `zhipuai`, and `openrouter`. |
| `api_keys` | map | provider names to strings | Optional inline API keys. Environment variables are recommended instead. |
| `local_endpoint` | string | `http://localhost:11434` | Ollama endpoint. |
| `local_model` | string | `llama3.2:3b` in example | Ollama model. The dataclass fallback checks saved settings and otherwise uses `llama4-scout-17b`. |
| `models` | map | provider names to model IDs | Default model per provider. |
| `timeout` | integer | `131400` in example; dataclass default `30` | Provider/API timeout. |
| `max_retries` | integer | `7` in example; dataclass default `3` | Provider/API retry count. |
| `retry_delay` | float | `1.0` dataclass default | Delay between retries. |
| `openrouter_api_key` | string | empty | Dedicated OpenRouter key field in the dataclass. |
| `compression_enabled` | boolean | `true` | Enable automatic context compression. |
| `compression_threshold` | integer | `6000` | Token count to trigger compression (estimated). |
| `compression_target_ratio` | integer | `50` | Target size after compression (50 = 50% of original). |
| `compression_max_tokens` | integer | `4000` | Max tokens for compression response. |
| `compression_model` | string | empty | Optional specific model for compression (empty = use current). |

## Provider Environment Variables

| Provider | Environment variable(s) |
| --- | --- |
| Google/Gemini | `GOOGLE_API_KEY`, `GEMINI_API_KEY`; Vertex-style options include `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`. |
| Groq | `GROQ_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| xAI | `XAI_API_KEY` |
| Meta | `META_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| Azure/Microsoft | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`; `run.py` also maps Microsoft selection to `AZURE_API_KEY`. |
| Amazon Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION_NAME` |
| Cohere | `COHERE_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Together | `TOGETHER_API_KEY` |
| MiniMax | `MINIMAX_API_KEY` |
| ZhipuAI | `ZHIPUAI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |

## `security` Section

Security features are configurable and most blocking features are disabled by default to preserve user control.

| Key | Default | Meaning |
| --- | --- | --- |
| `enable_command_blocking` | `false` | Block dangerous command substrings such as catastrophic deletes or fork bombs. |
| `enable_confirmation_prompts` | `false` | Require confirmation for risky commands. |
| `enable_sudo_warning` | `false` | Warn when a command begins with `sudo`. |
| `enable_shell_pipe_warning` | `false` | Warn on pipe-to-shell patterns such as `curl ... | bash`. |
| `enable_sandbox` | `true` | Use detected sandbox tools when available. |
| `sanitize_text_input` | `true` | Sanitize input text. |
| `validate_file_paths` | `true` | Validate file paths against sensitive directories. |
| `max_text_length` | `1000` | Maximum text length in security config dataclass. |
| `command_timeout` | `600` | Security-layer command timeout. |

Environment-driven security helpers read boolean environment variables in `security.py`. Use typical true values such as `1`, `true`, `yes`, or `on`.

## `execution` Section

| Key | Default / Example | Meaning |
| --- | --- | --- |
| `mode` | `auto` dataclass default | `auto`, `normal`, or `telegram`. `run.py` uses this to avoid prompting when set. |
| `safety_mode` | `true` | General safety mode flag. |
| `dry_run` | `false` | Show commands without executing when supported by callers. |
| `verify_commands` | `true` | Validate commands before execution. |
| `command_timeout` | `1800` in example; dataclass default `600` | Per-command timeout. |
| `task_timeout` | `2700` in example; dataclass default `7200` | Whole-task timeout. |
| `max_iterations` | `500` | Engine loop upper bound; Phase 5 verification can request additional work before final summarization. |
| `auto_recovery` | `true` | Allow automatic recovery behavior (e.g., install missing packages). |

## `engine` Section

| Key | Default / Example | Meaning |
| --- | --- | --- |
| `click_delay` | `0.1` | Delay between click actions. |
| `typing_delay` | `0.05` | Delay between keystrokes. |
| `scroll_duration` | `0.5` | Scroll animation duration. |
| `drag_duration` | `0.3` | Drag animation duration. |
| `screenshot_quality` | `95` | Screenshot quality (1-100). |
| `screenshot_format` | `PNG` | Screenshot format. |
| `max_task_retries` | `3` | Maximum task retries. |
| `max_command_retries` | `3` | Maximum command retries. |
| `command_timeout` | `600` | Engine-level command timeout. |
| `task_timeout` | `7200` | Engine-level task timeout. |
| `max_rebuilds_per_session` | `3` | Maximum rebuilds per session. |

## `logging` Section

| Key | Default / Example | Meaning |
| --- | --- | --- |
| `level` | `INFO` | Logging level. |
| `file` | `vexis.log` example; dataclass default `None` | Optional log file. |
| `json_format` | `false` | Structured JSON logs. |
| `console` | `true` | Console logging. |
| `max_file_size` | 10 MB dataclass default | Log rotation threshold. |
| `backup_count` | `5` dataclass default | Log backup count. |

## `cache` Section

| Key | Default | Meaning |
| --- | --- | --- |
| `enabled` | `true` | Enable prompt-response cache. |
| `max_size` | `1000` | Maximum cache entries. |
| `ttl` | `3600` | Time-to-live in seconds. |
| `persist_to_disk` | `true` | Save cache across sessions. |

## `cost` Section

| Key | Default | Meaning |
| --- | --- | --- |
| `daily_budget` | `null` | Optional USD daily budget. |
| `monthly_budget` | `null` | Optional USD monthly budget. |
| `per_request_budget` | `null` | Optional USD per-request budget. |
| `warning_threshold` | `0.8` | Warning at 80% of budget by default. |
| `critical_threshold` | `0.95` | Critical alert at 95% of budget by default. |

## `performance` Section

| Key | Default | Meaning |
| --- | --- | --- |
| `max_concurrent_tasks` | `1` | Maximum concurrent tasks. |
| `task_timeout` | `7200` | Performance-layer task timeout. |
| `command_timeout` | `600` | Performance-layer command timeout. |
| `api_timeout` | `30` | API request timeout. |
| `memory_limit_mb` | `1024` | Memory limit in MB. |

## `telegram` Section

| Key | Meaning |
| --- | --- |
| `enabled` | Enable Telegram bot mode. |
| `bot_token` | Bot token from BotFather. |
| `bot_username` | Bot username. |
| `api_id`, `api_hash` | Telegram API credentials where applicable. |
| `session_name` | Local session name. |
| `contacts` | List of configured contacts. |
| `authorized_users` | User IDs allowed to send tasks. |
| `output_recipients` | Users/chats that receive output. |
| `enable_input_listener` | Listen for incoming Telegram requests. |
| `send_phase2_end_updates` | Send generated command updates. |
| `max_history_length` | Maximum conversation history entries. |
| `allowed_user_ids` | Dataclass-supported alias/list for allowed users. |

## `user` Section

| Key | Default | Meaning |
| --- | --- | --- |
| `name` | `""` | User name. |
| `preferred_style` | `"detailed"` | Output style: `concise`, `detailed`, or `friendly`. |
| `auto_confirm` | `false` | Auto-confirm risky commands. |
| `show_progress` | `true` | Show progress updates. |

## `platform` Section

Platform-specific settings as a free-form dictionary. Used by `PlatformDetector` for OS-specific behavior.

## `custom` Section

Free-form dictionary for user-defined configuration values accessible via `Config.get("custom.key")`.

## `custom_system_prompt`

`custom_system_prompt` is injected into **Phase 1 only**. Use it to add persistent planning instructions, policy preferences, repository-specific constraints, or style requirements.

Example:

```yaml
custom_system_prompt: |
  Always prefer non-destructive commands.
  Before modifying files, inspect their current contents.
```

## Environment Variable Overrides

The following environment variables override config file values:

| Variable | Overrides |
| --- | --- |
| `AI_AGENT_LOG_LEVEL` | `logging.level` |
| `AI_AGENT_LOG_FILE` | `logging.file` |
| `AI_AGENT_LOG_JSON` | `logging.json_format` |
| `AI_AGENT_LOCAL_ENDPOINT` | `api.local_endpoint` |
| `AI_AGENT_LOCAL_MODEL` | `api.local_model` |
| `AI_AGENT_PREFERRED_PROVIDER` | `api.preferred_provider` |
| `AI_AGENT_API_TIMEOUT` | `api.timeout` |
| `AI_AGENT_API_MAX_RETRIES` | `api.max_retries` |
| `AI_AGENT_COMMAND_TIMEOUT` | `security.command_timeout` |
| `AI_AGENT_MAX_CONCURRENT_TASKS` | `performance.max_concurrent_tasks` |
| `AI_AGENT_TASK_TIMEOUT` | `performance.task_timeout` |

## Recommended Minimal Configurations

### Local Ollama

```yaml
api:
  preferred_provider: ollama
  local_endpoint: http://localhost:11434
  local_model: llama3.2:3b
  models:
    ollama: llama3.2:3b
execution:
  mode: normal
```

### Groq Cloud

```yaml
api:
  preferred_provider: groq
  models:
    groq: llama-3.3-70b-versatile
execution:
  mode: normal
```

Then export:

```bash
export GROQ_API_KEY="..."
```

### Telegram Mode

```yaml
execution:
  mode: telegram
telegram:
  enabled: true
  bot_token: "..."
  authorized_users: [123456789]
  output_recipients: [123456789]
```
