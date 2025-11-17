"""
Service Dependencies for FastAPI Dependency Injection

Provides application service instances for route handlers.
"""

from typing import AsyncGenerator
from fastapi import Depends

from src.database.unit_of_work import UnitOfWork
from src.services.application.conversation_service import ConversationApplicationService
from src.services.application.customer_service import CustomerApplicationService
from src.services.domain.conversation.domain_service import ConversationDomainService
from src.services.domain.customer.domain_service import CustomerDomainService
from src.services.infrastructure.customer_service import CustomerInfrastructureService
from src.services.infrastructure.analytics_service import AnalyticsService
from src.workflow.engine import AgentWorkflowEngine


async def get_conversation_application_service() -> AsyncGenerator[ConversationApplicationService, None]:
    """
    Dependency that provides ConversationApplicationService instance.

    Creates all required dependencies and yields the service.
    This is called per-request by FastAPI.

    Yields:
        ConversationApplicationService instance
    """
    # Create dependencies
    uow = UnitOfWork()
    domain_service = ConversationDomainService()
    customer_service = CustomerInfrastructureService()
    workflow_engine = AgentWorkflowEngine()
    analytics_service = AnalyticsService()

    # Create and yield the service
    service = ConversationApplicationService(
        uow=uow,
        domain_service=domain_service,
        customer_service=customer_service,
        workflow_engine=workflow_engine,
        analytics_service=analytics_service
    )

    try:
        yield service
    finally:
        # Cleanup if needed
        pass


async def get_customer_application_service() -> AsyncGenerator[CustomerApplicationService, None]:
    """
    Dependency that provides CustomerApplicationService instance.

    Yields:
        CustomerApplicationService instance
    """
    uow = UnitOfWork()
    domain_service = CustomerDomainService()
    infrastructure_service = CustomerInfrastructureService()

    service = CustomerApplicationService(
        uow=uow,
        domain_service=domain_service,
        infrastructure_service=infrastructure_service
    )

    try:
        yield service
    finally:
        pass


async def get_analytics_service() -> AsyncGenerator[AnalyticsService, None]:
    """
    Dependency that provides AnalyticsService instance.

    Yields:
        AnalyticsService instance
    """
    service = AnalyticsService()

    try:
        yield service
    finally:
        pass
    