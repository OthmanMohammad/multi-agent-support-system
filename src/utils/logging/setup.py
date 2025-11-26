"""
Logging Setup - Initialize structured logging with structlog

This module configures structlog with production-ready processors
for JSON output, PII masking, and correlation ID injection.
Uses centralized configuration management.

Environment Variables (via config):
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT: Output format (json or pretty)
    ENVIRONMENT: Environment name (staging or production)
"""

import logging
import sys
from typing import Any

import structlog

from src.core.config import get_settings


def add_correlation_id(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Processor to inject correlation ID into logs

    Gets correlation ID from context (set by middleware or context manager)
    and adds it to every log entry.
    """
    from src.utils.logging.context import get_correlation_id

    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id

    return event_dict


def setup_logging() -> None:
    """
    Initialize structured logging with structlog

    Configures different output formats based on LOG_FORMAT setting:
    - json: JSON output for production parsing
    - pretty: Pretty console output with colors for debugging

    Call this once at application startup.

    Example:
        from utils.logging import setup_logging

        setup_logging()
    """
    # Get configuration from centralized settings
    settings = get_settings()

    log_level = settings.logging.level
    log_format = settings.logging.format
    environment = settings.environment

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level, logging.INFO),
    )

    # Shared processors for all formats
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        add_correlation_id,
        structlog.processors.StackInfoRenderer(),
    ]

    # Format-specific processors
    if log_format == "json":
        # Production/Staging: JSON output
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty format: Console output with colors
        processors = [*shared_processors, structlog.dev.ConsoleRenderer()]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Log startup
    logger = get_logger(__name__)
    logger.info(
        "logging_initialized",
        log_level=log_level,
        log_format=log_format,
        environment=environment,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("operation_complete", status="success", duration_ms=42)
    """
    return structlog.get_logger(name)
