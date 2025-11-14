"""
Sales repository - Business logic for sales data access
"""
from typing import Optional, List
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime, timedelta

from src.database.base import BaseRepository
from src.database.models import Employee, Lead, Deal, SalesActivity, Quote


class EmployeeRepository(BaseRepository[Employee]):
    """Repository for employee operations"""

    def __init__(self, session):
        super().__init__(Employee, session)

    async def get_by_email(self, email: str) -> Optional[Employee]:
        """Get employee by email address"""
        result = await self.session.execute(
            select(Employee).where(Employee.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_department(
        self,
        department: str,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees by department"""
        result = await self.session.execute(
            select(Employee)
            .where(Employee.department == department)
            .order_by(Employee.name.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_role(
        self,
        role: str,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees by role"""
        result = await self.session.execute(
            select(Employee)
            .where(Employee.role == role)
            .order_by(Employee.name.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_employees(self) -> List[Employee]:
        """Get all active employees"""
        result = await self.session.execute(
            select(Employee)
            .where(Employee.is_active == 'true')
            .order_by(Employee.name.asc())
        )
        return list(result.scalars().all())


class LeadRepository(BaseRepository[Lead]):
    """Repository for lead operations"""

    def __init__(self, session):
        super().__init__(Lead, session)

    async def get_by_email(self, email: str) -> Optional[Lead]:
        """Get lead by email address"""
        result = await self.session.execute(
            select(Lead).where(Lead.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_source(
        self,
        lead_source: str,
        limit: int = 100
    ) -> List[Lead]:
        """Get leads by source"""
        result = await self.session.execute(
            select(Lead)
            .where(Lead.lead_source == lead_source)
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_qualified_leads(
        self,
        qualification_status: str = 'sql',
        limit: int = 100
    ) -> List[Lead]:
        """Get qualified leads"""
        result = await self.session.execute(
            select(Lead)
            .where(Lead.qualification_status == qualification_status)
            .order_by(Lead.lead_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_owner(
        self,
        owner_id: UUID,
        limit: int = 100
    ) -> List[Lead]:
        """Get leads assigned to an owner"""
        result = await self.session.execute(
            select(Lead)
            .where(Lead.owner_id == owner_id)
            .order_by(Lead.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_high_value_leads(
        self,
        min_score: int = 80,
        limit: int = 50
    ) -> List[Lead]:
        """Get high-value leads by score"""
        result = await self.session.execute(
            select(Lead)
            .where(Lead.lead_score >= min_score)
            .order_by(Lead.lead_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class DealRepository(BaseRepository[Deal]):
    """Repository for deal operations"""

    def __init__(self, session):
        super().__init__(Deal, session)

    async def get_by_customer(
        self,
        customer_id: UUID
    ) -> List[Deal]:
        """Get all deals for a customer"""
        result = await self.session.execute(
            select(Deal)
            .where(Deal.customer_id == customer_id)
            .order_by(Deal.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_stage(
        self,
        stage: str,
        limit: int = 100
    ) -> List[Deal]:
        """Get deals by stage"""
        result = await self.session.execute(
            select(Deal)
            .where(Deal.stage == stage)
            .order_by(Deal.expected_close_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_owner(
        self,
        owner_id: UUID,
        limit: int = 100
    ) -> List[Deal]:
        """Get deals assigned to an owner"""
        result = await self.session.execute(
            select(Deal)
            .where(Deal.owner_id == owner_id)
            .order_by(Deal.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_closing_soon(
        self,
        days: int = 30,
        limit: int = 100
    ) -> List[Deal]:
        """Get deals closing in the next N days"""
        cutoff = datetime.utcnow() + timedelta(days=days)
        result = await self.session.execute(
            select(Deal)
            .where(and_(
                Deal.expected_close_date <= cutoff,
                Deal.stage != 'closed_won',
                Deal.stage != 'closed_lost'
            ))
            .order_by(Deal.expected_close_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_total_pipeline_value(self) -> float:
        """Get total value of open deals"""
        result = await self.session.execute(
            select(func.sum(Deal.amount))
            .where(and_(
                Deal.stage != 'closed_won',
                Deal.stage != 'closed_lost'
            ))
        )
        return result.scalar() or 0.0

    async def get_won_deals(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Deal]:
        """Get won deals in a date range"""
        conditions = [Deal.stage == 'closed_won']

        if start_date:
            conditions.append(Deal.close_date >= start_date)
        if end_date:
            conditions.append(Deal.close_date <= end_date)

        result = await self.session.execute(
            select(Deal)
            .where(and_(*conditions))
            .order_by(Deal.close_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SalesActivityRepository(BaseRepository[SalesActivity]):
    """Repository for sales activity operations"""

    def __init__(self, session):
        super().__init__(SalesActivity, session)

    async def get_by_deal(
        self,
        deal_id: UUID,
        limit: int = 100
    ) -> List[SalesActivity]:
        """Get all activities for a deal"""
        result = await self.session.execute(
            select(SalesActivity)
            .where(SalesActivity.deal_id == deal_id)
            .order_by(SalesActivity.activity_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_owner(
        self,
        owner_id: UUID,
        limit: int = 100
    ) -> List[SalesActivity]:
        """Get activities by owner"""
        result = await self.session.execute(
            select(SalesActivity)
            .where(SalesActivity.owner_id == owner_id)
            .order_by(SalesActivity.activity_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_type(
        self,
        activity_type: str,
        limit: int = 100
    ) -> List[SalesActivity]:
        """Get activities by type"""
        result = await self.session.execute(
            select(SalesActivity)
            .where(SalesActivity.activity_type == activity_type)
            .order_by(SalesActivity.activity_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_activities(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[SalesActivity]:
        """Get recent activities"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(SalesActivity)
            .where(SalesActivity.activity_date >= cutoff)
            .order_by(SalesActivity.activity_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class QuoteRepository(BaseRepository[Quote]):
    """Repository for quote operations"""

    def __init__(self, session):
        super().__init__(Quote, session)

    async def get_by_deal(
        self,
        deal_id: UUID
    ) -> List[Quote]:
        """Get all quotes for a deal"""
        result = await self.session.execute(
            select(Quote)
            .where(Quote.deal_id == deal_id)
            .order_by(Quote.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 100
    ) -> List[Quote]:
        """Get all quotes for a customer"""
        result = await self.session.execute(
            select(Quote)
            .where(Quote.customer_id == customer_id)
            .order_by(Quote.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Quote]:
        """Get quotes by status"""
        result = await self.session.execute(
            select(Quote)
            .where(Quote.status == status)
            .order_by(Quote.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_expiring_soon(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[Quote]:
        """Get quotes expiring soon"""
        cutoff = datetime.utcnow() + timedelta(days=days)
        result = await self.session.execute(
            select(Quote)
            .where(and_(
                Quote.valid_until <= cutoff,
                Quote.status == 'sent'
            ))
            .order_by(Quote.valid_until.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
