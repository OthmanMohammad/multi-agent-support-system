"""
Domain Services - Pure business logic layer
Domain services contain ONLY business logic with NO external dependencies.
They are pure functions that:

Accept all data as parameters
Return Result objects
Create (but don't publish) events
Use specifications for business rules
Are easily testable without mocking

Usage:
from src.services.domain import ConversationDomainService
service = ConversationDomainService()

# Validate conversation creation
result = service.validate_conversation_creation(
    customer_plan="free",
    today_conversation_count=5,
    customer_blocked=False
)

if result.is_success:
    # Proceed with creation
    pass
"""

from src.services.domain.conversation.domain_service import ConversationDomainService
from src.services.domain.customer.domain_service import CustomerDomainService

version = "1.0.0"

__all__ = [
    "ConversationDomainService",
    "CustomerDomainService",
]
