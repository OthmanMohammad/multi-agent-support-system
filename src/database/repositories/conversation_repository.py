"""
Conversation repository - business logic for conversation data access
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.base import BaseRepository
from database.models import Conversation


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation operations"""
    
    def __init__(self, session):
        super().__init__(Conversation, session)
    
    async def create_with_customer(
        self,
        customer_id: UUID,
        **kwargs
    ) -> Conversation:
        """Create conversation linked to customer"""
        return await self.create(customer_id=customer_id, **kwargs)
    
    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Conversation]:
        """Get all conversations for a customer"""
        query = (
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .order_by(Conversation.started_at.desc())
            .limit(limit)
        )
        
        if status:
            query = query.where(Conversation.status == status)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_with_messages(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation with all messages (eager loading)"""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()
    
    async def mark_resolved(
        self,
        conversation_id: UUID,
        resolution_time_seconds: int
    ) -> Optional[Conversation]:
        """Mark conversation as resolved"""
        return await self.update(
            conversation_id,
            status="resolved",
            ended_at=datetime.utcnow(),
            resolution_time_seconds=resolution_time_seconds
        )
    
    async def mark_escalated(self, conversation_id: UUID) -> Optional[Conversation]:
        """Mark conversation as escalated to human"""
        return await self.update(
            conversation_id,
            status="escalated",
            ended_at=datetime.utcnow()
        )