"""
Conversation Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class ConversationBase(BaseModel):
    """Base conversation schema"""
    status: str = Field(default="active", pattern="^(active|resolved|escalated)$")
    primary_intent: Optional[str] = None
    agents_involved: list[str] = Field(default_factory=list)
    sentiment_avg: Optional[float] = Field(None, ge=-1, le=1)
    kb_articles_used: list[str] = Field(default_factory=list)


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""
    customer_id: UUID
    extra_metadata: dict = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    status: Optional[str] = Field(None, pattern="^(active|resolved|escalated)$")
    primary_intent: Optional[str] = None
    agents_involved: Optional[list[str]] = None
    sentiment_avg: Optional[float] = Field(None, ge=-1, le=1)
    kb_articles_used: Optional[list[str]] = None
    ended_at: Optional[datetime] = None
    resolution_time_seconds: Optional[int] = Field(None, ge=0)
    extra_metadata: Optional[dict] = None


class ConversationInDB(ConversationBase):
    """Conversation as stored in database"""
    id: UUID
    customer_id: UUID
    extra_metadata: dict
    started_at: datetime
    ended_at: Optional[datetime] = None
    resolution_time_seconds: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(ConversationInDB):
    """Conversation response for API"""
    message_count: Optional[int] = Field(default=0, description="Number of messages")


class ConversationWithMessages(ConversationInDB):
    """Conversation with related messages"""
    from database.schemas.message import MessageInDB
    messages: list[MessageInDB] = Field(default_factory=list)


class ConversationStatistics(BaseModel):
    """Conversation statistics"""
    total_conversations: int
    by_status: dict[str, int] = Field(default_factory=dict)
    by_intent: dict[str, int] = Field(default_factory=dict)
    avg_resolution_time_seconds: float = 0.0
    avg_sentiment: float = 0.0