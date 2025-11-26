"""
Caching Infrastructure Service - Redis caching operations

This service wraps Redis operations with Result-based error handling.
Provides caching, cache-aside pattern, and error resilience.

Pure infrastructure - no business logic.
"""

from collections.abc import Callable
from datetime import UTC, timedelta
from typing import Any

from src.core.errors import ExternalServiceError
from src.core.result import Result


class CachingService:
    """
    Infrastructure service for caching operations

    Wraps Redis with Result pattern and error handling.

    Responsibilities:
    - Get/set cache values
    - Cache invalidation
    - Cache-aside pattern implementation
    - TTL management

    NOT responsible for:
    - Deciding what to cache (caller's responsibility)
    - Determining cache keys (caller's responsibility)
    - Cache warming strategies (domain/application logic)

    NOTE: Currently a stub implementation. Integrate with Redis
    or use in-memory dict for local development.
    """

    def __init__(self, redis_client=None, use_memory_cache: bool = True):
        """
        Initialize caching service

        Args:
            redis_client: Redis client instance (optional)
            use_memory_cache: Use in-memory dict if Redis unavailable
        """
        self.redis_client = redis_client
        self.use_memory_cache = use_memory_cache

        # Fallback in-memory cache (not production-ready)
        if use_memory_cache and not redis_client:
            self._memory_cache: dict = {}
            self._cache_ttls: dict = {}
            print("Warning: Using in-memory cache (not suitable for production)")

    def is_available(self) -> bool:
        """
        Check if caching service is available

        Returns:
            True if Redis or memory cache is available
        """
        return self.redis_client is not None or self.use_memory_cache

    async def get(self, key: str) -> Result[Any | None]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Result with cached value or None if not found
        """
        if not self.is_available():
            return Result.fail(
                ExternalServiceError(
                    message="Cache service is not available",
                    service="Redis",
                    operation="get",
                    is_retryable=True,
                )
            )

        try:
            if self.redis_client:
                # TODO: Implement Redis get
                # value = await self.redis_client.get(key)
                # if value:
                #     return Result.ok(json.loads(value))
                # return Result.ok(None)
                return Result.ok(None)

            elif self.use_memory_cache:
                # Memory cache implementation
                if key in self._memory_cache:
                    # Check TTL
                    if key in self._cache_ttls:
                        from datetime import datetime

                        if datetime.now(UTC) > self._cache_ttls[key]:
                            # Expired
                            del self._memory_cache[key]
                            del self._cache_ttls[key]
                            return Result.ok(None)

                    return Result.ok(self._memory_cache[key])

                return Result.ok(None)

            return Result.ok(None)

        except Exception as e:
            # Cache errors should not break application
            print(f"Cache get error: {e}")
            return Result.ok(None)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> Result[None]:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (optional)

        Returns:
            Result with None on success
        """
        if not self.is_available():
            return Result.fail(
                ExternalServiceError(
                    message="Cache service is not available",
                    service="Redis",
                    operation="set",
                    is_retryable=True,
                )
            )

        try:
            if self.redis_client:
                # TODO: Implement Redis set
                # serialized = json.dumps(value)
                # if ttl:
                #     await self.redis_client.setex(key, ttl, serialized)
                # else:
                #     await self.redis_client.set(key, serialized)
                pass

            elif self.use_memory_cache:
                # Memory cache implementation
                self._memory_cache[key] = value

                if ttl:
                    from datetime import datetime

                    expiry = datetime.now(UTC) + timedelta(seconds=ttl)
                    self._cache_ttls[key] = expiry

            return Result.ok(None)

        except Exception as e:
            # Cache errors should not break application
            print(f"Cache set error: {e}")
            return Result.ok(None)

    async def delete(self, key: str) -> Result[None]:
        """
        Delete value from cache (invalidation)

        Args:
            key: Cache key to delete

        Returns:
            Result with None on success
        """
        if not self.is_available():
            return Result.ok(None)  # Silently succeed if cache unavailable

        try:
            if self.redis_client:
                # TODO: Implement Redis delete
                # await self.redis_client.delete(key)
                pass

            elif self.use_memory_cache:
                self._memory_cache.pop(key, None)
                self._cache_ttls.pop(key, None)

            return Result.ok(None)

        except Exception as e:
            print(f"Cache delete error: {e}")
            return Result.ok(None)

    async def exists(self, key: str) -> Result[bool]:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            Result with True if exists, False otherwise
        """
        if not self.is_available():
            return Result.ok(False)

        try:
            if self.redis_client:
                # TODO: Implement Redis exists
                # exists = await self.redis_client.exists(key)
                # return Result.ok(bool(exists))
                return Result.ok(False)

            elif self.use_memory_cache:
                # Check if key exists and not expired
                if key not in self._memory_cache:
                    return Result.ok(False)

                # Check TTL
                if key in self._cache_ttls:
                    from datetime import datetime

                    if datetime.now(UTC) > self._cache_ttls[key]:
                        # Expired
                        del self._memory_cache[key]
                        del self._cache_ttls[key]
                        return Result.ok(False)

                return Result.ok(True)

            return Result.ok(False)

        except Exception as e:
            print(f"Cache exists error: {e}")
            return Result.ok(False)

    async def get_or_compute(
        self, key: str, compute_func: Callable[[], Any], ttl: int | None = None
    ) -> Result[Any]:
        """
        Cache-aside pattern: Get from cache or compute and cache

        This is the most common caching pattern:
        1. Try to get from cache
        2. If miss, compute the value
        3. Store in cache
        4. Return value

        Args:
            key: Cache key
            compute_func: Function to compute value if cache miss
            ttl: Time-to-live in seconds (optional)

        Returns:
            Result with computed/cached value
        """
        # Try to get from cache
        cached_result = await self.get(key)

        if cached_result.is_success and cached_result.value is not None:
            # Cache hit
            return Result.ok(cached_result.value)

        # Cache miss - compute value
        try:
            value = compute_func()

            # Store in cache (fire and forget)
            await self.set(key, value, ttl)

            return Result.ok(value)

        except Exception as e:
            return Result.fail(
                ExternalServiceError(
                    message=f"Failed to compute value: {e!s}",
                    service="CachingService",
                    operation="get_or_compute",
                    is_retryable=True,
                )
            )

    async def invalidate_pattern(self, pattern: str) -> Result[int]:
        """
        Invalidate all keys matching pattern

        Useful for invalidating related cache entries.

        Args:
            pattern: Redis pattern (e.g., "user:*")

        Returns:
            Result with count of invalidated keys
        """
        if not self.is_available():
            return Result.ok(0)

        try:
            if self.redis_client:
                # TODO: Implement Redis pattern deletion
                # keys = await self.redis_client.keys(pattern)
                # if keys:
                #     await self.redis_client.delete(*keys)
                # return Result.ok(len(keys))
                return Result.ok(0)

            elif self.use_memory_cache:
                # Simple pattern matching for memory cache
                import fnmatch

                matched_keys = [k for k in self._memory_cache if fnmatch.fnmatch(k, pattern)]

                for key in matched_keys:
                    del self._memory_cache[key]
                    self._cache_ttls.pop(key, None)

                return Result.ok(len(matched_keys))

            return Result.ok(0)

        except Exception as e:
            print(f"Cache invalidate pattern error: {e}")
            return Result.ok(0)

    async def clear_all(self) -> Result[None]:
        """
        Clear all cache entries (use with caution!)

        Returns:
            Result with None on success
        """
        if not self.is_available():
            return Result.ok(None)

        try:
            if self.redis_client:
                # TODO: Implement Redis flush
                # await self.redis_client.flushdb()
                pass

            elif self.use_memory_cache:
                self._memory_cache.clear()
                self._cache_ttls.clear()

            return Result.ok(None)

        except Exception as e:
            print(f"Cache clear error: {e}")
            return Result.ok(None)
