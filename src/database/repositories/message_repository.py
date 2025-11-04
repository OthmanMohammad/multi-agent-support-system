"""
Message repository - business logic for message data access
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select

from database.base import BaseRepository
from database.models import Message


class MessageRepository(BaseRepository[Message]):
    """Repository for message operations"""
    
    def __init__(self, session):
        super().__init__(Message, session)
    
    async def create_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        agent_name: str = None,
        **kwargs
    ) -> Message:
        """Create a new message in conversation"""
        return await self.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
            **kwargs
        )
    
    async def get_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100
    ) -> List[Message]:
        """Get all messages for a conversation"""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_latest_message(self, conversation_id: UUID) -> Optional[Message]:
        """Get the most recent message in conversation"""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()