"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Ensure both repo root and src directory are importable during test collection.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_model_response():
    """Provide a mock model response"""
    return Mock(
        success=True,
        content="Test response",
        model="test-model",
        provider="test-provider",
        tokens_used=100,
        cost=0.001,
        latency=1.0,
        error=None
    )


@pytest.fixture
def mock_api_error():
    """Provide a mock API error"""
    return Mock(
        success=False,
        content="",
        model="test-model",
        provider="test-provider",
        tokens_used=0,
        cost=0.0,
        latency=0.0,
        error="API Error"
    )


@pytest.fixture
def sample_user_prompt():
    """Provide a sample user prompt"""
    return "List all files in the current directory"


@pytest.fixture
def sample_terminal_log():
    """Provide a sample terminal log"""
    return """
$ ls -la
total 128
drwxr-xr-x  10 user group   320 Apr 18 10:00 .
drwxr-xr-x   5 user group   160 Apr 18 09:00 ..
-rw-r--r--   1 user group  2048 Apr 18 10:00 file.txt

$ echo "Hello World"
Hello World
"""


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset singleton instances before each test to ensure isolation
    """
    # Import and reset singletons
    from src.ai_agent.utils import exceptions, cost_manager, prompt_cache, provider_fallback
    from src.ai_agent.core_processing.repo_index import IndexManager
    
    # Reset global instances
    exceptions._global_robustness_manager = None
    cost_manager._global_cost_manager = None
    prompt_cache._global_cache = None
    provider_fallback._global_fallback_manager = None
    IndexManager.reset_index()
    
    yield
    
    # Reset again after test
    exceptions._global_robustness_manager = None
    cost_manager._global_cost_manager = None
    prompt_cache._global_cache = None
    provider_fallback._global_fallback_manager = None
    IndexManager.reset_index()
