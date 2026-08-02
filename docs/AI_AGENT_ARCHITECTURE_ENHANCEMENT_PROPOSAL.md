# AI Agent Architecture Enhancement Proposal

## Goal
Define a next-generation architecture that surpasses contemporary coding/automation agents by improving:
1. Proactive planning
2. Deep codebase indexing
3. Autonomous tool-use optimization

---

## 1) Proactive Planning Upgrades

### A. Predictive Subgoal Graph (PSG)
Replace linear step lists with a dependency graph containing:
- required artifacts
- risk level
- estimated runtime
- rollback strategy
- validation command per node

Benefits:
- better parallelization decisions
- explicit blocker handling
- deterministic recovery after partial failure

### B. Plan Critic + Plan Optimizer Duo
Add two internal evaluators before execution:
- **Critic**: checks ambiguity, hidden assumptions, missing preconditions
- **Optimizer**: rewrites plan for fewer commands, lower risk, faster convergence

### C. Confidence-Gated Execution
Each node carries confidence and blast-radius scores. Low confidence auto-triggers:
- extra read/inspect commands
- dry-run mode
- smaller reversible edits

---

## 2) Deeper Codebase Indexing

### A. Multi-Layer Repository Index
Maintain continuously refreshed indexes:
- symbol graph (definitions/references)
- build/test dependency graph
- runtime log embeddings
- doc-to-code alignment map

### B. Delta-Aware Index Refresh
After each write, update only impacted slices instead of full re-indexing.

### C. Trace-Backed Retrieval
Every generated command/edit includes machine-checkable provenance:
- source file+line evidence
- reason chain linked to plan node
- confidence score

Outcome: stronger correctness than shallow semantic search approaches.

---

## 3) Autonomous Tool-Use Optimization

### A. Tool Policy Engine
Introduce a policy layer deciding *which* tool to use and *when*:
- shell
- structured file edit (`str_replace`)
- static analysis
- tests
- external APIs

The policy scores tools by safety, determinism, cost, and expected information gain.

### B. Self-Tuning Command Macros
Learn reusable command sequences per repository type (Python, Node, monorepo, etc.), with guardrails to avoid unsafe reuse.

### C. Verification-First Execution
Before expensive actions, run lightweight probes:
- existence checks
- schema checks
- targeted unit tests
- lint-only fast path

This reduces wasted tokens and failed long command runs.

---

## 4) Competitive Differentiators

To outperform leading agent UX and outcomes:
- **Higher completion reliability** via graph planning + critic loop
- **Faster median task time** via delta indexing + tool policy routing
- **Lower hallucination edits** via provenance-enforced retrieval
- **Safer autonomy** via confidence/risk gates and reversible micro-steps

---

## 5) Proposed Incremental Rollout

1. Add plan graph data model beside existing `step_list`.
2. Add critic/optimizer as optional pre-phase.
3. Implement index service with symbol + test graph first.
4. Add tool policy scoring for Phase 2 action generation.
5. Add provenance metadata to all writes/commands.
6. Promote to default mode after A/B success metrics.

## Success Metrics
- Task success rate
- Mean commands per successful task
- Time-to-first-correct-result
- Regression escape rate
- Token and API cost per resolved issue
