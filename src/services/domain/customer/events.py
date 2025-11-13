"""
Customer Domain Events - Event definitions
"""

from dataclasses import dataclass, field
from uuid import UUID
from src.core.events import DomainEvent


@dataclass
class CustomerCreatedEvent(DomainEvent):
    """Customer account was created"""
    customer_id: UUID = field(default=None)
    email: str = field(default="")
    plan: str = field(default="free")


@dataclass
class CustomerPlanUpgradedEvent(DomainEvent):
    """Customer upgraded their plan"""
    customer_id: UUID = field(default=None)
    email: str = field(default="")
    old_plan: str = field(default="")
    new_plan: str = field(default="")
    annual_value_change: float = field(default=0.0)


@dataclass
class CustomerPlanDowngradedEvent(DomainEvent):
    """Customer downgraded their plan"""
    customer_id: UUID = field(default=None)
    email: str = field(default="")
    old_plan: str = field(default="")
    new_plan: str = field(default="")
    annual_value_change: float = field(default=0.0)


@dataclass
class RateLimitExceededEvent(DomainEvent):
    """Customer exceeded rate limit"""
    customer_id: UUID = field(default=None)
    email: str = field(default="")
    plan: str = field(default="")
    limit: int = field(default=0)
    current_count: int = field(default=0)


@dataclass
class CustomerBlockedEvent(DomainEvent):
    """Customer account was blocked"""
    customer_id: UUID = field(default=None)
    email: str = field(default="")
    reason: str = field(default="")
    blocked_by: UUID = field(default=None)