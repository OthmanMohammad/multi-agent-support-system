"""
Customer intelligence provider.

Fetches customer profile data, business metrics, and key indicators from the database.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, UTC
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider
from src.database.models import (
    Customer,
    CustomerHealthEvent,
    CustomerSegment,
    CustomerNote,
    CustomerContact,
    Subscription
)
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session


class CustomerIntelligenceProvider(BaseContextProvider):
    """
    Provides customer profile and business intelligence.

    Fetches:
    - Company information (name, industry, size)
    - Plan and revenue metrics (plan, MRR, LTV)
    - Health score and churn risk
    - NPS score
    - Customer tenure
    - Segments
    - Key notes from CSMs
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch customer intelligence from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            **kwargs: Additional parameters

        Returns:
            Customer intelligence data
        """
        self.logger.debug("fetching_customer_intelligence", customer_id=customer_id)

        # Convert customer_id to UUID
        try:
            cust_uuid = UUID(customer_id)
        except (ValueError, AttributeError):
            self.logger.error("invalid_customer_id", customer_id=customer_id)
            return self._get_fallback_data(customer_id)

        # Get database session from kwargs or create new one
        session = kwargs.get("session")
        if session:
            return await self._fetch_with_session(cust_uuid, session)
        else:
            # Create new session
            async for session in get_db_session():
                return await self._fetch_with_session(cust_uuid, session)

    async def _fetch_with_session(
        self,
        customer_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Fetch customer intelligence using provided session.

        Args:
            customer_id: Customer UUID
            session: Database session

        Returns:
            Customer intelligence data
        """
        try:
            uow = UnitOfWork(session)

            # Fetch customer with relationships
            customer = await uow.customers.get_by_id(customer_id)
            if not customer:
                self.logger.warning("customer_not_found", customer_id=str(customer_id))
                return self._get_fallback_data(str(customer_id))

            # Fetch segments
            segments = await uow.customer_segments.find_by(customer_id=customer_id)
            segment_names = [seg.segment_name for seg in segments if hasattr(seg, 'segment_name')]

            # Fetch recent health events
            health_events = await self._fetch_recent_health_events(uow, customer_id)

            # Fetch active subscription for MRR/ARR
            subscription = await self._fetch_active_subscription(uow, customer_id)

            # Fetch primary contact
            primary_contact = await self._fetch_primary_contact(uow, customer_id)

            # Fetch key notes (recent, high priority)
            key_notes = await self._fetch_key_notes(uow, customer_id)

            # Calculate metrics
            mrr = float(subscription.mrr) if subscription and hasattr(subscription, 'mrr') else 0.0
            arr = float(subscription.arr) if subscription and hasattr(subscription, 'arr') else mrr * 12

            # Calculate LTV (simple: ARR * 3 years)
            ltv = arr * 3 if arr > 0 else 0.0

            # Get health score from metadata or calculate
            health_score = customer.extra_metadata.get('health_score', 50) if customer.extra_metadata else 50

            # Calculate churn risk (inverse of health score with some adjustments)
            churn_risk = max(0.05, min(0.95, (100 - health_score) / 100.0))

            # Get NPS score from metadata
            nps_score = customer.extra_metadata.get('nps_score') if customer.extra_metadata else None

            # Calculate account age
            customer_since = customer.created_at if hasattr(customer, 'created_at') else None
            account_age_days = 0
            if customer_since:
                account_age_days = (datetime.now(UTC) - customer_since.replace(tzinfo=None)).days

            # Extract company size and industry from metadata
            company_size = customer.extra_metadata.get('company_size') if customer.extra_metadata else None
            industry = customer.extra_metadata.get('industry') if customer.extra_metadata else None

            # Determine health trend
            health_trend = self._calculate_health_trend(health_events)

            return {
                # Core info
                "company_name": customer.name or f"Customer {str(customer_id)[:8]}",
                "industry": industry,
                "company_size": company_size,

                # Plan and revenue
                "plan": customer.plan,
                "mrr": mrr,
                "arr": arr,
                "ltv": ltv,

                # Health metrics
                "health_score": health_score,
                "health_trend": health_trend,
                "churn_risk": churn_risk,
                "nps_score": nps_score,

                # Tenure
                "customer_since": customer_since,
                "account_age_days": account_age_days,

                # Segmentation
                "segments": segment_names,

                # Contact info
                "primary_contact": primary_contact,

                # Key notes
                "key_notes": key_notes,
            }

        except Exception as e:
            self.logger.error(
                "fetch_failed",
                customer_id=str(customer_id),
                error=str(e),
                error_type=type(e).__name__
            )
            return self._get_fallback_data(str(customer_id))

    async def _fetch_recent_health_events(
        self,
        uow: UnitOfWork,
        customer_id: UUID,
        limit: int = 5
    ) -> list:
        """
        Fetch recent health events for customer.

        Args:
            uow: Unit of work
            customer_id: Customer ID
            limit: Max events to fetch

        Returns:
            List of recent health events
        """
        try:
            events = await uow.customer_health_events.find_by(
                customer_id=customer_id
            )
            # Sort by created_at descending and limit
            if events:
                events = sorted(
                    events,
                    key=lambda e: e.created_at if hasattr(e, 'created_at') else datetime.min,
                    reverse=True
                )[:limit]
            return events
        except Exception as e:
            self.logger.warning("failed_to_fetch_health_events", error=str(e))
            return []

    async def _fetch_active_subscription(
        self,
        uow: UnitOfWork,
        customer_id: UUID
    ) -> Optional[Any]:
        """
        Fetch active subscription for customer.

        Args:
            uow: Unit of work
            customer_id: Customer ID

        Returns:
            Active subscription or None
        """
        try:
            subscriptions = await uow.subscriptions.find_by(
                customer_id=customer_id,
                status="active"
            )
            return subscriptions[0] if subscriptions else None
        except Exception as e:
            self.logger.warning("failed_to_fetch_subscription", error=str(e))
            return None

    async def _fetch_primary_contact(
        self,
        uow: UnitOfWork,
        customer_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch primary contact for customer.

        Args:
            uow: Unit of work
            customer_id: Customer ID

        Returns:
            Primary contact dict or None
        """
        try:
            contacts = await uow.customer_contacts.find_by(customer_id=customer_id)
            if contacts:
                # Find primary contact or use first one
                primary = next(
                    (c for c in contacts if (c.is_primary if hasattr(c, 'is_primary') else False)),
                    contacts[0]
                )
                return {
                    "name": primary.name if hasattr(primary, 'name') else None,
                    "email": primary.email if hasattr(primary, 'email') else None,
                    "title": primary.title if hasattr(primary, 'title') else None,
                }
            return None
        except Exception as e:
            self.logger.warning("failed_to_fetch_primary_contact", error=str(e))
            return None

    async def _fetch_key_notes(
        self,
        uow: UnitOfWork,
        customer_id: UUID,
        limit: int = 3
    ) -> list:
        """
        Fetch key customer notes.

        Args:
            uow: Unit of work
            customer_id: Customer ID
            limit: Max notes to fetch

        Returns:
            List of key note strings
        """
        try:
            notes = await uow.customer_notes.find_by(customer_id=customer_id)
            if notes:
                # Sort by created_at descending
                notes = sorted(
                    notes,
                    key=lambda n: n.created_at if hasattr(n, 'created_at') else datetime.min,
                    reverse=True
                )[:limit]
                return [
                    note.content if hasattr(note, 'content') else str(note)
                    for note in notes
                ]
            return []
        except Exception as e:
            self.logger.warning("failed_to_fetch_notes", error=str(e))
            return []

    def _calculate_health_trend(self, health_events: list) -> str:
        """
        Calculate health trend from recent events.

        Args:
            health_events: List of health events

        Returns:
            Trend: "improving", "stable", or "declining"
        """
        if not health_events or len(health_events) < 2:
            return "stable"

        # Get last two health score changes
        score_changes = [
            event for event in health_events
            if hasattr(event, 'event_type') and event.event_type == "health_score_change"
        ][:2]

        if len(score_changes) < 2:
            return "stable"

        # Compare old_value to new_value
        recent = score_changes[0]
        if hasattr(recent, 'old_value') and hasattr(recent, 'new_value'):
            if recent.new_value and recent.old_value:
                change = float(recent.new_value) - float(recent.old_value)
                if change > 5:
                    return "improving"
                elif change < -5:
                    return "declining"

        return "stable"

    def _get_fallback_data(self, customer_id: str) -> Dict[str, Any]:
        """
        Get fallback data when database query fails.

        Args:
            customer_id: Customer ID

        Returns:
            Minimal customer intelligence data
        """
        return {
            "company_name": f"Customer {customer_id[:8]}",
            "industry": None,
            "company_size": None,
            "plan": "free",
            "mrr": 0.0,
            "arr": 0.0,
            "ltv": 0.0,
            "health_score": 50,
            "health_trend": "stable",
            "churn_risk": 0.5,
            "nps_score": None,
            "customer_since": None,
            "account_age_days": 0,
            "segments": [],
            "primary_contact": None,
            "key_notes": [],
        }
