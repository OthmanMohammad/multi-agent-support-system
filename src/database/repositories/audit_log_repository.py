"""
Audit log repository - Business logic for audit and compliance data access
"""
from typing import Optional, List
from sqlalchemy import select, and_
from uuid import UUID
from datetime import datetime, timedelta

from src.database.base import BaseRepository
from src.database.models import AuditLog


class AuditLogRepository(BaseRepository[AuditLog]):
    """
    Repository for audit log operations

    Note: Audit logs are immutable and do not support soft delete.
    They should never be deleted to maintain compliance and audit trail.
    """

    def __init__(self, session):
        super().__init__(AuditLog, session)

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs for a specific entity"""
        result = await self.session.execute(
            select(AuditLog)
            .where(and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            ))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_actor(
        self,
        actor_type: str,
        actor_id: UUID,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs for a specific actor"""
        result = await self.session.execute(
            select(AuditLog)
            .where(and_(
                AuditLog.actor_type == actor_type,
                AuditLog.actor_id == actor_id
            ))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_action(
        self,
        action: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs by action type"""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 1000
    ) -> List[AuditLog]:
        """Get audit logs in a date range with optional filters"""
        conditions = [
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        ]

        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)

        if action:
            conditions.append(AuditLog.action == action)

        result = await self.session.execute(
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_ip_address(
        self,
        ip_address: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs from a specific IP address"""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.ip_address == ip_address)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_activity(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent audit activity"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.timestamp >= cutoff)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_security_events(
        self,
        days: int = 7,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get security-related events (logins, logouts, exports)"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(AuditLog)
            .where(and_(
                AuditLog.action.in_(['login', 'logout', 'export']),
                AuditLog.timestamp >= cutoff
            ))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_changes(
        self,
        entity_type: str,
        field_name: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Search for changes to a specific field"""
        result = await self.session.execute(
            select(AuditLog)
            .where(and_(
                AuditLog.entity_type == entity_type,
                AuditLog.action == 'update',
                AuditLog.changes.has_key(field_name)  # JSONB has_key operation
            ))
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # Override delete method to prevent accidental deletion
    async def delete(self, id: UUID) -> bool:
        """
        Audit logs should never be deleted for compliance reasons.
        This method is disabled.
        """
        raise NotImplementedError(
            "Audit logs cannot be deleted. They are immutable for compliance and audit trail purposes."
        )

    async def soft_delete_by_id(self, id: UUID, deleted_by: Optional[UUID] = None):
        """
        Audit logs do not support soft delete.
        This method is disabled.
        """
        raise NotImplementedError(
            "Audit logs cannot be deleted. They are immutable for compliance and audit trail purposes."
        )
