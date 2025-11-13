"""
Logging Decorators - Convenient decorators for common logging patterns

These decorators make it easy to add logging to functions without
manual log calls. Useful for Phase 5 migration.

Decorators:
- @log_execution: Log function entry/exit with timing
- @log_errors: Catch and log exceptions
- @log_result: Log function return value
"""

import time
import functools
from typing import Callable, Any
from src.utils.logging.setup import get_logger


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution with timing
    
    Logs when function starts and completes, including execution time.
    Works with both sync and async functions.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        @log_execution
        async def process_message(message: str):
            # ... processing ...
            return result
        
        # Logs:
        # function_started function=process_message
        # function_completed function=process_message duration_ms=42
    """
    logger = get_logger(func.__module__)
    
    if functools.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            logger.info(
                "function_started",
                function=func.__name__,
            )
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.info(
                    "function_completed",
                    function=func.__name__,
                    duration_ms=duration_ms,
                )
                
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.error(
                    "function_failed",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    error=str(e),
                )
                raise
        
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            logger.info(
                "function_started",
                function=func.__name__,
            )
            
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.info(
                    "function_completed",
                    function=func.__name__,
                    duration_ms=duration_ms,
                )
                
                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                
                logger.error(
                    "function_failed",
                    function=func.__name__,
                    duration_ms=duration_ms,
                    error=str(e),
                )
                raise
        
        return sync_wrapper


def log_errors(func: Callable) -> Callable:
    """
    Decorator to catch and log exceptions
    
    Logs exceptions with full context but re-raises them.
    Use this when you want error logging without handling.
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        @log_errors
        async def risky_operation():
            # ... code that might raise ...
            pass
        
        # Logs on exception:
        # exception_occurred function=risky_operation error=... exc_info=...
    """
    logger = get_logger(func.__module__)
    
    if functools.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    "exception_occurred",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                raise
        
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    "exception_occurred",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                raise
        
        return sync_wrapper


def log_result(func: Callable) -> Callable:
    """
    Decorator to log function return value
    
    Useful for debugging data flow.
    WARNING: Don't use on functions returning sensitive data!
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    
    Example:
        @log_result
        def calculate_total(items: list) -> float:
            return sum(item.price for item in items)
        
        # Logs:
        # function_result function=calculate_total result=123.45
    """
    logger = get_logger(func.__module__)
    
    if functools.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            logger.debug(
                "function_result",
                function=func.__name__,
                result=str(result)[:200],  # Truncate long results
            )
            
            return result
        
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            logger.debug(
                "function_result",
                function=func.__name__,
                result=str(result)[:200],  # Truncate long results
            )
            
            return result
        
        return sync_wrapper