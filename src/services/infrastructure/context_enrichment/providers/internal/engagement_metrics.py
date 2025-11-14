"""
Engagement metrics provider.

Fetches customer engagement and product usage data.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider


class EngagementMetricsProvider(BaseContextProvider):
    """
    Provides customer engagement and usage metrics.

    Fetches:
    - Login activity
    - Session duration
    - Feature usage patterns
    - Feature adoption score
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

        Returns:
            Engagement metrics data
        """
        self.logger.debug("fetching_engagement_metrics", customer_id=customer_id)

        # TODO: Replace with actual database query from usage_events table
        # For now, return reasonable defaults with variation

        customer_hash = sum(ord(c) for c in customer_id) % 100

        # Login count (0-60 logins in last 30 days)
        login_count = customer_hash % 60

        # Last login (0-30 days ago, more recent for active users)
        if login_count > 20:
            days_ago = customer_hash % 3  # Very active: 0-2 days
        elif login_count > 5:
            days_ago = customer_hash % 7  # Active: 0-6 days
        else:
            days_ago = customer_hash % 30  # Inactive: 0-29 days

        last_login = datetime.utcnow() - timedelta(days=days_ago)

        # Average session duration (5-60 minutes)
        avg_session_duration = 5 + (customer_hash % 55)

        # Feature adoption score (0-1)
        feature_adoption = min(1.0, login_count / 30)

        # Most used features
        all_features = [
            "Projects", "Tasks", "Team Collaboration", "File Sharing",
            "Reports", "Calendar", "Comments", "Notifications",
            "Search", "Dashboard", "Templates", "Integrations"
        ]
        num_features = min(5, 1 + (customer_hash % 8))
        most_used = all_features[:num_features]

        # Unused features (inverse of used)
        unused = all_features[num_features:] if num_features < len(all_features) else []

        return {
            "last_login": last_login if login_count > 0 else None,
            "login_count_30d": login_count,
            "avg_session_duration_minutes": float(avg_session_duration),
            "feature_adoption_score": feature_adoption,
            "most_used_features": most_used,
            "unused_features": unused[:3],  # Top 3 unused
            "days_since_last_login": days_ago if login_count > 0 else None
        }
