"""
Authentication package

Provides authentication and authorization utilities:
- JWT token management
- Password hashing
- API key management
- Redis caching and rate limiting
- RBAC (Role-Based Access Control)
"""

from src.api.auth.jwt import JWTManager
from src.api.auth.password import PasswordManager
from src.api.auth.api_key_manager import APIKeyManager
from src.api.auth.redis_client import (
    get_redis_client,
    close_redis_client,
    TokenBlacklist,
    RateLimiter,
    SessionCache
)
from src.api.auth.permissions import (
    PermissionScope,
    SCOPE_DESCRIPTIONS,
    ROLE_SCOPES,
    has_permission,
    has_any_permission,
    has_all_permissions,
    get_missing_permissions,
    get_role_scopes,
    require_scopes,
    require_any_scope,
)

__all__ = [
    # JWT
    "JWTManager",
    # Passwords
    "PasswordManager",
    # API Keys
    "APIKeyManager",
    # Redis
    "get_redis_client",
    "close_redis_client",
    "TokenBlacklist",
    "RateLimiter",
    "SessionCache",
    # Permissions
    "PermissionScope",
    "SCOPE_DESCRIPTIONS",
    "ROLE_SCOPES",
    "has_permission",
    "has_any_permission",
    "has_all_permissions",
    "get_missing_permissions",
    "get_role_scopes",
    "require_scopes",
    "require_any_scope",
]
