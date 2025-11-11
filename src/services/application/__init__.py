"""
Application Services - Orchestration and use case coordination

Application services sit between the API layer and domain/infrastructure services.
They orchestrate complex workflows by:
- Coordinating multiple domain services
- Managing transactions via Unit of Work
- Calling infrastructure services for data access
- Publishing domain events
- Handling workflow execution

Architecture:
    API Layer (thin controllers)
        ↓
    Application Services (orchestration) ← YOU ARE HERE
        ↓ ↓ ↓
    Domain Services + Infrastructure Services + Workflow Engine

Example:
    from services.application import ConversationApplicationService
    
    service = ConversationApplicationService(uow, domain_service, customer_service, workflow_engine)
    result = await service.create_conversation(
        customer_email="user@example.com",
        message="I want to upgrade"
    )
"""

from services.application.conversation_service import ConversationApplicationService
from services.application.customer_service import CustomerApplicationService

__version__ = "1.0.0"

__all__ = [
    "ConversationApplicationService",
    "CustomerApplicationService",
]