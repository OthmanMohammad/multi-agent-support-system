"""
Unit of Work Pattern - Manages database transactions across repositories

The Unit of Work pattern ensures that multiple repository operations
happen within a single database transaction, providing ACID guarantees.

Usage:
    async with get_unit_of_work() as uow:
        customer = await uow.customers.create(...)
        conversation = await uow.conversations.create(...)
        # Transaction commits automatically on success
        # Rolls back automatically on exception
"""
from typing import Optional, AsyncContextManager
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from database.connection import get_db_session
from database.repositories import (
    CustomerRepository,
    ConversationRepository,
    MessageRepository,
    AgentPerformanceRepository
)


class UnitOfWork:
    """
    Unit of Work - Coordinates database operations in a single transaction
    
    Benefits:
    - Atomic operations (all succeed or all fail)
    - Consistent state across repositories
    - Automatic rollback on errors
    - Lazy repository initialization
    
    Attributes:
        session: Database session
        customers: Customer repository
        conversations: Conversation repository
        messages: Message repository
        agent_performance: Agent performance repository
    """
    
    def __init__(self, session: AsyncSession, current_user_id: Optional[UUID] = None):
        """
        Initialize Unit of Work
        
        Args:
            session: Async database session
            current_user_id: ID of user performing operations (for audit trail)
        """
        self.session = session
        self.current_user_id = current_user_id
        
        # Lazy-loaded repositories
        self._customer_repo: Optional[CustomerRepository] = None
        self._conversation_repo: Optional[ConversationRepository] = None
        self._message_repo: Optional[MessageRepository] = None
        self._agent_performance_repo: Optional[AgentPerformanceRepository] = None
    
    @property
    def customers(self) -> CustomerRepository:
        """Get customer repository (lazy-loaded)"""
        if self._customer_repo is None:
            self._customer_repo = CustomerRepository(self.session)
        return self._customer_repo
    
    @property
    def conversations(self) -> ConversationRepository:
        """Get conversation repository (lazy-loaded)"""
        if self._conversation_repo is None:
            self._conversation_repo = ConversationRepository(self.session)
        return self._conversation_repo
    
    @property
    def messages(self) -> MessageRepository:
        """Get message repository (lazy-loaded)"""
        if self._message_repo is None:
            self._message_repo = MessageRepository(self.session)
        return self._message_repo
    
    @property
    def agent_performance(self) -> AgentPerformanceRepository:
        """Get agent performance repository (lazy-loaded)"""
        if self._agent_performance_repo is None:
            self._agent_performance_repo = AgentPerformanceRepository(self.session)
        return self._agent_performance_repo
    
    async def commit(self):
        """Commit the current transaction"""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback the current transaction"""
        await self.session.rollback()
    
    async def flush(self):
        """
        Flush pending changes without committing
        Useful for getting auto-generated IDs
        """
        await self.session.flush()
    
    async def refresh(self, instance):
        """
        Refresh instance with latest data from database
        
        Args:
            instance: SQLAlchemy model instance
        """
        await self.session.refresh(instance)


@asynccontextmanager
async def get_unit_of_work(
    current_user_id: Optional[UUID] = None
) -> AsyncContextManager[UnitOfWork]:
    """
    Context manager for Unit of Work pattern
    
    Automatically commits on success, rolls back on exception.
    
    Args:
        current_user_id: ID of user performing operations (for audit)
    
    Usage:
        async with get_unit_of_work() as uow:
            customer = await uow.customers.create(...)
            conversation = await uow.conversations.create(...)
            # Commits automatically here
    
    Yields:
        UnitOfWork instance
    
    Raises:
        Exception: Any exception from nested operations (after rollback)
    """
    async with get_db_session() as session:
        uow = UnitOfWork(session, current_user_id)
        try:
            yield uow
            await uow.commit()
        except Exception as e:
            await uow.rollback()
            # Re-raise exception after rollback
            raise e


# Convenience function for backward compatibility
async def get_uow(current_user_id: Optional[UUID] = None) -> AsyncContextManager[UnitOfWork]:
    """Alias for get_unit_of_work"""
    return get_unit_of_work(current_user_id)


if __name__ == "__main__":
    import asyncio
    from uuid import uuid4
    
    async def test_unit_of_work():
        """Test Unit of Work pattern"""
        print("=" * 70)
        print("TESTING UNIT OF WORK")
        print("=" * 70)
        
        # Test successful transaction
        print("\n1. Testing successful transaction...")
        try:
            async with get_unit_of_work() as uow:
                customer = await uow.customers.create(
                    email=f"test_{uuid4().hex[:8]}@example.com",
                    name="Test User",
                    plan="free",
                    extra_metadata={}
                )
                print(f"   ✓ Customer created: {customer.email}")
                
                conversation = await uow.conversations.create_with_customer(
                    customer_id=customer.id
                )
                print(f"   ✓ Conversation created: {conversation.id}")
                
                # Transaction commits here
            
            print("   ✓ Transaction committed successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Test rollback on error
        print("\n2. Testing rollback on error...")
        try:
            async with get_unit_of_work() as uow:
                customer = await uow.customers.create(
                    email=f"test_{uuid4().hex[:8]}@example.com",
                    name="Test User 2",
                    plan="free",
                    extra_metadata={}
                )
                print(f"   ✓ Customer created: {customer.email}")
                
                # Simulate error
                raise ValueError("Simulated error")
        except ValueError:
            print("   ✓ Exception caught, transaction rolled back")
        
        print("\n✓ Unit of Work tests passed")
    
    asyncio.run(test_unit_of_work())