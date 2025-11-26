"""
Analytics and metrics models
"""

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.database.models.base import BaseModel


class ConversationAnalytics(BaseModel):
    """Aggregated conversation metrics by date and channel"""

    __tablename__ = "conversation_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    channel = Column(String(50), nullable=True, index=True)
    total_conversations = Column(Integer, nullable=False, server_default="0")
    resolved_conversations = Column(Integer, nullable=False, server_default="0")
    escalated_conversations = Column(Integer, nullable=False, server_default="0")
    avg_resolution_time_seconds = Column(Integer, nullable=True)
    avg_sentiment = Column(Float, nullable=True)
    avg_csat = Column(Float, nullable=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    @property
    def resolution_rate(self) -> float:
        """Calculate resolution rate percentage"""
        if self.total_conversations == 0:
            return 0.0
        return round((self.resolved_conversations / self.total_conversations) * 100, 2)

    @property
    def escalation_rate(self) -> float:
        """Calculate escalation rate percentage"""
        if self.total_conversations == 0:
            return 0.0
        return round((self.escalated_conversations / self.total_conversations) * 100, 2)

    def __repr__(self) -> str:
        return f"<ConversationAnalytics(date={self.date}, channel={self.channel}, total={self.total_conversations})>"


class FeatureUsage(BaseModel):
    """Track feature adoption and usage patterns"""

    __tablename__ = "feature_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_name = Column(String(100), nullable=False, index=True)
    usage_count = Column(Integer, nullable=False, server_default="0")
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="feature_usage")

    def __repr__(self) -> str:
        return f"<FeatureUsage(customer_id={self.customer_id}, feature={self.feature_name}, count={self.usage_count})>"


class ABTest(BaseModel):
    """A/B test results and variant assignments"""

    __tablename__ = "ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_name = Column(String(100), nullable=False, index=True)
    variant = Column(String(50), nullable=False, index=True)
    customer_id = Column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True
    )
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True
    )
    outcome = Column(String(50), nullable=True)
    metric_value = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    extra_metadata = Column(JSONB, default=dict, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="ab_tests")
    conversation = relationship("Conversation", back_populates="ab_tests")

    def __repr__(self) -> str:
        return f"<ABTest(test={self.test_name}, variant={self.variant}, outcome={self.outcome})>"
