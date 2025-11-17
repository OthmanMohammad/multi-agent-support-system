"""
Customer Application Service - Orchestrates customer use cases
"""

from typing import Optional, Dict, Any
from uuid import UUID

from src.core.result import Result
from src.core.errors import NotFoundError, InternalError
from src.core.events import get_event_bus
from src.database.unit_of_work import UnitOfWork
from src.services.domain.customer.domain_service import CustomerDomainService
from src.services.infrastructure.customer_service import CustomerInfrastructureService
from src.utils.logging.setup import get_logger


class CustomerApplicationService:
    """
    Application service for customer use cases
    
    """
    
    def __init__(
        self,
        uow: UnitOfWork,
        domain_service: CustomerDomainService,
        infrastructure_service: CustomerInfrastructureService
    ):
        self.uow = uow
        self.domain = domain_service
        self.infrastructure = infrastructure_service
        self._event_bus = None  # Lazy initialization
        self.logger = get_logger(__name__)

        self.logger.debug("customer_application_service_initialized")

    @property
    def event_bus(self):
        """Lazy-load event bus to allow test mocking"""
        if self._event_bus is None:
            self._event_bus = get_event_bus()
        return self._event_bus

    @event_bus.setter
    def event_bus(self, value):
        """Allow direct setting for tests"""
        self._event_bus = value
    
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        plan: str = "free"
    ) -> Result[Dict[str, Any]]:
        """Create new customer"""
        try:
            self.logger.info(
                "customer_creation_started",
                email=email,
                plan=plan
            )
            
            # Validate email
            validation = self.domain.validate_email(email)
            if validation.is_failure:
                self.logger.warning(
                    "customer_creation_validation_failed",
                    email=email,
                    error="invalid_email"
                )
                return Result.fail(validation.error)
            
            # Validate plan
            plan_validation = self.domain.validate_plan(plan)
            if plan_validation.is_failure:
                self.logger.warning(
                    "customer_creation_validation_failed",
                    email=email,
                    plan=plan,
                    error="invalid_plan"
                )
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
            
            self.logger.info(
                "customer_created",
                customer_id=str(customer.id),
                email=email,
                plan=plan
            )
            
            return Result.ok({
                "customer_id": str(customer.id),
                "email": customer.email,
                "name": customer.name,
                "plan": customer.plan,
                "created_at": customer.created_at.isoformat()
            })
            
        except Exception as e:
            self.logger.error(
                "customer_creation_failed",
                email=email,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
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
            self.logger.info(
                "customer_plan_upgrade_started",
                customer_id=str(customer_id),
                new_plan=new_plan
            )
            
            # Get current customer
            customer_result = await self.infrastructure.get_by_id(customer_id)
            if customer_result.is_failure:
                return Result.fail(customer_result.error)
            
            customer = customer_result.value
            old_plan = customer.plan
            
            # Validate plan transition
            validation = self.domain.validate_plan_transition(old_plan, new_plan)
            if validation.is_failure:
                self.logger.warning(
                    "customer_plan_upgrade_validation_failed",
                    customer_id=str(customer_id),
                    old_plan=old_plan,
                    new_plan=new_plan
                )
                return Result.fail(validation.error)
            
            transition_type = validation.value
            
            if transition_type != "upgrade":
                self.logger.warning(
                    "customer_plan_upgrade_incorrect_transition",
                    customer_id=str(customer_id),
                    expected="upgrade",
                    actual=transition_type
                )
                return Result.fail(InternalError(
                    message=f"Expected upgrade but got {transition_type}",
                    operation="upgrade_plan"
                ))
            
            # Execute upgrade
            result = await self.infrastructure.upgrade_plan(customer_id, new_plan)
            if result.is_failure:
                return Result.fail(result.error)
            
            updated_customer = result.value
            
            # Publish event
            event = self.domain.create_plan_upgraded_event(
                customer_id=customer_id,
                email=customer.email,
                old_plan=old_plan,
                new_plan=new_plan,
                annual_value_change=0.0
            )
            self.event_bus.publish(event)
            
            self.logger.info(
                "customer_plan_upgraded",
                customer_id=str(customer_id),
                old_plan=old_plan,
                new_plan=new_plan
            )
            
            return Result.ok({
                "customer_id": str(updated_customer.id),
                "email": updated_customer.email,
                "old_plan": old_plan,
                "new_plan": updated_customer.plan,
                "message": f"Successfully upgraded from {old_plan} to {new_plan}"
            })
            
        except Exception as e:
            self.logger.error(
                "customer_plan_upgrade_failed",
                customer_id=str(customer_id),
                new_plan=new_plan,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
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
            self.logger.info(
                "customer_plan_downgrade_started",
                customer_id=str(customer_id),
                new_plan=new_plan
            )
            
            # Get current customer
            customer_result = await self.infrastructure.get_by_id(customer_id)
            if customer_result.is_failure:
                return Result.fail(customer_result.error)
            
            customer = customer_result.value
            old_plan = customer.plan
            
            # Validate plan transition
            validation = self.domain.validate_plan_transition(old_plan, new_plan)
            if validation.is_failure:
                self.logger.warning(
                    "customer_plan_downgrade_validation_failed",
                    customer_id=str(customer_id),
                    old_plan=old_plan,
                    new_plan=new_plan
                )
                return Result.fail(validation.error)
            
            transition_type = validation.value
            
            if transition_type != "downgrade":
                self.logger.warning(
                    "customer_plan_downgrade_incorrect_transition",
                    customer_id=str(customer_id),
                    expected="downgrade",
                    actual=transition_type
                )
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
            
            self.logger.info(
                "customer_plan_downgraded",
                customer_id=str(customer_id),
                old_plan=old_plan,
                new_plan=new_plan
            )
            
            return Result.ok({
                "customer_id": str(updated_customer.id),
                "email": updated_customer.email,
                "old_plan": old_plan,
                "new_plan": updated_customer.plan,
                "message": f"Successfully downgraded from {old_plan} to {new_plan}"
            })
            
        except Exception as e:
            self.logger.error(
                "customer_plan_downgrade_failed",
                customer_id=str(customer_id),
                new_plan=new_plan,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
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
            self.logger.debug(
                "customer_profile_requested",
                customer_id=str(customer_id)
            )
            
            result = await self.infrastructure.get_customer_profile(customer_id)
            
            if result.is_success:
                self.logger.info(
                    "customer_profile_retrieved",
                    customer_id=str(customer_id)
                )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "customer_profile_retrieval_failed",
                customer_id=str(customer_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get customer profile: {str(e)}",
                operation="get_customer_profile",
                component="CustomerApplicationService"
            ))