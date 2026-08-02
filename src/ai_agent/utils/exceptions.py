"""
Exception classes for AI Agent System
Enhanced exceptions with categorization for 5-Phase Architecture
"""

import re
from enum import Enum, auto
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


class ErrorCategory(Enum):
    """Error categories for intelligent error handling and retry strategies"""
    TRANSIENT = "transient"           # Temporary errors, retryable (network timeout)
    PERMANENT = "permanent"           # Permanent errors, not retryable (invalid syntax)
    AUTHENTICATION = "authentication"  # Auth errors, require re-authentication
    RATE_LIMIT = "rate_limit"         # Rate limiting, retry with backoff
    VALIDATION = "validation"         # Input validation errors
    RESOURCE = "resource"             # Resource exhaustion (OOM, disk full)
    TIMEOUT = "timeout"               # Timeout errors
    CONFIGURATION = "configuration"   # Configuration errors
    EXTERNAL = "external"             # External service errors (API failures)
    UNKNOWN = "unknown"               # Uncategorized errors


@dataclass
class ErrorContext:
    """Context information for error handling"""
    category: ErrorCategory
    retryable: bool
    max_retries: int
    backoff_seconds: float
    error_code: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    phase: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AIAgentException(Exception):
    """Base exception for AI Agent system with categorization support"""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None, **kwargs):
        super().__init__(message)
        self.context = context or ErrorContext(
            category=ErrorCategory.UNKNOWN,
            retryable=False,
            max_retries=0,
            backoff_seconds=0.0
        )
        # Store any additional keyword arguments as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def is_retryable(self) -> bool:
        """Check if this error is retryable"""
        return self.context.retryable if self.context else False
    
    def get_retry_delay(self) -> float:
        """Get recommended retry delay in seconds"""
        return self.context.backoff_seconds if self.context else 0.0


class APIError(AIAgentException):
    """API-related error with automatic categorization"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        # Auto-categorize based on status code
        if status_code == 401 or status_code == 403:
            category = ErrorCategory.AUTHENTICATION
            retryable = False
            max_retries = 0
            backoff = 0.0
        elif status_code == 429:
            category = ErrorCategory.RATE_LIMIT
            retryable = True
            max_retries = 5
            backoff = 60.0  # 1 minute
        elif status_code and 500 <= status_code < 600:
            category = ErrorCategory.EXTERNAL
            retryable = True
            max_retries = 3
            backoff = 2.0
        elif status_code and 400 <= status_code < 500:
            category = ErrorCategory.VALIDATION
            retryable = False
            max_retries = 0
            backoff = 0.0
        else:
            category = ErrorCategory.EXTERNAL
            retryable = True
            max_retries = 3
            backoff = 1.0
        
        context = ErrorContext(
            category=category,
            retryable=retryable,
            max_retries=max_retries,
            backoff_seconds=backoff,
            error_code=str(status_code) if status_code else None
        )
        super().__init__(message, context=context, **kwargs)
        self.status_code = status_code


class ValidationError(AIAgentException):
    """Validation error - not retryable"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.VALIDATION,
            retryable=False,
            max_retries=0,
            backoff_seconds=0.0
        )
        super().__init__(message, context=context, **kwargs)
        self.field = field
        self.value = value


class ConfigurationError(AIAgentException):
    """Configuration error - not retryable"""
    
    def __init__(self, message: str, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.CONFIGURATION,
            retryable=False,
            max_retries=0,
            backoff_seconds=0.0
        )
        super().__init__(message, context=context, **kwargs)


class PlatformError(AIAgentException):
    """Platform-related error"""
    
    def __init__(self, message: str, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.EXTERNAL,
            retryable=True,
            max_retries=2,
            backoff_seconds=1.0
        )
        super().__init__(message, context=context, **kwargs)


class ScreenshotError(AIAgentException):
    """Screenshot-related error"""
    pass


class CommandFailureCategory(Enum):
    """Three-way classification for command execution failures.
    
    - TEMPORARY: The command failed due to a transient condition (network blip,
      service restarting, resource contention). Retrying is allowed and likely
      to succeed.
    - FUNDAMENTAL_MISUNDERSTANDING: The command or approach is fundamentally
      wrong for the objective. The LLM misunderstood the task or the environment.
      The correct response is to ask the user for clarification or to completely
      reconsider the approach.
    - ENVIRONMENT_ERROR: The command is correct but the environment is not set up
      properly (missing dependency, wrong working directory, permission denied).
      An alternative approach or different command is needed.
    """
    TEMPORARY = "temporary"
    FUNDAMENTAL_MISUNDERSTANDING = "fundamental_misunderstanding"
    ENVIRONMENT_ERROR = "environment_error"


@dataclass
class CommandFailureClassification:
    """Result of classifying a command failure."""
    category: CommandFailureCategory
    reason: str
    suggestion: str
    retry_allowed: bool
    stderr_patterns_matched: List[str] = field(default_factory=list)


