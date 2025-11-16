"""
Sales pipeline provider.

Fetches active deals, opportunities, and sales activities from database.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider
from src.database.models import Lead, Deal, SalesActivity, Quote
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session


class SalesPipelineProvider(BaseContextProvider):
    """
    Provides sales pipeline and opportunity information.

    Fetches:
    - Lead information and qualification status
    - Active deals and pipeline value
    - Recent sales activities
    - Pending quotes
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch sales pipeline from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            **kwargs: Additional parameters

        Returns:
            Sales pipeline data
        """
        self.logger.debug("fetching_sales_pipeline", customer_id=customer_id)

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
        """Fetch sales pipeline using provided session"""
        try:
            uow = UnitOfWork(session)

            # Fetch lead info (if customer was converted from lead)
            leads = await uow.leads.find_by(converted_to_customer_id=customer_id)
            lead_info = None
            if leads:
                lead = leads[0]
                lead_info = {
                    "source": lead.source if hasattr(lead, 'source') else None,
                    "qualification_status": "converted",
                    "lead_score": lead.lead_score if hasattr(lead, 'lead_score') else None,
                    "converted_at": lead.converted_at if hasattr(lead, 'converted_at') else None,
                }

            # Fetch active deals
            deals = await uow.deals.find_by(customer_id=customer_id)

            # Filter to active/open deals
            active_deals = [
                deal for deal in deals
                if hasattr(deal, 'status') and deal.status in ['open', 'negotiation', 'proposal']
            ]

            deal_list = []
            total_pipeline_value = 0.0

            for deal in active_deals[:5]:  # Top 5 deals
                value = float(deal.value) if hasattr(deal, 'value') and deal.value else 0.0
                probability = deal.probability if hasattr(deal, 'probability') else 0.5
                total_pipeline_value += value * probability

                deal_list.append({
                    "deal_id": str(deal.id) if hasattr(deal, 'id') else None,
                    "name": deal.name if hasattr(deal, 'name') else "Unnamed Deal",
                    "value": value,
                    "stage": deal.stage if hasattr(deal, 'stage') else "unknown",
                    "probability": probability,
                    "expected_close_date": deal.expected_close_date if hasattr(deal, 'expected_close_date') else None,
                })

            # Fetch recent sales activities (last 30 days)
            cutoff = datetime.utcnow() - timedelta(days=30)
            activities = await uow.sales_activities.find_by(customer_id=customer_id)

            recent_activities = [
                act for act in activities
                if hasattr(act, 'activity_date') and
                   act.activity_date.replace(tzinfo=None) > cutoff
            ]

            # Sort by date
            recent_activities = sorted(
                recent_activities,
                key=lambda a: a.activity_date if hasattr(a, 'activity_date') else datetime.min,
                reverse=True
            )[:5]

            activity_list = []
            for act in recent_activities:
                activity_list.append({
                    "type": act.activity_type if hasattr(act, 'activity_type') else "unknown",
                    "date": act.activity_date if hasattr(act, 'activity_date') else None,
                    "outcome": act.outcome if hasattr(act, 'outcome') else None,
                    "notes": act.notes[:100] if hasattr(act, 'notes') and act.notes else None,
                })

            # Fetch pending quotes
            quotes = await uow.quotes.find_by(customer_id=customer_id)

            pending_quotes = [
                quote for quote in quotes
                if hasattr(quote, 'status') and quote.status in ['draft', 'sent', 'pending']
            ]

            quote_list = []
            for quote in pending_quotes[:3]:
                quote_list.append({
                    "quote_id": str(quote.id) if hasattr(quote, 'id') else None,
                    "amount": float(quote.amount) if hasattr(quote, 'amount') else 0.0,
                    "status": quote.status if hasattr(quote, 'status') else "unknown",
                    "valid_until": quote.valid_until if hasattr(quote, 'valid_until') else None,
                })

            return {
                "lead_info": lead_info,
                "active_deals": deal_list,
                "total_pipeline_value": round(total_pipeline_value, 2),
                "recent_activities": activity_list,
                "pending_quotes": quote_list,
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
            "lead_info": None,
            "active_deals": [],
            "total_pipeline_value": 0.0,
            "recent_activities": [],
            "pending_quotes": [],
        }
