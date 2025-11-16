"""
Authentication Dependencies - Dependency injection for FastAPI

This module provides FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, Header, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.database.models.user import User, UserStatus
from src.database.models.api_key import APIKey
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session
from src.api.auth.jwt import JWTManager
from src.api.auth.api_key_manager import APIKeyManager
from src.api.auth.redis_client import TokenBlacklist
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)


# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


# =============================================================================
# JWT AUTHENTICATION
# =============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session = Depends(get_db_session)
) -> User:
    """
    Get current user from JWT access token.

    This is the main authentication dependency for protected endpoints.

    Args:
        credentials: HTTP Bearer credentials (JWT token)
        session: Database session

    Returns:
        Authenticated User instance

    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    # Check if credentials provided
    if not credentials:
        logger.warning("authentication_missing_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    # Validate JWT token
    try:
        payload = JWTManager.validate_access_token(token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "token_validation_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract JWT ID for blacklist check
    jti = payload.get("jti")
    if not jti:
        logger.warning("token_missing_jti")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )

    # Check if token is blacklisted (revoked)
    if await TokenBlacklist.is_blacklisted(jti):
        logger.warning("blacklisted_token_rejected", jti=jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract user ID
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("token_missing_user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Get user from database
    async with UnitOfWork(session) as uow:
        user = await uow.users.get(user_id)

        if not user:
            logger.warning(
                "user_not_found_from_token",
                user_id=user_id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        logger.debug(
            "user_authenticated_jwt",
            user_id=str(user.id),
            user_email=user.email,
            user_role=user.role.value
        )

        return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify they are active and verified.

    Use this for endpoints that require a verified, active account.

    Args:
        current_user: Current authenticated user

    Returns:
        Active, verified User instance

    Raises:
        HTTPException: 403 if user is not active or verified

    Usage:
        @router.get("/verified-only")
        async def verified_route(user: User = Depends(get_current_active_user)):
            return {"message": "You are verified!"}
    """
    # Check if user is active
    if not current_user.is_active:
        logger.warning(
            "inactive_user_access_denied",
            user_id=str(current_user.id),
            status=current_user.status.value
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )

    # Check account status
    if current_user.status == UserStatus.SUSPENDED:
        logger.warning(
            "suspended_user_access_denied",
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended"
        )

    if current_user.status == UserStatus.PENDING_VERIFICATION:
        logger.warning(
            "unverified_user_access_denied",
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address"
        )

    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session = Depends(get_db_session)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that work with or without authentication
    (e.g., public + private content).

    Args:
        credentials: HTTP Bearer credentials (optional)
        session: Database session

    Returns:
        User if authenticated, None otherwise

    Usage:
        @router.get("/public-or-private")
        async def flexible_route(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None


# =============================================================================
# API KEY AUTHENTICATION
# =============================================================================

async def verify_api_key(
    x_api_key: str = Header(..., description="API key for authentication"),
    request: Request = None,
    session = Depends(get_db_session)
) -> APIKey:
    """
    Verify API key from X-API-Key header.

    Use this for programmatic API access (machine-to-machine).

    Args:
        x_api_key: API key from X-API-Key header
        request: FastAPI request (for IP tracking)
        session: Database session

    Returns:
        Valid APIKey instance

    Raises:
        HTTPException: 401 if API key is invalid, expired, or inactive

    Usage:
        @router.get("/api-protected")
        async def api_route(api_key: APIKey = Depends(verify_api_key)):
            return {"api_key_id": api_key.id}
    """
    # Validate API key format
    is_valid, error = APIKeyManager.validate_api_key_format(x_api_key)
    if not is_valid:
        logger.warning("invalid_api_key_format", error=error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    # Extract prefix for database lookup
    prefix = APIKeyManager.extract_prefix(x_api_key)

    # Get API key from database
    async with UnitOfWork(session) as uow:
        api_key = await uow.api_keys.get_by_prefix(prefix)

        if not api_key:
            logger.warning("api_key_not_found", prefix=prefix)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        # Verify API key hash
        if not APIKeyManager.verify_api_key(x_api_key, api_key.key_hash):
            logger.warning(
                "api_key_verification_failed",
                prefix=prefix,
                key_id=str(api_key.id)
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        # Check if API key is valid (active, not expired, not deleted)
        if not api_key.is_valid():
            logger.warning(
                "invalid_api_key_used",
                key_id=str(api_key.id),
                is_active=api_key.is_active,
                is_expired=api_key.is_expired(),
                deleted_at=api_key.deleted_at
            )

            if api_key.is_expired():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired"
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is not active"
            )

        # Record API key usage
        client_ip = None
        if request:
            client_ip = request.client.host if request.client else None

        await uow.api_keys.record_usage(api_key.id, ip_address=client_ip)
        await uow.commit()

        logger.info(
            "api_key_authenticated",
            key_id=str(api_key.id),
            key_name=api_key.name,
            user_id=str(api_key.user_id),
            client_ip=client_ip
        )

        return api_key


async def get_user_from_api_key(
    api_key: APIKey = Depends(verify_api_key),
    session = Depends(get_db_session)
) -> User:
    """
    Get user associated with API key.

    Use this when you need the user object for an API key request.

    Args:
        api_key: Verified API key
        session: Database session

    Returns:
        User who owns the API key

    Raises:
        HTTPException: 401 if user not found

    Usage:
        @router.get("/api-user")
        async def api_user_route(user: User = Depends(get_user_from_api_key)):
            return {"user_id": user.id}
    """
    async with UnitOfWork(session) as uow:
        user = await uow.users.get(api_key.user_id)

        if not user:
            logger.error(
                "api_key_user_not_found",
                key_id=str(api_key.id),
                user_id=str(api_key.user_id)
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user


# =============================================================================
# COMBINED AUTHENTICATION (JWT OR API KEY)
# =============================================================================

async def get_current_user_or_api_key(
    jwt_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, description="API key for authentication"),
    request: Request = None,
    session = Depends(get_db_session)
) -> User:
    """
    Authenticate via JWT token OR API key.

    Tries JWT first, then API key if JWT not provided.

    Args:
        jwt_credentials: JWT Bearer credentials (optional)
        x_api_key: API key header (optional)
        request: FastAPI request
        session: Database session

    Returns:
        Authenticated User instance

    Raises:
        HTTPException: 401 if neither authentication method succeeds

    Usage:
        @router.get("/flexible-auth")
        async def flexible_route(user: User = Depends(get_current_user_or_api_key)):
            return {"user_id": user.id}
    """
    # Try JWT authentication first
    if jwt_credentials:
        try:
            return await get_current_user(jwt_credentials, session)
        except HTTPException:
            pass

    # Try API key authentication
    if x_api_key:
        try:
            api_key = await verify_api_key(x_api_key, request, session)
            return await get_user_from_api_key(api_key, session)
        except HTTPException:
            pass

    # Neither authentication method succeeded
    logger.warning("authentication_failed_both_methods")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide either Bearer token or X-API-Key header",
        headers={"WWW-Authenticate": "Bearer"}
    )
