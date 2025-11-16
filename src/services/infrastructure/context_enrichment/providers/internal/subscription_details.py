"""
Subscription details provider.

Fetches billing, subscription, and payment information from the database.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider
from src.database.models import Subscription, Invoice, Payment, Credit
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session


class SubscriptionDetailsProvider(BaseContextProvider):
    """
    Provides subscription and billing information.

    Fetches:
    - Current subscription (status, plan, billing cycle)
    - Seats (total, used, utilization)
    - Billing information (MRR, ARR, next invoice)
    - Payment health (failed payments, overdue invoices)
    - Credit balance
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
            **kwargs: Additional parameters

        Returns:
            Subscription details data
        """
        self.logger.debug("fetching_subscription_details", customer_id=customer_id)

        # Convert to UUID
        try:
            cust_uuid = UUID(customer_id)
        except (ValueError, AttributeError):
            self.logger.error("invalid_customer_id", customer_id=customer_id)
            return self._get_fallback_data()

        # Get or create session
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
        """Fetch subscription details using provided session"""
        try:
            uow = UnitOfWork(session)

            # Fetch active subscription
            subscriptions = await uow.subscriptions.find_by(
                customer_id=customer_id,
                status="active"
            )
            subscription = subscriptions[0] if subscriptions else None

            if not subscription:
                return self._get_fallback_data()

            # Calculate days to renewal
            days_to_renewal = None
            if hasattr(subscription, 'current_period_end') and subscription.current_period_end:
                delta = subscription.current_period_end.replace(tzinfo=None) - datetime.utcnow()
                days_to_renewal = max(0, delta.days)

            # Get trial status
            trial_status = None
            if hasattr(subscription, 'trial_end') and subscription.trial_end:
                if subscription.trial_end.replace(tzinfo=None) > datetime.utcnow():
                    trial_status = "active"
                else:
                    trial_status = "expired"

            # Fetch recent invoices
            invoices = await uow.invoices.find_by(customer_id=customer_id)
            invoices = sorted(
                invoices,
                key=lambda inv: inv.created_at if hasattr(inv, 'created_at') else datetime.min,
                reverse=True
            )[:5]

            # Check for overdue invoices
            overdue_count = sum(
                1 for inv in invoices
                if hasattr(inv, 'status') and inv.status == "overdue"
            )

            # Fetch recent payments
            payments = await uow.payments.find_by(customer_id=customer_id)
            payments = sorted(
                payments,
                key=lambda p: p.created_at if hasattr(p, 'created_at') else datetime.min,
                reverse=True
            )[:10]

            # Count failed payments in last 90 days
            failed_payments_90d = 0
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            for payment in payments:
                if (hasattr(payment, 'status') and payment.status == "failed" and
                    hasattr(payment, 'created_at') and
                    payment.created_at.replace(tzinfo=None) > cutoff_date):
                    failed_payments_90d += 1

            # Check payment method validity
            payment_method_valid = True
            if payments and hasattr(payments[0], 'status'):
                payment_method_valid = payments[0].status != "failed"

            # Fetch credit balance
            credits = await uow.credits.find_by(customer_id=customer_id)
            total_credit = sum(
                float(credit.amount) for credit in credits
                if hasattr(credit, 'amount') and hasattr(credit, 'status') and credit.status == "active"
            )

            return {
                "subscription": {
                    "status": subscription.status if hasattr(subscription, 'status') else "active",
                    "plan": subscription.plan if hasattr(subscription, 'plan') else "free",
                    "billing_cycle": subscription.billing_cycle if hasattr(subscription, 'billing_cycle') else "monthly",
                    "current_period_start": subscription.current_period_start if hasattr(subscription, 'current_period_start') else None,
                    "current_period_end": subscription.current_period_end if hasattr(subscription, 'current_period_end') else None,
                    "auto_renew": not subscription.cancel_at_period_end if hasattr(subscription, 'cancel_at_period_end') else True,
                    "seats_total": subscription.seats_total if hasattr(subscription, 'seats_total') else 1,
                    "seats_used": subscription.seats_used if hasattr(subscription, 'seats_used') else 1,
                    "seat_utilization": subscription.seat_utilization if hasattr(subscription, 'seat_utilization') else 100.0,
                },
                "billing": {
                    "mrr": float(subscription.mrr) if hasattr(subscription, 'mrr') else 0.0,
                    "arr": float(subscription.arr) if hasattr(subscription, 'arr') else 0.0,
                    "next_invoice_date": subscription.current_period_end if hasattr(subscription, 'current_period_end') else None,
                    "trial_status": trial_status,
                },
                "payment_health": {
                    "failed_payments_90d": failed_payments_90d,
                    "overdue_invoices": overdue_count,
                    "payment_method_valid": payment_method_valid,
                    "credit_balance": total_credit,
                },
                "days_to_renewal": days_to_renewal,
                "cancel_at_period_end": subscription.cancel_at_period_end if hasattr(subscription, 'cancel_at_period_end') else False,
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
            "subscription": {
                "status": "active",
                "plan": "free",
                "billing_cycle": "monthly",
                "current_period_start": None,
                "current_period_end": None,
                "auto_renew": True,
                "seats_total": 1,
                "seats_used": 1,
                "seat_utilization": 100.0,
            },
            "billing": {
                "mrr": 0.0,
                "arr": 0.0,
                "next_invoice_date": None,
                "trial_status": None,
            },
            "payment_health": {
                "failed_payments_90d": 0,
                "overdue_invoices": 0,
                "payment_method_valid": True,
                "credit_balance": 0.0,
            },
            "days_to_renewal": None,
            "cancel_at_period_end": False,
        }
