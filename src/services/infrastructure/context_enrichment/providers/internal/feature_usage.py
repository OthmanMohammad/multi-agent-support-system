"""
Feature usage provider.

Fetches detailed feature adoption and usage patterns from database.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider
from src.database.models import FeatureUsage
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session


class FeatureUsageProvider(BaseContextProvider):
    """
    Provides detailed feature usage and adoption patterns.

    Fetches:
    - Daily/weekly active features
    - Feature adoption rate
    - Power user count
    - Feature details (usage counts, trends, last used)
    - Adoption opportunities
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch feature usage from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            **kwargs: Additional parameters

        Returns:
            Feature usage data
        """
        self.logger.debug("fetching_feature_usage", customer_id=customer_id)

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
        """Fetch feature usage using provided session"""
        try:
            uow = UnitOfWork(session)

            # Fetch feature usage
            all_usage = await uow.feature_usage.find_by(customer_id=customer_id)

            if not all_usage:
                return self._get_fallback_data()

            # Calculate daily active features (last 24 hours)
            daily_cutoff = datetime.now(UTC) - timedelta(days=1)
            daily_features = set()
            for usage in all_usage:
                if (hasattr(usage, 'last_used_at') and usage.last_used_at and
                    usage.last_used_at.replace(tzinfo=None) > daily_cutoff):
                    if hasattr(usage, 'feature_name'):
                        daily_features.add(usage.feature_name)

            daily_active_features = len(daily_features)

            # Calculate weekly active features (last 7 days)
            weekly_cutoff = datetime.now(UTC) - timedelta(days=7)
            weekly_features = set()
            for usage in all_usage:
                if (hasattr(usage, 'last_used_at') and usage.last_used_at and
                    usage.last_used_at.replace(tzinfo=None) > weekly_cutoff):
                    if hasattr(usage, 'feature_name'):
                        weekly_features.add(usage.feature_name)

            weekly_active_features = len(weekly_features)

            # Aggregate usage by feature (last 30 days)
            monthly_cutoff = datetime.now(UTC) - timedelta(days=30)
            feature_stats = {}

            for usage in all_usage:
                if (hasattr(usage, 'date') and usage.date and
                    usage.date.replace(tzinfo=None) > monthly_cutoff):
                    name = usage.feature_name if hasattr(usage, 'feature_name') else "unknown"
                    count = usage.usage_count if hasattr(usage, 'usage_count') else 0
                    last_used = usage.last_used_at if hasattr(usage, 'last_used_at') else None

                    if name not in feature_stats:
                        feature_stats[name] = {
                            "usage_count_30d": 0,
                            "last_used": None,
                        }

                    feature_stats[name]["usage_count_30d"] += count
                    if last_used and (
                        not feature_stats[name]["last_used"] or
                        last_used > feature_stats[name]["last_used"]
                    ):
                        feature_stats[name]["last_used"] = last_used

            # Calculate feature adoption rate
            total_available = 20  # Assume 20 features total
            adopted_features = len(feature_stats)
            adoption_rate = adopted_features / total_available if total_available > 0 else 0.0

            # Identify power users (features used > 100 times/month)
            power_user_threshold = 100
            power_user_features = sum(
                1 for stats in feature_stats.values()
                if stats["usage_count_30d"] > power_user_threshold
            )

            # Build detailed feature list
            feature_details: List[Dict[str, Any]] = []
            for name, stats in sorted(
                feature_stats.items(),
                key=lambda x: x[1]["usage_count_30d"],
                reverse=True
            ):
                # Calculate trend (simple: compare to previous period)
                # For now, mark as "stable" - would need historical data for real trends
                trend = "stable"
                if stats["usage_count_30d"] > 200:
                    trend = "increasing"
                elif stats["usage_count_30d"] < 10:
                    trend = "decreasing"

                feature_details.append({
                    "feature": name,
                    "usage_count_30d": stats["usage_count_30d"],
                    "last_used": stats["last_used"],
                    "trend": trend,
                })

            # Identify adoption opportunities (high-value features not being used)
            all_premium_features = [
                ("advanced_analytics", "high"),
                ("custom_reports", "high"),
                ("api_access", "high"),
                ("webhooks", "medium"),
                ("sso", "medium"),
                ("audit_logs", "medium"),
                ("white_labeling", "high"),
            ]

            unused_premium = [
                f"{name} ({value} value)"
                for name, value in all_premium_features
                if name not in feature_stats
            ]

            return {
                "daily_active_features": daily_active_features,
                "weekly_active_features": weekly_active_features,
                "feature_adoption_rate": round(adoption_rate, 2),
                "power_user_count": power_user_features,
                "feature_details": feature_details[:10],  # Top 10
                "adoption_opportunities": unused_premium[:3],  # Top 3
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
            "daily_active_features": 0,
            "weekly_active_features": 0,
            "feature_adoption_rate": 0.0,
            "power_user_count": 0,
            "feature_details": [],
            "adoption_opportunities": [],
        }
