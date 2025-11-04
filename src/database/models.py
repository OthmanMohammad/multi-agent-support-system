"""
SQLAlchemy ORM Models - Database table definitions
"""
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey,
    CheckConstraint, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Customer(Base):
    """Customer table - stores user accounts"""
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    plan = Column(String(50), default="free", nullable=False, index=True)
    extra_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "plan IN ('free', 'basic', 'premium', 'enterprise')",
            name="check_customer_plan_values"
        ),
    )


class Conversation(Base):
    """Conversation table - stores chat sessions"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status = Column(String(50), default="active", nullable=False, index=True)
    primary_intent = Column(String(100), index=True)
    agents_involved = Column(ARRAY(String), default=[])
    sentiment_avg = Column(Float)
    kb_articles_used = Column(ARRAY(String), default=[])
    extra_metadata = Column(JSONB, default={})
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ended_at = Column(DateTime(timezone=True))
    resolution_time_seconds = Column(Integer)
    
    # Relationships
    customer = relationship("Customer", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'resolved', 'escalated')",
            name="check_conversation_status_values"
        ),
        CheckConstraint(
            "sentiment_avg IS NULL OR (sentiment_avg >= -1 AND sentiment_avg <= 1)",
            name="check_conversation_sentiment_range"
        ),
        Index("idx_conversations_started_at_desc", started_at.desc()),
    )


class Message(Base):
    """Message table - individual messages in conversations"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String(20), nullable=False)
    agent_name = Column(String(50), index=True)
    content = Column(Text, nullable=False)
    intent = Column(String(100))
    sentiment = Column(Float)
    confidence = Column(Float)
    tokens_used = Column(Integer)
    extra_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
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
    )


class AgentPerformance(Base):
    """Agent performance metrics for analytics"""
    __tablename__ = "agent_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(50), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_interactions = Column(Integer, default=0)
    successful_resolutions = Column(Integer, default=0)
    escalations = Column(Integer, default=0)
    avg_confidence = Column(Float)
    avg_sentiment = Column(Float)
    avg_response_time_ms = Column(Integer)
    extra_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_agent_performance_unique", agent_name, date, unique=True),
    )