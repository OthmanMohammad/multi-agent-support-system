"""
FastAPI dependencies for database access
Provides repository instances and Unit of Work to API endpoints
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from database.connection import get_db_session
from database.unit_of_work import UnitOfWork, get_unit_of_work as _get_uow
from database.repositories import (
    ConversationRepository,
    MessageRepository,
    CustomerRepository,
    AgentPerformanceRepository
)


# ===== CURRENT USER EXTRACTION =====

async def get_current_user_id(
    x_user_id: Optional[str] = Header(None)
) -> Optional[UUID]:
    """
    Extract current user ID from request headers
    
    This is a placeholder for proper authentication.
    In production, use JWT tokens or OAuth.
    
    Args:
        x_user_id: User ID from X-User-ID header
        
    Returns:
        User UUID or None
    """
    if x_user_id:
        try:
            return UUID(x_user_id)
        except ValueError:
            return None
    return None


# ===== UNIT OF WORK DEPENDENCY =====

async def get_uow(
    current_user_id: Optional[UUID] = Depends(get_current_user_id)
) -> AsyncGenerator[UnitOfWork, None]:
    """
    Dependency to get Unit of Work with automatic transaction management
    
    Usage:
        @app.post("/endpoint")
        async def endpoint(uow: UnitOfWork = Depends(get_uow)):
            customer = await uow.customers.create(...)
            conversation = await uow.conversations.create(...)
            # Transaction commits automatically
    
    Args:
        current_user_id: Current user ID from auth headers
    
    Yields:
        UnitOfWork instance with transaction management
    """
    async with _get_uow(current_user_id) as uow:
        yield uow


# ===== LEGACY DEPENDENCIES (Backward Compatibility) =====

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session (legacy)
    
    DEPRECATED: Use get_uow instead for better transaction management
    
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
    Dependency to get customer repository (legacy)
    
    DEPRECATED: Use get_uow().customers instead
    """
    return CustomerRepository(session)


async def get_conversation_repo(
    session: AsyncSession = Depends(get_db)
) -> ConversationRepository:
    """
    Dependency to get conversation repository (legacy)
    
    DEPRECATED: Use get_uow().conversations instead
    """
    return ConversationRepository(session)


async def get_message_repo(
    session: AsyncSession = Depends(get_db)
) -> MessageRepository:
    """
    Dependency to get message repository (legacy)
    
    DEPRECATED: Use get_uow().messages instead
    """
    return MessageRepository(session)


async def get_agent_performance_repo(
    session: AsyncSession = Depends(get_db)
) -> AgentPerformanceRepository:
    """
    Dependency to get agent performance repository (legacy)
    
    DEPRECATED: Use get_uow().agent_performance instead
    """
    return AgentPerformanceRepository(session)


# ===== COMPOSITE DEPENDENCY (Legacy) =====

class DatabaseRepositories:
    """
    Container for all repositories (legacy)
    
    DEPRECATED: Use UnitOfWork instead
    """
    
    def __init__(self, session: AsyncSession):
        self.customer = CustomerRepository(session)
        self.conversation = ConversationRepository(session)
        self.message = MessageRepository(session)
        self.agent_performance = AgentPerformanceRepository(session)


async def get_all_repos(
    session: AsyncSession = Depends(get_db)
) -> DatabaseRepositories:
    """
    Dependency to get all repositories at once (legacy)
    
    DEPRECATED: Use get_uow instead
    """
    return DatabaseRepositories(session)