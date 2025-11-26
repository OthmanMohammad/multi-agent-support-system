"""
Core patterns and infrastructure for the application

This package provides foundational patterns used throughout the application:
- Result Pattern: Railway Oriented Programming for error handling
- Domain Events: Event-driven architecture support
- Specification Pattern: Business rule encapsulation
- Error Types: Structured error handling
- Configuration Management: Type-safe centralized configuration

Usage:
    from core import Result, Error, DomainEvent, Specification, get_settings

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

    # Configuration
    settings = get_settings()
    api_key = settings.anthropic.api_key
"""

from src.core.config import Settings, get_settings
from src.core.config_validator import require_valid_configuration, validate_configuration
from src.core.errors import (
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    ErrorCodes,
    ExternalServiceError,
    InternalError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from src.core.events import (
    DomainEvent,
    EventBus,
    get_event_bus,
    reset_event_bus,
)
from src.core.result import Error, Result
from src.core.specifications import (
    AndSpecification,
    NotSpecification,
    OrSpecification,
    Specification,
)

__version__ = "1.0.0"

__all__ = [
    "AndSpecification",
    "AuthorizationError",
    "BusinessRuleError",
    "ConflictError",
    # Domain Events
    "DomainEvent",
    "Error",
    "ErrorCodes",
    "EventBus",
    "ExternalServiceError",
    "InternalError",
    "NotFoundError",
    "NotSpecification",
    "OrSpecification",
    "RateLimitError",
    # Result Pattern
    "Result",
    "Settings",
    # Specifications
    "Specification",
    # Error Types
    "ValidationError",
    "get_event_bus",
    # Configuration
    "get_settings",
    "require_valid_configuration",
    "reset_event_bus",
    "validate_configuration",
]
