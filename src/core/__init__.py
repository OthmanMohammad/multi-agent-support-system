"""
Core patterns and infrastructure for the application

This package provides foundational patterns used throughout the application:
- Result Pattern: Railway Oriented Programming for error handling
- Domain Events: Event-driven architecture support
- Specification Pattern: Business rule encapsulation
- Error Types: Structured error handling

Usage:
    from core import Result, Error, DomainEvent, Specification
    
    # Result pattern
    result = some_operation()
    if result.is_success:
        value = result.value
    else:
        error = result.error
    
    # Domain events
    bus = get_event_bus()
    bus.subscribe(MyEvent, my_handler)
    bus.publish(MyEvent(...))
    
    # Specifications
    can_process = IsActive().and_(HasPermission())
    if can_process.is_satisfied_by(entity):
        process(entity)
"""

from core.result import Result, Error
from core.errors import (
    ValidationError,
    BusinessRuleError,
    NotFoundError,
    ConflictError,
    AuthorizationError,
    RateLimitError,
    InternalError,
    ExternalServiceError,
    ErrorCodes,
)
from core.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    reset_event_bus,
)
from core.specifications import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
)

__version__ = "1.0.0"

__all__ = [
    # Result Pattern
    "Result",
    "Error",
    # Error Types
    "ValidationError",
    "BusinessRuleError",
    "NotFoundError",
    "ConflictError",
    "AuthorizationError",
    "RateLimitError",
    "InternalError",
    "ExternalServiceError",
    "ErrorCodes",
    # Domain Events
    "DomainEvent",
    "EventBus",
    "get_event_bus",
    "reset_event_bus",
    # Specifications
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
]