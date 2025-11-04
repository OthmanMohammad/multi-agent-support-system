"""
Message Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class MessageBase(BaseModel):
    """Base message schema"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=50000)
    agent_name: Optional[str] = Field(None, max_length=50)
    intent: Optional[str] = Field(None, max_length=100)
    sentiment: Optional[float] = Field(None, ge=-1, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=1)


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    conversation_id: UUID
    tokens_used: Optional[int] = Field(None, ge=0)
    extra_metadata: dict = Field(default_factory=dict)


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    content: Optional[str] = Field(None, min_length=1, max_length=50000)
    intent: Optional[str] = None
    sentiment: Optional[float] = Field(None, ge=-1, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    extra_metadata: Optional[dict] = None


class MessageInDB(MessageBase):
    """Message as stored in database"""
    id: UUID
    conversation_id: UUID
    tokens_used: Optional[int] = None
    extra_metadata: dict
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(MessageInDB):
    """Message response for API"""
    pass


class MessageSentimentDistribution(BaseModel):
    """Message sentiment distribution for a conversation"""
    positive: int = 0
    negative: int = 0
    neutral: int = 0
    average: float = 0.0