"""
Exception Enrichment - Add context to exceptions automatically

This module provides utilities to enrich exceptions with contextual information
from the logging context (correlation IDs, customer IDs, etc.) to make debugging
easier and provide better context in Sentry.

The enrichment is non-invasive - it adds attributes to existing exception objects
without changing their behavior or requiring special exception classes.
"""

from typing import Any

from src.utils.logging.context import (
    get_agent_name,
    get_conversation_id,
    get_correlation_id,
    get_customer_id,
)
from src.utils.logging.setup import get_logger

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


def get_exception_context(exc: Exception) -> dict[str, Any]:
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
            # context = {"correlation_id": "...", "customer_id": "..."}
            logger.error("operation_failed", **context)
    """
    context = {}

    # Extract enriched attributes
    if hasattr(exc, "correlation_id"):
        context["correlation_id"] = exc.correlation_id

    if hasattr(exc, "conversation_id"):
        context["conversation_id"] = exc.conversation_id

    if hasattr(exc, "customer_id"):
        context["customer_id"] = exc.customer_id

    if hasattr(exc, "agent_name"):
        context["agent_name"] = exc.agent_name

    # Add exception details
    context["error_type"] = type(exc).__name__
    context["error_message"] = str(exc)

    # Check if enriched
    context["was_enriched"] = getattr(exc, "_enriched", False)

    return context


def is_enriched(exc: Exception) -> bool:
    """
    Check if exception has been enriched

    Args:
        exc: Exception to check

    Returns:
        True if exception has been enriched with context
    """
    return getattr(exc, "_enriched", False)


class EnrichedExceptionMixin:
    """
    Mixin for custom exceptions to support enrichment

    Use this mixin if you want to create custom exception classes
    that explicitly support enrichment and provide helper methods.

    This is OPTIONAL - enrich_exception() works with any exception.
    This mixin just provides convenience methods.

    Example:
        class CustomError(EnrichedExceptionMixin, Exception):
            '''Custom error with enrichment support'''
            pass

        try:
            raise CustomError("Something went wrong")
        except CustomError as e:
            e.enrich()  # Uses mixin method
            logger.error("error", **e.get_context())
    """

    def enrich(self) -> "EnrichedExceptionMixin":
        """
        Enrich this exception with current context

        Returns:
            Self (for chaining)
        """
        enrich_exception(self)
        return self

    def get_context(self) -> dict[str, Any]:
        """
        Get context from this exception

        Returns:
            Dictionary of context attributes
        """
        return get_exception_context(self)

    def is_enriched(self) -> bool:
        """
        Check if this exception is enriched

        Returns:
            True if enriched
        """
        return is_enriched(self)

    @property
    def correlation_id(self) -> str | None:
        """Get correlation ID if available"""
        return getattr(self, "_correlation_id", None)

    @correlation_id.setter
    def correlation_id(self, value: str):
        """Set correlation ID"""
        self._correlation_id = value

    @property
    def conversation_id(self) -> str | None:
        """Get conversation ID if available"""
        return getattr(self, "_conversation_id", None)

    @conversation_id.setter
    def conversation_id(self, value: str):
        """Set conversation ID"""
        self._conversation_id = value

    @property
    def customer_id(self) -> str | None:
        """Get customer ID if available"""
        return getattr(self, "_customer_id", None)

    @customer_id.setter
    def customer_id(self, value: str):
        """Set customer ID"""
        self._customer_id = value

    @property
    def agent_name(self) -> str | None:
        """Get agent name if available"""
        return getattr(self, "_agent_name", None)

    @agent_name.setter
    def agent_name(self, value: str):
        """Set agent name"""
        self._agent_name = value
