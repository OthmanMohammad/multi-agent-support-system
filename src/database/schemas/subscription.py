"""
Subscription and billing Pydantic schemas - Data Transfer Objects
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionBase(BaseModel):
    """Base schema for subscriptions"""
    customer_id: UUID
    plan: str = Field(..., pattern="^(free|basic|premium|enterprise)$")
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$")
    mrr: Decimal
    arr: Optional[Decimal] = None
    seats_total: int = 1
    seats_used: int = 1
    status: str = Field("active", pattern="^(active|past_due|canceled|unpaid|trialing)$")
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    extra_metadata: dict = Field(default_factory=dict)


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription"""
    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""
    plan: Optional[str] = Field(None, pattern="^(free|basic|premium|enterprise)$")
    billing_cycle: Optional[str] = Field(None, pattern="^(monthly|annual)$")
    mrr: Optional[Decimal] = None
    arr: Optional[Decimal] = None
    seats_total: Optional[int] = None
    seats_used: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(active|past_due|canceled|unpaid|trialing)$")
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None
    canceled_at: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class SubscriptionInDB(SubscriptionBase):
    """Schema for subscription as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(SubscriptionInDB):
    """Schema for subscription API response"""
    is_active: bool
    is_trial: bool
    days_until_renewal: int
    seat_utilization: float


# ============================================================================
# Invoice Schemas
# ============================================================================

class InvoiceBase(BaseModel):
    """Base schema for invoices"""
    customer_id: UUID
    subscription_id: Optional[UUID] = None
    invoice_number: str = Field(..., max_length=50)
    amount: Decimal
    currency: str = Field("USD", max_length=3)
    status: str = Field("draft", pattern="^(draft|open|paid|void|uncollectible)$")
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    extra_metadata: dict = Field(default_factory=dict)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice"""
    pass


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""
    subscription_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(None, max_length=50)
    amount: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = Field(None, pattern="^(draft|open|paid|void|uncollectible)$")
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class InvoiceInDB(InvoiceBase):
    """Schema for invoice as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(InvoiceInDB):
    """Schema for invoice API response"""
    is_paid: bool
    is_overdue: bool


# ============================================================================
# Payment Schemas
# ============================================================================

class PaymentBase(BaseModel):
    """Base schema for payments"""
    customer_id: UUID
    invoice_id: Optional[UUID] = None
    amount: Decimal
    currency: str = Field("USD", max_length=3)
    status: str = Field("pending", pattern="^(pending|succeeded|failed|canceled|refunded)$")
    payment_method: Optional[str] = Field(None, max_length=50)
    transaction_id: Optional[str] = Field(None, max_length=255)
    processed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    extra_metadata: dict = Field(default_factory=dict)


class PaymentCreate(PaymentBase):
    """Schema for creating a payment"""
    pass


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    invoice_id: Optional[UUID] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = Field(None, pattern="^(pending|succeeded|failed|canceled|refunded)$")
    payment_method: Optional[str] = Field(None, max_length=50)
    transaction_id: Optional[str] = Field(None, max_length=255)
    processed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    extra_metadata: Optional[dict] = None


class PaymentInDB(PaymentBase):
    """Schema for payment as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(PaymentInDB):
    """Schema for payment API response"""
    is_successful: bool


# ============================================================================
# UsageEvent Schemas
# ============================================================================

class UsageEventBase(BaseModel):
    """Base schema for usage events"""
    customer_id: UUID
    event_type: str = Field(..., max_length=50)
    quantity: int = 1
    unit: Optional[str] = Field(None, max_length=50)
    timestamp: datetime
    extra_metadata: dict = Field(default_factory=dict)


class UsageEventCreate(UsageEventBase):
    """Schema for creating a usage event"""
    pass


class UsageEventUpdate(BaseModel):
    """Schema for updating a usage event"""
    event_type: Optional[str] = Field(None, max_length=50)
    quantity: Optional[int] = None
    unit: Optional[str] = Field(None, max_length=50)
    timestamp: Optional[datetime] = None
    extra_metadata: Optional[dict] = None


class UsageEventInDB(UsageEventBase):
    """Schema for usage event as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class UsageEventResponse(UsageEventInDB):
    """Schema for usage event API response"""
    pass


# ============================================================================
# Credit Schemas
# ============================================================================

class CreditBase(BaseModel):
    """Base schema for credits"""
    customer_id: UUID
    amount: Decimal
    currency: str = Field("USD", max_length=3)
    credit_type: str = Field(..., pattern="^(promotional|refund|goodwill|migration)$")
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    used_amount: Decimal = Decimal("0")
    status: str = Field("active", pattern="^(active|used|expired|canceled)$")
    extra_metadata: dict = Field(default_factory=dict)


class CreditCreate(CreditBase):
    """Schema for creating a credit"""
    pass


class CreditUpdate(BaseModel):
    """Schema for updating a credit"""
    amount: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    credit_type: Optional[str] = Field(None, pattern="^(promotional|refund|goodwill|migration)$")
    reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    used_amount: Optional[Decimal] = None
    status: Optional[str] = Field(None, pattern="^(active|used|expired|canceled)$")
    extra_metadata: Optional[dict] = None


class CreditInDB(CreditBase):
    """Schema for credit as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class CreditResponse(CreditInDB):
    """Schema for credit API response"""
    remaining_amount: float
    is_expired: bool
