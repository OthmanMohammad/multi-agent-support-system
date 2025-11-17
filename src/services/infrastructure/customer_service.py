"""
Customer Infrastructure Service - Data access for customer operations

This service wraps the customer repository with Result-based error handling.
It performs CRUD operations and data retrieval - NO business logic.

Business rules (rate limits, validation, plan eligibility) belong in
CustomerDomainService, not here.

"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta, UTC

from src.core.result import Result
from src.core.errors import NotFoundError, InternalError
from src.database.unit_of_work import UnitOfWork
from src.database.models import Customer
from src.utils.logging.setup import get_logger


class CustomerInfrastructureService:
    """
    Infrastructure service for customer data operations
    
    Responsibilities:
    - Database CRUD operations
    - Data retrieval and aggregation
    - Wraps repository pattern
    
    NOT responsible for:
    - Business rule validation (domain service)
    - Rate limit checking (domain service)
    - Complex calculations (domain service)
    
    """
    
    def __init__(self, uow: UnitOfWork):
        """
        Initialize with Unit of Work
        
        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow
        self.logger = get_logger(__name__)
        
        self.logger.debug("customer_infrastructure_service_initialized")
    
    async def get_or_create_by_email(
        self,
        email: str,
        name: Optional[str] = None,
        plan: str = "free"
    ) -> Result[Customer]:
        """
        Get existing customer or create new one
        
        This is a common pattern for upsert operations.
        No business logic - just database operation.
        
        Args:
            email: Customer email
            name: Customer name (optional)
            plan: Initial plan (default: free)
            
        Returns:
            Result with Customer
        """
        try:
            self.logger.debug(
                "customer_get_or_create_started",
                email=email,
                plan=plan
            )
            
            customer = await self.uow.customers.get_or_create_by_email(
                email=email,
                name=name,
                plan=plan
            )
            
            self.logger.info(
                "customer_retrieved",
                customer_id=str(customer.id),
                plan=customer.plan,
                was_created=customer.created_at > (datetime.now(UTC) - timedelta(seconds=1))
            )
            
            return Result.ok(customer)
            
        except Exception as e:
            self.logger.error(
                "customer_get_or_create_failed",
                email=email,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get/create customer: {str(e)}",
                operation="get_or_create_by_email",
                component="CustomerInfrastructureService"
            ))
    
    async def get_by_id(self, customer_id: UUID) -> Result[Customer]:
        """Get customer by ID"""
        try:
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                self.logger.warning(
                    "customer_not_found",
                    customer_id=str(customer_id)
                )
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            self.logger.debug(
                "customer_retrieved_by_id",
                customer_id=str(customer_id)
            )
            return Result.ok(customer)
            
        except Exception as e:
            self.logger.error(
                "customer_get_by_id_failed",
                customer_id=str(customer_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to fetch customer: {str(e)}",
                operation="get_by_id",
                component="CustomerInfrastructureService"
            ))
    
    async def get_by_email(self, email: str) -> Result[Optional[Customer]]:
        """Get customer by email"""
        try:
            customer = await self.uow.customers.get_by_email(email)
            
            self.logger.debug(
                "customer_search_by_email",
                email=email,
                found=customer is not None
            )
            return Result.ok(customer)
            
        except Exception as e:
            self.logger.error(
                "customer_get_by_email_failed",
                email=email,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to fetch customer by email: {str(e)}",
                operation="get_by_email",
                component="CustomerInfrastructureService"
            ))
    
    async def upgrade_plan(
        self,
        customer_id: UUID,
        new_plan: str
    ) -> Result[Customer]:
        """Upgrade customer plan"""
        try:
            self.logger.info(
                "customer_plan_upgrade_started",
                customer_id=str(customer_id),
                new_plan=new_plan
            )
            
            updated = await self.uow.customers.update(
                customer_id,
                plan=new_plan,
                updated_by=self.uow.current_user_id
            )
            
            if not updated:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            self.logger.info(
                "customer_plan_upgraded",
                customer_id=str(customer_id),
                new_plan=new_plan
            )
            return Result.ok(updated)
            
        except Exception as e:
            self.logger.error(
                "customer_plan_upgrade_failed",
                customer_id=str(customer_id),
                new_plan=new_plan,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to upgrade customer plan: {str(e)}",
                operation="upgrade_plan",
                component="CustomerInfrastructureService"
            ))
    
    async def downgrade_plan(
        self,
        customer_id: UUID,
        new_plan: str
    ) -> Result[Customer]:
        """Downgrade customer plan"""
        try:
            self.logger.info(
                "customer_plan_downgrade_started",
                customer_id=str(customer_id),
                new_plan=new_plan
            )
            
            updated = await self.uow.customers.update(
                customer_id,
                plan=new_plan,
                updated_by=self.uow.current_user_id
            )
            
            if not updated:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            self.logger.info(
                "customer_plan_downgraded",
                customer_id=str(customer_id),
                new_plan=new_plan
            )
            return Result.ok(updated)
            
        except Exception as e:
            self.logger.error(
                "customer_plan_downgrade_failed",
                customer_id=str(customer_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to downgrade customer plan: {str(e)}",
                operation="downgrade_plan",
                component="CustomerInfrastructureService"
            ))
    
    async def get_conversation_count_for_date(
        self,
        customer_id: UUID,
        date: datetime
    ) -> Result[int]:
        """Get number of conversations for a specific date"""
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            count = await self.uow.conversations.count(
                customer_id=customer_id,
                started_at__gte=start_of_day,
                started_at__lt=end_of_day
            )
            
            self.logger.debug(
                "customer_conversation_count_retrieved",
                customer_id=str(customer_id),
                date=start_of_day.date().isoformat(),
                count=count
            )
            return Result.ok(count)
            
        except Exception as e:
            self.logger.error(
                "customer_conversation_count_failed",
                customer_id=str(customer_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to count conversations: {str(e)}",
                operation="get_conversation_count_for_date",
                component="CustomerInfrastructureService"
            ))
    
    async def get_usage_stats(
        self,
        customer_id: UUID,
        days: int = 30
    ) -> Result[dict]:
        """Get customer usage statistics"""
        try:
            since = datetime.now(UTC) - timedelta(days=days)
            
            conversations = await self.uow.conversations.get_by_customer(
                customer_id=customer_id,
                limit=1000
            )
            
            recent_convs = [
                c for c in conversations
                if c.started_at >= since
            ]
            
            stats = {
                "total_conversations": len(recent_convs),
                "resolved": len([c for c in recent_convs if c.status == "resolved"]),
                "escalated": len([c for c in recent_convs if c.status == "escalated"]),
                "active": len([c for c in recent_convs if c.status == "active"]),
                "avg_sentiment": sum(c.sentiment_avg or 0 for c in recent_convs) / len(recent_convs) if recent_convs else 0,
                "period_days": days
            }
            
            self.logger.info(
                "customer_usage_stats_retrieved",
                customer_id=str(customer_id),
                days=days,
                total_conversations=stats["total_conversations"]
            )
            return Result.ok(stats)
            
        except Exception as e:
            self.logger.error(
                "customer_usage_stats_failed",
                customer_id=str(customer_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to get usage stats: {str(e)}",
                operation="get_usage_stats",
                component="CustomerInfrastructureService"
            ))
    
    async def block_customer(
        self,
        customer_id: UUID,
        reason: str
    ) -> Result[Customer]:
        """Block customer account"""
        try:
            self.logger.warning(
                "customer_block_started",
                customer_id=str(customer_id),
                reason=reason
            )
            
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            metadata = customer.extra_metadata.copy() if customer.extra_metadata else {}
            metadata["blocked"] = True
            metadata["blocked_reason"] = reason
            metadata["blocked_at"] = datetime.now(UTC).isoformat()
            
            updated = await self.uow.customers.update(
                customer_id,
                extra_metadata=metadata,
                updated_by=self.uow.current_user_id
            )
            
            self.logger.warning(
                "customer_blocked",
                customer_id=str(customer_id),
                reason=reason
            )
            return Result.ok(updated)
            
        except Exception as e:
            self.logger.error(
                "customer_block_failed",
                customer_id=str(customer_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to block customer: {str(e)}",
                operation="block_customer",
                component="CustomerInfrastructureService"
            ))
    
    async def unblock_customer(
        self,
        customer_id: UUID
    ) -> Result[Customer]:
        """Unblock customer account"""
        try:
            self.logger.info(
                "customer_unblock_started",
                customer_id=str(customer_id)
            )
            
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            metadata = customer.extra_metadata.copy() if customer.extra_metadata else {}
            metadata["blocked"] = False
            metadata.pop("blocked_reason", None)
            metadata.pop("blocked_at", None)
            
            updated = await self.uow.customers.update(
                customer_id,
                extra_metadata=metadata,
                updated_by=self.uow.current_user_id
            )
            
            self.logger.info(
                "customer_unblocked",
                customer_id=str(customer_id)
            )
            return Result.ok(updated)
            
        except Exception as e:
            self.logger.error(
                "customer_unblock_failed",
                customer_id=str(customer_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to unblock customer: {str(e)}",
                operation="unblock_customer",
                component="CustomerInfrastructureService"
            ))
    
    async def get_customer_profile(
        self,
        customer_id: UUID
    ) -> Result[dict]:
        """Get complete customer profile"""
        try:
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            conversations = await self.uow.conversations.get_by_customer(
                customer_id=customer_id,
                limit=10
            )
            
            profile = {
                "id": str(customer.id),
                "email": customer.email,
                "name": customer.name,
                "plan": customer.plan,
                "created_at": customer.created_at.isoformat(),
                "metadata": customer.extra_metadata,
                "recent_conversations_count": len(conversations),
                "total_conversations": await self._count_total_conversations(customer_id),
                "blocked": customer.extra_metadata.get("blocked", False) if customer.extra_metadata else False
            }
            
            self.logger.debug(
                "customer_profile_retrieved",
                customer_id=str(customer_id)
            )
            return Result.ok(profile)
            
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
                component="CustomerInfrastructureService"
            ))
    
    async def _count_total_conversations(self, customer_id: UUID) -> int:
        """Helper to count total conversations (internal)"""
        try:
            return await self.uow.conversations.count(customer_id=customer_id)
        except:
            return 0