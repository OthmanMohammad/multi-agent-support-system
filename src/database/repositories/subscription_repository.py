"""
Subscription and billing repository - Business logic for subscription data access
"""
from typing import Optional, List
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime, timedelta, UTC

from src.database.base import BaseRepository
from src.database.models import Subscription, Invoice, Payment, UsageEvent, Credit


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for subscription operations"""

    def __init__(self, session):
        super().__init__(Subscription, session)

    async def get_by_customer(
        self,
        customer_id: UUID
    ) -> Optional[Subscription]:
        """Get active subscription for a customer"""
        result = await self.session.execute(
            select(Subscription)
            .where(and_(
                Subscription.customer_id == customer_id,
                Subscription.status == 'active'
            ))
        )
        return result.scalar_one_or_none()

    async def get_by_plan(
        self,
        plan: str,
        limit: int = 100
    ) -> List[Subscription]:
        """Get all subscriptions on a specific plan"""
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.plan == plan)
            .order_by(Subscription.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_expiring_soon(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Subscription]:
        """Get subscriptions expiring in the next N days"""
        cutoff = datetime.now(UTC) + timedelta(days=days)
        result = await self.session.execute(
            select(Subscription)
            .where(and_(
                Subscription.current_period_end <= cutoff,
                Subscription.status == 'active'
            ))
            .order_by(Subscription.current_period_end.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_total_mrr(self) -> float:
        """Get total Monthly Recurring Revenue"""
        result = await self.session.execute(
            select(func.sum(Subscription.mrr))
            .where(Subscription.status == 'active')
        )
        return result.scalar() or 0.0

    async def get_churned_subscriptions(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Subscription]:
        """Get recently churned subscriptions"""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self.session.execute(
            select(Subscription)
            .where(and_(
                Subscription.status == 'canceled',
                Subscription.canceled_at >= cutoff
            ))
            .order_by(Subscription.canceled_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for invoice operations"""

    def __init__(self, session):
        super().__init__(Invoice, session)

    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all invoices for a customer"""
        result = await self.session.execute(
            select(Invoice)
            .where(Invoice.customer_id == customer_id)
            .order_by(Invoice.invoice_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unpaid(
        self,
        limit: int = 100
    ) -> List[Invoice]:
        """Get all unpaid invoices"""
        result = await self.session.execute(
            select(Invoice)
            .where(Invoice.status == 'unpaid')
            .order_by(Invoice.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_overdue(
        self,
        limit: int = 100
    ) -> List[Invoice]:
        """Get overdue invoices"""
        result = await self.session.execute(
            select(Invoice)
            .where(and_(
                Invoice.status == 'unpaid',
                Invoice.due_date < datetime.now(UTC)
            ))
            .order_by(Invoice.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_total_revenue(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """Get total revenue in a date range"""
        query = select(func.sum(Invoice.total))

        conditions = [Invoice.status == 'paid']
        if start_date:
            conditions.append(Invoice.invoice_date >= start_date)
        if end_date:
            conditions.append(Invoice.invoice_date <= end_date)

        query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar() or 0.0


class PaymentRepository(BaseRepository[Payment]):
    """Repository for payment operations"""

    def __init__(self, session):
        super().__init__(Payment, session)

    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 100
    ) -> List[Payment]:
        """Get all payments for a customer"""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.customer_id == customer_id)
            .order_by(Payment.payment_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_invoice(
        self,
        invoice_id: UUID
    ) -> List[Payment]:
        """Get all payments for an invoice"""
        result = await self.session.execute(
            select(Payment)
            .where(Payment.invoice_id == invoice_id)
            .order_by(Payment.payment_date.desc())
        )
        return list(result.scalars().all())

    async def get_failed_payments(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Payment]:
        """Get recent failed payments"""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self.session.execute(
            select(Payment)
            .where(and_(
                Payment.status == 'failed',
                Payment.payment_date >= cutoff
            ))
            .order_by(Payment.payment_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class UsageEventRepository(BaseRepository[UsageEvent]):
    """Repository for usage event operations"""

    def __init__(self, session):
        super().__init__(UsageEvent, session)

    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 1000
    ) -> List[UsageEvent]:
        """Get usage events for a customer"""
        result = await self.session.execute(
            select(UsageEvent)
            .where(UsageEvent.customer_id == customer_id)
            .order_by(UsageEvent.event_timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_subscription(
        self,
        subscription_id: UUID,
        limit: int = 1000
    ) -> List[UsageEvent]:
        """Get usage events for a subscription"""
        result = await self.session.execute(
            select(UsageEvent)
            .where(UsageEvent.subscription_id == subscription_id)
            .order_by(UsageEvent.event_timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_total_usage(
        self,
        customer_id: UUID,
        metric_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        """Get total usage for a metric in a date range"""
        conditions = [
            UsageEvent.customer_id == customer_id,
            UsageEvent.metric_name == metric_name
        ]

        if start_date:
            conditions.append(UsageEvent.event_timestamp >= start_date)
        if end_date:
            conditions.append(UsageEvent.event_timestamp <= end_date)

        result = await self.session.execute(
            select(func.sum(UsageEvent.quantity))
            .where(and_(*conditions))
        )
        return result.scalar() or 0.0


class CreditRepository(BaseRepository[Credit]):
    """Repository for credit operations"""

    def __init__(self, session):
        super().__init__(Credit, session)

    async def get_by_customer(
        self,
        customer_id: UUID
    ) -> List[Credit]:
        """Get all credits for a customer"""
        result = await self.session.execute(
            select(Credit)
            .where(Credit.customer_id == customer_id)
            .order_by(Credit.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_credits(
        self,
        customer_id: UUID
    ) -> List[Credit]:
        """Get active credits for a customer"""
        result = await self.session.execute(
            select(Credit)
            .where(and_(
                Credit.customer_id == customer_id,
                Credit.remaining_amount > 0,
                Credit.expires_at > datetime.now(UTC)
            ))
            .order_by(Credit.expires_at.asc())
        )
        return list(result.scalars().all())

    async def get_total_available(
        self,
        customer_id: UUID
    ) -> float:
        """Get total available credit balance for a customer"""
        result = await self.session.execute(
            select(func.sum(Credit.remaining_amount))
            .where(and_(
                Credit.customer_id == customer_id,
                Credit.remaining_amount > 0,
                Credit.expires_at > datetime.now(UTC)
            ))
        )
        return result.scalar() or 0.0
