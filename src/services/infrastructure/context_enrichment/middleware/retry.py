"""
Retry logic for context enrichment operations.

Automatically retries failed operations with exponential backoff.
"""

from typing import Optional, Callable, Any, Type, Tuple
import asyncio
import structlog
from functools import wraps
from dataclasses import dataclass

logger = structlog.get_logger(__name__)


@dataclass
class RetryPolicy:
    """
    Retry policy configuration.

    Attributes:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Multiplier for exponential backoff
        jitter: Add randomness to prevent thundering herd
    """
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


async def with_retry(
    func: Callable,
    *args,
    policy: Optional[RetryPolicy] = None,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs
) -> Any:
    """
    Execute async function with retry logic.

    Args:
        func: Async function to execute
        *args: Function arguments
        policy: Retry policy (uses default if None)
        retry_exceptions: Exception types to retry
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted

    Example:
        >>> result = await with_retry(
        ...     fetch_data,
        ...     customer_id,
        ...     policy=RetryPolicy(max_attempts=5),
        ...     retry_exceptions=(TimeoutError, ConnectionError)
        ... )
    """
    if policy is None:
        policy = RetryPolicy()

    last_exception = None

    for attempt in range(policy.max_attempts):
        try:
            result = await func(*args, **kwargs)

            if attempt > 0:
                logger.info(
                    "retry_succeeded",
                    function=func.__name__,
                    attempt=attempt + 1,
                    max_attempts=policy.max_attempts
                )

            return result

        except retry_exceptions as e:
            last_exception = e

            if attempt + 1 >= policy.max_attempts:
                logger.error(
                    "retry_exhausted",
                    function=func.__name__,
                    attempts=attempt + 1,
                    error=str(e)
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(
                policy.initial_delay * (policy.exponential_base ** attempt),
                policy.max_delay
            )

            # Add jitter if enabled
            if policy.jitter:
                import random
                delay = delay * (0.5 + random.random())

            logger.warning(
                "retrying_operation",
                function=func.__name__,
                attempt=attempt + 1,
                max_attempts=policy.max_attempts,
                delay=delay,
                error=str(e)
            )

            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to add retry logic to async functions.

    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Multiplier for exponential backoff
        jitter: Add randomness to delays
        retry_exceptions: Exception types to retry

    Example:
        >>> @retry(max_attempts=5, retry_exceptions=(TimeoutError,))
        ... async def fetch_external_data(customer_id: str):
        ...     return await external_api_call(customer_id)
    """
    policy = RetryPolicy(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter
    )

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await with_retry(
                func,
                *args,
                policy=policy,
                retry_exceptions=retry_exceptions,
                **kwargs
            )
        return wrapper
    return decorator


class RetryableError(Exception):
    """Base class for retryable errors"""
    pass


class NonRetryableError(Exception):
    """Base class for non-retryable errors"""
    pass
