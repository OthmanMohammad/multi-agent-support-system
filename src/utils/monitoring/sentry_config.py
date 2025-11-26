"""
Sentry Configuration - Error tracking and performance monitoring

This module initializes Sentry with:
- FastAPI integration for automatic error capture
- SQLAlchemy integration for database query tracking
- Performance monitoring (configurable sampling)
- PII filtering via before_send hook
- Correlation ID injection from logging context
- Customer/conversation/agent context enrichment
- Centralized configuration management
"""

import re
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from src.core.config import get_settings

# Sensitive field patterns for PII masking
SENSITIVE_KEYS = {
    "password",
    "token",
    "api_key",
    "secret",
    "credit_card",
    "ssn",
    "social_security",
    "authorization",
    "auth",
    "cookie",
    "session",
    "access_token",
    "refresh_token",
}


def _should_mask_key(key: str) -> bool:
    """
    Check if key contains sensitive data that should be masked

    Args:
        key: Dictionary key name

    Returns:
        True if key should be masked
    """
    key_lower = key.lower()

    # Exact matches
    if key_lower in SENSITIVE_KEYS:
        return True

    # Partial matches (e.g., "user_password", "api_token")
    return any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)


def _mask_email(email: str) -> str:
    """
    Partially mask email address for PII protection

    Args:
        email: Email address

    Returns:
        Masked email (e.g., us***@example.com)
    """
    if "@" not in email:
        return "***@***"

    local, domain = email.split("@", 1)

    if len(local) <= 2:
        return f"***@{domain}"

    return f"{local[0]}{local[1]}***@{domain}"


def _mask_value(value: Any) -> str:
    """
    Mask sensitive value appropriately

    Args:
        value: Value to mask

    Returns:
        Masked value
    """
    if not isinstance(value, str):
        return "***MASKED***"

    # Email pattern
    if "@" in value and "." in value:
        return _mask_email(value)

    # Credit card pattern (13-19 digits)
    if re.match(r"^\d{13,19}$", value.replace(" ", "").replace("-", "")):
        return f"****{value[-4:]}"

    # Generic masking
    if len(value) <= 3:
        return "***MASKED***"

    return f"{value[0]}***{value[-1]}"


def _mask_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively mask sensitive data in dictionary

    Args:
        data: Dictionary to process

    Returns:
        Dictionary with sensitive data masked
    """
    if not isinstance(data, dict):
        return data

    masked = {}

    for key, value in data.items():
        if _should_mask_key(key):
            # Mask sensitive field
            masked[key] = _mask_value(value)
        elif isinstance(value, dict):
            # Recursively mask nested dicts
            masked[key] = _mask_dict(value)
        elif isinstance(value, list):
            # Process lists
            masked[key] = [_mask_dict(item) if isinstance(item, dict) else item for item in value]
        else:
            # Keep as-is
            masked[key] = value

    return masked


def before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Filter and enrich events before sending to Sentry

    This hook runs on every event before it's sent to Sentry.
    Use this to:
    1. Mask PII/sensitive data
    2. Add correlation IDs and context
    3. Filter out unwanted errors

    Args:
        event: Sentry event dict
        hint: Additional context about the event

    Returns:
        Modified event dict or None to drop the event
    """
    # Import here to avoid circular imports
    from utils.logging.context import (
        get_agent_name,
        get_conversation_id,
        get_correlation_id,
        get_customer_id,
    )

    # Add correlation ID as tag for easy filtering
    correlation_id = get_correlation_id()
    if correlation_id:
        event.setdefault("tags", {})["correlation_id"] = correlation_id

    # Add context from logging system
    context = event.setdefault("contexts", {}).setdefault("custom", {})

    if correlation_id:
        context["correlation_id"] = correlation_id

    conversation_id = get_conversation_id()
    if conversation_id:
        context["conversation_id"] = conversation_id

    customer_id = get_customer_id()
    if customer_id:
        context["customer_id"] = customer_id

    agent_name = get_agent_name()
    if agent_name:
        context["agent_name"] = agent_name

    # Mask PII in request data
    if "request" in event:
        request_data = event["request"]

        # Mask sensitive data in request body
        if "data" in request_data and isinstance(request_data["data"], dict):
            request_data["data"] = _mask_dict(request_data["data"])

        # Mask sensitive headers
        if "headers" in request_data:
            headers = request_data["headers"]
            if isinstance(headers, dict):
                for key in list(headers.keys()):
                    if _should_mask_key(key):
                        headers[key] = "***MASKED***"

        # Mask sensitive query parameters
        if "query_string" in request_data:
            # Query string masking would go here if needed
            pass

    # Mask PII in extra data
    if "extra" in event:
        event["extra"] = _mask_dict(event["extra"])

    # Mask PII in breadcrumbs
    if "breadcrumbs" in event:
        breadcrumbs = event["breadcrumbs"].get("values", [])
        for breadcrumb in breadcrumbs:
            if "data" in breadcrumb:
                breadcrumb["data"] = _mask_dict(breadcrumb["data"])

    return event


