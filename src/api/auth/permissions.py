"""
RBAC (Role-Based Access Control) - Permission scopes and enforcement

This module defines permission scopes and provides utilities for
enforcing role-based access control throughout the API.
"""

from functools import wraps

from fastapi import HTTPException, status

from src.database.models.user import UserRole
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)


# =============================================================================
# PERMISSION SCOPES
# =============================================================================


class PermissionScope:
    """
    Permission scopes for fine-grained access control.

    Scopes follow the pattern: action:resource:tier
    - action: read, write, execute, delete, admin
    - resource: agents, conversations, customers, analytics, etc.
    - tier: optional tier level for agents (tier1-tier4)
    """

    # Agent execution permissions
    READ_AGENTS = "read:agents"
    EXECUTE_AGENTS_TIER1 = "execute:agents:tier1"
    EXECUTE_AGENTS_TIER2 = "execute:agents:tier2"
    EXECUTE_AGENTS_TIER3 = "execute:agents:tier3"
    EXECUTE_AGENTS_TIER4 = "execute:agents:tier4"
    ADMIN_AGENTS = "admin:agents"

    # Conversation permissions
    READ_CONVERSATIONS = "read:conversations"
    WRITE_CONVERSATIONS = "write:conversations"
    DELETE_CONVERSATIONS = "delete:conversations"
    ASSIGN_CONVERSATIONS = "assign:conversations"
    ESCALATE_CONVERSATIONS = "escalate:conversations"

    # Customer permissions
    READ_CUSTOMERS = "read:customers"
    WRITE_CUSTOMERS = "write:customers"
    DELETE_CUSTOMERS = "delete:customers"
    READ_CUSTOMER_PII = "read:customers:pii"

    # Workflow permissions
    READ_WORKFLOWS = "read:workflows"
    EXECUTE_WORKFLOWS = "execute:workflows"
    WRITE_WORKFLOWS = "write:workflows"
    DELETE_WORKFLOWS = "delete:workflows"

    # Analytics permissions
    READ_ANALYTICS = "read:analytics"
    READ_ANALYTICS_DETAILED = "read:analytics:detailed"
    EXPORT_ANALYTICS = "export:analytics"

    # Webhook permissions
    READ_WEBHOOKS = "read:webhooks"
    WRITE_WEBHOOKS = "write:webhooks"
    DELETE_WEBHOOKS = "delete:webhooks"

    # API Key permissions
    READ_API_KEYS = "read:api_keys"
    WRITE_API_KEYS = "write:api_keys"
    DELETE_API_KEYS = "delete:api_keys"

    # User management permissions
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    MANAGE_ROLES = "manage:roles"

    # System administration
    ADMIN_CONFIG = "admin:config"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_SECURITY = "admin:security"

    # Wildcard (super admin only)
    ALL = "*"


# =============================================================================
# SCOPE DESCRIPTIONS
# =============================================================================

SCOPE_DESCRIPTIONS = {
    # Agents
    PermissionScope.READ_AGENTS: "View agent information and capabilities",
    PermissionScope.EXECUTE_AGENTS_TIER1: "Execute Tier 1 (Essential) agents",
    PermissionScope.EXECUTE_AGENTS_TIER2: "Execute Tier 2 (Revenue) agents",
    PermissionScope.EXECUTE_AGENTS_TIER3: "Execute Tier 3 (Operational) agents",
    PermissionScope.EXECUTE_AGENTS_TIER4: "Execute Tier 4 (Advanced) agents",
    PermissionScope.ADMIN_AGENTS: "Manage agent registry and configuration",
    # Conversations
    PermissionScope.READ_CONVERSATIONS: "View conversations",
    PermissionScope.WRITE_CONVERSATIONS: "Create and update conversations",
    PermissionScope.DELETE_CONVERSATIONS: "Delete conversations",
    PermissionScope.ASSIGN_CONVERSATIONS: "Assign conversations to agents",
    PermissionScope.ESCALATE_CONVERSATIONS: "Escalate conversations to humans",
    # Customers
    PermissionScope.READ_CUSTOMERS: "View customer information",
    PermissionScope.WRITE_CUSTOMERS: "Create and update customers",
    PermissionScope.DELETE_CUSTOMERS: "Delete customers",
    PermissionScope.READ_CUSTOMER_PII: "View customer PII (emails, phone numbers)",
    # Workflows
    PermissionScope.READ_WORKFLOWS: "View workflow definitions",
    PermissionScope.EXECUTE_WORKFLOWS: "Execute workflows",
    PermissionScope.WRITE_WORKFLOWS: "Create and update workflows",
    PermissionScope.DELETE_WORKFLOWS: "Delete workflows",
    # Analytics
    PermissionScope.READ_ANALYTICS: "View basic analytics",
    PermissionScope.READ_ANALYTICS_DETAILED: "View detailed analytics and reports",
    PermissionScope.EXPORT_ANALYTICS: "Export analytics data",
    # Webhooks
    PermissionScope.READ_WEBHOOKS: "View webhooks",
    PermissionScope.WRITE_WEBHOOKS: "Create and update webhooks",
    PermissionScope.DELETE_WEBHOOKS: "Delete webhooks",
    # API Keys
    PermissionScope.READ_API_KEYS: "View API keys",
    PermissionScope.WRITE_API_KEYS: "Create API keys",
    PermissionScope.DELETE_API_KEYS: "Revoke API keys",
    # Users
    PermissionScope.READ_USERS: "View users",
    PermissionScope.WRITE_USERS: "Create and update users",
    PermissionScope.DELETE_USERS: "Delete users",
    PermissionScope.MANAGE_ROLES: "Manage user roles and permissions",
    # System
    PermissionScope.ADMIN_CONFIG: "Modify system configuration",
    PermissionScope.ADMIN_SYSTEM: "System administration",
    PermissionScope.ADMIN_SECURITY: "Security administration",
    # Wildcard
    PermissionScope.ALL: "All permissions (super admin)",
}


