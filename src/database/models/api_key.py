"""
API Key Model - Programmatic authentication

This module defines the APIKey model for machine-to-machine authentication.
"""

from typing import Optional, List
from datetime import datetime, UTC
from uuid import UUID
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.models.base import BaseModel


class APIKey(BaseModel):
    """
    API Key model for programmatic authentication.

    Features:
    - Secure key generation (msa_live_xxx or msa_test_xxx)
    - Bcrypt hashing (keys never stored in plain text)
    - Scope-based permissions
    - Expiration support
    - Usage tracking
    - Prefix for quick lookup
    - Revocation support (via soft delete)

    Security:
    - Keys are hashed with bcrypt (only shown once at creation)
    - Keys are prefixed with environment (msa_live_, msa_test_)
    - Keys can be scoped to specific permissions
    - Keys can expire automatically
    - Last used tracking for security audits

    Key Format:
        msa_live_RANDOMSTRING  (production)
        msa_test_RANDOMSTRING  (testing)

    Relationships:
    - user: User who owns the API key
    """

    __tablename__ = "api_keys"

    # Foreign key to user
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this API key"
    )

    # Key information
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable key name"
    )

    key_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Key prefix for quick lookup (e.g., msa_live_abc123...)"
    )

    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hash of the API key"
    )

    # Permissions
    scopes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Comma-separated permission scopes"
    )

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Expiration timestamp (null = never expires)"
    )

    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time key was used"
    )

    last_used_ip: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="IP address of last use"
    )

    usage_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="Number of times key has been used"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether key is active"
    )

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description of key purpose"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
        lazy="joined"
    )

    def __repr__(self) -> str:
        """String representation"""
        return f"<APIKey(id={self.id}, name='{self.name}', prefix='{self.key_prefix}')>"

    def to_dict(self, include_key_hash: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_key_hash: Whether to include key_hash
                            (should never be exposed to API)

        Returns:
            Dictionary representation
        """
        data = super().to_dict()

        # Never expose key hash by default
        if not include_key_hash:
            data.pop("key_hash", None)

        # Parse scopes
        if "scopes" in data and data["scopes"]:
            data["scopes"] = [s.strip() for s in data["scopes"].split(",")]
        else:
            data["scopes"] = []

        return data

    def get_scopes(self) -> List[str]:
        """
        Get API key scopes as list.

        Returns:
            List of permission scopes
        """
        if not self.scopes:
            return []
        return [s.strip() for s in self.scopes.split(",")]

    def set_scopes(self, scopes: List[str]) -> None:
        """
        Set API key scopes from list.

        Args:
            scopes: List of permission scopes
        """
        self.scopes = ",".join(scopes) if scopes else None

    def is_expired(self) -> bool:
        """
        Check if API key is expired.

        Returns:
            True if expired, False otherwise
        """
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at

    def is_valid(self) -> bool:
        """
        Check if API key is valid (not expired, not deleted, active).

        Returns:
            True if valid, False otherwise
        """
        return (
            self.is_active
            and not self.is_expired()
            and self.deleted_at is None
        )

    def record_usage(self, ip_address: Optional[str] = None) -> None:
        """
        Record API key usage.

        Args:
            ip_address: IP address of the request
        """
        self.usage_count += 1
        self.last_used_at = datetime.now(UTC)
        if ip_address:
            self.last_used_ip = ip_address
