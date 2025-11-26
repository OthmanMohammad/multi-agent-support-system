"""
Authentication package

Provides authentication and authorization utilities:
- JWT token management
- Password hashing
- API key management
- Redis caching and rate limiting
- RBAC (Role-Based Access Control)
"""

from src.api.auth.api_key_manager import APIKeyManager
from src.api.auth.jwt import JWTManager
from src.api.auth.password import PasswordManager
from src.api.auth.permissions import (
    ROLE_SCOPES,
    SCOPE_DESCRIPTIONS,
    PermissionScope,
    get_missing_permissions,
    get_role_scopes,
    has_all_permissions,
    has_any_permission,
    has_permission,
    require_any_scope,
    require_scopes,
)
from src.api.auth.redis_client import (
    RateLimiter,
    SessionCache,
    TokenBlacklist,
    close_redis_client,
    get_redis_client,
)

__all__ = [
    "ROLE_SCOPES",
    "SCOPE_DESCRIPTIONS",
    # API Keys
    "APIKeyManager",
    # JWT
    "JWTManager",
    # Passwords
    "PasswordManager",
    # Permissions
    "PermissionScope",
    "RateLimiter",
    "SessionCache",
    "TokenBlacklist",
    "close_redis_client",
    "get_missing_permissions",
    # Redis
    "get_redis_client",
    "get_role_scopes",
    "has_all_permissions",
    "has_any_permission",
    "has_permission",
    "require_any_scope",
    "require_scopes",
]