# =============================================================================
# ROLE-SCOPE MAPPING
# =============================================================================

ROLE_SCOPES: dict[UserRole, list[str]] = {
    # Super admin has all permissions
    UserRole.SUPER_ADMIN: [PermissionScope.ALL],
    # Admin has most permissions except system administration
    UserRole.ADMIN: [
        # Agents
        PermissionScope.READ_AGENTS,
        PermissionScope.EXECUTE_AGENTS_TIER1,
        PermissionScope.EXECUTE_AGENTS_TIER2,
        PermissionScope.EXECUTE_AGENTS_TIER3,
        # Conversations
        PermissionScope.READ_CONVERSATIONS,
        PermissionScope.WRITE_CONVERSATIONS,
        PermissionScope.ASSIGN_CONVERSATIONS,
        PermissionScope.ESCALATE_CONVERSATIONS,
        # Customers
        PermissionScope.READ_CUSTOMERS,
        PermissionScope.WRITE_CUSTOMERS,
        PermissionScope.READ_CUSTOMER_PII,
        # Workflows
        PermissionScope.READ_WORKFLOWS,
        PermissionScope.EXECUTE_WORKFLOWS,
        PermissionScope.WRITE_WORKFLOWS,
        # Analytics
        PermissionScope.READ_ANALYTICS,
        PermissionScope.READ_ANALYTICS_DETAILED,
        PermissionScope.EXPORT_ANALYTICS,
        # Webhooks
        PermissionScope.READ_WEBHOOKS,
        PermissionScope.WRITE_WEBHOOKS,
        # API Keys
        PermissionScope.READ_API_KEYS,
        PermissionScope.WRITE_API_KEYS,
        # Users (manage team)
        PermissionScope.READ_USERS,
        PermissionScope.WRITE_USERS,
    ],
    # Regular user has standard permissions
    UserRole.USER: [
        # Agents (Tier 1 only)
        PermissionScope.READ_AGENTS,
        PermissionScope.EXECUTE_AGENTS_TIER1,
        # Conversations
        PermissionScope.READ_CONVERSATIONS,
        PermissionScope.WRITE_CONVERSATIONS,
        # Customers (limited)
        PermissionScope.READ_CUSTOMERS,
        # Workflows (execute only)
        PermissionScope.READ_WORKFLOWS,
        PermissionScope.EXECUTE_WORKFLOWS,
        # Analytics (basic)
        PermissionScope.READ_ANALYTICS,
        # API Keys (own keys only)
        PermissionScope.READ_API_KEYS,
        PermissionScope.WRITE_API_KEYS,
    ],
    # Read-only user
    UserRole.READONLY: [
        PermissionScope.READ_AGENTS,
        PermissionScope.READ_CONVERSATIONS,
        PermissionScope.READ_CUSTOMERS,
        PermissionScope.READ_WORKFLOWS,
        PermissionScope.READ_ANALYTICS,
    ],
    # API client (programmatic access)
    UserRole.API_CLIENT: [
        # Agents (Tier 1-2)
        PermissionScope.READ_AGENTS,
        PermissionScope.EXECUTE_AGENTS_TIER1,
        PermissionScope.EXECUTE_AGENTS_TIER2,
        # Conversations
        PermissionScope.READ_CONVERSATIONS,
        PermissionScope.WRITE_CONVERSATIONS,
        # Customers
        PermissionScope.READ_CUSTOMERS,
        PermissionScope.WRITE_CUSTOMERS,
        # Workflows
        PermissionScope.READ_WORKFLOWS,
        PermissionScope.EXECUTE_WORKFLOWS,
    ],
}


# =============================================================================
# PERMISSION CHECKING
# =============================================================================


