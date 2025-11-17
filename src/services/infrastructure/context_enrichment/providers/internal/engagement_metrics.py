"""
Engagement metrics provider.

Fetches customer engagement and product usage data from database.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, UTC
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider
from src.database.models import UsageEvent, FeatureUsage
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session


class EngagementMetricsProvider(BaseContextProvider):
    """
    Provides customer engagement and usage metrics.

    Fetches:
    - Login activity (last login, login frequency)
    - Session duration
    - Feature usage patterns
    - Feature adoption score
    - Most/least used features
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch engagement metrics from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            **kwargs: Additional parameters

        Returns:
            Engagement metrics data
        """
        self.logger.debug("fetching_engagement_metrics", customer_id=customer_id)

        try:
            cust_uuid = UUID(customer_id)
        except (ValueError, AttributeError):
            self.logger.error("invalid_customer_id", customer_id=customer_id)
            return self._get_fallback_data()

        session = kwargs.get("session")
        if session:
            return await self._fetch_with_session(cust_uuid, session)
        else:
            async for session in get_db_session():
                return await self._fetch_with_session(cust_uuid, session)

    async def _fetch_with_session(
        self,
        customer_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Fetch engagement metrics using provided session"""
        try:
            uow = UnitOfWork(session)

            # Fetch usage events for last 30 days
            cutoff_date = datetime.now(UTC) - timedelta(days=30)
            usage_events = await uow.usage_events.find_by(customer_id=customer_id)

            # Filter to last 30 days
            recent_events = [
                event for event in usage_events
                if hasattr(event, 'created_at') and
                   event.created_at.replace(tzinfo=None) > cutoff_date
            ]

            # Count login events
            login_events = [
                event for event in recent_events
                if hasattr(event, 'event_type') and event.event_type == 'login'
            ]
            login_count = len(login_events)

            # Get last login
            if login_events:
                last_login = max(
                    event.created_at for event in login_events
                    if hasattr(event, 'created_at')
                )
                days_since = (datetime.now(UTC) - last_login.replace(tzinfo=None)).days
            else:
                last_login = None
                days_since = None

            # Calculate average session duration
            session_durations = []
            for event in recent_events:
                if hasattr(event, 'extra_metadata') and event.extra_metadata:
                    duration = event.extra_metadata.get('session_duration_minutes')
                    if duration:
                        session_durations.append(float(duration))

            avg_session_duration = (
                sum(session_durations) / len(session_durations)
                if session_durations else 0.0
            )

            # Fetch feature usage
            feature_usage = await uow.feature_usage.find_by(customer_id=customer_id)

            # Filter to last 30 days
            recent_features = [
                fu for fu in feature_usage
                if hasattr(fu, 'date') and
                   fu.date.replace(tzinfo=None) > cutoff_date
            ]

            # Aggregate feature usage by feature name
            feature_counts = {}
            for fu in recent_features:
                if hasattr(fu, 'feature_name') and hasattr(fu, 'usage_count'):
                    name = fu.feature_name
                    count = fu.usage_count
                    feature_counts[name] = feature_counts.get(name, 0) + count

            # Sort by usage
            sorted_features = sorted(
                feature_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )

            most_used = [name for name, count in sorted_features[:5]]

            # Calculate feature adoption score (# features used / total available)
            total_available_features = 20  # Assume 20 features available
            features_used = len(feature_counts)
            feature_adoption = min(1.0, features_used / total_available_features)

            # Identify unused premium features
            all_premium_features = [
                "advanced_analytics", "custom_reports", "api_access",
                "webhooks", "sso", "audit_logs", "priority_support"
            ]
            unused_features = [
                feat for feat in all_premium_features
                if feat not in feature_counts
            ]

            return {
                "last_login": last_login,
                "login_count_30d": login_count,
                "avg_session_duration_minutes": round(avg_session_duration, 1),
                "feature_adoption_score": round(feature_adoption, 2),
                "most_used_features": most_used,
                "unused_features": unused_features[:3],
                "days_since_last_login": days_since,
            }

        except Exception as e:
            self.logger.error(
                "fetch_failed",
                customer_id=str(customer_id),
                error=str(e),
                error_type=type(e).__name__
            )
            return self._get_fallback_data()

    def _get_fallback_data(self) -> Dict[str, Any]:
        """Get fallback data when query fails"""
        return {
            "last_login": None,
            "login_count_30d": 0,
            "avg_session_duration_minutes": 0.0,
            "feature_adoption_score": 0.0,
            "most_used_features": [],
            "unused_features": [],
            "days_since_last_login": None,
        }
