"""
Shared fixtures for infrastructure service tests

These fixtures provide mocked dependencies for infrastructure services
to enable isolated unit testing without real database, Redis, or external APIs.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, UTC


# ===== Mock Unit of Work =====

@pytest.fixture
def mock_uow():
    """
    Create mock Unit of Work with all repositories
    
    Usage:
        def test_something(mock_uow):
            service = CustomerInfrastructureService(mock_uow)
            mock_uow.customers.get_by_id.return_value = some_customer
            # ... test code ...
    """
    uow = MagicMock()
    
    # Mock all repositories with AsyncMock
    uow.customers = AsyncMock()
    uow.conversations = AsyncMock()
    uow.messages = AsyncMock()
    uow.agent_performance = AsyncMock()
    
    # Mock methods
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.flush = AsyncMock()
    uow.refresh = AsyncMock()
    
    # Mock user ID for audit trail
    uow.current_user_id = None
    
    return uow


# ===== Mock Domain Models =====

@pytest.fixture
def mock_customer():
    """Create a mock customer model"""
    customer = MagicMock()
    customer.id = uuid4()
    customer.email = "test@example.com"
    customer.name = "Test User"
    customer.plan = "free"
    customer.extra_metadata = {}
    customer.created_at = datetime.now(UTC)
    customer.updated_at = None
    return customer


@pytest.fixture
def mock_conversation():
    """Create a mock conversation model"""
    conversation = MagicMock()
    conversation.id = uuid4()
    conversation.customer_id = uuid4()
    conversation.status = "active"
    conversation.primary_intent = "billing"
    conversation.agents_involved = ["router"]
    conversation.sentiment_avg = None
    conversation.kb_articles_used = []
    conversation.extra_metadata = {}
    conversation.started_at = datetime.now(UTC)
    conversation.ended_at = None
    conversation.resolution_time_seconds = None
    conversation.messages = []
    return conversation


@pytest.fixture
def mock_message():
    """Create a mock message model"""
    message = MagicMock()
    message.id = uuid4()
    message.conversation_id = uuid4()
    message.role = "user"
    message.content = "Test message content"
    message.agent_name = None
    message.intent = None
    message.sentiment = None
    message.confidence = None
    message.tokens_used = None
    message.extra_metadata = {}
    message.created_at = datetime.now(UTC)
    return message


# ===== Mock Vector Store =====

@pytest.fixture
def mock_vector_store():
    """
    Create mock vector store for KB tests
    
    Usage:
        def test_kb_search(mock_vector_store):
            service = KnowledgeBaseService()
            service.vector_store = mock_vector_store
            service.available = True
            # ... test code ...
    """
    with patch('services.infrastructure.knowledge_base_service.VectorStore') as mock:
        mock_instance = MagicMock()
        
        # Mock methods
        mock_instance.search = MagicMock(return_value=[])
        mock_instance.get_collection_info = MagicMock(return_value={
            "name": "kb_articles",
            "vector_size": 384,
            "points_count": 100,
            "status": "green"
        })
        
        mock.return_value = mock_instance
        yield mock_instance


# ===== Mock External Services =====

@pytest.fixture
def mock_redis():
    """Mock Redis client for caching tests"""
    with patch('services.infrastructure.caching_service.redis') as mock:
        redis_instance = MagicMock()
        
        # Mock Redis operations
        redis_instance.get = AsyncMock(return_value=None)
        redis_instance.set = AsyncMock(return_value=True)
        redis_instance.delete = AsyncMock(return_value=1)
        redis_instance.exists = AsyncMock(return_value=False)
        
        mock.return_value = redis_instance
        yield redis_instance


@pytest.fixture
def mock_notification_client():
    """Mock notification client (email, Slack, etc.)"""
    client = MagicMock()
    
    # Mock methods
    client.send_email = AsyncMock(return_value={"status": "sent"})
    client.send_slack = AsyncMock(return_value={"status": "sent"})
    client.send_webhook = AsyncMock(return_value={"status": "sent"})
    
    return client


# ===== Sample Data Factories =====

@pytest.fixture
def customer_factory():
    """
    Factory for creating test customers
    
    Usage:
        def test_something(customer_factory):
            customer = customer_factory(email="custom@example.com")
    """
    def _create_customer(**kwargs):
        defaults = {
            "id": uuid4(),
            "email": f"test_{uuid4().hex[:8]}@example.com",
            "name": "Test User",
            "plan": "free",
            "extra_metadata": {},
            "created_at": datetime.now(UTC),
            "updated_at": None
        }
        defaults.update(kwargs)
        
        customer = MagicMock()
        for key, value in defaults.items():
            setattr(customer, key, value)
        
        return customer
    
    return _create_customer


@pytest.fixture
def conversation_factory():
    """
    Factory for creating test conversations
    
    Usage:
        def test_something(conversation_factory):
            conv = conversation_factory(status="resolved")
    """
    def _create_conversation(**kwargs):
        defaults = {
            "id": uuid4(),
            "customer_id": uuid4(),
            "status": "active",
            "primary_intent": None,
            "agents_involved": [],
            "sentiment_avg": None,
            "kb_articles_used": [],
            "extra_metadata": {},
            "started_at": datetime.now(UTC),
            "ended_at": None,
            "resolution_time_seconds": None,
            "messages": []
        }
        defaults.update(kwargs)
        
        conversation = MagicMock()
        for key, value in defaults.items():
            setattr(conversation, key, value)
        
        return conversation
    
    return _create_conversation


# ===== Statistics/Analytics Fixtures =====

@pytest.fixture
def sample_conversation_stats():
    """Sample conversation statistics data"""
    return {
        "total_conversations": 100,
        "by_status": {
            "active": 20,
            "resolved": 70,
            "escalated": 10
        },
        "by_intent": {
            "billing": 40,
            "technical": 30,
            "usage": 20,
            "api": 10
        },
        "avg_resolution_time_seconds": 1800,
        "avg_sentiment": 0.65
    }


@pytest.fixture
def sample_kb_articles():
    """Sample KB articles for search results"""
    return [
        {
            "doc_id": "1",
            "title": "How to Upgrade Your Plan",
            "content": "To upgrade your plan, go to Settings > Billing...",
            "category": "billing",
            "tags": ["upgrade", "plan", "pricing"],
            "similarity_score": 0.92
        },
        {
            "doc_id": "2",
            "title": "API Rate Limits",
            "content": "Our API has the following rate limits...",
            "category": "api",
            "tags": ["api", "limits", "technical"],
            "similarity_score": 0.85
        }
    ]