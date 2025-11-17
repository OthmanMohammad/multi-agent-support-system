"""
Message repository - Business logic for message data access
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, and_, case
from datetime import datetime, timedelta, UTC

from src.database.base import BaseRepository
from src.database.models import Message


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
        """
        Create a new message in conversation
        
        Args:
            conversation_id: Conversation UUID
            role: Message role (user, assistant, system)
            content: Message content
            agent_name: Agent that sent message (optional)
            **kwargs: Additional message fields
            
        Returns:
            Created message
        """
        return await self.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
            extra_metadata={},
            **kwargs
        )
    
    async def get_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100
    ) -> List[Message]:
        """
        Get all messages for a conversation
        
        Args:
            conversation_id: Conversation UUID
            limit: Maximum messages to return
            
        Returns:
            List of messages in chronological order
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_latest_message(self, conversation_id: UUID) -> Optional[Message]:
        """
        Get the most recent message in conversation
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Latest message or None
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_by_agent(
        self,
        agent_name: str,
        limit: int = 100
    ) -> List[Message]:
        """
        Get all messages by specific agent
        
        Args:
            agent_name: Agent name
            limit: Maximum messages to return
            
        Returns:
            List of messages from agent
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.agent_name == agent_name)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_role(
        self,
        conversation_id: UUID,
        role: str
    ) -> List[Message]:
        """
        Get messages by role in a conversation
        
        Args:
            conversation_id: Conversation UUID
            role: Message role (user, assistant, system)
            
        Returns:
            List of messages with specified role
        """
        result = await self.session.execute(
            select(Message)
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.role == role
                )
            )
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
    
    async def get_sentiment_distribution(
        self,
        conversation_id: UUID
    ) -> dict:
        """
        Get sentiment breakdown for conversation
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Dict with sentiment distribution
        """
        result = await self.session.execute(
            select(
                func.count(case((Message.sentiment > 0.3, 1))).label('positive'),
                func.count(case((Message.sentiment < -0.3, 1))).label('negative'),
                func.count(case((
                    and_(Message.sentiment >= -0.3, Message.sentiment <= 0.3), 
                    1
                ))).label('neutral'),
                func.avg(Message.sentiment).label('average')
            )
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.sentiment.isnot(None)
                )
            )
        )
        
        row = result.one()
        return {
            "positive": row.positive or 0,
            "negative": row.negative or 0,
            "neutral": row.neutral or 0,
            "average": round(row.average, 2) if row.average else 0.0
        }
    
    async def get_average_confidence(
        self,
        conversation_id: UUID
    ) -> float:
        """
        Get average confidence score for conversation
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Average confidence (0-1)
        """
        result = await self.session.execute(
            select(func.avg(Message.confidence))
            .where(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.confidence.isnot(None)
                )
            )
        )
        avg = result.scalar()
        return round(float(avg), 2) if avg else 0.0
    
    async def get_token_usage(
        self,
        conversation_id: Optional[UUID] = None,
        days: int = 7
    ) -> dict:
        """
        Get token usage statistics
        
        Args:
            conversation_id: Optional conversation filter
            days: Number of days to analyze
            
        Returns:
            Dict with token statistics
        """
        since = datetime.now(UTC) - timedelta(days=days)
        
        query = select(
            func.sum(Message.tokens_used).label('total'),
            func.avg(Message.tokens_used).label('average'),
            func.count(Message.id).label('message_count')
        ).where(
            and_(
                Message.created_at >= since,
                Message.tokens_used.isnot(None)
            )
        )
        
        if conversation_id:
            query = query.where(Message.conversation_id == conversation_id)
        
        result = await self.session.execute(query)
        row = result.one()
        
        return {
            "total_tokens": int(row.total or 0),
            "average_tokens_per_message": round(float(row.average or 0), 2),
            "message_count": row.message_count or 0
        }
    
    async def search_content(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[Message]:
        """
        Search messages by content
        
        Args:
            search_term: Term to search for
            limit: Maximum results
            
        Returns:
            List of matching messages
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.content.ilike(f"%{search_term}%"))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())