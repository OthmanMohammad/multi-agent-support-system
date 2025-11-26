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

from src.services.infrastructure.analytics_service import AnalyticsService
from src.services.infrastructure.caching_service import CachingService
from src.services.infrastructure.customer_service import CustomerInfrastructureService
from src.services.infrastructure.knowledge_base_service import KnowledgeBaseService
from src.services.infrastructure.notification_service import NotificationService

__version__ = "1.0.0"

__all__ = [
    "AnalyticsService",
    "CachingService",
    "CustomerInfrastructureService",
    "KnowledgeBaseService",
    "NotificationService",
]
