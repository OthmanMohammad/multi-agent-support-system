"""
Agent handoff and collaboration Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# AgentHandoff Schemas
# ============================================================================


class AgentHandoffBase(BaseModel):
    """Base schema for agent handoffs"""

    conversation_id: UUID
    from_agent: str = Field(..., max_length=50)
    to_agent: str = Field(..., max_length=50)
    handoff_reason: str
    state_transferred: dict | None = None
    confidence_before: Decimal | None = Field(None, ge=0, le=1)
    timestamp: datetime
    latency_ms: int | None = Field(None, ge=0)
    extra_metadata: dict = Field(default_factory=dict)


class AgentHandoffCreate(AgentHandoffBase):
    """Schema for creating an agent handoff"""

    pass


class AgentHandoffUpdate(BaseModel):
    """Schema for updating an agent handoff"""

    from_agent: str | None = Field(None, max_length=50)
    to_agent: str | None = Field(None, max_length=50)
    handoff_reason: str | None = None
    state_transferred: dict | None = None
    confidence_before: Decimal | None = Field(None, ge=0, le=1)
    timestamp: datetime | None = None
    latency_ms: int | None = Field(None, ge=0)
    extra_metadata: dict | None = None


class AgentHandoffInDB(AgentHandoffBase):
    """Schema for agent handoff as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class AgentHandoffResponse(AgentHandoffInDB):
    """Schema for agent handoff API response"""

    handoff_duration_seconds: float


# ============================================================================
# AgentCollaboration Schemas
# ============================================================================


class AgentCollaborationBase(BaseModel):
    """Base schema for agent collaborations"""

    conversation_id: UUID
    collaboration_type: str = Field(
        ..., pattern="^(sequential|parallel|debate|verification|expert_panel)$"
    )
    agents_involved: list[str]
    coordinator_agent: str | None = Field(None, max_length=50)
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: int | None = Field(None, ge=0)
    outcome: str | None = None
    consensus_reached: bool | None = None
    extra_metadata: dict = Field(default_factory=dict)


class AgentCollaborationCreate(AgentCollaborationBase):
    """Schema for creating an agent collaboration"""

    pass


class AgentCollaborationUpdate(BaseModel):
    """Schema for updating an agent collaboration"""

    collaboration_type: str | None = Field(
        None, pattern="^(sequential|parallel|debate|verification|expert_panel)$"
    )
    agents_involved: list[str] | None = None
    coordinator_agent: str | None = Field(None, max_length=50)
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_ms: int | None = Field(None, ge=0)
    outcome: str | None = None
    consensus_reached: bool | None = None
    extra_metadata: dict | None = None


class AgentCollaborationInDB(AgentCollaborationBase):
    """Schema for agent collaboration as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class AgentCollaborationResponse(AgentCollaborationInDB):
    """Schema for agent collaboration API response"""

    agent_count: int
    duration_seconds: float
    is_complete: bool


# ============================================================================
# ConversationTag Schemas
# ============================================================================


class ConversationTagBase(BaseModel):
    """Base schema for conversation tags"""

    conversation_id: UUID
    tag: str = Field(..., max_length=50)
    tag_category: str | None = Field(None, max_length=50)
    confidence: Decimal | None = Field(None, ge=0, le=1)
    tagged_by: str | None = Field(None, max_length=50)
    extra_metadata: dict = Field(default_factory=dict)


class ConversationTagCreate(ConversationTagBase):
    """Schema for creating a conversation tag"""

    pass


class ConversationTagUpdate(BaseModel):
    """Schema for updating a conversation tag"""

    tag: str | None = Field(None, max_length=50)
    tag_category: str | None = Field(None, max_length=50)
    confidence: Decimal | None = Field(None, ge=0, le=1)
    tagged_by: str | None = Field(None, max_length=50)
    extra_metadata: dict | None = None


class ConversationTagInDB(ConversationTagBase):
    """Schema for conversation tag as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ConversationTagResponse(ConversationTagInDB):
    """Schema for conversation tag API response"""

    pass
