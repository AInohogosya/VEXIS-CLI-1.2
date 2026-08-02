# Glossary

## Table of Contents

- [Architecture Terms](#architecture-terms)
- [Phase Terms](#phase-terms)
- [Provider Terms](#provider-terms)
- [Technical Terms](#technical-terms)
- [Acronyms](#acronyms)

---

## Architecture Terms

### 6-Phase Architecture

The core system architecture of VEXIS-CLI, consisting of six distinct phases that guide a project from strategic assessment through enterprise transformation:

1. **Strategic Assessment** — Requirements analysis, feasibility evaluation, risk assessment
2. **Architecture Design** — Component design, interface design, data model design
3. **Pilot Implementation** — Proof of concept implementation with tests
4. **Integration & Scaling** — System integration and infrastructure scaling
5. **Optimization & Governance** — Performance optimization and governance establishment
6. **Enterprise Transformation** — Organization-wide adoption and continuous improvement

### Artifact

A produced output from a phase execution. Artifacts can include documents, code, configurations, reports, or any other deliverable. Each phase produces specific artifacts that serve as inputs for subsequent phases.

### Gate

A validation checkpoint between phases. A gate defines criteria that must be met before the system can proceed to the next phase. Gates have configurable minimum scores and required approver counts.

### Feedback Loop

A mechanism by which downstream phases can provide input to upstream phases. When a downstream phase discovers issues or requirements that affect earlier phases, the feedback loop triggers re-evaluation of the affected phase.

### Orchestrator

The central coordination component that manages the execution of all six phases. The orchestrator handles phase ordering, state transitions, gate validation, and error recovery.

### Phase Executor

A component responsible for executing all tasks within a specific phase. Each phase has its own executor that manages task scheduling, parallel execution, and result aggregation.

### Task

The smallest unit of work within a phase. Each task has a specific type, input requirements, and expected output. Tasks are executed by the phase executor and their results are aggregated into phase outputs.

---

## Phase Terms

### Phase State

The current lifecycle state of a phase. Possible states:

| State | Description |
|-------|-------------|
| `PENDING` | Phase is waiting to be executed |
| `RUNNING` | Phase is currently executing |
| `REVIEW` | Phase output is under gate review |
| `COMPLETED` | Phase completed successfully |
| `REJECTED` | Phase output failed gate review |
| `FAILED` | Phase execution encountered an error |
| `RETRYING` | Phase is being retried after failure |

### Gate Score

A numerical value (0.0 to 1.0) representing how well a phase's output meets the gate criteria. The gate score is computed by evaluating multiple quality dimensions of the phase output.

### Gate Review

The process of evaluating a phase's output against predefined criteria. A gate review may require one or more approvers to sign off before the phase can be marked as completed.

### Phase Handoff

The process of transferring outputs from one phase as inputs to the next phase. Phase handoffs include validation to ensure all required artifacts are present and properly formatted.

### Retry Count

The number of times a phase has been retried after a failure or gate rejection. Each phase has a maximum retry count to prevent infinite loops.

---

## Provider Terms

### AI Provider

A service that offers AI model inference capabilities. VEXIS-CLI supports multiple AI providers including OpenAI, Groq, Google, Ollama, and custom providers.

### Provider Chain

An ordered list of providers to try when executing a request. The system attempts each provider in sequence until one succeeds or all fail.

### Fallback Chain

A specific type of provider chain used when the primary provider fails. Fallback chains are configured per task type and can include different models and timeout settings.

### Provider Health

The current operational status of a provider. Health is determined by response latency, error rate, and consecutive failure count. Possible states: `healthy`, `degraded`, `unhealthy`.

### Circuit Breaker

A design pattern that prevents requests from being sent to a failing provider. When the error rate exceeds a threshold, the circuit breaker opens and all requests are redirected to fallback providers.

### Rate Limiting

A mechanism to control the number of requests sent to a provider within a time period. Rate limiting prevents provider quota exhaustion and ensures fair usage.

### Token

The basic unit of text processed by AI models. Tokens can be words, parts of words, or punctuation. Token count affects both cost and processing time.

### Completion

The response from an AI provider containing the generated text, token usage statistics, and metadata about the request.

### Streaming

A mode of response delivery where the AI provider sends the output incrementally as it is generated, rather than waiting for the complete response.

---

## Technical Terms

### Bulkhead

An isolation pattern that limits the resources (threads, connections, memory) allocated to a specific operation. Prevents a single failing component from consuming all system resources.

### Cache Layer

A storage layer that keeps frequently accessed data for fast retrieval. VEXIS-CLI uses a three-layer cache: L1 (in-memory LRU), L2 (Redis), and L3 (materialized views).

### Cache Hit

When requested data is found in the cache, avoiding the need to fetch it from the primary source.

### Cache Miss

When requested data is not found in the cache and must be fetched from the primary source.

### Cache Invalidation

The process of removing or updating cached data when the underlying data changes, ensuring cache consistency.

### Connection Pool

A cache of database connections that can be reused, reducing the overhead of establishing new connections for each request.

### Exponential Backoff

A retry strategy where the wait time between retries increases exponentially (e.g., 1s, 2s, 4s, 8s). Reduces load on failing services during recovery.

### Idempotency

The property of an operation where performing it multiple times produces the same result as performing it once. Critical for retry safety.

### Materialized View

A database object that stores the result of a query physically, allowing faster access to complex query results. Refreshed periodically.

### Migration

A database schema change managed through versioned scripts. Migrations allow the database schema to evolve alongside the application code.

### Sandbox

An isolated execution environment for running untrusted code. Sandboxes restrict access to system resources, network, and filesystem.

### Structured Logging

A logging approach where log entries are emitted in a structured format (typically JSON) rather as plain text, enabling automated parsing and analysis.

### Timeout

The maximum duration allowed for an operation before it is cancelled. Timeouts prevent operations from hanging indefinitely.

---

## Acronyms

| Acronym | Full Form |
|---------|-----------|
| **ADR** | Architecture Decision Record |
| **API** | Application Programming Interface |
| **ARM** | Azure Resource Manager |
| **CI/CD** | Continuous Integration / Continuous Deployment |
| **CLI** | Command Line Interface |
| **CPU** | Central Processing Unit |
| **DNS** | Domain Name System |
| **E2E** | End-to-End |
| **GDPR** | General Data Protection Regulation |
| **GIN** | Generalized Inverted Index (PostgreSQL) |
| **GPU** | Graphics Processing Unit |
| **HIPAA** | Health Insurance Portability and Accountability Act |
| **HTTP** | Hypertext Transfer Protocol |
| **HTTP/2** | HTTP version 2 |
| **IAM** | Identity and Access Management |
| **IaC** | Infrastructure as Code |
| **JWT** | JSON Web Token |
| **KPI** | Key Performance Indicator |
| **LRU** | Least Recently Used |
| **MFA** | Multi-Factor Authentication |
| **ORM** | Object-Relational Mapping |
| **PCI DSS** | Payment Card Industry Data Security Standard |
| **RBAC** | Role-Based Access Control |
| **ABAC** | Attribute-Based Access Control |
| **REST** | Representational State Transfer |
| **RPC** | Remote Procedure Call |
| **RSS** | Resident Set Size (memory metric) |
| **SLA** | Service Level Agreement |
| **SOC 2** | Service Organization Control 2 |
| **SQL** | Structured Query Language |
| **SSL** | Secure Sockets Layer |
| **TLS** | Transport Layer Security |
| **TTL** | Time To Live |
| **VMS** | Virtual Memory Size |
| **YAML** | YAML Ain't Markup Language |
