"""
Test fixtures for context enrichment tests.
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

from src.services.infrastructure.context_enrichment.types import (
    EnrichedContext,
    ProviderResult,
    AgentType,
    ProviderStatus,
    ProviderPriority
)
from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider
from src.services.infrastructure.context_enrichment.registry import ProviderRegistry
from src.services.infrastructure.context_enrichment.cache import ContextCache
from src.services.infrastructure.context_enrichment.orchestrator import ContextOrchestrator


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_customer_id() -> str:
    """Sample customer ID"""
    return str(uuid4())


@pytest.fixture
def sample_conversation_id() -> str:
    """Sample conversation ID"""
    return str(uuid4())


@pytest.fixture
def sample_provider_result() -> ProviderResult:
    """Sample provider result"""
    return ProviderResult(
        provider_name="test_provider",
        status=ProviderStatus.SUCCESS,
        data={
            "company_name": "Test Company",
            "plan": "enterprise",
            "mrr": 5000.0,
            "health_score": 85
        },
        error=None,
        latency_ms=50,
        fetched_at=datetime.utcnow()
    )


@pytest.fixture
def sample_enriched_context(sample_customer_id: str) -> EnrichedContext:
    """Sample enriched context"""
    return EnrichedContext(
        customer_id=sample_customer_id,
        agent_type=AgentType.SUPPORT,
        conversation_id=None,
        data={
            "company_name": "Test Company",
            "plan": "enterprise",
            "mrr": 5000.0,
            "health_score": 85,
            "segments": ["enterprise", "high_value"],
            "support_history": {
                "total_tickets": 10,
                "open_tickets": 2,
                "avg_resolution_time_hours": 24.5
            }
        },
        provider_results=[],
        enriched_at=datetime.utcnow(),
        cache_hit=False,
        relevance_score=0.85,
        latency_ms=100
    )


@pytest.fixture
def sample_customer_data() -> Dict[str, Any]:
    """Sample customer data"""
    return {
        "company_name": "Test Company Inc",
        "industry": "Technology",
        "company_size": "51-200",
        "plan": "enterprise",
        "mrr": 5000.0,
        "arr": 60000.0,
        "ltv": 180000.0,
        "health_score": 85,
        "health_trend": "improving",
        "churn_risk": 0.15,
        "nps_score": 8,
        "customer_since": datetime.utcnow(),
        "account_age_days": 365,
        "segments": ["enterprise", "high_value", "engaged"],
        "primary_contact": {
            "name": "John Doe",
            "email": "john@testcompany.com",
            "title": "CTO"
        },
        "key_notes": [
            "Recently expanded to 50 seats",
            "Interested in premium features",
            "Very engaged with product"
        ]
    }


class MockProvider(BaseContextProvider):
    """Mock provider for testing"""

    def __init__(self, name: str = "mock_provider", data: Dict[str, Any] = None):
        super().__init__()
        self.name = name
        self._data = data or {}
        self.fetch_called = False
        self.fetch_count = 0

    async def fetch(
        self,
        customer_id: str,
        conversation_id: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Fetch mock data"""
        self.fetch_called = True
        self.fetch_count += 1
        return self._data.copy()


class SlowMockProvider(BaseContextProvider):
    """Slow mock provider for timeout testing"""

    def __init__(self, delay_seconds: float = 1.0):
        super().__init__()
        self.name = "slow_provider"
        self.delay_seconds = delay_seconds

    async def fetch(
        self,
        customer_id: str,
        conversation_id: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Fetch with delay"""
        await asyncio.sleep(self.delay_seconds)
        return {"slow_data": "value"}


class FailingMockProvider(BaseContextProvider):
    """Failing mock provider for error testing"""

    def __init__(self, error_message: str = "Provider failed"):
        super().__init__()
        self.name = "failing_provider"
        self.error_message = error_message

    async def fetch(
        self,
        customer_id: str,
        conversation_id: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Always fail"""
        raise Exception(self.error_message)


@pytest.fixture
def mock_provider() -> MockProvider:
    """Mock provider fixture"""
    return MockProvider(data={"test_key": "test_value"})


@pytest.fixture
def slow_provider() -> SlowMockProvider:
    """Slow provider fixture"""
    return SlowMockProvider(delay_seconds=0.5)


@pytest.fixture
def failing_provider() -> FailingMockProvider:
    """Failing provider fixture"""
    return FailingMockProvider()


@pytest.fixture
def mock_registry(mock_provider: MockProvider) -> ProviderRegistry:
    """Mock provider registry"""
    registry = ProviderRegistry()
    registry.register("mock_provider", mock_provider)
    return registry


@pytest.fixture
async def test_cache() -> ContextCache:
    """Test cache fixture (in-memory only)"""
    cache = ContextCache(
        enable_l1=True,
        enable_l2=False,  # Disable Redis for tests
        l1_ttl=30,
        l1_max_size=100
    )
    yield cache
    await cache.clear()


@pytest.fixture
async def test_orchestrator(
    mock_registry: ProviderRegistry,
    test_cache: ContextCache
) -> ContextOrchestrator:
    """Test orchestrator fixture"""
    orchestrator = ContextOrchestrator(
        registry=mock_registry,
        cache=test_cache
    )
    return orchestrator


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_uow(mock_db_session):
    """Mock unit of work"""
    from unittest.mock import MagicMock

    uow = MagicMock()
    uow.session = mock_db_session

    # Mock repositories
    uow.customers = AsyncMock()
    uow.subscriptions = AsyncMock()
    uow.invoices = AsyncMock()
    uow.payments = AsyncMock()
    uow.credits = AsyncMock()
    uow.conversations = AsyncMock()
    uow.messages = AsyncMock()
    uow.usage_events = AsyncMock()
    uow.customer_segments = AsyncMock()
    uow.customer_health_events = AsyncMock()
    uow.customer_notes = AsyncMock()
    uow.customer_contacts = AsyncMock()

    return uow


@pytest.fixture
def sample_database_customer():
    """Sample database customer object"""
    from unittest.mock import MagicMock

    customer = MagicMock()
    customer.id = uuid4()
    customer.name = "Test Company"
    customer.plan = "enterprise"
    customer.created_at = datetime.utcnow()
    customer.extra_metadata = {
        "health_score": 85,
        "nps_score": 8,
        "industry": "Technology",
        "company_size": "51-200"
    }
    return customer


@pytest.fixture
def sample_database_subscription():
    """Sample database subscription object"""
    from unittest.mock import MagicMock

    subscription = MagicMock()
    subscription.id = uuid4()
    subscription.status = "active"
    subscription.plan = "enterprise"
    subscription.billing_cycle = "monthly"
    subscription.mrr = 5000.0
    subscription.arr = 60000.0
    subscription.seats_total = 50
    subscription.seats_used = 45
    subscription.seat_utilization = 90.0
    subscription.current_period_start = datetime.utcnow()
    subscription.current_period_end = datetime.utcnow()
    subscription.cancel_at_period_end = False
    subscription.trial_end = None
    return subscription


# Performance testing helpers
@pytest.fixture
def performance_threshold_ms() -> int:
    """Performance threshold in milliseconds"""
    return 100  # p95 should be < 100ms


@pytest.fixture
def load_test_customers() -> list:
    """Generate list of customer IDs for load testing"""
    return [str(uuid4()) for _ in range(100)]
