"""
Customer routes - HTTP endpoints for customer management

All endpoints require authentication via JWT token or API key.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.api.dependencies import get_customer_application_service
from src.api.dependencies.auth_dependencies import get_current_user_or_api_key
from src.api.error_handlers import map_error_to_http
from src.database.models.user import User
from src.services.application.customer_service import CustomerApplicationService
from src.utils.logging.setup import get_logger

router = APIRouter()
logger = get_logger(__name__)


class CustomerCreateRequest(BaseModel):
    """Request model for creating customer"""

    email: str
    name: str = None
    plan: str = "free"


class PlanChangeRequest(BaseModel):
    """Request model for plan changes"""

    new_plan: str


@router.post("/customers", status_code=201)
async def create_customer(
    request: CustomerCreateRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    service: CustomerApplicationService = Depends(get_customer_application_service),
):
    """Create new customer

    Requires authentication via JWT token or API key.
    """
    logger.info(
        "create_customer_endpoint_called",
        email=request.email,
        plan=request.plan,
        user_id=str(current_user.id),
    )

    result = await service.create_customer(
        email=request.email, name=request.name, plan=request.plan
    )

    if result.is_failure:
        logger.warning(
            "create_customer_failed", email=request.email, error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "create_customer_success",
        customer_id=result.value.get("customer_id"),
        email=request.email,
        plan=request.plan,
    )

    return result.value


@router.get("/customers/{customer_id}")
async def get_customer_profile(
    customer_id: UUID,
    current_user: User = Depends(get_current_user_or_api_key),
    service: CustomerApplicationService = Depends(get_customer_application_service),
):
    """Get customer profile with statistics

    Requires authentication via JWT token or API key.
    """
    logger.debug("get_customer_profile_endpoint_called", customer_id=str(customer_id))

    result = await service.get_customer_profile(customer_id)

    if result.is_failure:
        logger.warning(
            "get_customer_profile_failed",
            customer_id=str(customer_id),
            error_type=type(result.error).__name__,
        )
        raise map_error_to_http(result.error)

    logger.debug("get_customer_profile_success", customer_id=str(customer_id))

    return result.value


@router.get("/customers")
async def list_customers(
    plan: str | None = Query(None, description="Filter by plan"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    current_user: User = Depends(get_current_user_or_api_key),
    service: CustomerApplicationService = Depends(get_customer_application_service),
):
    """List all customers with optional filters

    Requires authentication via JWT token or API key.
    """
    logger.debug("list_customers_endpoint_called", plan=plan, limit=limit)

    result = await service.list_customers(plan=plan, limit=limit)

    if result.is_failure:
        logger.warning("list_customers_failed", plan=plan, error_type=type(result.error).__name__)
        raise map_error_to_http(result.error)

    logger.info("list_customers_success", count=len(result.value), plan=plan)

    return result.value


@router.delete("/customers/{customer_id}", status_code=200)
async def delete_customer(
    customer_id: UUID,
    current_user: User = Depends(get_current_user_or_api_key),
    service: CustomerApplicationService = Depends(get_customer_application_service),
):
    """Delete a customer

    Requires authentication via JWT token or API key.
    """
    logger.warning("delete_customer_endpoint_called", customer_id=str(customer_id))

    result = await service.delete_customer(customer_id)

    if result.is_failure:
        logger.error(
            "delete_customer_failed",
            customer_id=str(customer_id),
            error_type=type(result.error).__name__,
        )
        raise map_error_to_http(result.error)

    logger.info("delete_customer_success", customer_id=str(customer_id))

    return {"status": "deleted", "customer_id": str(customer_id)}


@router.post("/customers/{customer_id}/upgrade")
async def upgrade_customer_plan(
    customer_id: UUID,
    request: PlanChangeRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    service: CustomerApplicationService = Depends(get_customer_application_service),
):
    """Upgrade customer plan

    Requires authentication via JWT token or API key.
    """
    logger.info(
        "upgrade_customer_plan_endpoint_called",
        customer_id=str(customer_id),
        new_plan=request.new_plan,
    )

    result = await service.upgrade_plan(customer_id=customer_id, new_plan=request.new_plan)

    if result.is_failure:
        logger.warning(
            "upgrade_customer_plan_failed",
            customer_id=str(customer_id),
            new_plan=request.new_plan,
            error_type=type(result.error).__name__,
        )
        raise map_error_to_http(result.error)

    logger.info(
        "upgrade_customer_plan_success",
        customer_id=str(customer_id),
        old_plan=result.value.get("old_plan"),
        new_plan=result.value.get("new_plan"),
    )

    return result.value


@router.post("/customers/{customer_id}/downgrade")
async def downgrade_customer_plan(
    customer_id: UUID,
    request: PlanChangeRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    service: CustomerApplicationService = Depends(get_customer_application_service),
):
    """Downgrade customer plan

    Requires authentication via JWT token or API key.
    """
    logger.info(
        "downgrade_customer_plan_endpoint_called",
        customer_id=str(customer_id),
        new_plan=request.new_plan,
    )

    result = await service.downgrade_plan(customer_id=customer_id, new_plan=request.new_plan)

    if result.is_failure:
        logger.warning(
            "downgrade_customer_plan_failed",
            customer_id=str(customer_id),
            new_plan=request.new_plan,
            error_type=type(result.error).__name__,
        )
        raise map_error_to_http(result.error)

    logger.info(
        "downgrade_customer_plan_success",
        customer_id=str(customer_id),
        old_plan=result.value.get("old_plan"),
        new_plan=result.value.get("new_plan"),
    )

    return result.value
