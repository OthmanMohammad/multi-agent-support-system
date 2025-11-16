"""
Rate limiter for context enrichment requests.

Prevents abuse and ensures fair resource allocation.
"""

from typing import Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import deque
import asyncio
import structlog
from functools import wraps

logger = structlog.get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.

    Limits requests per customer to prevent abuse and ensure fair usage.

    Example:
        >>> limiter = RateLimiter(max_requests=100, period_seconds=60)
        >>> await limiter.acquire("customer_123")
    """

    def __init__(
        self,
        max_requests: int = 100,
        period_seconds: int = 60
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in period
            period_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self._buckets: Dict[str, deque] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def acquire(self, key: str) -> bool:
        """
        Try to acquire a token for the given key.

        Args:
            key: Rate limit key (e.g., customer ID)

        Returns:
            True if request allowed, False if rate limited

        Example:
            >>> allowed = await limiter.acquire("customer_123")
            >>> if not allowed:
            ...     raise RateLimitExceeded()
        """
        # Get or create lock for this key
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            now = datetime.utcnow()

            # Initialize bucket if needed
            if key not in self._buckets:
                self._buckets[key] = deque()

            bucket = self._buckets[key]

            # Remove expired timestamps
            cutoff = now - timedelta(seconds=self.period_seconds)
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            # Check if under limit
            if len(bucket) < self.max_requests:
                bucket.append(now)
                logger.debug(
                    "rate_limit_allowed",
                    key=key,
                    current_requests=len(bucket),
                    max_requests=self.max_requests
                )
                return True
            else:
                logger.warning(
                    "rate_limit_exceeded",
                    key=key,
                    current_requests=len(bucket),
                    max_requests=self.max_requests
                )
                return False

    def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.

        Args:
            key: Rate limit key to reset
        """
        if key in self._buckets:
            self._buckets[key].clear()
            logger.info("rate_limit_reset", key=key)

    def get_remaining(self, key: str) -> int:
        """
        Get remaining requests for a key.

        Args:
            key: Rate limit key

        Returns:
            Number of remaining requests
        """
        if key not in self._buckets:
            return self.max_requests

        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.period_seconds)

        bucket = self._buckets[key]

        # Count non-expired requests
        valid_requests = sum(1 for ts in bucket if ts >= cutoff)

        return max(0, self.max_requests - valid_requests)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(
    max_requests: int = 100,
    period_seconds: int = 60
) -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Args:
        max_requests: Maximum requests per period
        period_seconds: Period in seconds

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_requests, period_seconds)
    return _rate_limiter


def rate_limit(
    max_requests: int = 100,
    period_seconds: int = 60,
    key_func: Optional[Callable] = None
):
    """
    Decorator to apply rate limiting to async functions.

    Args:
        max_requests: Maximum requests per period
        period_seconds: Period in seconds
        key_func: Function to extract rate limit key from args

    Example:
        >>> @rate_limit(max_requests=10, period_seconds=60)
        ... async def fetch_data(customer_id: str):
        ...     return await expensive_operation(customer_id)
    """
    def decorator(func):
        limiter = RateLimiter(max_requests, period_seconds)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            elif args:
                key = str(args[0])  # Use first argument as key
            else:
                key = "global"

            # Check rate limit
            allowed = await limiter.acquire(key)
            if not allowed:
                raise RateLimitExceeded(
                    f"Rate limit exceeded for key: {key}. "
                    f"Max {max_requests} requests per {period_seconds}s"
                )

            # Call original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass
