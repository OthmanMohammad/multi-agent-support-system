"""
Enhanced two-tier caching for context enrichment.

Implements L1 (in-memory LRU) + L2 (Redis) caching strategy with:
- Sub-10ms L1 cache latency
- LRU eviction policy for L1
- Automatic cache warming
- Cache statistics and monitoring
- Graceful fallback when Redis unavailable
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import OrderedDict
import asyncio
import json
import pickle
import structlog
from dataclasses import dataclass, asdict

from src.services.infrastructure.context_enrichment.types import EnrichedContext, AgentType
from src.core.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass
class CacheStats:
    """Cache statistics"""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l1_evictions: int = 0
    l1_size: int = 0
    l2_size: int = 0
    total_sets: int = 0
    total_gets: int = 0

    @property
    def l1_hit_rate(self) -> float:
        """Calculate L1 hit rate"""
        total = self.l1_hits + self.l1_misses
        return (self.l1_hits / total * 100) if total > 0 else 0.0

    @property
    def l2_hit_rate(self) -> float:
        """Calculate L2 hit rate"""
        total = self.l2_hits + self.l2_misses
        return (self.l2_hits / total * 100) if total > 0 else 0.0

    @property
    def overall_hit_rate(self) -> float:
        """Calculate overall hit rate"""
        total_hits = self.l1_hits + self.l2_hits
        total = self.total_gets
        return (total_hits / total * 100) if total > 0 else 0.0


class LRUCache:
    """
    Thread-safe LRU cache implementation.

    Uses OrderedDict to maintain insertion/access order.
    Automatically evicts least recently used items when capacity reached.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self._lock = asyncio.Lock()
        self._evictions = 0

    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                return None

            value, expires_at = self._cache[key]

            # Check expiration
            if datetime.utcnow() >= expires_at:
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: Any, ttl: int):
        """
        Set item in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        async with self._lock:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)

            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = (value, expires_at)
                self._cache.move_to_end(key)
                return

            # Check if we need to evict
            if len(self._cache) >= self.max_size:
                # Remove oldest item (first in OrderedDict)
                self._cache.popitem(last=False)
                self._evictions += 1

            # Add new item
            self._cache[key] = (value, expires_at)

    async def delete(self, key: str):
        """Delete item from cache"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]

    async def clear(self):
        """Clear all items"""
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        """Get current cache size"""
        return len(self._cache)

    async def evictions(self) -> int:
        """Get number of evictions"""
        return self._evictions

    async def cleanup_expired(self):
        """Remove all expired entries"""
        async with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, (_, expires_at) in self._cache.items()
                if now >= expires_at
            ]
            for key in expired_keys:
                del self._cache[key]