def has_permission(user_scopes: list[str], required_scope: str) -> bool:
    """
    Check if user has a specific permission scope.

    Args:
        user_scopes: List of scopes the user has
        required_scope: Required scope

    Returns:
        True if user has permission, False otherwise

    Example:
        >>> has_permission(["read:agents", "execute:agents:tier1"], "read:agents")
        True
        >>> has_permission(["read:agents"], "write:agents")
        False
    """
    # Check for wildcard
    if PermissionScope.ALL in user_scopes:
        return True

    # Check for exact match
    return required_scope in user_scopes


def has_any_permission(user_scopes: list[str], required_scopes: list[str]) -> bool:
    """
    Check if user has any of the required permissions.

    Args:
        user_scopes: List of scopes the user has
        required_scopes: List of required scopes (any match)

    Returns:
        True if user has at least one permission, False otherwise

    Example:
        >>> has_any_permission(
        ...     ["read:agents"],
        ...     ["read:agents", "write:agents"]
        ... )
        True
    """
    # Check for wildcard
    if PermissionScope.ALL in user_scopes:
        return True

    # Check for any match
    user_scope_set = set(user_scopes)
    required_scope_set = set(required_scopes)
    return bool(user_scope_set & required_scope_set)


def has_all_permissions(user_scopes: list[str], required_scopes: list[str]) -> bool:
    """
    Check if user has all of the required permissions.

    Args:
        user_scopes: List of scopes the user has
        required_scopes: List of required scopes (all must match)

    Returns:
        True if user has all permissions, False otherwise

    Example:
        >>> has_all_permissions(
        ...     ["read:agents", "write:agents"],
        ...     ["read:agents", "write:agents"]
        ... )
        True
    """
    # Check for wildcard
    if PermissionScope.ALL in user_scopes:
        return True

    # Check for all matches
    user_scope_set = set(user_scopes)
    required_scope_set = set(required_scopes)
    return required_scope_set.issubset(user_scope_set)


def get_missing_permissions(user_scopes: list[str], required_scopes: list[str]) -> list[str]:
    """
    Get list of missing permissions.

    Args:
        user_scopes: List of scopes the user has
        required_scopes: List of required scopes

    Returns:
        List of missing scopes

    Example:
        >>> get_missing_permissions(
        ...     ["read:agents"],
        ...     ["read:agents", "write:agents"]
        ... )
        ['write:agents']
    """
    # Wildcard has all permissions
    if PermissionScope.ALL in user_scopes:
        return []

    user_scope_set = set(user_scopes)
    required_scope_set = set(required_scopes)
    return list(required_scope_set - user_scope_set)


def get_role_scopes(role: UserRole) -> list[str]:
    """
    Get all scopes for a role.

    Args:
        role: User role

    Returns:
        List of permission scopes

    Example:
        >>> scopes = get_role_scopes(UserRole.USER)
        >>> "read:agents" in scopes
        True
    """
    return ROLE_SCOPES.get(role, [])


# =============================================================================
# PERMISSION DECORATOR
# =============================================================================


def require_scopes(*required_scopes: str):
    """
    Decorator to enforce permission scopes on endpoints.

    Args:
        *required_scopes: Required permission scopes (all must match)

    Raises:
        HTTPException: 403 if user lacks required permissions

    Example:
        >>> @require_scopes(PermissionScope.READ_AGENTS)
        ... async def get_agents(current_user: User = Depends(get_current_user)):
        ...     return agents
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")

            if not current_user:
                logger.error("require_scopes_no_user", endpoint=func.__name__)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication dependency not configured",
                )

            # Get user scopes
            user_scopes = current_user.get_scopes()

            # Check permissions
            if not has_all_permissions(user_scopes, list(required_scopes)):
                missing = get_missing_permissions(user_scopes, list(required_scopes))

                logger.warning(
                    "permission_denied",
                    user_id=str(current_user.id),
                    user_email=current_user.email,
                    user_role=current_user.role.value,
                    required_scopes=list(required_scopes),
                    missing_scopes=missing,
                    endpoint=func.__name__,
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing)}",
                )

            logger.debug(
                "permission_granted",
                user_id=str(current_user.id),
                scopes=list(required_scopes),
                endpoint=func.__name__,
            )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_scope(*required_scopes: str):
    """
    Decorator to enforce permission scopes (any match).

    Args:
        *required_scopes: Required permission scopes (any match)

    Raises:
        HTTPException: 403 if user lacks any required permission

    Example:
        >>> @require_any_scope(PermissionScope.READ_AGENTS, PermissionScope.ADMIN_AGENTS)
        ... async def get_agents(current_user: User = Depends(get_current_user)):
        ...     return agents
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication dependency not configured",
                )

            user_scopes = current_user.get_scopes()

            if not has_any_permission(user_scopes, list(required_scopes)):
                logger.warning(
                    "permission_denied",
                    user_id=str(current_user.id),
                    required_scopes_any=list(required_scopes),
                    endpoint=func.__name__,
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions (need any of): {', '.join(required_scopes)}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
