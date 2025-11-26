"""
User Model - Authentication and authorization

This module defines the User model for authentication and user management.
Supports JWT authentication, API keys, and role-based access control (RBAC).
"""

from __future__ import annotations

import enum
from datetime import datetime  # noqa: TC003 - Required at runtime for SQLAlchemy ORM
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import BaseModel

if TYPE_CHECKING:
    from src.database.models.api_key import APIKey


class UserRole(str, enum.Enum):
    """User roles for RBAC"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    API_CLIENT = "api_client"


class UserStatus(str, enum.Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class OAuthProvider(str, enum.Enum):
    """OAuth providers"""

    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


class User(BaseModel):
    """
    User model for authentication and authorization.

    Features:
    - Password-based authentication (bcrypt)
    - JWT token support (access + refresh)
    - OAuth 2.0 authentication
    - Role-based access control (RBAC)
    - Email verification
    - Account status management
    - API key relationships
    - Audit trail (from BaseModel)
    - Soft delete support (from BaseModel)

    Relationships:
    - api_keys: List of API keys owned by user
    - conversations: Conversations created by user (via created_by)
    - customers: Customers created by user (via created_by)

    Security:
    - Passwords are hashed with bcrypt (never stored in plain text)
    - Tokens can be revoked via blacklist
    - Failed login tracking (future enhancement)
    - Session management (future enhancement)
    """

    __tablename__ = "users"

    # Primary authentication
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True, comment="User email (used for login)"
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # Nullable for OAuth-only users
        comment="Bcrypt password hash",
    )

    # Profile information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="User full name")

    organization: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Organization name"
    )

    # Role and permissions
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False, length=50),
        nullable=False,
        default=UserRole.USER,
        index=True,
        comment="User role for RBAC",
    )

    scopes: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, comment="Comma-separated permission scopes"
    )

    # Account status
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, native_enum=False, length=50),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
        index=True,
        comment="Account status",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True, comment="Whether user can log in"
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Whether email is verified"
    )

    # OAuth information
    oauth_provider: Mapped[OAuthProvider | None] = mapped_column(
        SQLEnum(OAuthProvider, native_enum=False, length=50),
        nullable=True,
        comment="OAuth provider (if OAuth user)",
    )

    oauth_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True, comment="OAuth provider user ID"
    )

    # Email verification
    email_verification_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Email verification token"
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Timestamp when email was verified"
    )

    # Password reset
    password_reset_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Password reset token"
    )

    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Password reset token expiration"
    )

    # Session tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last successful login timestamp"
    )

    last_login_ip: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Last login IP address"
    )

    # Relationships
    api_keys: Mapped[list[APIKey]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        """String representation"""
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_sensitive: Whether to include sensitive fields
                              (password_hash, tokens, etc.)

        Returns:
            Dictionary representation
        """
        data = super().to_dict()

        # Remove sensitive fields by default
        if not include_sensitive:
            sensitive_fields = [
                "password_hash",
                "email_verification_token",
                "password_reset_token",
                "password_reset_expires_at",
            ]
            for field in sensitive_fields:
                data.pop(field, None)

        # Convert enums to values
        if "role" in data and isinstance(data["role"], UserRole):
            data["role"] = data["role"].value
        if "status" in data and isinstance(data["status"], UserStatus):
            data["status"] = data["status"].value
        if "oauth_provider" in data and isinstance(data["oauth_provider"], OAuthProvider):
            data["oauth_provider"] = data["oauth_provider"].value

        # Parse scopes from comma-separated string
        if data.get("scopes"):
            data["scopes"] = [s.strip() for s in data["scopes"].split(",")]
        else:
            data["scopes"] = []

        return data

    def get_scopes(self) -> list[str]:
        """
        Get user scopes as list.

        Returns:
            List of permission scopes
        """
        if not self.scopes:
            return []
        return [s.strip() for s in self.scopes.split(",")]

    def set_scopes(self, scopes: list[str]) -> None:
        """
        Set user scopes from list.

        Args:
            scopes: List of permission scopes
        """
        self.scopes = ",".join(scopes) if scopes else None

    def has_scope(self, scope: str) -> bool:
        """
        Check if user has a specific scope.

        Args:
            scope: Permission scope to check

        Returns:
            True if user has scope, False otherwise
        """
        # Super admin has all scopes
        if self.role == UserRole.SUPER_ADMIN:
            return True

        user_scopes = self.get_scopes()

        # Check for wildcard
        if "*" in user_scopes:
            return True

        return scope in user_scopes

    def can_access_resource(self, required_scopes: list[str]) -> bool:
        """
        Check if user can access a resource requiring specific scopes.

        Args:
            required_scopes: List of required scopes

        Returns:
            True if user has all required scopes, False otherwise
        """
        # Super admin can access everything
        if self.role == UserRole.SUPER_ADMIN:
            return True

        user_scopes = set(self.get_scopes())

        # Check for wildcard
        if "*" in user_scopes:
            return True

        # Check if user has all required scopes
        return set(required_scopes).issubset(user_scopes)
