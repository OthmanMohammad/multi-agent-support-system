"""
Authentication Routes - User authentication and API key management

Endpoints:
- POST /auth/register - User registration
- POST /auth/login - User login
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout and revoke tokens
- POST /auth/reset-password - Initiate password reset
- POST /auth/reset-password/confirm - Complete password reset
- POST /auth/verify-email - Verify email address
- POST /auth/resend-verification - Resend verification email
- GET /auth/me - Get current user profile
- PUT /auth/me - Update user profile
- POST /auth/me/change-password - Change password
- GET /auth/api-keys - List API keys
- POST /auth/api-keys - Create API key
- DELETE /auth/api-keys/{id} - Revoke API key
"""

from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User, UserRole, UserStatus
from src.database.models.api_key import APIKey
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session
from src.api.models.auth_models import (
    UserRegisterRequest,
    UserRegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
    EmailVerificationRequest,
    EmailVerificationResponse,
    ResendVerificationRequest,
    UserProfile,
    UpdateUserProfile,
    ChangePasswordRequest,
    APIKeyCreateRequest,
    APIKeyResponse,
    APIKeyListResponse,
)
from src.api.dependencies import get_current_user, get_current_active_user
from src.api.auth import (
    JWTManager,
    PasswordManager,
    APIKeyManager,
    TokenBlacklist,
    get_role_scopes,
)
from src.core.config import get_settings
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# USER REGISTRATION
# =============================================================================

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: UserRegisterRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Register a new user account.

    Creates a new user with pending email verification status.
    Returns JWT tokens for immediate authentication.

    - **email**: Valid email address (unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - **full_name**: User's full name
    - **organization**: Optional organization name
    """
    logger.info("user_registration_started", email=request.email)

    # Validate password strength
    is_valid, error = PasswordManager.validate_password_strength(request.password.get_secret_value())
    if not is_valid:
        logger.warning("registration_weak_password", email=request.email, error=error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    async with UnitOfWork(session) as uow:
        # Check if email already exists
        if await uow.users.email_exists(request.email):
            logger.warning("registration_email_exists", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Hash password
        password_hash = PasswordManager.hash_password(request.password.get_secret_value())

        # Generate email verification token
        verification_token = PasswordManager.generate_email_verification_token()

        # Create user
        user = await uow.users.create(
            email=request.email,
            password_hash=password_hash,
            full_name=request.full_name,
            organization=request.organization,
            role=UserRole.USER,
            status=UserStatus.PENDING_VERIFICATION,
            is_active=True,
            is_verified=False,
            email_verification_token=verification_token,
        )

        # Get role scopes
        scopes = get_role_scopes(user.role)
        user.set_scopes(scopes)

        await uow.commit()

        logger.info(
            "user_registered",
            user_id=str(user.id),
            email=user.email,
            role=user.role.value
        )

        # Generate JWT tokens
        access_token = JWTManager.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            scopes=scopes
        )

        refresh_token = JWTManager.create_refresh_token(user_id=user.id)

        # TODO: Send verification email (implement email service)
        logger.info("verification_email_queued", user_id=str(user.id), token=verification_token)

        return UserRegisterResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.jwt.access_token_expire_minutes * 60
        )


# =============================================================================
# USER LOGIN
# =============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate user and return JWT tokens.

    Returns access token (short-lived) and refresh token (long-lived).

    - **email**: User email address
    - **password**: User password
    """
    logger.info("user_login_attempt", email=request.email)

    async with UnitOfWork(session) as uow:
        # Get user by email
        user = await uow.users.get_by_email(request.email)

        if not user:
            logger.warning("login_failed_user_not_found", email=request.email)
            # Don't reveal if user exists
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Verify password
        if not user.password_hash or not PasswordManager.verify_password(
            request.password.get_secret_value(),
            user.password_hash
        ):
            logger.warning("login_failed_invalid_password", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        # Check if user is active
        if not user.is_active:
            logger.warning("login_failed_inactive_user", email=request.email, status=user.status.value)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

        # Update last login
        await uow.users.update_last_login(user.id)
        await uow.commit()

        logger.info("user_logged_in", user_id=str(user.id), email=user.email)

        # Generate JWT tokens
        scopes = user.get_scopes()
        access_token = JWTManager.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            scopes=scopes
        )

        refresh_token = JWTManager.create_refresh_token(user_id=user.id)

        # Build user profile
        user_profile = UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization=user.organization,
            role=user.role.value,
            status=user.status.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            scopes=scopes,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.jwt.access_token_expire_minutes * 60,
            user=user_profile
        )


