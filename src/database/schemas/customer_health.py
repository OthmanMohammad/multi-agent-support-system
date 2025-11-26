"""
Customer health Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# CustomerHealthEvent Schemas
# ============================================================================


class CustomerHealthEventBase(BaseModel):
    """Base schema for customer health events"""

    customer_id: UUID
    event_type: str = Field(
        ..., pattern="^(health_score_change|churn_risk_change|engagement_drop|usage_spike)$"
    )
    old_value: Decimal | None = None
    new_value: Decimal | None = None
    reason: str | None = None
    detected_by: str | None = None
    severity: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    extra_metadata: dict = Field(default_factory=dict)


class CustomerHealthEventCreate(CustomerHealthEventBase):
    """Schema for creating a customer health event"""

    pass


class CustomerHealthEventUpdate(BaseModel):
    """Schema for updating a customer health event"""

    event_type: str | None = Field(
        None, pattern="^(health_score_change|churn_risk_change|engagement_drop|usage_spike)$"
    )
    old_value: Decimal | None = None
    new_value: Decimal | None = None
    reason: str | None = None
    detected_by: str | None = None
    severity: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    extra_metadata: dict | None = None


class CustomerHealthEventInDB(CustomerHealthEventBase):
    """Schema for customer health event as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerHealthEventResponse(CustomerHealthEventInDB):
    """Schema for customer health event API response"""

    pass


# ============================================================================
# CustomerSegment Schemas
# ============================================================================


class CustomerSegmentBase(BaseModel):
    """Base schema for customer segments"""

    customer_id: UUID
    segment_name: str = Field(..., max_length=100)
    segment_type: str = Field(..., pattern="^(industry|lifecycle|value|behavior|risk)$")
    confidence_score: Decimal | None = None
    assigned_at: datetime
    assigned_by: str | None = Field(None, max_length=50)
    extra_metadata: dict = Field(default_factory=dict)


class CustomerSegmentCreate(CustomerSegmentBase):
    """Schema for creating a customer segment"""

    pass


class CustomerSegmentUpdate(BaseModel):
    """Schema for updating a customer segment"""

    segment_name: str | None = Field(None, max_length=100)
    segment_type: str | None = Field(None, pattern="^(industry|lifecycle|value|behavior|risk)$")
    confidence_score: Decimal | None = None
    assigned_by: str | None = Field(None, max_length=50)
    extra_metadata: dict | None = None


class CustomerSegmentInDB(CustomerSegmentBase):
    """Schema for customer segment as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerSegmentResponse(CustomerSegmentInDB):
    """Schema for customer segment API response"""

    pass


# ============================================================================
# CustomerNote Schemas
# ============================================================================


class CustomerNoteBase(BaseModel):
    """Base schema for customer notes"""

    customer_id: UUID
    note_type: str = Field(..., pattern="^(general|support|sales|success|technical)$")
    content: str
    is_internal: bool = True
    visibility: str = Field("team", pattern="^(private|team|company)$")
    author_id: UUID | None = None
    extra_metadata: dict = Field(default_factory=dict)


class CustomerNoteCreate(CustomerNoteBase):
    """Schema for creating a customer note"""

    pass


class CustomerNoteUpdate(BaseModel):
    """Schema for updating a customer note"""

    note_type: str | None = Field(None, pattern="^(general|support|sales|success|technical)$")
    content: str | None = None
    is_internal: bool | None = None
    visibility: str | None = Field(None, pattern="^(private|team|company)$")
    extra_metadata: dict | None = None


class CustomerNoteInDB(CustomerNoteBase):
    """Schema for customer note as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerNoteResponse(CustomerNoteInDB):
    """Schema for customer note API response"""

    pass


# ============================================================================
# CustomerContact Schemas
# ============================================================================


class CustomerContactBase(BaseModel):
    """Base schema for customer contacts"""

    customer_id: UUID
    email: str = Field(..., max_length=255)
    name: str | None = Field(None, max_length=255)
    title: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    role: str | None = Field(None, pattern="^(admin|billing|technical|business|user)$")
    is_primary: bool = False
    extra_metadata: dict = Field(default_factory=dict)


class CustomerContactCreate(CustomerContactBase):
    """Schema for creating a customer contact"""

    pass


class CustomerContactUpdate(BaseModel):
    """Schema for updating a customer contact"""

    email: str | None = Field(None, max_length=255)
    name: str | None = Field(None, max_length=255)
    title: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=50)
    role: str | None = Field(None, pattern="^(admin|billing|technical|business|user)$")
    is_primary: bool | None = None
    extra_metadata: dict | None = None


class CustomerContactInDB(CustomerContactBase):
    """Schema for customer contact as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerContactResponse(CustomerContactInDB):
    """Schema for customer contact API response"""

    pass


# ============================================================================
# CustomerIntegration Schemas
# ============================================================================


class CustomerIntegrationBase(BaseModel):
    """Base schema for customer integrations"""

    customer_id: UUID
    integration_type: str = Field(..., max_length=50)
    status: str = Field("active", pattern="^(active|paused|error|disconnected)$")
    config: dict = Field(default_factory=dict)
    last_sync_at: datetime | None = None
    last_sync_status: str | None = Field(None, max_length=20)
    error_count: int = 0
    extra_metadata: dict = Field(default_factory=dict)


class CustomerIntegrationCreate(CustomerIntegrationBase):
    """Schema for creating a customer integration"""

    pass


class CustomerIntegrationUpdate(BaseModel):
    """Schema for updating a customer integration"""

    integration_type: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern="^(active|paused|error|disconnected)$")
    config: dict | None = None
    last_sync_at: datetime | None = None
    last_sync_status: str | None = Field(None, max_length=20)
    error_count: int | None = None
    extra_metadata: dict | None = None


class CustomerIntegrationInDB(CustomerIntegrationBase):
    """Schema for customer integration as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerIntegrationResponse(CustomerIntegrationInDB):
    """Schema for customer integration API response"""

    pass
