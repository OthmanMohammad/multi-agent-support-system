"""
Security and compliance Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# AuditLog Schemas
# ============================================================================


class AuditLogBase(BaseModel):
    """Base schema for audit logs"""

    entity_type: str = Field(..., max_length=50)
    entity_id: UUID | None = None
    action: str = Field(..., pattern="^(create|read|update|delete|login|logout|export)$")
    actor_type: str = Field(..., pattern="^(user|agent|system|api)$")
    actor_id: UUID | None = None
    changes: dict | None = None
    ip_address: str | None = Field(None, max_length=45)
    user_agent: str | None = None
    timestamp: datetime
    extra_metadata: dict = Field(default_factory=dict)


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log"""

    pass


class AuditLogUpdate(BaseModel):
    """
    Schema for updating an audit log

    Note: Audit logs should generally be immutable. This schema exists for
    consistency but should rarely be used in practice.
    """

    extra_metadata: dict | None = None


class AuditLogInDB(AuditLogBase):
    """
    Schema for audit log as stored in database

    Note: AuditLog model does not inherit from BaseModel, so it lacks the
    soft delete fields (deleted_at, deleted_by) and update tracking.
    Audit logs are immutable and should never be deleted.
    """

    id: UUID

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(AuditLogInDB):
    """Schema for audit log API response"""

    pass
