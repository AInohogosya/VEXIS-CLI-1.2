# VEXIS-CLI-3 Detailed User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation & Setup](#installation--setup)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [AI Provider Setup](#ai-provider-setup)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Getting Started

### What is VEXIS-CLI-3?

VEXIS-CLI-3 is an intelligent command-line agent that transforms natural language instructions into executable terminal commands. It features an 8-phase pipeline architecture, supports 17 AI providers, and offers both local (privacy-first) and cloud-based options.

### Key Features

- **Natural Language Processing**: Convert plain English commands to terminal operations
- **Multi-Provider Support**: 17 AI providers including local Ollama models
- **8-Phase Pipeline**: Critic & Optimizer → Planning → Action Generation → Execution → Dynamic Update → Verification → Summarization → Bot User Review
- **Error Handling**: Intelligent error recovery and user guidance
- **One-Liner Execution**: Simple `python3 run.py "your command"` syntax
- **Cross-Platform**: Works on macOS, Linux, and Windows
- **Telegram Mode**: Remote control via Telegram bot

---

## Installation & Setup

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/AInohogosya/VEXIS-CLI-3.git
cd VEXIS-CLI-3

# Run your first command (dependencies auto-installed)
python3 run.py "list files in current directory"
```

### Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/AInohogosya/VEXIS-CLI-3.git
cd VEXIS-CLI-3

# 2. Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Run the agent
python3 run.py "your instruction here"
```

### System Requirements

- **Python**: 3.8 or higher
- **Memory**: 4GB+ RAM recommended
- **Storage**: 2GB+ free space
- **Network**: Internet connection for cloud providers

---

## Configuration

### Basic Configuration

Edit `config.yaml` to customize your setup:

```yaml
api:
  preferred_provider: "ollama"  # Your preferred AI provider (17 providers supported)
  local_endpoint: "http://localhost:11434"  # Ollama endpoint
  local_model: "llama3.2:3b"  # Default local model
  timeout: 120  # Request timeout in seconds
  max_retries: 3  # Maximum retry attempts

execution:
  mode: "normal"  # "normal", "telegram", or "auto"
  command_timeout: 1800  # Command execution timeout (30 minutes)
  task_timeout: 7200  # Overall task timeout (120 minutes)
  max_iterations: 500  # Maximum pipeline loop iterations

logging:
  level: "INFO"
  file: "vexis.log"
  console: true
```

### Environment Variables

You can override configuration using environment variables:

```bash
export GOOGLE_API_KEY="your-google-key"
export OPENAI_API_KEY="your-openai-key"
export GROQ_API_KEY="your-groq-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export XAI_API_KEY="your-xai-key"
export META_API_KEY="your-meta-key"
export MISTRAL_API_KEY="your-mistral-key"
export AZURE_API_KEY="your-azure-key"
export AWS_ACCESS_KEY_ID="your-aws-key"
export COHERE_API_KEY="your-cohere-key"
export DEEPSEEK_API_KEY="your-deepseek-key"
export TOGETHER_API_KEY="your-together-key"
export MINIMAX_API_KEY="your-minimax-key"
export ZHIPUAI_API_KEY="your-zhipuai-key"
export OPENROUTER_API_KEY="your-openrouter-key"
```

---

## Usage Examples

### Basic Commands

```bash
# File operations
python3 run.py "create a file called hello.txt with content 'Hello World'"
python3 run.py "list all Python files in the current directory"
python3 run.py "copy hello.txt to backup_hello.txt"

# System information
python3 run.py "show system information"
python3 run.py "check disk usage"
python3 run.py "list running processes"

# Development tasks
python3 run.py "create a new Python project structure"
python3 run.py "install requirements from requirements.txt"
python3 run.py "run tests for the current project"
```

### Advanced Commands

```bash
# With options
python3 run.py "deploy the application" --debug
python3 run.py "setup development environment" --no-prompt
python3 run.py "complex task" --max-iterations 200

# SDK management
python3 run.py --install-sdks
python3 run.py --sdk-status

# Environment check and fix
python3 run.py --check
python3 run.py --fix

# Complex workflows
python3 run.py "create a backup of all configuration files"
python3 run.py "setup a Python development environment with Django"
```

