"""
Customer routes - HTTP endpoints for customer management
"""
from fastapi import APIRouter, Depends, Query, Body
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr

from api.dependencies import get_customer_application_service
from api.error_handlers import map_error_to_http
from services.application.customer_service import CustomerApplicationService

router = APIRouter()


# ADDED: Request model for customer creation
class CreateCustomerRequest(BaseModel):
    """Request model for creating a customer"""
    email: EmailStr
    name: Optional[str] = None
    plan: str = "free"


@router.post("", status_code=201)
async def create_customer(
    request: CreateCustomerRequest,  # FIXED: Use request body instead of query params
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Create new customer"""
    result = await service.create_customer(
        email=request.email,
        name=request.name,
        plan=request.plan
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


# ADDED: Request model for plan update
class UpdatePlanRequest(BaseModel):
    """Request model for updating customer plan"""
    new_plan: str


@router.put("/{customer_id}/plan")
async def update_customer_plan(
    customer_id: UUID,
    action: str = Query(..., regex="^(upgrade|downgrade)$"),
    request: UpdatePlanRequest = Body(...),  # FIXED: Use request body
    service: CustomerApplicationService = Depends(get_customer_application_service)
):
    """Update customer plan (upgrade or downgrade)"""
    if action == "upgrade":
        result = await service.upgrade_plan(customer_id, request.new_plan)
    else:
        result = await service.downgrade_plan(customer_id, request.new_plan)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value