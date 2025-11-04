"""
Agent performance repository - Track agent metrics
"""
from typing import List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
from sqlalchemy import select, and_, func

from database.base import BaseRepository
from database.models import AgentPerformance


class AgentPerformanceRepository(BaseRepository[AgentPerformance]):
    """Repository for agent performance metrics"""
    
    def __init__(self, session):
        super().__init__(AgentPerformance, session)
    
    async def record_daily_metrics(
        self,
        agent_name: str,
        date: datetime,
        **metrics
    ) -> AgentPerformance:
        """
        Record or update daily metrics for an agent
        Uses UPSERT pattern (update if exists, insert if not)
        
        Args:
            agent_name: Name of the agent
            date: Date for metrics
            **metrics: Metric values (total_interactions, successful_resolutions, etc.)
            
        Returns:
            AgentPerformance record
        """
        # Try to find existing record
        result = await self.session.execute(
            select(AgentPerformance).where(
                and_(
                    AgentPerformance.agent_name == agent_name,
                    AgentPerformance.date == date
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            for key, value in metrics.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new
            return await self.create(
                agent_name=agent_name,
                date=date,
                extra_metadata={},
                **metrics
            )
    
    async def get_agent_metrics(
        self,
        agent_name: str,
        days: int = 30
    ) -> List[AgentPerformance]:
        """
        Get metrics for specific agent over time
        
        Args:
            agent_name: Agent name
            days: Number of days to retrieve
            
        Returns:
            List of performance records
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        result = await self.session.execute(
            select(AgentPerformance)
            .where(
                and_(
                    AgentPerformance.agent_name == agent_name,
                    AgentPerformance.date >= since
                )
            )
            .order_by(AgentPerformance.date.desc())
        )
        return list(result.scalars().all())
    
    async def get_all_agents_summary(self, days: int = 7) -> dict:
        """
        Get summary stats for all agents
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with agent summaries
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        result = await self.session.execute(
            select(
                AgentPerformance.agent_name,
                func.sum(AgentPerformance.total_interactions).label('total'),
                func.sum(AgentPerformance.successful_resolutions).label('successes'),
                func.sum(AgentPerformance.escalations).label('escalations'),
                func.avg(AgentPerformance.avg_confidence).label('avg_conf'),
                func.avg(AgentPerformance.avg_sentiment).label('avg_sent')
            )
            .where(AgentPerformance.date >= since)
            .group_by(AgentPerformance.agent_name)
        )
        
        return {
            row.agent_name: {
                "total_interactions": int(row.total or 0),
                "successful_resolutions": int(row.successes or 0),
                "total_escalations": int(row.escalations or 0),
                "success_rate": round((row.successes / row.total * 100), 2) if row.total else 0.0,
                "avg_confidence": round(float(row.avg_conf), 2) if row.avg_conf else 0.0,
                "avg_sentiment": round(float(row.avg_sent), 2) if row.avg_sent else 0.0
            }
            for row in result
        }
    
    async def get_performance_trend(
        self,
        agent_name: str,
        days: int = 30
    ) -> List[dict]:
        """
        Get daily performance trend for agent
        
        Args:
            agent_name: Agent name
            days: Number of days
            
        Returns:
            List of daily metrics
        """
        metrics = await self.get_agent_metrics(agent_name, days)
        
        return [
            {
                "date": metric.date.date().isoformat(),
                "total_interactions": metric.total_interactions,
                "success_rate": metric.success_rate,
                "avg_confidence": metric.avg_confidence,
                "avg_sentiment": metric.avg_sentiment
            }
            for metric in reversed(metrics)  # Chronological order
        ]
    
    async def get_top_performers(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[AgentPerformance]:
        """
        Get top performing agents by success rate
        
        Args:
            days: Number of days to analyze
            limit: Maximum agents to return
            
        Returns:
            List of top performing agent records
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get aggregated data
        result = await self.session.execute(
            select(
                AgentPerformance.agent_name,
                func.sum(AgentPerformance.total_interactions).label('total'),
                func.sum(AgentPerformance.successful_resolutions).label('successes')
            )
            .where(AgentPerformance.date >= since)
            .group_by(AgentPerformance.agent_name)
            .having(func.sum(AgentPerformance.total_interactions) > 0)
        )
        
        # Calculate success rates and sort
        performers = []
        for row in result:
            success_rate = (row.successes / row.total * 100) if row.total else 0
            performers.append({
                "agent_name": row.agent_name,
                "total_interactions": row.total,
                "successful_resolutions": row.successes,
                "success_rate": round(success_rate, 2)
            })
        
        # Sort by success rate
        performers.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return performers[:limit]
    
    async def compare_agents(
        self,
        agent_names: List[str],
        days: int = 7
    ) -> dict:
        """
        Compare performance metrics between agents
        
        Args:
            agent_names: List of agent names to compare
            days: Number of days to analyze
            
        Returns:
            Dict with comparison data
        """
        since = datetime.utcnow() - timedelta(days=days)
        
        comparison = {}
        
        for agent_name in agent_names:
            result = await self.session.execute(
                select(
                    func.sum(AgentPerformance.total_interactions).label('total'),
                    func.sum(AgentPerformance.successful_resolutions).label('successes'),
                    func.sum(AgentPerformance.escalations).label('escalations'),
                    func.avg(AgentPerformance.avg_confidence).label('conf'),
                    func.avg(AgentPerformance.avg_sentiment).label('sent')
                )
                .where(
                    and_(
                        AgentPerformance.agent_name == agent_name,
                        AgentPerformance.date >= since
                    )
                )
            )
            
            row = result.one()
            
            comparison[agent_name] = {
                "total_interactions": int(row.total or 0),
                "successful_resolutions": int(row.successes or 0),
                "escalations": int(row.escalations or 0),
                "success_rate": round((row.successes / row.total * 100), 2) if row.total else 0.0,
                "avg_confidence": round(float(row.conf), 2) if row.conf else 0.0,
                "avg_sentiment": round(float(row.sent), 2) if row.sent else 0.0
            }
        
        return comparison