### Interactive Mode

When run without an argument, VEXIS-CLI-3 enters interactive mode:

```bash
$ python3 run.py

# Interactive Mode Commands:
# Type your instruction to execute
# Type 'quit', 'exit', or 'q' to exit
# Type '/reset' to clear conversation history
# Type '/restart' to restart while keeping current settings
# Type '/KG' (Keep Going) to resume a task after timeout
```

### Telegram Mode

```yaml
# In config.yaml:
execution:
  mode: "telegram"
telegram:
  enabled: true
  bot_token: "your-bot-token"
  authorized_users: [123456789]
```

---

## AI Provider Setup

### Local Providers

#### Ollama Setup

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Start Ollama Service**:
   ```bash
   ollama serve
   ```

3. **Download Models**:
   ```bash
   ollama pull llama3.2:3b
   ollama pull qwen2.5:3b
   ollama pull deepseek-r1:7b
   ```

4. **Configure VEXIS-CLI-3**:
   ```yaml
   api:
     preferred_provider: "ollama"
     local_model: "llama3.2:3b"
   ```

### Cloud Providers

| Provider | Environment Variable | Config Preference |
|----------|---------------------|-------------------|
| Google | `GOOGLE_API_KEY` | `google` |
| OpenAI | `OPENAI_API_KEY` | `openai` |
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic` |
| Groq | `GROQ_API_KEY` | `groq` |
| xAI | `XAI_API_KEY` | `xai` |
| Meta | `META_API_KEY` | `meta` |
| Mistral | `MISTRAL_API_KEY` | `mistral` |
| Microsoft | `AZURE_API_KEY` | `microsoft` |
| Amazon | `AWS_ACCESS_KEY_ID` | `amazon` |
| Cohere | `COHERE_API_KEY` | `cohere` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek` |
| Together | `TOGETHER_API_KEY` | `together` |
| MiniMax | `MINIMAX_API_KEY` | `minimax` |
| ZhipuAI | `ZHIPUAI_API_KEY` | `zhipuai` |
| OpenRouter | `OPENROUTER_API_KEY` | `openrouter` |

---

## Advanced Features

### 8-Phase Execution Engine

VEXIS-CLI-3 uses a sophisticated 8-phase execution pipeline:

1. **Phase 0 (Critic & Optimizer)**: Analyzes the plan for ambiguity, risk, and optimization opportunities before execution begins
2. **Phase 1 (Initial Planning)**: Converts the user instruction into a structured step list with action type classification
3. **Phase 2 (Action Generation)**: Generates executable shell commands or native actions for the current step
4. **Phase 3 (Execution)**: Programmatically executes commands with zero LLM involvement — 100% deterministic
5. **Phase 4 (Dynamic Update)**: Evaluates results and updates the remaining step list using VEXIS commands like `Summary_of_Progress [...]` and `step_list [...]`
6. **Phase 5 (Verification)**: LLM reviews the full execution log to confirm true success and detect hidden failures
7. **Phase 6 (Summarization)**: Generates the final user-facing report
8. **Phase 7 (Bot User Review)**: LLM reviews the entire conversation and can feed corrections back into the pipeline

### Action Type System

The pipeline classifies intent into explicit action types:
- `run_command` — Execute shell commands
- `write_file` — Write content to files
- `read_file` — Read file contents
- `search` — Search file contents across the project
- `list_files` — List files and directories
- `keep_text` — Store text in memory records
- `keep_file` — Store file snapshots in memory
- `answer_directly` — Provide a direct answer without command execution
- `ask_user` — Ask the user for clarification

### DAG-Based Task Execution

The engine supports directed acyclic graph (DAG) task structures where each task can declare dependencies:
```
id: task_1
action: Install dependencies
waiting_for: []

id: task_2
action: Run build
waiting_for: ["task_1"]
```

### Native Action Formats

