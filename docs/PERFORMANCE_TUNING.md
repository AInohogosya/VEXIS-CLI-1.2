# Performance Tuning Guide

## Table of Contents

- [Overview](#overview)
- [Performance Philosophy](#performance-philosophy)
- [Benchmarking Framework](#benchmarking-framework)
- [Phase-Level Performance](#phase-level-performance)
- [Provider Performance](#provider-performance)
- [Database Optimization](#database-optimization)
- [Caching Strategies](#caching-strategies)
- [Memory Management](#memory-management)
- [Concurrency and Parallelism](#concurrency-and-parallelism)
- [Network Optimization](#network-optimization)
- [AI Model Optimization](#ai-model-optimization)
- [Monitoring and Profiling](#monitoring-and-profiling)
- [Performance Checklist](#performance-checklist)

---

## Overview

This guide provides comprehensive performance tuning strategies for the VEXIS-CLI 6-Phase Architecture system. It covers optimization techniques across all layers — from AI provider selection and database tuning to caching strategies and concurrency models.

### Performance Goals

| Metric | Target | Critical Threshold |
|--------|--------|--------------------|
| API Response Time (p50) | < 100ms | > 500ms |
| API Response Time (p99) | < 500ms | > 2s |
| Task Execution Time | < 30s | > 120s |
| Database Query Time (p95) | < 50ms | > 200ms |
| Cache Hit Rate | > 90% | < 70% |
| Memory Usage | < 70% | > 90% |
| CPU Usage | < 60% | > 85% |
| Error Rate | < 0.1% | > 1% |

---

## Performance Philosophy

### Core Principles

1. **Measure First, Optimize Second**: Never optimize without profiling data
2. **Bottleneck-Driven**: Focus on the slowest component first
3. **Horizontal Before Vertical**: Scale out before scaling up
4. **Cache Aggressively**: Reduce redundant computation at every layer
5. **Fail Fast**: Detect and handle performance degradation early

### Performance Layers

```
┌─────────────────────────────────────────────┐
│              Client Layer                     │
│  (Connection pooling, Request batching)       │
├─────────────────────────────────────────────┤
│              API Gateway                      │
│  (Rate limiting, Load balancing)              │
├─────────────────────────────────────────────┤
│              Application Layer                │
│  (Caching, Concurrency, Async I/O)            │
├─────────────────────────────────────────────┤
│              AI Provider Layer                │
│  (Model selection, Fallback chains)           │
├─────────────────────────────────────────────┤
│              Data Layer                       │
│  (Query optimization, Indexing, Pooling)      │
├─────────────────────────────────────────────┤
│              Infrastructure Layer             │
│  (CPU, Memory, Network, Disk I/O)             │
└─────────────────────────────────────────────┘
```

---

## Benchmarking Framework

### Running Benchmarks

```bash
# Full system benchmark
python -m vexis benchmark --full --output report.json

# Phase-specific benchmark
python -m vexis benchmark --phase 3 --iterations 100

# Provider latency comparison
python -m vexis benchmark --providers groq,openai,ollama --model llama3

# Database query benchmark
python -m vexis benchmark --database --queries 1000

# Cache performance benchmark
python -m vexis benchmark --cache --hit-ratio-target 0.95
```

### Benchmark Configuration

```yaml
# benchmark.yaml
benchmark:
  warmup_iterations: 10
  measurement_iterations: 100
  confidence_level: 0.95
  timeout_seconds: 300

  phases:
    - id: 1
      name: "Strategic Assessment"
      tasks: ["analyze", "evaluate", "prioritize"]
    - id: 2
      name: "Architecture Design"
      tasks: ["design", "model", "validate"]
    - id: 3
      name: "Pilot Implementation"
      tasks: ["implement", "test", "verify"]
    - id: 4
      name: "Integration & Scaling"
      tasks: ["integrate", "scale", "monitor"]
    - id: 5
      name: "Optimization & Governance"
      tasks: ["optimize", "govern", "audit"]
    - id: 6
      name: "Enterprise Transformation"
      tasks: ["transform", "evolve", "sustain"]

  providers:
    - name: "groq"
      models: ["llama3-70b-8192", "mixtral-8x7b-32768"]
    - name: "openai"
      models: ["gpt-4o", "gpt-4o-mini"]
    - name: "ollama"
      models: ["llama3", "mistral", "codellama"]

  report:
    format: "json"
    include_percentiles: [50, 90, 95, 99]
    include_histograms: true
```

### Interpreting Results

```json
{
  "benchmark_id": "bench_20240524_001",
  "timestamp": "2024-05-24T10:00:00Z",
  "summary": {
    "total_tasks": 600,
    "total_duration_sec": 45.2,
    "avg_latency_ms": 75.3,
    "p50_ms": 62.1,
    "p95_ms": 145.8,
    "p99_ms": 289.4,
    "throughput_tps": 13.27,
    "error_rate": 0.003
  },
  "phase_results": [
    {
      "phase": 1,
      "avg_latency_ms": 45.2,
      "throughput_tps": 22.1,
      "bottleneck": "ai_provider"
    }
  ]
}
```

---

## Phase-Level Performance

### Phase 1: Strategic Assessment

**Typical Bottlenecks**: AI provider latency, input parsing

```python
# Optimization: Batch assessment requests
class StrategicAssessmentOptimizer:
    def batch_analyze(self, items: list[AssessmentItem]) -> list[Assessment]:
        """Batch multiple assessment items into a single AI call."""
        # Instead of N individual calls, make 1 batched call
        prompt = self._build_batch_prompt(items)
        response = self.provider.complete(prompt)
        return self._parse_batch_response(response, items)

    def _build_batch_prompt(self, items: list[AssessmentItem]) -> str:
        sections = []
        for i, item in enumerate(items):
            sections.append(f"Item {i + 1}: {item.description}")
        return f"Assess the following items:\n" + "\n".join(sections)
```

**Tuning Parameters**:

```yaml
phase_1:
  batch_size: 10              # Items per batch
  cache_ttl: 3600             # Cache assessments for 1 hour
  timeout: 30                 # Max seconds per assessment
  max_input_tokens: 4096      # Limit input size
  parallel_batches: 3         # Concurrent batch requests
```

### Phase 2: Architecture Design

**Typical Bottlenecks**: Complex reasoning, large context windows

```python
# Optimization: Incremental design with caching
class ArchitectureDesignOptimizer:
    def design_incrementally(self, requirements: Requirements) -> Architecture:
        """Build architecture incrementally, caching intermediate results."""
        # Check cache for similar requirements
        cache_key = self._compute_similarity_key(requirements)
        cached = self.cache.get(cache_key)
        if cached and cached.similarity > 0.95:
            return cached.architecture

        # Build in stages, caching each stage
        components = self._design_components(requirements)
        self.cache.set(f"{cache_key}:components", components, ttl=7200)

        interfaces = self._design_interfaces(components)
        self.cache.set(f"{cache_key}:interfaces", interfaces, ttl=7200)

        return Architecture(components=components, interfaces=interfaces)
```

**Tuning Parameters**:

```yaml
phase_2:
  incremental_design: true
  component_cache_ttl: 7200
  max_components_per_request: 20
  context_compression: true
  design_timeout: 60
```

### Phase 3: Pilot Implementation

**Typical Bottlenecks**: Code generation, file I/O, test execution

```python
# Optimization: Parallel file generation with async I/O
class PilotImplementationOptimizer:
    async def implement_parallel(self, design: Design) -> Implementation:
        """Generate implementation files in parallel."""
        tasks = []
        for component in design.components:
            task = asyncio.create_task(
                self._generate_component(component)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._assemble_implementation(results)

    async def _generate_component(self, component: Component) -> ComponentCode:
        """Generate code for a single component asynchronously."""
        code = await self.provider.acomplete(
            prompt=self._build_prompt(component),
            max_tokens=8192
        )
        return ComponentCode(component=component, code=code)
```

**Tuning Parameters**:

```yaml
phase_3:
  parallel_generation: true
  max_concurrent_files: 5
  file_write_buffer_size: 65536
  test_execution_timeout: 120
  sandbox_memory_limit: "512m"
  sandbox_cpu_limit: 1.0
```

### Phase 4: Integration & Scaling

**Typical Bottlenecks**: Network I/O, service discovery, load balancing

```yaml
phase_4:
  connection_pool_size: 20
  connection_pool_max_overflow: 10
  connection_pool_recycle: 3600
  health_check_interval: 10
  circuit_breaker_threshold: 5
  circuit_breaker_timeout: 30
  retry_max_attempts: 3
  retry_backoff_factor: 2.0
```

### Phase 5: Optimization & Governance

**Typical Bottlenecks**: Metrics collection, audit logging, policy evaluation

```yaml
phase_5:
  metrics_batch_size: 100
  metrics_flush_interval: 15
  audit_log_buffer_size: 1000
  policy_cache_ttl: 300
  governance_scan_interval: 3600
  optimization_parallelism: 4
```

### Phase 6: Enterprise Transformation

**Typical Bottlenecks**: Large-scale data processing, cross-system coordination

```yaml
phase_6:
  batch_processing_size: 500
  event_queue_size: 10000
  saga_timeout: 300
  compensation_retry_count: 3
  transformation_parallelism: 8
  data_pipeline_workers: 4
```

---

## Provider Performance

### Provider Selection Strategy

```python
class ProviderPerformanceRouter:
    """Route requests to the best-performing provider."""

    def __init__(self, providers: list[Provider]):
        self.providers = providers
        self.metrics: dict[str, ProviderMetrics] = {}

    def select_provider(self, task: Task) -> Provider:
        """Select the optimal provider based on current performance."""
        candidates = []
        for provider in self.providers:
            metrics = self.metrics.get(provider.name)
            if not metrics or not metrics.is_healthy():
                continue

            score = self._compute_score(provider, metrics, task)
            candidates.append((provider, score))

        if not candidates:
            raise NoHealthyProviderError("No healthy providers available")

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _compute_score(
        self, provider: Provider, metrics: ProviderMetrics, task: Task
    ) -> float:
        """Compute a performance score for a provider-task pair."""
        latency_score = 1.0 / (1.0 + metrics.avg_latency_ms / 1000.0)
        success_score = metrics.success_rate
        cost_score = 1.0 / (1.0 + metrics.cost_per_token * 1000)
        capability_score = 1.0 if task.model in provider.models else 0.3

        return (
            0.35 * latency_score
            + 0.30 * success_score
            + 0.15 * cost_score
            + 0.20 * capability_score
        )
```

### Provider-Specific Tuning

#### Groq

```yaml
groq:
  max_tokens: 8192
  temperature: 0.7
  top_p: 0.9
  timeout: 30
  # Groq is optimized for inference speed
  # Use for: real-time tasks, low-latency requirements
  preferred_for:
    - phase_1_assessment
    - phase_3_code_generation
    - quick_analysis
```

#### OpenAI

```yaml
openai:
  max_tokens: 16384
  temperature: 0.5
  top_p: 0.95
  timeout: 60
  # OpenAI offers the best reasoning capabilities
  # Use for: complex design, architecture decisions
  preferred_for:
    - phase_2_architecture_design
    - phase_5_governance
    - complex_reasoning
```

#### Ollama (Local)

```yaml
ollama:
  max_tokens: 4096
  temperature: 0.7
  num_ctx: 8192
  num_gpu_layers: 35
  timeout: 120
  # Ollama runs locally — no network latency but limited by hardware
  # Use for: offline operation, data-sensitive tasks, cost savings
  preferred_for:
    - offline_operation
    - sensitive_data_processing
    - development_testing
```

### Provider Fallback Chain

```yaml
fallback_chains:
  default:
    - provider: groq
      timeout: 15
      retry: 1
    - provider: openai
      timeout: 30
      retry: 2
    - provider: ollama
      timeout: 60
      retry: 1

  critical:
    - provider: openai
      timeout: 30
      retry: 3
    - provider: groq
      timeout: 20
      retry: 2
    - provider: ollama
      timeout: 120
      retry: 2
```

---

## Database Optimization

### Connection Pooling

```python
# SQLAlchemy connection pool configuration
DATABASE_CONFIG = {
    "pool_size": 20,              # Base pool size
    "max_overflow": 10,           # Additional connections under load
    "pool_timeout": 30,           # Seconds to wait for a connection
    "pool_recycle": 3600,         # Recycle connections after 1 hour
    "pool_pre_ping": True,        # Verify connections before use
    "echo": False,                # Disable SQL logging in production
}
```

### Query Optimization

```python
# BAD: N+1 query problem
tasks = session.query(Task).all()
for task in tasks:
    print(task.phase.name)  # Triggers a query for each task

# GOOD: Eager loading
tasks = session.query(Task).options(
    joinedload(Task.phase),
    joinedload(Task.provider)
).all()

# GOOD: Select only needed columns
results = session.query(
    Task.id, Task.status, Task.created_at
).filter(
    Task.phase_id == phase_id
).order_by(
    Task.created_at.desc()
).limit(100).all()
```

### Indexing Strategy

```sql
-- Core indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_tasks_phase_status
    ON tasks (phase_id, status);

CREATE INDEX CONCURRENTLY idx_tasks_created_at
    ON tasks (created_at DESC);

CREATE INDEX CONCURRENTLY idx_tasks_provider
    ON tasks (provider_id, status);

CREATE INDEX CONCURRENTLY idx_audit_logs_timestamp
    ON audit_logs (timestamp DESC);

CREATE INDEX CONCURRENTLY idx_audit_logs_entity
    ON audit_logs (entity_type, entity_id);

-- Partial indexes for common filters
CREATE INDEX CONCURRENTLY idx_tasks_active
    ON tasks (phase_id, priority)
    WHERE status IN ('pending', 'running');

-- GIN index for JSONB columns
CREATE INDEX CONCURRENTLY idx_tasks_metadata
    ON tasks USING GIN (metadata);
```

### Partitioning

```sql
-- Partition audit logs by month for efficient querying
CREATE TABLE audit_logs (
    id          BIGSERIAL,
    timestamp   TIMESTAMPTZ NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id   UUID NOT NULL,
    action      TEXT NOT NULL,
    details     JSONB
) PARTITION BY RANGE (timestamp);

CREATE TABLE audit_logs_2024_05
    PARTITION OF audit_logs
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE audit_logs_2024_06
    PARTITION OF audit_logs
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
```

---

## Caching Strategies

### Multi-Layer Cache Architecture

```
┌──────────────────────────────────────────┐
│            L1: In-Memory Cache            │
│  (LRU, per-process, < 1ms access)        │
│  Size: 256 MB                            │
│  TTL: 60 seconds                         │
├──────────────────────────────────────────┤
│            L2: Redis Cache                │
│  (Shared, < 5ms access)                  │
│  Size: 2 GB                              │
│  TTL: 3600 seconds                       │
├──────────────────────────────────────────┤
│            L3: Database Cache             │
│  (Materialized views, < 50ms access)     │
│  Refresh: Every 5 minutes                │
└──────────────────────────────────────────┘
```

### Cache Configuration

```yaml
cache:
  l1:
    backend: "lru"
    max_size_mb: 256
    default_ttl: 60
    eviction_policy: "lru"

  l2:
    backend: "redis"
    url: "redis://localhost:6379/0"
    max_memory_mb: 2048
    default_ttl: 3600
    eviction_policy: "allkeys-lru"
    key_prefix: "vexis:"
    compression: true

  l3:
    backend: "materialized_view"
    refresh_interval: 300
    views:
      - task_summary
      - phase_metrics
      - provider_stats
```

### Cache Invalidation

```python
class CacheManager:
    """Multi-layer cache with intelligent invalidation."""

    def __init__(self):
        self.l1 = LRUCache(maxsize=256 * 1024 * 1024)
        self.l2 = RedisCache(url="redis://localhost:6379/0")

    async def get(self, key: str) -> Any:
        # L1 check
        value = self.l1.get(key)
        if value is not None:
            return value

        # L2 check
        value = await self.l2.get(key)
        if value is not None:
            self.l1.set(key, value)
            return value

        return None

    async def invalidate(self, key: str, cascade: bool = True):
        """Invalidate a key across all cache layers."""
        self.l1.delete(key)
        await self.l2.delete(key)

        if cascade:
            # Invalidate related keys
            pattern = f"{key}:*"
            related = await self.l2.keys(pattern)
            for rkey in related:
                self.l1.delete(rkey)
                await self.l2.delete(rkey)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern."""
        self.l1.clear()  # L1 is per-process, safe to clear
        keys = await self.l2.keys(pattern)
        if keys:
            await self.l2.delete(*keys)
```

### Cache Warming

```python
class CacheWarmer:
    """Proactively warm cache with frequently accessed data."""

    async def warm_cache(self):
        """Warm cache with hot data."""
        # Warm phase configurations
        phases = await self.db.query(Phase).all()
        for phase in phases:
            await self.cache.set(
                f"phase:{phase.id}:config",
                phase.config,
                ttl=3600
            )

        # Warm provider health status
        providers = await self.db.query(Provider).all()
        for provider in providers:
            health = await self.check_provider_health(provider)
            await self.cache.set(
                f"provider:{provider.name}:health",
                health,
                ttl=60
            )

        # Warm recent task summaries
        summaries = await self.db.query(TaskSummary).filter(
            TaskSummary.created_at > datetime.utcnow() - timedelta(hours=24)
        ).all()
        for summary in summaries:
            await self.cache.set(
                f"task_summary:{summary.id}",
                summary,
                ttl=1800
            )
```

---

## Memory Management

### Python Memory Optimization

```python
# Use __slots__ for high-volume objects
class TaskResult:
    __slots__ = ['task_id', 'status', 'output', 'duration_ms', 'tokens_used']

    def __init__(self, task_id, status, output, duration_ms, tokens_used):
        self.task_id = task_id
        self.status = status
        self.output = output
        self.duration_ms = duration_ms
        self.tokens_used = tokens_used


# Use generators for large datasets
def process_tasks_streaming(batch_size: int = 100):
    """Process tasks in streaming fashion to limit memory usage."""
    offset = 0
    while True:
        batch = session.query(Task).offset(offset).limit(batch_size).all()
        if not batch:
            break
        for task in batch:
            yield process_task(task)
        offset += batch_size
        # Explicitly free the batch
        del batch


# Use weak references for caches that shouldn't prevent GC
import weakref

class ProviderRegistry:
    def __init__(self):
        self._providers: weakref.WeakValueDictionary[str, Provider] = (
            weakref.WeakValueDictionary()
        )
```

### Memory Monitoring

```python
import tracemalloc
import psutil

class MemoryMonitor:
    """Monitor and alert on memory usage."""

    def __init__(self, threshold_percent: float = 85.0):
        self.threshold = threshold_percent
        tracemalloc.start()

    def check_memory(self) -> MemoryStatus:
        """Check current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()

        # Get top memory consumers
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")[:10]

        return MemoryStatus(
            rss_mb=memory_info.rss / (1024 * 1024),
            vms_mb=memory_info.vms / (1024 * 1024),
            percent=memory_percent,
            is_critical=memory_percent > self.threshold,
            top_consumers=[
                (str(stat.traceback), stat.size / 1024)
                for stat in top_stats
            ],
        )
```

---

## Concurrency and Parallelism

### Async I/O Configuration

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Global thread pool for CPU-bound operations
thread_pool = ThreadPoolExecutor(
    max_workers=8,
    thread_name_prefix="vexis-worker"
)

# Async semaphore to limit concurrent AI calls
ai_semaphore = asyncio.Semaphore(10)

async def execute_with_concurrency_limit(task: Task) -> TaskResult:
    """Execute a task with controlled concurrency."""
    async with ai_semaphore:
        result = await ai_provider.acomplete(task.prompt)
        return result

async def run_phase_parallel(phase: Phase, tasks: list[Task]) -> list[TaskResult]:
    """Run phase tasks with controlled parallelism."""
    # Create tasks with semaphore control
    async def bounded_execute(task):
        async with asyncio.Semaphore(phase.max_concurrency):
            return await execute_task(task)

    results = await asyncio.gather(
        *[bounded_execute(t) for t in tasks],
        return_exceptions=True
    )
    return results
```

### Worker Pool Configuration

```yaml
workers:
  # CPU-bound workers (code analysis, parsing)
  cpu_workers:
    count: 8
    queue_size: 100
    max_task_duration: 300

  # I/O-bound workers (API calls, file operations)
  io_workers:
    count: 16
    queue_size: 200
    max_task_duration: 60

  # AI provider workers
  ai_workers:
    count: 10
    queue_size: 50
    max_task_duration: 120
    rate_limit_per_minute: 60
```

---

## Network Optimization

### HTTP Client Configuration

```python
import httpx

# Optimized HTTP client for AI provider calls
http_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20,
        keepalive_expiry=30,
    ),
    timeout=httpx.Timeout(
        connect=5.0,
        read=60.0,
        write=10.0,
        pool=5.0,
    ),
    http2=True,  # Enable HTTP/2 for multiplexing
)
```

### Connection Keep-Alive

```yaml
network:
  keep_alive:
    enabled: true
    idle_timeout: 30
    max_requests_per_connection: 1000

  compression:
    enabled: true
    algorithm: "gzip"
    min_size_bytes: 1024

  dns:
    cache_ttl: 300
    resolver: "async"
```

---

## AI Model Optimization

### Model Selection by Task

| Task Type | Recommended Model | Reason |
|-----------|------------------|--------|
| Quick classification | gpt-4o-mini | Fast, cheap, good enough |
| Code generation | gpt-4o | Best code quality |
| Architecture design | gpt-4o | Best reasoning |
| Simple extraction | llama3-8b (Ollama) | Fast, local, no cost |
| Complex analysis | gpt-4o | Best comprehension |
| Batch processing | mixtral-8x7b (Groq) | Fast, good quality |

### Token Optimization

```python
class TokenOptimizer:
    """Optimize token usage for AI provider calls."""

    def optimize_prompt(self, prompt: str, max_tokens: int = 4096) -> str:
        """Reduce prompt token count while preserving meaning."""
        # Remove redundant whitespace
        prompt = " ".join(prompt.split())

        # Remove unnecessary examples
        prompt = self._remove_redundant_examples(prompt)

        # Compress verbose sections
        prompt = self._compress_sections(prompt)

        # Truncate if still too long
        token_count = self.count_tokens(prompt)
        if token_count > max_tokens:
            prompt = self._smart_truncate(prompt, max_tokens)

        return prompt

    def batch_prompts(
        self, prompts: list[str], max_batch_tokens: int = 8192
    ) -> list[list[str]]:
        """Group prompts into batches that fit within token limits."""
        batches = []
        current_batch = []
        current_tokens = 0

        for prompt in prompts:
            tokens = self.count_tokens(prompt)
            if current_tokens + tokens > max_batch_tokens and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            current_batch.append(prompt)
            current_tokens += tokens

        if current_batch:
            batches.append(current_batch)

        return batches
```

### Streaming Responses

```python
async def stream_phase_output(task: Task) -> AsyncIterator[str]:
    """Stream AI output for real-time progress updates."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            provider.url,
            json={
                "model": task.model,
                "messages": task.messages,
                "stream": True,
                "max_tokens": task.max_tokens,
            },
            headers=provider.auth_headers(),
        ) as response:
            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    data = json.loads(chunk[6:])
                    if data.get("choices"):
                        delta = data["choices"][0].get("delta", {})
                        if content := delta.get("content"):
                            yield content
```

---

## Monitoring and Profiling

### Performance Metrics Collection

```python
from prometheus_client import Histogram, Counter, Gauge

# Define metrics
TASK_DURATION = Histogram(
    "vexis_task_duration_seconds",
    "Task execution duration",
    ["phase", "provider", "status"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

PROVIDER_LATENCY = Histogram(
    "vexis_provider_latency_seconds",
    "AI provider response latency",
    ["provider", "model"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

CACHE_HITS = Counter(
    "vexis_cache_hits_total",
    "Total cache hits",
    ["cache_layer"],
)

CACHE_MISSES = Counter(
    "vexis_cache_misses_total",
    "Total cache misses",
    ["cache_layer"],
)

ACTIVE_TASKS = Gauge(
    "vexis_active_tasks",
    "Number of currently active tasks",
    ["phase"],
)
```

### Profiling Tools

```bash
# CPU profiling
python -m cProfile -o profile.stats -m vexis run --phase 3
python -m pstats profile.stats

# Memory profiling
python -m memory_profiler vexis/run.py

# Line-by-line profiling
kernprof -l -v vexis/run.py

# Async profiling
python -m vexis profile --async --duration 60
```

### Performance Dashboard Queries

```prometheus
# Average task duration by phase
avg(vexis_task_duration_seconds_sum) by (phase)
/ avg(vexis_task_duration_seconds_count) by (phase)

# Provider p99 latency
histogram_quantile(0.99, rate(vexis_provider_latency_seconds_bucket[5m]))

# Cache hit rate
rate(vexis_cache_hits_total[5m])
/ (rate(vexis_cache_hits_total[5m]) + rate(vexis_cache_misses_total[5m]))

# Error rate by provider
rate(vexis_task_duration_seconds_count{status="error"}[5m])
/ rate(vexis_task_duration_seconds_count[5m])
```

---

## Performance Checklist

### Pre-Deployment

- [ ] Run full benchmark suite and establish baselines
- [ ] Configure connection pooling for all databases
- [ ] Set up multi-layer caching (L1, L2, L3)
- [ ] Configure provider fallback chains
- [ ] Enable HTTP/2 for all API clients
- [ ] Set up Prometheus metrics collection
- [ ] Configure memory monitoring and alerts
- [ ] Review and optimize all database indexes
- [ ] Configure async I/O with appropriate concurrency limits
- [ ] Set up cache warming for hot data

### Ongoing Monitoring

- [ ] Review p50/p95/p99 latency daily
- [ ] Monitor cache hit rates weekly
- [ ] Track provider error rates and latency trends
- [ ] Review database slow query log weekly
- [ ] Monitor memory usage and garbage collection
- [ ] Review connection pool utilization
- [ ] Track token usage and cost per phase
- [ ] Review and adjust concurrency limits monthly

### Optimization Cycle

1. **Profile** — Identify the bottleneck
2. **Measure** — Establish baseline metrics
3. **Optimize** — Apply targeted improvements
4. **Verify** — Confirm improvement with benchmarks
5. **Monitor** — Watch for regressions
6. **Repeat** — Move to the next bottleneck
