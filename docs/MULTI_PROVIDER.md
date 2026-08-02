# Multi-Provider Integration Guide

## Table of Contents

- [Overview](#overview)
- [Supported Providers](#supported-providers)
- [Provider Architecture](#provider-architecture)
- [Configuration](#configuration)
- [Fallback System](#fallback-system)
- [Provider Health Monitoring](#provider-health-monitoring)
- [Cost Management](#cost-management)
- [Best Practices](#best-practices)

---

## Overview

VEXIS-CLI-3 supports **17 AI providers** through two provider layers: a runtime path used by the pipeline engine and a standalone unified API adapter package. The system supports automatic provider fallback, health monitoring, and cost tracking.

### Key Features

- **17 Providers**: Ollama (local) + 16 cloud providers
- **Automatic Fallback**: Seamless switching when a provider is unavailable
- **Health Monitoring**: Circuit-breaker pattern with failure tracking
- **Cost Tracking**: Per-provider cost monitoring and budgeting
- **Vision Support**: Image-based tasks via compatible providers
- **Unified API**: Standalone `api/` package for direct integrations

---

## Supported Providers

### Provider Comparison

| Provider | Name in Config | Strengths | Latency | Cost |
|----------|----------------|-----------|---------|------|
| **Ollama** | `ollama` | Local, private | Variable | Free |
| **Google** | `google` | Multimodal, enterprise | Medium | Medium |
| **OpenAI** | `openai` | Advanced reasoning | Medium | High |
| **Anthropic** | `anthropic` | Analytical excellence | Medium | High |
| **Groq** | `groq` | Ultra-fast inference | Very Low | Low |
| **xAI** | `xai` | Real-time knowledge | Medium | Medium |
| **Meta** | `meta` | Open-source leadership | Medium | Low |
| **Mistral** | `mistral` | Multilingual | Medium | Medium |
| **Microsoft** | `microsoft` | Enterprise Azure | Medium | High |
| **Amazon** | `amazon` | Scalable Bedrock | Medium | Medium |
| **Cohere** | `cohere` | Enterprise workflows | Medium | Medium |
| **DeepSeek** | `deepseek` | Technical reasoning | Medium | Low |
| **Together** | `together` | Open-source hosting | Medium | Low |
| **MiniMax** | `minimax` | Productivity tasks | Medium | Low |
| **ZhipuAI** | `zhipuai` | Chinese language | Medium | Low |
| **OpenRouter** | `openrouter` | 300+ model marketplace | Variable | Variable |

### API Key Environment Variables

| Provider | Environment Variable(s) |
|----------|------------------------|
| Google | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Groq | `GROQ_API_KEY` |
| xAI | `XAI_API_KEY` |
| Meta | `META_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| Microsoft | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |
| Amazon | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION_NAME` |
| Cohere | `COHERE_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Together | `TOGETHER_API_KEY` |
| MiniMax | `MINIMAX_API_KEY` |
| ZhipuAI | `ZHIPUAI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |

---

## Provider Architecture

### Runtime Provider Path (Pipeline)

The 8-phase pipeline uses `ModelRunner` as the bridge to AI providers:

```
FivePhaseEngine
    |
    v
ModelRunner (phase-specific prompts)
    |
    v
MultiProviderVisionAPIClient
    |
    +---> OllamaProvider (local HTTP)
    +---> GoogleProvider (Gemini API)
    +---> OpenRouterProvider (OpenRouter API)
    +---> [Other providers via configured clients]
```

Each phase call includes:
- Task-specific prompt text formatted by `PromptTemplate`.
- System instructions for the VEXIS workflow.
- Provider and model choices.
- Generation parameters (max tokens, temperature, timeout).
- Optional image data for vision-capable paths.
- Phase-specific output validation.

The response is normalized into `ModelResponse` with success flag, content, model, provider, token usage, cost, latency, and error text.

### Unified API Package

The `api/` package is a standalone adapter layer:

```
BaseLLM (abstract interface)
    |
    +---> OpenAIGoogleClient
    +---> GoogleClient
    +---> AnthropicClient
    +---> GroqClient
    +-- -> xAIClient
    +---> MetaClient
    +---> MistralClient
    +---> MicrosoftClient
    +---> AmazonClient
    +---> CohereClient
    +---> DeepSeekClient
    +---> TogetherClient
    +---> MiniMaxClient
    +---> ZhipuAIClient
    |
    v
LLMFactory (registration and creation)
```

Both layers share common dataclasses:
- `GenerationConfig`: normalizes generation parameters.
- `LLMResponse`: normalizes provider responses.
- `ModelInfo`: model metadata (context window, capabilities, cost).

---

## Configuration

### Configuring the Preferred Provider

```yaml
api:
  preferred_provider: "ollama"  # or any of the 17 provider keys
  local_endpoint: "http://localhost:11434"
  local_model: "llama3.2:3b"
  models:
    ollama: "llama3.2:3b"
    google: "gemini-3.1-pro-preview"
    groq: "llama-3.3-70b-versatile"
    openai: "gpt-4o"
    # ... etc for all 17 providers
```

### API Key Configuration

API keys can be set via:
1. **Environment variables** (recommended): `OPENAI_API_KEY`, `GROQ_API_KEY`, etc.
2. **Config file**: `api.api_keys` map (less secure).
3. **Settings manager**: Persisted by `SettingsManager` during interactive setup.
4. **Runtime prompt**: `run.py` prompts for keys during provider selection.

### SDK Management

```bash
# Check which provider SDKs are installed
python3 manage_sdks.py status
python3 run.py --sdk-status

# Install missing SDKs
python3 manage_sdks.py install
python3 run.py --install-sdks

# Install a specific provider
python3 manage_sdks.py install google
```

---

## Fallback System

### Provider Fallback Manager

`ProviderFallbackManager` in `provider_fallback.py` implements circuit-breaker-style fallback:

- **Health tracking**: Each provider has status, success/failure counts, consecutive failure counts, last success/failure timestamps, and average latency.
- **Circuit breaker**: Opens after configurable consecutive failures; retries after recovery timeout.
- **Fallback config**: Controls provider order, max retries per provider, circuit-breaker threshold, recovery timeout, retry delay, and exponential backoff.
- **Retry conditions**: Configurable to fallback on rate limits, auth errors, network errors, or all failures.

### Fallback Behavior

When a provider fails:
1. Record the failure and increment consecutive failure count.
2. If consecutive failures exceed the threshold, open the circuit.
3. Select the next healthy provider in the fallback chain.
4. Retry with the new provider.
5. After the recovery timeout, attempt the original provider again.

---

## Provider Health Monitoring

The health monitoring system tracks:

- **Provider status**: `healthy`, `degraded`, or `unhealthy`.
- **Consecutive failures**: Tracked per provider.
- **Average latency**: Used for load balancing decisions.
- **Last success/failure timestamps**: For recovery decisions.

Health decisions are used by the fallback system to route requests away from failing providers.

---

## Cost Management

### Cost Manager

`CostManager` in `cost_manager.py`:

- **Cost estimation**: Per provider/model/token count.
- **Budget enforcement**: Daily, monthly, and per-request budgets.
- **Alternative suggestions**: Cheaper models for the same task.
- **Alerts**: Warning at 80% and critical at 95% of budget by default.
- **Usage tracking**: Persisted per provider/model.

### Budget Configuration

```yaml
cost:
  daily_budget: 10.0       # $10/day
  monthly_budget: 100.0    # $100/month
  per_request_budget: 0.50  # 50 cents/request
  warning_threshold: 0.8    # Alert at 80%
  critical_threshold: 0.95  # Critical at 95%
```

---

## Best Practices

### Provider Selection

1. **Use Ollama for privacy**: Sensitive data never leaves your machine.
2. **Use Groq for speed**: Ultra-fast inference for time-critical tasks.
3. **Use OpenAI/Google for complex reasoning**: Best for architecture design and complex analysis.
4. **Use OpenRouter for access**: 300+ models when you need variety.
5. **Use DeepSeek for reasoning**: Strong technical and coding capabilities.

### Cost Optimization

1. **Set budgets and alerts**: Prevent unexpected costs.
2. **Use cheaper models for simple tasks**: Don't use GPT-5.4 for basic file operations.
3. **Cache responses**: Enabled by default via `PromptCache`.
4. **Monitor usage**: Check the cost dashboard regularly.

### Reliability

1. **Always have a local fallback**: Configure Ollama as backup for cloud providers.
2. **Set appropriate timeouts**: Prevent hanging requests.
3. **Monitor health**: The circuit-breaker pattern prevents cascading failures.
4. **Test fallback regularly**: Ensure fallback works when needed.

### Security

1. **Use environment variables for API keys**: Never hardcode credentials.
2. **Rotate keys regularly**: Minimize exposure from key leaks.
3. **Use Ollama for sensitive data**: Keep data on-premises.
4. **Audit provider access**: Monitor which provider is used for what tasks.
