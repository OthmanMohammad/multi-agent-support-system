"""
Customer Infrastructure Service - Data access for customer operations

This service wraps the customer repository with Result-based error handling.
It performs CRUD operations and data retrieval - NO business logic.

Business rules (rate limits, validation, plan eligibility) belong in
CustomerDomainService, not here.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from core.result import Result
from core.errors import NotFoundError, InternalError
from database.unit_of_work import UnitOfWork
from database.models import Customer


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
            customer = await self.uow.customers.get_or_create_by_email(
                email=email,
                name=name,
                plan=plan
            )
            
            return Result.ok(customer)
            
        except Exception as e:
            return Result.fail(InternalError(
                message=f"Failed to get/create customer: {str(e)}",
                operation="get_or_create_by_email",
                component="CustomerInfrastructureService"
            ))
    
    async def get_by_id(self, customer_id: UUID) -> Result[Customer]:
        """
        Get customer by ID
        
        Args:
            customer_id: Customer UUID
            
        Returns:
            Result with Customer or NotFoundError
        """
        try:
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            return Result.ok(customer)
            
        except Exception as e:
            return Result.fail(InternalError(
                message=f"Failed to fetch customer: {str(e)}",
                operation="get_by_id",
                component="CustomerInfrastructureService"
            ))
    
    async def get_by_email(self, email: str) -> Result[Optional[Customer]]:
        """
        Get customer by email
        
        Args:
            email: Customer email
            
        Returns:
            Result with Customer or None if not found
        """
        try:
            customer = await self.uow.customers.get_by_email(email)
            return Result.ok(customer)
            
        except Exception as e:
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
        """
        Upgrade customer plan
        
        NOTE: Business rule validation should be done by domain service first.
        This just updates the database.
        
        Args:
            customer_id: Customer UUID
            new_plan: New plan name
            
        Returns:
            Result with updated Customer
        """
        try:
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
            
            return Result.ok(updated)
            
        except Exception as e:
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
        """
        Downgrade customer plan
        
        NOTE: Business rule validation should be done by domain service first.
        This just updates the database.
        
        Args:
            customer_id: Customer UUID
            new_plan: New plan name
            
        Returns:
            Result with updated Customer
        """
        try:
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
            
            return Result.ok(updated)
            
        except Exception as e:
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
        """
        Get number of conversations for a specific date
        
        This is pure data retrieval - domain service uses this data
        to check rate limits (the business logic part).
        
        Args:
            customer_id: Customer UUID
            date: Date to check
            
        Returns:
            Result with conversation count
        """
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            count = await self.uow.conversations.count(
                customer_id=customer_id,
                started_at__gte=start_of_day,
                started_at__lt=end_of_day
            )
            
            return Result.ok(count)
            
        except Exception as e:
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
        """
        Get customer usage statistics
        
        Simple aggregation of data - no business logic.
        
        Args:
            customer_id: Customer UUID
            days: Number of days to analyze
            
        Returns:
            Result with usage stats dict
        """
        try:
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get conversations
            conversations = await self.uow.conversations.get_by_customer(
                customer_id=customer_id,
                limit=1000
            )
            
            # Filter by date
            recent_convs = [
                c for c in conversations
                if c.started_at >= since
            ]
            
            # Calculate simple stats (aggregation, not business logic)
            stats = {
                "total_conversations": len(recent_convs),
                "resolved": len([c for c in recent_convs if c.status == "resolved"]),
                "escalated": len([c for c in recent_convs if c.status == "escalated"]),
                "active": len([c for c in recent_convs if c.status == "active"]),
                "avg_sentiment": sum(c.sentiment_avg or 0 for c in recent_convs) / len(recent_convs) if recent_convs else 0,
                "period_days": days
            }
            
            return Result.ok(stats)
            
        except Exception as e:
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
        """
        Block customer account
        
        Args:
            customer_id: Customer UUID
            reason: Reason for blocking
            
        Returns:
            Result with updated Customer
        """
        try:
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            # Update metadata
            metadata = customer.extra_metadata.copy() if customer.extra_metadata else {}
            metadata["blocked"] = True
            metadata["blocked_reason"] = reason
            metadata["blocked_at"] = datetime.utcnow().isoformat()
            
            updated = await self.uow.customers.update(
                customer_id,
                extra_metadata=metadata,
                updated_by=self.uow.current_user_id
            )
            
            return Result.ok(updated)
            
        except Exception as e:
            return Result.fail(InternalError(
                message=f"Failed to block customer: {str(e)}",
                operation="block_customer",
                component="CustomerInfrastructureService"
            ))
    
    async def unblock_customer(
        self,
        customer_id: UUID
    ) -> Result[Customer]:
        """
        Unblock customer account
        
        Args:
            customer_id: Customer UUID
            
        Returns:
            Result with updated Customer
        """
        try:
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            # Update metadata
            metadata = customer.extra_metadata.copy() if customer.extra_metadata else {}
            metadata["blocked"] = False
            metadata.pop("blocked_reason", None)
            metadata.pop("blocked_at", None)
            
            updated = await self.uow.customers.update(
                customer_id,
                extra_metadata=metadata,
                updated_by=self.uow.current_user_id
            )
            
            return Result.ok(updated)
            
        except Exception as e:
            return Result.fail(InternalError(
                message=f"Failed to unblock customer: {str(e)}",
                operation="unblock_customer",
                component="CustomerInfrastructureService"
            ))
    
    async def get_customer_profile(
        self,
        customer_id: UUID
    ) -> Result[dict]:
        """
        Get complete customer profile
        
        Args:
            customer_id: Customer UUID
            
        Returns:
            Result with customer profile dict
        """
        try:
            customer = await self.uow.customers.get_by_id(customer_id)
            
            if not customer:
                return Result.fail(NotFoundError(
                    resource="Customer",
                    identifier=str(customer_id)
                ))
            
            # Get recent conversations
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
            
            return Result.ok(profile)
            
        except Exception as e:
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