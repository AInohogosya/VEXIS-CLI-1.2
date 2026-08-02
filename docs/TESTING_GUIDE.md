# Testing Guide

## Table of Contents

- [Overview](#overview)
- [Testing Philosophy](#testing-philosophy)
- [Test Pyramid](#test-pyramid)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Phase-Specific Testing](#phase-specific-testing)
- [Provider Testing](#provider-testing)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)
- [Test Configuration](#test-configuration)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

---

## Overview

This guide covers the comprehensive testing strategy for the VEXIS-CLI-3 6-Phase Architecture system. It includes testing approaches for all layers — from unit tests for individual components to end-to-end tests for complete phase workflows.

### Testing Goals

| Goal | Target | Measurement |
|------|--------|-------------|
| Code Coverage | > 85% | Line + branch coverage |
| Unit Test Pass Rate | > 99% | Per commit |
| Integration Test Pass Rate | > 95% | Per PR |
| E2E Test Pass Rate | > 90% | Per release |
| Test Execution Time | < 10 min | Full suite |
| Flaky Test Rate | < 1% | Per week |

---

## Testing Philosophy

### Core Principles

1. **Test Behavior, Not Implementation**: Focus on what the code does, not how it does it
2. **Fast Feedback**: Tests should run quickly and provide immediate feedback
3. **Deterministic**: Tests should produce the same results every time
4. **Independent**: Tests should not depend on each other
5. **Readable**: Tests should be easy to understand and maintain

### Testing Layers

```
┌─────────────────────────────────────────────┐
│              E2E Tests                       │
│  (Full phase workflows, user journeys)       │
│  Slow, expensive, high confidence            │
├─────────────────────────────────────────────┤
│           Integration Tests                  │
│  (Component interactions, API contracts)     │
│  Medium speed, medium confidence             │
├─────────────────────────────────────────────┤
│              Unit Tests                      │
│  (Individual functions, classes)             │
│  Fast, cheap, high volume                    │
└─────────────────────────────────────────────┘
```

---

## Test Pyramid

### Distribution

```
        /\
       /  \
      / E2E\        5% of tests, high confidence
     /------\
    / Integ. \      20% of tests, medium confidence
   /----------\
  /   Unit     \    75% of tests, fast feedback
 /--------------\
```

### Test Counts by Phase

| Phase | Unit Tests | Integration Tests | E2E Tests |
|-------|-----------|-------------------|-----------|
| Phase 1 | 50 | 10 | 3 |
| Phase 2 | 60 | 12 | 3 |
| Phase 3 | 80 | 15 | 5 |
| Phase 4 | 40 | 20 | 4 |
| Phase 5 | 30 | 10 | 2 |
| Phase 6 | 20 | 8 | 2 |
| **Total** | **280** | **75** | **19** |

---

## Unit Testing

### Framework Setup

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_provider():
    """Create a mock AI provider."""
    provider = AsyncMock()
    provider.name = "mock"
    provider.complete.return_value = Completion(
        content="Mock response",
        model="mock-model",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    return provider

@pytest.fixture
def mock_cache():
    """Create a mock cache."""
    cache = AsyncMock()
    cache.get.return_value = None
    return cache

@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        id="test-001",
        phase_id=1,
        type="analysis",
        prompt="Analyze this requirement",
        max_tokens=4096,
        temperature=0.7,
    )
```

### Testing Phase Tasks

```python
# tests/unit/test_phase1.py
import pytest
from unittest.mock import AsyncMock, patch

class TestRequirementsAnalysisTask:
    """Unit tests for Requirements Analysis Task."""

    @pytest.fixture
    def task(self, mock_provider):
        return RequirementsAnalysisTask(provider=mock_provider)

    @pytest.mark.asyncio
    async def test_decompose_requirements(self, task):
        """Test that requirements are properly decomposed."""
        requirements = RequirementsDocument(
            content="Build a REST API with authentication and rate limiting."
        )

        result = await task.execute(requirements)

        assert len(result.items) >= 2
        assert any("REST API" in item.description for item in result.items)
        assert any("authentication" in item.description.lower() for item in result.items)

    @pytest.mark.asyncio
    async def test_classify_requirements(self, task):
        """Test that requirements are properly classified."""
        requirements = RequirementsDocument(
            content="The system must respond within 200ms."
        )

        result = await task.execute(requirements)

        assert result.items[0].type == "non-functional"
        assert result.items[0].priority in ["critical", "high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_detect_conflicts(self, task):
        """Test that conflicting requirements are detected."""
        requirements = RequirementsDocument(
            content="""
            - The system must store all data locally.
            - The system must use cloud storage for all data.
            """
        )

        result = await task.execute(requirements)

        assert len(result.conflicts) > 0

    @pytest.mark.asyncio
    async def test_empty_requirements(self, task):
        """Test handling of empty requirements."""
        requirements = RequirementsDocument(content="")

        result = await task.execute(requirements)

        assert len(result.items) == 0
        assert len(result.gaps) > 0

    @pytest.mark.asyncio
    async def test_provider_error_handling(self, mock_provider):
        """Test that provider errors are handled gracefully."""
        mock_provider.complete.side_effect = ProviderError("API error")
        task = RequirementsAnalysisTask(provider=mock_provider)

        requirements = RequirementsDocument(content="Build a REST API.")

        with pytest.raises(ProviderError):
            await task.execute(requirements)


class TestFeasibilityEvaluationTask:
    """Unit tests for Feasibility Evaluation Task."""

    @pytest.mark.asyncio
    async def test_technical_feasibility(self):
        """Test technical feasibility evaluation."""
        task = FeasibilityEvaluationTask(provider=AsyncMock())
        analysis = AnalysisResult(items=[
            ClassifiedRequirement(
                item=RequirementItem(description="Build a REST API"),
                type="functional",
                priority="high",
                complexity="moderate",
                dependencies=[],
            )
        ])
        constraints = Constraints(
            budget=100000,
            timeline=90,
            resources=["python", "postgresql"]
        )

        result = await task.execute(analysis, constraints)

        assert len(result.evaluations) == 1
        assert 0 <= result.evaluations[0].overall <= 1
```

### Testing Error Handlers

```python
# tests/unit/test_error_handling.py
class TestErrorHandler:
    """Unit tests for error handling system."""

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry mechanism with exponential backoff."""
        handler = ErrorHandler(max_retries=3, backoff_factor=1.0)
        call_count = 0

        @handler.with_retry
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError("Temporary failure")
            return "success"

        result = await flaky_operation()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker pattern."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
        )

        call_count = 0

        @breaker.protect
        async def failing_operation():
            nonlocal call_count
            call_count += 1
            raise TransientError("Always fails")

        # First 3 calls should attempt execution
        for _ in range(3):
            with pytest.raises(TransientError):
                await failing_operation()

        # 4th call should be rejected by circuit breaker
        with pytest.raises(CircuitOpenError):
            await failing_operation()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_bulkhead_pattern(self):
        """Test bulkhead isolation pattern."""
        bulkhead = Bulkhead(max_concurrent=2, max_wait=1)

        @bulkhead.protect
        async def slow_operation():
            await asyncio.sleep(0.5)
            return "done"

        # First 2 should succeed
        results = await asyncio.gather(
            slow_operation(),
            slow_operation(),
        )
        assert all(r == "done" for r in results)

        # Third should be rejected when first 2 are still running
        with pytest.raises(BulkheadFullError):
            await asyncio.gather(
                slow_operation(),
                slow_operation(),
                slow_operation(),
            )
```

---

## Integration Testing

### Test Setup

```python
# tests/integration/conftest.py
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def postgres():
    """Start a PostgreSQL container for integration tests."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis():
    """Start a Redis container for integration tests."""
    with RedisContainer("redis:7") as redis:
        yield redis

@pytest_asyncio.fixture
async def db_session(postgres):
    """Create a database session for testing."""
    engine = create_async_engine(postgres.get_connection_url())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Phase Integration Tests

```python
# tests/integration/test_phase_flow.py
class TestPhase1ToPhase2Flow:
    """Integration test for Phase 1 -> Phase 2 handoff."""

    @pytest.mark.asyncio
    async def test_phase1_output_feeds_phase2(self, db_session):
        """Test that Phase 1 output is valid input for Phase 2."""
        # Execute Phase 1
        phase1 = Phase1Executor(
            provider=MockProvider(),
            db=db_session,
        )
        assessment = await phase1.execute(
            requirements=RequirementsDocument(content="Build a microservice for user management"),
            constraints=Constraints(budget=50000, timeline=60),
        )

        # Verify Phase 1 output
        assert assessment is not None
        assert len(assessment.requirements_analysis.items) > 0
        assert assessment.feasibility_report is not None

        # Feed into Phase 2
        phase2 = Phase2Executor(
            provider=MockProvider(),
            db=db_session,
        )
        design = await phase2.execute(assessment=assessment)

        # Verify Phase 2 output
        assert design is not None
        assert len(design.component_design.components) > 0
        assert design.data_model is not None

    @pytest.mark.asyncio
    async def test_gate_validation(self, db_session):
        """Test that gate validation works correctly."""
        phase1 = Phase1Executor(
            provider=MockProvider(),
            db=db_session,
        )

        # Create a minimal assessment
        assessment = StrategicAssessment(
            requirements_analysis=AnalysisResult(items=[]),
            feasibility_report=FeasibilityReport(evaluations=[]),
            risk_assessment=RiskAssessment(risks=[]),
        )

        gate = StrategicReviewGate()
        result = await gate.validate(assessment)

        # Should fail with empty assessment
        assert not result.passed
        assert result.score < 0.7
```

### Provider Integration Tests

```python
# tests/integration/test_providers.py
class TestProviderIntegration:
    """Integration tests with real providers (optional)."""

    @pytest.fixture
    def real_provider(self):
        """Create a real provider (skipped if no API key)."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            pytest.skip("GROQ_API_KEY not set")
        return GroqProvider(api_key=api_key)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_groq_completion(self, real_provider):
        """Test actual Groq API call."""
        result = await real_provider.complete(
            messages=[Message(role="user", content="Say hello")],
            model="llama3-8b-8192",
            max_tokens=50,
        )

        assert result.content
        assert result.total_tokens > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fallback_chain(self):
        """Test fallback chain with real providers."""
        manager = ProviderManager(config=ProviderConfig(
            providers=[
                ProviderConfig(name="primary", type="groq", api_key="invalid"),
                ProviderConfig(name="fallback", type="ollama"),
            ]
        ))

        # Should fall back to Ollama when Groq fails
        result = await manager.complete(
            messages=[Message(role="user", content="Hello")],
            task=Task(phase_id=1, max_tokens=50),
        )

        assert result is not None
```

---

## End-to-End Testing

### Full Workflow Tests

```python
# tests/e2e/test_full_workflow.py
class TestFull6PhaseWorkflow:
    """End-to-end tests for the complete 6-phase workflow."""

    @pytest.fixture
    def workflow_env(self):
        """Set up the full workflow test environment."""
        return WorkflowEnvironment(
            provider=MockProvider(responses={
                "phase1": MockResponses.strategic_assessment(),
                "phase2": MockResponses.architecture_design(),
                "phase3": MockResponses.pilot_implementation(),
                "phase4": MockResponses.integration_scaling(),
                "phase5": MockResponses.optimization_governance(),
                "phase6": MockResponses.enterprise_transformation(),
            }),
            db=TestDatabase(),
            cache=TestCache(),
        )

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_workflow(self, workflow_env):
        """Test the complete 6-phase workflow end-to-end."""
        orchestrator = PhaseOrchestrator(
            provider=workflow_env.provider,
            db=workflow_env.db,
            cache=workflow_env.cache,
        )

        result = await orchestrator.execute(
            input=WorkflowInput(
                requirements="Build a task management API with user authentication",
                constraints=Constraints(budget=100000, timeline=120),
            )
        )

        # Verify all phases completed
        assert result.phase_results[1].state == PhaseState.COMPLETED
        assert result.phase_results[2].state == PhaseState.COMPLETED
        assert result.phase_results[3].state == PhaseState.COMPLETED
        assert result.phase_results[4].state == PhaseState.COMPLETED
        assert result.phase_results[5].state == PhaseState.COMPLETED
        assert result.phase_results[6].state == PhaseState.COMPLETED

        # Verify artifacts were produced
        assert result.artifacts["requirements_breakdown.md"]
        assert result.artifacts["architecture_design.md"]
        assert result.artifacts["src/"]
        assert result.artifacts["adoption_plan.md"]

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_workflow_with_gate_rejection(self, workflow_env):
        """Test workflow when a gate rejects and requires revision."""
        # Configure Phase 2 gate to reject
        workflow_env.gate_overrides[2] = GateOverride(
            min_score=0.99  # Impossibly high score
        )

        orchestrator = PhaseOrchestrator(
            provider=workflow_env.provider,
            db=workflow_env.db,
            gate_overrides=workflow_env.gate_overrides,
        )

        result = await orchestrator.execute(
            input=WorkflowInput(
                requirements="Build a simple API",
                constraints=Constraints(budget=10000, timeline=30),
            )
        )

        # Phase 2 should be rejected
        assert result.phase_results[2].state == PhaseState.REJECTED
        # Should have retry attempts
        assert result.phase_results[2].retry_count > 0
```

---

## Phase-Specific Testing

### Phase 3: Implementation Testing

```python
# tests/unit/test_phase3_implementation.py
class TestPilotImplementation:
    """Tests for Phase 3 pilot implementation."""

    @pytest.mark.asyncio
    async def test_code_generation(self):
        """Test that generated code is syntactically valid."""
        task = ComponentImplementationTask(provider=AsyncMock())
        component = Component(
            name="UserService",
            purpose="Manage user accounts",
            interface=["create_user", "get_user", "update_user", "delete_user"],
        )

        code = await task.implement_component(component, MockDesign())

        # Verify generated code is valid Python
        compile(code.main_file, "<string>", "exec")

    @pytest.mark.asyncio
    async def test_test_generation(self):
        """Test that generated tests are valid and pass."""
        task = TestExecutionTask()
        implementation = MockImplementation(
            files={"user_service.py": "def create_user(name): return {'name': name}"}
        )

        tests = await task.generate_tests(
            component=MockComponent(name="UserService"),
            code=implementation,
        )

        # Verify tests are valid Python
        for test_file in tests:
            compile(test_file.content, "<string>", "exec")

    @pytest.mark.asyncio
    async def test_sandbox_execution(self):
        """Test that code runs in sandboxed environment."""
        sandbox = Sandbox(
            memory_limit="256m",
            cpu_limit=1.0,
            network="none",
            timeout=30,
        )

        result = await sandbox.execute("print('hello')")

        assert result.exit_code == 0
        assert "hello" in result.stdout
```

---

## Provider Testing

### Mock Provider

```python
# tests/mocks/mock_provider.py
class MockProvider(AIProvider):
    """Configurable mock provider for testing."""

    def __init__(self, responses: dict[str, Any] = None):
        self._name = "mock"
        self.responses = responses or {}
        self.call_history: list[dict] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            models=["mock-model"],
            max_tokens=16384,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=False,
        )

    async def complete(
        self,
        messages: list[Message],
        model: str = "mock-model",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> Completion:
        self.call_history.append({
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })

        # Return configured response or default
        response_key = kwargs.get("phase", "default")
        content = self.responses.get(response_key, "Mock response")

        return Completion(
            content=content,
            model=model,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )

    async def health_check(self) -> HealthStatus:
        return HealthStatus(healthy=True, latency_ms=1.0)

    def estimate_cost(self, tokens: int, model: str) -> float:
        return 0.0
```

---

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py
class TestPhasePerformance:
    """Performance tests for phase execution."""

    @pytest.mark.performance
    async def test_phase1_throughput(self):
        """Test Phase 1 throughput under load."""
        phase1 = Phase1Executor(provider=MockProvider())

        start = time.monotonic()
        tasks = [
            phase1.execute(
                requirements=RequirementsDocument(content=f"Requirement {i}"),
                constraints=Constraints(budget=10000, timeline=30),
            )
            for i in range(100)
        ]
        results = await asyncio.gather(*tasks)
        duration = time.monotonic() - start

        assert len(results) == 100
        assert duration < 30  # Should complete within 30 seconds

    @pytest.mark.performance
    async def test_provider_latency(self):
        """Test provider response latency."""
        provider = MockProvider()

        latencies = []
        for _ in range(50):
            start = time.monotonic()
            await provider.complete(
                messages=[Message(role="user", content="Hello")],
                model="mock-model",
            )
            latencies.append((time.monotonic() - start) * 1000)

        p50 = sorted(latencies)[len(latencies) // 2]
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]

        assert p50 < 100  # p50 < 100ms
        assert p95 < 200  # p95 < 200ms
        assert p99 < 500  # p99 < 500ms
```

---

## Security Testing

```python
# tests/security/test_security.py
class TestSecurity:
    """Security-focused tests."""

    def test_api_key_not_logged(self, caplog):
        """Test that API keys are never logged."""
        config = Config(providers=[
            ProviderConfig(name="test", api_key="secret-key-12345")
        ])

        logger.info(f"Config loaded: {config}")

        assert "secret-key-12345" not in caplog.text

    def test_input_sanitization(self):
        """Test that user inputs are sanitized."""
        malicious_input = "Requirement'; DROP TABLE users; --"
        sanitized = sanitize_input(malicious_input)

        assert "DROP TABLE" not in sanitized
        assert ";" not in sanitized

    @pytest.mark.asyncio
    async def test_sandbox_escape_prevention(self):
        """Test that sandbox prevents code escape."""
        sandbox = Sandbox(network="none", filesystem="readonly")

        result = await sandbox.execute(
            "import os; os.system('rm -rf /')"
        )

        # Should fail or be blocked
        assert result.exit_code != 0 or "Permission denied" in result.stderr
```

---

## Test Configuration

### pytest Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (requires services)
    e2e: End-to-end tests (full workflow)
    performance: Performance tests (load, latency)
    security: Security-focused tests
    slow: Slow tests (skip in quick mode)

addopts =
    --strict-markers
    --tb=short
    -v
    --cov=vexis
    --cov-report=html
    --cov-report=term-missing

filterwarnings =
    ignore::DeprecationWarning
```

### Running Tests

```bash
# Run all unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run E2E tests
pytest -m e2e

# Run with coverage
pytest --cov=vexis --cov-report=html

# Run performance tests
pytest -m performance

# Run security tests
pytest -m security

# Run all tests
pytest

# Run quick mode (skip slow tests)
pytest -m "not slow"

# Run specific phase tests
pytest tests/unit/test_phase1.py -v

# Run with parallel execution
pytest -n auto
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest -m unit --cov=vexis --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest -m integration -v

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest -m e2e -v
```

---

## Best Practices

### Writing Good Tests

1. **One assertion per concept**: Each test should verify one thing
2. **Use descriptive names**: Test names should describe the scenario
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use fixtures**: Share setup code across tests
5. **Mock external dependencies**: Isolate the code under test

### Test Maintenance

1. **Review test coverage weekly**: Identify untested code
2. **Fix flaky tests immediately**: Don't let them accumulate
3. **Update tests with code changes**: Keep tests in sync
4. **Delete obsolete tests**: Remove tests for removed features
5. **Refactor test code**: Keep tests clean and maintainable

### Anti-Patterns to Avoid

1. **Testing implementation details**: Test behavior, not internals
2. **Dependent tests**: Tests should not rely on execution order
3. **Slow unit tests**: Unit tests should be fast (< 100ms each)
4. **Over-mocking**: Don't mock everything — use real objects when practical
5. **Ignoring test failures**: Fix failures immediately, don't skip
