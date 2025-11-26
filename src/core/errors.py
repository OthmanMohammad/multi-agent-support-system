"""
Enhanced Error Types - Structured error handling with context

This module provides specific error classes for different failure scenarios.
All errors inherit from the base Error class and include structured context.

Error Categories:
- ValidationError: Input validation failures
- BusinessRuleError: Business logic violations
- NotFoundError: Resource not found
- ConflictError: Resource conflicts (duplicates)
- AuthorizationError: Permission denied
- RateLimitError: Rate limit exceeded
- InternalError: Unexpected internal failures

Example:
    >>> from core.errors import ValidationError, NotFoundError
    >>>
    >>> # Validation error with field context
    >>> error = ValidationError(
    ...     message="Email is required",
    ...     field="email",
    ...     constraint="required"
    ... )
    >>>
    >>> # Not found error with resource context
    >>> error = NotFoundError(
    ...     resource="Customer",
    ...     identifier="user@example.com"
    ... )
"""

from typing import Any

from src.core.result import Error

__all__ = [
    "AuthorizationError",
    "BusinessRuleError",
    "ConflictError",
    "ExternalServiceError",
    "InternalError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
]


# ===== Error Factory Functions =====
# These provide convenient ways to create specific error types


def ValidationError(
    message: str,
    field: str | None = None,
    value: Any | None = None,
    constraint: str | None = None,
    **extra_details,
) -> Error:
    """
    Create a validation error for invalid input

    Use when:
    - Required fields are missing
    - Field values don't meet constraints
    - Input format is invalid
    - Data type is incorrect

    Args:
        message: Human-readable error message
        field: Name of the field that failed validation
        value: The invalid value (will be converted to string)
        constraint: Type of constraint violated (required, min_length, pattern, etc.)
        **extra_details: Additional context fields

    Returns:
        Error with VALIDATION_ERROR code

    Example:
        >>> error = ValidationError(
        ...     message="Email must be valid",
        ...     field="email",
        ...     value="invalid-email",
        ...     constraint="email_format"
        ... )
        >>> error.code
        'VALIDATION_ERROR'
        >>> error.details['field']
        'email'
    """
    details = {**extra_details}

    if field:
        details["field"] = field
    if value is not None:
        details["value"] = str(value)[:100]  # Truncate long values
    if constraint:
        details["constraint"] = constraint

    return Error(code="VALIDATION_ERROR", message=message, details=details if details else None)


def BusinessRuleError(
    message: str, rule: str | None = None, entity: str | None = None, **extra_details
) -> Error:
    """
    Create a business rule violation error

    Use when:
    - Business invariants are violated
    - Operations not allowed in current state
    - Prerequisites not met
    - Business logic constraints failed

    Args:
        message: Human-readable error message
        rule: Name of the violated business rule
        entity: Entity/domain object involved
        **extra_details: Additional context fields

    Returns:
        Error with BUSINESS_RULE_VIOLATION code

    Example:
        >>> error = BusinessRuleError(
        ...     message="Cannot resolve conversation without agent response",
        ...     rule="ConversationResolutionRule",
        ...     entity="Conversation"
        ... )
        >>> error.code
        'BUSINESS_RULE_VIOLATION'
    """
    details = {**extra_details}

    if rule:
        details["rule"] = rule
    if entity:
        details["entity"] = entity

    return Error(
        code="BUSINESS_RULE_VIOLATION", message=message, details=details if details else None
    )


def NotFoundError(
    resource: str,
    identifier: str | None = None,
    search_criteria: dict | None = None,
    **extra_details,
) -> Error:
    """
    Create a resource not found error

    Use when:
    - Requested resource doesn't exist
    - Database query returns no results
    - Referenced entity not found

    Args:
        resource: Type of resource (e.g., "Customer", "Conversation")
        identifier: Resource identifier (ID, email, etc.)
        search_criteria: Criteria used to search (for complex lookups)
        **extra_details: Additional context fields

    Returns:
        Error with NOT_FOUND code

    Example:
        >>> error = NotFoundError(
        ...     resource="Customer",
        ...     identifier="user123"
        ... )
        >>> error.message
        'Customer not found'

        >>> # Complex search
        >>> error = NotFoundError(
        ...     resource="Conversation",
        ...     search_criteria={"customer_id": "123", "status": "active"}
        ... )
    """
    details = {**extra_details}
    details["resource"] = resource

    if identifier:
        details["identifier"] = identifier
    if search_criteria:
        details["search_criteria"] = search_criteria

    message = f"{resource} not found"
    if identifier:
        message += f": {identifier}"

    return Error(code="NOT_FOUND", message=message, details=details)


