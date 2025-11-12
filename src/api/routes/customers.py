"""
Customer routes - HTTP endpoints for customer management

"""
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from pydantic import BaseModel

from api.dependencies import get_customer_application_service
from api.error_handlers import map_error_to_http
from services.application.customer_service import CustomerApplicationService
from utils.logging.setup import get_logger

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
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Create new customer"""
    logger.info(
        "create_customer_endpoint_called",
        email=request.email,
        plan=request.plan
    )
    
    result = await service.create_customer(
        email=request.email,
        name=request.name,
        plan=request.plan
    )
    
    if result.is_failure:
        logger.warning(
            "create_customer_failed",
            email=request.email,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "create_customer_success",
        customer_id=result.value.get("customer_id"),
        email=request.email,
        plan=request.plan
    )
    
    return result.value


@router.get("/customers/{customer_id}")
async def get_customer_profile(
    customer_id: UUID,
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Get customer profile with statistics"""
    logger.debug(
        "get_customer_profile_endpoint_called",
        customer_id=str(customer_id)
    )
    
    result = await service.get_customer_profile(customer_id)
    
    if result.is_failure:
        logger.warning(
            "get_customer_profile_failed",
            customer_id=str(customer_id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.debug(
        "get_customer_profile_success",
        customer_id=str(customer_id)
    )
    
    return result.value


@router.post("/customers/{customer_id}/upgrade")
async def upgrade_customer_plan(
    customer_id: UUID,
    request: PlanChangeRequest,
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Upgrade customer plan"""
    logger.info(
        "upgrade_customer_plan_endpoint_called",
        customer_id=str(customer_id),
        new_plan=request.new_plan
    )
    
    result = await service.upgrade_plan(
        customer_id=customer_id,
        new_plan=request.new_plan
    )
    
    if result.is_failure:
        logger.warning(
            "upgrade_customer_plan_failed",
            customer_id=str(customer_id),
            new_plan=request.new_plan,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "upgrade_customer_plan_success",
        customer_id=str(customer_id),
        old_plan=result.value.get("old_plan"),
        new_plan=result.value.get("new_plan")
    )
    
    return result.value


@router.post("/customers/{customer_id}/downgrade")
async def downgrade_customer_plan(
    customer_id: UUID,
    request: PlanChangeRequest,
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Downgrade customer plan"""
    logger.info(
        "downgrade_customer_plan_endpoint_called",
        customer_id=str(customer_id),
        new_plan=request.new_plan
    )
    
    result = await service.downgrade_plan(
        customer_id=customer_id,
        new_plan=request.new_plan
    )
    
    if result.is_failure:
        logger.warning(
            "downgrade_customer_plan_failed",
            customer_id=str(customer_id),
            new_plan=request.new_plan,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "downgrade_customer_plan_success",
        customer_id=str(customer_id),
        old_plan=result.value.get("old_plan"),
        new_plan=result.value.get("new_plan")
    )
    
    return result.value