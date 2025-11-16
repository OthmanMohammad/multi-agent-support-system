"""
Tests for context cache (L1 + L2 tiers).
"""

import pytest
import asyncio
from datetime import datetime

from src.services.infrastructure.context_enrichment.cache import (
    ContextCache,
    LRUCache,
    CacheStats
)
from src.services.infrastructure.context_enrichment.types import AgentType


@pytest.mark.asyncio
async def test_lru_cache_basic():
    """Test basic LRU cache operations"""
    cache = LRUCache(max_size=3)

    # Set values
    await cache.set("key1", "value1", ttl=60)
    await cache.set("key2", "value2", ttl=60)
    await cache.set("key3", "value3", ttl=60)

    # Get values
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"

    # Check size
    assert await cache.size() == 3


@pytest.mark.asyncio
async def test_lru_cache_eviction():
    """Test LRU eviction when capacity reached"""
    cache = LRUCache(max_size=2)

    # Fill cache
    await cache.set("key1", "value1", ttl=60)
    await cache.set("key2", "value2", ttl=60)

    # Add third item - should evict key1 (least recently used)
    await cache.set("key3", "value3", ttl=60)

    # key1 should be evicted
    assert await cache.get("key1") is None
    assert await cache.get("key2") == "value2"
    assert await cache.get("key3") == "value3"

    # Check eviction count
    assert await cache.evictions() == 1


@pytest.mark.asyncio
async def test_lru_cache_access_updates_order():
    """Test that accessing an item updates its position in LRU"""
    cache = LRUCache(max_size=2)

    await cache.set("key1", "value1", ttl=60)
    await cache.set("key2", "value2", ttl=60)

    # Access key1 to make it most recently used
    await cache.get("key1")

    # Add key3 - should evict key2 (now least recently used)
    await cache.set("key3", "value3", ttl=60)

    # key1 should still be present
    assert await cache.get("key1") == "value1"
    assert await cache.get("key2") is None  # Evicted
    assert await cache.get("key3") == "value3"


@pytest.mark.asyncio
async def test_lru_cache_ttl_expiration():
    """Test TTL expiration in LRU cache"""
    cache = LRUCache(max_size=10)

    # Set with very short TTL
    await cache.set("key1", "value1", ttl=0)  # Expires immediately

    # Should be None (expired)
    await asyncio.sleep(0.1)
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_lru_cache_delete():
    """Test deleting items from LRU cache"""
    cache = LRUCache(max_size=10)

    await cache.set("key1", "value1", ttl=60)
    assert await cache.get("key1") == "value1"

    await cache.delete("key1")
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_lru_cache_clear():
    """Test clearing LRU cache"""
    cache = LRUCache(max_size=10)

    await cache.set("key1", "value1", ttl=60)
    await cache.set("key2", "value2", ttl=60)

    await cache.clear()

    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    assert await cache.size() == 0


@pytest.mark.asyncio
async def test_context_cache_l1_only():
    """Test context cache with L1 only"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False,
        l1_ttl=30,
        l1_max_size=100
    )

    # Create sample context
    from tests.context.conftest import sample_enriched_context
    context = sample_enriched_context("test-customer")

    # Set and get
    await cache.set("test-key", context)
    retrieved = await cache.get("test-key")

    assert retrieved is not None
    assert retrieved.cache_hit is True

    # Check stats
    stats = await cache.get_stats()
    assert stats.l1_hits == 1
    assert stats.total_gets == 1


@pytest.mark.asyncio
async def test_context_cache_miss():
    """Test cache miss"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    result = await cache.get("nonexistent-key")
    assert result is None

    # Check stats
    stats = await cache.get_stats()
    assert stats.l1_misses == 1


@pytest.mark.asyncio
async def test_context_cache_set_and_get():
    """Test setting and getting from context cache"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False,
        l1_ttl=30
    )

    from tests.context.conftest import sample_enriched_context
    context = sample_enriched_context("test-customer")

    # Set
    await cache.set("test-key", context)

    # Get
    retrieved = await cache.get("test-key")

    assert retrieved is not None
    assert retrieved.customer_id == context.customer_id
    assert retrieved.cache_hit is True


@pytest.mark.asyncio
async def test_context_cache_delete():
    """Test deleting from context cache"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    from tests.context.conftest import sample_enriched_context
    context = sample_enriched_context("test-customer")

    await cache.set("test-key", context)
    await cache.delete("test-key")

    retrieved = await cache.get("test-key")
    assert retrieved is None


