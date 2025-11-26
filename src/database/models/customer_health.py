"""
Customer health tracking models
"""

import uuid

from sqlalchemy import DECIMAL, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database.models.base import BaseModel


class CustomerHealthEvent(BaseModel):
    """Track customer health score changes and health-related events"""

    __tablename__ = "customer_health_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(50), nullable=False)
    old_value = Column(DECIMAL(precision=5, scale=2), nullable=True)
    new_value = Column(DECIMAL(precision=5, scale=2), nullable=True)
    reason = Column(Text, nullable=True)
    detected_by = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="health_events")

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('health_score_change', 'churn_risk_change', 'engagement_drop', 'usage_spike')",
            name="check_health_event_type",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')", name="check_health_event_severity"
        ),
    )

    def __repr__(self) -> str:
        return f"<CustomerHealthEvent(id={self.id}, customer_id={self.customer_id}, event_type={self.event_type})>"


class CustomerSegment(BaseModel):
    """Customer segmentation for targeting and personalization"""

    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_name = Column(String(100), nullable=False, index=True)
    segment_type = Column(String(50), nullable=False)
    confidence_score = Column(DECIMAL(precision=3, scale=2), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    assigned_by = Column(String(50), nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="segments")

    __table_args__ = (
        CheckConstraint(
            "segment_type IN ('industry', 'lifecycle', 'value', 'behavior', 'risk')",
            name="check_segment_type",
        ),
    )

    def __repr__(self) -> str:
        return f"<CustomerSegment(id={self.id}, customer_id={self.customer_id}, segment={self.segment_name})>"


class CustomerNote(BaseModel):
    """Internal notes about customers"""

    __tablename__ = "customer_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    note_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(String(20), nullable=False, server_default="true")
    visibility = Column(String(20), nullable=False, server_default="team")
    author_id = Column(UUID(as_uuid=True), nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="notes")

    __table_args__ = (
        CheckConstraint(
            "note_type IN ('general', 'support', 'sales', 'success', 'technical')",
            name="check_note_type",
        ),
        CheckConstraint(
            "visibility IN ('private', 'team', 'company')", name="check_note_visibility"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerNote(id={self.id}, customer_id={self.customer_id}, type={self.note_type})>"
        )


class CustomerContact(BaseModel):
    """Multiple contacts per customer account"""

    __tablename__ = "customer_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    title = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    role = Column(String(50), nullable=True)
    is_primary = Column(String(20), nullable=False, server_default="false")
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="contacts")

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'billing', 'technical', 'business', 'user')",
            name="check_contact_role",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerContact(id={self.id}, email={self.email}, customer_id={self.customer_id})>"
        )


class CustomerIntegration(BaseModel):
    """Track customer integrations with external systems"""

    __tablename__ = "customer_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    integration_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, server_default="active")
    config = Column(JSONB, default=dict, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(20), nullable=True)
    error_count = Column(Integer, nullable=False, server_default="0")
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="integrations")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'error', 'disconnected')",
            name="check_integration_status",
        ),
    )

    @property
    def is_healthy(self) -> bool:
        """Check if integration is healthy"""
        return self.status == "active" and self.error_count < 5

    def __repr__(self) -> str:
        return f"<CustomerIntegration(id={self.id}, customer_id={self.customer_id}, type={self.integration_type})>"