def ConflictError(
    message: str,
    resource: str | None = None,
    conflicting_id: str | None = None,
    constraint: str | None = None,
    **extra_details,
) -> Error:
    """
    Create a conflict error for duplicate or conflicting resources

    Use when:
    - Unique constraint violated
    - Resource already exists
    - Concurrent modification conflict
    - State conflict

    Args:
        message: Human-readable error message
        resource: Type of resource
        conflicting_id: ID of conflicting resource
        constraint: Constraint that was violated (unique_email, etc.)
        **extra_details: Additional context fields

    Returns:
        Error with CONFLICT code

    Example:
        >>> error = ConflictError(
        ...     message="Customer with this email already exists",
        ...     resource="Customer",
        ...     conflicting_id="user@example.com",
        ...     constraint="unique_email"
        ... )
        >>> error.code
        'CONFLICT'
    """
    details = {**extra_details}

    if resource:
        details["resource"] = resource
    if conflicting_id:
        details["conflicting_id"] = conflicting_id
    if constraint:
        details["constraint"] = constraint

    return Error(code="CONFLICT", message=message, details=details if details else None)


def AuthorizationError(
    message: str = "Permission denied",
    required_permission: str | None = None,
    resource: str | None = None,
    action: str | None = None,
    **extra_details,
) -> Error:
    """
    Create an authorization/permission error

    Use when:
    - User lacks required permissions
    - Action not allowed for current user
    - Resource access forbidden

    Args:
        message: Human-readable error message
        required_permission: Permission that was required
        resource: Resource being accessed
        action: Action being attempted
        **extra_details: Additional context fields

    Returns:
        Error with AUTHORIZATION_ERROR code

    Example:
        >>> error = AuthorizationError(
        ...     message="Cannot delete other users' conversations",
        ...     required_permission="delete:conversation",
        ...     resource="Conversation",
        ...     action="delete"
        ... )
        >>> error.code
        'AUTHORIZATION_ERROR'
    """
    details = {**extra_details}

    if required_permission:
        details["required_permission"] = required_permission
    if resource:
        details["resource"] = resource
    if action:
        details["action"] = action

    return Error(code="AUTHORIZATION_ERROR", message=message, details=details if details else None)


def RateLimitError(
    message: str = "Rate limit exceeded",
    limit: int | None = None,
    window_seconds: int | None = None,
    retry_after_seconds: int | None = None,
    **extra_details,
) -> Error:
    """
    Create a rate limit exceeded error

    Use when:
    - API rate limit exceeded
    - Too many requests in time window
    - Throttling applied

    Args:
        message: Human-readable error message
        limit: Maximum requests allowed
        window_seconds: Time window in seconds
        retry_after_seconds: Seconds to wait before retrying
        **extra_details: Additional context fields

    Returns:
        Error with RATE_LIMIT_EXCEEDED code

    Example:
        >>> error = RateLimitError(
        ...     message="Too many requests",
        ...     limit=100,
        ...     window_seconds=3600,
        ...     retry_after_seconds=300
        ... )
        >>> error.details['retry_after_seconds']
        300
    """
    details = {**extra_details}

    if limit is not None:
        details["limit"] = limit
    if window_seconds is not None:
        details["window_seconds"] = window_seconds
    if retry_after_seconds is not None:
        details["retry_after_seconds"] = retry_after_seconds

    return Error(code="RATE_LIMIT_EXCEEDED", message=message, details=details if details else None)


def InternalError(
    message: str = "An internal error occurred",
    operation: str | None = None,
    component: str | None = None,
    **extra_details,
) -> Error:
    """
    Create an internal error for unexpected failures

    Use when:
    - Unexpected exception occurred
    - System error (not user's fault)
    - Infrastructure failure
    - Database error

    Args:
        message: Human-readable error message (keep vague for security)
        operation: Operation that was being performed
        component: Component/service where error occurred
        **extra_details: Additional context fields (for logging only)

    Returns:
        Error with INTERNAL_ERROR code

    Example:
        >>> error = InternalError(
        ...     message="Failed to process request",
        ...     operation="create_customer",
        ...     component="CustomerService"
        ... )
        >>> error.code
        'INTERNAL_ERROR'

    Note:
        Keep error messages vague to avoid exposing internal details.
        Log full details server-side but don't expose to clients.
    """
    details = {**extra_details}

    if operation:
        details["operation"] = operation
    if component:
        details["component"] = component

    return Error(code="INTERNAL_ERROR", message=message, details=details if details else None)


