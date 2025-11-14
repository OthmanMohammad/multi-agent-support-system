"""
Context caching layer.

Provides in-memory caching with optional Redis backend for enriched context.
Falls back to in-memory cache if Redis is not available.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
import structlog

from src.services.infrastructure.context_enrichment.models import EnrichedContext
from src.services.infrastructure.context_enrichment.exceptions import CacheError

logger = structlog.get_logger(__name__)


class InMemoryCache:
    """
    Simple in-memory cache implementation.

    This is used as a fallback when Redis is not available.
    Note: This cache is not shared across processes.
    """

    def __init__(self):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self._default_ttl = 300  # 5 minutes

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.utcnow() < expires_at:
                logger.debug("in_memory_cache_hit", key=key)
                return value
            else:
                # Expired - remove it
                del self._cache[key]
                logger.debug("in_memory_cache_expired", key=key)

        logger.debug("in_memory_cache_miss", key=key)
        return None

    async def set(self, key: str, value: Dict[str, Any], ttl: int = None):
        """Set value in cache with TTL"""
        ttl = ttl or self._default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = (value, expires_at)
        logger.debug("in_memory_cache_set", key=key, ttl=ttl)

    async def delete(self, key: str):
        """Delete value from cache"""
        if key in self._cache:
            del self._cache[key]
            logger.debug("in_memory_cache_deleted", key=key)

    async def clear(self):
        """Clear all cache"""
        self._cache.clear()
        logger.debug("in_memory_cache_cleared")

    def cleanup_expired(self):
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, expires_at) in self._cache.items()
            if now >= expires_at
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.debug("in_memory_cache_cleanup", expired_count=len(expired_keys))


class ContextCache:
    """
    Context caching layer with Redis backend and in-memory fallback.

    Attempts to use Redis if available, falls back to in-memory cache.
    """

    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            redis_url: Redis connection URL (optional)
            default_ttl: Default TTL in seconds (default: 5 minutes)
        """
        self.default_ttl = default_ttl
        self.redis_url = redis_url
        self.redis_client = None
        self.use_redis = False

        # Always have in-memory cache as fallback
        self.memory_cache = InMemoryCache()

        # Try to initialize Redis if URL provided
        if redis_url:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.use_redis = True
                logger.info("redis_cache_initialized", url=redis_url)
            except ImportError:
                logger.warning("redis_not_available_using_memory_cache")
            except Exception as e:
                logger.warning("redis_initialization_failed_using_memory_cache", error=str(e))
        else:
            logger.info("using_in_memory_cache")

    async def get(self, customer_id: str) -> Optional[EnrichedContext]:
        """
        Get enriched context from cache.

        Args:
            customer_id: Customer ID

        Returns:
            EnrichedContext if found, None otherwise
        """
        key = self._make_key(customer_id)

        # Try Redis first if available
        if self.use_redis and self.redis_client:
            try:
                data = await self.redis_client.get(key)
                if data:
                    logger.debug("redis_cache_hit", customer_id=customer_id)
                    return self._deserialize(data)
                logger.debug("redis_cache_miss", customer_id=customer_id)
            except Exception as e:
                logger.warning("redis_get_failed_falling_back_to_memory", error=str(e))
                # Fall through to memory cache

        # Fall back to memory cache
        data = await self.memory_cache.get(key)
        if data:
            return self._deserialize_dict(data)

        return None

    async def set(
        self,
        customer_id: str,
        context: EnrichedContext,
        ttl: Optional[int] = None
    ):
        """
        Set enriched context in cache.

        Args:
            customer_id: Customer ID
            context: EnrichedContext to cache
            ttl: TTL in seconds (optional, uses default if not provided)
        """
        key = self._make_key(customer_id)
        ttl = ttl or self.default_ttl

        # Try Redis first if available
        if self.use_redis and self.redis_client:
            try:
                serialized = self._serialize(context)
                await self.redis_client.setex(key, ttl, serialized)
                logger.debug("redis_cache_set", customer_id=customer_id, ttl=ttl)
                return  # Success - no need to use memory cache
            except Exception as e:
                logger.warning("redis_set_failed_using_memory_cache", error=str(e))
                # Fall through to memory cache

        # Use memory cache
        await self.memory_cache.set(key, context.to_dict(), ttl)

    async def invalidate(self, customer_id: str):
        """
        Invalidate cache for a customer.

        Args:
            customer_id: Customer ID
        """
        key = self._make_key(customer_id)

        # Invalidate from both Redis and memory cache
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.delete(key)
                logger.debug("redis_cache_invalidated", customer_id=customer_id)
            except Exception as e:
                logger.warning("redis_delete_failed", error=str(e))

        await self.memory_cache.delete(key)

    async def clear_all(self):
        """Clear all cached contexts"""
        if self.use_redis and self.redis_client:
            try:
                # Delete all keys matching our pattern
                pattern = "context:customer:*"
                async for key in self.redis_client.scan_iter(match=pattern):
                    await self.redis_client.delete(key)
                logger.info("redis_cache_cleared")
            except Exception as e:
                logger.warning("redis_clear_failed", error=str(e))

        await self.memory_cache.clear()

    def _make_key(self, customer_id: str) -> str:
        """Generate cache key"""
        return f"context:customer:{customer_id}"

    def _serialize(self, context: EnrichedContext) -> str:
        """Serialize EnrichedContext to JSON string"""
        try:
            # Convert to dict and serialize
            data = context.to_dict()
            return json.dumps(data, default=str)  # default=str handles datetime
        except Exception as e:
            logger.error("serialization_failed", error=str(e))
            raise CacheError(f"Failed to serialize context: {e}")

    def _deserialize(self, data: str) -> Optional[EnrichedContext]:
        """Deserialize JSON string to EnrichedContext"""
        try:
            context_dict = json.loads(data)
            return self._deserialize_dict(context_dict)
        except Exception as e:
            logger.error("deserialization_failed", error=str(e))
            return None

    def _deserialize_dict(self, data: Dict[str, Any]) -> Optional[EnrichedContext]:
        """Convert dictionary back to EnrichedContext"""
        try:
            # Import here to avoid circular import
            from src.services.infrastructure.context_enrichment.models import (
                CustomerIntelligence,
                EngagementMetrics,
                SupportHistory,
                SubscriptionDetails,
                AccountHealth,
                CompanyEnrichment,
                ProductStatus,
                EnrichedContext
            )

            # Parse datetime strings
            if isinstance(data.get("enriched_at"), str):
                data["enriched_at"] = datetime.fromisoformat(data["enriched_at"])

            # Reconstruct nested objects
            context = EnrichedContext(
                customer_intelligence=CustomerIntelligence(**data["customer_intelligence"]),
                engagement_metrics=EngagementMetrics(**data["engagement_metrics"]),
                support_history=SupportHistory(**data["support_history"]),
                subscription_details=SubscriptionDetails(**data["subscription_details"]),
                account_health=AccountHealth(**data["account_health"]),
                company_enrichment=CompanyEnrichment(**data["company_enrichment"]) if data.get("company_enrichment") else None,
                product_status=ProductStatus(**data["product_status"]),
                enriched_at=data["enriched_at"],
                cache_hit=True,  # Mark as cache hit
                enrichment_latency_ms=data.get("enrichment_latency_ms", 0),
                providers_used=data.get("providers_used", [])
            )

            # Parse nested datetime objects
            if isinstance(context.customer_intelligence.customer_since, str):
                context.customer_intelligence.customer_since = datetime.fromisoformat(
                    context.customer_intelligence.customer_since
                )
            if isinstance(context.engagement_metrics.last_login, str):
                context.engagement_metrics.last_login = datetime.fromisoformat(
                    context.engagement_metrics.last_login
                )
            if isinstance(context.support_history.last_conversation, str):
                context.support_history.last_conversation = datetime.fromisoformat(
                    context.support_history.last_conversation
                )
            if isinstance(context.subscription_details.current_period_end, str):
                context.subscription_details.current_period_end = datetime.fromisoformat(
                    context.subscription_details.current_period_end
                )

            return context

        except Exception as e:
            logger.error("dict_to_context_failed", error=str(e))
            return None
