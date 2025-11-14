"""
Agent handoff and collaboration Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ============================================================================
# AgentHandoff Schemas
# ============================================================================

class AgentHandoffBase(BaseModel):
    """Base schema for agent handoffs"""
    conversation_id: UUID
    from_agent: str = Field(..., max_length=50)
    to_agent: str = Field(..., max_length=50)
    handoff_reason: str
    state_transferred: Optional[dict] = None
    confidence_before: Optional[Decimal] = Field(None, ge=0, le=1)
    timestamp: datetime
    latency_ms: Optional[int] = Field(None, ge=0)
    extra_metadata: dict = Field(default_factory=dict)


class AgentHandoffCreate(AgentHandoffBase):
    """Schema for creating an agent handoff"""
    pass


class AgentHandoffUpdate(BaseModel):
    """Schema for updating an agent handoff"""
    from_agent: Optional[str] = Field(None, max_length=50)
    to_agent: Optional[str] = Field(None, max_length=50)
    handoff_reason: Optional[str] = None
    state_transferred: Optional[dict] = None
    confidence_before: Optional[Decimal] = Field(None, ge=0, le=1)
    timestamp: Optional[datetime] = None
    latency_ms: Optional[int] = Field(None, ge=0)
    extra_metadata: Optional[dict] = None


class AgentHandoffInDB(AgentHandoffBase):
    """Schema for agent handoff as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

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
    collaboration_type: str = Field(..., pattern="^(sequential|parallel|debate|verification|expert_panel)$")
    agents_involved: list[str]
    coordinator_agent: Optional[str] = Field(None, max_length=50)
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = Field(None, ge=0)
    outcome: Optional[str] = None
    consensus_reached: Optional[bool] = None
    extra_metadata: dict = Field(default_factory=dict)


class AgentCollaborationCreate(AgentCollaborationBase):
    """Schema for creating an agent collaboration"""
    pass


class AgentCollaborationUpdate(BaseModel):
    """Schema for updating an agent collaboration"""
    collaboration_type: Optional[str] = Field(None, pattern="^(sequential|parallel|debate|verification|expert_panel)$")
    agents_involved: Optional[list[str]] = None
    coordinator_agent: Optional[str] = Field(None, max_length=50)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = Field(None, ge=0)
    outcome: Optional[str] = None
    consensus_reached: Optional[bool] = None
    extra_metadata: Optional[dict] = None


class AgentCollaborationInDB(AgentCollaborationBase):
    """Schema for agent collaboration as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

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
    tag_category: Optional[str] = Field(None, max_length=50)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    tagged_by: Optional[str] = Field(None, max_length=50)
    extra_metadata: dict = Field(default_factory=dict)


class ConversationTagCreate(ConversationTagBase):
    """Schema for creating a conversation tag"""
    pass


class ConversationTagUpdate(BaseModel):
    """Schema for updating a conversation tag"""
    tag: Optional[str] = Field(None, max_length=50)
    tag_category: Optional[str] = Field(None, max_length=50)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    tagged_by: Optional[str] = Field(None, max_length=50)
    extra_metadata: Optional[dict] = None


class ConversationTagInDB(ConversationTagBase):
    """Schema for conversation tag as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationTagResponse(ConversationTagInDB):
    """Schema for conversation tag API response"""
    pass
