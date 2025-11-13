"""
Configuration validation on application startup.

Validates configuration and fails fast with clear errors.
"""

from typing import List, Tuple
from src.core.config import get_settings
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)


class ConfigurationError(Exception):
    """Configuration validation error"""
    pass


def validate_configuration() -> Tuple[bool, List[str]]:
    """
    Validate application configuration.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    try:
        settings = get_settings()
    except Exception as e:
        errors.append(f"Failed to load configuration: {e}")
        return False, errors

    # Validate environment
    if settings.environment not in ["staging", "production"]:
        errors.append(
            f"Invalid environment '{settings.environment}'. "
            f"Must be 'staging' or 'production'"
        )

    # Validate CORS
    if not settings.api.cors_origins:
        errors.append("No CORS origins configured")

    # Validate database
    db_url = str(settings.database.url)
    if "localhost" in db_url and settings.is_production():
        errors.append(
            "SECURITY: localhost database URL detected in production"
        )

    if "example.com" in db_url:
        errors.append(
            "Database URL contains example.com - update with real database"
        )

    # Validate Anthropic API
    if "your" in settings.anthropic.api_key.lower():
        errors.append("Anthropic API key not configured (still has placeholder)")

    # Validate Qdrant
    if "your" in settings.qdrant.url.lower():
        errors.append("Qdrant URL not configured (still has placeholder)")

    # Production-specific validation
    if settings.is_production():
        if not settings.sentry.dsn:
            errors.append("PRODUCTION: Sentry DSN not configured")

        if settings.debug:
            errors.append("PRODUCTION: Debug mode must be disabled")

        if settings.logging.level == "DEBUG":
            errors.append("PRODUCTION: Log level should not be DEBUG")

        if settings.logging.format != "json":
            errors.append("PRODUCTION: Log format should be 'json'")

    # Log validation results
    if errors:
        logger.error(
            "configuration_validation_failed",
            error_count=len(errors),
            errors=errors
        )
    else:
        logger.info(
            "configuration_validation_passed",
            environment=settings.environment
        )

    return len(errors) == 0, errors


def require_valid_configuration():
    """
    Require valid configuration or exit application.

    Call this during application startup to fail fast.
    
    Raises:
        SystemExit: If configuration is invalid
    """
    is_valid, errors = validate_configuration()

    if not is_valid:
        logger.critical(
            "configuration_validation_failed_startup_aborted",
            errors=errors
        )

        print("\n" + "=" * 70)
        print("CONFIGURATION VALIDATION FAILED")
        print("=" * 70)
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print("=" * 70)
        print("\nFix configuration errors and restart application.")
        print("See .env.template for configuration reference.\n")

        raise SystemExit(1)

    logger.info(
        "configuration_validated",
        environment=get_settings().environment
    )