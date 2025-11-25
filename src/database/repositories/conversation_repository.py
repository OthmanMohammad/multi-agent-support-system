"""
Conversation repository - Business logic for conversation data access
"""
from typing import List, Optional
from datetime import datetime, timedelta, UTC
from uuid import UUID
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from src.database.base import BaseRepository
from src.database.models import Conversation, Message


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation operations"""
    
    def __init__(self, session):
        super().__init__(Conversation, session)
    
    async def create_with_customer(
        self,
        customer_id: UUID,
        **kwargs
    ) -> Conversation:
        """
        Create conversation linked to customer
        
        Args:
            customer_id: Customer UUID
            **kwargs: Additional conversation fields
            
        Returns:
            Created conversation
        """
        return await self.create(
            customer_id=customer_id,
            agents_involved=[],
            kb_articles_used=[],
            extra_metadata={},
            **kwargs
        )
    
    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Conversation]:
        """
        Get all conversations for a customer
        
        Args:
            customer_id: Customer UUID
            limit: Maximum conversations to return
            status: Filter by status (optional)
            
        Returns:
            List of conversations
        """
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
        """
        Get conversation with all messages (eager loading)

        Args:
            conversation_id: Conversation UUID

        Returns:
            Conversation with messages or None
        """
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def get_with_customer(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Get conversation with customer relationship (eager loading)

        Args:
            conversation_id: Conversation UUID

        Returns:
            Conversation with customer loaded or None
        """
        from src.database.models import Customer
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.customer))
        )
        return result.scalar_one_or_none()
    
    async def mark_resolved(
        self,
        conversation_id: UUID,
        resolution_time_seconds: int
    ) -> Optional[Conversation]:
        """
        Mark conversation as resolved
        
        Args:
            conversation_id: Conversation UUID
            resolution_time_seconds: Time to resolution
            
        Returns:
            Updated conversation or None
        """
        return await self.update(
            conversation_id,
            status="resolved",
            ended_at=datetime.now(UTC),
            resolution_time_seconds=resolution_time_seconds
        )
    
    async def mark_escalated(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Mark conversation as escalated to human
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Updated conversation or None
        """
        return await self.update(
            conversation_id,
            status="escalated",
            ended_at=datetime.now(UTC)
        )
    
    async def search_by_intent(
        self,
        intent: str,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Find conversations by intent
        
        Args:
            intent: Intent category
            limit: Maximum results
            
        Returns:
            List of conversations
        """
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.primary_intent == intent)
            .order_by(Conversation.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        customer_id: Optional[UUID] = None
    ) -> List[Conversation]:
        """
        Get conversations within date range
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            customer_id: Optional customer filter
            
        Returns:
            List of conversations
        """
        query = select(Conversation).where(
            and_(
                Conversation.started_at >= start_date,
                Conversation.started_at <= end_date
            )
        )
        
        if customer_id:
            query = query.where(Conversation.customer_id == customer_id)
        
        query = query.order_by(Conversation.started_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_unresolved_conversations(
        self,
        hours_old: int = 24
    ) -> List[Conversation]:
        """
        Get active conversations older than X hours
        
        Args:
            hours_old: Minimum age in hours
            
        Returns:
            List of unresolved conversations
        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours_old)
        
        result = await self.session.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.status == "active",
                    Conversation.started_at < cutoff
                )
            )
            .order_by(Conversation.started_at.asc())
        )
        return list(result.scalars().all())
    
    async def get_statistics(self, days: int = 7) -> dict:
        """
        Get conversation statistics for last N days
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Statistics dictionary
        """
        since = datetime.now(UTC) - timedelta(days=days)
        
        # Total conversations
        total_result = await self.session.execute(
            select(func.count(Conversation.id))
            .where(Conversation.started_at >= since)
        )
        total_conversations = total_result.scalar()
        
        # By status
        status_result = await self.session.execute(
            select(
                Conversation.status,
                func.count(Conversation.id)
            )
            .where(Conversation.started_at >= since)
            .group_by(Conversation.status)
        )
        by_status = {row[0]: row[1] for row in status_result}
        
        # By intent
        intent_result = await self.session.execute(
            select(
                Conversation.primary_intent,
                func.count(Conversation.id)
            )
            .where(
                and_(
                    Conversation.started_at >= since,
                    Conversation.primary_intent.isnot(None)
                )
            )
            .group_by(Conversation.primary_intent)
        )
        by_intent = {row[0]: row[1] for row in intent_result}
        
        # Average resolution time
        avg_resolution_result = await self.session.execute(
            select(func.avg(Conversation.resolution_time_seconds))
            .where(
                and_(
                    Conversation.started_at >= since,
                    Conversation.resolution_time_seconds.isnot(None)
                )
            )
        )
        avg_resolution_time = avg_resolution_result.scalar() or 0
        
        # Average sentiment
        avg_sentiment_result = await self.session.execute(
            select(func.avg(Conversation.sentiment_avg))
            .where(
                and_(
                    Conversation.started_at >= since,
                    Conversation.sentiment_avg.isnot(None)
                )
            )
        )
        avg_sentiment = avg_sentiment_result.scalar() or 0
        
        return {
            "total_conversations": total_conversations,
            "by_status": by_status,
            "by_intent": by_intent,
            "avg_resolution_time_seconds": int(avg_resolution_time),
            "avg_sentiment": round(float(avg_sentiment), 2)
        }
    
    async def get_agent_usage_stats(self, days: int = 7) -> dict:
        """
        Get statistics on which agents are used most
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with agent usage counts
        """
        since = datetime.now(UTC) - timedelta(days=days)
        
        result = await self.session.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.started_at >= since,
                    Conversation.agents_involved.isnot(None)
                )
            )
        )
        conversations = result.scalars().all()
        
        # Count agent usage
        agent_counts = {}
        for conv in conversations:
            for agent in conv.agents_involved or []:
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        return agent_counts