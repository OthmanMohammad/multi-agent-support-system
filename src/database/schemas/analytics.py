"""
Analytics Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# ============================================================================
# ConversationAnalytics Schemas
# ============================================================================

class ConversationAnalyticsBase(BaseModel):
    """Base schema for conversation analytics"""
    date: datetime
    channel: Optional[str] = Field(None, max_length=50)
    total_conversations: int = 0
    resolved_conversations: int = 0
    escalated_conversations: int = 0
    avg_resolution_time_seconds: Optional[int] = None
    avg_sentiment: Optional[float] = None
    avg_csat: Optional[float] = None
    extra_metadata: dict = Field(default_factory=dict)


class ConversationAnalyticsCreate(ConversationAnalyticsBase):
    """Schema for creating conversation analytics"""
    pass


class ConversationAnalyticsUpdate(BaseModel):
    """Schema for updating conversation analytics"""
    date: Optional[datetime] = None
    channel: Optional[str] = Field(None, max_length=50)
    total_conversations: Optional[int] = None
    resolved_conversations: Optional[int] = None
    escalated_conversations: Optional[int] = None
    avg_resolution_time_seconds: Optional[int] = None
    avg_sentiment: Optional[float] = None
    avg_csat: Optional[float] = None
    extra_metadata: Optional[dict] = None


class ConversationAnalyticsInDB(ConversationAnalyticsBase):
    """Schema for conversation analytics as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

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
    last_used_at: Optional[datetime] = None
    date: datetime
    extra_metadata: dict = Field(default_factory=dict)


class FeatureUsageCreate(FeatureUsageBase):
    """Schema for creating feature usage"""
    pass


class FeatureUsageUpdate(BaseModel):
    """Schema for updating feature usage"""
    feature_name: Optional[str] = Field(None, max_length=100)
    usage_count: Optional[int] = None
    last_used_at: Optional[datetime] = None
    date: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class FeatureUsageInDB(FeatureUsageBase):
    """Schema for feature usage as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

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
    customer_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    outcome: Optional[str] = Field(None, max_length=50)
    metric_value: Optional[float] = None
    timestamp: datetime
    extra_metadata: dict = Field(default_factory=dict)


class ABTestCreate(ABTestBase):
    """Schema for creating an A/B test"""
    pass


class ABTestUpdate(BaseModel):
    """Schema for updating an A/B test"""
    test_name: Optional[str] = Field(None, max_length=100)
    variant: Optional[str] = Field(None, max_length=50)
    customer_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    outcome: Optional[str] = Field(None, max_length=50)
    metric_value: Optional[float] = None
    timestamp: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class ABTestInDB(ABTestBase):
    """Schema for A/B test as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class ABTestResponse(ABTestInDB):
    """Schema for A/B test API response"""
    pass
