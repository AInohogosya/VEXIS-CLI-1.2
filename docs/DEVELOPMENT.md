# Development Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Coding Standards](#coding-standards)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Database Migrations](#database-migrations)
8. [API Development](#api-development)
9. [Plugin Development](#plugin-development)
10. [Contribution Guidelines](#contribution-guidelines)
11. [Code Review Process](#code-review-process)
12. [Release Process](#release-process)
13. [Development Tools](#development-tools)
14. [Common Issues and Solutions](#common-issues-and-solutions)

## Introduction

This development guide provides comprehensive information for contributing to the 6-Phase Architecture project. Whether you're a new contributor or an experienced developer, this guide will help you navigate the codebase, understand development workflows, and contribute effectively.

### Project Philosophy

- **Modular Design**: Build with modularity and extensibility in mind
- **Test-Driven Development**: Write tests before implementation
- **Clean Code**: Prioritize readability and maintainability
- **Continuous Improvement**: Regular refactoring and optimization
- **Community First**: Foster a welcoming and inclusive community

## Development Environment Setup

### Prerequisites

- **Python**: 3.8 or higher
- **Poetry**: 1.2 or higher (dependency management)
- **Docker**: 20.10 or higher (containerization)
- **PostgreSQL**: 14 or higher (database)
- **Redis**: 6.2 or higher (caching)
- **Git**: 2.30 or higher (version control)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/AInohogosya/VEXIS-CLI-3.git
cd VEXIS-CLI-3
```

#### 2. Set Up Python Environment

```bash
# Install pyenv (optional but recommended)
curl https://pyenv.run | bash

# Install Python 3.10.0
pyenv install 3.10.0

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

#### 3. Install Dependencies

```bash
# Install project dependencies
poetry install

# Install development dependencies
poetry install --with=dev

# Install pre-commit hooks
pre-commit install
```

#### 4. Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env file with your configuration
nano .env

# Example .env configuration
AI_AGENT_PREFERRED_PROVIDER=groq
AI_AGENT_LOCAL_ENDPOINT=http://localhost:11434
AI_AGENT_LOCAL_MODEL=llama-4-scout-17b
AI_AGENT_API_KEY=your-api-key-here
DB_PASSWORD=your-database-password
REDIS_PASSWORD=your-redis-password
```

#### 5. Set Up Database

```bash
# Install PostgreSQL
sudo apt-get install postgresql  # Ubuntu/Debian
brew install postgresql          # macOS

# Start PostgreSQL service
sudo systemctl start postgresql

# Create database user
sudo -u postgres psql -c "CREATE USER vexiscore_dev WITH PASSWORD 'dev_password';"

# Create database
sudo -u postgres psql -c "CREATE DATABASE vexiscore_dev OWNER vexiscore_dev;"

# Initialize database schema
python3 manage.py migrate
```

#### 6. Start Development Server

```bash
# Start development server
python3 run.py --dev

# Or start with hot reload
uvicorn app.main:app --reload --port 8000
```

### Development Tools

#### Essential Tools

- **IDE**: VS Code, PyCharm, or your preferred IDE
- **Database GUI**: DBeaver, pgAdmin, or TablePlus
- **API Client**: Postman, Insomnia, or HTTPie
- **Git Client**: Git CLI, GitKraken, or SourceTree
- **Terminal**: iTerm2, Windows Terminal, or GNOME Terminal

#### VS Code Extensions

- **Python**: Microsoft's Python extension
- **Docker**: Docker extension for VS Code
- **PostgreSQL**: PostgreSQL extension
- **Prettier**: Code formatter
- **ESLint**: JavaScript linter
- **GitLens**: Git integration

## Project Structure

### Core Architecture

```
VEXIS-CLI/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main application entry point
│   ├── api/                 # FastAPI application
│   │   ├── __init__.py
│   │   ├── routes.py        # API routes
│   │   ├── schemas.py       # Pydantic schemas
│   │   └── dependencies.py  # Dependency injection
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration management
│   │   ├── security.py      # Security utilities
│   │   └── logging.py       # Logging configuration
│   ├── phases/              # 6-Phase Architecture implementation
│   │   ├── __init__.py
│   │   ├── phase1.py        # Strategic Assessment
│   │   ├── phase2.py        # Architecture Design
│   │   ├── phase3.py        # Pilot Implementation
│   │   ├── phase4.py        # Integration & Scaling
│   │   ├── phase5.py        # Optimization & Governance
│   │   └── phase6.py        # Enterprise Transformation
│   ├── tasks/               # Task management
│   │   ├── __init__.py
│   │   ├── models.py        # Task models
│   │   ├── executors.py     # Task execution
│   │   └── schedulers.py    # Task scheduling
│   ├── providers/           # AI provider integrations
│   │   ├── __init__.py
│   │   ├── base.py          # Base provider class
│   │   ├── groq.py          # Groq provider
│   │   ├── google.py        # Google provider
│   │   ├── openai.py        # OpenAI provider
│   │   └── ollama.py        # Ollama provider
│   ├── database/            # Database layer
│   │   ├── __init__.py
│   │   ├── models.py        # Database models
│   │   ├── crud.py          # Create, Read, Update, Delete operations
│   │   └── database.py      # Database connection
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py    # Data validators
│   │   ├── helpers.py       # Helper functions
│   │   └── decorators.py    # Function decorators
│   └── middleware/          # Middleware components
│       ├── __init__.py
│       ├── auth.py          # Authentication middleware
│       └── logging.py       # Logging middleware
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── config/
│   ├── __init__.py
│   ├── settings.py          # Settings and configuration
│   └── validation.py        # Configuration validation
├── scripts/
│   ├── database.py          # Database management scripts
│   ├── deploy.py            # Deployment scripts
│   └── utils.py             # Utility scripts
├── plugins/                 # Plugin system
│   ├── __init__.py
│   ├── base.py              # Base plugin class
│   ├── example_plugin.py    # Example plugin
│   └── custom_plugin.py     # Custom plugin template
├── migrations/              # Database migrations
│   ├── __init__.py
│   └── versions/
├── static/                  # Static files
├── templates/               # Template files
├── .env.example             # Environment variable example
├── .gitignore               # Git ignore configuration
├── pyproject.toml           # Poetry configuration
├── README.md                # Project documentation
├── CONTRIBUTING.md          # Contribution guidelines
└── LICENSE                  # Project license
```

### Important Files

- **app/main.py**: Main application entry point
- **app/api/routes.py**: API route definitions
- **app/phases/phase1.py**: Phase 1 implementation
- **app/providers/base.py**: Base provider class
- **app/database/models.py**: Database models
- **config/settings.py**: Configuration settings
- **tests/conftest.py**: Pytest configuration

## Coding Standards

### Python Style Guide

#### PEP 8 Compliance

- Follow PEP 8 style guide for Python code
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 79 characters
- Use blank lines to separate logical sections
- Use descriptive variable and function names

#### Type Hints

```python
from typing import Optional, List, Dict

def process_task(
    task_id: str,
    parameters: Dict[str, Any],
    priority: Optional[int] = None
) -> Dict[str, Any]:
    """Process a task with given parameters."""
    # Implementation
    return result
```

#### Docstrings

```python
def calculate_metrics(data: List[float]) -> Dict[str, float]:
    """
    Calculate statistical metrics for given data.

    Args:
        data (List[float]): List of numerical data points

    Returns:
        Dict[str, float]: Dictionary containing calculated metrics

    Raises:
        ValueError: If data is empty or invalid

    Example:
        >>> calculate_metrics([1.0, 2.0, 3.0])
        {'mean': 2.0, 'median': 2.0, 'std_dev': 0.816}
    """
    if not data:
        raise ValueError("Data cannot be empty")

    # Implementation
    return {
        "mean": sum(data) / len(data),
        "median": sorted(data)[len(data) // 2],
        "std_dev": (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5
    }
```

### FastAPI Best Practices

#### Route Definitions

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> TaskResponse:
    """
    Get task details by task ID.
    
    Args:
        task_id: Unique identifier of the task
        
    Returns:
        TaskResponse: Task details with execution status
        
    Raises:
        HTTPException: If task is not found
    """
    task = await get_task_from_db(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task
```

#### Dependency Injection

```python
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

def get_db() -> Session:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from authentication token."""
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
    return user
```

### Database Models

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Task(Base):
    """Task database model."""
    
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="pending")
    phase = Column(String, nullable=False)
    parameters = Column(JSON)
    created_at = Column(DateTime, server_default=text("now()"))
    updated_at = Column(DateTime, server_default=text("now()"), onupdate=text("now()"))
    completed_at = Column(DateTime)
    execution_count = Column(Integer, default=0)
    
    # Relationships
    executions = relationship("TaskExecution", back_populates="task")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "phase": self.phase,
            "created_at": self.created_at.isoformat(),
            "execution_count": self.execution_count
        }
```

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration
├── unit/
│   ├── __init__.py
│   ├── test_phases.py   # Phase unit tests
│   ├── test_tasks.py    # Task unit tests
│   └── test_providers.py # Provider unit tests
├── integration/
│   ├── __init__.py
│   ├── test_api.py      # API integration tests
│   └── test_database.py # Database integration tests
└── e2e/
    ├── __init__.py
    └── test_workflow.py # End-to-end workflow tests
```

### Writing Tests

#### Unit Tests

```python
import pytest
from app.phases.phase1 import StrategicAssessmentPhase
from app.providers.base import BaseProvider

class MockProvider(BaseProvider):
    """Mock provider for testing."""
    
    def execute(self, command: str) -> Dict[str, Any]:
        return {"success": True, "result": "mock_result"}

def test_phase1_initialization():
    """Test Phase 1 initialization."""
    phase = StrategicAssessmentPhase(
        phase_id="phase1",
        provider=MockProvider(),
        config={"timeout": 3600}
    )
    
    assert phase.phase_id == "phase1"
    assert phase.status == "pending"
    assert phase.progress == 0

def test_phase1_execution():
    """Test Phase 1 execution."""
    phase = StrategicAssessmentPhase(
        phase_id="phase1",
        provider=MockProvider(),
        config={"timeout": 3600}
    )
    
    result = phase.execute_step("intent_analysis")
    assert result["success"] is True
    assert "mock_result" in result["result"]
```

#### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())

def test_get_task_success():
    """Test getting an existing task."""
    response = client.get("/tasks/existing_task_id")
    assert response.status_code == 200
    assert "task" in response.json()
    assert response.json()["task"]["id"] == "existing_task_id"

def test_get_task_not_found():
    """Test getting a non-existent task."""
    response = client.get("/tasks/nonexistent_task_id")
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]
```

#### Test Fixtures

```python
import pytest
from app.database import SessionLocal, engine

@pytest.fixture(scope="session")
def db_engine():
    """Database engine fixture."""
    yield engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Database session fixture."""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    yield connection
    
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_task(db_session):
    """Test task fixture."""
    from app.tasks.models import Task
    
    task = Task(
        id="test_task_123",
        name="Test Task",
        phase="phase1",
        parameters={"test": "value"}
    )
    db_session.add(task)
    db_session.commit()
    
    yield task
    
    db_session.delete(task)
    db_session.commit()
```

### Test Coverage

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html

# Target coverage thresholds
# - Unit tests: 90%+
# - Integration tests: 80%+
# - Overall: 85%+
```

## Debugging

### Debugging Tools

#### Python Debugger (pdb)

```python
import pdb

def complex_function(data):
    pdb.set_trace()  # Breakpoint
    result = data * 2
    return result

# Debug with pdb
python3 -m pdb your_script.py
```

#### VS Code Debugger

1. Set breakpoints in your code
2. Start debugging (F5)
3. Use debug console to inspect variables
4. Step through code with F10 (step over), F11 (step into)

#### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Log messages
logger.debug("Debug message")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

### Common Debugging Techniques

#### Print Debugging

```python
def process_data(data):
    print(f"DEBUG: Input data = {data}")  # Debug print
    result = complex_operation(data)
    print(f"DEBUG: Result = {result}")  # Debug print
    return result
```

#### Logging Debugging

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug(f"Processing data: {data}")
    result = complex_operation(data)
    logger.debug(f"Result: {result}")
    return result
```

#### Interactive Debugging

```bash
# Use IPython for interactive debugging
pip install ipython

import IPython

def process_data(data):
    IPython.embed()  # Start IPython shell
    result = complex_operation(data)
    return result
```

### Debugging Performance Issues

```python
import cProfile
import pstats

def profile_function(func):
    """Profile a function and print statistics."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func()
    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(10)  # Print top 10 functions
    
    return result

# Profile a function
@profile_function
def complex_operation():
    # Complex operation code
    pass
```

## Database Migrations

### Migration Structure

```
migrations/
├── versions/
│   ├── 001_initial_migration.py
│   ├── 002_add_task_table.py
│   ├── 003_add_phase_tables.py
│   └── 004_add_provider_tables.py
└── env.py
```

### Creating Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new column to tasks table"

# Example migration file
def upgrade():
    op.add_column('tasks', sa.Column('priority', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('tasks', 'priority')
```

### Running Migrations

```bash
# Upgrade to latest migration
alembic upgrade head

# Upgrade to specific version
alembic upgrade ae1f4a3b9f0e

# Downgrade to previous version
alembic downgrade -1

# Show migration history
alembic history
```

### Migration Best Practices

1. **Test migrations** in development before production
2. **Backup database** before running migrations
3. **Run migrations** during low-traffic periods
4. **Test rollback procedures**
5. **Document migration changes**

## API Development

### FastAPI Development

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="6-Phase Architecture API")

class TaskCreate(BaseModel):
    """Task creation schema."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    phase: str = Field(..., regex="^phase[1-6]$")
    parameters: dict = {}

class TaskResponse(BaseModel):
    """Task response schema."""
    
    id: str
    name: str
    status: str
    progress: int
    
    class Config:
        from_attributes = True

@app.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate) -> TaskResponse:
    """
    Create a new task.
    
    Args:
        task: Task creation parameters
        
    Returns:
        TaskResponse: Created task details
    """
    # Implementation
    return TaskResponse(id="generated_id", name=task.name, status="pending", progress=0)

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """
    Get task details by ID.
    
    Args:
        task_id: Task identifier
        
    Returns:
        TaskResponse: Task details
        
    Raises:
        HTTPException: If task not found
    """
    task = await get_task_from_database(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

### API Documentation

```python
# Enable Swagger UI
app = FastAPI(
    title="6-Phase Architecture API",
    description="API for 6-Phase Architecture system",
    version="2.1.0",
    docs_url="/docs",
    docs_url_oauth2_redirect="/docs/oauth2-redirect",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "tasks",
            "description": "Task management endpoints"
        },
        {
            "name": "phases",
            "description": "Phase management endpoints"
        }
    ]
)
```

### API Testing

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())

def test_create_task():
    """Test task creation endpoint."""
    response = client.post(
        "/tasks",
        json={
            "name": "Test Task",
            "description": "Test task description",
            "phase": "phase1",
            "parameters": {"key": "value"}
        }
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Task"

def test_get_task():
    """Test task retrieval endpoint."""
    response = client.get("/tasks/test_task_id")
    assert response.status_code == 200
    assert response.json()["id"] == "test_task_id"
```

## Plugin Development

### Plugin System

```python
# plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    """Base plugin class."""
    
    @abstractmethod
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a command."""
        pass
    
    @abstractmethod
    def validate(self, parameters: Dict[str, Any]) -> bool:
        """Validate plugin parameters."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Get plugin version."""
        pass

# plugins/example_plugin.py
from plugins.base import BasePlugin

class ExamplePlugin(BasePlugin):
    """Example plugin implementation."""
    
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "result": f"Executed {command} with {kwargs}"
        }
    
    def validate(self, parameters: Dict[str, Any]) -> bool:
        return "command" in parameters
    
    @property
    def name(self) -> str:
        return "example_plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
```

### Plugin Registration

```python
# app/plugins/__init__.py
from typing import Dict, Type
from plugins.base import BasePlugin
from plugins.example_plugin import ExamplePlugin

# Plugin registry
PLUGINS: Dict[str, Type[BasePlugin]] = {
    "example_plugin": ExamplePlugin
}

def get_plugin(plugin_name: str) -> BasePlugin:
    """Get plugin instance by name."""
    if plugin_name not in PLUGINS:
        raise ValueError(f"Plugin {plugin_name} not found")
    return PLUGINS[plugin_name]()
```

### Custom Plugin Development

```python
# plugins/custom_plugin.py
from plugins.base import BasePlugin

class CustomPlugin(BasePlugin):
    """Custom plugin implementation."""
    
    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        # Custom execution logic
        result = perform_custom_operation(command, **kwargs)
        return {
            "success": True,
            "result": result,
            "plugin": self.name,
            "version": self.version
        }
    
    def validate(self, parameters: Dict[str, Any]) -> bool:
        # Custom validation logic
        required_fields = ["command", "parameters"]
        return all(field in parameters for field in required_fields)
    
    @property
    def name(self) -> str:
        return "custom_plugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def custom_method(self) -> str:
        """Custom method specific to this plugin."""
        return "Custom method executed"
```

## Contribution Guidelines

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Write tests** for your changes
5. **Run tests** to ensure everything works
6. **Submit a pull request**

### Code of Conduct

- Be respectful and inclusive
- Assume good faith
- Provide constructive feedback
- Focus on the code, not the person

### Git Workflow

```bash
# Update your fork
git checkout main
git pull upstream main
git push origin main

# Create a feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Add your-feature with tests"

# Push to your fork
git push origin feature/your-feature

# Create a pull request
```

### Pull Request Guidelines

- **Title**: Clear and descriptive title
- **Description**: Detailed description of changes
- **Tests**: Include tests for all changes
- **Documentation**: Update documentation if needed
- **Changelog**: Add entry to CHANGELOG.md

### Code Review Process

1. **Submit pull request**
2. **Automated checks**: CI/CD runs tests and checks
3. **Code review**: Maintainers review your code
4. **Address feedback**: Respond to review comments
5. **Approval**: Get at least one approval
6. **Merge**: Changes are merged to main branch

## Code Review Process

### Review Checklist

- [ ] **Functionality**: Code works as intended
- [ ] **Tests**: Tests cover all changes
- [ ] **Performance**: No performance regressions
- [ ] **Security**: No security vulnerabilities
- [ ] **Style**: Follows coding standards
- [ ] **Documentation**: Documentation is updated
- [ ] **Error Handling**: Proper error handling
- [ ] **Edge Cases**: Edge cases are handled

### Providing Feedback

- Be constructive and specific
- Focus on the code, not the person
- Provide examples and alternatives
- Ask questions instead of making demands

### Receiving Feedback

- Be open to suggestions
- Ask clarifying questions
- Don't take feedback personally
- Thank reviewers for their time

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):

- **MAJOR version** when you make incompatible API changes
- **MINOR version** when you add functionality in a backward-compatible manner
- **PATCH version** when you make backward-compatible bug fixes

### Release Checklist

- [ ] **Update version number** in `pyproject.toml`, `app/main.py`, etc.
- [ ] **Update changelog** in `CHANGELOG.md`
- [ ] **Run tests** and ensure 100% pass
- [ ] **Build package**: `poetry build`
- [ ] **Tag release**: `git tag -a v2.1.0 -m "Release v2.1.0"`
- [ ] **Push tags**: `git push origin --tags`
- [ ] **Publish to PyPI**: `poetry publish`
- [ ] **Update documentation**
- [ ] **Announce release** on community channels

### Hotfix Process

For critical bugs requiring immediate fix:

1. **Create hotfix branch**: `git checkout -b hotfix/critical-bug`
2. **Fix the bug** and add tests
3. **Run tests** to ensure fix works
4. **Merge hotfix** to main and current release branch
5. **Release new patch version**

## Development Tools

### Essential Tools

```bash
# Install development tools
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Install pre-push hooks
pre-push install
```

### Code Quality Tools

```bash
# Run black for code formatting
black app/ tests/

# Run isort for import sorting
isort app/ tests/

# Run flake8 for linting
flake8 app/ tests/

# Run mypy for type checking
mypy app/ tests/

# Run bandit for security linting
bandit -r app/

# Run safety for dependency checking
safety check
```

### Testing Tools

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_phases.py

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest --tb=short --exitfirst
```

## Common Issues and Solutions

### Database Issues

**Issue**: `Database connection error`

**Solution**:
1. Verify PostgreSQL service is running
2. Check database credentials
3. Verify network connectivity

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
python3 manage.py check_db_connection

# Reset database migrations
alembic downgrade -1
alembic upgrade head
```

### Dependency Issues

**Issue**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
1. Reinstall dependencies
2. Check virtual environment
3. Update requirements

```bash
# Reinstall dependencies
poetry install --no-dev

# Check virtual environment
which python

# Update requirements
poetry update
```

### Testing Issues

**Issue**: `Tests failing due to database issues`

**Solution**:
1. Reset test database
2. Run tests in isolation
3. Check test fixtures

```bash
# Reset test database
python3 manage.py reset_test_db

# Run specific test in isolation
pytest tests/unit/test_phases.py::test_phase1_initialization -xvs

# Debug failing test
pytest tests/unit/test_phases.py -k test_phase1_execution -xvs
```

### Performance Issues

**Issue**: `Slow application performance`

**Solution**:
1. Profile code to identify bottlenecks
2. Optimize database queries
3. Implement caching

```bash
# Profile code
python3 -m cProfile -o profile.out app/main.py
python3 -m pstats profile.out

# Optimize database queries
EXPLAIN ANALYZE SELECT * FROM tasks WHERE status = 'pending';

# Implement caching
from app.utils.cache import cache_result

@cache_result(ttl=3600)
def get_expensive_data():
    # Expensive operation
    pass
```

---

**Development Version**: 2.1.0  
**Last Updated**: 2026-05-24  
**Maintainer**: VEXIS-CLI-3 Development Team  
**Contact**: development@vexis-project.com