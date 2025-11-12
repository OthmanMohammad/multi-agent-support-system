"""
Logging Context - Correlation IDs and context propagation

This module provides async-safe context management using contextvars
for tracking correlation IDs and other contextual information across
async operations.

Context variables are thread-safe and async-safe, making them perfect
for FastAPI applications with async handlers.
"""

import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar
from contextlib import contextmanager

# Context variables for async-safe storage
_correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", 
    default=None
)
_conversation_id_var: ContextVar[Optional[str]] = ContextVar(
    "conversation_id",
    default=None
)
_customer_id_var: ContextVar[Optional[str]] = ContextVar(
    "customer_id",
    default=None
)
_agent_name_var: ContextVar[Optional[str]] = ContextVar(
    "agent_name",
    default=None
)


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID
    
    Returns:
        UUID string for correlation tracking
    """
    return str(uuid.uuid4())


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID from context
    
    Returns:
        Correlation ID or None if not set
    """
    return _correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID in context
    
    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_id_var.set(correlation_id)


def get_or_create_correlation_id() -> str:
    """
    Get existing correlation ID or create new one
    
    Returns:
        Correlation ID (existing or newly created)
    """
    correlation_id = get_correlation_id()
    if not correlation_id:
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
    return correlation_id


@contextmanager
def correlation_context(correlation_id: Optional[str] = None):
    """
    Context manager for correlation ID tracking
    
    Automatically generates correlation ID if not provided.
    Cleans up on exit.
    
    Args:
        correlation_id: Optional correlation ID (generates if None)
    
    Yields:
        Correlation ID
    
    Example:
        with correlation_context() as corr_id:
            logger.info("request_start")
            await process()
            logger.info("request_end")
            # Both logs will have same correlation_id
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    
    # Store previous value
    token = _correlation_id_var.set(correlation_id)
    
    try:
        yield correlation_id
    finally:
        # Restore previous value
        _correlation_id_var.reset(token)


@contextmanager
def conversation_context(conversation_id: str, customer_id: str = None):
    """
    Context manager for conversation context
    
    Sets conversation and customer IDs for logging context.
    
    Args:
        conversation_id: Conversation UUID
        customer_id: Customer UUID (optional)
    
    Yields:
        Conversation ID
    
    Example:
        with conversation_context(conv_id, cust_id):
            logger.info("message_received", message=msg)
            # Log includes conversation_id and customer_id
    """
    # Store previous values
    conv_token = _conversation_id_var.set(conversation_id)
    cust_token = _customer_id_var.set(customer_id) if customer_id else None
    
    try:
        yield conversation_id
    finally:
        # Restore previous values
        _conversation_id_var.reset(conv_token)
        if cust_token:
            _customer_id_var.reset(cust_token)


@contextmanager
def agent_context(agent_name: str):
    """
    Context manager for agent context
    
    Sets current agent name for logging context.
    
    Args:
        agent_name: Agent name (router, billing, technical, etc.)
    
    Yields:
        Agent name
    
    Example:
        with agent_context("billing"):
            logger.info("agent_execution_start")
            result = await agent.execute(message)
            logger.info("agent_execution_complete")
    """
    token = _agent_name_var.set(agent_name)
    
    try:
        yield agent_name
    finally:
        _agent_name_var.reset(token)


@contextmanager
def log_context(**kwargs):
    """
    Generic context manager for arbitrary context data
    
    Sets multiple context variables at once.
    Currently supports: correlation_id, conversation_id, customer_id, agent_name
    
    Args:
        **kwargs: Context key-value pairs
    
    Yields:
        None
    
    Example:
        with log_context(
            correlation_id=corr_id,
            conversation_id=conv_id,
            agent_name="router"
        ):
            logger.info("processing")
    """
    tokens = []
    
    # Set all provided context variables
    if "correlation_id" in kwargs:
        tokens.append(("correlation_id", _correlation_id_var.set(kwargs["correlation_id"])))
    
    if "conversation_id" in kwargs:
        tokens.append(("conversation_id", _conversation_id_var.set(kwargs["conversation_id"])))
    
    if "customer_id" in kwargs:
        tokens.append(("customer_id", _customer_id_var.set(kwargs["customer_id"])))
    
    if "agent_name" in kwargs:
        tokens.append(("agent_name", _agent_name_var.set(kwargs["agent_name"])))
    
    try:
        yield
    finally:
        # Restore all previous values
        for name, token in tokens:
            if name == "correlation_id":
                _correlation_id_var.reset(token)
            elif name == "conversation_id":
                _conversation_id_var.reset(token)
            elif name == "customer_id":
                _customer_id_var.reset(token)
            elif name == "agent_name":
                _agent_name_var.reset(token)


# Context getters for use in processors
def get_conversation_id() -> Optional[str]:
    """Get current conversation ID"""
    return _conversation_id_var.get()


def get_customer_id() -> Optional[str]:
    """Get current customer ID"""
    return _customer_id_var.get()


def get_agent_name() -> Optional[str]:
    """Get current agent name"""
    return _agent_name_var.get()