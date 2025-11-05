"""
Services package - Business logic layer

This package contains service classes that implement business logic,
coordinate between repositories and domain models, and return Results
instead of raising exceptions.

Architecture:
- Services use Result pattern for error handling
- Services coordinate repositories via Unit of Work
- Services publish Domain Events for side effects
- Services use Specifications for business rules

Usage:
    from services.base import BaseService
    
    class CustomerService(BaseService):
        def __init__(self, uow: UnitOfWork):
            super().__init__()
            self.uow = uow
        
        def create_customer(self, email: str) -> Result[Customer]:
            # Validation
            validation = self.require_not_none(email, "email")
            if validation.is_failure:
                return validation
            
            if not self.is_valid_email(email):
                return Result.fail(ValidationError(
                    message="Invalid email format",
                    field="email",
                    value=email
                ))
            
            # Check if exists
            existing = await self.uow.customers.get_by_email(email)
            if existing:
                return Result.fail(ConflictError(
                    message="Customer with this email already exists",
                    conflicting_id=email
                ))
            
            # Create
            customer = await self.uow.customers.create(email=email)
            
            # Publish event
            from core.events import get_event_bus
            event = CustomerCreatedEvent(customer_id=customer.id, email=email)
            get_event_bus().publish(event)
            
            return Result.ok(customer)
"""

from services.base import BaseService

__version__ = "1.0.0"

__all__ = ["BaseService"]