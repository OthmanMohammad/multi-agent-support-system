"""
Exception Decorators - Convenient decorators for exception handling

These decorators provide clean, declarative exception handling:
- Automatic enrichment with context
- Structured logging of exceptions
- Sentry capture for errors
- Conversion to Result pattern (for workflow errors)

Use these decorators to eliminate boilerplate exception handling code.
"""

import functools
from typing import Callable, Optional, List, Type
import logging

from utils.exceptions.enrichment import enrich_exception, get_exception_context
from utils.logging.setup import get_logger

# Import for type hints only (avoid circular import)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.result import Result


def capture_exceptions(
    log_errors: bool = True,
    send_to_sentry: bool = True,
    enrich: bool = True,
    reraise: bool = True,
    log_level: str = "error",
) -> Callable:
    """
    Decorator to automatically handle exceptions with enrichment and logging
    
    This decorator:
    1. Enriches exceptions with context (correlation_id, etc.)
    2. Logs exceptions with structured data
    3. Sends to Sentry (if enabled)
    4. Re-raises (unless reraise=False)
    
    Works with both sync and async functions.
    
    Args:
        log_errors: Log exceptions when caught
        send_to_sentry: Send exceptions to Sentry
        enrich: Enrich exceptions with context
        reraise: Re-raise exception after handling (default: True)
        log_level: Logging level for exceptions (default: "error")
    
    Returns:
        Decorated function
    
    Example:
        @capture_exceptions(log_errors=True, send_to_sentry=True)
        async def risky_operation(user_id: str):
            # Any exception will be:
            # 1. Enriched with correlation_id
            # 2. Logged with structured data
            # 3. Sent to Sentry
            # 4. Re-raised
            await process_user(user_id)
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                # Enrich with context
                if enrich:
                    enrich_exception(exc)
                
                # Log the exception
                if log_errors:
                    context = get_exception_context(exc)
                    log_func = getattr(logger, log_level, logger.error)
                    log_func(
                        "exception_captured",
                        function=func.__name__,
                        **context,
                        exc_info=True
                    )
                
                # Send to Sentry
                if send_to_sentry:
                    try:
                        import sentry_sdk
                        from utils.monitoring.sentry_config import capture_exception as sentry_capture
                        sentry_capture(exc, function=func.__name__)
                    except Exception as sentry_err:
                        logger.warning(
                            "sentry_capture_failed",
                            error=str(sentry_err)
                        )
                
                # Re-raise or swallow
                if reraise:
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                # Same handling as async
                if enrich:
                    enrich_exception(exc)
                
                if log_errors:
                    context = get_exception_context(exc)
                    log_func = getattr(logger, log_level, logger.error)
                    log_func(
                        "exception_captured",
                        function=func.__name__,
                        **context,
                        exc_info=True
                    )
                
                if send_to_sentry:
                    try:
                        import sentry_sdk
                        from utils.monitoring.sentry_config import capture_exception as sentry_capture
                        sentry_capture(exc, function=func.__name__)
                    except Exception as sentry_err:
                        logger.warning(
                            "sentry_capture_failed",
                            error=str(sentry_err)
                        )
                
                if reraise:
                    raise
        
        # Return appropriate wrapper based on function type
        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_workflow_errors(
    default_status: str = "failed",
    capture_types: Optional[List[Type[Exception]]] = None,
) -> Callable:
    """
    Decorator to convert workflow exceptions to Result pattern
    
    Use this on workflow operations that should return Result[T]
    instead of raising exceptions. Catches WorkflowException and
    converts to Result.fail().
    
    Args:
        default_status: Default status for failed results
        capture_types: Exception types to capture (default: WorkflowException)
    
    Returns:
        Decorated function that returns Result
    
    Example:
        @handle_workflow_errors(default_status="failed")
        async def execute_workflow(message: str) -> Result[Dict]:
            # If WorkflowException raised, returns Result.fail()
            # instead of raising
            result = await workflow.execute(message)
            return Result.ok(result)
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        # Import here to avoid circular imports
        from workflow.exceptions import WorkflowException
        from core.result import Result
        from core.errors import InternalError
        
        # Default capture types
        types_to_capture = capture_types or [WorkflowException]
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except tuple(types_to_capture) as exc:
                # Enrich the exception
                enrich_exception(exc)
                
                # Log it
                context = get_exception_context(exc)
                logger.warning(
                    "workflow_error_caught",
                    function=func.__name__,
                    **context
                )
                
                # Convert to Result.fail()
                error = InternalError(
                    message=str(exc),
                    operation=func.__name__,
                    component="workflow"
                )
                return Result.fail(error)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(types_to_capture) as exc:
                enrich_exception(exc)
                
                context = get_exception_context(exc)
                logger.warning(
                    "workflow_error_caught",
                    function=func.__name__,
                    **context
                )
                
                error = InternalError(
                    message=str(exc),
                    operation=func.__name__,
                    component="workflow"
                )
                return Result.fail(error)
        
        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_exceptions(
    log_level: str = "error",
    include_context: bool = True,
) -> Callable:
    """
    Simple decorator to just log exceptions (doesn't capture or reraise)
    
    Use when you just want exceptions logged but don't need Sentry capture
    or enrichment.
    
    Args:
        log_level: Logging level (default: "error")
        include_context: Include exception context in log (default: True)
    
    Returns:
        Decorated function
    
    Example:
        @log_exceptions(log_level="warning")
        def might_fail():
            # Exception logged at warning level
            # Then re-raised normally
            risky_operation()
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                log_func = getattr(logger, log_level, logger.error)
                
                if include_context:
                    context = get_exception_context(exc)
                    log_func(
                        "exception_occurred",
                        function=func.__name__,
                        **context,
                        exc_info=True
                    )
                else:
                    log_func(
                        "exception_occurred",
                        function=func.__name__,
                        error=str(exc),
                        error_type=type(exc).__name__,
                        exc_info=True
                    )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                log_func = getattr(logger, log_level, logger.error)
                
                if include_context:
                    context = get_exception_context(exc)
                    log_func(
                        "exception_occurred",
                        function=func.__name__,
                        **context,
                        exc_info=True
                    )
                else:
                    log_func(
                        "exception_occurred",
                        function=func.__name__,
                        error=str(exc),
                        error_type=type(exc).__name__,
                        exc_info=True
                    )
                
                raise
        
        if functools.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator