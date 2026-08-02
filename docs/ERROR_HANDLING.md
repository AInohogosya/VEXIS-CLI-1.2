# Error Handling Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Error Handling Philosophy](#error-handling-philosophy)
3. [Error Classification](#error-classification)
4. [Error Handling Architecture](#error-handling-architecture)
5. [Phase-Specific Error Handling](#phase-specific-error-handling)
6. [Provider Error Handling](#provider-error-handling)
7. [Recovery Strategies](#recovery-strategies)
8. [Error Reporting and Logging](#error-reporting-and-logging)
9. [Custom Error Types](#custom-error-types)
10. [Best Practices](#best-practices)
11. [Error Handling Patterns](#error-handling-patterns)
12. [Monitoring and Alerting](#monitoring-and-alerting)

## Introduction

The 6-Phase Architecture implements a comprehensive error handling system designed to ensure system reliability, graceful degradation, and automatic recovery. This guide provides detailed information about the error handling mechanisms, recovery strategies, and best practices for managing errors across all phases of the architecture.

### Error Handling Objectives

- **Graceful Degradation**: System continues operating with reduced functionality
- **Automatic Recovery**: Self-healing mechanisms for common failures
- **Detailed Diagnostics**: Comprehensive error information for debugging
- **User-Friendly Messages**: Clear, actionable error messages for users
- **Audit Trail**: Complete logging of all errors and recovery actions

## Error Handling Philosophy

### Core Principles

1. **Fail Fast, Fail Loud**: Detect and report errors immediately
2. **Never Silently Ignore**: Every error is logged and tracked
3. **Recover When Possible**: Automatic recovery for transient failures
4. **Degrade Gracefully**: Reduce functionality rather than complete failure
5. **Inform the User**: Provide clear, actionable error messages

### Error Handling Layers

```
┌─────────────────────────────────────────────┐
│              User Interface Layer            │
│  (User-friendly messages, suggestions)       │
├─────────────────────────────────────────────┤
│              Application Layer               │
│  (Business logic errors, validation)         │
├─────────────────────────────────────────────┤
│              Phase Execution Layer           │
│  (Phase-specific errors, retries)            │
├─────────────────────────────────────────────┤
│              Provider Abstraction Layer      │
│  (Provider errors, fallback logic)           │
├─────────────────────────────────────────────┤
│              Infrastructure Layer            │
│  (Network, database, system errors)          │
└─────────────────────────────────────────────┘
```

## Error Classification

### Error Categories

#### 1. Transient Errors

Errors that are temporary and likely to resolve on retry.

| Error Type | Description | Retry Strategy |
|------------|-------------|----------------|
| `NetworkTimeout` | Network request timed out | Exponential backoff |
| `RateLimitExceeded` | API rate limit reached | Wait and retry |
| `ServiceUnavailable` | Provider service down | Switch provider |
| `ConnectionReset` | Connection dropped | Immediate retry |
| `TemporaryFailure` | Temporary system issue | Fixed delay retry |

#### 2. Permanent Errors

Errors that require intervention to resolve.

| Error Type | Description | Resolution |
|------------|-------------|------------|
| `AuthenticationError` | Invalid credentials | Update credentials |
| `AuthorizationError` | Insufficient permissions | Request access |
| `ResourceNotFound` | Resource does not exist | Verify resource |
| `InvalidConfiguration` | Configuration error | Fix configuration |
| `QuotaExceeded` | Usage quota exceeded | Upgrade plan |

#### 3. Validation Errors

Errors caused by invalid input or parameters.

| Error Type | Description | Resolution |
|------------|-------------|------------|
| `InvalidInput` | Input does not match schema | Correct input |
| `MissingParameter` | Required parameter missing | Provide parameter |
| `TypeMismatch` | Parameter type incorrect | Fix type |
| `ConstraintViolation` | Value violates constraints | Adjust value |
| `FormatError` | Invalid format | Fix format |

#### 4. System Errors

Errors caused by system-level issues.

| Error Type | Description | Resolution |
|------------|-------------|------------|
| `OutOfMemory` | Insufficient memory | Scale resources |
| `DiskFull` | Insufficient disk space | Free disk space |
| `ProcessCrashed` | Process terminated unexpectedly | Restart process |
| `DependencyMissing` | Required dependency not found | Install dependency |
| `SystemOverload` | System under heavy load | Scale horizontally |

### Error Severity Levels

```python
class ErrorSeverity:
    """Error severity levels."""
    
    DEBUG = 0      # Informational, no action required
    INFO = 1       # Minor issue, logged for reference
    WARNING = 2    # Potential issue, monitoring required
    ERROR = 3      # Error occurred, recovery attempted
    CRITICAL = 4   # System failure, immediate attention required
    FATAL = 5      # Unrecoverable error, system shutdown
```

## Error Handling Architecture

### Error Handling Flow

```
┌──────────────┐
│ Error Occurs │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Classify Error   │
│ (Type, Severity) │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐     ┌──────────────────┐
│ Transient Error? │────▶│ Retry with       │
│                  │ Yes │ Exponential      │
│                  │     │ Backoff          │
└──────┬───────────┘     └──────────────────┘
       │ No
       ▼
┌──────────────────┐     ┌──────────────────┐
│ Recoverable?     │────▶│ Execute Recovery │
│                  │ Yes │ Strategy         │
│                  │     └──────────────────┘
└──────┬───────────┘
       │ No
       ▼
┌──────────────────┐
│ Log Error        │
│ Alert if needed  │
│ Report to user   │
└──────────────────┘
```

### Error Handler Implementation

```python
import time
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Central error handling system."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_counts = {}
        self.recovery_strategies = {}
    
    def classify_error(self, error: Exception) -> dict:
        """Classify an error by type and severity."""
        error_type = type(error).__name__
        
        transient_errors = [
            'NetworkTimeout', 'RateLimitExceeded',
            'ServiceUnavailable', 'ConnectionReset'
        ]
        
        permanent_errors = [
            'AuthenticationError', 'AuthorizationError',
            'ResourceNotFound', 'InvalidConfiguration'
        ]
        
        if error_type in transient_errors:
            return {
                'category': 'transient',
                'severity': 'WARNING',
                'retryable': True
            }
        elif error_type in permanent_errors:
            return {
                'category': 'permanent',
                'severity': 'ERROR',
                'retryable': False
            }
        else:
            return {
                'category': 'unknown',
                'severity': 'ERROR',
                'retryable': False
            }
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                classification = self.classify_error(e)
                
                if not classification['retryable']:
                    logger.error(
                        f"Non-retryable error: {e}"
                    )
                    raise
                
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
        
        logger.error(
            f"All {self.max_retries + 1} attempts failed. "
            f"Last error: {last_error}"
        )
        raise last_error
    
    def register_recovery(
        self,
        error_type: str,
        recovery_func: Callable
    ):
        """Register a recovery strategy for an error type."""
        self.recovery_strategies[error_type] = recovery_func
    
    def attempt_recovery(self, error: Exception) -> bool:
        """Attempt to recover from an error."""
        error_type = type(error).__name__
        
        if error_type in self.recovery_strategies:
            try:
                recovery_func = self.recovery_strategies[error_type]
                recovery_func(error)
                logger.info(
                    f"Successfully recovered from {error_type}"
                )
                return True
            except Exception as recovery_error:
                logger.error(
                    f"Recovery failed for {error_type}: "
                    f"{recovery_error}"
                )
                return False
        
        return False
```

### Decorator-Based Error Handling

```python
def with_error_handling(
    max_retries: int = 3,
    fallback: Optional[Callable] = None,
    error_types: tuple = (Exception,)
):
    """Decorator for automatic error handling."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(max_retries=max_retries)
            
            try:
                return handler.execute_with_retry(
                    func, *args, **kwargs
                )
            except error_types as e:
                # Attempt recovery
                if handler.attempt_recovery(e):
                    return func(*args, **kwargs)
                
                # Use fallback if provided
                if fallback:
                    logger.warning(
                        f"Using fallback for {func.__name__}"
                    )
                    return fallback(*args, **kwargs)
                
                # Re-raise if no recovery or fallback
                raise
        return wrapper
    return decorator

# Usage example
@with_error_handling(
    max_retries=3,
    fallback=lambda: {"result": "default"},
    error_types=(NetworkTimeout, ConnectionReset)
)
def call_external_api():
    """Call external API with automatic error handling."""
    response = requests.get("https://api.example.com/data")
    return response.json()
```

## Phase-Specific Error Handling

### Phase 1: Strategic Assessment Errors

```python
class Phase1ErrorHandler:
    """Error handler for Phase 1: Strategic Assessment."""
    
    def __init__(self):
        self.error_handler = ErrorHandler(max_retries=2)
    
    def handle_intent_analysis_error(self, error: Exception):
        """Handle intent analysis failures."""
        if isinstance(error, AmbiguousInputError):
            # Request clarification from user
            return {
                "status": "needs_clarification",
                "message": "Could not determine intent. Please provide more details.",
                "suggestions": self._generate_suggestions()
            }
        elif isinstance(error, ModelOverloadError):
            # Switch to simpler model
            return self._fallback_to_simple_model()
        else:
            raise error
    
    def handle_risk_assessment_error(self, error: Exception):
        """Handle risk assessment failures."""
        logger.warning(f"Risk assessment error: {error}")
        # Return default risk assessment
        return {
            "risk_level": "medium",
            "confidence": 0.5,
            "note": "Default assessment due to analysis error"
        }
    
    def _generate_suggestions(self) -> list:
        """Generate suggestions for ambiguous input."""
        return [
            "Be more specific about the task",
            "Provide context about the environment",
            "Specify expected outcomes"
        ]
    
    def _fallback_to_simple_model(self) -> dict:
        """Fallback to a simpler model."""
        return {
            "status": "degraded",
            "message": "Using simplified analysis due to model overload",
            "model": "simple-intent-classifier"
        }
```

### Phase 2: Architecture Design Errors

```python
class Phase2ErrorHandler:
    """Error handler for Phase 2: Architecture Design."""
    
    def handle_component_selection_error(self, error: Exception):
        """Handle component selection failures."""
        if isinstance(error, ComponentNotFoundError):
            # Use default component
            return self._get_default_component()
        elif isinstance(error, CompatibilityError):
            # Find compatible alternative
            return self._find_compatible_alternative(error)
        else:
            raise error
    
    def handle_design_validation_error(self, error: Exception):
        """Handle design validation failures."""
        return {
            "status": "validation_failed",
            "errors": self._parse_validation_errors(error),
            "recommendations": self._generate_recommendations(error)
        }
    
    def _get_default_component(self) -> dict:
        """Get default component as fallback."""
        return {
            "component": "default",
            "reason": "Using default component due to selection error"
        }
    
    def _find_compatible_alternative(self, error: CompatibilityError) -> dict:
        """Find compatible alternative component."""
        return {
            "component": error.alternative,
            "reason": f"Alternative for incompatible component: {error.component}"
        }
```

### Phase 3: Pilot Implementation Errors

```python
class Phase3ErrorHandler:
    """Error handler for Phase 3: Pilot Implementation."""
    
    def __init__(self):
        self.error_handler = ErrorHandler(max_retries=5)
        self.checkpoint_manager = CheckpointManager()
    
    def handle_execution_error(self, error: Exception, context: dict):
        """Handle command execution errors."""
        # Save checkpoint before recovery
        self.checkpoint_manager.save_checkpoint(context)
        
        if isinstance(error, CommandTimeoutError):
            return self._handle_timeout(error, context)
        elif isinstance(error, PermissionError):
            return self._handle_permission_error(error, context)
        elif isinstance(error, ResourceExhaustedError):
            return self._handle_resource_exhaustion(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_timeout(self, error: CommandTimeoutError, context: dict):
        """Handle command timeout."""
        return {
            "status": "timeout",
            "partial_result": context.get("partial_result"),
            "suggestion": "Consider breaking the task into smaller steps"
        }
    
    def _handle_permission_error(self, error: PermissionError, context: dict):
        """Handle permission errors."""
        return {
            "status": "permission_denied",
            "required_permissions": error.required_permissions,
            "suggestion": "Run with elevated privileges or adjust permissions"
        }
    
    def _handle_resource_exhaustion(self, error: ResourceExhaustedError, context: dict):
        """Handle resource exhaustion."""
        # Free resources and retry
        self._free_resources()
        return {
            "status": "retrying",
            "message": "Resources freed, retrying execution"
        }
    
    def _free_resources(self):
        """Free system resources."""
        import gc
        gc.collect()
```

### Phase 4: Integration & Scaling Errors

```python
class Phase4ErrorHandler:
    """Error handler for Phase 4: Integration & Scaling."""
    
    def handle_integration_error(self, error: Exception, system: str):
        """Handle integration failures."""
        if isinstance(error, APIConnectionError):
            return self._handle_api_connection_error(error, system)
        elif isinstance(error, DataSyncError):
            return self._handle_data_sync_error(error, system)
        elif isinstance(error, ConfigurationMismatchError):
            return self._handle_config_mismatch(error, system)
        else:
            raise error
    
    def handle_scaling_error(self, error: Exception):
        """Handle scaling failures."""
        if isinstance(error, InsufficientResourcesError):
            return {
                "status": "scaling_delayed",
                "message": "Insufficient resources for scaling",
                "retry_after": 300
            }
        elif isinstance(error, LoadBalancerError):
            return self._handle_load_balancer_error(error)
        else:
            raise error
```

### Phase 5: Optimization & Governance Errors

```python
class Phase5ErrorHandler:
    """Error handler for Phase 5: Optimization & Governance."""
    
    def handle_optimization_error(self, error: Exception):
        """Handle optimization failures."""
        logger.warning(f"Optimization error: {error}")
        # Return current state without optimization
        return {
            "status": "optimization_skipped",
            "message": "Optimization skipped due to error",
            "current_metrics": self._get_current_metrics()
        }
    
    def handle_governance_error(self, error: Exception):
        """Handle governance violations."""
        if isinstance(error, ComplianceViolationError):
            return {
                "status": "compliance_violation",
                "violation": error.violation_details,
                "action_required": "Manual review required"
            }
        elif isinstance(error, PolicyViolationError):
            return {
                "status": "policy_violation",
                "policy": error.policy_name,
                "remediation": error.remediation_steps
            }
        else:
            raise error
```

### Phase 6: Enterprise Transformation Errors

```python
class Phase6ErrorHandler:
    """Error handler for Phase 6: Enterprise Transformation."""
    
    def handle_transformation_error(self, error: Exception):
        """Handle transformation failures."""
        if isinstance(error, RollbackRequiredError):
            return self._execute_rollback(error)
        elif isinstance(error, PartialDeploymentError):
            return self._handle_partial_deployment(error)
        elif isinstance(error, StakeholderApprovalError):
            return {
                "status": "pending_approval",
                "message": "Transformation requires stakeholder approval",
                "approvers": error.required_approvers
            }
        else:
            raise error
    
    def _execute_rollback(self, error: RollbackRequiredError) -> dict:
        """Execute rollback procedure."""
        logger.critical(f"Executing rollback: {error.reason}")
        return {
            "status": "rolling_back",
            "reason": error.reason,
            "rollback_steps": error.rollback_steps
        }
```

## Provider Error Handling

### Provider Error Classification

```python
class ProviderErrorHandler:
    """Handle errors from AI providers."""
    
    PROVIDER_ERRORS = {
        'groq': {
            'rate_limit': ('RateLimitExceeded', 'WARNING', True),
            'auth_error': ('AuthenticationError', 'ERROR', False),
            'timeout': ('NetworkTimeout', 'WARNING', True),
            'model_error': ('ModelError', 'ERROR', False),
        },
        'google': {
            'quota_exceeded': ('QuotaExceeded', 'ERROR', False),
            'invalid_request': ('InvalidInput', 'ERROR', False),
            'service_unavailable': ('ServiceUnavailable', 'WARNING', True),
        },
        'ollama': {
            'connection_refused': ('ConnectionError', 'ERROR', True),
            'model_not_found': ('ResourceNotFound', 'ERROR', False),
            'out_of_memory': ('OutOfMemory', 'CRITICAL', False),
        }
    }
    
    def handle_provider_error(
        self,
        provider: str,
        error_code: str,
        error_message: str
    ) -> dict:
        """Handle provider-specific errors."""
        provider_errors = self.PROVIDER_ERRORS.get(provider, {})
        error_info = provider_errors.get(error_code, ('UnknownError', 'ERROR', False))
        
        error_type, severity, retryable = error_info
        
        return {
            'provider': provider,
            'error_type': error_type,
            'severity': severity,
            'retryable': retryable,
            'message': error_message,
            'timestamp': time.time()
        }
    
    def should_switch_provider(self, error: dict) -> bool:
        """Determine if provider should be switched."""
        return (
            error['severity'] in ('ERROR', 'CRITICAL') and
            not error['retryable']
        )
```

### Provider Fallback Chain

```python
class ProviderFallbackChain:
    """Manage provider fallback chain."""
    
    def __init__(self, providers: list):
        self.providers = providers
        self.current_index = 0
        self.failure_counts = {p: 0 for p in providers}
    
    def get_current_provider(self) -> str:
        """Get current active provider."""
        return self.providers[self.current_index]
    
    def switch_to_next(self) -> Optional[str]:
        """Switch to next available provider."""
        self.failure_counts[self.get_current_provider()] += 1
        
        for i in range(len(self.providers)):
            idx = (self.current_index + i + 1) % len(self.providers)
            provider = self.providers[idx]
            
            if self.failure_counts[provider] < 3:
                self.current_index = idx
                logger.info(f"Switched to provider: {provider}")
                return provider
        
        logger.error("All providers exhausted")
        return None
    
    def reset(self):
        """Reset failure counts."""
        self.failure_counts = {p: 0 for p in self.providers}
        self.current_index = 0
```

## Recovery Strategies

### Automatic Recovery

```python
class RecoveryManager:
    """Manage automatic recovery strategies."""
    
    def __init__(self):
        self.strategies = {}
        self.recovery_history = []
    
    def register_strategy(
        self,
        error_type: str,
        strategy: Callable,
        max_attempts: int = 3
    ):
        """Register a recovery strategy."""
        self.strategies[error_type] = {
            'func': strategy,
            'max_attempts': max_attempts,
            'attempts': 0
        }
    
    def attempt_recovery(self, error: Exception, context: dict) -> bool:
        """Attempt to recover from an error."""
        error_type = type(error).__name__
        
        if error_type not in self.strategies:
            logger.warning(f"No recovery strategy for {error_type}")
            return False
        
        strategy = self.strategies[error_type]
        
        if strategy['attempts'] >= strategy['max_attempts']:
            logger.error(
                f"Max recovery attempts reached for {error_type}"
            )
            return False
        
        try:
            strategy['func'](error, context)
            strategy['attempts'] += 1
            self.recovery_history.append({
                'error_type': error_type,
                'timestamp': time.time(),
                'success': True
            })
            logger.info(f"Recovery successful for {error_type}")
            return True
        except Exception as recovery_error:
            logger.error(f"Recovery failed: {recovery_error}")
            self.recovery_history.append({
                'error_type': error_type,
                'timestamp': time.time(),
                'success': False,
                'error': str(recovery_error)
            })
            return False
```

### Checkpoint Recovery

```python
class CheckpointManager:
    """Manage execution checkpoints for recovery."""
    
    def __init__(self, checkpoint_dir: str = "/tmp/vexis_checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoints = {}
    
    def save_checkpoint(self, context: dict):
        """Save execution checkpoint."""
        checkpoint_id = context.get('task_id', 'unknown')
        checkpoint = {
            'id': checkpoint_id,
            'timestamp': time.time(),
            'phase': context.get('phase'),
            'step': context.get('step'),
            'data': context.get('data', {}),
            'progress': context.get('progress', 0)
        }
        
        self.checkpoints[checkpoint_id] = checkpoint
        logger.debug(f"Checkpoint saved: {checkpoint_id}")
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        """Restore from checkpoint."""
        checkpoint = self.checkpoints.get(checkpoint_id)
        
        if checkpoint:
            logger.info(f"Restored from checkpoint: {checkpoint_id}")
            return checkpoint
        
        logger.warning(f"Checkpoint not found: {checkpoint_id}")
        return None
    
    def cleanup_old_checkpoints(self, max_age: int = 86400):
        """Clean up old checkpoints."""
        current_time = time.time()
        to_remove = []
        
        for checkpoint_id, checkpoint in self.checkpoints.items():
            if current_time - checkpoint['timestamp'] > max_age:
                to_remove.append(checkpoint_id)
        
        for checkpoint_id in to_remove:
            del self.checkpoints[checkpoint_id]
            logger.debug(f"Cleaned up checkpoint: {checkpoint_id}")
```

## Error Reporting and Logging

### Structured Error Logging

```python
import json
from datetime import datetime

class StructuredErrorLogger:
    """Structured error logging system."""
    
    def __init__(self, log_file: str = "errors.json"):
        self.log_file = log_file
    
    def log_error(
        self,
        error: Exception,
        context: dict,
        severity: str = "ERROR"
    ):
        """Log error in structured format."""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": self._get_traceback(error),
            "context": {
                "phase": context.get("phase"),
                "step": context.get("step"),
                "task_id": context.get("task_id"),
                "provider": context.get("provider"),
                "user_id": context.get("user_id")
            },
            "system": {
                "hostname": context.get("hostname"),
                "platform": context.get("platform"),
                "version": context.get("version")
            }
        }
        
        # Write to structured log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(error_entry) + "\n")
        
        # Also log to standard logger
        logger.log(
            self._severity_to_level(severity),
            f"[{error_entry['error_type']}] {error_entry['error_message']}"
        )
    
    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback."""
        import traceback
        return traceback.format_exception(
            type(error), error, error.__traceback__
        )
    
    def _severity_to_level(self, severity: str) -> int:
        """Convert severity string to logging level."""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(severity, logging.ERROR)
```

## Custom Error Types

```python
# Custom exception hierarchy
class VEXISBaseError(Exception):
    """Base exception for VEXIS-CLI-3."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}
        self.timestamp = time.time()

# Phase-specific errors
class PhaseExecutionError(VEXISBaseError):
    """Error during phase execution."""
    pass

class PhaseTimeoutError(PhaseExecutionError):
    """Phase execution timed out."""
    pass

class PhaseDependencyError(PhaseExecutionError):
    """Phase dependency not met."""
    pass

# Provider errors
class ProviderError(VEXISBaseError):
    """Base provider error."""
    pass

class ProviderConnectionError(ProviderError):
    """Failed to connect to provider."""
    pass

class ProviderResponseError(ProviderError):
    """Invalid response from provider."""
    pass

class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""
    pass

# Task errors
class TaskError(VEXISBaseError):
    """Base task error."""
    pass

class TaskExecutionError(TaskError):
    """Task execution failed."""
    pass

class TaskValidationError(TaskError):
    """Task validation failed."""
    pass

class TaskTimeoutError(TaskError):
    """Task execution timed out."""
    pass

# Configuration errors
class ConfigurationError(VEXISBaseError):
    """Configuration error."""
    pass

class InvalidConfigurationError(ConfigurationError):
    """Invalid configuration."""
    pass

class MissingConfigurationError(ConfigurationError):
    """Required configuration missing."""
    pass

# Security errors
class SecurityError(VEXISBaseError):
    """Security-related error."""
    pass

class AuthenticationError(SecurityError):
    """Authentication failed."""
    pass

class AuthorizationError(SecurityError):
    """Authorization failed."""
    pass

class ComplianceViolationError(SecurityError):
    """Compliance violation detected."""
    pass
```

## Best Practices

### Error Handling Best Practices

1. **Use Specific Exception Types**
   ```python
   # Good
   raise TaskExecutionError(
       "Command failed",
       details={"command": "ls", "exit_code": 1}
   )
   
   # Bad
   raise Exception("Something went wrong")
   ```

2. **Include Context Information**
   ```python
   # Good
   raise ProviderConnectionError(
       f"Failed to connect to {provider}",
       details={
           "provider": provider,
           "endpoint": endpoint,
           "timeout": timeout
       }
   )
   ```

3. **Implement Proper Cleanup**
   ```python
   try:
       resource = acquire_resource()
       process(resource)
   finally:
       release_resource(resource)
   ```

4. **Use Context Managers**
   ```python
   with managed_resource() as resource:
       process(resource)
   # Resource automatically cleaned up
   ```

5. **Log Before Raising**
   ```python
   logger.error(f"Operation failed: {error_details}")
   raise OperationFailedError(error_details)
   ```

### Anti-Patterns to Avoid

1. **Silent Exception Swallowing**
   ```python
   # Bad
   try:
       risky_operation()
   except:
       pass
   
   # Good
   try:
       risky_operation()
   except SpecificError as e:
       logger.error(f"Operation failed: {e}")
       handle_error(e)
   ```

2. **Overly Broad Exception Handling**
   ```python
   # Bad
   try:
       specific_operation()
   except Exception as e:
       handle_all_errors(e)
   
   # Good
   try:
       specific_operation()
   except ExpectedError as e:
       handle_expected(e)
   except AnotherError as e:
       handle_another(e)
   ```

3. **Losing Stack Trace**
   ```python
   # Bad
   try:
       operation()
   except Exception as e:
       raise NewError("Failed")  # Lost original traceback
   
   # Good
   try:
       operation()
   except Exception as e:
       raise NewError("Failed") from e  # Preserves chain
   ```

## Error Handling Patterns

### Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance."""
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker."""
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = self.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    "Circuit breaker is open"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = self.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            logger.warning(
                f"Circuit breaker opened after "
                f"{self.failure_count} failures"
            )
```

### Retry with Exponential Backoff

```python
def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,)
) -> Any:
    """Retry function with exponential backoff."""
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except retryable_exceptions as e:
            last_error = e
            
            if attempt < max_retries:
                delay = min(
                    base_delay * (exponential_base ** attempt),
                    max_delay
                )
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
    
    raise last_error
```

### Bulkhead Pattern

```python
class Bulkhead:
    """Bulkhead pattern for resource isolation."""
    
    def __init__(self, max_concurrent: int = 10, max_wait: int = 30):
        self.semaphore = threading.Semaphore(max_concurrent)
        self.max_wait = max_wait
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function within bulkhead."""
        acquired = self.semaphore.acquire(timeout=self.max_wait)
        
        if not acquired:
            raise BulkheadFullError(
                "Bulkhead is full, cannot accept more requests"
            )
        
        try:
            return func(*args, **kwargs)
        finally:
            self.semaphore.release()
```

## Monitoring and Alerting

### Error Metrics

```python
class ErrorMetrics:
    """Track and report error metrics."""
    
    def __init__(self):
        self.error_counts = {}
        self.error_rates = {}
        self.last_errors = {}
    
    def record_error(self, error_type: str, severity: str):
        """Record an error occurrence."""
        key = f"{error_type}:{severity}"
        
        if key not in self.error_counts:
            self.error_counts[key] = 0
        
        self.error_counts[key] += 1
        self.last_errors[key] = time.time()
    
    def get_error_rate(self, error_type: str, window: int = 300) -> float:
        """Get error rate for a specific error type."""
        key = f"{error_type}:ERROR"
        last_time = self.last_errors.get(key, 0)
        
        if time.time() - last_time > window:
            return 0.0
        
        return self.error_counts.get(key, 0) / window
    
    def get_summary(self) -> dict:
        """Get error summary."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts,
            "last_errors": self.last_errors,
            "timestamp": time.time()
        }
```

### Alert Configuration

```yaml
# Error alerting configuration
error_alerting:
  enabled: true
  
  rules:
    - name: "High Error Rate"
      condition: "error_rate > 10"
      severity: "WARNING"
      channels: ["slack", "email"]
      cooldown: 300
    
    - name: "Critical Error"
      condition: "severity == 'CRITICAL'"
      severity: "CRITICAL"
      channels: ["pagerduty", "slack", "email"]
      cooldown: 60
    
    - name: "Provider Down"
      condition: "provider_status == 'down'"
      severity: "ERROR"
      channels: ["slack"]
      cooldown: 120
    
    - name: "Circuit Breaker Open"
      condition: "circuit_breaker == 'open'"
      severity: "WARNING"
      channels: ["slack", "email"]
      cooldown: 180
```

---

**Error Handling Version**: 2.1.0  
**Last Updated**: 2026-05-24  
**Maintainer**: VEXIS-CLI-3 Development Team