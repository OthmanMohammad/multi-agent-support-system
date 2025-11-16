"""
User repository - Business logic for user data access

Provides methods for user authentication, management, and authorization.
"""

from typing import Optional, List
from sqlalchemy import select, func, or_
from uuid import UUID
from datetime import datetime

from src.database.base import BaseRepository
from src.database.models import User, UserRole, UserStatus


class UserRepository(BaseRepository[User]):
    """Repository for user operations"""

    def __init__(self, session):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User instance or None
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_oauth(
        self,
        oauth_provider: str,
        oauth_id: str
    ) -> Optional[User]:
        """
        Get user by OAuth provider and ID.

        Args:
            oauth_provider: OAuth provider (google, github, microsoft)
            oauth_id: OAuth provider user ID

        Returns:
            User instance or None
        """
        result = await self.session.execute(
            select(User).where(
                User.oauth_provider == oauth_provider,
                User.oauth_id == oauth_id
            )
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count(User.id)).where(User.email == email)
        )
        count = result.scalar()
        return count > 0

    async def get_active_users(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Get all active users.

        Args:
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List of active users
        """
        result = await self.session.execute(
            select(User)
            .where(
                User.is_active == True,
                User.deleted_at.is_(None)
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_role(
        self,
        role: UserRole,
        limit: int = 100
    ) -> List[User]:
        """
        Get users by role.

        Args:
            role: User role
            limit: Maximum records to return

        Returns:
            List of users with specified role
        """
        result = await self.session.execute(
            select(User)
            .where(
                User.role == role,
                User.deleted_at.is_(None)
            )
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: UserStatus,
        limit: int = 100
    ) -> List[User]:
        """
        Get users by status.

        Args:
            status: User status
            limit: Maximum records to return

        Returns:
            List of users with specified status
        """
        result = await self.session.execute(
            select(User)
            .where(
                User.status == status,
                User.deleted_at.is_(None)
            )
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def verify_email(self, user_id: UUID) -> Optional[User]:
        """
        Mark user email as verified.

        Args:
            user_id: User UUID

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            is_verified=True,
            email_verified_at=datetime.utcnow(),
            email_verification_token=None,
            status=UserStatus.ACTIVE
        )

    async def set_password_reset_token(
        self,
        user_id: UUID,
        token: str,
        expires_at: datetime
    ) -> Optional[User]:
        """
        Set password reset token.

        Args:
            user_id: User UUID
            token: Reset token
            expires_at: Token expiration

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            password_reset_token=token,
            password_reset_expires_at=expires_at
        )

    async def clear_password_reset_token(
        self,
        user_id: UUID
    ) -> Optional[User]:
        """
        Clear password reset token after use.

        Args:
            user_id: User UUID

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            password_reset_token=None,
            password_reset_expires_at=None
        )

    async def update_last_login(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """
        Update last login timestamp and IP.

        Args:
            user_id: User UUID
            ip_address: Login IP address

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            last_login_at=datetime.utcnow(),
            last_login_ip=ip_address
        )

    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Activate user account.

        Args:
            user_id: User UUID

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            is_active=True,
            status=UserStatus.ACTIVE
        )

    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate user account.

        Args:
            user_id: User UUID

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            is_active=False,
            status=UserStatus.INACTIVE
        )

    async def suspend_user(self, user_id: UUID) -> Optional[User]:
        """
        Suspend user account.

        Args:
            user_id: User UUID

        Returns:
            Updated user or None
        """
        return await self.update(
            user_id,
            is_active=False,
            status=UserStatus.SUSPENDED
        )

    async def get_user_stats(self) -> dict:
        """
        Get user statistics.

        Returns:
            Dict with user counts by role and status
        """
        total_users = await self.session.execute(
            select(func.count(User.id)).where(User.deleted_at.is_(None))
        )

        active_users = await self.session.execute(
            select(func.count(User.id)).where(
                User.is_active == True,
                User.deleted_at.is_(None)
            )
        )

        verified_users = await self.session.execute(
            select(func.count(User.id)).where(
                User.is_verified == True,
                User.deleted_at.is_(None)
            )
        )

        return {
            "total": total_users.scalar(),
            "active": active_users.scalar(),
            "verified": verified_users.scalar(),
        }

    async def search_users(
        self,
        query: str,
        limit: int = 50
    ) -> List[User]:
        """
        Search users by email or name.

        Args:
            query: Search query
            limit: Maximum records to return

        Returns:
            List of matching users
        """
        result = await self.session.execute(
            select(User)
            .where(
                or_(
                    User.email.ilike(f"%{query}%"),
                    User.full_name.ilike(f"%{query}%"),
                    User.organization.ilike(f"%{query}%")
                ),
                User.deleted_at.is_(None)
            )
            .limit(limit)
        )
        return list(result.scalars().all())
