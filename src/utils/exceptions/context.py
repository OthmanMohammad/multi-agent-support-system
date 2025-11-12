"""
Exception Context Utilities - Helper functions for exception context

Provides utilities to extract specific context attributes from
enriched exceptions for logging, debugging, and Sentry.
"""

from typing import Optional


def get_exception_correlation_id(exc: Exception) -> Optional[str]:
    """
    Get correlation ID from enriched exception
    
    Args:
        exc: Exception (enriched or not)
    
    Returns:
        Correlation ID or None
    
    Example:
        try:
            await operation()
        except Exception as e:
            corr_id = get_exception_correlation_id(e)
            if corr_id:
                print(f"Failed with correlation ID: {corr_id}")
    """
    return getattr(exc, "correlation_id", None)


def get_exception_customer_id(exc: Exception) -> Optional[str]:
    """
    Get customer ID from enriched exception
    
    Args:
        exc: Exception (enriched or not)
    
    Returns:
        Customer ID or None
    """
    return getattr(exc, "customer_id", None)


def get_exception_conversation_id(exc: Exception) -> Optional[str]:
    """
    Get conversation ID from enriched exception
    
    Args:
        exc: Exception (enriched or not)
    
    Returns:
        Conversation ID or None
    """
    return getattr(exc, "conversation_id", None)


def get_exception_agent_name(exc: Exception) -> Optional[str]:
    """
    Get agent name from enriched exception
    
    Args:
        exc: Exception (enriched or not)
    
    Returns:
        Agent name or None
    """
    return getattr(exc, "agent_name", None)


def has_context(exc: Exception) -> bool:
    """
    Check if exception has any context attributes
    
    Args:
        exc: Exception to check
    
    Returns:
        True if exception has at least one context attribute
    """
    return any([
        hasattr(exc, "correlation_id"),
        hasattr(exc, "customer_id"),
        hasattr(exc, "conversation_id"),
        hasattr(exc, "agent_name"),
    ])


def format_exception_context(exc: Exception) -> str:
    """
    Format exception context as human-readable string
    
    Args:
        exc: Exception (enriched or not)
    
    Returns:
        Formatted string with context
    
    Example:
        try:
            await operation()
        except Exception as e:
            print(format_exception_context(e))
            # Output: "correlation_id=abc123, customer_id=user456"
    """
    parts = []
    
    if corr_id := get_exception_correlation_id(exc):
        parts.append(f"correlation_id={corr_id}")
    
    if cust_id := get_exception_customer_id(exc):
        parts.append(f"customer_id={cust_id}")
    
    if conv_id := get_exception_conversation_id(exc):
        parts.append(f"conversation_id={conv_id}")
    
    if agent := get_exception_agent_name(exc):
        parts.append(f"agent={agent}")
    
    return ", ".join(parts) if parts else "no context"