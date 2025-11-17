"""
API Dependencies Package

FastAPI dependency injection utilities for authentication,
database access, and other cross-cutting concerns.
"""

from src.api.dependencies.auth_dependencies import (
    get_current_user,
    get_current_active_user,
    get_optional_user,
    verify_api_key,
    get_user_from_api_key,
    get_current_user_or_api_key,
)

from src.api.dependencies.service_dependencies import (
    get_conversation_application_service,
)

__all__ = [
    # JWT authentication
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    # API key authentication
    "verify_api_key",
    "get_user_from_api_key",
    # Combined authentication
    "get_current_user_or_api_key",
    # Service dependencies
    "get_conversation_application_service",
]