def ExternalServiceError(
    message: str,
    service: str,
    operation: str | None = None,
    status_code: int | None = None,
    is_retryable: bool = False,
    **extra_details,
) -> Error:
    """
    Create an external service error

    Use when:
    - External API call failed
    - Third-party service unavailable
    - Integration error

    Args:
        message: Human-readable error message
        service: Name of external service (e.g., "Qdrant", "OpenAI")
        operation: Operation being performed
        status_code: HTTP status code (if applicable)
        is_retryable: Whether operation can be retried
        **extra_details: Additional context fields

    Returns:
        Error with EXTERNAL_SERVICE_ERROR code

    Example:
        >>> error = ExternalServiceError(
        ...     message="Vector search service unavailable",
        ...     service="Qdrant",
        ...     operation="search",
        ...     status_code=503,
        ...     is_retryable=True
        ... )
        >>> error.details['is_retryable']
        True
    """
    details = {**extra_details}
    details["service"] = service
    details["is_retryable"] = is_retryable

    if operation:
        details["operation"] = operation
    if status_code is not None:
        details["status_code"] = status_code

    return Error(code="EXTERNAL_SERVICE_ERROR", message=message, details=details)


# ===== Error Code Constants =====
# Useful for pattern matching and error handling


class ErrorCodes:
    """
    Error code constants for pattern matching

    Usage:
        >>> from core.errors import ErrorCodes
        >>>
        >>> if result.is_failure:
        ...     if result.error.code == ErrorCodes.NOT_FOUND:
        ...         handle_not_found(result.error)
        ...     elif result.error.code == ErrorCodes.VALIDATION_ERROR:
        ...         handle_validation(result.error)
    """

    VALIDATION_ERROR = "VALIDATION_ERROR"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


if __name__ == "__main__":
    # Self-test
    print("=" * 70)
    print("ENHANCED ERROR TYPES - SELF TEST")
    print("=" * 70)

    # Test ValidationError
    print("\n1. Testing ValidationError...")
    error = ValidationError(message="Email is required", field="email", constraint="required")
    assert error.code == "VALIDATION_ERROR"
    assert error.details["field"] == "email"
    print(f"   ✓ {error}")

    # Test BusinessRuleError
    print("\n2. Testing BusinessRuleError...")
    error = BusinessRuleError(
        message="Cannot resolve without agent response", rule="ConversationResolutionRule"
    )
    assert error.code == "BUSINESS_RULE_VIOLATION"
    print(f"   ✓ {error}")

    # Test NotFoundError
    print("\n3. Testing NotFoundError...")
    error = NotFoundError(resource="Customer", identifier="user123")
    assert error.code == "NOT_FOUND"
    assert error.message == "Customer not found: user123"
    print(f"   ✓ {error}")

    # Test ConflictError
    print("\n4. Testing ConflictError...")
    error = ConflictError(
        message="Email already exists", resource="Customer", conflicting_id="user@example.com"
    )
    assert error.code == "CONFLICT"
    print(f"   ✓ {error}")

    # Test AuthorizationError
    print("\n5. Testing AuthorizationError...")
    error = AuthorizationError(
        message="Permission denied", required_permission="delete:conversation"
    )
    assert error.code == "AUTHORIZATION_ERROR"
    print(f"   ✓ {error}")

    # Test RateLimitError
    print("\n6. Testing RateLimitError...")
    error = RateLimitError(message="Too many requests", limit=100, retry_after_seconds=60)
    assert error.code == "RATE_LIMIT_EXCEEDED"
    print(f"   ✓ {error}")

    # Test InternalError
    print("\n7. Testing InternalError...")
    error = InternalError(message="Database connection failed", component="CustomerRepository")
    assert error.code == "INTERNAL_ERROR"
    print(f"   ✓ {error}")

    # Test ExternalServiceError
    print("\n8. Testing ExternalServiceError...")
    error = ExternalServiceError(
        message="Vector search failed", service="Qdrant", is_retryable=True
    )
    assert error.code == "EXTERNAL_SERVICE_ERROR"
    assert error.details["is_retryable"] is True
    print(f"   ✓ {error}")

    # Test ErrorCodes constants
    print("\n9. Testing ErrorCodes constants...")
    assert ErrorCodes.VALIDATION_ERROR == "VALIDATION_ERROR"
    assert ErrorCodes.NOT_FOUND == "NOT_FOUND"
    print("   ✓ ErrorCodes working")

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)
