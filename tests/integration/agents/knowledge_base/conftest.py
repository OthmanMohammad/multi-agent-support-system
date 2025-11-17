"""
Pytest fixtures for KB integration tests.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Conversation, Message, KBArticle
from src.database.session import get_db_session


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for integration tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def sample_kb_articles(test_db_session: AsyncSession) -> List[KBArticle]:
    """Create sample KB articles for testing"""
    articles = [
        KBArticle(
            title="How to Upgrade Your Plan",
            content="To upgrade your plan, navigate to Settings > Billing > Change Plan. Select your desired plan and confirm.",
            category="billing",
            tags=["billing", "upgrade", "plans"],
            quality_score=85.0,
            view_count=250,
            helpful_count=230,
            not_helpful_count=20,
        ),
        KBArticle(
            title="API Authentication Guide",
            content="Our API uses OAuth 2.0 for authentication. Generate an API key from your dashboard...",
            category="integrations",
            tags=["api", "authentication", "oauth"],
            quality_score=90.0,
            view_count=500,
            helpful_count=475,
            not_helpful_count=25,
        ),
        KBArticle(
            title="Troubleshooting Login Issues",
            content="If you're having trouble logging in, try clearing your browser cache...",
            category="technical",
            tags=["login", "troubleshooting", "authentication"],
            quality_score=70.0,
            view_count=150,
            helpful_count=98,
            not_helpful_count=52,
        ),
        KBArticle(
            title="Data Export Instructions",
            content="You can export your data in CSV or JSON format. Navigate to Settings > Data Export...",
            category="usage",
            tags=["data", "export", "csv", "json"],
            quality_score=88.0,
            view_count=180,
            helpful_count=160,
            not_helpful_count=20,
        )
    ]

    for article in articles:
        test_db_session.add(article)

    await test_db_session.commit()

    return articles


@pytest.fixture
async def sample_tickets(test_db_session: AsyncSession) -> List[Conversation]:
    """Create sample conversations for testing (replacing tickets)"""
    from uuid import uuid4
    from src.database.models import Customer

    # Create a test customer first
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
        plan="premium"
    )
    test_db_session.add(customer)
    await test_db_session.flush()

    conversations = []

    # Create conversations with common questions
    questions = [
        ("How do I upgrade my plan?", "billing_upgrade"),
        ("Can I upgrade to premium?", "billing_upgrade"),
        ("What's the upgrade process?", "billing_upgrade"),
        ("How to export data?", "data_export"),
        ("Can I download my data?", "data_export"),
        ("API authentication not working", "api_auth"),
        ("OAuth setup help needed", "api_auth"),
    ]

    for i, (question, intent) in enumerate(questions):
        conversation = Conversation(
            customer_id=customer.id,
            status="resolved",
            channel="chat",
            sentiment="neutral",
            extra_metadata={"intent": intent, "subject": question}
        )
        conversations.append(conversation)
        test_db_session.add(conversation)

    await test_db_session.commit()

    return conversations


@pytest.fixture
async def sample_conversations(test_db_session: AsyncSession, sample_tickets: List[Conversation]) -> List[Conversation]:
    """Create sample conversations with messages for testing"""
    # sample_tickets are already conversations, add messages to them
    for i, conversation in enumerate(sample_tickets[:5]):
        subject = conversation.extra_metadata.get("subject", "Question")

        # Add messages
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=subject,
        )
        test_db_session.add(user_message)

        agent_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="Here's how to resolve your issue...",
        )
        test_db_session.add(agent_message)

    await test_db_session.commit()

    return sample_tickets[:5]


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for integration tests"""
    class MockQdrantClient:
        def __init__(self):
            self.collections = {}
            self.points = {}

        def create_collection(self, collection_name: str, vectors_config):
            self.collections[collection_name] = vectors_config
            self.points[collection_name] = []

        def upsert(self, collection_name: str, points: List):
            if collection_name not in self.points:
                self.points[collection_name] = []
            self.points[collection_name].extend(points)

        def search(self, collection_name: str, query_vector: List[float], limit: int = 5):
            # Return mock search results
            return [
                type('SearchResult', (), {
                    'id': f'point_{i}',
                    'score': 0.9 - (i * 0.1),
                    'payload': {
                        'article_id': f'kb_00{i+1}',
                        'title': f'Article {i+1}',
                        'chunk_index': 0
                    }
                })
                for i in range(min(limit, 3))
            ]

        def delete(self, collection_name: str, points_selector):
            if collection_name in self.points:
                # Simple mock - just clear points
                self.points[collection_name] = []

    return MockQdrantClient()


@pytest.fixture
def mock_embedding_model():
    """Mock sentence transformer model"""
    import numpy as np

    class MockEmbeddingModel:
        def encode(self, texts, **kwargs):
            # Return mock embeddings (384 dimensions for all-MiniLM-L6-v2)
            if isinstance(texts, str):
                texts = [texts]
            return np.random.rand(len(texts), 384).astype('float32')

    return MockEmbeddingModel()
