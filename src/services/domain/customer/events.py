"""
Customer Domain Events - Event definitions
"""
from dataclasses import dataclass
from uuid import UUID
from core.events import DomainEvent

@dataclass
class CustomerCreatedEvent(DomainEvent):
    """Customer account was created"""
    customer_id: UUID
    email: str
    plan: str

@dataclass
class CustomerPlanUpgradedEvent(DomainEvent):
    """Customer upgraded their plan"""
    customer_id: UUID
    email: str
    old_plan: str
    new_plan: str
    annual_value_change: float

@dataclass
class CustomerPlanDowngradedEvent(DomainEvent):
    """Customer downgraded their plan"""
    customer_id: UUID
    email: str
    old_plan: str
    new_plan: str
    annual_value_change: float

@dataclass
class RateLimitExceededEvent(DomainEvent):
    """Customer exceeded rate limit"""
    customer_id: UUID
    email: str
    plan: str
    limit: int
    current_count: int

@dataclass
class CustomerBlockedEvent(DomainEvent):
    """Customer account was blocked"""
    customer_id: UUID
    email: str
    reason: str
    blocked_by: UUID