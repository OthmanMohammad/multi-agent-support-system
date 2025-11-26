"""
Agent Performance Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class AgentPerformanceBase(BaseModel):
    """Base agent performance schema"""

    agent_name: str = Field(..., max_length=50)
    date: datetime
    total_interactions: int = Field(default=0, ge=0)
    successful_resolutions: int = Field(default=0, ge=0)
    escalations: int = Field(default=0, ge=0)
    avg_confidence: float | None = Field(None, ge=0, le=1)
    avg_sentiment: float | None = Field(None, ge=-1, le=1)
    avg_response_time_ms: int | None = Field(None, ge=0)


class AgentPerformanceCreate(AgentPerformanceBase):
    """Schema for creating agent performance record"""

    extra_metadata: dict = Field(default_factory=dict)


class AgentPerformanceUpdate(BaseModel):
    """Schema for updating agent performance"""

    total_interactions: int | None = Field(None, ge=0)
    successful_resolutions: int | None = Field(None, ge=0)
    escalations: int | None = Field(None, ge=0)
    avg_confidence: float | None = Field(None, ge=0, le=1)
    avg_sentiment: float | None = Field(None, ge=-1, le=1)
    avg_response_time_ms: int | None = Field(None, ge=0)
    extra_metadata: dict | None = None


class AgentPerformanceInDB(AgentPerformanceBase):
    """Agent performance as stored in database"""

    id: UUID
    extra_metadata: dict
    created_at: datetime

    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_interactions == 0:
            return 0.0
        return round((self.successful_resolutions / self.total_interactions) * 100, 2)

    model_config = ConfigDict(from_attributes=True)


class AgentPerformanceResponse(AgentPerformanceInDB):
    """Agent performance response for API"""

    pass


class AgentPerformanceSummary(BaseModel):
    """Summary statistics for an agent"""

    agent_name: str
    total_interactions: int
    successful_resolutions: int
    success_rate: float
    avg_confidence: float
    avg_sentiment: float
    total_escalations: int


class AllAgentsSummary(BaseModel):
    """Summary for all agents"""

    agents: dict[str, AgentPerformanceSummary]
    period_days: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
