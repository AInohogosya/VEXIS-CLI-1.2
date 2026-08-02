"""
Unit tests for enhanced exception handling
"""

import pytest
from src.ai_agent.utils.exceptions import (
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    APIError,
    ValidationError,
    ExecutionError,
    TimeoutError,
    ResourceExhaustedError,
    CommandFailureClassifier,
    CommandFailureCategory,
    CommandFailureClassification,
)


class TestErrorCategory:
    """Test error category definitions"""
    
    def test_category_values(self):
        """Test that all categories have correct string values"""
        assert ErrorCategory.TRANSIENT.value == "transient"
        assert ErrorCategory.PERMANENT.value == "permanent"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.RATE_LIMIT.value == "rate_limit"


class TestAPIError:
    """Test APIError with automatic categorization"""
    
    def test_auth_error_categorization(self):
        """Test 401/403 errors are categorized as authentication"""
        error = APIError("Unauthorized", status_code=401)
        assert error.context.category == ErrorCategory.AUTHENTICATION
        assert error.context.retryable == False
    
    def test_rate_limit_categorization(self):
        """Test 429 errors are categorized as rate limit"""
        error = APIError("Too Many Requests", status_code=429)
        assert error.context.category == ErrorCategory.RATE_LIMIT
        assert error.context.retryable == True
        assert error.context.backoff_seconds == 60.0
    
    def test_server_error_categorization(self):
        """Test 5xx errors are categorized as external and retryable"""
        error = APIError("Server Error", status_code=500)
        assert error.context.category == ErrorCategory.EXTERNAL
        assert error.context.retryable == True
    
    def test_validation_error_categorization(self):
        """Test 4xx errors (except 429) are validation errors"""
        error = APIError("Bad Request", status_code=400)
        assert error.context.category == ErrorCategory.VALIDATION
        assert error.context.retryable == False


class TestErrorHandler:
    """Test centralized error handling"""
    
    def test_should_retry_for_retryable_error(self):
        """Test that retryable errors are retried within limit"""
        error = APIError("Server Error", status_code=500)
        assert ErrorHandler.should_retry(error, attempt=0) == True
        assert ErrorHandler.should_retry(error, attempt=1) == True
        assert ErrorHandler.should_retry(error, attempt=2) == True
        assert ErrorHandler.should_retry(error, attempt=3) == False  # max_retries=3
    
    def test_should_not_retry_for_non_retryable_error(self):
        """Test that non-retryable errors are never retried"""
        error = ValidationError("Invalid input")
        assert ErrorHandler.should_retry(error, attempt=0) == False
    
    def test_retry_delay_with_exponential_backoff(self):
        """Test exponential backoff calculation"""
        error = APIError("Server Error", status_code=500)
        
        # Base backoff is 2.0 seconds for 5xx errors
        assert ErrorHandler.get_retry_delay(error, attempt=0) == 2.0
        assert ErrorHandler.get_retry_delay(error, attempt=1) == 4.0
        assert ErrorHandler.get_retry_delay(error, attempt=2) == 8.0
        assert ErrorHandler.get_retry_delay(error, attempt=5) == 30.0  # capped at 30s
    
    def test_rate_limit_delay_is_longer(self):
        """Test rate limit errors have longer delays"""
        error = APIError("Too Many Requests", status_code=429)
        
        # Base backoff is 60.0 seconds for rate limits
        assert ErrorHandler.get_retry_delay(error, attempt=0) == 60.0
        assert ErrorHandler.get_retry_delay(error, attempt=1) == 120.0
        # Capped at 300s (5 minutes) for rate limits
        assert ErrorHandler.get_retry_delay(error, attempt=5) == 300.0


class TestExecutionError:
    """Test ExecutionError categorization based on exit code"""
    
    def test_sigint_not_retryable(self):
        """Test SIGINT (130) is not retryable"""
        error = ExecutionError("Interrupted", exit_code=130)
        assert error.context.category == ErrorCategory.PERMANENT
        assert error.context.retryable == False
    
    def test_other_signals_are_retryable(self):
        """Test other signal terminations are retryable"""
        error = ExecutionError("Terminated", exit_code=137)  # SIGKILL
        assert error.context.category == ErrorCategory.TRANSIENT
        assert error.context.retryable == True
    
    def test_regular_exit_code_retryable(self):
        """Test regular exit codes are retryable"""
        error = ExecutionError("Command failed", exit_code=1)
        assert error.context.category == ErrorCategory.EXTERNAL
        assert error.context.retryable == True


class TestSpecializedErrors:
    """Test other specialized error types"""
    
    def test_timeout_error_is_retryable(self):
        """Test timeout errors are retryable"""
        error = TimeoutError("Connection timeout", timeout_seconds=30.0)
        assert error.context.category == ErrorCategory.TIMEOUT
        assert error.context.retryable == True
        assert error.context.max_retries == 3
    
    def test_resource_exhausted_is_retryable(self):
        """Test resource exhausted errors are retryable with longer backoff"""
        error = ResourceExhaustedError("Out of memory", resource_type="memory")
        assert error.context.category == ErrorCategory.RESOURCE
        assert error.context.retryable == True
        assert error.context.backoff_seconds == 30.0
    
    def test_validation_error_is_not_retryable(self):
        """Test validation errors are never retryable"""
        error = ValidationError("Invalid field", field="name", value="")
        assert error.context.category == ErrorCategory.VALIDATION
        assert error.context.retryable == False
        assert error.context.max_retries == 0


