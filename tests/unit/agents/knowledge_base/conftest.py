"""
Shared fixtures for Knowledge Base agent tests.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from contextlib import contextmanager
import uuid
import sys


# Mock EventBus BEFORE any imports that might use it
def _create_mock_event_bus():
    """Create comprehensive EventBus mock"""
    mock_bus = AsyncMock()
    mock_bus.publish = AsyncMock()
    mock_bus.subscribe = AsyncMock()
    mock_bus.send = AsyncMock()
    mock_bus.emit = AsyncMock()
    mock_bus.dispatch = AsyncMock()
    mock_bus.notify = AsyncMock()
    return mock_bus


# Install mock at module level before imports
_global_mock_bus = _create_mock_event_bus()


def pytest_configure(config):
    """Configure pytest to mock EventBus before any imports"""
    # Mock the EventBus module-level singleton
    if 'src.core.events' in sys.modules:
        sys.modules['src.core.events']._event_bus = _global_mock_bus

    # Patch get_event_bus function
    def mock_get_event_bus():
        return _global_mock_bus

    if 'src.core.events' in sys.modules:
        sys.modules['src.core.events'].get_event_bus = mock_get_event_bus


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client"""
    with patch('src.agents.essential.knowledge_base.searcher.VectorStore') as mock:
        mock_instance = MagicMock()
        mock_instance.search.return_value = [
            {
                "doc_id": "kb_123",
                "title": "Test Article",
                "content": "Test content for article",
                "category": "billing",
                "tags": ["upgrade", "plans"],
                "similarity_score": 0.92,
                "url": "/kb/test-article"
            }
        ]
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM calls"""
    async def mock_call_llm(self, system_prompt, user_message, max_tokens=1024):
        # Return different responses based on context
        if "quality" in system_prompt.lower():
            return '''{"completeness": 85, "clarity": 90, "accuracy": 95, "examples": 75, "issues": [], "strengths": ["Clear instructions"], "confidence": 0.88}'''
        elif "faq" in system_prompt.lower():
            return '''{"question": "How do I upgrade my plan?", "answer": "Go to Settings > Billing > Select Plan", "alternate_phrasings": ["Can I upgrade?", "How to upgrade?"], "category": "billing", "confidence": 0.9}'''
        elif "gap" in system_prompt.lower() or "topic" in system_prompt.lower():
            return '''{"topic": "API Authentication", "suggested_article_title": "API Authentication Guide", "key_questions": ["How to authenticate?", "API keys?"], "category": "api"}'''
        else:
            return '''{"result": "mocked response"}'''

    monkeypatch.setattr(
        'src.agents.base.base_agent.BaseAgent.call_llm',
        mock_call_llm
    )


@pytest.fixture
def sample_kb_article():
    """Sample KB article for testing"""
    return {
        "id": "kb_test_123",
        "article_id": "kb_test_123",
        "title": "How to Upgrade Your Plan",
        "content": """
## Overview
Upgrading your plan is simple.

## Steps
1. Go to Settings
2. Click Billing
3. Select new plan
4. Confirm upgrade

## Examples
```python
upgrade_plan(user_id="123", plan="premium")
```

## Notes
You'll be charged a prorated amount.
        """,
        "category": "billing",
        "tags": ["upgrade", "billing", "plans"],
        "quality_score": 85,
        "helpful_count": 45,
        "not_helpful_count": 3,
        "view_count": 500,
        "created_at": datetime.now() - timedelta(days=30),
        "updated_at": datetime.now() - timedelta(days=7)
    }


@pytest.fixture
def sample_kb_results(sample_kb_article):
    """Sample KB search results"""
    return [
        sample_kb_article,
        {
            "id": "kb_test_456",
            "article_id": "kb_test_456",
            "title": "Plan Pricing",
            "content": "Our plans: Basic $10, Premium $25, Enterprise custom",
            "category": "billing",
            "tags": ["pricing", "plans"],
            "similarity_score": 0.85,
            "quality_score": 90,
            "helpful_count": 30,
            "not_helpful_count": 2,
            "view_count": 300,
            "created_at": datetime.now() - timedelta(days=60),
            "updated_at": datetime.now() - timedelta(days=14)
        }
    ]


@pytest.fixture
def mock_db_session(monkeypatch):
    """Mock database session"""
    from contextlib import asynccontextmanager

    session = MagicMock()

    # Mock ASYNC context manager - this is critical!
    @asynccontextmanager
    async def mock_get_session():
        yield session

    # Configure mock session
    session.query.return_value.filter.return_value.first.return_value = None
    session.query.return_value.filter.return_value.all.return_value = []

    # Mock execute to return a result with .all() method
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_result.scalars.return_value = MagicMock(all=MagicMock(return_value=[]))
    session.execute = AsyncMock(return_value=mock_result)

    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.add = MagicMock()

    # Patch get_db_session to return our mock
    monkeypatch.setattr(
        'src.database.connection.get_db_session',
        mock_get_session
    )

    return session


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model"""
    with patch('sentence_transformers.SentenceTransformer') as mock:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = [[0.1] * 384]  # 384-dim embedding
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing"""
    return {
        "conversation_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "primary_intent": "billing_upgrade",
        "kb_match_score": 0.5,  # Low match
        "created_at": datetime.now()
    }


@pytest.fixture(autouse=True, scope="function")
def mock_event_bus(monkeypatch):
    """Mock EventBus for all KB agent tests"""
    # Create a comprehensive mock with all possible methods
    mock_bus = AsyncMock()
    mock_bus.publish = AsyncMock(return_value=None)
    mock_bus.subscribe = AsyncMock(return_value=None)
    mock_bus.send = AsyncMock(return_value=None)
    mock_bus.emit = AsyncMock(return_value=None)
    mock_bus.dispatch = AsyncMock(return_value=None)
    mock_bus.notify = AsyncMock(return_value=None)

    # Mock class that returns the mock_bus instance
    mock_bus_class = MagicMock(return_value=mock_bus)

    def get_mock_event_bus():
        return mock_bus

    # Patch EventBus module
    monkeypatch.setattr('src.core.events.get_event_bus', get_mock_event_bus, raising=False)
    monkeypatch.setattr('src.core.events.EventBus', mock_bus_class, raising=False)

    # CRITICAL: Patch the services' event_bus attributes directly
    # This handles cases where services are already instantiated
    try:
        import src.services.application.conversation_service as conv_service
        if hasattr(conv_service, 'ConversationApplicationService'):
            # Patch the __init__ to set event_bus to our mock
            original_init = conv_service.ConversationApplicationService.__init__
            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                self.event_bus = mock_bus
            monkeypatch.setattr(conv_service.ConversationApplicationService, '__init__', patched_init, raising=False)
    except (ImportError, AttributeError):
        pass

    try:
        import src.services.application.customer_service as cust_service
        if hasattr(cust_service, 'CustomerApplicationService'):
            original_init = cust_service.CustomerApplicationService.__init__
            def patched_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                self.event_bus = mock_bus
            monkeypatch.setattr(cust_service.CustomerApplicationService, '__init__', patched_init, raising=False)
    except (ImportError, AttributeError):
        pass

    return mock_bus
