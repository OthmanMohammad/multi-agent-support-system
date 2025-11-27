"""
Test script for all repositories
Can be run with pytest or directly with Python

Note: These tests use global database connections which conflict with
pytest-asyncio event loop isolation. Skip in CI until proper fixtures are added.
"""
import asyncio
from datetime import datetime, timedelta, UTC
from uuid import uuid4
import pytest

from src.database.connection import get_db_session, init_db, close_db
from src.database.repositories import (
    CustomerRepository,
    ConversationRepository,
    MessageRepository,
    AgentPerformanceRepository
)


# Skip all tests - global database connections conflict with pytest-asyncio event loops
pytestmark = pytest.mark.skip(
    reason="Database tests use global connections that conflict with pytest-asyncio event loop isolation"
)


@pytest.mark.asyncio
async def test_customer_repository():
    """Test customer repository operations"""
    print("\n" + "=" * 70)
    print("TESTING CUSTOMER REPOSITORY")
    print("=" * 70)
    
    async with get_db_session() as session:
        repo = CustomerRepository(session)
        
        # Create
        print("\n1. Creating customer...")
        customer = await repo.create(
            email=f"test_{uuid4().hex[:8]}@example.com",
            name="Test User",
            plan="premium",
            extra_metadata={"source": "test"}
        )
        print(f"   ✓ Created: {customer.email}")
        assert customer.email is not None
        assert customer.plan == "premium"
        
        # Get by ID
        print("\n2. Getting by ID...")
        retrieved = await repo.get_by_id(customer.id)
        print(f"   ✓ Retrieved: {retrieved.email}")
        assert retrieved is not None
        assert retrieved.id == customer.id
        
        # Get by email
        print("\n3. Getting by email...")
        by_email = await repo.get_by_email(customer.email)
        print(f"   ✓ Found: {by_email.name}")
        assert by_email is not None
        assert by_email.email == customer.email
        
        # Get or create
        print("\n4. Testing get_or_create...")
        existing = await repo.get_or_create_by_email(customer.email)
        print(f"   ✓ Found existing: {existing.id == customer.id}")
        assert existing.id == customer.id
        
        # Upgrade plan
        print("\n5. Upgrading plan...")
        upgraded = await repo.upgrade_plan(customer.id, "enterprise")
        print(f"   ✓ New plan: {upgraded.plan}")
        assert upgraded.plan == "enterprise"
        
        # Get plan distribution
        print("\n6. Getting plan distribution...")
        distribution = await repo.get_plan_distribution()
        print(f"   ✓ Distribution: {distribution}")
        assert isinstance(distribution, dict)
        
        # Cleanup
        deleted = await repo.delete(customer.id)
        assert deleted is True
        print("\n✓ Customer tests passed")


@pytest.mark.asyncio
async def test_conversation_repository():
    """Test conversation repository operations"""
    print("\n" + "=" * 70)
    print("TESTING CONVERSATION REPOSITORY")
    print("=" * 70)
    
    async with get_db_session() as session:
        customer_repo = CustomerRepository(session)
        conv_repo = ConversationRepository(session)
        
        # Create test customer
        customer = await customer_repo.create(
            email=f"test_{uuid4().hex[:8]}@example.com",
            name="Conv Test User",
            plan="free",
            extra_metadata={}
        )
        
        # Create conversation
        print("\n1. Creating conversation...")
        conversation = await conv_repo.create_with_customer(
            customer_id=customer.id,
            status="active",
            primary_intent="billing_upgrade"
        )
        print(f"   ✓ Created: {conversation.id}")
        assert conversation.id is not None
        assert conversation.status == "active"
        
        # Get by customer
        print("\n2. Getting conversations by customer...")
        conversations = await conv_repo.get_by_customer(customer.id)
        print(f"   ✓ Found: {len(conversations)} conversations")
        assert len(conversations) >= 1
        
        # Search by intent
        print("\n3. Searching by intent...")
        by_intent = await conv_repo.search_by_intent("billing_upgrade")
        print(f"   ✓ Found: {len(by_intent)} conversations")
        assert len(by_intent) >= 1
        
        # Mark resolved
        print("\n4. Marking as resolved...")
        resolved = await conv_repo.mark_resolved(conversation.id, 120)
        print(f"   ✓ Status: {resolved.status}, Time: {resolved.resolution_time_seconds}s")
        assert resolved.status == "resolved"
        assert resolved.resolution_time_seconds == 120
        
        # Get statistics
        print("\n5. Getting statistics...")
        stats = await conv_repo.get_statistics(days=7)
        print(f"   ✓ Total: {stats['total_conversations']}")
        print(f"   ✓ By status: {stats['by_status']}")
        assert stats['total_conversations'] >= 0
        assert isinstance(stats['by_status'], dict)
        
        # Cleanup
        await conv_repo.delete(conversation.id)
        await customer_repo.delete(customer.id)
        print("\n✓ Conversation tests passed")


