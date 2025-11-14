"""
Agent handoff and collaboration models
"""
from sqlalchemy import Column, String, Integer, DECIMAL, Text, ForeignKey, CheckConstraint, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from src.database.models.base import BaseModel


class AgentHandoff(BaseModel):
    """Track agent-to-agent handoffs during conversations"""

    __tablename__ = "agent_handoffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    from_agent = Column(String(50), nullable=False, index=True)
    to_agent = Column(String(50), nullable=False, index=True)
    handoff_reason = Column(Text, nullable=False)
    state_transferred = Column(JSONB, nullable=True)
    confidence_before = Column(DECIMAL(precision=3, scale=2), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="handoffs")

    __table_args__ = (
        CheckConstraint(
            "from_agent != to_agent",
            name="check_handoff_different_agents"
        ),
    )

    @property
    def handoff_duration_seconds(self) -> float:
        """Get handoff duration in seconds"""
        if self.latency_ms:
            return self.latency_ms / 1000
        return 0

    def __repr__(self) -> str:
        return f"<AgentHandoff(id={self.id}, from={self.from_agent}, to={self.to_agent})>"


class AgentCollaboration(BaseModel):
    """Track multi-agent collaboration sessions"""

    __tablename__ = "agent_collaborations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    collaboration_type = Column(String(50), nullable=False, index=True)
    agents_involved = Column(ARRAY(String), nullable=False)
    coordinator_agent = Column(String(50), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    outcome = Column(Text, nullable=True)
    consensus_reached = Column(Boolean, nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="collaborations")

    __table_args__ = (
        CheckConstraint(
            "collaboration_type IN ('sequential', 'parallel', 'debate', 'verification', 'expert_panel')",
            name="check_collaboration_type"
        ),
    )

    @property
    def agent_count(self) -> int:
        """Get number of agents involved"""
        return len(self.agents_involved) if self.agents_involved else 0

    @property
    def duration_seconds(self) -> float:
        """Get collaboration duration in seconds"""
        if self.duration_ms:
            return self.duration_ms / 1000
        return 0

    @property
    def is_complete(self) -> bool:
        """Check if collaboration is complete"""
        return self.end_time is not None

    def __repr__(self) -> str:
        return f"<AgentCollaboration(id={self.id}, type={self.collaboration_type}, agents={self.agent_count})>"


class ConversationTag(BaseModel):
    """Tags for conversations for categorization and analysis"""

    __tablename__ = "conversation_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tag = Column(String(50), nullable=False, index=True)
    tag_category = Column(String(50), nullable=True)
    confidence = Column(DECIMAL(precision=3, scale=2), nullable=True)
    tagged_by = Column(String(50), nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="tags")

    def __repr__(self) -> str:
        return f"<ConversationTag(id={self.id}, tag={self.tag}, conversation_id={self.conversation_id})>"
