"""
Analytics repository - Business logic for analytics data access
"""
from typing import Optional, List
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime, timedelta

from src.database.base import BaseRepository
from src.database.models import ConversationAnalytics, FeatureUsage, ABTest


class ConversationAnalyticsRepository(BaseRepository[ConversationAnalytics]):
    """Repository for conversation analytics operations"""

    def __init__(self, session):
        super().__init__(ConversationAnalytics, session)

    async def get_by_conversation(
        self,
        conversation_id: UUID
    ) -> Optional[ConversationAnalytics]:
        """Get analytics for a specific conversation"""
        result = await self.session.execute(
            select(ConversationAnalytics)
            .where(ConversationAnalytics.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[ConversationAnalytics]:
        """Get analytics for a date range"""
        result = await self.session.execute(
            select(ConversationAnalytics)
            .where(and_(
                ConversationAnalytics.conversation_date >= start_date,
                ConversationAnalytics.conversation_date <= end_date
            ))
            .order_by(ConversationAnalytics.conversation_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_average_resolution_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """Get average resolution time in seconds"""
        conditions = [ConversationAnalytics.resolution_time_seconds.isnot(None)]

        if start_date:
            conditions.append(ConversationAnalytics.conversation_date >= start_date)
        if end_date:
            conditions.append(ConversationAnalytics.conversation_date <= end_date)

        result = await self.session.execute(
            select(func.avg(ConversationAnalytics.resolution_time_seconds))
            .where(and_(*conditions))
        )
        return result.scalar() or 0.0

    async def get_escalation_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """Get escalation rate percentage"""
        conditions = []

        if start_date:
            conditions.append(ConversationAnalytics.conversation_date >= start_date)
        if end_date:
            conditions.append(ConversationAnalytics.conversation_date <= end_date)

        if conditions:
            total_result = await self.session.execute(
                select(func.count(ConversationAnalytics.id))
                .where(and_(*conditions))
            )
            escalated_result = await self.session.execute(
                select(func.count(ConversationAnalytics.id))
                .where(and_(
                    ConversationAnalytics.was_escalated == True,
                    *conditions
                ))
            )
        else:
            total_result = await self.session.execute(
                select(func.count(ConversationAnalytics.id))
            )
            escalated_result = await self.session.execute(
                select(func.count(ConversationAnalytics.id))
                .where(ConversationAnalytics.was_escalated == True)
            )

        total = total_result.scalar() or 0
        escalated = escalated_result.scalar() or 0

        return (escalated / total * 100) if total > 0 else 0.0


class FeatureUsageRepository(BaseRepository[FeatureUsage]):
    """Repository for feature usage operations"""

    def __init__(self, session):
        super().__init__(FeatureUsage, session)

    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 100
    ) -> List[FeatureUsage]:
        """Get feature usage for a customer"""
        result = await self.session.execute(
            select(FeatureUsage)
            .where(FeatureUsage.customer_id == customer_id)
            .order_by(FeatureUsage.first_used_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_feature(
        self,
        feature_name: str,
        limit: int = 100
    ) -> List[FeatureUsage]:
        """Get all usage records for a specific feature"""
        result = await self.session.execute(
            select(FeatureUsage)
            .where(FeatureUsage.feature_name == feature_name)
            .order_by(FeatureUsage.usage_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_feature_adoption_rate(
        self,
        feature_name: str
    ) -> float:
        """Get adoption rate for a feature"""
        # Total customers
        total_result = await self.session.execute(
            select(func.count(func.distinct(FeatureUsage.customer_id)))
        )
        total = total_result.scalar() or 0

        # Customers using this feature
        feature_result = await self.session.execute(
            select(func.count(func.distinct(FeatureUsage.customer_id)))
            .where(FeatureUsage.feature_name == feature_name)
        )
        adopters = feature_result.scalar() or 0

        return (adopters / total * 100) if total > 0 else 0.0

    async def get_top_features(
        self,
        limit: int = 10
    ) -> List[dict]:
        """Get most used features"""
        result = await self.session.execute(
            select(
                FeatureUsage.feature_name,
                func.sum(FeatureUsage.usage_count).label('total_usage'),
                func.count(func.distinct(FeatureUsage.customer_id)).label('unique_users')
            )
            .group_by(FeatureUsage.feature_name)
            .order_by(func.sum(FeatureUsage.usage_count).desc())
            .limit(limit)
        )

        return [
            {
                'feature_name': row.feature_name,
                'total_usage': row.total_usage,
                'unique_users': row.unique_users
            }
            for row in result
        ]


class ABTestRepository(BaseRepository[ABTest]):
    """Repository for A/B test operations"""

    def __init__(self, session):
        super().__init__(ABTest, session)

    async def get_by_customer(
        self,
        customer_id: UUID
    ) -> List[ABTest]:
        """Get all A/B tests for a customer"""
        result = await self.session.execute(
            select(ABTest)
            .where(ABTest.customer_id == customer_id)
            .order_by(ABTest.enrolled_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_test_name(
        self,
        test_name: str,
        limit: int = 1000
    ) -> List[ABTest]:
        """Get all participants in a specific test"""
        result = await self.session.execute(
            select(ABTest)
            .where(ABTest.test_name == test_name)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_variant(
        self,
        test_name: str,
        variant: str,
        limit: int = 1000
    ) -> List[ABTest]:
        """Get all participants in a specific variant"""
        result = await self.session.execute(
            select(ABTest)
            .where(and_(
                ABTest.test_name == test_name,
                ABTest.variant == variant
            ))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_test_results(
        self,
        test_name: str
    ) -> dict:
        """Get aggregated results for an A/B test"""
        result = await self.session.execute(
            select(
                ABTest.variant,
                func.count(ABTest.id).label('participants'),
                func.sum(ABTest.converted).label('conversions'),
                func.avg(ABTest.metric_value).label('avg_metric')
            )
            .where(ABTest.test_name == test_name)
            .group_by(ABTest.variant)
        )

        results = {}
        for row in result:
            conversion_rate = (row.conversions / row.participants * 100) if row.participants > 0 else 0.0
            results[row.variant] = {
                'participants': row.participants,
                'conversions': row.conversions,
                'conversion_rate': conversion_rate,
                'avg_metric': float(row.avg_metric) if row.avg_metric else 0.0
            }

        return results

    async def get_active_tests(self) -> List[str]:
        """Get list of active test names"""
        result = await self.session.execute(
            select(func.distinct(ABTest.test_name))
        )
        return [row[0] for row in result]