In addition to shell commands, the engine supports:
- `read_file("path")` — Read file contents
- `search("pattern", "path")` — Search file contents (read-only)
- `list_files("path")` — List files and directories (read-only)
- `write_file("path")` — Write content to a file
- `keep_text("content")` — Store text in memory
- `keep_file("path")` — Store a file snapshot
- `<str_replace>` blocks — Targeted text replacement in existing files
- `hack("command")` — Custom command placeholder (logged, not executed)

### Task Verification

The Phase 5 verification system checks whether the original task was truly successful by analyzing the complete execution log. If issues are found, recovery steps are generated and executed before proceeding to summarization.

### Error Recovery

Automatic error recovery mechanisms:
- **Retry Logic**: Automatic retries for transient failures with exponential backoff
- **Provider Fallback**: Seamless switching to alternative providers on failure
- **Context Compression**: Automatic context compression at iteration intervals (every 10 iterations) to prevent unbounded growth
- **/KG Command**: Resume a timed-out task with doubled timeout
- **Partial Context Preservation**: When a task is cancelled by a newer request, completed steps are saved to conversation history

---

## Troubleshooting

### Common Issues

#### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve

# Check connection
curl http://localhost:11434/api/tags
```

#### Permission Errors (macOS)

1. **Full Disk Access**:
   - Go to System Preferences > Security & Privacy > Privacy
   - Add Terminal to Full Disk Access

2. **Permission Fix**:
   ```bash
   chmod +x run.py
   ```

#### Model Compatibility Issues

Some models may have compatibility issues. Recommended alternatives:
- `llama3.2:3b` — Most stable local model
- `qwen2.5:3b` — Lightweight and reliable
- `deepseek-r1:7b` — Advanced reasoning
- Cloud providers like Groq or Google for production use

#### Dependency Issues

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Update pip
pip install --upgrade pip

# Clean install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug Mode

Enable verbose logging:

```bash
python3 run.py "your command" --debug
```

### Getting Help

1. Check the [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)
2. Review [Error Handling Documentation](./docs/ERROR_HANDLING.md)
3. Check GitHub Issues
4. Join community discussions

---

## Best Practices

### Performance Optimization

1. **Choose the Right Model**:
   - Local: `llama3.2:3b` or `llama-4-scout-17b` for balance
   - Cloud: Google Gemini for reliability, Groq for speed

2. **Optimize Commands**:
   - Be specific in your instructions
   - Break complex tasks into smaller steps
   - Use appropriate model for task complexity

### Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Local Models**: Use Ollama for sensitive data
3. **Network**: Use secure connections for cloud providers
4. **File Paths**: The system validates paths against sensitive directories

### Productivity Tips

1. **Aliases**: Create shell aliases for common tasks
2. **Configuration**: Fine-tune settings for your workflow
3. **Interactive Mode**: Use for maintaining context across multiple commands
4. **Telegram Mode**: Use for remote monitoring and control

---

## FAQ

### Q: Which provider should I use?
**A**: For privacy: Ollama. For speed: Groq. For reliability: Google Gemini. For the latest models: OpenRouter.

### Q: How do I handle large tasks?
**A**: Break them into smaller, specific commands for better results. The pipeline handles multi-step tasks automatically.

### Q: Can I use multiple providers?
**A**: Yes, configure fallback providers. The system will automatically switch if a provider fails.

### Q: Is my data secure?
**A**: Local Ollama models keep data on your machine. Cloud providers send data to their servers.

### Q: How do I update VEXIS-CLI-3?
**A**: `git pull origin main` and reinstall dependencies if needed.

### Q: What's the /KG command?
**A**: Keep Going — resume a timed-out task from where it left off, with doubled timeout.

---

## Support & Community

- **Documentation**: [Full docs](./docs/)
- **Issues**: [GitHub Issues](https://github.com/AInohogosya/VEXIS-CLI-3/issues)
- **Updates**: Check the repository regularly for updates

---

**Version**: 3.0.0
**Last Updated**: 2026-06-01
**Compatibility**: Python 3.8+
