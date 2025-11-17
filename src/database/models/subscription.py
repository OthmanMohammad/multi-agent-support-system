"""
Subscription and billing models
"""
from sqlalchemy import Column, String, Integer, DECIMAL, Boolean, Text, ForeignKey, CheckConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC

from src.database.models.base import BaseModel


class Subscription(BaseModel):
    """Customer subscription records"""

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    plan = Column(String(50), nullable=False)
    billing_cycle = Column(String(20), nullable=False)
    mrr = Column(DECIMAL(precision=10, scale=2), nullable=False)
    arr = Column(DECIMAL(precision=10, scale=2), nullable=True)
    seats_total = Column(Integer, nullable=False, server_default="1")
    seats_used = Column(Integer, nullable=False, server_default="1")
    status = Column(String(20), nullable=False, server_default="active", index=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, nullable=False, server_default="false")
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    invoices = relationship(
        "Invoice",
        back_populates="subscription",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "plan IN ('free', 'basic', 'premium', 'enterprise')",
            name="check_subscription_plan"
        ),
        CheckConstraint(
            "billing_cycle IN ('monthly', 'annual')",
            name="check_billing_cycle"
        ),
        CheckConstraint(
            "status IN ('active', 'past_due', 'canceled', 'unpaid', 'trialing')",
            name="check_subscription_status"
        ),
        CheckConstraint(
            "seats_used <= seats_total",
            name="check_seats_capacity"
        ),
    )

    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == "active"

    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial"""
        return self.status == "trialing"

    @property
    def days_until_renewal(self) -> int:
        """Calculate days until renewal"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.now(UTC)
        return max(0, delta.days)

    @property
    def seat_utilization(self) -> float:
        """Calculate seat utilization percentage"""
        if self.seats_total == 0:
            return 0.0
        return round((self.seats_used / self.seats_total) * 100, 1)

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, customer_id={self.customer_id}, plan={self.plan}, status={self.status})>"


class Invoice(BaseModel):
    """Customer invoices"""

    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True
    )
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    amount = Column(DECIMAL(precision=10, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="USD")
    status = Column(String(20), nullable=False, server_default="draft", index=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    subscription = relationship("Subscription", back_populates="invoices")
    payments = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'open', 'paid', 'void', 'uncollectible')",
            name="check_invoice_status"
        ),
    )

    @property
    def is_paid(self) -> bool:
        """Check if invoice is paid"""
        return self.status == "paid"

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        if self.status == "paid" or not self.due_at:
            return False
        return datetime.now(UTC) > self.due_at

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, amount={self.amount}, status={self.status})>"


class Payment(BaseModel):
    """Payment transactions"""

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    amount = Column(DECIMAL(precision=10, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="USD")
    status = Column(String(20), nullable=False, server_default="pending", index=True)
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    failed_reason = Column(Text, nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="payments")
    invoice = relationship("Invoice", back_populates="payments")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed', 'canceled', 'refunded')",
            name="check_payment_status"
        ),
    )

    @property
    def is_successful(self) -> bool:
        """Check if payment succeeded"""
        return self.status == "succeeded"

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"


class UsageEvent(BaseModel):
    """Track usage events for metering and billing"""

    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, server_default="1")
    unit = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="usage_events")

    def __repr__(self) -> str:
        return f"<UsageEvent(id={self.id}, customer_id={self.customer_id}, type={self.event_type}, qty={self.quantity})>"


class Credit(BaseModel):
    """Account credits and promotions"""

    __tablename__ = "credits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    amount = Column(DECIMAL(precision=10, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="USD")
    credit_type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    used_amount = Column(DECIMAL(precision=10, scale=2), nullable=False, server_default="0")
    status = Column(String(20), nullable=False, server_default="active", index=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="credits")

    __table_args__ = (
        CheckConstraint(
            "credit_type IN ('promotional', 'refund', 'goodwill', 'migration')",
            name="check_credit_type"
        ),
        CheckConstraint(
            "status IN ('active', 'used', 'expired', 'canceled')",
            name="check_credit_status"
        ),
        CheckConstraint(
            "used_amount <= amount",
            name="check_credit_usage"
        ),
    )

    @property
    def remaining_amount(self) -> float:
        """Calculate remaining credit amount"""
        return float(self.amount - self.used_amount)

    @property
    def is_expired(self) -> bool:
        """Check if credit is expired"""
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at

    def __repr__(self) -> str:
        return f"<Credit(id={self.id}, customer_id={self.customer_id}, amount={self.amount}, status={self.status})>"