@pytest.mark.asyncio
async def test_message_repository():
    """Test message repository operations"""
    print("\n" + "=" * 70)
    print("TESTING MESSAGE REPOSITORY")
    print("=" * 70)
    
    async with get_db_session() as session:
        customer_repo = CustomerRepository(session)
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)
        
        # Setup
        customer = await customer_repo.create(
            email=f"test_{uuid4().hex[:8]}@example.com",
            name="Msg Test User",
            plan="free",
            extra_metadata={}
        )
        conversation = await conv_repo.create_with_customer(customer_id=customer.id)
        
        # Create message
        print("\n1. Creating message...")
        message = await msg_repo.create_message(
            conversation_id=conversation.id,
            role="user",
            content="Hello, I need help",
            sentiment=0.5,
            confidence=0.9
        )
        print(f"   ✓ Created: {message.content[:30]}...")
        assert message.id is not None
        assert message.role == "user"
        
        # Create agent response
        response = await msg_repo.create_message(
            conversation_id=conversation.id,
            role="assistant",
            content="I'm happy to help you!",
            agent_name="router",
            sentiment=0.8,
            confidence=0.95
        )
        assert response.role == "assistant"
        
        # Get by conversation
        print("\n2. Getting messages by conversation...")
        messages = await msg_repo.get_by_conversation(conversation.id)
        print(f"   ✓ Found: {len(messages)} messages")
        assert len(messages) == 2
        
        # Get latest message
        print("\n3. Getting latest message...")
        latest = await msg_repo.get_latest_message(conversation.id)
        print(f"   ✓ Latest: {latest.content[:30]}...")
        assert latest is not None
        assert latest.role == "assistant"
        
        # Get sentiment distribution
        print("\n4. Getting sentiment distribution...")
        sentiment = await msg_repo.get_sentiment_distribution(conversation.id)
        print(f"   ✓ Average: {sentiment['average']}")
        assert 'average' in sentiment
        
        # Get by agent
        print("\n5. Getting messages by agent...")
        by_agent = await msg_repo.get_by_agent("router")
        print(f"   ✓ Found: {len(by_agent)} messages from router")
        assert len(by_agent) >= 1
        
        # Cleanup
        await conv_repo.delete(conversation.id)
        await customer_repo.delete(customer.id)
        print("\n✓ Message tests passed")


@pytest.mark.asyncio
async def test_agent_performance_repository():
    """Test agent performance repository operations"""
    print("\n" + "=" * 70)
    print("TESTING AGENT PERFORMANCE REPOSITORY")
    print("=" * 70)
    
    async with get_db_session() as session:
        repo = AgentPerformanceRepository(session)
        
        # Record metrics
        print("\n1. Recording daily metrics...")
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        
        metrics = await repo.record_daily_metrics(
            agent_name="billing",
            date=today,
            total_interactions=100,
            successful_resolutions=85,
            escalations=5,
            avg_confidence=0.92,
            avg_sentiment=0.7
        )
        print(f"   ✓ Recorded: {metrics.agent_name} - {metrics.success_rate}% success")
        assert metrics.agent_name == "billing"
        assert metrics.total_interactions == 100
        
        # Update existing
        print("\n2. Updating metrics...")
        updated = await repo.record_daily_metrics(
            agent_name="billing",
            date=today,
            total_interactions=150,
            successful_resolutions=130
        )
        print(f"   ✓ Updated: {updated.total_interactions} interactions")
        assert updated.total_interactions == 150
        
        # Get agent metrics
        print("\n3. Getting agent metrics...")
        agent_metrics = await repo.get_agent_metrics("billing", days=30)
        print(f"   ✓ Found: {len(agent_metrics)} records")
        assert len(agent_metrics) >= 1
        
        # Get all agents summary
        print("\n4. Getting summary for all agents...")
        summary = await repo.get_all_agents_summary(days=7)
        print(f"   ✓ Agents: {list(summary.keys())}")
        assert isinstance(summary, dict)
        
        # Cleanup
        await repo.delete(metrics.id)
        print("\n✓ Agent performance tests passed")


# Pytest fixtures
@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Setup database before tests"""
    await init_db()
    yield
    await close_db()


# Main function for direct execution
async def main():
    """Run all repository tests directly (non-pytest)"""
    print("=" * 70)
    print("REPOSITORY TEST SUITE")
    print("=" * 70)
    
    try:
        # Initialize database
        await init_db()
        
        # Run tests
        await test_customer_repository()
        await test_conversation_repository()
        await test_message_repository()
        await test_agent_performance_repository()
        
        print("\n" + "=" * 70)
        print("✓ ALL REPOSITORY TESTS PASSED")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_db()


if __name__ == "__main__":
    # Run directly with Python (not pytest)
    asyncio.run(main())