@pytest.mark.asyncio
async def test_context_cache_clear():
    """Test clearing context cache"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    from tests.context.conftest import sample_enriched_context

    # Add multiple items
    for i in range(5):
        context = sample_enriched_context(f"customer-{i}")
        await cache.set(f"key-{i}", context)

    # Clear all
    await cache.clear()

    # All should be gone
    for i in range(5):
        retrieved = await cache.get(f"key-{i}")
        assert retrieved is None


@pytest.mark.asyncio
async def test_context_cache_stats():
    """Test cache statistics"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    from tests.context.conftest import sample_enriched_context
    context = sample_enriched_context("test-customer")

    # Set
    await cache.set("key1", context)

    # Get (hit)
    await cache.get("key1")

    # Get (miss)
    await cache.get("nonexistent")

    # Get stats
    stats = await cache.get_stats()

    assert stats.total_sets == 1
    assert stats.total_gets == 2
    assert stats.l1_hits == 1
    assert stats.l1_misses == 1
    assert stats.l1_hit_rate == 50.0  # 1 hit out of 2 gets


@pytest.mark.asyncio
async def test_context_cache_health_check():
    """Test cache health check"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    health = await cache.health_check()

    assert health["l1_enabled"] is True
    assert health["l1_status"] == "healthy"
    assert health["l2_enabled"] is False


@pytest.mark.asyncio
async def test_context_cache_cleanup():
    """Test cache cleanup of expired entries"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False,
        l1_ttl=1  # 1 second TTL
    )

    from tests.context.conftest import sample_enriched_context
    context = sample_enriched_context("test-customer")

    # Set with short TTL
    await cache.set("test-key", context)

    # Wait for expiration
    await asyncio.sleep(1.5)

    # Cleanup
    await cache.cleanup()

    # Should be gone
    retrieved = await cache.get("test-key")
    assert retrieved is None


@pytest.mark.asyncio
async def test_cache_stats_calculations():
    """Test CacheStats calculations"""
    stats = CacheStats()

    # Test with no data
    assert stats.l1_hit_rate == 0.0
    assert stats.l2_hit_rate == 0.0
    assert stats.overall_hit_rate == 0.0

    # Add some hits and misses
    stats.l1_hits = 8
    stats.l1_misses = 2
    stats.l2_hits = 1
    stats.l2_misses = 1
    stats.total_gets = 10

    assert stats.l1_hit_rate == 80.0
    assert stats.l2_hit_rate == 50.0
    assert stats.overall_hit_rate == 90.0  # (8+1)/10


@pytest.mark.asyncio
async def test_context_cache_warm_cache():
    """Test cache warming functionality"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    from tests.context.conftest import sample_enriched_context

    # Mock fetch function
    async def mock_fetch(customer_id: str, agent_type: AgentType):
        return sample_enriched_context(customer_id)

    # Warm cache for multiple customers
    customer_ids = ["cust1", "cust2", "cust3"]

    await cache.warm_cache(
        customer_ids=customer_ids,
        agent_type=AgentType.SUPPORT,
        fetch_func=mock_fetch
    )

    # All should be cached
    for cust_id in customer_ids:
        key = f"context:{cust_id}:{AgentType.SUPPORT.value}"
        cached = await cache.get(key)
        assert cached is not None


@pytest.mark.asyncio
async def test_context_cache_concurrent_access():
    """Test concurrent cache access"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    from tests.context.conftest import sample_enriched_context

    async def set_and_get(key: str):
        context = sample_enriched_context(f"customer-{key}")
        await cache.set(key, context)
        retrieved = await cache.get(key)
        return retrieved is not None

    # Run 100 concurrent operations
    tasks = [set_and_get(f"key-{i}") for i in range(100)]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(results)


@pytest.mark.asyncio
async def test_context_cache_reset_stats():
    """Test resetting cache statistics"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    from tests.context.conftest import sample_enriched_context
    context = sample_enriched_context("test-customer")

    # Generate some stats
    await cache.set("key1", context)
    await cache.get("key1")
    await cache.get("nonexistent")

    # Reset
    await cache.reset_stats()

    # Stats should be zero
    stats = await cache.get_stats()
    assert stats.total_sets == 0
    assert stats.total_gets == 0
    assert stats.l1_hits == 0
    assert stats.l1_misses == 0


@pytest.mark.asyncio
async def test_lru_cache_update_existing_key():
    """Test updating existing key in LRU cache"""
    cache = LRUCache(max_size=3)

    await cache.set("key1", "value1", ttl=60)
    await cache.set("key1", "value2", ttl=60)  # Update

    result = await cache.get("key1")
    assert result == "value2"


@pytest.mark.asyncio
async def test_context_cache_serialization():
    """Test cache serialization and deserialization"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False
    )

    from tests.context.conftest import sample_enriched_context
    original = sample_enriched_context("test-customer")

    # Set and get
    await cache.set("test-key", original)
    retrieved = await cache.get("test-key")

    # Should be equal
    assert retrieved is not None
    assert retrieved.customer_id == original.customer_id
    assert retrieved.agent_type == original.agent_type
