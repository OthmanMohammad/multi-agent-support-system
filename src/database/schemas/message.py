"""
Message Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageBase(BaseModel):
    """Base message schema"""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=50000)
    agent_name: str | None = Field(None, max_length=50)
    intent: str | None = Field(None, max_length=100)
    sentiment: float | None = Field(None, ge=-1, le=1)
    confidence: float | None = Field(None, ge=0, le=1)


class MessageCreate(MessageBase):
    """Schema for creating a message"""

    conversation_id: UUID
    tokens_used: int | None = Field(None, ge=0)
    extra_metadata: dict = Field(default_factory=dict)


class MessageUpdate(BaseModel):
    """Schema for updating a message"""

    content: str | None = Field(None, min_length=1, max_length=50000)
    intent: str | None = None
    sentiment: float | None = Field(None, ge=-1, le=1)
    confidence: float | None = Field(None, ge=0, le=1)
    extra_metadata: dict | None = None


class MessageInDB(MessageBase):
    """Message as stored in database

    Note: Uses field aliases for API compatibility with frontend:
    - created_at → timestamp (alternative name frontend might use)
    """

    id: UUID
    conversation_id: UUID
    tokens_used: int | None = None
    extra_metadata: dict = Field(default_factory=dict, serialization_alias="metadata")
    created_at: datetime = Field(serialization_alias="timestamp", default=None)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # Allow both field names
    )


class MessageResponse(MessageInDB):
    """Message response for API"""

    pass


class MessageSentimentDistribution(BaseModel):
    """Message sentiment distribution for a conversation"""

    positive: int = 0
    negative: int = 0
    neutral: int = 0
    average: float = 0.0
