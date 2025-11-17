"""
Tests for context orchestrator.
"""

import pytest
import asyncio
from datetime import datetime, UTC

from src.services.infrastructure.context_enrichment.types import (
    AgentType,
    ProviderStatus
)
from src.services.infrastructure.context_enrichment.orchestrator import ContextOrchestrator
from tests.context.conftest import (
    MockProvider,
    SlowMockProvider,
    FailingMockProvider
)


@pytest.mark.asyncio
async def test_orchestrator_basic_enrichment(
    test_orchestrator: ContextOrchestrator,
    sample_customer_id: str
):
    """Test basic context enrichment"""
    context = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )

    assert context is not None
    assert context.customer_id == sample_customer_id
    assert context.agent_type == AgentType.SUPPORT
    assert isinstance(context.data, dict)
    assert context.enriched_at is not None
    assert context.latency_ms >= 0


@pytest.mark.asyncio
async def test_orchestrator_with_multiple_providers(sample_customer_id: str):
    """Test orchestrator with multiple providers"""
    # Create providers
    provider1 = MockProvider("provider1", {"key1": "value1", "shared": "from_p1"})
    provider2 = MockProvider("provider2", {"key2": "value2", "shared": "from_p2"})
    provider3 = MockProvider("provider3", {"key3": "value3"})

    # Create registry
    from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
    registry = ProviderRegistry()
    registry.register("provider1", provider1)
    registry.register("provider2", provider2)
    registry.register("provider3", provider3)

    # Configure for SUPPORT agent
    registry.configure_agent(
        AgentType.SUPPORT,
        ["provider1", "provider2", "provider3"]
    )

    # Create orchestrator
    orchestrator = ContextOrchestrator(registry=registry)

    # Enrich
    context = await orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )

    assert context is not None
    assert "key1" in context.data or "_metadata" in context.data
    assert provider1.fetch_called
    assert provider2.fetch_called
    assert provider3.fetch_called


@pytest.mark.asyncio
async def test_orchestrator_handles_provider_timeout(sample_customer_id: str):
    """Test orchestrator handles slow providers with timeout"""
    # Create slow provider (2 second delay)
    slow_provider = SlowMockProvider(delay_seconds=2.0)
    fast_provider = MockProvider("fast", {"fast_data": "value"})

    # Create registry
    from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
    registry = ProviderRegistry()
    registry.register("slow", slow_provider)
    registry.register("fast", fast_provider)

    registry.configure_agent(AgentType.SUPPORT, ["slow", "fast"])

    # Create orchestrator
    orchestrator = ContextOrchestrator(registry=registry)

    # Enrich with short timeout (500ms)
    context = await orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT,
        timeout_ms=500
    )

    assert context is not None
    # Slow provider should timeout, but fast provider should succeed
    assert fast_provider.fetch_called

    # Check provider results
    timeout_results = [
        r for r in context.provider_results
        if r.status == ProviderStatus.TIMEOUT
    ]
    assert len(timeout_results) > 0  # Slow provider timed out


@pytest.mark.asyncio
async def test_orchestrator_handles_provider_failure(sample_customer_id: str):
    """Test orchestrator handles provider failures gracefully"""
    # Create failing and successful providers
    failing = FailingMockProvider("Something went wrong")
    success = MockProvider("success", {"good_data": "value"})

    # Create registry
    from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
    registry = ProviderRegistry()
    registry.register("failing", failing)
    registry.register("success", success)

    registry.configure_agent(AgentType.SUPPORT, ["failing", "success"])

    # Create orchestrator
    orchestrator = ContextOrchestrator(registry=registry)

    # Enrich
    context = await orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )

    assert context is not None
    # Should succeed despite one provider failing
    assert success.fetch_called

    # Check provider results
    failed_results = [
        r for r in context.provider_results
        if r.status == ProviderStatus.FAILED
    ]
    assert len(failed_results) > 0


@pytest.mark.asyncio
async def test_orchestrator_caching(
    test_orchestrator: ContextOrchestrator,
    sample_customer_id: str,
    mock_provider: MockProvider
):
    """Test orchestrator caching behavior"""
    # First call - should miss cache
    context1 = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )
    assert context1.cache_hit is False
    first_call_count = mock_provider.fetch_count

    # Second call - should hit cache
    context2 = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )
    assert context2.cache_hit is True
    # Provider should not be called again
    assert mock_provider.fetch_count == first_call_count


@pytest.mark.asyncio
async def test_orchestrator_force_refresh(
    test_orchestrator: ContextOrchestrator,
    sample_customer_id: str,
    mock_provider: MockProvider
):
    """Test force refresh bypasses cache"""
    # First call
    context1 = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )
    first_call_count = mock_provider.fetch_count

    # Second call with force_refresh
    context2 = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT,
        force_refresh=True
    )
    assert context2.cache_hit is False
    # Provider should be called again
    assert mock_provider.fetch_count > first_call_count


