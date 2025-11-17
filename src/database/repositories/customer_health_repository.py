"""
Customer health repository - Business logic for customer health data access
"""
from typing import Optional, List
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime, timedelta, UTC

from src.database.base import BaseRepository
from src.database.models import (
    CustomerHealthEvent,
    CustomerSegment,
    CustomerNote,
    CustomerContact,
    CustomerIntegration
)


class CustomerHealthEventRepository(BaseRepository[CustomerHealthEvent]):
    """Repository for customer health event operations"""

    def __init__(self, session):
        super().__init__(CustomerHealthEvent, session)

    async def get_by_customer(
        self,
        customer_id: UUID,
        limit: int = 100
    ) -> List[CustomerHealthEvent]:
        """Get all health events for a customer"""
        result = await self.session.execute(
            select(CustomerHealthEvent)
            .where(CustomerHealthEvent.customer_id == customer_id)
            .order_by(CustomerHealthEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_severity(
        self,
        customer_id: UUID,
        severity: str
    ) -> List[CustomerHealthEvent]:
        """Get health events by severity level"""
        result = await self.session.execute(
            select(CustomerHealthEvent)
            .where(and_(
                CustomerHealthEvent.customer_id == customer_id,
                CustomerHealthEvent.severity == severity
            ))
            .order_by(CustomerHealthEvent.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_recent_critical(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[CustomerHealthEvent]:
        """Get recent critical health events"""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self.session.execute(
            select(CustomerHealthEvent)
            .where(and_(
                CustomerHealthEvent.severity == 'critical',
                CustomerHealthEvent.created_at >= cutoff
            ))
            .order_by(CustomerHealthEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class CustomerSegmentRepository(BaseRepository[CustomerSegment]):
    """Repository for customer segment operations"""

    def __init__(self, session):
        super().__init__(CustomerSegment, session)

    async def get_by_customer(
        self,
        customer_id: UUID
    ) -> List[CustomerSegment]:
        """Get all segments for a customer"""
        result = await self.session.execute(
            select(CustomerSegment)
            .where(CustomerSegment.customer_id == customer_id)
            .order_by(CustomerSegment.assigned_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_segment_name(
        self,
        segment_name: str,
        limit: int = 100
    ) -> List[CustomerSegment]:
        """Get all customers in a specific segment"""
        result = await self.session.execute(
            select(CustomerSegment)
            .where(CustomerSegment.segment_name == segment_name)
            .order_by(CustomerSegment.assigned_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_segment_distribution(self) -> dict:
        """Get distribution of customers across segments"""
        result = await self.session.execute(
            select(
                CustomerSegment.segment_name,
                func.count(CustomerSegment.id).label('count')
            )
            .group_by(CustomerSegment.segment_name)
        )
        return {row.segment_name: row.count for row in result}


class CustomerNoteRepository(BaseRepository[CustomerNote]):
    """Repository for customer note operations"""

    def __init__(self, session):
        super().__init__(CustomerNote, session)

    async def get_by_customer(
        self,
        customer_id: UUID,
        note_type: Optional[str] = None,
        limit: int = 100
    ) -> List[CustomerNote]:
        """Get notes for a customer, optionally filtered by type"""
        query = select(CustomerNote).where(CustomerNote.customer_id == customer_id)

        if note_type:
            query = query.where(CustomerNote.note_type == note_type)

        query = query.order_by(CustomerNote.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_author(
        self,
        author_id: UUID,
        limit: int = 100
    ) -> List[CustomerNote]:
        """Get notes by author"""
        result = await self.session.execute(
            select(CustomerNote)
            .where(CustomerNote.author_id == author_id)
            .order_by(CustomerNote.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class CustomerContactRepository(BaseRepository[CustomerContact]):
    """Repository for customer contact operations"""

    def __init__(self, session):
        super().__init__(CustomerContact, session)

    async def get_by_customer(
        self,
        customer_id: UUID
    ) -> List[CustomerContact]:
        """Get all contacts for a customer"""
        result = await self.session.execute(
            select(CustomerContact)
            .where(CustomerContact.customer_id == customer_id)
            .order_by(CustomerContact.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_email(self, email: str) -> Optional[CustomerContact]:
        """Get contact by email address"""
        result = await self.session.execute(
            select(CustomerContact).where(CustomerContact.email == email)
        )
        return result.scalar_one_or_none()

    async def get_primary_contact(
        self,
        customer_id: UUID
    ) -> Optional[CustomerContact]:
        """Get primary contact for a customer"""
        result = await self.session.execute(
            select(CustomerContact)
            .where(and_(
                CustomerContact.customer_id == customer_id,
                CustomerContact.is_primary == 'true'
            ))
        )
        return result.scalar_one_or_none()


class CustomerIntegrationRepository(BaseRepository[CustomerIntegration]):
    """Repository for customer integration operations"""

    def __init__(self, session):
        super().__init__(CustomerIntegration, session)

    async def get_by_customer(
        self,
        customer_id: UUID
    ) -> List[CustomerIntegration]:
        """Get all integrations for a customer"""
        result = await self.session.execute(
            select(CustomerIntegration)
            .where(CustomerIntegration.customer_id == customer_id)
            .order_by(CustomerIntegration.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_type(
        self,
        customer_id: UUID,
        integration_type: str
    ) -> Optional[CustomerIntegration]:
        """Get specific integration type for a customer"""
        result = await self.session.execute(
            select(CustomerIntegration)
            .where(and_(
                CustomerIntegration.customer_id == customer_id,
                CustomerIntegration.integration_type == integration_type
            ))
        )
        return result.scalar_one_or_none()

    async def get_unhealthy(self, limit: int = 100) -> List[CustomerIntegration]:
        """Get integrations with errors"""
        result = await self.session.execute(
            select(CustomerIntegration)
            .where(CustomerIntegration.error_count >= 5)
            .order_by(CustomerIntegration.error_count.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
