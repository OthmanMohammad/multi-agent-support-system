"""
Rate Limiting Middleware - Request rate limiting per user/IP

This middleware enforces rate limits based on user tier, API key, or IP address.
Uses Redis for distributed rate limiting with token bucket algorithm.
"""

import time

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.auth import RateLimiter
from src.api.auth.jwt import JWTManager
from src.core.config import get_settings
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)
settings = get_settings()


# =============================================================================
# RATE LIMIT TIERS
# =============================================================================

RATE_LIMITS = {
    # Free tier (default, by IP)
    "free": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 1000,
    },
    # Regular user
    "user": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000,
    },
    # Admin users
    "admin": {
        "requests_per_minute": 300,
        "requests_per_hour": 5000,
        "requests_per_day": 50000,
    },
    # Super admin (virtually unlimited)
    "super_admin": {
        "requests_per_minute": 1000,
        "requests_per_hour": 20000,
        "requests_per_day": 200000,
    },
    # API clients
    "api_client": {
        "requests_per_minute": 120,
        "requests_per_hour": 2000,
        "requests_per_day": 20000,
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_rate_limit_key(request: Request) -> tuple[str, str]:
    """
    Get rate limit key and tier for request.

    Priority:
    1. Authenticated user (from JWT token)
    2. API key
    3. IP address (fallback)

    Args:
        request: FastAPI request

    Returns:
        Tuple of (rate_limit_key, tier)
    """
    # Try to get user from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.replace("Bearer ", "")
            payload = JWTManager.verify_token(token)
            user_id = payload.get("sub")
            role = payload.get("role", "user")

            if user_id:
                # Map role to tier
                if role == "super_admin":
                    tier = "super_admin"
                elif role == "admin":
                    tier = "admin"
                elif role == "api_client":
                    tier = "api_client"
                else:
                    tier = "user"

                return f"user:{user_id}", tier
        except Exception:
            pass  # Invalid token, fall through to other methods

    # Try to get API key from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use key prefix as identifier
        prefix = api_key[:20] if len(api_key) >= 20 else api_key
        return f"apikey:{prefix}", "api_client"

    # Fallback to IP address
    client_ip = "unknown"
    if request.client:
        client_ip = request.client.host

    return f"ip:{client_ip}", "free"


def get_tier_limits(tier: str) -> dict:
    """
    Get rate limits for a tier.

    Args:
        tier: Rate limit tier

    Returns:
        Dict with rate limits
    """
    return RATE_LIMITS.get(tier, RATE_LIMITS["free"])


# =============================================================================
# RATE LIMIT MIDDLEWARE
# =============================================================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis token bucket algorithm.

    Features:
    - Per-user rate limiting (authenticated users)
    - Per-API-key rate limiting
    - Per-IP rate limiting (anonymous requests)
    - Tiered limits based on user role
    - Standard rate limit headers (X-RateLimit-*)
    - Configurable via settings
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with rate limit headers

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Skip rate limiting if disabled
        if not settings.redis.rate_limit_enabled:
            logger.debug("rate_limiting_disabled")
            return await call_next(request)

        # Skip rate limiting for health check and metrics
        if request.url.path in ["/api/health", "/health", "/", "/metrics"]:
            return await call_next(request)

        # Get rate limit key and tier
        rate_limit_key, tier = get_rate_limit_key(request)
        limits = get_tier_limits(tier)

        logger.debug("rate_limit_check", key=rate_limit_key, tier=tier, path=request.url.path)

        # Check minute limit (primary limit)
        allowed, current_count, remaining = await RateLimiter.check_rate_limit(
            key=f"{rate_limit_key}:minute",
            max_requests=limits["requests_per_minute"],
            window_seconds=60,
        )

        if not allowed:
            # Get reset time
            reset_time = await RateLimiter.get_reset_time(f"{rate_limit_key}:minute")

            logger.warning(
                "rate_limit_exceeded",
                key=rate_limit_key,
                tier=tier,
                path=request.url.path,
                current=current_count,
                limit=limits["requests_per_minute"],
                reset_in=reset_time,
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Maximum {limits['requests_per_minute']} requests per minute allowed.",
                    "tier": tier,
                    "limit": limits["requests_per_minute"],
                    "reset_in_seconds": reset_time or 60,
                },
                headers={
                    "X-RateLimit-Limit": str(limits["requests_per_minute"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + (reset_time or 60)),
                    "Retry-After": str(reset_time or 60),
                },
            )

        # Check hour limit (secondary limit)
        hour_allowed, hour_current, hour_remaining = await RateLimiter.check_rate_limit(
            key=f"{rate_limit_key}:hour",
            max_requests=limits["requests_per_hour"],
            window_seconds=3600,
        )

        if not hour_allowed:
            reset_time = await RateLimiter.get_reset_time(f"{rate_limit_key}:hour")

            logger.warning(
                "hourly_rate_limit_exceeded",
                key=rate_limit_key,
                tier=tier,
                current=hour_current,
                limit=limits["requests_per_hour"],
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Hourly rate limit exceeded",
                    "message": f"Too many requests. Maximum {limits['requests_per_hour']} requests per hour allowed.",
                    "tier": tier,
                    "limit": limits["requests_per_hour"],
                    "reset_in_seconds": reset_time or 3600,
                },
                headers={
                    "X-RateLimit-Limit-Hour": str(limits["requests_per_hour"]),
                    "X-RateLimit-Remaining-Hour": "0",
                    "Retry-After": str(reset_time or 3600),
                },
            )

        # Check daily limit (tertiary limit)
        day_allowed, day_current, day_remaining = await RateLimiter.check_rate_limit(
            key=f"{rate_limit_key}:day",
            max_requests=limits["requests_per_day"],
            window_seconds=86400,
        )

        if not day_allowed:
            reset_time = await RateLimiter.get_reset_time(f"{rate_limit_key}:day")

            logger.warning(
                "daily_rate_limit_exceeded",
                key=rate_limit_key,
                tier=tier,
                current=day_current,
                limit=limits["requests_per_day"],
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Daily rate limit exceeded",
                    "message": f"Too many requests. Maximum {limits['requests_per_day']} requests per day allowed.",
                    "tier": tier,
                    "limit": limits["requests_per_day"],
                    "reset_in_seconds": reset_time or 86400,
                },
                headers={
                    "X-RateLimit-Limit-Day": str(limits["requests_per_day"]),
                    "X-RateLimit-Remaining-Day": "0",
                    "Retry-After": str(reset_time or 86400),
                },
            )

        # Request allowed - process it
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limits["requests_per_minute"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        # Add hourly and daily limits
        response.headers["X-RateLimit-Limit-Hour"] = str(limits["requests_per_hour"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(hour_remaining)

        response.headers["X-RateLimit-Limit-Day"] = str(limits["requests_per_day"])
        response.headers["X-RateLimit-Remaining-Day"] = str(day_remaining)

        # Add tier information
        response.headers["X-RateLimit-Tier"] = tier

        return response
