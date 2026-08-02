# Contributing to VEXIS-CLI-3

Thank you for your interest in contributing! This document describes the workflow, standards, and expectations for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Workflow](#contribution-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Requests](#pull-requests)
- [Security](#security)

## Code of Conduct

Be respectful, constructive, and inclusive. Harassment or exclusionary behavior will not be tolerated.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally.
3. Set up the development environment (below).
4. Create a branch for your change.

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- (Optional) [uv](https://docs.astral.sh/uv/) for faster package management

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/VEXIS-CLI-3.git
cd VEXIS-CLI-3

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys (never commit this file!)
```

### Using uv (Recommended)

```bash
git clone https://github.com/YOUR_USERNAME/VEXIS-CLI-3.git
cd VEXIS-CLI-3
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Contribution Workflow

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make focused changes**: Keep changes small and atomic.
3. **Add/update tests**: Every bug fix and feature needs tests.
4. **Update documentation**: Keep docs in sync with code changes.
5. **Run checks**: See [Before Submitting](#before-submitting) below.
6. **Commit**: Write clear commit messages.
7. **Push and open a PR**: Target the `main` branch.

## Code Standards

### Style

- **Formatter**: Black (line length 100)
- **Import sorting**: isort (compatible with Black)
- **Linter**: flake8
- **Type hints**: mypy (where practical)

```bash
# Auto-format
black src/ run.py agent_core.py
isort src/ run.py agent_core.py

# Lint
flake8 src/ run.py agent_core.py --max-line-length=100
mypy src/ --ignore-missing-imports
```

### Rules

- Keep command execution deterministic and auditable.
- Do not add LLM-based command extraction to Phase 3.
- Mask secrets in logs and error messages.
- Keep provider-specific code isolated in provider modules.
- Add configuration fields through dataclasses and `config.example.yaml`.
- Preserve backward compatibility for existing config keys where practical.
- Do not add try/catch blocks around imports.
- Use environment variables or `.env` files for secrets — never hardcode them.

## Testing

### Running Tests

```bash
# Full test suite
pytest

# Unit tests only
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_security.py -v

# With coverage
pytest --cov=src --cov-report=term-missing
```

### What to Test

Add unit tests for:

- New command parsing behavior
- New security rules
- New exception categories or retry rules
- Provider fallback changes
- Telegram queue or cancellation behavior
- Cost/cache persistence changes
- Configuration validation

### Test Markers

- `@pytest.mark.unit` — Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` — Integration tests (may need API keys)
- `@pytest.mark.e2e` — End-to-end tests
- `@pytest.mark.slow` — Slow tests (skipped in quick runs)

## Documentation

Update docs whenever behavior changes:

| Change Type | Documents to Update |
|---|---|
| Pipeline behavior | `docs/ARCHITECTURE.md`, `docs/RUNTIME_FLOW.md` |
| Configuration | `docs/CONFIGURATION.md`, `config.example.yaml` |
| Providers | `docs/PROVIDERS.md` |
| Command execution | `docs/COMMAND_EXECUTION.md` |
| Public APIs | `docs/API_REFERENCE.md`, `docs/MODULE_INVENTORY.md` |
| Errors | `docs/ERROR_HANDLING.md`, `docs/TROUBLESHOOTING.md` |

## Pull Requests

### Before Submitting

Run at least:

```bash
black --check src/ run.py agent_core.py
isort --check-only src/ run.py agent_core.py
pytest tests/unit/ -v
python3 system_check.py
```

### PR Description Template

Every PR should include:

1. **Summary** — What changed and why
2. **Related Issues** — Link to any related issues
3. **Type of Change** — Bug fix / feature / breaking / docs
4. **Testing** — What tests were run and their results
5. **Screenshots** — Only if a visible UI changed
6. **Checklist**:
   - Code follows style guidelines
   - Self-reviewed
   - Tests added/updated
   - Documentation updated
   - No secrets committed

### Review Process

- All PRs require at least one review approval.
- CI checks (lint, test) must pass.
- Address review comments promptly.
- Squash commits before merging if requested.

## Security

- **Never commit API keys, tokens, or secrets.**
- Use `.env` files (already in `.gitignore`) or environment variables.
- Report security vulnerabilities via email, not public issues.
- Follow the principle of least privilege for API integrations.

## Getting Help

- **Documentation**: [docs/](./)
- **Issues**: [GitHub Issues](https://github.com/AInohogosya/VEXIS-CLI-3/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AInohogosya/VEXIS-CLI-3/discussions)

---

🙏 Thank you for helping make VEXIS-CLI-3 better!
