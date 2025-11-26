"""
API Dependencies Package

FastAPI dependency injection utilities for authentication,
database access, and other cross-cutting concerns.
"""

from src.api.dependencies.auth_dependencies import (
    get_current_active_user,
    get_current_user,
    get_current_user_or_api_key,
    get_optional_user,
    get_user_from_api_key,
    verify_api_key,
)
from src.api.dependencies.service_dependencies import (
    get_analytics_service,
    get_conversation_application_service,
    get_customer_application_service,
)

__all__ = [
    "get_analytics_service",
    # Service dependencies
    "get_conversation_application_service",
    "get_current_active_user",
    # JWT authentication
    "get_current_user",
    # Combined authentication
    "get_current_user_or_api_key",
    "get_customer_application_service",
    "get_optional_user",
    "get_user_from_api_key",
    # API key authentication
    "verify_api_key",
]