def init_sentry() -> None:
    """
    Initialize Sentry SDK using centralized configuration

    Call this once at application startup (in FastAPI startup event).
    If SENTRY_DSN is not set in config, Sentry will be disabled.

    Example:
        @app.on_event("startup")
        async def startup_event():
            init_sentry()
    """
    settings = get_settings()

    if not settings.sentry.dsn:
        print(
            f"⚠️  Sentry DSN not configured - Sentry monitoring disabled (environment: {settings.environment})"
        )
        return

    # Initialize Sentry with config
    sentry_sdk.init(
        dsn=settings.sentry.dsn,
        environment=settings.sentry.environment,
        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",  # Group by endpoint for better organization
            ),
            SqlalchemyIntegration(),
        ],
        # Performance monitoring
        traces_sample_rate=settings.sentry.traces_sample_rate,
        profiles_sample_rate=settings.sentry.profiles_sample_rate,
        # PII filtering and context enrichment
        before_send=before_send,
        # Error sampling (capture 100% of errors)
        sample_rate=1.0,
        # Don't send default PII (we'll add what we need in before_send)
        send_default_pii=settings.sentry.send_default_pii,
        # Attach stack traces to messages
        attach_stacktrace=settings.sentry.attach_stacktrace,
        # Enable distributed tracing
        enable_tracing=True,
        # Set release version
        release=settings.app_version,
        # Max breadcrumbs
        max_breadcrumbs=settings.sentry.max_breadcrumbs,
    )

    print(
        f"✓ Sentry initialized "
        f"(environment: {settings.sentry.environment}, "
        f"traces: {settings.sentry.traces_sample_rate * 100}%, "
        f"profiles: {settings.sentry.profiles_sample_rate * 100}%)"
    )


def capture_exception(error: Exception, **context: Any) -> None:
    """
    Manually capture an exception with additional context

    Use this to capture handled exceptions that you want tracked in Sentry.
    Unhandled exceptions are captured automatically.

    Args:
        error: Exception to capture
        **context: Additional context to attach (customer_id, conversation_id, etc.)

    Example:
        try:
            process_payment(customer_id, amount)
        except PaymentError as e:
            capture_exception(
                e,
                customer_id=customer.id,
                amount=amount,
                payment_method="credit_card"
            )
            # Handle the error...
    """
    # Import here to avoid circular imports
    from src.utils.logging.context import get_correlation_id

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in context.items():
            # Mask sensitive values
            if _should_mask_key(key):
                scope.set_context(key, {"value": _mask_value(str(value))})
            else:
                scope.set_context(key, {"value": str(value)})

        # Add correlation ID
        correlation_id = get_correlation_id()
        if correlation_id:
            scope.set_tag("correlation_id", correlation_id)

        # Capture the exception
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **context: Any) -> None:
    """
    Capture a custom message in Sentry

    Use this for important events that aren't errors but should be tracked.

    Args:
        message: Message to log
        level: Severity level ('debug', 'info', 'warning', 'error', 'fatal')
        **context: Additional context

    Example:
        capture_message(
            "High error rate detected",
            level="warning",
            error_rate=0.15,
            endpoint="/api/conversations"
        )
    """
    # Import here to avoid circular imports
    from src.utils.logging.context import get_correlation_id

    with sentry_sdk.push_scope() as scope:
        # Add custom context
        for key, value in context.items():
            if _should_mask_key(key):
                scope.set_context(key, {"value": _mask_value(str(value))})
            else:
                scope.set_context(key, {"value": str(value)})

        # Add correlation ID
        correlation_id = get_correlation_id()
        if correlation_id:
            scope.set_tag("correlation_id", correlation_id)

        # Capture the message
        sentry_sdk.capture_message(message, level=level)


# Self-test when run directly
if __name__ == "__main__":
    print("=" * 70)
    print("SENTRY CONFIGURATION - SELF TEST")
    print("=" * 70)

    # Test PII masking
    print("\n1. Testing PII masking...")

    test_data = {
        "email": "user@example.com",
        "password": "secret123",
        "amount": 100.00,
        "nested": {"api_key": "sk_live_abcdef123456", "name": "John Doe"},
    }

    masked = _mask_dict(test_data)

    assert masked["email"] == "us***@example.com"
    assert masked["password"] == "***MASKED***"
    assert masked["amount"] == 100.00  # Not sensitive
    assert masked["nested"]["api_key"] == "***MASKED***"
    assert masked["nested"]["name"] == "John Doe"  # Not sensitive

    print("   ✓ PII masking works correctly")

    # Test email masking
    print("\n2. Testing email masking...")
    assert _mask_email("user@example.com") == "us***@example.com"
    assert _mask_email("a@example.com") == "***@example.com"
    print("   ✓ Email masking works")

    # Test sensitive key detection
    print("\n3. Testing sensitive key detection...")
    assert _should_mask_key("password")
    assert _should_mask_key("user_password")
    assert _should_mask_key("API_KEY")
    assert not _should_mask_key("username")
    assert not _should_mask_key("email")  # email is not in SENSITIVE_KEYS
    print("   ✓ Sensitive key detection works")

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)
    print("\nNOTE: To fully test Sentry integration:")
    print("1. Configure Sentry in .env file")
    print(
        "2. Run: python -c 'from utils.monitoring.sentry_config import init_sentry; init_sentry()'"
    )
    print("3. Check Sentry dashboard for initialization event")