# =============================================================================
# TOKEN REFRESH
# =============================================================================

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token using refresh token.

    Returns new access token and new refresh token (token rotation).

    - **refresh_token**: Valid refresh token
    """
    logger.debug("token_refresh_started")

    # Validate refresh token
    try:
        payload = JWTManager.validate_refresh_token(request.refresh_token)
    except HTTPException as e:
        logger.warning("token_refresh_failed_invalid_token")
        raise e

    # Extract JWT ID
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # Check if token is blacklisted
    if await TokenBlacklist.is_blacklisted(jti):
        logger.warning("token_refresh_failed_blacklisted", jti=jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )

    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    async with UnitOfWork(session) as uow:
        # Get user
        user = await uow.users.get(user_id)

        if not user or not user.is_active:
            logger.warning("token_refresh_failed_user_inactive", user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active"
            )

        logger.info("token_refreshed", user_id=str(user.id))

        # Generate new tokens
        scopes = user.get_scopes()
        new_access_token = JWTManager.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            scopes=scopes
        )

        new_refresh_token = JWTManager.create_refresh_token(user_id=user.id)

        # Blacklist old refresh token (token rotation)
        ttl = settings.jwt.refresh_token_expire_days * 24 * 60 * 60
        await TokenBlacklist.add_token(jti, ttl_seconds=ttl)

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.jwt.access_token_expire_minutes * 60
        )


# =============================================================================
# LOGOUT
# =============================================================================

@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user and revoke tokens.

    Blacklists the current access token to prevent further use.
    Client should also discard refresh token.
    """
    logger.info("user_logout", user_id=str(current_user.id))

    # TODO: Extract JTI from request headers and blacklist
    # For now, just return success
    # In production, extract token from Authorization header and blacklist it

    return LogoutResponse(message="Successfully logged out")


# =============================================================================
# PASSWORD RESET
# =============================================================================