class CommandFailureClassifier:
    """Classifies command execution failures into actionable categories.
    
    Examines stderr output, exit code, and command content to determine
    whether a failure is temporary (retryable), a fundamental misunderstanding
    (needs user clarification), or an environment issue (needs alternative approach).
    """

    # Patterns that indicate temporary/transient failures
    TEMPORARY_PATTERNS = [
        r'time\s*out',
        r'timed\s*out',
        r'connection\s*refused',
        r'connection\s*reset',
        r'network\s*(error|unreachable)',
        r'failed to connect',
        r'temporary\s*failure',
        r'resource temporarily unavailable',
        r'econnrefused',
        r'econnreset',
        r'etimedout',
        r'too many (open files|connections)',
        r'rate\s*limit',
        r'429',
        r'503',
        r'502',
    ]

    # Patterns that indicate fundamental misunderstanding
    FUNDAMENTAL_PATTERNS = [
        r'no such (file|directory)',
        r'not found',
        r'command not found',
        r'unknown command',
        r'invalid option',
        r'unrecognized',
        r'bad (option|argument)',
        r'illegal option',
        r'requires a (valid )?argument',
        r'usage:',
        r'no matching',
        r'is not (a|an|valid)',
        r'cannot find',
        r'does not exist',
        r'No such',
    ]

    # Patterns that indicate environment/precondition errors
    ENVIRONMENT_PATTERNS = [
        r'permission denied',
        r'eacces',
        r'not permitted',
        r'insufficient',
        r'cannot (create|open|access)',
        r'is not installed',
        r'no module named',
        r'import error',
        r'missing',
        r'not\s*configured',
        r'requires.*to be (installed|set up|configured)',
        r'docker:.*not found',
        r'git:.*not (a|an)',
        r'npm ERR!',
        r'pip.*error',
        r'virtualenv',
        r'venv',
        r'already (exists|installed)',
        r'conflict',
        r'version.*not (supported|found|available)',
        r'does not support',
        r'eexist',
        r'enospc',
    ]

    @staticmethod
    def classify(
        stderr: str,
        stdout: str,
        return_code: int,
        command: str,
    ) -> CommandFailureClassification:
        """Classify a command failure into one of three categories.
        
        Args:
            stderr: Standard error output from the command.
            stdout: Standard output from the command.
            return_code: Exit code of the command.
            command: The shell command that was executed.
            
        Returns:
            A CommandFailureClassification with category, reason, and suggestion.
        """
        combined = f"{stderr}\n{stdout}".lower()
        matched_temporary: List[str] = []
        matched_fundamental: List[str] = []
        matched_environment: List[str] = []

        for pattern in CommandFailureClassifier.TEMPORARY_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                matched_temporary.append(pattern)

        for pattern in CommandFailureClassifier.FUNDAMENTAL_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                matched_fundamental.append(pattern)

        for pattern in CommandFailureClassifier.ENVIRONMENT_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                matched_environment.append(pattern)

        # Priority-based classification
        if return_code == 130:
            return CommandFailureClassification(
                category=CommandFailureCategory.TEMPORARY,
                reason="Command was interrupted by user (SIGINT)",
                suggestion="Retry the command if needed.",
                retry_allowed=True,
                stderr_patterns_matched=matched_temporary,
            )

        if return_code == 127:
            return CommandFailureClassification(
                category=CommandFailureCategory.FUNDAMENTAL_MISUNDERSTANDING,
                reason="Command not found (exit code 127)",
                suggestion="The command or tool is not available. Check if it needs to be installed or use a different approach.",
                retry_allowed=False,
                stderr_patterns_matched=matched_fundamental,
            )

        if matched_temporary:
            return CommandFailureClassification(
                category=CommandFailureCategory.TEMPORARY,
                reason=f"Temporary/transient failure detected: matched patterns {matched_temporary}",
                suggestion="Retry the command - this is likely a transient issue.",
                retry_allowed=True,
                stderr_patterns_matched=matched_temporary,
            )

        if matched_fundamental:
            return CommandFailureClassification(
                category=CommandFailureCategory.FUNDAMENTAL_MISUNDERSTANDING,
                reason=f"Command or approach is fundamentally wrong: matched patterns {matched_fundamental}",
                suggestion="Reconsider the approach. The command syntax, path, or tool is incorrect for this environment.",
                retry_allowed=True,
                stderr_patterns_matched=matched_fundamental,
            )

        if matched_environment:
            return CommandFailureClassification(
                category=CommandFailureCategory.ENVIRONMENT_ERROR,
                reason=f"Environment issue detected: matched patterns {matched_environment}",
                suggestion="Try an alternative approach. The environment may need configuration changes or a different tool.",
                retry_allowed=True,
                stderr_patterns_matched=matched_environment,
            )

        if return_code and return_code > 128:
            return CommandFailureClassification(
                category=CommandFailureCategory.TEMPORARY,
                reason=f"Command terminated by signal (exit code {return_code})",
                suggestion="Retry the command. The process was killed by a signal, likely a transient issue.",
                retry_allowed=True,
                stderr_patterns_matched=[],
            )

        if return_code != 0 and return_code != -1:
            return CommandFailureClassification(
                category=CommandFailureCategory.TEMPORARY,
                reason=f"Command failed with exit code {return_code}. No specific failure pattern matched.",
                suggestion="Retry the command. If it fails again, consider using a different approach.",
                retry_allowed=True,
                stderr_patterns_matched=[],
            )

        return CommandFailureClassification(
            category=CommandFailureCategory.TEMPORARY,
            reason="Command succeeded or unknown state",
            suggestion="No action needed.",
            retry_allowed=True,
            stderr_patterns_matched=[],
        )


