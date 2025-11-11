"""
Customer routes - HTTP endpoints for customer management

Thin controllers that delegate to CustomerApplicationService.
"""

from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import Optional

from api.dependencies import get_customer_application_service
from api.error_handlers import map_error_to_http
from services.application.customer_service import CustomerApplicationService

router = APIRouter()


@router.post("", status_code=201)
async def create_customer(
    email: str,
    name: Optional[str] = None,
    plan: str = "free",
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Create new customer"""
    result = await service.create_customer(
        email=email,
        name=name,
        plan=plan
    )
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/{customer_id}")
async def get_customer_profile(
    customer_id: UUID,
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Get customer profile with statistics"""
    result = await service.get_customer_profile(customer_id)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.put("/{customer_id}/plan")
async def update_customer_plan(
    customer_id: UUID,
    new_plan: str,
    action: str = Query(..., regex="^(upgrade|downgrade)$"),
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Update customer plan (upgrade or downgrade)"""
    if action == "upgrade":
        result = await service.upgrade_plan(customer_id, new_plan)
    else:
        result = await service.downgrade_plan(customer_id, new_plan)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value