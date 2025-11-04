"""
FastAPI dependencies for database access
Provides repository instances to API endpoints via dependency injection
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db_session
from database.repositories import (
    ConversationRepository,
    MessageRepository,
    CustomerRepository,
    AgentPerformanceRepository
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(session: AsyncSession = Depends(get_db)):
            # Use session
    
    Yields:
        Async database session
    """
    async with get_db_session() as session:
        yield session


async def get_customer_repo(
    session: AsyncSession = Depends(get_db)
) -> CustomerRepository:
    """
    Dependency to get customer repository
    
    Usage:
        @app.get("/customers")
        async def get_customers(
            repo: CustomerRepository = Depends(get_customer_repo)
        ):
            return await repo.get_all()
    
    Returns:
        CustomerRepository instance
    """
    return CustomerRepository(session)


async def get_conversation_repo(
    session: AsyncSession = Depends(get_db)
) -> ConversationRepository:
    """
    Dependency to get conversation repository
    
    Returns:
        ConversationRepository instance
    """
    return ConversationRepository(session)


async def get_message_repo(
    session: AsyncSession = Depends(get_db)
) -> MessageRepository:
    """
    Dependency to get message repository
    
    Returns:
        MessageRepository instance
    """
    return MessageRepository(session)


async def get_agent_performance_repo(
    session: AsyncSession = Depends(get_db)
) -> AgentPerformanceRepository:
    """
    Dependency to get agent performance repository
    
    Returns:
        AgentPerformanceRepository instance
    """
    return AgentPerformanceRepository(session)


# Optional: Create a composite dependency that provides all repos at once
class DatabaseRepositories:
    """Container for all repositories"""
    
    def __init__(self, session: AsyncSession):
        self.customer = CustomerRepository(session)
        self.conversation = ConversationRepository(session)
        self.message = MessageRepository(session)
        self.agent_performance = AgentPerformanceRepository(session)


async def get_all_repos(
    session: AsyncSession = Depends(get_db)
) -> DatabaseRepositories:
    """
    Dependency to get all repositories at once
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(repos: DatabaseRepositories = Depends(get_all_repos)):
            customer = await repos.customer.get_by_id(id)
            conversations = await repos.conversation.get_by_customer(customer.id)
    
    Returns:
        DatabaseRepositories with all repository instances
    """
    return DatabaseRepositories(session)