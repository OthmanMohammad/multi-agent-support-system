"""
Customer repository - business logic for customer data access
"""
from typing import Optional
from sqlalchemy import select

from database.base import BaseRepository
from database.models import Customer


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customer operations"""
    
    def __init__(self, session):
        super().__init__(Customer, session)
    
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
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
        """Get existing customer or create new one"""
        customer = await self.get_by_email(email)
        
        if not customer:
            customer = await self.create(
                email=email,
                name=name,
                plan=plan
            )
        
        return customer