class ContextCache:
    """
    Two-tier context cache with L1 (in-memory LRU) + L2 (Redis).

    Features:
    - L1: In-memory LRU cache for sub-10ms access
    - L2: Redis cache for distributed caching
    - Automatic promotion from L2 to L1 on cache hit
    - Graceful fallback when Redis unavailable
    - Comprehensive cache statistics

    Cache flow:
    1. Check L1 ??? if hit, return (sub-10ms)
    2. Check L2 ??? if hit, promote to L1 and return (~20ms)
    3. Cache miss ??? fetch from providers, store in both tiers

    Example:
        >>> cache = ContextCache()
        >>> await cache.set("key", context)
        >>> context = await cache.get("key")
    """

    def __init__(
        self,
        l1_max_size: Optional[int] = None,
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None,
        redis_url: Optional[str] = None,
        enable_l1: bool = True,
        enable_l2: bool = True
    ):
        """
        Initialize two-tier cache.

        Args:
            l1_max_size: Max items in L1 cache
            l1_ttl: L1 TTL in seconds
            l2_ttl: L2 TTL in seconds
            redis_url: Redis connection URL
            enable_l1: Enable L1 cache
            enable_l2: Enable L2 cache
        """
        self.settings = get_settings()
        config = self.settings.context_enrichment

        # Configuration
        self.enable_l1 = enable_l1 and config.enable_l1_cache
        self.enable_l2 = enable_l2 and config.enable_l2_cache
        self.l1_ttl = l1_ttl or config.l1_cache_ttl
        self.l2_ttl = l2_ttl or config.l2_cache_ttl
        self.l1_max_size = l1_max_size or config.l1_cache_max_size

        # L1 cache (in-memory LRU)
        self.l1_cache = LRUCache(max_size=self.l1_max_size) if self.enable_l1 else None

        # L2 cache (Redis)
        self.redis_client = None
        self.redis_available = False

        if self.enable_l2:
            redis_url = redis_url or config.redis_url
            if redis_url:
                self._initialize_redis(redis_url)

        # Statistics
        self.stats = CacheStats()

        self.logger = logger.bind(component="context_cache")

    def _initialize_redis(self, redis_url: str):
        """Initialize Redis connection"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle serialization
            )
            self.redis_available = True
            self.logger.info("redis_initialized", url=redis_url)
        except ImportError:
            self.logger.warning("redis_library_not_available")
            self.redis_available = False
        except Exception as e:
            self.logger.error(
                "redis_initialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            self.redis_available = False

    async def get(self, key: str) -> Optional[EnrichedContext]:
        """
        Get enriched context from cache.

        Checks L1 first, then L2, promoting L2 hits to L1.

        Args:
            key: Cache key

        Returns:
            EnrichedContext if found, None otherwise
        """
        self.stats.total_gets += 1

        # Try L1 first (fastest)
        if self.enable_l1 and self.l1_cache:
            l1_value = await self.l1_cache.get(key)
            if l1_value is not None:
                self.stats.l1_hits += 1
                self.logger.debug("l1_cache_hit", key=key)
                # Mark as cache hit
                if isinstance(l1_value, EnrichedContext):
                    l1_value.cache_hit = True
                return l1_value

            self.stats.l1_misses += 1

        # Try L2 (Redis)
        if self.enable_l2 and self.redis_available and self.redis_client:
            try:
                l2_data = await self.redis_client.get(key)
                if l2_data:
                    self.stats.l2_hits += 1
                    self.logger.debug("l2_cache_hit", key=key)

                    # Deserialize
                    context = self._deserialize(l2_data)
                    if context:
                        # Promote to L1
                        if self.enable_l1 and self.l1_cache:
                            await self.l1_cache.set(key, context, self.l1_ttl)

                        # Mark as cache hit
                        context.cache_hit = True
                        return context

                self.stats.l2_misses += 1

            except Exception as e:
                self.logger.warning(
                    "l2_cache_error",
                    error=str(e),
                    error_type=type(e).__name__
                )
                self.stats.l2_misses += 1

        # Cache miss on both tiers
        return None

    async def set(self, key: str, context: EnrichedContext):
        """
        Store context in both cache tiers.

        Args:
            key: Cache key
            context: EnrichedContext to cache
        """
        self.stats.total_sets += 1

        # Store in L1
        if self.enable_l1 and self.l1_cache:
            try:
                await self.l1_cache.set(key, context, self.l1_ttl)
                self.logger.debug("l1_cache_set", key=key, ttl=self.l1_ttl)
            except Exception as e:
                self.logger.warning(
                    "l1_cache_set_failed",
                    error=str(e),
                    error_type=type(e).__name__
                )

        # Store in L2
        if self.enable_l2 and self.redis_available and self.redis_client:
            try:
                serialized = self._serialize(context)
                await self.redis_client.setex(key, self.l2_ttl, serialized)
                self.logger.debug("l2_cache_set", key=key, ttl=self.l2_ttl)
            except Exception as e:
                self.logger.warning(
                    "l2_cache_set_failed",
                    error=str(e),
                    error_type=type(e).__name__
                )

    async def delete(self, key: str):
        """
        Delete key from both cache tiers.

        Args:
            key: Cache key
        """
        # Delete from L1
        if self.enable_l1 and self.l1_cache:
            await self.l1_cache.delete(key)

        # Delete from L2
        if self.enable_l2 and self.redis_available and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                self.logger.warning("l2_cache_delete_failed", error=str(e))

    async def clear(self):
        """Clear both cache tiers"""
        # Clear L1
        if self.enable_l1 and self.l1_cache:
            await self.l1_cache.clear()

        # Clear L2 (all keys matching pattern)
        if self.enable_l2 and self.redis_available and self.redis_client:
            try:
                pattern = "context:*"
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )
                    if keys:
                        await self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as e:
                self.logger.warning("l2_cache_clear_failed", error=str(e))

    async def warm_cache(
        self,
        customer_ids: List[str],
        agent_type: AgentType,
        fetch_func: callable
    ):
        """
        Warm cache by pre-fetching contexts.

        Args:
            customer_ids: List of customer IDs to warm
            agent_type: Agent type for context
            fetch_func: Async function to fetch context (customer_id, agent_type) -> EnrichedContext
        """
        self.logger.info(
            "cache_warming_started",
            customer_count=len(customer_ids),
            agent_type=agent_type.value
        )

        # Warm in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(customer_ids), batch_size):
            batch = customer_ids[i:i + batch_size]

            tasks = []
            for customer_id in batch:
                task = self._warm_single(customer_id, agent_type, fetch_func)
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        self.logger.info(
            "cache_warming_completed",
            customer_count=len(customer_ids)
        )

    async def _warm_single(
        self,
        customer_id: str,
        agent_type: AgentType,
        fetch_func: callable
    ):
        """Warm cache for single customer"""
        try:
            cache_key = f"context:{customer_id}:{agent_type.value}"

            # Check if already cached
            existing = await self.get(cache_key)
            if existing:
                return  # Already warm

            # Fetch and cache
            context = await fetch_func(customer_id, agent_type)
            if context:
                await self.set(cache_key, context)

        except Exception as e:
            self.logger.warning(
                "cache_warm_failed",
                customer_id=customer_id,
                error=str(e)
            )

    async def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats object
        """
        # Update sizes
        if self.enable_l1 and self.l1_cache:
            self.stats.l1_size = await self.l1_cache.size()
            self.stats.l1_evictions = await self.l1_cache.evictions()

        if self.enable_l2 and self.redis_available and self.redis_client:
            try:
                # Count keys matching pattern
                pattern = "context:*"
                cursor = 0
                count = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )
                    count += len(keys)
                    if cursor == 0:
                        break
                self.stats.l2_size = count
            except Exception:
                pass

        return self.stats

    async def reset_stats(self):
        """Reset cache statistics"""
        self.stats = CacheStats()

    async def health_check(self) -> Dict[str, Any]:
        """
        Check cache health.

        Returns:
            Health check results
        """
        health = {
            "l1_enabled": self.enable_l1,
            "l2_enabled": self.enable_l2,
            "redis_available": self.redis_available,
        }

        # Check L1
        if self.enable_l1 and self.l1_cache:
            health["l1_size"] = await self.l1_cache.size()
            health["l1_status"] = "healthy"

        # Check L2
        if self.enable_l2 and self.redis_available and self.redis_client:
            try:
                await self.redis_client.ping()
                health["l2_status"] = "healthy"
            except Exception as e:
                health["l2_status"] = "unhealthy"
                health["l2_error"] = str(e)
        else:
            health["l2_status"] = "disabled"

        return health

    async def cleanup(self):
        """Cleanup expired entries from both tiers"""
        # Cleanup L1
        if self.enable_l1 and self.l1_cache:
            await self.l1_cache.cleanup_expired()

        # L2 (Redis) handles expiration automatically via TTL

    def _serialize(self, context: EnrichedContext) -> bytes:
        """
        Serialize EnrichedContext to bytes.

        Uses pickle for efficient serialization with full type support.

        Args:
            context: EnrichedContext to serialize

        Returns:
            Serialized bytes
        """
        try:
            # Use pickle for efficient serialization
            return pickle.dumps(context)
        except Exception as e:
            self.logger.error(
                "serialization_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            # Fallback to JSON
            try:
                data = asdict(context) if hasattr(context, '__dataclass_fields__') else vars(context)
                return json.dumps(data, default=str).encode('utf-8')
            except Exception as e2:
                self.logger.error("json_serialization_failed", error=str(e2))
                raise

    def _deserialize(self, data: bytes) -> Optional[EnrichedContext]:
        """
        Deserialize bytes to EnrichedContext.

        Args:
            data: Serialized bytes

        Returns:
            EnrichedContext or None if deserialization fails
        """
        try:
            # Try pickle first
            return pickle.loads(data)
        except Exception as e:
            self.logger.warning("pickle_deserialization_failed", error=str(e))

            # Fallback to JSON
            try:
                json_str = data.decode('utf-8')
                context_dict = json.loads(json_str)

                # Reconstruct EnrichedContext from dict
                # This is a simplified version - adjust based on your actual types
                return EnrichedContext(**context_dict)

            except Exception as e2:
                self.logger.error(
                    "deserialization_failed",
                    error=str(e2),
                    error_type=type(e2).__name__
                )
                return None

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Close Redis connection if needed
        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception:
                pass


# Global cache instance
_cache: Optional[ContextCache] = None


def get_cache() -> ContextCache:
    """
    Get or create global cache instance.

    Returns:
        Global ContextCache instance
    """
    global _cache
    if _cache is None:
        _cache = ContextCache()
    return _cache
