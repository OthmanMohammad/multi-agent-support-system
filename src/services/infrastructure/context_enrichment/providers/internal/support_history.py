"""
Support history provider.

Fetches customer support interaction history and satisfaction metrics from database.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db_session
from src.database.unit_of_work import UnitOfWork
from src.services.infrastructure.context_enrichment.providers.base_provider import (
    BaseContextProvider,
)


class SupportHistoryProvider(BaseContextProvider):
    """
    Provides support interaction history.

    Fetches:
    - Total conversations and resolution stats
    - Average resolution time
    - CSAT scores (last and average)
    - Most common issues/intents
    - Escalation history
    - Open tickets
    """

    async def fetch(
        self, customer_id: str, conversation_id: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Fetch support history from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            **kwargs: Additional parameters

        Returns:
            Support history data
        """
        self.logger.debug("fetching_support_history", customer_id=customer_id)

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

    async def _fetch_with_session(self, customer_id: UUID, session: AsyncSession) -> dict[str, Any]:
        """Fetch support history using provided session"""
        try:
            uow = UnitOfWork(session)

            # Fetch all conversations
            conversations = await uow.conversations.find_by(customer_id=customer_id)

            if not conversations:
                return self._get_fallback_data()

            # Calculate stats
            total_conversations = len(conversations)

            resolved = sum(
                1 for conv in conversations if hasattr(conv, "status") and conv.status == "resolved"
            )

            escalated = sum(
                1 for conv in conversations if hasattr(conv, "escalated") and conv.escalated
            )

            open_tickets = sum(
                1
                for conv in conversations
                if hasattr(conv, "status") and conv.status in ["active", "waiting"]
            )

            # Calculate average resolution time
            resolution_times = []
            for conv in conversations:
                if (
                    hasattr(conv, "resolved_at")
                    and conv.resolved_at
                    and hasattr(conv, "started_at")
                    and conv.started_at
                ):
                    delta = conv.resolved_at - conv.started_at
                    resolution_times.append(delta.total_seconds() / 60)  # minutes

            avg_resolution_time = (
                sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
            )

            # Get last conversation
            sorted_convs = sorted(
                conversations,
                key=lambda c: c.started_at if hasattr(c, "started_at") else datetime.min,
                reverse=True,
            )
            last_conversation = sorted_convs[0].started_at if sorted_convs else None

            # Get CSAT scores
            csat_scores = [
                conv.csat_score
                for conv in conversations
                if hasattr(conv, "csat_score") and conv.csat_score is not None
            ]

            last_csat = csat_scores[0] if csat_scores else None
            avg_csat = sum(csat_scores) / len(csat_scores) if csat_scores else None

            # Get most common issues (from primary_intent)
            intent_counts = {}
            for conv in conversations:
                if hasattr(conv, "primary_intent") and conv.primary_intent:
                    intent = conv.primary_intent
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1

            most_common_issues = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            most_common_issues = [issue for issue, count in most_common_issues]

            return {
                "total_conversations": total_conversations,
                "resolved_conversations": resolved,
                "avg_resolution_time_minutes": round(avg_resolution_time, 1),
                "most_common_issues": most_common_issues,
                "last_conversation": last_conversation,
                "last_csat": last_csat,
                "avg_csat": round(avg_csat, 1) if avg_csat else None,
                "escalation_count": escalated,
                "open_tickets": open_tickets,
            }

        except Exception as e:
            self.logger.error(
                "fetch_failed",
                customer_id=str(customer_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return self._get_fallback_data()

    def _get_fallback_data(self) -> dict[str, Any]:
        """Get fallback data when query fails"""
        return {
            "total_conversations": 0,
            "resolved_conversations": 0,
            "avg_resolution_time_minutes": 0.0,
            "most_common_issues": [],
            "last_conversation": None,
            "last_csat": None,
            "avg_csat": None,
            "escalation_count": 0,
            "open_tickets": 0,
        }
