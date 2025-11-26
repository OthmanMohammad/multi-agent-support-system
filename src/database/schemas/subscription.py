"""
Subscription and billing Pydantic schemas - Data Transfer Objects
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Subscription Schemas
# ============================================================================


class SubscriptionBase(BaseModel):
    """Base schema for subscriptions"""

    customer_id: UUID
    plan: str = Field(..., pattern="^(free|basic|premium|enterprise)$")
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$")
    mrr: Decimal
    arr: Decimal | None = None
    seats_total: int = 1
    seats_used: int = 1
    status: str = Field("active", pattern="^(active|past_due|canceled|unpaid|trialing)$")
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    canceled_at: datetime | None = None
    trial_start: datetime | None = None
    trial_end: datetime | None = None
    extra_metadata: dict = Field(default_factory=dict)


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a subscription"""

    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""

    plan: str | None = Field(None, pattern="^(free|basic|premium|enterprise)$")
    billing_cycle: str | None = Field(None, pattern="^(monthly|annual)$")
    mrr: Decimal | None = None
    arr: Decimal | None = None
    seats_total: int | None = None
    seats_used: int | None = None
    status: str | None = Field(None, pattern="^(active|past_due|canceled|unpaid|trialing)$")
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool | None = None
    canceled_at: datetime | None = None
    trial_start: datetime | None = None
    trial_end: datetime | None = None
    extra_metadata: dict | None = None


class SubscriptionInDB(SubscriptionBase):
    """Schema for subscription as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

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
    subscription_id: UUID | None = None
    invoice_number: str = Field(..., max_length=50)
    amount: Decimal
    currency: str = Field("USD", max_length=3)
    status: str = Field("draft", pattern="^(draft|open|paid|void|uncollectible)$")
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    extra_metadata: dict = Field(default_factory=dict)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice"""

    pass


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""

    subscription_id: UUID | None = None
    invoice_number: str | None = Field(None, max_length=50)
    amount: Decimal | None = None
    currency: str | None = Field(None, max_length=3)
    status: str | None = Field(None, pattern="^(draft|open|paid|void|uncollectible)$")
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    extra_metadata: dict | None = None


class InvoiceInDB(InvoiceBase):
    """Schema for invoice as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

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
    invoice_id: UUID | None = None
    amount: Decimal
    currency: str = Field("USD", max_length=3)
    status: str = Field("pending", pattern="^(pending|succeeded|failed|canceled|refunded)$")
    payment_method: str | None = Field(None, max_length=50)
    transaction_id: str | None = Field(None, max_length=255)
    processed_at: datetime | None = None
    failed_reason: str | None = None
    extra_metadata: dict = Field(default_factory=dict)


class PaymentCreate(PaymentBase):
    """Schema for creating a payment"""

    pass


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""

    invoice_id: UUID | None = None
    amount: Decimal | None = None
    currency: str | None = Field(None, max_length=3)
    status: str | None = Field(None, pattern="^(pending|succeeded|failed|canceled|refunded)$")
    payment_method: str | None = Field(None, max_length=50)
    transaction_id: str | None = Field(None, max_length=255)
    processed_at: datetime | None = None
    failed_reason: str | None = None
    extra_metadata: dict | None = None


class PaymentInDB(PaymentBase):
    """Schema for payment as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

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
    unit: str | None = Field(None, max_length=50)
    timestamp: datetime
    extra_metadata: dict = Field(default_factory=dict)


class UsageEventCreate(UsageEventBase):
    """Schema for creating a usage event"""

    pass


class UsageEventUpdate(BaseModel):
    """Schema for updating a usage event"""

    event_type: str | None = Field(None, max_length=50)
    quantity: int | None = None
    unit: str | None = Field(None, max_length=50)
    timestamp: datetime | None = None
    extra_metadata: dict | None = None


class UsageEventInDB(UsageEventBase):
    """Schema for usage event as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

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
    reason: str | None = None
    expires_at: datetime | None = None
    used_amount: Decimal = Decimal("0")
    status: str = Field("active", pattern="^(active|used|expired|canceled)$")
    extra_metadata: dict = Field(default_factory=dict)


class CreditCreate(CreditBase):
    """Schema for creating a credit"""

    pass


class CreditUpdate(BaseModel):
    """Schema for updating a credit"""

    amount: Decimal | None = None
    currency: str | None = Field(None, max_length=3)
    credit_type: str | None = Field(None, pattern="^(promotional|refund|goodwill|migration)$")
    reason: str | None = None
    expires_at: datetime | None = None
    used_amount: Decimal | None = None
    status: str | None = Field(None, pattern="^(active|used|expired|canceled)$")
    extra_metadata: dict | None = None


class CreditInDB(CreditBase):
    """Schema for credit as stored in database"""

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    deleted_at: datetime | None = None
    deleted_by: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class CreditResponse(CreditInDB):
    """Schema for credit API response"""

    remaining_amount: float
    is_expired: bool
