"""
Services package - Business logic layer

This package contains service classes that implement business logic,
coordinate between repositories and domain models, and return Results
instead of raising exceptions.

Architecture Layers:
- Domain Services: Pure business logic, no external dependencies
- Infrastructure Services: Data access and external integrations
- Application Services: Orchestration and workflow coordination (future)

Usage:
    # Domain services (pure business logic)
    from services.domain import ConversationDomainService, CustomerDomainService
    
    # Infrastructure services (data access)
    from services.infrastructure import (
        CustomerInfrastructureService,
        KnowledgeBaseService,
        AnalyticsService,
        NotificationService,
        CachingService
    )
    
    # Base service for custom services
    from services.base import BaseService
"""

from services.base import BaseService

# Domain services
from services.domain.conversation import ConversationDomainService
from services.domain.customer import CustomerDomainService

# Infrastructure services
from services.infrastructure import (
    CustomerInfrastructureService,
    KnowledgeBaseService,
    AnalyticsService,
    NotificationService,
    CachingService,
)

__version__ = "1.0.0"

__all__ = [
    # Base
    "BaseService",
    # Domain Services
    "ConversationDomainService",
    "CustomerDomainService",
    # Infrastructure Services
    "CustomerInfrastructureService",
    "KnowledgeBaseService",
    "AnalyticsService",
    "NotificationService",
    "CachingService",
]