class TestCommandFailureClassifier:
    """Test the CommandFailureClassifier three-way classification."""

    def test_classifies_temporary_timeout(self):
        classification = CommandFailureClassifier.classify(
            stderr="timed out waiting for connection",
            stdout="",
            return_code=1,
            command="curl http://example.com",
        )
        assert classification.category == CommandFailureCategory.TEMPORARY
        assert classification.retry_allowed is True

    def test_classifies_temporary_connection_refused(self):
        classification = CommandFailureClassifier.classify(
            stderr="connection refused",
            stdout="",
            return_code=1,
            command="curl http://localhost:9999",
        )
        assert classification.category == CommandFailureCategory.TEMPORARY
        assert classification.retry_allowed is True

    def test_classifies_temporary_rate_limit(self):
        classification = CommandFailureClassifier.classify(
            stderr="rate limit exceeded (429)",
            stdout="",
            return_code=1,
            command="curl https://api.example.com",
        )
        assert classification.category == CommandFailureCategory.TEMPORARY
        assert classification.retry_allowed is True

    def test_classifies_sigint_as_temporary(self):
        classification = CommandFailureClassifier.classify(
            stderr="",
            stdout="",
            return_code=130,
            command="long_running_process",
        )
        assert classification.category == CommandFailureCategory.TEMPORARY
        assert classification.retry_allowed is True

    def test_classifies_signal_termination_as_temporary(self):
        classification = CommandFailureClassifier.classify(
            stderr="",
            stdout="",
            return_code=137,
            command="some_command",
        )
        assert classification.category == CommandFailureCategory.TEMPORARY
        assert classification.retry_allowed is True

    def test_classifies_fundamental_no_such_file(self):
        classification = CommandFailureClassifier.classify(
            stderr="No such file or directory: /nonexistent/path",
            stdout="",
            return_code=1,
            command="cat /nonexistent/path",
        )
        assert classification.category == CommandFailureCategory.FUNDAMENTAL_MISUNDERSTANDING
        assert classification.retry_allowed is True

    def test_classifies_fundamental_command_not_found(self):
        classification = CommandFailureClassifier.classify(
            stderr="command not found: nonexistent_tool",
            stdout="",
            return_code=127,
            command="nonexistent_tool",
        )
        assert classification.category == CommandFailureCategory.FUNDAMENTAL_MISUNDERSTANDING
        assert classification.retry_allowed is False

    def test_classifies_fundamental_invalid_option(self):
        classification = CommandFailureClassifier.classify(
            stderr="invalid option -- 'z'",
            stdout="",
            return_code=1,
            command="ls -z",
        )
        assert classification.category == CommandFailureCategory.FUNDAMENTAL_MISUNDERSTANDING
        assert classification.retry_allowed is True

    def test_classifies_environment_permission_denied(self):
        classification = CommandFailureClassifier.classify(
            stderr="permission denied: /etc/shadow",
            stdout="",
            return_code=1,
            command="cat /etc/shadow",
        )
        assert classification.category == CommandFailureCategory.ENVIRONMENT_ERROR
        assert classification.retry_allowed is True

    def test_classifies_environment_missing_module(self):
        classification = CommandFailureClassifier.classify(
            stderr="No module named 'nonexistent_module'",
            stdout="",
            return_code=1,
            command="python -c 'import nonexistent_module'",
        )
        assert classification.category == CommandFailureCategory.ENVIRONMENT_ERROR
        assert classification.retry_allowed is True

    def test_classifies_environment_npm_error(self):
        classification = CommandFailureClassifier.classify(
            stderr="npm ERR! code ENOENT",
            stdout="",
            return_code=1,
            command="npm install",
        )
        assert classification.category == CommandFailureCategory.ENVIRONMENT_ERROR
        assert classification.retry_allowed is True

    def test_classifies_unknown_failure_as_temporary(self):
        classification = CommandFailureClassifier.classify(
            stderr="something went wrong",
            stdout="",
            return_code=1,
            command="some_command",
        )
        assert classification.category == CommandFailureCategory.TEMPORARY
        assert classification.retry_allowed is True

    def test_classifies_success_as_temporary_fallback(self):
        classification = CommandFailureClassifier.classify(
            stderr="",
            stdout="all good",
            return_code=0,
            command="echo hello",
        )
        assert classification.category == CommandFailureCategory.TEMPORARY
        assert classification.retry_allowed is True

    def test_execution_error_includes_classification(self):
        error = ExecutionError(
            "Command failed",
            command="nonexistent_tool",
            exit_code=127,
            stderr="command not found: nonexistent_tool",
            stdout="",
        )
        assert error.failure_classification is not None
        assert error.failure_classification.category == CommandFailureCategory.FUNDAMENTAL_MISUNDERSTANDING
        assert error.context.category == ErrorCategory.PERMANENT
