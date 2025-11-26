"""
Sales, leads, and deals models
"""

import uuid

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database.models.base import BaseModel


class Employee(BaseModel):
    """Internal team members"""

    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, index=True)
    department = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    assigned_leads = relationship(
        "Lead", back_populates="assigned_employee", foreign_keys="Lead.assigned_to"
    )
    assigned_deals = relationship(
        "Deal", back_populates="assigned_employee", foreign_keys="Deal.assigned_to"
    )
    sales_activities = relationship(
        "SalesActivity", back_populates="performer", foreign_keys="SalesActivity.performed_by"
    )

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, email={self.email}, name={self.name}, role={self.role})>"


class Lead(BaseModel):
    """Sales leads and prospects"""

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    budget = Column(String(50), nullable=True)
    authority = Column(String(50), nullable=True)
    need_score = Column(DECIMAL(precision=3, scale=2), nullable=True)
    timeline = Column(String(50), nullable=True)
    lead_score = Column(Integer, nullable=False, server_default="0", index=True)
    qualification_status = Column(String(50), nullable=False, server_default="new", index=True)
    source = Column(String(50), nullable=True)
    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    converted_to_customer_id = Column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    converted_at = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    assigned_employee = relationship(
        "Employee", back_populates="assigned_leads", foreign_keys=[assigned_to]
    )
    converted_customer = relationship(
        "Customer", back_populates="converted_from_lead", foreign_keys=[converted_to_customer_id]
    )
    deals = relationship("Deal", back_populates="lead", cascade="all, delete-orphan")
    activities = relationship("SalesActivity", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "qualification_status IN ('new', 'mql', 'sql', 'qualified', 'disqualified', 'converted')",
            name="check_lead_qualification_status",
        ),
        CheckConstraint("lead_score BETWEEN 0 AND 100", name="check_lead_score_range"),
        CheckConstraint(
            "need_score IS NULL OR (need_score BETWEEN 0 AND 1)", name="check_need_score_range"
        ),
    )

    @property
    def is_qualified(self) -> bool:
        """Check if lead is qualified"""
        return self.qualification_status in ("sql", "qualified")

    @property
    def is_converted(self) -> bool:
        """Check if lead is converted to customer"""
        return (
            self.qualification_status == "converted" and self.converted_to_customer_id is not None
        )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, email={self.email}, score={self.lead_score}, status={self.qualification_status})>"


class Deal(BaseModel):
    """Sales opportunities and deals"""

    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    value = Column(DECIMAL(precision=10, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="USD")
    stage = Column(String(50), nullable=False, server_default="prospecting", index=True)
    probability = Column(Integer, nullable=False, server_default="0")
    expected_close_date = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    lost_reason = Column(Text, nullable=True)
    assigned_to = Column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="deals")
    customer = relationship("Customer", back_populates="deals")
    assigned_employee = relationship(
        "Employee", back_populates="assigned_deals", foreign_keys=[assigned_to]
    )
    activities = relationship("SalesActivity", back_populates="deal", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="deal", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "stage IN ('prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost')",
            name="check_deal_stage",
        ),
        CheckConstraint("probability BETWEEN 0 AND 100", name="check_deal_probability"),
    )

    @property
    def is_won(self) -> bool:
        """Check if deal is won"""
        return self.stage == "closed_won"

    @property
    def is_lost(self) -> bool:
        """Check if deal is lost"""
        return self.stage == "closed_lost"

    @property
    def is_closed(self) -> bool:
        """Check if deal is closed"""
        return self.stage in ("closed_won", "closed_lost")

    @property
    def weighted_value(self) -> float:
        """Calculate weighted value based on probability"""
        return float(self.value) * (self.probability / 100)

    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, name={self.name}, value={self.value}, stage={self.stage})>"


class SalesActivity(BaseModel):
    """Sales activities (calls, emails, demos, etc.)"""

    __tablename__ = "sales_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    lead_id = Column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=True, index=True
    )
    activity_type = Column(String(50), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    outcome = Column(String(50), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    performed_by = Column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    deal = relationship("Deal", back_populates="activities")
    lead = relationship("Lead", back_populates="activities")
    performer = relationship(
        "Employee", back_populates="sales_activities", foreign_keys=[performed_by]
    )

    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('call', 'email', 'meeting', 'demo', 'proposal', 'follow_up')",
            name="check_activity_type",
        ),
    )

    @property
    def is_completed(self) -> bool:
        """Check if activity is completed"""
        return self.completed_at is not None

    def __repr__(self) -> str:
        return f"<SalesActivity(id={self.id}, type={self.activity_type}, subject={self.subject})>"


class Quote(BaseModel):
    """Price quotes for deals"""

    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id = Column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quote_number = Column(String(50), nullable=False, unique=True, index=True)
    total_amount = Column(DECIMAL(precision=10, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, server_default="USD")
    status = Column(String(20), nullable=False, server_default="draft")
    valid_until = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    line_items = Column(JSONB, default=list, nullable=False)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    deal = relationship("Deal", back_populates="quotes")
    customer = relationship("Customer", back_populates="quotes")

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'sent', 'accepted', 'declined', 'expired')",
            name="check_quote_status",
        ),
    )

    @property
    def is_accepted(self) -> bool:
        """Check if quote is accepted"""
        return self.status == "accepted"

    def __repr__(self) -> str:
        return f"<Quote(id={self.id}, number={self.quote_number}, amount={self.total_amount}, status={self.status})>"