@pytest.mark.asyncio
async def test_orchestrator_cache_invalidation(
    test_orchestrator: ContextOrchestrator,
    sample_customer_id: str
):
    """Test cache invalidation"""
    # Enrich to populate cache
    context1 = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )

    # Invalidate cache
    await test_orchestrator.invalidate_cache(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )

    # Next call should miss cache
    context2 = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )
    assert context2.cache_hit is False


@pytest.mark.asyncio
async def test_orchestrator_conversation_context(
    test_orchestrator: ContextOrchestrator,
    sample_customer_id: str,
    sample_conversation_id: str
):
    """Test conversation-specific context"""
    context = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT,
        conversation_id=sample_conversation_id
    )

    assert context.conversation_id == sample_conversation_id


@pytest.mark.asyncio
async def test_orchestrator_different_agent_types(
    test_orchestrator: ContextOrchestrator,
    sample_customer_id: str
):
    """Test different agent types get different contexts"""
    support_context = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )

    billing_context = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.BILLING
    )

    # Should be different contexts (different cache keys)
    assert support_context.agent_type == AgentType.SUPPORT
    assert billing_context.agent_type == AgentType.BILLING


@pytest.mark.asyncio
async def test_orchestrator_parallel_execution(sample_customer_id: str):
    """Test providers execute in parallel"""
    # Create slow providers
    provider1 = SlowMockProvider(delay_seconds=0.1)
    provider2 = SlowMockProvider(delay_seconds=0.1)
    provider3 = SlowMockProvider(delay_seconds=0.1)

    provider1.name = "slow1"
    provider2.name = "slow2"
    provider3.name = "slow3"

    # Create registry
    from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
    registry = ProviderRegistry()
    registry.register("slow1", provider1)
    registry.register("slow2", provider2)
    registry.register("slow3", provider3)

    registry.configure_agent(AgentType.SUPPORT, ["slow1", "slow2", "slow3"])

    # Create orchestrator
    orchestrator = ContextOrchestrator(registry=registry)

    # Enrich and measure time
    start = datetime.now(UTC)
    context = await orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT,
        timeout_ms=5000
    )
    elapsed_ms = (datetime.now(UTC) - start).total_seconds() * 1000

    # If sequential, would take ~300ms (3 x 100ms)
    # If parallel, should take ~100ms
    # Allow some overhead, but should be significantly faster than sequential
    assert elapsed_ms < 250  # Should be closer to 100ms than 300ms


@pytest.mark.asyncio
async def test_orchestrator_health_check(test_orchestrator: ContextOrchestrator):
    """Test orchestrator health check"""
    health = await test_orchestrator.health_check()

    assert "orchestrator" in health
    assert health["orchestrator"] == "healthy"
    assert "cache" in health
    assert "providers" in health


@pytest.mark.asyncio
async def test_orchestrator_metrics(test_orchestrator: ContextOrchestrator):
    """Test orchestrator metrics collection"""
    metrics = await test_orchestrator.get_metrics()

    assert metrics is not None
    assert isinstance(metrics, dict)


@pytest.mark.asyncio
async def test_orchestrator_no_providers_for_agent(sample_customer_id: str):
    """Test orchestrator with no providers for agent type"""
    from src.services.infrastructure.context_enrichment.registry import ProviderRegistry

    # Empty registry
    registry = ProviderRegistry()

    orchestrator = ContextOrchestrator(registry=registry)

    # Enrich
    context = await orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT
    )

    # Should return empty context
    assert context is not None
    assert len(context.data) == 0 or "_metadata" in context.data


@pytest.mark.asyncio
async def test_orchestrator_custom_timeout(
    test_orchestrator: ContextOrchestrator,
    sample_customer_id: str
):
    """Test custom timeout parameter"""
    context = await test_orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT,
        timeout_ms=2000
    )

    assert context is not None


@pytest.mark.asyncio
async def test_orchestrator_specific_providers(sample_customer_id: str):
    """Test requesting specific providers"""
    provider1 = MockProvider("provider1", {"key1": "value1"})
    provider2 = MockProvider("provider2", {"key2": "value2"})
    provider3 = MockProvider("provider3", {"key3": "value3"})

    from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
    registry = ProviderRegistry()
    registry.register("provider1", provider1)
    registry.register("provider2", provider2)
    registry.register("provider3", provider3)

    registry.configure_agent(
        AgentType.SUPPORT,
        ["provider1", "provider2", "provider3"]
    )

    orchestrator = ContextOrchestrator(registry=registry)

    # Request only provider1 and provider2
    context = await orchestrator.enrich(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT,
        providers=["provider1", "provider2"]
    )

    assert provider1.fetch_called
    assert provider2.fetch_called
    assert not provider3.fetch_called
