"""
Conversation model - Chat sessions between customer and agents
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey,
    CheckConstraint, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from database.models.base import BaseModel


class Conversation(BaseModel):
    """Conversation/Chat session"""
    
    __tablename__ = "conversations"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Status and Intent
    status = Column(
        String(50),
        default="active",
        nullable=False,
        index=True
    )
    primary_intent = Column(String(100), nullable=True, index=True)
    
    # Agent Tracking
    agents_involved = Column(ARRAY(String), default=list, nullable=False)
    
    # Sentiment Analysis
    sentiment_avg = Column(Float, nullable=True)
    
    # Knowledge Base Usage
    kb_articles_used = Column(ARRAY(String), default=list, nullable=False)
    
    # Flexible metadata
    extra_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamps
    started_at = Column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
        index=True
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance Metrics
    resolution_time_seconds = Column(Integer, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="selectin"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'resolved', 'escalated')",
            name="check_conversation_status_values"
        ),
        CheckConstraint(
            "sentiment_avg IS NULL OR (sentiment_avg >= -1 AND sentiment_avg <= 1)",
            name="check_conversation_sentiment_range"
        ),
        Index("idx_conversations_started_at_desc", "started_at", postgresql_using="btree"),
        Index("idx_conversations_active_old", "status", "started_at",
              postgresql_where="status = 'active'"),  # Partial index for unresolved
    )
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, status={self.status}, intent={self.primary_intent})>"