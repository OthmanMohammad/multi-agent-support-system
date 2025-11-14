"""
Security and compliance models
"""
from sqlalchemy import Column, String, Text, CheckConstraint, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from src.database.models.base import Base  # Use Base instead of BaseModel for immutable logs


class AuditLog(Base):
    """
    Immutable audit logs for compliance and security tracking

    Note: This model inherits from Base directly instead of BaseModel
    to avoid soft delete functionality (audit logs should never be deleted).
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    changes = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "action IN ('create', 'read', 'update', 'delete', 'login', 'logout', 'export')",
            name="check_audit_action"
        ),
        CheckConstraint(
            "actor_type IN ('user', 'agent', 'system', 'api')",
            name="check_audit_actor_type"
        ),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_actor", "actor_type", "actor_id"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, entity={self.entity_type}, action={self.action}, actor={self.actor_type})>"
