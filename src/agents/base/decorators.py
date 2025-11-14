"""
Agent decorators for common functionality.

This module provides decorators for agent methods to add
cross-cutting concerns like logging, error handling, timing, etc.
"""

import time
import functools
from typing import Callable, Any
import structlog

logger = structlog.get_logger(__name__)


def log_agent_action(action_name: str):
    """
    Decorator to log agent actions with timing.

    Args:
        action_name: Name of the action being performed

    Example:
        @log_agent_action("intent_classification")
        async def classify_intent(self, message: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> Any:
            agent_name = getattr(self.config, 'name', 'unknown') if hasattr(self, 'config') else 'unknown'
            log = logger.bind(agent=agent_name, action=action_name)

            log.info(f"{action_name}_started")
            start_time = time.time()

            try:
                result = await func(self, *args, **kwargs)
                duration = time.time() - start_time

                log.info(
                    f"{action_name}_completed",
                    duration_ms=round(duration * 1000, 2)
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                log.error(
                    f"{action_name}_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=round(duration * 1000, 2)
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> Any:
            agent_name = getattr(self.config, 'name', 'unknown') if hasattr(self, 'config') else 'unknown'
            log = logger.bind(agent=agent_name, action=action_name)

            log.info(f"{action_name}_started")
            start_time = time.time()

            try:
                result = func(self, *args, **kwargs)
                duration = time.time() - start_time

                log.info(
                    f"{action_name}_completed",
                    duration_ms=round(duration * 1000, 2)
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                log.error(
                    f"{action_name}_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=round(duration * 1000, 2)
                )
                raise

        # Return appropriate wrapper based on whether function is async
        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry agent operations on failure.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Example:
        @retry_on_error(max_retries=3, delay=2.0)
        async def call_external_api(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            "retry_attempt",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e)
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "max_retries_exceeded",
                            max_retries=max_retries,
                            error=str(e)
                        )

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            "retry_attempt",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e)
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "max_retries_exceeded",
                            max_retries=max_retries,
                            error=str(e)
                        )

            raise last_exception

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def validate_state(required_fields: list):
    """
    Decorator to validate state before processing.

    Args:
        required_fields: List of required state fields

    Example:
        @validate_state(["current_message", "customer_id"])
        async def process(self, state: AgentState):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(self, state, *args, **kwargs) -> Any:
            missing_fields = [
                field for field in required_fields
                if field not in state or state[field] is None
            ]

            if missing_fields:
                raise ValueError(
                    f"Missing required state fields: {', '.join(missing_fields)}"
                )

            return await func(self, state, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(self, state, *args, **kwargs) -> Any:
            missing_fields = [
                field for field in required_fields
                if field not in state or state[field] is None
            ]

            if missing_fields:
                raise ValueError(
                    f"Missing required state fields: {', '.join(missing_fields)}"
                )

            return func(self, state, *args, **kwargs)

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def cache_result(ttl_seconds: int = 300):
    """
    Decorator to cache agent method results.

    Args:
        ttl_seconds: Time to live for cached results

    Example:
        @cache_result(ttl_seconds=600)
        async def get_customer_plan(self, customer_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        cache = {}

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> Any:
            # Create cache key from args
            cache_key = str(args) + str(kwargs)
            current_time = time.time()

            # Check cache
            if cache_key in cache:
                cached_result, cached_time = cache[cache_key]
                if current_time - cached_time < ttl_seconds:
                    logger.debug("cache_hit", cache_key=cache_key[:50])
                    return cached_result

            # Call function and cache result
            result = await func(self, *args, **kwargs)
            cache[cache_key] = (result, current_time)

            # Clean old cache entries
            cache_keys_to_remove = [
                k for k, (_, t) in cache.items()
                if current_time - t >= ttl_seconds
            ]
            for k in cache_keys_to_remove:
                del cache[k]

            return result

        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> Any:
            cache_key = str(args) + str(kwargs)
            current_time = time.time()

            if cache_key in cache:
                cached_result, cached_time = cache[cache_key]
                if current_time - cached_time < ttl_seconds:
                    logger.debug("cache_hit", cache_key=cache_key[:50])
                    return cached_result

            result = func(self, *args, **kwargs)
            cache[cache_key] = (result, current_time)

            cache_keys_to_remove = [
                k for k, (_, t) in cache.items()
                if current_time - t >= ttl_seconds
            ]
            for k in cache_keys_to_remove:
                del cache[k]

            return result

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Import asyncio for async sleep
import asyncio