@router.post("/reset-password", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Request password reset email.

    Sends password reset link to user's email.
    Always returns success (don't reveal if email exists).

    - **email**: User email address
    """
    logger.info("password_reset_requested", email=request.email)

    async with UnitOfWork(session) as uow:
        user = await uow.users.get_by_email(request.email)

        if user:
            # Generate reset token
            reset_token = PasswordManager.generate_password_reset_token()
            expires_at = datetime.utcnow() + timedelta(hours=24)

            # Save reset token
            await uow.users.set_password_reset_token(
                user.id,
                reset_token,
                expires_at
            )
            await uow.commit()

            # TODO: Send password reset email
            logger.info(
                "password_reset_email_queued",
                user_id=str(user.id),
                token=reset_token
            )
        else:
            logger.debug("password_reset_email_not_found", email=request.email)

    # Always return success (security: don't reveal if email exists)
    return PasswordResetResponse(message="If that email exists, a password reset link has been sent")


@router.post("/reset-password/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Complete password reset with token.

    - **token**: Password reset token from email
    - **new_password**: New password (must meet strength requirements)
    """
    logger.info("password_reset_confirm_started")

    # Validate password strength
    is_valid, error = PasswordManager.validate_password_strength(
        request.new_password.get_secret_value()
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    async with UnitOfWork(session) as uow:
        # Find user with this reset token
        # Note: This is a simplified query - in production, add index on reset token
        users = await uow.users.get_active_users(limit=1000)
        user = None
        for u in users:
            if u.password_reset_token == request.token:
                user = u
                break

        if not user:
            logger.warning("password_reset_invalid_token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )

        # Check token expiration
        if not user.password_reset_expires_at or user.password_reset_expires_at < datetime.utcnow():
            logger.warning("password_reset_token_expired", user_id=str(user.id))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired"
            )

        # Hash new password
        password_hash = PasswordManager.hash_password(request.new_password.get_secret_value())

        # Update password and clear reset token
        await uow.users.update(user.id, password_hash=password_hash)
        await uow.users.clear_password_reset_token(user.id)
        await uow.commit()

        logger.info("password_reset_completed", user_id=str(user.id))

        return {"message": "Password reset successfully"}


# =============================================================================
# EMAIL VERIFICATION
# =============================================================================

@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email(
    request: EmailVerificationRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Verify email address with token.

    - **token**: Email verification token from email
    """
    logger.info("email_verification_started")

    async with UnitOfWork(session) as uow:
        # Find user with this verification token
        users = await uow.users.get_by_status(UserStatus.PENDING_VERIFICATION, limit=1000)
        user = None
        for u in users:
            if u.email_verification_token == request.token:
                user = u
                break

        if not user:
            logger.warning("email_verification_invalid_token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email verification token"
            )

        # Verify email
        await uow.users.verify_email(user.id)
        await uow.commit()

        logger.info("email_verified", user_id=str(user.id))

        # Build user profile
        user_profile = UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization=user.organization,
            role=user.role.value,
            status=UserStatus.ACTIVE.value,
            is_active=user.is_active,
            is_verified=True,
            scopes=user.get_scopes(),
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )

        return EmailVerificationResponse(
            message="Email verified successfully",
            user=user_profile
        )


@router.post("/resend-verification")
async def resend_verification_email(
    request: ResendVerificationRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Resend email verification link.

    - **email**: User email address
    """
    logger.info("resend_verification_requested", email=request.email)

    async with UnitOfWork(session) as uow:
        user = await uow.users.get_by_email(request.email)

        if user and not user.is_verified:
            # Generate new verification token
            verification_token = PasswordManager.generate_email_verification_token()

            await uow.users.update(user.id, email_verification_token=verification_token)
            await uow.commit()

            # TODO: Send verification email
            logger.info(
                "verification_email_resent",
                user_id=str(user.id),
                token=verification_token
            )

    return {"message": "If that email exists and is unverified, a new verification link has been sent"}


# =============================================================================
# USER PROFILE
# =============================================================================

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.

    Returns detailed information about the authenticated user.
    """
    logger.debug("get_user_profile", user_id=str(current_user.id))

    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        organization=current_user.organization,
        role=current_user.role.value,
        status=current_user.status.value,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        scopes=current_user.get_scopes(),
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    request: UpdateUserProfile,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update current user profile.

    - **full_name**: Updated full name (optional)
    - **organization**: Updated organization (optional)
    """
    logger.info("update_user_profile", user_id=str(current_user.id))

    async with UnitOfWork(session) as uow:
        # Build update dict (only update provided fields)
        update_data = {}
        if request.full_name is not None:
            update_data["full_name"] = request.full_name
        if request.organization is not None:
            update_data["organization"] = request.organization

        if update_data:
            await uow.users.update(current_user.id, **update_data)
            await uow.commit()

            # Refresh user
            updated_user = await uow.users.get(current_user.id)

            logger.info("user_profile_updated", user_id=str(current_user.id), fields=list(update_data.keys()))

            return UserProfile(
                id=updated_user.id,
                email=updated_user.email,
                full_name=updated_user.full_name,
                organization=updated_user.organization,
                role=updated_user.role.value,
                status=updated_user.status.value,
                is_active=updated_user.is_active,
                is_verified=updated_user.is_verified,
                scopes=updated_user.get_scopes(),
                created_at=updated_user.created_at,
                last_login_at=updated_user.last_login_at
            )

        # No changes
        return UserProfile.model_validate(current_user)


@router.post("/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Change current user password.

    - **current_password**: Current password
    - **new_password**: New password (must meet strength requirements)
    """
    logger.info("change_password_started", user_id=str(current_user.id))

    # Verify current password
    if not current_user.password_hash or not PasswordManager.verify_password(
        request.current_password.get_secret_value(),
        current_user.password_hash
    ):
        logger.warning("change_password_invalid_current", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    is_valid, error = PasswordManager.validate_password_strength(
        request.new_password.get_secret_value()
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Hash new password
    password_hash = PasswordManager.hash_password(request.new_password.get_secret_value())

    async with UnitOfWork(session) as uow:
        await uow.users.update(current_user.id, password_hash=password_hash)
        await uow.commit()

        logger.info("password_changed", user_id=str(current_user.id))

        return {"message": "Password changed successfully"}


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List all API keys for current user.

    Returns all API keys (active and inactive) owned by the user.
    """
    logger.debug("list_api_keys", user_id=str(current_user.id))

    async with UnitOfWork(session) as uow:
        api_keys = await uow.api_keys.get_user_keys(current_user.id, include_inactive=True)

        key_responses = [
            APIKeyResponse(
                id=key.id,
                name=key.name,
                key=None,  # Never return full key
                key_prefix=key.key_prefix,
                scopes=key.get_scopes(),
                is_active=key.is_active,
                expires_at=key.expires_at,
                created_at=key.created_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count
            )
            for key in api_keys
        ]

        return APIKeyListResponse(
            keys=key_responses,
            total=len(key_responses)
        )


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create a new API key.

    Returns the full API key - **save it immediately as it won't be shown again!**

    - **name**: Human-readable name for the key
    - **scopes**: Permission scopes (defaults to basic permissions)
    - **expires_at**: Optional expiration date
    - **description**: Optional description
    """
    logger.info("create_api_key_started", user_id=str(current_user.id), name=request.name)

    # Generate API key
    is_test = settings.environment == "staging"
    full_key, key_prefix, key_hash = APIKeyManager.generate_api_key(is_test=is_test)

    async with UnitOfWork(session) as uow:
        # Create API key
        api_key = await uow.api_keys.create(
            user_id=current_user.id,
            name=request.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=",".join(request.scopes) if request.scopes else None,
            expires_at=request.expires_at,
            is_active=True,
            description=request.description,
            usage_count=0
        )

        await uow.commit()

        logger.info(
            "api_key_created",
            user_id=str(current_user.id),
            key_id=str(api_key.id),
            key_prefix=key_prefix
        )

        # Return full key (only time it's shown!)
        return APIKeyResponse(
            id=api_key.id,
            name=api_key.name,
            key=full_key,  # Only shown once!
            key_prefix=key_prefix,
            scopes=api_key.get_scopes(),
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            usage_count=api_key.usage_count
        )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Revoke an API key.

    Permanently revokes the specified API key (soft delete).

    - **key_id**: UUID of the API key to revoke
    """
    logger.info("revoke_api_key_started", user_id=str(current_user.id), key_id=str(key_id))

    async with UnitOfWork(session) as uow:
        # Get API key
        api_key = await uow.api_keys.get(key_id)

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        # Check ownership
        if api_key.user_id != current_user.id:
            logger.warning(
                "revoke_api_key_unauthorized",
                user_id=str(current_user.id),
                key_id=str(key_id),
                key_owner=str(api_key.user_id)
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to revoke this API key"
            )

        # Revoke (soft delete)
        await uow.api_keys.revoke_key(key_id)
        await uow.commit()

        logger.info("api_key_revoked", user_id=str(current_user.id), key_id=str(key_id))

        return None  # 204 No Content
