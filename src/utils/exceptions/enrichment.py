"""
Exception Enrichment - Add context to exceptions automatically

This module provides utilities to enrich exceptions with contextual information
from the logging context (correlation IDs, customer IDs, etc.) to make debugging
easier and provide better context in Sentry.

The enrichment is non-invasive - it adds attributes to existing exception objects
without changing their behavior or requiring special exception classes.
"""

from typing import Dict, Any, Optional

from utils.logging.context import (
    get_correlation_id,
    get_conversation_id,
    get_customer_id,
    get_agent_name,
)
from utils.logging.setup import get_logger

logger = get_logger(__name__)


def enrich_exception(exc: Exception) -> Exception:
    """
    Enrich exception with current context from logging
    
    Adds context as attributes to the exception object:
    - exc.correlation_id: Request tracking ID
    - exc.conversation_id: Conversation UUID
    - exc.customer_id: Customer identifier
    - exc.agent_name: Current agent executing
    
    This is non-invasive - works with any exception type without
    requiring special base classes.
    
    Args:
        exc: Exception to enrich
    
    Returns:
        Same exception instance (mutated with context attributes)
    
    Example:
        try:
            await risky_operation()
        except ValueError as e:
            enriched = enrich_exception(e)
            # enriched now has correlation_id, customer_id, etc.
            logger.error("operation_failed", exception=enriched)
            raise enriched
    """
    # Get context from logging contextvars
    correlation_id = get_correlation_id()
    conversation_id = get_conversation_id()
    customer_id = get_customer_id()
    agent_name = get_agent_name()
    
    # Add as attributes (if available)
    if correlation_id:
        exc.correlation_id = correlation_id
    
    if conversation_id:
        exc.conversation_id = conversation_id
    
    if customer_id:
        exc.customer_id = customer_id
    
    if agent_name:
        exc.agent_name = agent_name
    
    # Track that we've enriched this exception
    exc._enriched = True
    
    logger.debug(
        "exception_enriched",
        error_type=type(exc).__name__,
        correlation_id=correlation_id,
        has_conversation=conversation_id is not None,
        has_customer=customer_id is not None,
    )
    
    return exc


def get_exception_context(exc: Exception) -> Dict[str, Any]:
    """
    Extract context from enriched exception
    
    Returns all context attributes that were added by enrich_exception().
    Useful for logging or sending to Sentry.
    
    Args:
        exc: Exception (enriched or not)
    
    Returns:
        Dictionary of context attributes
    
    Example:
        try:
            await operation()
        except Exception as e:
            context = get_exception_context(e)
            logger.error("operation_failed", **context)
    """
    context = {}
    
    # Extract context attributes if present
    if hasattr(exc, 'correlation_id'):
        context['correlation_id'] = exc.correlation_id
    
    if hasattr(exc, 'conversation_id'):
        context['conversation_id'] = exc.conversation_id
    
    if hasattr(exc, 'customer_id'):
        context['customer_id'] = exc.customer_id
    
    if hasattr(exc, 'agent_name'):
        context['agent_name'] = exc.agent_name
    
    # Add exception type and message
    context['error_type'] = type(exc).__name__
    context['error_message'] = str(exc)
    
    # Track if enriched
    context['is_enriched'] = getattr(exc, '_enriched', False)
    
    return context


def is_enriched(exc: Exception) -> bool:
    """
    Check if exception has been enriched with context
    
    Args:
        exc: Exception to check
    
    Returns:
        True if exception has been enriched
    """
    return getattr(exc, '_enriched', False)


def enrich_and_log(exc: Exception, message: str = "exception_occurred") -> Exception:
    """
    Enrich exception and log it in one step
    
    Convenience function that enriches the exception with context
    and logs it with structured logging.
    
    Args:
        exc: Exception to enrich and log
        message: Log message (event name)
    
    Returns:
        Enriched exception
    
    Example:
        try:
            await risky_operation()
        except ValueError as e:
            enriched = enrich_and_log(e, "risky_operation_failed")
            raise enriched
    """
    # Enrich exception
    enriched = enrich_exception(exc)
    
    # Extract context
    context = get_exception_context(enriched)
    
    # Log with context
    logger.error(
        message,
        **context,
        exc_info=True
    )
    
    return enriched