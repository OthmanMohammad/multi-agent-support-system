"""
Integration tests for context enrichment system.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from src.services.infrastructure.context_enrichment.types import AgentType
from src.services.infrastructure.context_enrichment.orchestrator import get_orchestrator
from src.services.infrastructure.context_enrichment.cache import get_cache
from src.services.infrastructure.context_enrichment.registry import get_registry


@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_to_end_enrichment():
    """Test end-to-end context enrichment flow"""
    orchestrator = get_orchestrator()
    customer_id = str(uuid4())

    # Enrich context
    context = await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )

    assert context is not None
    assert context.customer_id == customer_id
    assert isinstance(context.data, dict)
    assert context.latency_ms >= 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cache_integration():
    """Test cache integration with enrichment"""
    orchestrator = get_orchestrator()
    cache = get_cache()
    customer_id = str(uuid4())

    # Clear cache
    await cache.clear()

    # First call - cache miss
    context1 = await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )
    assert context1.cache_hit is False

    # Second call - cache hit
    context2 = await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )
    assert context2.cache_hit is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_agent_types():
    """Test enrichment for multiple agent types"""
    orchestrator = get_orchestrator()
    customer_id = str(uuid4())

    agent_types = [
        AgentType.SUPPORT,
        AgentType.BILLING,
        AgentType.SUCCESS,
        AgentType.SALES
    ]

    for agent_type in agent_types:
        context = await orchestrator.enrich(
            customer_id=customer_id,
            agent_type=agent_type
        )
        assert context is not None
        assert context.agent_type == agent_type


@pytest.mark.asyncio
@pytest.mark.integration
async def test_conversation_context_integration():
    """Test conversation-specific enrichment"""
    orchestrator = get_orchestrator()
    customer_id = str(uuid4())
    conversation_id = str(uuid4())

    context = await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT,
        conversation_id=conversation_id
    )

    assert context.conversation_id == conversation_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_provider_registry_integration():
    """Test provider registry integration"""
    registry = get_registry()

    # Get providers for support agent
    providers = registry.get_providers_for_agent(AgentType.SUPPORT)

    assert isinstance(providers, list)
    assert len(providers) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_check_integration():
    """Test system health check"""
    orchestrator = get_orchestrator()

    health = await orchestrator.health_check()

    assert "orchestrator" in health
    assert "cache" in health
    assert "providers" in health


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cache_invalidation_integration():
    """Test cache invalidation"""
    orchestrator = get_orchestrator()
    customer_id = str(uuid4())

    # Enrich and cache
    await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )

    # Invalidate
    await orchestrator.invalidate_cache(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )

    # Next call should not hit cache
    context = await orchestrator.enrich(
        customer_id=customer_id,
        agent_type=AgentType.SUPPORT
    )
    assert context.cache_hit is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_enrichments():
    """Test concurrent enrichment requests"""
    import asyncio
    orchestrator = get_orchestrator()

    async def enrich_customer(customer_id: str):
        return await orchestrator.enrich(
            customer_id=customer_id,
            agent_type=AgentType.SUPPORT
        )

    # Create 10 concurrent requests
    customer_ids = [str(uuid4()) for _ in range(10)]
    tasks = [enrich_customer(cid) for cid in customer_ids]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert len(results) == 10
    assert all(r is not None for r in results)
