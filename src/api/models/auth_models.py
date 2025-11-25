"""
Authentication Pydantic Models

Request and response models for authentication endpoints.
"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator

from src.database.models.user import UserRole, UserStatus


# =============================================================================
# USER REGISTRATION
# =============================================================================

class UserRegisterRequest(BaseModel):
    """User registration request"""

    email: EmailStr = Field(..., description="User email address")
    password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)"
    )
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    organization: Optional[str] = Field(None, max_length=255, description="Organization name")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "organization": "Acme Corp"
            }]
        }
    }


class UserRegisterResponse(BaseModel):
    """User registration response"""

    user_id: UUID
    email: str
    full_name: str
    role: str
    status: str
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "status": "pending_verification",
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "Bearer",
                "expires_in": 3600
            }]
        }
    }


# =============================================================================
# USER LOGIN
# =============================================================================

class LoginRequest(BaseModel):
    """User login request"""

    email: EmailStr = Field(..., description="User email address")
    password: SecretStr = Field(..., description="Password")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com",
                "password": "SecurePass123!"
            }]
        }
    }


class OAuthLoginRequest(BaseModel):
    """OAuth login request - for NextAuth integration"""

    email: EmailStr = Field(..., description="User email from OAuth provider")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name from OAuth provider")
    provider: str = Field(..., description="OAuth provider name (google, github)")
    provider_user_id: str = Field(..., description="User ID from OAuth provider")
    avatar_url: Optional[str] = Field(None, description="Avatar URL from OAuth provider")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@gmail.com",
                "full_name": "John Doe",
                "provider": "google",
                "provider_user_id": "123456789",
                "avatar_url": "https://lh3.googleusercontent.com/..."
            }]
        }
    }


class LoginResponse(BaseModel):
    """User login response"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: "UserProfile"

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "role": "user",
                    "status": "active",
                    "is_verified": True,
                    "scopes": ["read:agents", "execute:agents:tier1"]
                }
            }]
        }
    }


# =============================================================================
# TOKEN REFRESH
# =============================================================================

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str = Field(..., description="Refresh token")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }]
        }
    }


class RefreshTokenResponse(BaseModel):
    """Refresh token response"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "Bearer",
                "expires_in": 3600
            }]
        }
    }


# =============================================================================
# LOGOUT
# =============================================================================

class LogoutResponse(BaseModel):
    """Logout response"""

    message: str = "Successfully logged out"


# =============================================================================
# PASSWORD RESET
# =============================================================================

class PasswordResetRequest(BaseModel):
    """Password reset request (initiate reset)"""

    email: EmailStr = Field(..., description="User email address")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "user@example.com"
            }]
        }
    }


class PasswordResetResponse(BaseModel):
    """Password reset response"""

    message: str = "Password reset email sent"


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation (complete reset)"""

    token: str = Field(..., description="Password reset token from email")
    new_password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "token": "abc123def456",
                "new_password": "NewSecurePass123!"
            }]
        }
    }


# =============================================================================
# EMAIL VERIFICATION
# =============================================================================

class EmailVerificationRequest(BaseModel):
    """Email verification request"""

    token: str = Field(..., description="Email verification token")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "token": "abc123def456"
            }]
        }
    }


class EmailVerificationResponse(BaseModel):
    """Email verification response"""

    message: str = "Email verified successfully"
    user: "UserProfile"


class ResendVerificationRequest(BaseModel):
    """Resend verification email request"""

    email: EmailStr = Field(..., description="User email address")


# =============================================================================
# USER PROFILE
# =============================================================================

class UserProfile(BaseModel):
    """User profile information"""

    id: UUID
    email: str
    full_name: str
    organization: Optional[str] = None
    role: str
    status: str
    is_active: bool
    is_verified: bool
    scopes: List[str] = []
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "organization": "Acme Corp",
                "role": "user",
                "status": "active",
                "is_active": True,
                "is_verified": True,
                "scopes": ["read:agents", "execute:agents:tier1"],
                "created_at": "2025-01-01T00:00:00Z",
                "last_login_at": "2025-11-16T12:00:00Z"
            }]
        }
    }


class UpdateUserProfile(BaseModel):
    """Update user profile request"""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    organization: Optional[str] = Field(None, max_length=255)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "full_name": "Jane Doe",
                "organization": "New Corp"
            }]
        }
    }


class ChangePasswordRequest(BaseModel):
    """Change password request"""

    current_password: SecretStr = Field(..., description="Current password")
    new_password: SecretStr = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass123!"
            }]
        }
    }


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

class APIKeyCreateRequest(BaseModel):
    """Create API key request"""

    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    scopes: List[str] = Field(
        default=["read:agents", "execute:agents:tier1"],
        description="Permission scopes"
    )
    expires_at: Optional[datetime] = Field(None, description="Expiration date (optional)")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "Production API Key",
                "scopes": ["read:agents", "execute:agents:tier1", "write:conversations"],
                "expires_at": "2026-01-01T00:00:00Z",
                "description": "API key for production integration"
            }]
        }
    }


class APIKeyResponse(BaseModel):
    """API key response"""

    id: UUID
    name: str
    key: Optional[str] = Field(None, description="Full API key (only shown once!)")
    key_prefix: str = Field(..., description="Key prefix for identification")
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    usage_count: int

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Production API Key",
                "key": "msa_live_abc123def456...",
                "key_prefix": "msa_live_abc123def45",
                "scopes": ["read:agents", "execute:agents:tier1"],
                "is_active": True,
                "expires_at": "2026-01-01T00:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "last_used_at": "2025-11-16T12:00:00Z",
                "usage_count": 1542
            }]
        }
    }


class APIKeyListResponse(BaseModel):
    """List of API keys"""

    keys: List[APIKeyResponse]
    total: int


# =============================================================================
# UPDATE CIRCULAR REFERENCES
# =============================================================================

# Update forward references for nested models
LoginResponse.model_rebuild()
EmailVerificationResponse.model_rebuild()
