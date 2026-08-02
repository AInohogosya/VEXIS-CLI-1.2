# Migration Guide

## Table of Contents

- [Overview](#overview)
- [Migrating from Single-Provider to Multi-Provider](#migrating-from-single-provider-to-multi-provider)
- [Migrating from 3-Phase to 6-Phase Architecture](#migrating-from-3-phase-to-6-phase-architecture)
- [Migrating from Cloud-Only to Hybrid (Cloud + Ollama)](#migrating-from-cloud-only-to-hybrid-cloud--ollama)
- [Database Migrations](#database-migrations)
- [Configuration Migration](#configuration-migration)
- [API Version Migration](#api-version-migration)
- [Rollback Procedures](#rollback-procedures)
- [Migration Checklist](#migration-checklist)

---

## Overview

This guide provides step-by-step instructions for migrating between different versions and configurations of the VEXIS-CLI system. It covers architecture migrations, provider changes, database schema updates, and configuration transitions.

### Migration Types

| Migration | Complexity | Downtime | Risk |
|-----------|-----------|----------|------|
| Single → Multi Provider | Medium | None | Low |
| 3-Phase → 6-Phase | High | Required | Medium |
| Cloud → Hybrid | Medium | None | Low |
| Database Schema | Low | Minimal | Medium |
| Configuration | Low | None | Low |
| API Version | Medium | None | Medium |

---

## Migrating from Single-Provider to Multi-Provider

### Step 1: Update Configuration

```yaml
# Before (single provider)
provider:
  name: "openai"
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4o"

# After (multi-provider)
providers:
  - name: "primary"
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o"
    enabled: true

  - name: "fallback"
    type: "groq"
    api_key: "${GROQ_API_KEY}"
    model: "llama3-70b-8192"
    enabled: true

fallback_chains:
  default:
    - provider: "primary"
      timeout: 30
      max_retries: 2
    - provider: "fallback"
      timeout: 15
      max_retries: 1
```

### Step 2: Update Code

```python
# Before
from vexis.providers import OpenAIProvider

provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
result = await provider.complete(messages)

# After
from vexis.providers import ProviderManager

manager = ProviderManager.from_config("providers.yaml")
result = await manager.complete(messages, task=task)
```

### Step 3: Add Provider Health Checks

```python
# Add health check endpoint
@app.get("/health/providers")
async def provider_health():
    return manager.health_monitor.get_summary()
```

### Step 4: Test Fallback

```bash
# Test with primary provider disabled
vexis run --phase 1 --disable-provider primary

# Verify fallback is used
vexis logs --filter "fallback"
```

---

## Migrating from 3-Phase to 6-Phase Architecture

### Mapping

```
Old 3-Phase          →    New 6-Phase
─────────────────────────────────────────
Phase 1: Planning    →    Phase 1: Strategic Assessment
                         →    Phase 2: Architecture Design
Phase 2: Development →    Phase 3: Pilot Implementation
                         →    Phase 4: Integration & Scaling
Phase 3: Deployment  →    Phase 5: Optimization & Governance
                         →    Phase 6: Enterprise Transformation
```

### Step 1: Database Schema Update

```sql
-- Add new phase entries
INSERT INTO phases (id, name, description, position) VALUES
  (1, 'Strategic Assessment', 'Analyze requirements, evaluate feasibility, assess risks', 1),
  (2, 'Architecture Design', 'Design components, interfaces, data models', 2),
  (3, 'Pilot Implementation', 'Implement proof of concept with tests', 3),
  (4, 'Integration & Scaling', 'Integrate with existing systems, scale infrastructure', 4),
  (5, 'Optimization & Governance', 'Optimize performance and cost, establish governance', 5),
  (6, 'Enterprise Transformation', 'Drive adoption, establish CI, plan evolution', 6);

-- Migrate existing tasks
UPDATE tasks SET phase_id = 1 WHERE phase_id = 1 AND type IN ('analysis', 'assessment');
UPDATE tasks SET phase_id = 2 WHERE phase_id = 1 AND type IN ('design', 'planning');
UPDATE tasks SET phase_id = 3 WHERE phase_id = 2 AND type IN ('implementation', 'coding');
UPDATE tasks SET phase_id = 4 WHERE phase_id = 2 AND type IN ('integration', 'scaling');
UPDATE tasks SET phase_id = 5 WHERE phase_id = 3 AND type IN ('deployment', 'optimization');
UPDATE tasks SET phase_id = 6 WHERE phase_id = 3 AND type IN ('monitoring', 'governance');

-- Add new gate configurations
INSERT INTO gates (phase_id, min_score, required_approvers) VALUES
  (1, 0.70, 1),
  (2, 0.75, 2),
  (3, 0.80, 1),
  (4, 0.80, 2),
  (5, 0.75, 2),
  (6, 0.70, 3);
```

### Step 2: Update Task Definitions

```python
# Before: 3-phase task mapping
PHASE_MAPPING = {
    "planning": 1,
    "development": 2,
    "deployment": 3,
}

# After: 6-phase task mapping
PHASE_MAPPING = {
    "strategic_assessment": 1,
    "requirements_analysis": 1,
    "feasibility_evaluation": 1,
    "risk_assessment": 1,
    "architecture_design": 2,
    "component_design": 2,
    "interface_design": 2,
    "data_model_design": 2,
    "pilot_implementation": 3,
    "code_generation": 3,
    "test_generation": 3,
    "integration": 4,
    "scaling": 4,
    "monitoring_setup": 4,
    "optimization": 5,
    "governance": 5,
    "cost_optimization": 5,
    "adoption": 6,
    "transformation": 6,
    "evolution_planning": 6,
}
```

### Step 3: Create New Phase Executors

```python
# Create new phase executors for phases 2, 4, 5, 6
# Phase 2: Architecture Design
class Phase2Executor(PhaseExecutor):
    tasks = [
        ComponentDesignTask,
        InterfaceDesignTask,
        DataModelDesignTask,
        DeploymentDesignTask,
    ]
    gate = ArchitectureReviewGate

# Phase 4: Integration & Scaling
class Phase4Executor(PhaseExecutor):
    tasks = [
        IntegrationPlanningTask,
        InfrastructureConfigurationTask,
        MonitoringSetupTask,
    ]
    gate = IntegrationReviewGate

# Phase 5: Optimization & Governance
class Phase5Executor(PhaseExecutor):
    tasks = [
        PerformanceOptimizationTask,
        CostOptimizationTask,
        GovernanceEstablishmentTask,
    ]
    gate = OptimizationReviewGate

# Phase 6: Enterprise Transformation
class Phase6Executor(PhaseExecutor):
    tasks = [
        AdoptionPlanningTask,
        ContinuousImprovementTask,
        EvolutionPlanningTask,
    ]
    gate = TransformationReviewGate
```

### Step 4: Update Orchestrator

```python
# Before
class Orchestrator:
    phases = [Phase1Executor, Phase2Executor, Phase3Executor]

# After
class Orchestrator:
    phases = [
        Phase1Executor,  # Strategic Assessment
        Phase2Executor,  # Architecture Design
        Phase3Executor,  # Pilot Implementation
        Phase4Executor,  # Integration & Scaling
        Phase5Executor,  # Optimization & Governance
        Phase6Executor,  # Enterprise Transformation
    ]
```

---

## Migrating from Cloud-Only to Hybrid (Cloud + Ollama)

### Step 1: Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Pull required models
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

### Step 2: Update Configuration

```yaml
# Add Ollama to providers
providers:
  - name: "openai"
    type: "openai"
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o"
    enabled: true

  - name: "ollama"
    type: "ollama"
    base_url: "http://localhost:11434/v1"
    model: "llama3"
    enabled: true

# Configure fallback to use Ollama for sensitive tasks
fallback_chains:
  default:
    - provider: "openai"
      timeout: 30
      max_retries: 2
    - provider: "ollama"
      timeout: 120
      max_retries: 1

  sensitive_data:
    - provider: "ollama"
      timeout: 120
      max_retries: 2
```

### Step 3: Classify Data Sensitivity

```python
class DataClassifier:
    """Classify data to determine which provider to use."""

    SENSITIVE_PATTERNS = [
        r'\b\d{3}-\d{2}-\d{4}\b',          # SSN
        r'\b\d{16}\b',                       # Credit card
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'password\s*[:=]\s*\S+',           # Passwords
        r'api[_-]?key\s*[:=]\s*\S+',        # API keys
    ]

    def classify(self, text: str) -> DataClassification:
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                return DataClassification.SENSITIVE
        return DataClassification.PUBLIC

    def select_provider(self, text: str) -> str:
        classification = self.classify(text)
        if classification == DataClassification.SENSITIVE:
            return "ollama"  # Keep sensitive data local
        return "openai"  # Use cloud for non-sensitive data
```

---

## Database Migrations

### Using Alembic

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create a new migration
alembic revision --autogenerate -m "Add 6-phase support"

# Review the generated migration
cat alembic/versions/xxxx_add_6_phase_support.py

# Apply the migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Migration Script Example

```python
"""Add 6-phase support

Revision ID: abc123
Revises: xyz789
Create Date: 2024-05-24 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'

def upgrade():
    # Add new columns
    op.add_column('tasks', sa.Column('phase_id', sa.Integer(), nullable=True))
    op.add_column('tasks', sa.Column('gate_status', sa.String(20), nullable=True))
    op.add_column('tasks', sa.Column('retry_count', sa.Integer(), default=0))

    # Create new tables
    op.create_table(
        'phases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), default=True),
    )

    op.create_table(
        'gates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('phase_id', sa.Integer(), sa.ForeignKey('phases.id')),
        sa.Column('min_score', sa.Float(), default=0.7),
        sa.Column('required_approvers', sa.Integer(), default=1),
    )

    # Create indexes
    op.create_index('idx_tasks_phase', 'tasks', ['phase_id'])
    op.create_index('idx_tasks_gate', 'tasks', ['gate_status'])

    # Migrate data
    op.execute("""
        UPDATE tasks SET phase_id = CASE
            WHEN type IN ('analysis', 'assessment') THEN 1
            WHEN type IN ('design', 'planning') THEN 2
            WHEN type IN ('implementation', 'coding') THEN 3
            WHEN type IN ('integration', 'scaling') THEN 4
            WHEN type IN ('deployment', 'optimization') THEN 5
            WHEN type IN ('monitoring', 'governance') THEN 6
            ELSE 1
        END
    """)

    # Make phase_id non-nullable after migration
    op.alter_column('tasks', 'phase_id', nullable=False)

def downgrade():
    # Remove new columns
    op.drop_column('tasks', 'phase_id')
    op.drop_column('tasks', 'gate_status')
    op.drop_column('tasks', 'retry_count')

    # Drop new tables
    op.drop_table('gates')
    op.drop_table('phases')

    # Drop indexes
    op.drop_index('idx_tasks_phase')
    op.drop_index('idx_tasks_gate')
```

---

## Configuration Migration

### Configuration Versioning

```yaml
# config_version: 2.0
# migration_from: 1.0

providers:
  # New in 2.0: multi-provider support
  - name: "primary"
    type: "openai"
    api_key: "${OPENAI_API_KEY}"

  - name: "fallback"
    type: "groq"
    api_key: "${GROQ_API_KEY}"

phases:
  # New in 2.0: 6-phase architecture
  count: 6
  mapping:
    strategic_assessment: 1
    architecture_design: 2
    pilot_implementation: 3
    integration_scaling: 4
    optimization_governance: 5
    enterprise_transformation: 6
```

### Automated Config Migration Tool

```python
class ConfigMigrator:
    """Migrate configuration from old format to new format."""

    MIGRATIONS = {
        "1.0": "1.1",
        "1.1": "2.0",
    }

    def migrate(self, config: dict, from_version: str, to_version: str) -> dict:
        """Migrate configuration between versions."""
        current = from_version
        while current != to_version:
            next_version = self.MIGRATIONS.get(current)
            if not next_version:
                raise MigrationError(f"No migration path from {current} to {to_version}")

            migrate_func = getattr(self, f"migrate_{current.replace('.', '_')}_{next_version.replace('.', '_')}")
            config = migrate_func(config)
            current = next_version

        return config

    def migrate_1_0_1_1(self, config: dict) -> dict:
        """Migrate from 1.0 to 1.1."""
        # Add timeout field if missing
        if "timeout" not in config.get("provider", {}):
            config.setdefault("provider", {})["timeout"] = 60
        return config

    def migrate_1_1_2_0(self, config: dict) -> dict:
        """Migrate from 1.1 to 2.0 (multi-provider + 6-phase)."""
        old_provider = config.pop("provider", {})
        config["providers"] = [
            {
                "name": "primary",
                "type": old_provider.get("name", "openai"),
                "api_key": old_provider.get("api_key", "${OPENAI_API_KEY}"),
                "model": old_provider.get("model", "gpt-4o"),
                "enabled": True,
            }
        ]
        config["fallback_chains"] = {
            "default": [
                {"provider": "primary", "timeout": 30, "max_retries": 2}
            ]
        }
        config["phases"] = {"count": 6, "mapping": self._default_phase_mapping()}
        return config
```

---

## API Version Migration

### API Versioning Strategy

```python
from fastapi import APIRouter, Header

router = APIRouter()

@router.get("/v1/tasks")
async def list_tasks_v1():
    """Legacy API version 1."""
    return {"tasks": [], "version": "1.0"}

@router.get("/v2/tasks")
async def list_tasks_v2(
    phase_id: int = None,
    gate_status: str = None,
):
    """API version 2 with 6-phase support."""
    query = select(Task)
    if phase_id:
        query = query.where(Task.phase_id == phase_id)
    if gate_status:
        query = query.where(Task.gate_status == gate_status)
    return {"tasks": await db.fetch_all(query), "version": "2.0"}

# Version negotiation via header
@router.get("/tasks")
async def list_tasks(
    x_api_version: str = Header(default="2.0"),
):
    if x_api_version.startswith("1"):
        return await list_tasks_v1()
    return await list_tasks_v2()
```

### Deprecation Timeline

| Version | Status | Deprecation Date | End of Life |
|---------|--------|-----------------|-------------|
| API v1 | Deprecated | 2024-06-01 | 2024-12-01 |
| API v2 | Current | — | — |
| Config v1 | Deprecated | 2024-06-01 | 2024-09-01 |
| Config v2 | Current | — | — |

---

## Rollback Procedures

### Configuration Rollback

```bash
# Backup current config
cp config.yaml config.yaml.bak

# Rollback to previous version
git checkout HEAD~1 -- config.yaml

# Restart services
vexis restart
```

### Database Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123

# Verify rollback
alembic current
```

### Full System Rollback

```bash
# Tag current state before migration
git tag pre-migration-$(date +%Y%m%d)

# If migration fails, rollback everything
git checkout pre-migration-$(date +%Y%m%d)
alembic downgrade -1
vexis restart

# Verify system health
vexis health-check --full
```

---

## Migration Checklist

### Pre-Migration

- [ ] Backup all configuration files
- [ ] Backup database
- [ ] Tag current code version
- [ ] Review migration documentation
- [ ] Test migration in staging environment
- [ ] Notify team of planned migration
- [ ] Schedule maintenance window (if needed)
- [ ] Prepare rollback plan

### During Migration

- [ ] Apply database migrations
- [ ] Update configuration files
- [ ] Deploy new code version
- [ ] Run health checks
- [ ] Verify provider connectivity
- [ ] Test phase execution
- [ ] Validate gate functionality
- [ ] Check monitoring dashboards

### Post-Migration

- [ ] Run full test suite
- [ ] Verify all phases execute correctly
- [ ] Test fallback chains
- [ ] Validate data integrity
- [ ] Check performance baselines
- [ ] Update documentation
- [ ] Notify team of completion
- [ ] Monitor for 24 hours
