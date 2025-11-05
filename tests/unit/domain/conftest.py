"""
Shared fixtures for domain services tests
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List


# ===== Mock Data Fixtures =====

@pytest.fixture
def sample_customer_id():
    """Sample customer UUID"""
    return uuid4()


@pytest.fixture
def sample_conversation_id():
    """Sample conversation UUID"""
    return uuid4()


@pytest.fixture
def sample_message_id():
    """Sample message UUID"""
    return uuid4()


@pytest.fixture
def sample_timestamp():
    """Sample timestamp"""
    return datetime.utcnow()


@pytest.fixture
def timestamp_1_hour_ago():
    """Timestamp from 1 hour ago"""
    return datetime.utcnow() - timedelta(hours=1)


@pytest.fixture
def timestamp_5_minutes_ago():
    """Timestamp from 5 minutes ago"""
    return datetime.utcnow() - timedelta(minutes=5)


# ===== Mock Conversation Object =====

class MockMessage:
    """Mock message object for testing"""
    def __init__(
        self,
        role: str = "user",
        content: str = "Test message",
        agent_name: str = None,
        sentiment: float = None,
        confidence: float = None
    ):
        self.role = role
        self.content = content
        self.agent_name = agent_name
        self.sentiment = sentiment
        self.confidence = confidence


class MockConversation:
    """Mock conversation object for testing"""
    def __init__(
        self,
        status: str = "active",
        messages: List[MockMessage] = None,
        sentiment_avg: float = None,
        agents_involved: List[str] = None,
        started_at: datetime = None
    ):
        self.status = status
        self.messages = messages or []
        self.sentiment_avg = sentiment_avg
        self.agents_involved = agents_involved or []
        self.started_at = started_at or datetime.utcnow()


@pytest.fixture
def mock_conversation():
    """Create a basic mock conversation"""
    return MockConversation()


@pytest.fixture
def active_conversation_with_messages():
    """Active conversation with user and agent messages"""
    return MockConversation(
        status="active",
        messages=[
            MockMessage(role="user", content="I need help"),
            MockMessage(role="assistant", content="How can I help?", agent_name="router"),
        ]
    )


@pytest.fixture
def resolved_conversation():
    """Resolved conversation"""
    return MockConversation(
        status="resolved",
        messages=[
            MockMessage(role="user", content="Issue"),
            MockMessage(role="assistant", content="Solution", agent_name="technical"),
        ]
    )


@pytest.fixture
def escalated_conversation():
    """Escalated conversation"""
    return MockConversation(
        status="escalated",
        messages=[
            MockMessage(role="user", content="Complex issue"),
        ],
        agents_involved=["router", "technical", "escalation"]
    )


@pytest.fixture
def conversation_without_agent():
    """Conversation with only user messages"""
    return MockConversation(
        status="active",
        messages=[
            MockMessage(role="user", content="Hello"),
        ]
    )


# ===== Customer Data Fixtures =====

@pytest.fixture
def free_customer_data():
    """Mock free plan customer data"""
    return {
        "plan": "free",
        "blocked": False,
        "suspended": False,
        "conversation_count": 0
    }


@pytest.fixture
def premium_customer_data():
    """Mock premium plan customer data"""
    return {
        "plan": "premium",
        "blocked": False,
        "suspended": False,
        "conversation_count": 50
    }


@pytest.fixture
def blocked_customer_data():
    """Mock blocked customer data"""
    return {
        "plan": "basic",
        "blocked": True,
        "suspended": False,
        "conversation_count": 0
    }


@pytest.fixture
def customer_at_rate_limit():
    """Mock customer at rate limit"""
    return {
        "plan": "free",
        "blocked": False,
        "suspended": False,
        "conversation_count": 10  # Free plan limit
    }


# ===== Usage Pattern Fixtures =====

@pytest.fixture
def usage_pattern_frequent_rate_limits():
    """Usage pattern with frequent rate limit hits"""
    return {
        "rate_limit_hits_this_month": 5,
        "advanced_features_used": 0,
        "team_size": 3
    }


@pytest.fixture
def usage_pattern_advanced_features():
    """Usage pattern with advanced feature usage"""
    return {
        "rate_limit_hits_this_month": 0,
        "advanced_features_used": 10,
        "team_size": 5
    }


@pytest.fixture
def usage_pattern_large_team():
    """Usage pattern with large team"""
    return {
        "rate_limit_hits_this_month": 0,
        "advanced_features_used": 3,
        "team_size": 75
    }