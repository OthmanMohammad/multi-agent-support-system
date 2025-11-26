"""
JWT Token Management - Access and refresh tokens

This module handles JWT token generation, validation, and revocation.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt

from src.core.config import get_settings
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)
settings = get_settings()


class JWTManager:
    """
    JWT token management for authentication.

    Features:
    - Access token generation (short-lived)
    - Refresh token generation (long-lived)
    - Token validation and parsing
    - Token revocation support (via Redis blacklist)
    - Automatic expiration handling
    """

    # Algorithm for JWT encoding
    ALGORITHM = "HS256"

    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days

    @classmethod
    def create_access_token(
        cls,
        user_id: UUID,
        email: str,
        role: str,
        scopes: list[str],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User UUID
            email: User email
            role: User role (for RBAC)
            scopes: Permission scopes
            expires_delta: Optional custom expiration

        Returns:
            JWT access token string
        """
        # Set expiration
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Create payload
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "email": email,  # User email
            "role": role,  # User role
            "scopes": scopes,  # Permission scopes
            "type": "access",  # Token type
            "exp": expire,  # Expiration time
            "iat": datetime.now(UTC),  # Issued at
            "jti": str(uuid4()),  # JWT ID (for revocation)
        }

        # Encode token
        token = jwt.encode(payload, settings.jwt.secret_key, algorithm=cls.ALGORITHM)

        logger.debug("access_token_created", user_id=str(user_id), expires_at=expire.isoformat())

        return token

    @classmethod
    def create_refresh_token(cls, user_id: UUID, expires_delta: timedelta | None = None) -> str:
        """
        Create JWT refresh token.

        Args:
            user_id: User UUID
            expires_delta: Optional custom expiration

        Returns:
            JWT refresh token string
        """
        # Set expiration
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)

        # Create payload (minimal for refresh tokens)
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "type": "refresh",  # Token type
            "exp": expire,  # Expiration time
            "iat": datetime.now(UTC),  # Issued at
            "jti": str(uuid4()),  # JWT ID (for revocation)
        }

        # Encode token
        token = jwt.encode(payload, settings.jwt.secret_key, algorithm=cls.ALGORITHM)

        logger.debug("refresh_token_created", user_id=str(user_id), expires_at=expire.isoformat())

        return token

    @classmethod
    def verify_token(cls, token: str) -> dict[str, Any]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode token
            payload = jwt.decode(token, settings.jwt.secret_key, algorithms=[cls.ALGORITHM])

            logger.debug(
                "token_verified", token_type=payload.get("type"), user_id=payload.get("sub")
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

        except JWTError as e:
            logger.warning("token_invalid", error=str(e), error_type=type(e).__name__)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

    @classmethod
    def get_user_id_from_token(cls, token: str) -> UUID:
        """
        Extract user ID from token.

        Args:
            token: JWT token string

        Returns:
            User UUID

        Raises:
            HTTPException: If token is invalid
        """
        payload = cls.verify_token(token)
        user_id_str = payload.get("sub")

        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing user ID"
            )

        try:
            return UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: malformed user ID"
            ) from None

    @classmethod
    def get_token_jti(cls, token: str) -> str:
        """
        Extract JWT ID (jti) from token.

        Used for token revocation (blacklisting).

        Args:
            token: JWT token string

        Returns:
            JWT ID string

        Raises:
            HTTPException: If token is invalid
        """
        payload = cls.verify_token(token)
        jti = payload.get("jti")

        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing JWT ID"
            )

        return jti

    @classmethod
    def validate_access_token(cls, token: str) -> dict[str, Any]:
        """
        Validate access token and return payload.

        Args:
            token: JWT access token

        Returns:
            Token payload

        Raises:
            HTTPException: If token is invalid or not an access token
        """
        payload = cls.verify_token(token)

        # Check token type
        if payload.get("type") != "access":
            logger.warning("invalid_token_type", expected="access", actual=payload.get("type"))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        return payload

    @classmethod
    def validate_refresh_token(cls, token: str) -> dict[str, Any]:
        """
        Validate refresh token and return payload.

        Args:
            token: JWT refresh token

        Returns:
            Token payload

        Raises:
            HTTPException: If token is invalid or not a refresh token
        """
        payload = cls.verify_token(token)

        # Check token type
        if payload.get("type") != "refresh":
            logger.warning("invalid_token_type", expected="refresh", actual=payload.get("type"))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        return payload
