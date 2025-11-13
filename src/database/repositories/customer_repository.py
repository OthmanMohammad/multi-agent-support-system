"""
Customer repository - Business logic for customer data access
"""
from typing import Optional, List
from sqlalchemy import select, func
from uuid import UUID

from src.database.base import BaseRepository
from src.database.models import Customer


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customer operations"""
    
    def __init__(self, session):
        super().__init__(Customer, session)
    
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """
        Get customer by email address
        
        Args:
            email: Customer email
            
        Returns:
            Customer instance or None
        """
        result = await self.session.execute(
            select(Customer).where(Customer.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_by_email(
        self,
        email: str,
        name: str = None,
        plan: str = "free"
    ) -> Customer:
        """
        Get existing customer or create new one
        
        Args:
            email: Customer email
            name: Customer name (optional)
            plan: Subscription plan
            
        Returns:
            Customer instance (existing or new)
        """
        customer = await self.get_by_email(email)
        
        if not customer:
            customer = await self.create(
                email=email,
                name=name,
                plan=plan,
                extra_metadata={}
            )
        
        return customer
    
    async def get_by_plan(self, plan: str, limit: int = 100) -> List[Customer]:
        """
        Get all customers on a specific plan
        
        Args:
            plan: Plan name (free, basic, premium, enterprise)
            limit: Maximum records to return
            
        Returns:
            List of customers
        """
        result = await self.session.execute(
            select(Customer)
            .where(Customer.plan == plan)
            .order_by(Customer.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def upgrade_plan(self, customer_id: UUID, new_plan: str) -> Optional[Customer]:
        """
        Upgrade customer to a new plan
        
        Args:
            customer_id: Customer UUID
            new_plan: New plan name
            
        Returns:
            Updated customer or None
        """
        return await self.update(customer_id, plan=new_plan)
    
    async def get_plan_distribution(self) -> dict:
        """
        Get distribution of customers across plans
        
        Returns:
            Dict with plan counts
        """
        result = await self.session.execute(
            select(
                Customer.plan,
                func.count(Customer.id).label('count')
            )
            .group_by(Customer.plan)
        )
        
        return {row.plan: row.count for row in result}
    
    async def search_by_email_pattern(self, pattern: str, limit: int = 50) -> List[Customer]:
        """
        Search customers by email pattern
        
        Args:
            pattern: Email pattern (e.g., '%@company.com')
            limit: Maximum results
            
        Returns:
            List of matching customers
        """
        result = await self.session.execute(
            select(Customer)
            .where(Customer.email.like(pattern))
            .order_by(Customer.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())