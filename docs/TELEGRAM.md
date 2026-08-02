# Telegram Mode

VEXIS-CLI-3 can run as a Telegram-controlled automation agent. Telegram mode lets authorized users send instructions remotely and receive progress, command, timeout, and summary messages.

## Configuration

Minimal Telegram configuration:

```yaml
execution:
  mode: telegram
telegram:
  enabled: true
  bot_token: "<bot-token>"
  bot_username: "<bot-username>"
  authorized_users: [123456789]
  output_recipients: [123456789]
  enable_input_listener: true
  send_phase2_end_updates: true
  max_history_length: 50
```

`api_id`, `api_hash`, `session_name`, and `contacts` are also supported in the dataclass/config example for richer Telegram integrations.

## Main Components

| Component | Role |
| --- | --- |
| `TelegramBotManager` | Owns bot lifecycle, message queue, handlers, outbound messages, restart callback, and terminal history reference. |
| `ConversationHistory` | Stores recent messages and context for prompt construction. |
| Engine Telegram fields | `PipelineContext.telegram_mode`, `telegram_user_id`, and `conversation_history` allow the pipeline to send targeted updates. |

## Message Queue Behavior

The Telegram queue is designed to be resilient:

- Failed message sends are retried only up to a bounded retry count.
- Delayed retries are skipped without blocking newer queue items.
- Queue processing avoids unbounded blocking when one message cannot be delivered.

## Overlapping User Tasks

If a user sends a new instruction while an older task for that user is still running, the bot can cancel the active task and start the latest one. Internally this calls the engine cancellation path and foreground command cancellation where available.

## Restart Command

The Telegram command handling includes restart support. A restart command:

1. Acknowledges the request.
2. Invokes the configured restart callback.
3. Allows `run.py` to preserve mode/provider/model/API-key state through `VEXIS_RESTART_*` variables.

## Progress Updates

Depending on configuration, Telegram users can receive:

- Start acknowledgements.
- Phase 2 generated command updates.
- Timeout errors when command execution exceeds configured limits.
- Final summaries.
- Error messages.

## Authorization

Use `authorized_users` and/or `allowed_user_ids` to restrict who can issue tasks. Use `output_recipients` for users/chats that should receive output. Do not run Telegram mode without an authorization list on shared or internet-facing bots.

## Operational Tips

- Use a dedicated bot token for VEXIS-CLI-3.
- Avoid placing bot tokens directly in committed config files; prefer local `config.yaml` or environment/secret management.
- Set conservative `max_iterations` and timeouts for remote use.
- Enable security warnings/blocking for remote operation.
- Monitor logs for repeated queue failures.
