"""
Sales and leads Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ============================================================================
# Employee Schemas
# ============================================================================

class EmployeeBase(BaseModel):
    """Base schema for employees"""
    email: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    role: str = Field(..., max_length=50)
    department: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    extra_metadata: dict = Field(default_factory=dict)


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee"""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee"""
    email: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    extra_metadata: Optional[dict] = None


class EmployeeInDB(EmployeeBase):
    """Schema for employee as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeResponse(EmployeeInDB):
    """Schema for employee API response"""
    pass


# ============================================================================
# Lead Schemas
# ============================================================================

class LeadBase(BaseModel):
    """Base schema for leads"""
    email: str = Field(..., max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    budget: Optional[str] = Field(None, max_length=50)
    authority: Optional[str] = Field(None, max_length=50)
    need_score: Optional[Decimal] = None
    timeline: Optional[str] = Field(None, max_length=50)
    lead_score: int = 0
    qualification_status: str = Field("new", pattern="^(new|mql|sql|qualified|disqualified|converted)$")
    source: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[UUID] = None
    converted_to_customer_id: Optional[UUID] = None
    converted_at: Optional[datetime] = None
    extra_metadata: dict = Field(default_factory=dict)


class LeadCreate(LeadBase):
    """Schema for creating a lead"""
    pass


class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    email: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    budget: Optional[str] = Field(None, max_length=50)
    authority: Optional[str] = Field(None, max_length=50)
    need_score: Optional[Decimal] = None
    timeline: Optional[str] = Field(None, max_length=50)
    lead_score: Optional[int] = None
    qualification_status: Optional[str] = Field(None, pattern="^(new|mql|sql|qualified|disqualified|converted)$")
    source: Optional[str] = Field(None, max_length=50)
    assigned_to: Optional[UUID] = None
    converted_to_customer_id: Optional[UUID] = None
    converted_at: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class LeadInDB(LeadBase):
    """Schema for lead as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class LeadResponse(LeadInDB):
    """Schema for lead API response"""
    is_qualified: bool
    is_converted: bool


# ============================================================================
# Deal Schemas
# ============================================================================

class DealBase(BaseModel):
    """Base schema for deals"""
    lead_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    name: str = Field(..., max_length=255)
    value: Decimal
    currency: str = Field("USD", max_length=3)
    stage: str = Field("prospecting", pattern="^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$")
    probability: int = 0
    expected_close_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    lost_reason: Optional[str] = None
    assigned_to: Optional[UUID] = None
    extra_metadata: dict = Field(default_factory=dict)


class DealCreate(DealBase):
    """Schema for creating a deal"""
    pass


class DealUpdate(BaseModel):
    """Schema for updating a deal"""
    lead_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=255)
    value: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    stage: Optional[str] = Field(None, pattern="^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$")
    probability: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    lost_reason: Optional[str] = None
    assigned_to: Optional[UUID] = None
    extra_metadata: Optional[dict] = None


class DealInDB(DealBase):
    """Schema for deal as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class DealResponse(DealInDB):
    """Schema for deal API response"""
    is_won: bool
    is_lost: bool
    is_closed: bool
    weighted_value: float


# ============================================================================
# SalesActivity Schemas
# ============================================================================

class SalesActivityBase(BaseModel):
    """Base schema for sales activities"""
    deal_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    activity_type: str = Field(..., pattern="^(call|email|meeting|demo|proposal|follow_up)$")
    subject: str = Field(..., max_length=255)
    description: Optional[str] = None
    outcome: Optional[str] = Field(None, max_length=50)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    performed_by: Optional[UUID] = None
    extra_metadata: dict = Field(default_factory=dict)


class SalesActivityCreate(SalesActivityBase):
    """Schema for creating a sales activity"""
    pass


class SalesActivityUpdate(BaseModel):
    """Schema for updating a sales activity"""
    deal_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    activity_type: Optional[str] = Field(None, pattern="^(call|email|meeting|demo|proposal|follow_up)$")
    subject: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    outcome: Optional[str] = Field(None, max_length=50)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    performed_by: Optional[UUID] = None
    extra_metadata: Optional[dict] = None


class SalesActivityInDB(SalesActivityBase):
    """Schema for sales activity as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class SalesActivityResponse(SalesActivityInDB):
    """Schema for sales activity API response"""
    is_completed: bool


# ============================================================================
# Quote Schemas
# ============================================================================

class QuoteBase(BaseModel):
    """Base schema for quotes"""
    deal_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    quote_number: str = Field(..., max_length=50)
    total_amount: Decimal
    currency: str = Field("USD", max_length=3)
    status: str = Field("draft", pattern="^(draft|sent|accepted|declined|expired)$")
    valid_until: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    line_items: list = Field(default_factory=list)
    extra_metadata: dict = Field(default_factory=dict)


class QuoteCreate(QuoteBase):
    """Schema for creating a quote"""
    pass


class QuoteUpdate(BaseModel):
    """Schema for updating a quote"""
    deal_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    quote_number: Optional[str] = Field(None, max_length=50)
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = Field(None, pattern="^(draft|sent|accepted|declined|expired)$")
    valid_until: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    line_items: Optional[list] = None
    extra_metadata: Optional[dict] = None


class QuoteInDB(QuoteBase):
    """Schema for quote as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class QuoteResponse(QuoteInDB):
    """Schema for quote API response"""
    is_accepted: bool