class ExecutionError(AIAgentException):
    """Execution error - may be retryable depending on command"""
    
    def __init__(self, message: str, command: Optional[str] = None, exit_code: Optional[int] = None, **kwargs):
        # Classify the failure
        classification = CommandFailureClassifier.classify(
            stderr=kwargs.pop("stderr", ""),
            stdout=kwargs.pop("stdout", ""),
            return_code=exit_code or -1,
            command=command or "",
        )
        self.failure_classification = classification
        
        # Determine retryability based on classification
        if classification.category == CommandFailureCategory.FUNDAMENTAL_MISUNDERSTANDING:
            category = ErrorCategory.PERMANENT
            retryable = classification.retry_allowed
            max_retries = 2 if retryable else 0
            backoff = 1.0
        elif classification.category == CommandFailureCategory.ENVIRONMENT_ERROR:
            category = ErrorCategory.EXTERNAL
            retryable = True
            max_retries = 3
            backoff = 1.0
        elif exit_code == 130:  # SIGINT
            category = ErrorCategory.PERMANENT
            retryable = False
            max_retries = 0
            backoff = 0.0
        elif exit_code and exit_code > 128:  # Signal termination
            category = ErrorCategory.TRANSIENT
            retryable = True
            max_retries = 2
            backoff = 0.5
        else:
            category = ErrorCategory.EXTERNAL
            retryable = True
            max_retries = 3
            backoff = 1.0
        
        context = ErrorContext(
            category=category,
            retryable=retryable,
            max_retries=max_retries,
            backoff_seconds=backoff,
            error_code=str(exit_code) if exit_code else None
        )
        super().__init__(message, context=context, **kwargs)
        self.command = command
        self.exit_code = exit_code


class TaskGenerationError(AIAgentException):
    """Task generation error - retryable"""
    
    def __init__(self, message: str, instruction: Optional[str] = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.TRANSIENT,
            retryable=True,
            max_retries=2,
            backoff_seconds=1.0
        )
        super().__init__(message, context=context, **kwargs)
        self.instruction = instruction


class CommandParsingError(AIAgentException):
    """Command parsing error - not retryable (usually code issue)"""
    
    def __init__(self, message: str, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.PERMANENT,
            retryable=False,
            max_retries=0,
            backoff_seconds=0.0
        )
        super().__init__(message, context=context, **kwargs)


class VerificationError(AIAgentException):
    """Task verification error"""
    
    def __init__(self, message: str, task: Optional[str] = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.VALIDATION,
            retryable=True,
            max_retries=1,
            backoff_seconds=0.5
        )
        super().__init__(message, context=context, **kwargs)
        self.task = task


class TimeoutError(AIAgentException):
    """Timeout error - retryable with backoff"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.TIMEOUT,
            retryable=True,
            max_retries=3,
            backoff_seconds=5.0
        )
        super().__init__(message, context=context, **kwargs)
        self.timeout_seconds = timeout_seconds


class ResourceExhaustedError(AIAgentException):
    """Resource exhausted error - retryable with longer backoff"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, **kwargs):
        context = ErrorContext(
            category=ErrorCategory.RESOURCE,
            retryable=True,
            max_retries=2,
            backoff_seconds=30.0  # Longer backoff for resources
        )
        super().__init__(message, context=context, **kwargs)
        self.resource_type = resource_type


class ErrorHandler:
    """Centralized error handling with retry logic"""
    
    @staticmethod
    def classify_error(error: Exception, provider: Optional[str] = None, 
                      phase: Optional[str] = None) -> ErrorContext:
        """Classify an exception and return error context"""
        if isinstance(error, AIAgentException) and error.context:
            # Update context with current provider/phase
            error.context.provider = provider
            error.context.phase = phase
            return error.context
        
        # Default classification for unknown errors
        return ErrorContext(
            category=ErrorCategory.UNKNOWN,
            retryable=False,
            max_retries=0,
            backoff_seconds=0.0,
            provider=provider,
            phase=phase
        )
    
    @staticmethod
    def should_retry(error: Exception, attempt: int) -> bool:
        """Determine if error should be retried based on attempt count"""
        context = ErrorHandler.classify_error(error)
        
        if not context.retryable:
            return False
        
        if attempt >= context.max_retries:
            return False
        
        return True
    
    @staticmethod
    def get_retry_delay(error: Exception, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        context = ErrorHandler.classify_error(error)
        
        # Exponential backoff: backoff * (2 ^ attempt)
        delay = context.backoff_seconds * (2 ** attempt)
        
        # Cap at 5 minutes for rate limits, 30 seconds for others
        if context.category == ErrorCategory.RATE_LIMIT:
            return min(delay, 300.0)
        else:
            return min(delay, 30.0)
