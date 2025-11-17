"""
API Key repository - Business logic for API key data access

Provides methods for API key management and validation.
"""

from typing import Optional, List
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, timedelta, UTC

from src.database.base import BaseRepository
from src.database.models import APIKey


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API key operations"""

    def __init__(self, session):
        super().__init__(APIKey, session)

    async def get_by_prefix(self, key_prefix: str) -> Optional[APIKey]:
        """
        Get API key by prefix (for quick lookup).

        Args:
            key_prefix: Key prefix (e.g., msa_live_abc123...)

        Returns:
            APIKey instance or None
        """
        result = await self.session.execute(
            select(APIKey).where(APIKey.key_prefix == key_prefix)
        )
        return result.scalar_one_or_none()

    async def get_user_keys(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[APIKey]:
        """
        Get all API keys for a user.

        Args:
            user_id: User UUID
            include_inactive: Whether to include inactive keys

        Returns:
            List of API keys
        """
        query = select(APIKey).where(
            APIKey.user_id == user_id,
            APIKey.deleted_at.is_(None)
        )

        if not include_inactive:
            query = query.where(APIKey.is_active == True)

        result = await self.session.execute(
            query.order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_keys(
        self,
        user_id: UUID
    ) -> List[APIKey]:
        """
        Get all active, non-expired API keys for a user.

        Args:
            user_id: User UUID

        Returns:
            List of active API keys
        """
        now = datetime.now(UTC)

        result = await self.session.execute(
            select(APIKey).where(
                APIKey.user_id == user_id,
                APIKey.is_active == True,
                APIKey.deleted_at.is_(None),
                # Either no expiration or not yet expired
                (APIKey.expires_at.is_(None)) | (APIKey.expires_at > now)
            )
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_key(self, key_id: UUID) -> Optional[APIKey]:
        """
        Revoke an API key (soft delete).

        Args:
            key_id: API key UUID

        Returns:
            Revoked API key or None
        """
        return await self.delete(key_id)

    async def deactivate_key(self, key_id: UUID) -> Optional[APIKey]:
        """
        Deactivate an API key (without deleting).

        Args:
            key_id: API key UUID

        Returns:
            Updated API key or None
        """
        return await self.update(key_id, is_active=False)

    async def activate_key(self, key_id: UUID) -> Optional[APIKey]:
        """
        Activate an API key.

        Args:
            key_id: API key UUID

        Returns:
            Updated API key or None
        """
        return await self.update(key_id, is_active=True)

    async def record_usage(
        self,
        key_id: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[APIKey]:
        """
        Record API key usage (increment counter, update timestamp).

        Args:
            key_id: API key UUID
            ip_address: Request IP address

        Returns:
            Updated API key or None
        """
        key = await self.get(key_id)
        if not key:
            return None

        # Increment usage count
        usage_count = (key.usage_count or 0) + 1

        return await self.update(
            key_id,
            usage_count=usage_count,
            last_used_at=datetime.now(UTC),
            last_used_ip=ip_address
        )

    async def get_expired_keys(self, limit: int = 100) -> List[APIKey]:
        """
        Get all expired API keys.

        Args:
            limit: Maximum records to return

        Returns:
            List of expired API keys
        """
        now = datetime.now(UTC)

        result = await self.session.execute(
            select(APIKey).where(
                APIKey.expires_at.isnot(None),
                APIKey.expires_at < now,
                APIKey.deleted_at.is_(None)
            )
            .order_by(APIKey.expires_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def cleanup_expired_keys(self) -> int:
        """
        Soft delete all expired API keys.

        Returns:
            Number of keys deleted
        """
        expired_keys = await self.get_expired_keys(limit=1000)
        count = 0

        for key in expired_keys:
            await self.delete(key.id)
            count += 1

        return count

    async def get_key_stats(self, user_id: Optional[UUID] = None) -> dict:
        """
        Get API key statistics.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Dict with key counts
        """
        base_filter = [APIKey.deleted_at.is_(None)]

        if user_id:
            base_filter.append(APIKey.user_id == user_id)

        total_keys = await self.session.execute(
            select(func.count(APIKey.id)).where(*base_filter)
        )

        active_keys = await self.session.execute(
            select(func.count(APIKey.id)).where(
                *base_filter,
                APIKey.is_active == True
            )
        )

        expired_keys = await self.session.execute(
            select(func.count(APIKey.id)).where(
                *base_filter,
                APIKey.expires_at.isnot(None),
                APIKey.expires_at < datetime.now(UTC)
            )
        )

        return {
            "total": total_keys.scalar(),
            "active": active_keys.scalar(),
            "expired": expired_keys.scalar(),
        }

    async def get_unused_keys(
        self,
        days_unused: int = 90,
        limit: int = 100
    ) -> List[APIKey]:
        """
        Get API keys that haven't been used in N days.

        Args:
            days_unused: Number of days unused
            limit: Maximum records to return

        Returns:
            List of unused API keys
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=days_unused)

        result = await self.session.execute(
            select(APIKey).where(
                APIKey.deleted_at.is_(None),
                # Either never used or last used before cutoff
                (APIKey.last_used_at.is_(None)) | (APIKey.last_used_at < cutoff_date)
            )
            .order_by(APIKey.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
