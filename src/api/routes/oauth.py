"""
OAuth 2.0 Routes - Social authentication with Google and GitHub

Provides endpoints for:
- Google OAuth login
- GitHub OAuth login
- OAuth callback handling
- Token exchange

Part of: Phase 4 - Security & OAuth
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import secrets
from datetime import datetime

from src.api.models.auth_models import LoginResponse, UserProfile
from src.api.auth.jwt import JWTManager
from src.database.repositories.user_repository import UserRepository
from src.database.models.user import User, UserRole, UserStatus
from src.database.connection import get_db_session
from src.database.uow import UnitOfWork
from src.core.config import get_settings
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create router
router = APIRouter(prefix="/oauth")


# =============================================================================
# OAUTH STATE MANAGEMENT (in-memory for now, should use Redis)
# =============================================================================

class OAuthStateStore:
    """In-memory OAuth state storage"""

    def __init__(self):
        self._states = {}

    def create_state(self, provider: str) -> str:
        """Create OAuth state token"""
        state = secrets.token_urlsafe(32)
        self._states[state] = {
            "provider": provider,
            "created_at": datetime.utcnow(),
        }
        return state

    def verify_state(self, state: str, provider: str) -> bool:
        """Verify OAuth state token"""
        if state not in self._states:
            return False
        stored = self._states.pop(state)
        return stored["provider"] == provider


oauth_state_store = OAuthStateStore()


# =============================================================================
# OAUTH CONFIGURATION
# =============================================================================

OAUTH_CONFIG = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["openid", "email", "profile"],
    },
    "github": {
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "user_info_url": "https://api.github.com/user",
        "scopes": ["user:email", "read:user"],
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_or_create_oauth_user(
    email: str,
    full_name: str,
    provider: str,
    provider_user_id: str,
    session
) -> User:
    """Get or create user from OAuth data"""

    uow = UnitOfWork(session)

    # Check if user exists with this OAuth provider
    user = await uow.users.get_by_oauth(provider, provider_user_id)

    if user:
        # Update last login
        await uow.users.update_last_login(user.id)
        await uow.commit()
        return user

    # Check if user exists with this email
    user = await uow.users.get_by_email(email)

    if user:
        # Link OAuth provider to existing user
        user.oauth_provider = provider
        user.oauth_provider_user_id = provider_user_id
        await uow.users.update_last_login(user.id)
        await uow.commit()
        return user

    # Create new user
    user = User(
        email=email,
        full_name=full_name,
        oauth_provider=provider,
        oauth_provider_user_id=provider_user_id,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_verified=True,  # OAuth users are pre-verified
        password_hash=None,  # No password for OAuth users
    )

    uow.session.add(user)
    await uow.commit()
    await uow.session.refresh(user)

    logger.info(
        "oauth_user_created",
        user_id=str(user.id),
        email=email,
        provider=provider
    )

    return user


# =============================================================================
# GOOGLE OAUTH
# =============================================================================

@router.get("/google")
async def google_oauth_login(
    redirect_uri: Optional[str] = Query(None, description="Redirect URI after auth")
):
    """
    Initiate Google OAuth flow.

    Redirects user to Google consent screen. User will be redirected back
    to the callback URL after authorization.

    No authentication required.
    """
    logger.info("google_oauth_initiated")

    # Create state token
    state = oauth_state_store.create_state("google")

    # Build authorization URL
    # Note: In production, use actual OAuth client ID from settings
    client_id = settings.oauth.google_client_id if hasattr(settings, 'oauth') else "YOUR_GOOGLE_CLIENT_ID"
    callback_url = f"{settings.api.base_url}/api/oauth/google/callback"

    scopes = " ".join(OAUTH_CONFIG["google"]["scopes"])

    auth_url = (
        f"{OAUTH_CONFIG['google']['auth_url']}?"
        f"client_id={client_id}&"
        f"redirect_uri={callback_url}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"state={state}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    return RedirectResponse(url=auth_url)


@router.get("/google/callback", response_model=LoginResponse)
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State token"),
    session = Depends(get_db_session)
):
    """
    Google OAuth callback endpoint.

    Receives authorization code from Google, exchanges it for tokens,
    retrieves user information, and creates/logs in the user.

    Returns JWT tokens for API authentication.
    """
    logger.info("google_oauth_callback", state=state)

    # Verify state
    if not oauth_state_store.verify_state(state, "google"):
        logger.warning("google_oauth_invalid_state", state=state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state"
        )

    # TODO: Exchange code for access token
    # TODO: Fetch user info from Google
    # For now, use mock data

    mock_email = "oauth_user@gmail.com"
    mock_name = "OAuth User"
    mock_provider_id = "google_123456789"

    # Get or create user
    user = await get_or_create_oauth_user(
        email=mock_email,
        full_name=mock_name,
        provider="google",
        provider_user_id=mock_provider_id,
        session=session
    )

    # Create JWT tokens
    access_token = JWTManager.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        scopes=user.get_scopes()
    )

    refresh_token = JWTManager.create_refresh_token(user_id=user.id)

    logger.info(
        "google_oauth_success",
        user_id=str(user.id),
        email=user.email
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.jwt.access_token_expire_minutes * 60,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization=user.organization,
            role=user.role.value,
            status=user.status.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            scopes=user.get_scopes(),
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
    )


# =============================================================================
# GITHUB OAUTH
# =============================================================================

@router.get("/github")
async def github_oauth_login(
    redirect_uri: Optional[str] = Query(None, description="Redirect URI after auth")
):
    """
    Initiate GitHub OAuth flow.

    Redirects user to GitHub authorization screen. User will be redirected back
    to the callback URL after authorization.

    No authentication required.
    """
    logger.info("github_oauth_initiated")

    # Create state token
    state = oauth_state_store.create_state("github")

    # Build authorization URL
    # Note: In production, use actual OAuth client ID from settings
    client_id = settings.oauth.github_client_id if hasattr(settings, 'oauth') else "YOUR_GITHUB_CLIENT_ID"
    callback_url = f"{settings.api.base_url}/api/oauth/github/callback"

    scopes = " ".join(OAUTH_CONFIG["github"]["scopes"])

    auth_url = (
        f"{OAUTH_CONFIG['github']['auth_url']}?"
        f"client_id={client_id}&"
        f"redirect_uri={callback_url}&"
        f"scope={scopes}&"
        f"state={state}"
    )

    return RedirectResponse(url=auth_url)


@router.get("/github/callback", response_model=LoginResponse)
async def github_oauth_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State token"),
    session = Depends(get_db_session)
):
    """
    GitHub OAuth callback endpoint.

    Receives authorization code from GitHub, exchanges it for tokens,
    retrieves user information, and creates/logs in the user.

    Returns JWT tokens for API authentication.
    """
    logger.info("github_oauth_callback", state=state)

    # Verify state
    if not oauth_state_store.verify_state(state, "github"):
        logger.warning("github_oauth_invalid_state", state=state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state"
        )

    # TODO: Exchange code for access token
    # TODO: Fetch user info from GitHub
    # For now, use mock data

    mock_email = "oauth_user@github.com"
    mock_name = "GitHub User"
    mock_provider_id = "github_987654321"

    # Get or create user
    user = await get_or_create_oauth_user(
        email=mock_email,
        full_name=mock_name,
        provider="github",
        provider_user_id=mock_provider_id,
        session=session
    )

    # Create JWT tokens
    access_token = JWTManager.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
        scopes=user.get_scopes()
    )

    refresh_token = JWTManager.create_refresh_token(user_id=user.id)

    logger.info(
        "github_oauth_success",
        user_id=str(user.id),
        email=user.email
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.jwt.access_token_expire_minutes * 60,
        user=UserProfile(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization=user.organization,
            role=user.role.value,
            status=user.status.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            scopes=user.get_scopes(),
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
    )


# =============================================================================
# OAUTH STATUS
# =============================================================================

@router.get("/providers")
async def list_oauth_providers():
    """
    List available OAuth providers.

    Returns configuration for supported OAuth providers.
    No authentication required.
    """
    return {
        "providers": [
            {
                "name": "google",
                "display_name": "Google",
                "auth_url": "/api/oauth/google",
                "enabled": True,
            },
            {
                "name": "github",
                "display_name": "GitHub",
                "auth_url": "/api/oauth/github",
                "enabled": True,
            },
        ]
    }
