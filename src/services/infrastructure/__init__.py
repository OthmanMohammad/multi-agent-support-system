"""
Infrastructure Services - Data access and integration layer

Infrastructure services handle technical concerns:
- Database operations (CRUD)
- External API integration
- Caching
- Notifications
- Knowledge base operations

These services are thin wrappers that:
- Return Result objects
- Delegate to repositories via Unit of Work
- Handle external service calls
- Contain NO business logic

Business logic belongs in domain services.
"""

from services.infrastructure.customer_service import CustomerInfrastructureService
from services.infrastructure.knowledge_base_service import KnowledgeBaseService
from services.infrastructure.analytics_service import AnalyticsService
from services.infrastructure.notification_service import NotificationService
from services.infrastructure.caching_service import CachingService

__version__ = "1.0.0"

__all__ = [
    "CustomerInfrastructureService",
    "KnowledgeBaseService",
    "AnalyticsService",
    "NotificationService",
    "CachingService",
]