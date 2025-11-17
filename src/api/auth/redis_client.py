"""
Redis Client for Authentication

Provides Redis client for:
- Token blacklist (revoked tokens)
- Rate limiting
- Session management
- Caching

Single global connection pool for performance.
"""

from typing import Optional
import redis.asyncio as redis
from redis.asyncio import Redis

from src.core.config import get_settings
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)
settings = get_settings()


# Global Redis client instance
_redis_client: Optional[Redis] = None


async def get_redis_client() -> Optional[Redis]:
    """
    Get or create Redis client connection.

    Uses connection pooling for performance.
    Returns existing client if already initialized.
    Returns None if Redis is disabled in settings.

    Returns:
        Redis async client or None if disabled

    Example:
        >>> client = await get_redis_client()
        >>> if client:
        ...     await client.set("key", "value")
        ...     value = await client.get("key")
    """
    global _redis_client

    # If Redis is disabled, return None
    if not settings.redis.enabled:
        logger.info("redis_disabled", message="Redis is disabled in configuration")
        return None

    if _redis_client is None:
        logger.info("redis_client_initializing", url=settings.redis.url)

        # Create Redis client with connection pooling
        _redis_client = redis.from_url(
            settings.redis.url,
            password=settings.redis.password,
            max_connections=settings.redis.max_connections,
            socket_timeout=settings.redis.socket_timeout,
            socket_connect_timeout=settings.redis.socket_connect_timeout,
            decode_responses=settings.redis.decode_responses,
        )

        # Test connection
        try:
            await _redis_client.ping()
            logger.info("redis_client_connected_successfully")
        except Exception as e:
            logger.error(
                "redis_client_connection_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    return _redis_client


async def close_redis_client() -> None:
    """
    Close Redis client connection.

    Should be called on application shutdown.

    Example:
        >>> await close_redis_client()
    """
    global _redis_client

    if _redis_client is not None:
        logger.info("redis_client_closing")
        await _redis_client.close()
        _redis_client = None
        logger.info("redis_client_closed")


class TokenBlacklist:
    """
    Token blacklist for JWT revocation.

    When a user logs out or a token is compromised, add the token's JTI
    (JWT ID) to the blacklist to prevent further use.
    """

    @staticmethod
    async def add_token(jti: str, ttl_seconds: int) -> None:
        """
        Add token to blacklist.

        Args:
            jti: JWT ID (from token payload)
            ttl_seconds: Time to live (match token expiration)

        Example:
            >>> await TokenBlacklist.add_token("token-id-123", ttl_seconds=3600)
        """
        if not settings.redis.token_blacklist_enabled:
            logger.debug("token_blacklist_disabled")
            return

        client = await get_redis_client()
        if client is None:
            logger.warning("token_blacklist_unavailable", message="Redis not available")
            return

        key = f"blacklist:token:{jti}"

        await client.setex(key, ttl_seconds, "1")

        logger.info("token_blacklisted", jti=jti, ttl_seconds=ttl_seconds)

    @staticmethod
    async def is_blacklisted(jti: str) -> bool:
        """
        Check if token is blacklisted.

        Args:
            jti: JWT ID (from token payload)

        Returns:
            True if blacklisted, False otherwise

        Example:
            >>> if await TokenBlacklist.is_blacklisted("token-id-123"):
            ...     raise HTTPException(401, "Token has been revoked")
        """
        if not settings.redis.token_blacklist_enabled:
            return False

        client = await get_redis_client()
        if client is None:
            # If Redis is unavailable, we cannot check blacklist
            # Return False to allow token (fail open for availability)
            return False

        key = f"blacklist:token:{jti}"

        exists = await client.exists(key)

        if exists:
            logger.warning("blacklisted_token_used", jti=jti)

        return bool(exists)


class RateLimiter:
    """
    Rate limiting using token bucket algorithm.

    Tracks request counts per key (user ID, API key, IP address)
    with sliding window implementation.
    """

    @staticmethod
    async def check_rate_limit(
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Uses sliding window counter algorithm.

        Args:
            key: Rate limit key (e.g., "user:123" or "ip:1.2.3.4")
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, current_count, remaining)

        Example:
            >>> allowed, current, remaining = await RateLimiter.check_rate_limit(
            ...     "user:123",
            ...     max_requests=100,
            ...     window_seconds=60
            ... )
            >>> if not allowed:
            ...     raise HTTPException(429, f"Rate limit exceeded. {remaining} requests remaining")
        """
        if not settings.redis.rate_limit_enabled:
            return True, 0, max_requests

        client = await get_redis_client()
        if client is None:
            # If Redis is unavailable, allow all requests (fail open)
            logger.warning("rate_limit_unavailable", message="Redis not available")
            return True, 0, max_requests

        redis_key = f"ratelimit:{key}"

        # Increment counter
        current_count = await client.incr(redis_key)

        # Set expiration on first request
        if current_count == 1:
            await client.expire(redis_key, window_seconds)

        # Check if limit exceeded
        remaining = max(0, max_requests - current_count)
        is_allowed = current_count <= max_requests

        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                key=key,
                current_count=current_count,
                max_requests=max_requests
            )

        return is_allowed, current_count, remaining

    @staticmethod
    async def reset_rate_limit(key: str) -> None:
        """
        Reset rate limit for a key.

        Args:
            key: Rate limit key

        Example:
            >>> await RateLimiter.reset_rate_limit("user:123")
        """
        client = await get_redis_client()
        if client is None:
            return

        redis_key = f"ratelimit:{key}"
        await client.delete(redis_key)
        logger.info("rate_limit_reset", key=key)

    @staticmethod
    async def get_reset_time(key: str) -> Optional[int]:
        """
        Get time until rate limit resets.

        Args:
            key: Rate limit key

        Returns:
            Seconds until reset, or None if no limit set

        Example:
            >>> reset_time = await RateLimiter.get_reset_time("user:123")
            >>> print(f"Rate limit resets in {reset_time} seconds")
        """
        client = await get_redis_client()
        if client is None:
            return None

        redis_key = f"ratelimit:{key}"
        ttl = await client.ttl(redis_key)
        return ttl if ttl > 0 else None


class SessionCache:
    """
    Session caching for frequently accessed data.

    Cache user sessions, permissions, and other frequently accessed data
    to reduce database queries.
    """

    @staticmethod
    async def set_session(
        session_id: str,
        data: str,
        ttl_seconds: int = 3600
    ) -> None:
        """
        Store session data.

        Args:
            session_id: Session identifier
            data: Session data (as JSON string)
            ttl_seconds: Time to live (default: 1 hour)

        Example:
            >>> import json
            >>> session_data = json.dumps({"user_id": "123", "role": "admin"})
            >>> await SessionCache.set_session("session-abc", session_data)
        """
        client = await get_redis_client()
        if client is None:
            logger.warning("session_cache_unavailable", message="Redis not available")
            return

        key = f"session:{session_id}"
        await client.setex(key, ttl_seconds, data)
        logger.debug("session_cached", session_id=session_id, ttl=ttl_seconds)

    @staticmethod
    async def get_session(session_id: str) -> Optional[str]:
        """
        Retrieve session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data as JSON string, or None if not found

        Example:
            >>> import json
            >>> data = await SessionCache.get_session("session-abc")
            >>> if data:
            ...     session = json.loads(data)
        """
        client = await get_redis_client()
        if client is None:
            return None

        key = f"session:{session_id}"
        data = await client.get(key)
        return data

    @staticmethod
    async def delete_session(session_id: str) -> None:
        """
        Delete session data.

        Args:
            session_id: Session identifier

        Example:
            >>> await SessionCache.delete_session("session-abc")
        """
        client = await get_redis_client()
        if client is None:
            return

        key = f"session:{session_id}"
        await client.delete(key)
        logger.debug("session_deleted", session_id=session_id)
