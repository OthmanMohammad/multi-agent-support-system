"""
Exception utilities - Context enrichment and handling for exceptions

This package provides utilities to enhance exception handling with:
- Automatic context enrichment (correlation_id, customer_id, etc.)
- Decorators for cleaner exception handling
- Integration with structured logging and Sentry

Features:
- Enrich exceptions with request context
- Extract context from enriched exceptions
- Decorators for automatic enrichment and logging
- Works with existing domain exceptions (doesn't replace them)

Quick Start:
    from src.utils.exceptions import enrich_exception, capture_exceptions
    
    # Enrich exception with context
    try:
        process_payment()
    except PaymentError as e:
        enriched = enrich_exception(e)
        logger.error("payment_failed", exception=enriched)
        raise
    
    # Or use decorator
    @capture_exceptions(log_errors=True, send_to_sentry=True)
    async def risky_operation():
        # Exceptions automatically enriched and logged
        await process()
"""

from src.utils.exceptions.enrichment import (
    enrich_exception,
    get_exception_context,
    EnrichedExceptionMixin,
)
from src.utils.exceptions.decorators import (
    capture_exceptions,
    handle_workflow_errors,
)
from src.utils.exceptions.context import (
    get_exception_correlation_id,
    get_exception_customer_id,
    get_exception_conversation_id,
    get_exception_agent_name,
)

__version__ = "1.0.0"

__all__ = [
    # Enrichment
    "enrich_exception",
    "get_exception_context",
    "EnrichedExceptionMixin",
    # Decorators
    "capture_exceptions",
    "handle_workflow_errors",
    # Context extraction
    "get_exception_correlation_id",
    "get_exception_customer_id",
    "get_exception_conversation_id",
    "get_exception_agent_name",
]