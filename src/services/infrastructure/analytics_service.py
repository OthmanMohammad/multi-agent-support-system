"""
Analytics Infrastructure Service - Data aggregation and metrics

This service aggregates data from repositories to provide statistics
and metrics. It's pure data retrieval and aggregation - no business logic.

Business logic for interpreting metrics belongs in domain services.

"""

from typing import Dict, Optional
from datetime import datetime, timedelta

from core.result import Result
from core.errors import InternalError
from database.unit_of_work import UnitOfWork
from utils.logging.setup import get_logger


class AnalyticsService:
    """
    Infrastructure service for analytics and metrics
    
    Responsibilities:
    - Aggregate data from repositories
    - Calculate statistics (counts, averages, distributions)
    - Return structured metrics
    
    NOT responsible for:
    - Interpreting metrics (domain service)
    - Making business decisions (domain service)
    - Recommendations (domain service)
    
    """
    
    def __init__(self, uow: UnitOfWork):
        """
        Initialize with Unit of Work
        
        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow
        self.logger = get_logger(__name__)
        
        self.logger.debug("analytics_service_initialized")
    
    async def get_conversation_statistics(
        self,
        days: int = 7
    ) -> Result[Dict]:
        """
        Get conversation statistics for period
        
        Simple aggregation from repository - no business logic.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Result with statistics dict
        """
        try:
            self.logger.debug(
                "conversation_statistics_requested",
                days=days
            )
            
            stats = await self.uow.conversations.get_statistics(days=days)
            
            self.logger.info(
                "conversation_statistics_retrieved",
                days=days,
                total_conversations=stats.get("total_conversations", 0)
            )
            return Result.ok(stats)
            
        except Exception as e:
            self.logger.error(
                "conversation_statistics_failed",
                days=days,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get conversation statistics: {str(e)}",
                operation="get_conversation_statistics",
                component="AnalyticsService"
            ))
    
    async def get_agent_performance(
        self,
        agent_name: str,
        days: int = 7
    ) -> Result[Dict]:
        """
        Get performance metrics for specific agent
        
        Args:
            agent_name: Agent name (router, billing, technical, etc.)
            days: Number of days to analyze
            
        Returns:
            Result with performance dict
        """
        try:
            self.logger.debug(
                "agent_performance_requested",
                agent_name=agent_name,
                days=days
            )
            
            metrics_list = await self.uow.agent_performance.get_agent_metrics(
                agent_name=agent_name,
                days=days
            )
            
            if not metrics_list:
                self.logger.info(
                    "agent_performance_no_data",
                    agent_name=agent_name,
                    days=days
                )
                return Result.ok({
                    "agent_name": agent_name,
                    "total_interactions": 0,
                    "successful_resolutions": 0,
                    "escalations": 0,
                    "avg_confidence": 0.0,
                    "avg_sentiment": 0.0,
                    "success_rate": 0.0
                })
            
            # Aggregate across days
            total_interactions = sum(m.total_interactions for m in metrics_list)
            successful_resolutions = sum(m.successful_resolutions for m in metrics_list)
            escalations = sum(m.escalations for m in metrics_list)
            
            # Calculate averages (weighted by interactions)
            weighted_confidence = sum(
                (m.avg_confidence or 0) * m.total_interactions 
                for m in metrics_list
            )
            weighted_sentiment = sum(
                (m.avg_sentiment or 0) * m.total_interactions 
                for m in metrics_list
            )
            
            avg_confidence = weighted_confidence / total_interactions if total_interactions > 0 else 0.0
            avg_sentiment = weighted_sentiment / total_interactions if total_interactions > 0 else 0.0
            success_rate = (successful_resolutions / total_interactions * 100) if total_interactions > 0 else 0.0
            
            performance = {
                "agent_name": agent_name,
                "total_interactions": total_interactions,
                "successful_resolutions": successful_resolutions,
                "escalations": escalations,
                "avg_confidence": round(avg_confidence, 2),
                "avg_sentiment": round(avg_sentiment, 2),
                "success_rate": round(success_rate, 2)
            }
            
            self.logger.info(
                "agent_performance_retrieved",
                agent_name=agent_name,
                total_interactions=total_interactions,
                success_rate=round(success_rate, 2)
            )
            return Result.ok(performance)
            
        except Exception as e:
            self.logger.error(
                "agent_performance_failed",
                agent_name=agent_name,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get agent performance: {str(e)}",
                operation="get_agent_performance",
                component="AnalyticsService"
            ))
    
    async def get_customer_satisfaction_scores(
        self,
        days: int = 30
    ) -> Result[Dict]:
        """Get customer satisfaction metrics based on sentiment"""
        try:
            self.logger.debug(
                "csat_scores_requested",
                days=days
            )
            
            since = datetime.utcnow() - timedelta(days=days)
            
            conversations = await self.uow.conversations.get_by_date_range(
                start_date=since,
                end_date=datetime.utcnow()
            )
            
            with_sentiment = [
                c for c in conversations 
                if c.sentiment_avg is not None
            ]
            
            if not with_sentiment:
                self.logger.info("csat_scores_no_data", days=days)
                return Result.ok({
                    "avg_sentiment": 0.0,
                    "positive_count": 0,
                    "neutral_count": 0,
                    "negative_count": 0,
                    "total_conversations": 0
                })
            
            avg_sentiment = sum(c.sentiment_avg for c in with_sentiment) / len(with_sentiment)
            
            positive_count = len([c for c in with_sentiment if c.sentiment_avg > 0.3])
            neutral_count = len([c for c in with_sentiment if -0.3 <= c.sentiment_avg <= 0.3])
            negative_count = len([c for c in with_sentiment if c.sentiment_avg < -0.3])
            
            scores = {
                "avg_sentiment": round(avg_sentiment, 2),
                "positive_count": positive_count,
                "neutral_count": neutral_count,
                "negative_count": negative_count,
                "total_conversations": len(with_sentiment)
            }
            
            self.logger.info(
                "csat_scores_retrieved",
                days=days,
                avg_sentiment=round(avg_sentiment, 2),
                total=len(with_sentiment)
            )
            return Result.ok(scores)
            
        except Exception as e:
            self.logger.error(
                "csat_scores_failed",
                days=days,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get CSAT scores: {str(e)}",
                operation="get_customer_satisfaction_scores",
                component="AnalyticsService"
            ))
    
    async def get_intent_distribution(
        self,
        days: int = 7
    ) -> Result[Dict[str, int]]:
        """Get distribution of intents"""
        try:
            stats = await self.uow.conversations.get_statistics(days=days)
            intent_dist = stats.get("by_intent", {})
            
            self.logger.info(
                "intent_distribution_retrieved",
                days=days,
                unique_intents=len(intent_dist)
            )
            return Result.ok(intent_dist)
            
        except Exception as e:
            self.logger.error(
                "intent_distribution_failed",
                days=days,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get intent distribution: {str(e)}",
                operation="get_intent_distribution",
                component="AnalyticsService"
            ))
    
    async def get_resolution_time_trends(
        self,
        days: int = 7
    ) -> Result[Dict]:
        """Get resolution time trends"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            conversations = await self.uow.conversations.get_by_date_range(
                start_date=since,
                end_date=datetime.utcnow()
            )
            
            resolved = [
                c for c in conversations
                if c.status == "resolved" and c.resolution_time_seconds is not None
            ]
            
            if not resolved:
                self.logger.info("resolution_time_trends_no_data", days=days)
                return Result.ok({
                    "avg_resolution_seconds": 0,
                    "min_resolution_seconds": 0,
                    "max_resolution_seconds": 0,
                    "median_resolution_seconds": 0
                })
            
            times = sorted([c.resolution_time_seconds for c in resolved])
            avg_time = sum(times) / len(times)
            median_time = times[len(times) // 2]
            
            trends = {
                "avg_resolution_seconds": int(avg_time),
                "min_resolution_seconds": min(times),
                "max_resolution_seconds": max(times),
                "median_resolution_seconds": median_time
            }
            
            self.logger.info(
                "resolution_time_trends_retrieved",
                days=days,
                avg_seconds=int(avg_time),
                resolved_count=len(resolved)
            )
            return Result.ok(trends)
            
        except Exception as e:
            self.logger.error(
                "resolution_time_trends_failed",
                days=days,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get resolution time trends: {str(e)}",
                operation="get_resolution_time_trends",
                component="AnalyticsService"
            ))
    
    async def get_escalation_rate(
        self,
        days: int = 7
    ) -> Result[Dict]:
        """Get escalation rate"""
        try:
            stats = await self.uow.conversations.get_statistics(days=days)
            
            total = stats.get("total_conversations", 0)
            by_status = stats.get("by_status", {})
            escalated = by_status.get("escalated", 0)
            
            escalation_rate = (escalated / total * 100) if total > 0 else 0.0
            
            result = {
                "escalated_count": escalated,
                "total_count": total,
                "escalation_rate": round(escalation_rate, 2)
            }
            
            self.logger.info(
                "escalation_rate_retrieved",
                days=days,
                escalation_rate=round(escalation_rate, 2),
                total=total
            )
            return Result.ok(result)
            
        except Exception as e:
            self.logger.error(
                "escalation_rate_failed",
                days=days,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get escalation rate: {str(e)}",
                operation="get_escalation_rate",
                component="AnalyticsService"
            ))
    
    async def get_kb_effectiveness(
        self,
        days: int = 7
    ) -> Result[Dict]:
        """Get KB usage metrics"""
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            conversations = await self.uow.conversations.get_by_date_range(
                start_date=since,
                end_date=datetime.utcnow()
            )
            
            total = len(conversations)
            with_kb = [
                c for c in conversations
                if c.kb_articles_used and len(c.kb_articles_used) > 0
            ]
            
            kb_usage_rate = (len(with_kb) / total * 100) if total > 0 else 0.0
            
            total_articles = sum(len(c.kb_articles_used) for c in with_kb)
            avg_articles = (total_articles / len(with_kb)) if with_kb else 0.0
            
            unique_articles = set()
            for c in with_kb:
                unique_articles.update(c.kb_articles_used)
            
            effectiveness = {
                "total_conversations": total,
                "conversations_with_kb": len(with_kb),
                "kb_usage_rate": round(kb_usage_rate, 2),
                "avg_articles_per_conversation": round(avg_articles, 2),
                "unique_articles_used": len(unique_articles)
            }
            
            self.logger.info(
                "kb_effectiveness_retrieved",
                days=days,
                kb_usage_rate=round(kb_usage_rate, 2),
                total=total
            )
            return Result.ok(effectiveness)
            
        except Exception as e:
            self.logger.error(
                "kb_effectiveness_failed",
                days=days,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get KB effectiveness: {str(e)}",
                operation="get_kb_effectiveness",
                component="AnalyticsService"
            ))
    
    async def track_agent_interaction(
        self,
        agent_name: str,
        success: bool,
        confidence: float
    ) -> Result[None]:
        """Track an agent interaction for analytics"""
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            existing = await self.uow.agent_performance.get_agent_metrics(
                agent_name=agent_name,
                days=1
            )
            
            if existing and existing[0].date.date() == today.date():
                metric = existing[0]
                await self.uow.agent_performance.update(
                    metric.id,
                    total_interactions=metric.total_interactions + 1,
                    successful_resolutions=metric.successful_resolutions + (1 if success else 0),
                    avg_confidence=(
                        (metric.avg_confidence * metric.total_interactions + confidence) / 
                        (metric.total_interactions + 1)
                    ) if metric.avg_confidence else confidence
                )
            else:
                await self.uow.agent_performance.record_daily_metrics(
                    agent_name=agent_name,
                    date=today,
                    total_interactions=1,
                    successful_resolutions=1 if success else 0,
                    escalations=0,
                    avg_confidence=confidence
                )
            
            self.logger.debug(
                "agent_interaction_tracked",
                agent_name=agent_name,
                success=success,
                confidence=round(confidence, 2)
            )
            return Result.ok(None)
            
        except Exception as e:
            self.logger.warning(
                "agent_interaction_tracking_failed",
                agent_name=agent_name,
                error=str(e)
            )
            return Result.ok(None)
    
    async def get_agent_comparison(
        self,
        days: int = 7
    ) -> Result[Dict]:
        """Compare performance across all agents"""
        try:
            summary = await self.uow.agent_performance.get_all_agents_summary(days=days)
            
            self.logger.info(
                "agent_comparison_retrieved",
                days=days,
                agent_count=len(summary)
            )
            return Result.ok(summary)
            
        except Exception as e:
            self.logger.error(
                "agent_comparison_failed",
                days=days,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get agent comparison: {str(e)}",
                operation="get_agent_comparison",
                component="AnalyticsService"
            ))