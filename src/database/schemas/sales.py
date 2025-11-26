"""
Sales and leads Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Employee Schemas
# ============================================================================


class EmployeeBase(BaseModel):
    """Base schema for employees"""

    email: str = Field(..., max_length=255)
    name: str = Field(..., max_length=255)
    role: str = Field(..., max_length=50)
    department: str | None = Field(None, max_length=50)
    is_active: bool = True
    extra_metadata: dict = Field(default_factory=dict)


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee"""

    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee"""

    email: str | None = Field(None, max_length=255)
    name: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=50)
    department: str | None = Field(None, max_length=50)
    is_active: bool | None = None
    extra_metadata: dict | None = None


class EmployeeInDB(EmployeeBase):
    """Schema for employee as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

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
    name: str | None = Field(None, max_length=255)
    company: str | None = Field(None, max_length=255)
    title: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    budget: str | None = Field(None, max_length=50)
    authority: str | None = Field(None, max_length=50)
    need_score: Decimal | None = None
    timeline: str | None = Field(None, max_length=50)
    lead_score: int = 0
    qualification_status: str = Field(
        "new", pattern="^(new|mql|sql|qualified|disqualified|converted)$"
    )
    source: str | None = Field(None, max_length=50)
    assigned_to: UUID | None = None
    converted_to_customer_id: UUID | None = None
    converted_at: datetime | None = None
    extra_metadata: dict = Field(default_factory=dict)


class LeadCreate(LeadBase):
    """Schema for creating a lead"""

    pass


class LeadUpdate(BaseModel):
    """Schema for updating a lead"""

    email: str | None = Field(None, max_length=255)
    name: str | None = Field(None, max_length=255)
    company: str | None = Field(None, max_length=255)
    title: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    budget: str | None = Field(None, max_length=50)
    authority: str | None = Field(None, max_length=50)
    need_score: Decimal | None = None
    timeline: str | None = Field(None, max_length=50)
    lead_score: int | None = None
    qualification_status: str | None = Field(
        None, pattern="^(new|mql|sql|qualified|disqualified|converted)$"
    )
    source: str | None = Field(None, max_length=50)
    assigned_to: UUID | None = None
    converted_to_customer_id: UUID | None = None
    converted_at: datetime | None = None
    extra_metadata: dict | None = None


class LeadInDB(LeadBase):
    """Schema for lead as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

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

    lead_id: UUID | None = None
    customer_id: UUID | None = None
    name: str = Field(..., max_length=255)
    value: Decimal
    currency: str = Field("USD", max_length=3)
    stage: str = Field(
        "prospecting",
        pattern="^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$",
    )
    probability: int = 0
    expected_close_date: datetime | None = None
    closed_at: datetime | None = None
    lost_reason: str | None = None
    assigned_to: UUID | None = None
    extra_metadata: dict = Field(default_factory=dict)


class DealCreate(DealBase):
    """Schema for creating a deal"""

    pass


class DealUpdate(BaseModel):
    """Schema for updating a deal"""

    lead_id: UUID | None = None
    customer_id: UUID | None = None
    name: str | None = Field(None, max_length=255)
    value: Decimal | None = None
    currency: str | None = Field(None, max_length=3)
    stage: str | None = Field(
        None, pattern="^(prospecting|qualification|proposal|negotiation|closed_won|closed_lost)$"
    )
    probability: int | None = None
    expected_close_date: datetime | None = None
    closed_at: datetime | None = None
    lost_reason: str | None = None
    assigned_to: UUID | None = None
    extra_metadata: dict | None = None


class DealInDB(DealBase):
    """Schema for deal as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

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

    deal_id: UUID | None = None
    lead_id: UUID | None = None
    activity_type: str = Field(..., pattern="^(call|email|meeting|demo|proposal|follow_up)$")
    subject: str = Field(..., max_length=255)
    description: str | None = None
    outcome: str | None = Field(None, max_length=50)
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    performed_by: UUID | None = None
    extra_metadata: dict = Field(default_factory=dict)


class SalesActivityCreate(SalesActivityBase):
    """Schema for creating a sales activity"""

    pass


class SalesActivityUpdate(BaseModel):
    """Schema for updating a sales activity"""

    deal_id: UUID | None = None
    lead_id: UUID | None = None
    activity_type: str | None = Field(
        None, pattern="^(call|email|meeting|demo|proposal|follow_up)$"
    )
    subject: str | None = Field(None, max_length=255)
    description: str | None = None
    outcome: str | None = Field(None, max_length=50)
    scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    performed_by: UUID | None = None
    extra_metadata: dict | None = None


class SalesActivityInDB(SalesActivityBase):
    """Schema for sales activity as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class SalesActivityResponse(SalesActivityInDB):
    """Schema for sales activity API response"""

    is_completed: bool


# ============================================================================
# Quote Schemas
# ============================================================================


class QuoteBase(BaseModel):
    """Base schema for quotes"""

    deal_id: UUID | None = None
    customer_id: UUID | None = None
    quote_number: str = Field(..., max_length=50)
    total_amount: Decimal
    currency: str = Field("USD", max_length=3)
    status: str = Field("draft", pattern="^(draft|sent|accepted|declined|expired)$")
    valid_until: datetime | None = None
    accepted_at: datetime | None = None
    line_items: list = Field(default_factory=list)
    extra_metadata: dict = Field(default_factory=dict)


class QuoteCreate(QuoteBase):
    """Schema for creating a quote"""

    pass


class QuoteUpdate(BaseModel):
    """Schema for updating a quote"""

    deal_id: UUID | None = None
    customer_id: UUID | None = None
    quote_number: str | None = Field(None, max_length=50)
    total_amount: Decimal | None = None
    currency: str | None = Field(None, max_length=3)
    status: str | None = Field(None, pattern="^(draft|sent|accepted|declined|expired)$")
    valid_until: datetime | None = None
    accepted_at: datetime | None = None
    line_items: list | None = None
    extra_metadata: dict | None = None


class QuoteInDB(QuoteBase):
    """Schema for quote as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class QuoteResponse(QuoteInDB):
    """Schema for quote API response"""

    is_accepted: bool
