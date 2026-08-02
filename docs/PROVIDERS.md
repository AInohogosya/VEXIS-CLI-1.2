# AI Providers

VEXIS-CLI supports 17 local and cloud AI providers through runtime integration code and a standalone unified API adapter package.

## Provider Selection Concepts

There are three related provider concepts:

1. **Runtime selected provider**: The provider used by `ModelRunner` during the 8-phase pipeline.
2. **Saved settings provider/model**: The provider and model persisted by `SettingsManager` and restored by `run.py`.
3. **Unified API provider**: The provider clients in `api/` that implement `BaseLLM` and can be used independently.

## Supported Provider Names

The configuration supports these 17 provider keys:

| Key | Provider | Type |
|-----|----------|------|
| `ollama` | Ollama (local) | Local |
| `google` | Google Gemini | Cloud |
| `openai` | OpenAI GPT | Cloud |
| `anthropic` | Anthropic Claude | Cloud |
| `groq` | Groq | Cloud |
| `xai` | xAI Grok | Cloud |
| `meta` | Meta Llama | Cloud |
| `mistral` | Mistral AI | Cloud |
| `microsoft` | Microsoft Azure | Cloud |
| `amazon` | Amazon Bedrock | Cloud |
| `cohere` | Cohere | Cloud |
| `deepseek` | DeepSeek | Cloud |
| `together` | Together AI | Cloud |
| `minimax` | MiniMax | Cloud |
| `zhipuai` | ZhipuAI / Z.ai | Cloud |
| `openrouter` | OpenRouter | Cloud |

Aliases in the unified API include `gemini` for Google and `claude` for Anthropic.

## Runtime Provider Path

`ModelRunner` sends phase prompts to `MultiProviderVisionAPIClient`. Each phase call includes:

- Task-specific prompt text.
- System instructions for the VEXIS workflow.
- Provider and model choices.
- Generation parameters such as max tokens, temperature, and timeout.
- Optional image data for vision-capable paths.
- Phase-specific output validation (code blocks required for Phase 2, `Summary_of_Progress` for Phase 4/5).

The response is normalized into `ModelResponse` with success flag, content, task type, model, provider, token usage, cost, latency, error text, and metadata.

## Unified API Package

The `api/` package standardizes 17 provider clients around:

- `GenerationConfig`: max tokens, temperature, top-p, stop sequences, response format, stream flag, and extra parameters.
- `LLMResponse`: content, model, provider, token counts, finish reason, cost estimate, latency, and raw response.
- `ModelInfo`: model ID, display name, provider, context window, max output tokens, supported features, and cost data.
- `BaseLLM`: abstract interface for `generate`, `generate_stream`, async variants, `list_models`, `get_model_info`, `count_tokens`, and `is_available`.
- `LLMFactory`: provider registration and creation.

## API Key Variables

| Provider | Required variables |
| --- | --- |
| Google | `GOOGLE_API_KEY` or `GEMINI_API_KEY`; optional `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`. |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Groq | `GROQ_API_KEY` |
| xAI | `XAI_API_KEY` |
| Meta | `META_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| Microsoft Azure | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, optional `AZURE_OPENAI_DEPLOYMENT`. `run.py` also maps Microsoft selection to `AZURE_API_KEY`. |
| Amazon Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, optional `AWS_REGION_NAME`. |
| Cohere | `COHERE_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Together | `TOGETHER_API_KEY` |
| MiniMax | `MINIMAX_API_KEY` |
| ZhipuAI | `ZHIPUAI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |

## SDK Management

Provider SDKs are optional. The project can check and install missing SDKs:

```bash
python3 manage_sdks.py status
python3 manage_sdks.py install
python3 manage_sdks.py install google
python3 run.py --sdk-status
python3 run.py --install-sdks
```

The core installation includes common SDKs such as `openai`, `groq`, `ollama`, and `python-telegram-bot`. Optional extras include `anthropic`, `google-genai`, `mistralai`, `boto3`, and `cohere`.

## Ollama

Ollama is the local privacy-first provider. Configure it with:

```yaml
api:
  preferred_provider: ollama
  local_endpoint: "http://localhost:11434"
  local_model: "llama3.2:3b"
```

The Ollama provider sends HTTP requests to the local endpoint, detects common local-model errors, and can suggest cloud alternatives when a cloud-only model name is selected for Ollama.

## Groq Helpers

The `Groq/` folder contains an older but useful Groq-specific model selector:

- `groq_models.py` defines production and preview model metadata and capability filters.
- `provider.py` prompts for API key and model choice.
- `groq_hello.py` demonstrates progressive selection and a basic Groq API request.

## Provider Fallback

`ProviderFallbackManager` tracks provider health and supports circuit-breaker-style fallback:

- Providers have status, success/failure counts, consecutive failure counts, last success/failure timestamps, average latency, and optional circuit-open-until time.
- Fallback config controls provider order, max retries per provider, circuit-breaker threshold, recovery timeout, retry delay, exponential backoff, and whether to fallback on rate limits or auth errors.
- Callers can ask for the next available provider or execute a function with fallback behavior.

## Cost Awareness

`CostManager` estimates costs for supported provider/model combinations, enforces daily/monthly/per-request budgets, suggests cheaper alternatives, records usage, tracks provider cost totals, and persists usage data.

## Adding a Provider

To add a provider to the unified API layer:

1. Create `api/<provider>_client.py`.
2. Subclass `BaseLLM`.
3. Implement provider type, default model, initialization, config conversion, generation, streaming if supported, and model listing.
4. Register it with `LLMFactory` in the module and/or `api/__init__.py`.
5. Add API key handling and docs.
6. Add tests or example usage.

To add a provider to the runtime pipeline, update the multi-provider client and selection/settings code in addition to configuration and docs.
