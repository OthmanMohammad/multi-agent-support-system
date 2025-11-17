"""
Agent handoff and collaboration repository - Business logic for agent coordination data access
"""
from typing import Optional, List
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime, timedelta, UTC

from src.database.base import BaseRepository
from src.database.models import AgentHandoff, AgentCollaboration, ConversationTag


class AgentHandoffRepository(BaseRepository[AgentHandoff]):
    """Repository for agent handoff operations"""

    def __init__(self, session):
        super().__init__(AgentHandoff, session)

    async def get_by_conversation(
        self,
        conversation_id: UUID
    ) -> List[AgentHandoff]:
        """Get all handoffs for a conversation"""
        result = await self.session.execute(
            select(AgentHandoff)
            .where(AgentHandoff.conversation_id == conversation_id)
            .order_by(AgentHandoff.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_by_agent(
        self,
        agent_name: str,
        direction: str = 'both',
        limit: int = 100
    ) -> List[AgentHandoff]:
        """
        Get handoffs involving a specific agent

        Args:
            agent_name: Name of the agent
            direction: 'from', 'to', or 'both'
            limit: Maximum results
        """
        if direction == 'from':
            query = select(AgentHandoff).where(AgentHandoff.from_agent == agent_name)
        elif direction == 'to':
            query = select(AgentHandoff).where(AgentHandoff.to_agent == agent_name)
        else:  # both
            query = select(AgentHandoff).where(
                (AgentHandoff.from_agent == agent_name) | (AgentHandoff.to_agent == agent_name)
            )

        query = query.order_by(AgentHandoff.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_handoff_patterns(
        self,
        days: int = 30,
        limit: int = 20
    ) -> List[dict]:
        """Get most common handoff patterns"""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self.session.execute(
            select(
                AgentHandoff.from_agent,
                AgentHandoff.to_agent,
                func.count(AgentHandoff.id).label('count'),
                func.avg(AgentHandoff.latency_ms).label('avg_latency')
            )
            .where(AgentHandoff.timestamp >= cutoff)
            .group_by(AgentHandoff.from_agent, AgentHandoff.to_agent)
            .order_by(func.count(AgentHandoff.id).desc())
            .limit(limit)
        )

        return [
            {
                'from_agent': row.from_agent,
                'to_agent': row.to_agent,
                'count': row.count,
                'avg_latency_ms': float(row.avg_latency) if row.avg_latency else 0.0
            }
            for row in result
        ]

    async def get_average_handoff_time(
        self,
        agent_name: Optional[str] = None,
        days: Optional[int] = None
    ) -> float:
        """Get average handoff latency in milliseconds"""
        conditions = [AgentHandoff.latency_ms.isnot(None)]

        if agent_name:
            conditions.append(
                (AgentHandoff.from_agent == agent_name) | (AgentHandoff.to_agent == agent_name)
            )

        if days:
            cutoff = datetime.now(UTC) - timedelta(days=days)
            conditions.append(AgentHandoff.timestamp >= cutoff)

        result = await self.session.execute(
            select(func.avg(AgentHandoff.latency_ms))
            .where(and_(*conditions))
        )
        return result.scalar() or 0.0


class AgentCollaborationRepository(BaseRepository[AgentCollaboration]):
    """Repository for agent collaboration operations"""

    def __init__(self, session):
        super().__init__(AgentCollaboration, session)

    async def get_by_conversation(
        self,
        conversation_id: UUID
    ) -> List[AgentCollaboration]:
        """Get all collaborations for a conversation"""
        result = await self.session.execute(
            select(AgentCollaboration)
            .where(AgentCollaboration.conversation_id == conversation_id)
            .order_by(AgentCollaboration.start_time.asc())
        )
        return list(result.scalars().all())

    async def get_active_collaborations(
        self,
        limit: int = 100
    ) -> List[AgentCollaboration]:
        """Get currently active collaborations"""
        result = await self.session.execute(
            select(AgentCollaboration)
            .where(AgentCollaboration.end_time.is_(None))
            .order_by(AgentCollaboration.start_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self,
        collaboration_type: str,
        limit: int = 100
    ) -> List[AgentCollaboration]:
        """Get collaborations by type"""
        result = await self.session.execute(
            select(AgentCollaboration)
            .where(AgentCollaboration.collaboration_type == collaboration_type)
            .order_by(AgentCollaboration.start_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_agent(
        self,
        agent_name: str,
        limit: int = 100
    ) -> List[AgentCollaboration]:
        """Get collaborations involving a specific agent"""
        result = await self.session.execute(
            select(AgentCollaboration)
            .where(AgentCollaboration.agents_involved.contains([agent_name]))
            .order_by(AgentCollaboration.start_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_consensus_rate(
        self,
        collaboration_type: Optional[str] = None,
        days: Optional[int] = None
    ) -> float:
        """Get percentage of collaborations that reached consensus"""
        conditions = [AgentCollaboration.consensus_reached.isnot(None)]

        if collaboration_type:
            conditions.append(AgentCollaboration.collaboration_type == collaboration_type)

        if days:
            cutoff = datetime.now(UTC) - timedelta(days=days)
            conditions.append(AgentCollaboration.start_time >= cutoff)

        total_result = await self.session.execute(
            select(func.count(AgentCollaboration.id))
            .where(and_(*conditions))
        )
        total = total_result.scalar() or 0

        consensus_result = await self.session.execute(
            select(func.count(AgentCollaboration.id))
            .where(and_(
                AgentCollaboration.consensus_reached == True,
                *conditions
            ))
        )
        consensus = consensus_result.scalar() or 0

        return (consensus / total * 100) if total > 0 else 0.0


class ConversationTagRepository(BaseRepository[ConversationTag]):
    """Repository for conversation tag operations"""

    def __init__(self, session):
        super().__init__(ConversationTag, session)

    async def get_by_conversation(
        self,
        conversation_id: UUID
    ) -> List[ConversationTag]:
        """Get all tags for a conversation"""
        result = await self.session.execute(
            select(ConversationTag)
            .where(ConversationTag.conversation_id == conversation_id)
            .order_by(ConversationTag.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_tag(
        self,
        tag: str,
        limit: int = 100
    ) -> List[ConversationTag]:
        """Get all conversations with a specific tag"""
        result = await self.session.execute(
            select(ConversationTag)
            .where(ConversationTag.tag == tag)
            .order_by(ConversationTag.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(
        self,
        tag_category: str,
        limit: int = 100
    ) -> List[ConversationTag]:
        """Get tags by category"""
        result = await self.session.execute(
            select(ConversationTag)
            .where(ConversationTag.tag_category == tag_category)
            .order_by(ConversationTag.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_tag_distribution(
        self,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """Get distribution of tags"""
        query = select(
            ConversationTag.tag,
            func.count(ConversationTag.id).label('count'),
            func.avg(ConversationTag.confidence).label('avg_confidence')
        )

        if category:
            query = query.where(ConversationTag.tag_category == category)

        query = query.group_by(ConversationTag.tag).order_by(func.count(ConversationTag.id).desc()).limit(limit)

        result = await self.session.execute(query)

        return [
            {
                'tag': row.tag,
                'count': row.count,
                'avg_confidence': float(row.avg_confidence) if row.avg_confidence else 0.0
            }
            for row in result
        ]

    async def search_tags(
        self,
        pattern: str,
        limit: int = 50
    ) -> List[ConversationTag]:
        """Search tags by pattern"""
        result = await self.session.execute(
            select(ConversationTag)
            .where(ConversationTag.tag.like(f'%{pattern}%'))
            .order_by(ConversationTag.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
