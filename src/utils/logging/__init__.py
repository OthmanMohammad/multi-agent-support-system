"""
Logging infrastructure - Structured logging with correlation IDs

This package provides production-grade structured logging using structlog.

Features:
- JSON output for production, pretty console for development
- Correlation ID tracking across async operations
- Automatic PII masking for compliance
- Context propagation through agent workflows
- Integration with FastAPI

Quick Start:
    from src.utils.logging import setup_logging, get_logger
    
    # Initialize once at startup
    setup_logging()
    
    # Get logger in any module
    logger = get_logger(__name__)
    
    # Log with structured data
    logger.info(
        "conversation_created",
        conversation_id=conv_id,
        customer_id=cust_id
    )

With Context:
    from src.utils.logging import correlation_context
    
    with correlation_context():
        logger.info("processing_request")
        await process()
        logger.info("request_complete")
        # Both logs will have same correlation_id
"""

from src.utils.logging.setup import setup_logging, get_logger
from src.utils.logging.context import (
    correlation_context,
    conversation_context,
    agent_context,
    log_context,
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    get_or_create_correlation_id,
)
from src.utils.logging.decorators import (
    log_execution,
    log_errors,
    log_result,
)

__version__ = "1.0.0"

__all__ = [
    # Setup
    "setup_logging",
    "get_logger",
    # Context managers
    "correlation_context",
    "conversation_context",
    "agent_context",
    "log_context",
    # Context utilities
    "get_correlation_id",
    "set_correlation_id",
    "generate_correlation_id",
    "get_or_create_correlation_id",
    # Decorators
    "log_execution",
    "log_errors",
    "log_result",
]