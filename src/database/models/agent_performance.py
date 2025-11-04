"""
Agent Performance model - Tracks daily metrics for each agent
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from database.models.base import BaseModel


class AgentPerformance(BaseModel):
    """Daily performance metrics for agents"""
    
    __tablename__ = "agent_performance"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Agent and Date
    agent_name = Column(String(50), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Performance Metrics
    total_interactions = Column(Integer, default=0, nullable=False)
    successful_resolutions = Column(Integer, default=0, nullable=False)
    escalations = Column(Integer, default=0, nullable=False)
    
    # Quality Metrics
    avg_confidence = Column(Float, nullable=True)
    avg_sentiment = Column(Float, nullable=True)
    avg_response_time_ms = Column(Integer, nullable=True)
    
    # Flexible metadata for custom metrics
    extra_metadata = Column(JSONB, default=dict, nullable=False)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Constraints and Indexes
    __table_args__ = (
        # Unique constraint: one record per agent per day
        Index(
            "idx_agent_performance_unique",
            "agent_name",
            "date",
            unique=True
        ),
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_interactions == 0:
            return 0.0
        return (self.successful_resolutions / self.total_interactions) * 100
    
    def __repr__(self) -> str:
        return f"<AgentPerformance(agent={self.agent_name}, date={self.date}, success_rate={self.success_rate:.1f}%)>"