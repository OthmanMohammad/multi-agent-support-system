"""
Conversation Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.database.schemas.message import MessageInDB


class ConversationBase(BaseModel):
    """Base conversation schema"""

    status: str = Field(default="active", pattern="^(active|resolved|escalated)$")
    primary_intent: str | None = None
    # Alias for frontend compatibility (frontend expects agent_history)
    agents_involved: list[str] = Field(default_factory=list, serialization_alias="agent_history")
    sentiment_avg: float | None = Field(None, ge=-1, le=1)
    kb_articles_used: list[str] = Field(default_factory=list)


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""

    customer_id: UUID
    extra_metadata: dict = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""

    status: str | None = Field(None, pattern="^(active|resolved|escalated)$")
    primary_intent: str | None = None
    agents_involved: list[str] | None = None
    sentiment_avg: float | None = Field(None, ge=-1, le=1)
    kb_articles_used: list[str] | None = None
    ended_at: datetime | None = None
    resolution_time_seconds: int | None = Field(None, ge=0)
    extra_metadata: dict | None = None


class ConversationInDB(ConversationBase):
    """Conversation as stored in database

    Note: Uses field aliases for API compatibility with frontend:
    - id → conversation_id
    - updated_at → last_updated
    """

    id: UUID = Field(serialization_alias="conversation_id")
    customer_id: UUID
    extra_metadata: dict
    started_at: datetime
    ended_at: datetime | None = None
    resolution_time_seconds: int | None = None
    # Timestamp fields from BaseModel (TimestampMixin)
    created_at: datetime | None = None
    updated_at: datetime | None = Field(None, serialization_alias="last_updated")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both field names
    )


class ConversationResponse(ConversationInDB):
    """Conversation response for API"""

    message_count: int | None = Field(default=0, description="Number of messages")


class ConversationWithMessages(ConversationInDB):
    """Conversation with related messages"""

    messages: list[MessageInDB] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ConversationStatistics(BaseModel):
    """Conversation statistics"""

    total_conversations: int
    by_status: dict[str, int] = Field(default_factory=dict)
    by_intent: dict[str, int] = Field(default_factory=dict)
    avg_resolution_time_seconds: float = 0.0
    avg_sentiment: float = 0.0


