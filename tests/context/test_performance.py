"""
Performance tests for context enrichment.
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
import statistics

from src.services.infrastructure.context_enrichment.types import AgentType
from src.services.infrastructure.context_enrichment.orchestrator import get_orchestrator


@pytest.mark.asyncio
@pytest.mark.performance
async def test_enrichment_latency(performance_threshold_ms: int):
    """Test enrichment latency is under threshold"""
    orchestrator = get_orchestrator()
    customer_id = str(uuid4())

    start = datetime.utcnow()
    context = await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )
    latency_ms = (datetime.utcnow() - start).total_seconds() * 1000

    assert latency_ms < performance_threshold_ms


@pytest.mark.asyncio
@pytest.mark.performance
async def test_cache_hit_latency():
    """Test cache hit latency is sub-10ms"""
    orchestrator = get_orchestrator()
    customer_id = str(uuid4())

    # Prime cache
    await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )

    # Measure cache hit latency
    start = datetime.utcnow()
    context = await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )
    latency_ms = (datetime.utcnow() - start).total_seconds() * 1000

    assert context.cache_hit is True
    assert latency_ms < 10  # Sub-10ms for cache hit


@pytest.mark.asyncio
@pytest.mark.performance
async def test_p95_latency(load_test_customers: list):
    """Test p95 latency under 100ms"""
    orchestrator = get_orchestrator()
    latencies = []

    # Run enrichment for multiple customers
    for customer_id in load_test_customers[:20]:  # Test with 20 customers
        start = datetime.utcnow()
        await orchestrator.enrich(
            customer_id=customer_id,
            agent_type=AgentType.SUPPORT,
            force_refresh=True  # No cache to test real performance
        )
        latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
        latencies.append(latency_ms)

    # Calculate p95
    p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile

    assert p95 < 100  # p95 should be < 100ms


@pytest.mark.asyncio
@pytest.mark.performance
async def test_throughput():
    """Test system can handle high throughput"""
    orchestrator = get_orchestrator()

    # Generate customer IDs
    customer_ids = [str(uuid4()) for _ in range(100)]

    async def enrich_customer(customer_id: str):
        return await orchestrator.enrich(
            customer_id=customer_id,
            agent_type=AgentType.SUPPORT
        )

    # Run 100 concurrent requests
    start = datetime.utcnow()
    results = await asyncio.gather(*[enrich_customer(cid) for cid in customer_ids])
    elapsed = (datetime.utcnow() - start).total_seconds()

    # Calculate throughput
    throughput = len(results) / elapsed  # requests per second

    # Should handle at least 50 req/sec (target is 10k req/sec with production setup)
    assert throughput > 50


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_requests():
    """Test handling concurrent requests without degradation"""
    orchestrator = get_orchestrator()
    customer_id = str(uuid4())

    async def single_request():
        start = datetime.utcnow()
        context = await orchestrator.enrich(
            customer_id=customer_id,
            agent_type=AgentType.SUPPORT
        )
        return (datetime.utcnow() - start).total_seconds() * 1000

    # Run 50 concurrent requests
    latencies = await asyncio.gather(*[single_request() for _ in range(50)])

    # Average latency should still be reasonable
    avg_latency = statistics.mean(latencies)
    assert avg_latency < 200  # Average should be under 200ms


@pytest.mark.asyncio
@pytest.mark.performance
async def test_cache_performance():
    """Test cache performance under load"""
    orchestrator = get_orchestrator()
    customer_ids = [str(uuid4()) for _ in range(10)]

    # Prime cache
    for customer_id in customer_ids:
        await orchestrator.enrich(
            customer_id=customer_id,
            agent_type=AgentType.SUPPORT
        )

    # Measure cache hit performance
    cache_hit_latencies = []
    for _ in range(100):
        customer_id = customer_ids[_ % len(customer_ids)]
        start = datetime.utcnow()
        context = await orchestrator.enrich(
            customer_id=customer_id,
            agent_type=AgentType.SUPPORT
        )
        latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
        if context.cache_hit:
            cache_hit_latencies.append(latency_ms)

    # All cache hits should be fast
    avg_cache_latency = statistics.mean(cache_hit_latencies)
    assert avg_cache_latency < 10  # Average cache hit < 10ms


@pytest.mark.asyncio
@pytest.mark.performance
async def test_memory_efficiency():
    """Test memory efficiency with many cached items"""
    from src.services.infrastructure.context_enrichment.cache import ContextCache

    cache = ContextCache(
        enable_l1=True,
        enable_l2=False,
        l1_max_size=1000
    )

    from tests.context.conftest import sample_enriched_context

    # Cache 1000 items
    for i in range(1000):
        context = sample_enriched_context(f"customer-{i}")
        await cache.set(f"key-{i}", context)

    # Check size
    stats = await cache.get_stats()
    assert stats.l1_size <= 1000  # Should respect max size

    await cache.clear()


@pytest.mark.asyncio
@pytest.mark.performance
async def test_provider_parallel_execution():
    """Test providers execute in parallel for better performance"""
    from tests.context.conftest import SlowMockProvider
    from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
    from src.services.infrastructure.context_enrichment.orchestrator import ContextOrchestrator

    # Create 5 slow providers (each 100ms)
    providers = [SlowMockProvider(delay_seconds=0.1) for _ in range(5)]
    for i, provider in enumerate(providers):
        provider.name = f"slow_{i}"

    registry = ProviderRegistry()
    for provider in providers:
        registry.register(provider.name, provider)

    registry.configure_agent(
        AgentType.SUPPORT,
        [p.name for p in providers]
    )

    orchestrator = ContextOrchestrator(registry=registry)

    # Enrich
    start = datetime.utcnow()
    context = await orchestrator.enrich(
        customer_id=str(uuid4()),
        agent_type=AgentType.SUPPORT,
        timeout_ms=5000
    )
    latency_ms = (datetime.utcnow() - start).total_seconds() * 1000

    # If sequential: 500ms (5 * 100ms)
    # If parallel: ~100ms
    # Should be significantly faster than sequential
    assert latency_ms < 300  # Should be closer to 100ms than 500ms
