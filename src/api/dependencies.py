"""
FastAPI dependencies for database access and services
Provides repository instances, Unit of Work, and Application Services to API endpoints
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db_session
from src.database.repositories import (
    AgentPerformanceRepository,
    ConversationRepository,
    CustomerRepository,
    MessageRepository,
)
from src.database.unit_of_work import UnitOfWork
from src.database.unit_of_work import get_unit_of_work as _get_uow

# NEW: Import application services
from src.services.application.conversation_service import ConversationApplicationService
from src.services.application.customer_service import CustomerApplicationService

# NEW: Import domain and infrastructure services
from src.services.domain.conversation.domain_service import ConversationDomainService
from src.services.domain.customer.domain_service import CustomerDomainService
from src.services.infrastructure.analytics_service import AnalyticsService
from src.services.infrastructure.customer_service import CustomerInfrastructureService
from src.workflow.engine import AgentWorkflowEngine

# ===== CURRENT USER EXTRACTION =====


async def get_current_user_id(x_user_id: str | None = Header(None)) -> UUID | None:
    """
    Extract current user ID from request headers

    This is a placeholder for proper authentication.
    In production, use JWT tokens or OAuth.

    Args:
        x_user_id: User ID from X-User-ID header

    Returns:
        User UUID or None
    """
    if x_user_id:
        try:
            return UUID(x_user_id)
        except ValueError:
            return None
    return None


# ===== UNIT OF WORK DEPENDENCY =====


async def get_uow(
    current_user_id: UUID | None = Depends(get_current_user_id),
) -> AsyncGenerator[UnitOfWork, None]:
    """
    Dependency to get Unit of Work with automatic transaction management

    Usage:
        @app.post("/endpoint")
        async def endpoint(uow: UnitOfWork = Depends(get_uow)):
            customer = await uow.customers.create(...)
            conversation = await uow.conversations.create(...)
            # Transaction commits automatically

    Args:
        current_user_id: Current user ID from auth headers

    Yields:
        UnitOfWork instance with transaction management
    """
    async with _get_uow(current_user_id) as uow:
        yield uow


# ===== APPLICATION SERVICE DEPENDENCIES (NEW) =====


async def get_conversation_application_service(
    uow: UnitOfWork = Depends(get_uow),
) -> ConversationApplicationService:
    """
    Get conversation application service with all dependencies

    This is where dependency injection happens for the orchestration layer.

    Returns:
        ConversationApplicationService ready to use
    """
    # Create domain service (pure, no dependencies)
    domain_service = ConversationDomainService()

    # Create infrastructure services
    customer_service = CustomerInfrastructureService(uow)
    analytics_service = AnalyticsService(uow)

    # Create workflow engine
    workflow_engine = AgentWorkflowEngine()

    # Create and return application service
    return ConversationApplicationService(
        uow=uow,
        domain_service=domain_service,
        customer_service=customer_service,
        workflow_engine=workflow_engine,
        analytics_service=analytics_service,
    )


async def get_customer_application_service(
    uow: UnitOfWork = Depends(get_uow),
) -> CustomerApplicationService:
    """
    Get customer application service with all dependencies

    Returns:
        CustomerApplicationService ready to use
    """
    # Create domain service (pure, no dependencies)
    domain_service = CustomerDomainService()

    # Create infrastructure service
    infrastructure_service = CustomerInfrastructureService(uow)

    # Create and return application service
    return CustomerApplicationService(
        uow=uow, domain_service=domain_service, infrastructure_service=infrastructure_service
    )


async def get_analytics_service(uow: UnitOfWork = Depends(get_uow)) -> AnalyticsService:
    """
    Get analytics service

    Returns:
        AnalyticsService ready to use
    """
    return AnalyticsService(uow)


# ===== LEGACY DEPENDENCIES (Backward Compatibility) =====


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session (legacy)

    DEPRECATED: Use get_uow instead for better transaction management
    """
    async with get_db_session() as session:
        yield session


async def get_customer_repo(session: AsyncSession = Depends(get_db)) -> CustomerRepository:
    """DEPRECATED: Use get_uow().customers instead"""
    return CustomerRepository(session)


async def get_conversation_repo(session: AsyncSession = Depends(get_db)) -> ConversationRepository:
    """DEPRECATED: Use get_uow().conversations instead"""
    return ConversationRepository(session)


async def get_message_repo(session: AsyncSession = Depends(get_db)) -> MessageRepository:
    """DEPRECATED: Use get_uow().messages instead"""
    return MessageRepository(session)


async def get_agent_performance_repo(
    session: AsyncSession = Depends(get_db),
) -> AgentPerformanceRepository:
    """DEPRECATED: Use get_uow().agent_performance instead"""
    return AgentPerformanceRepository(session)
