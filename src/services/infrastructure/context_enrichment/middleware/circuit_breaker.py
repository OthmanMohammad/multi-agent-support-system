"""
Circuit breaker for context enrichment providers.

Prevents cascading failures by failing fast when a provider is unhealthy.
"""

from typing import Optional, Callable, Any
from datetime import datetime, timedelta, UTC
from enum import Enum
import asyncio
import structlog
from functools import wraps

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Tracks failures and opens circuit to prevent cascading failures.
    Automatically attempts recovery after timeout.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, fail fast
    - HALF_OPEN: Testing if service recovered

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        >>> async with breaker:
        ...     result = await unreliable_operation()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        name: str = "default"
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes in half-open before closing
            timeout: Seconds before attempting recovery
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection.

        Args:
            func: Async function to call
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        async with self._lock:
            # Check if should attempt recovery
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(
                        "circuit_breaker_half_open",
                        name=self.name,
                        timeout_elapsed=True
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

        # Attempt to call function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1

                if self._success_count >= self.success_threshold:
                    logger.info(
                        "circuit_breaker_closed",
                        name=self.name,
                        success_count=self._success_count
                    )
                    self._state = CircuitState.CLOSED
                    self._success_count = 0

    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now(UTC)

            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    "circuit_breaker_reopened",
                    name=self.name,
                    reason="failure_in_half_open"
                )
                self._state = CircuitState.OPEN
                self._success_count = 0

            elif self._failure_count >= self.failure_threshold:
                logger.warning(
                    "circuit_breaker_opened",
                    name=self.name,
                    failure_count=self._failure_count,
                    threshold=self.failure_threshold
                )
                self._state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if should attempt to close circuit"""
        if not self._last_failure_time:
            return True

        elapsed = datetime.now(UTC) - self._last_failure_time
        return elapsed.total_seconds() >= self.timeout

    async def reset(self):
        """Manually reset circuit breaker"""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info("circuit_breaker_reset", name=self.name)

    async def __aenter__(self):
        """Context manager entry"""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is None:
            await self._on_success()
        else:
            await self._on_failure()
        return False


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open"""
    pass


# Global circuit breakers registry
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout: int = 60
) -> CircuitBreaker:
    """
    Get or create a circuit breaker.

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening
        timeout: Recovery timeout in seconds

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            failure_threshold=failure_threshold,
            timeout=timeout,
            name=name
        )
    return _circuit_breakers[name]


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    timeout: int = 60
):
    """
    Decorator to apply circuit breaker to async functions.

    Args:
        name: Circuit breaker name (defaults to function name)
        failure_threshold: Failures before opening circuit
        timeout: Recovery timeout in seconds

    Example:
        >>> @circuit_breaker(failure_threshold=3, timeout=30)
        ... async def fetch_data(customer_id: str):
        ...     return await external_api_call(customer_id)
    """
    def decorator(func):
        breaker_name = name or func.__name__
        breaker = get_circuit_breaker(breaker_name, failure_threshold, timeout)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        return wrapper
    return decorator
