"""
Message model - Individual messages in conversations
"""
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey,
    CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database.models.base import BaseModel


class Message(BaseModel):
    """Individual message in a conversation"""
    
    __tablename__ = "messages"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Message Content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Agent Information
    agent_name = Column(String(50), nullable=True, index=True)
    
    # Classification
    intent = Column(String(100), nullable=True)
    sentiment = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Performance Tracking
    tokens_used = Column(Integer, nullable=True)
    
    # Flexible metadata
    extra_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships - FIXED: Changed "Message" to "Conversation"
    conversation = relationship("Conversation", back_populates="messages")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="check_message_role_values"
        ),
        CheckConstraint(
            "sentiment IS NULL OR (sentiment >= -1 AND sentiment <= 1)",
            name="check_message_sentiment_range"
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="check_message_confidence_range"
        ),
        Index("idx_messages_conversation_created", "conversation_id", "created_at"),
        Index("idx_messages_agent_created", "agent_name", "created_at"),
    )
    
    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role}, content='{preview}')>"