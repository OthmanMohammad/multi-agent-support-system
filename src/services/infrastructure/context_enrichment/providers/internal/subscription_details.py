"""
Subscription details provider.

Fetches current subscription and billing information.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider


class SubscriptionDetailsProvider(BaseContextProvider):
    """
    Provides subscription and billing details.

    Fetches:
    - Seat allocation
    - Billing cycle
    - Renewal dates
    - Trial status
    - Payment method status
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch subscription details from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)

        Returns:
            Subscription details data
        """
        self.logger.debug("fetching_subscription_details", customer_id=customer_id)

        # TODO: Replace with actual database query from subscriptions table
        # For now, return reasonable defaults

        customer_hash = sum(ord(c) for c in customer_id) % 100

        # Seats (1-50 total, 50-100% utilized)
        seats_total = 1 + (customer_hash % 49)
        utilization_pct = 0.5 + ((customer_hash % 50) / 100)  # 50-100%
        seats_used = max(1, int(seats_total * utilization_pct))

        # Billing cycle
        billing_cycle = "monthly" if customer_hash % 2 == 0 else "annual"

        # Current period end (7-90 days from now)
        days_to_renewal = 7 + (customer_hash % 83)
        current_period_end = datetime.utcnow() + timedelta(days=days_to_renewal)

        # Cancellation status (10% are cancelled)
        cancel_at_period_end = (customer_hash % 10) == 0

        # Trial status (20% on trial)
        if customer_hash % 5 == 0:
            trial_status = "active"
        else:
            trial_status = None

        # Payment method valid (95% valid)
        payment_method_valid = (customer_hash % 20) != 0

        return {
            "seats_total": seats_total,
            "seats_used": seats_used,
            "billing_cycle": billing_cycle,
            "current_period_end": current_period_end,
            "days_to_renewal": days_to_renewal,
            "cancel_at_period_end": cancel_at_period_end,
            "trial_status": trial_status,
            "payment_method_valid": payment_method_valid
        }
