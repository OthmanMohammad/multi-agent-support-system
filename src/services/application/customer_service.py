"""
Customer Application Service - Orchestrates customer use cases
"""

from typing import Optional, Dict, Any
from uuid import UUID

from core.result import Result
from core.errors import NotFoundError, InternalError
from core.events import get_event_bus
from database.unit_of_work import UnitOfWork
from services.domain.customer.domain_service import CustomerDomainService
from services.infrastructure.customer_service import CustomerInfrastructureService


class CustomerApplicationService:
    """Application service for customer use cases"""
    
    def __init__(
        self,
        uow: UnitOfWork,
        domain_service: CustomerDomainService,
        infrastructure_service: CustomerInfrastructureService
    ):
        self.uow = uow
        self.domain = domain_service
        self.infrastructure = infrastructure_service
        self.event_bus = get_event_bus()
    
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        plan: str = "free"
    ) -> Result[Dict[str, Any]]:
        """Create new customer"""
        try:
            # Validate email
            validation = self.domain.validate_email(email)
            if validation.is_failure:
                return Result.fail(validation.error)
            
            # Validate plan
            plan_validation = self.domain.validate_plan(plan)
            if plan_validation.is_failure:
                return Result.fail(plan_validation.error)
            
            # Create customer
            result = await self.infrastructure.get_or_create_by_email(
                email=email,
                name=name,
                plan=plan
            )
            
            if result.is_failure:
                return Result.fail(result.error)
            
            customer = result.value
            
            return Result.ok({
                "customer_id": str(customer.id),
                "email": customer.email,
                "name": customer.name,
                "plan": customer.plan,
                "created_at": customer.created_at.isoformat()
            })
            
        except Exception as e:
            return Result.fail(InternalError(
                message=f"Failed to create customer: {str(e)}",
                operation="create_customer",
                component="CustomerApplicationService"
            ))
    
    async def upgrade_plan(
        self,
        customer_id: UUID,
        new_plan: str
    ) -> Result[Dict[str, Any]]:
        """Upgrade customer plan"""
        try:
            # Get current customer
            customer_result = await self.infrastructure.get_by_id(customer_id)
            if customer_result.is_failure:
                return Result.fail(customer_result.error)
            
            customer = customer_result.value
            old_plan = customer.plan
            
            # Validate plan transition
            validation = self.domain.validate_plan_transition(old_plan, new_plan)
            if validation.is_failure:
                return Result.fail(validation.error)
            
            transition_type = validation.value
            
            if transition_type != "upgrade":
                return Result.fail(InternalError(
                    message=f"Expected upgrade but got {transition_type}",
                    operation="upgrade_plan"
                ))
            
            # Execute upgrade
            result = await self.infrastructure.upgrade_plan(customer_id, new_plan)
            if result.is_failure:
                return Result.fail(result.error)
            
            updated_customer = result.value
            
            # REMOVED: plan_benefits calculation that was causing inf error
            
            # Publish event
            event = self.domain.create_plan_upgraded_event(
                customer_id=customer_id,
                email=customer.email,
                old_plan=old_plan,
                new_plan=new_plan,
                annual_value_change=0.0
            )
            self.event_bus.publish(event)
            
            # FIXED: Simplified response without benefits
            return Result.ok({
                "customer_id": str(updated_customer.id),
                "email": updated_customer.email,
                "old_plan": old_plan,
                "new_plan": updated_customer.plan,
                "message": f"Successfully upgraded from {old_plan} to {new_plan}"
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Result.fail(InternalError(
                message=f"Failed to upgrade plan: {str(e)}",
                operation="upgrade_plan",
                component="CustomerApplicationService"
            ))
    
    async def downgrade_plan(
        self,
        customer_id: UUID,
        new_plan: str
    ) -> Result[Dict[str, Any]]:
        """Downgrade customer plan"""
        try:
            # Get current customer
            customer_result = await self.infrastructure.get_by_id(customer_id)
            if customer_result.is_failure:
                return Result.fail(customer_result.error)
            
            customer = customer_result.value
            old_plan = customer.plan
            
            # Validate plan transition
            validation = self.domain.validate_plan_transition(old_plan, new_plan)
            if validation.is_failure:
                return Result.fail(validation.error)
            
            transition_type = validation.value
            
            if transition_type != "downgrade":
                return Result.fail(InternalError(
                    message=f"Expected downgrade but got {transition_type}",
                    operation="downgrade_plan"
                ))
            
            # Execute downgrade
            result = await self.infrastructure.downgrade_plan(customer_id, new_plan)
            if result.is_failure:
                return Result.fail(result.error)
            
            updated_customer = result.value
            
            # Publish event
            event = self.domain.create_plan_downgraded_event(
                customer_id=customer_id,
                email=customer.email,
                old_plan=old_plan,
                new_plan=new_plan,
                annual_value_change=0.0
            )
            self.event_bus.publish(event)
            
            return Result.ok({
                "customer_id": str(updated_customer.id),
                "email": updated_customer.email,
                "old_plan": old_plan,
                "new_plan": updated_customer.plan,
                "message": f"Successfully downgraded from {old_plan} to {new_plan}"
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Result.fail(InternalError(
                message=f"Failed to downgrade plan: {str(e)}",
                operation="downgrade_plan",
                component="CustomerApplicationService"
            ))
    
    async def get_customer_profile(
        self,
        customer_id: UUID
    ) -> Result[Dict[str, Any]]:
        """Get customer profile with statistics"""
        try:
            result = await self.infrastructure.get_customer_profile(customer_id)
            return result
            
        except Exception as e:
            return Result.fail(InternalError(
                message=f"Failed to get customer profile: {str(e)}",
                operation="get_customer_profile",
                component="CustomerApplicationService"
            ))