"""
Analytics Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# ConversationAnalytics Schemas
# ============================================================================


class ConversationAnalyticsBase(BaseModel):
    """Base schema for conversation analytics"""

    date: datetime
    channel: str | None = Field(None, max_length=50)
    total_conversations: int = 0
    resolved_conversations: int = 0
    escalated_conversations: int = 0
    avg_resolution_time_seconds: int | None = None
    avg_sentiment: float | None = None
    avg_csat: float | None = None
    extra_metadata: dict = Field(default_factory=dict)


class ConversationAnalyticsCreate(ConversationAnalyticsBase):
    """Schema for creating conversation analytics"""

    pass


class ConversationAnalyticsUpdate(BaseModel):
    """Schema for updating conversation analytics"""

    date: datetime | None = None
    channel: str | None = Field(None, max_length=50)
    total_conversations: int | None = None
    resolved_conversations: int | None = None
    escalated_conversations: int | None = None
    avg_resolution_time_seconds: int | None = None
    avg_sentiment: float | None = None
    avg_csat: float | None = None
    extra_metadata: dict | None = None


class ConversationAnalyticsInDB(ConversationAnalyticsBase):
    """Schema for conversation analytics as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ConversationAnalyticsResponse(ConversationAnalyticsInDB):
    """Schema for conversation analytics API response"""

    resolution_rate: float
    escalation_rate: float


# ============================================================================
# FeatureUsage Schemas
# ============================================================================


class FeatureUsageBase(BaseModel):
    """Base schema for feature usage"""

    customer_id: UUID
    feature_name: str = Field(..., max_length=100)
    usage_count: int = 0
    last_used_at: datetime | None = None
    date: datetime
    extra_metadata: dict = Field(default_factory=dict)


class FeatureUsageCreate(FeatureUsageBase):
    """Schema for creating feature usage"""

    pass


class FeatureUsageUpdate(BaseModel):
    """Schema for updating feature usage"""

    feature_name: str | None = Field(None, max_length=100)
    usage_count: int | None = None
    last_used_at: datetime | None = None
    date: datetime | None = None
    extra_metadata: dict | None = None


class FeatureUsageInDB(FeatureUsageBase):
    """Schema for feature usage as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class FeatureUsageResponse(FeatureUsageInDB):
    """Schema for feature usage API response"""

    pass


# ============================================================================
# ABTest Schemas
# ============================================================================


class ABTestBase(BaseModel):
    """Base schema for A/B tests"""

    test_name: str = Field(..., max_length=100)
    variant: str = Field(..., max_length=50)
    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    outcome: str | None = Field(None, max_length=50)
    metric_value: float | None = None
    timestamp: datetime
    extra_metadata: dict = Field(default_factory=dict)


class ABTestCreate(ABTestBase):
    """Schema for creating an A/B test"""

    pass


class ABTestUpdate(BaseModel):
    """Schema for updating an A/B test"""

    test_name: str | None = Field(None, max_length=100)
    variant: str | None = Field(None, max_length=50)
    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    outcome: str | None = Field(None, max_length=50)
    metric_value: float | None = None
    timestamp: datetime | None = None
    extra_metadata: dict | None = None


class ABTestInDB(ABTestBase):
    """Schema for A/B test as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ABTestResponse(ABTestInDB):
    """Schema for A/B test API response"""

    pass
