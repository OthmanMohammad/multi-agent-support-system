"""
Customer model - User accounts
"""

import uuid

from sqlalchemy import CheckConstraint, Column, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database.models.base import BaseModel, TimestampMixin


class Customer(BaseModel, TimestampMixin):
    """Customer/User account"""

    __tablename__ = "customers"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core Fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    plan = Column(String(50), default="free", nullable=False, index=True)

    # Flexible metadata for additional customer info
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    conversations = relationship(
        "Conversation", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    health_events = relationship(
        "CustomerHealthEvent",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    segments = relationship(
        "CustomerSegment", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    notes = relationship(
        "CustomerNote", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    contacts = relationship(
        "CustomerContact", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    integrations = relationship(
        "CustomerIntegration",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    subscriptions = relationship(
        "Subscription", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    invoices = relationship(
        "Invoice", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    payments = relationship(
        "Payment", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    usage_events = relationship(
        "UsageEvent", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    credits = relationship(
        "Credit", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    converted_from_lead = relationship(
        "Lead",
        back_populates="converted_customer",
        foreign_keys="Lead.converted_to_customer_id",
        uselist=False,
    )
    deals = relationship(
        "Deal", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    quotes = relationship(
        "Quote", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    feature_usage = relationship(
        "FeatureUsage", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    ab_tests = relationship(
        "ABTest", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    sla_compliance = relationship(
        "SLACompliance", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    consent_records = relationship(
        "ConsentRecord", back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "plan IN ('free', 'basic', 'premium', 'enterprise')", name="check_customer_plan_values"
        ),
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, email={self.email}, plan={self.plan})>"
