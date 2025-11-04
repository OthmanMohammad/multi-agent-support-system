"""
FastAPI dependencies for database access
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db_session
from database.repositories.conversation_repository import ConversationRepository
from database.repositories.message_repository import MessageRepository
from database.repositories.customer_repository import CustomerRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with get_db_session() as session:
        yield session


async def get_conversation_repo(
    session: AsyncSession = Depends(get_db)
) -> ConversationRepository:
    """Dependency to get conversation repository"""
    return ConversationRepository(session)


async def get_message_repo(
    session: AsyncSession = Depends(get_db)
) -> MessageRepository:
    """Dependency to get message repository"""
    return MessageRepository(session)


async def get_customer_repo(
    session: AsyncSession = Depends(get_db)
) -> CustomerRepository:
    """Dependency to get customer repository"""
    return CustomerRepository(session)