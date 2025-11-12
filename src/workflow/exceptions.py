"""
Workflow Exceptions - Custom exceptions for agent workflow errors

Provides specific exception types for different failure modes in the
workflow engine, with context and recovery hints.

Phase 4 Enhancement: Added comprehensive docstrings and better error context
for integration with exception enrichment and Sentry tracking.
"""
from typing import Optional, Dict, Any


class WorkflowException(Exception):
    """
    Base exception for all workflow-related errors
    
    All workflow exceptions inherit from this, making it easy
    to catch any workflow error with a single except clause.
    
    Phase 4 Enhancement: This exception supports automatic context enrichment.
    When caught by error handlers, it will include:
    - correlation_id: Request tracking ID
    - conversation_id: Conversation UUID  
    - customer_id: Customer identifier
    - agent_name: Current agent executing
    
    These attributes are added automatically by the enrichment system,
    making debugging much easier.
    
    Example:
        try:
            await workflow.execute(message)
        except WorkflowException as e:
            # Exception is automatically enriched with context
            # e.correlation_id, e.customer_id, etc. are available
            logger.error("workflow_failed", exception=e)
    """
    
    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        recovery_hint: Optional[str] = None
    ):
        """
        Initialize workflow exception
        
        Args:
            message: Error message
            context: Additional context about the error
            recovery_hint: Suggestion for how to recover
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.recovery_hint = recovery_hint
    
    def __str__(self) -> str:
        """String representation with context"""
        parts = [self.message]
        
        if self.context:
            parts.append(f"Context: {self.context}")
        
        if self.recovery_hint:
            parts.append(f"Recovery: {self.recovery_hint}")
        
        return " | ".join(parts)


class AgentExecutionError(WorkflowException):
    """
    Raised when an agent fails to execute properly
    
    This can happen due to:
    - LLM API errors
    - Agent logic errors
    - Invalid agent responses
    - Unexpected exceptions in agent code
    
    Phase 4 Enhancement: Includes agent_name in context for better debugging.
    When enriched, this exception will also include correlation_id, customer_id,
    and conversation_id from the request context.
    
    Example:
        try:
            result = await billing_agent.execute(state)
        except Exception as e:
            raise AgentExecutionError(
                "Billing agent failed to process request",
                agent_name="billing",
                original_error=e
            )
    """
    
    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        if agent_name:
            ctx["agent_name"] = agent_name
        if original_error:
            ctx["original_error"] = str(original_error)
            ctx["error_type"] = type(original_error).__name__
        
        super().__init__(
            message=message,
            context=ctx,
            recovery_hint="Check agent logs and retry. If persistent, escalate to human."
        )
        self.agent_name = agent_name
        self.original_error = original_error


class AgentTimeoutError(WorkflowException):
    """
    Raised when workflow execution exceeds timeout
    
    This prevents workflows from hanging indefinitely.
    Can be caused by:
    - Slow LLM responses
    - Network issues
    - Infinite loops in agent logic
    
    Phase 4 Enhancement: Includes timeout_seconds in context.
    When enriched, helps identify which specific request/customer
    experienced the timeout via correlation_id and customer_id.
    
    Example:
        try:
            result = await asyncio.wait_for(
                workflow.execute(state),
                timeout=30
            )
        except asyncio.TimeoutError:
            raise AgentTimeoutError(
                "Workflow exceeded 30 second timeout",
                timeout_seconds=30
            )
    """
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        if timeout_seconds:
            ctx["timeout_seconds"] = timeout_seconds
        
        super().__init__(
            message=message,
            context=ctx,
            recovery_hint="Increase timeout or optimize agent logic. Check for infinite loops."
        )
        self.timeout_seconds = timeout_seconds


class InvalidStateError(WorkflowException):
    """
    Raised when agent state is invalid or malformed
    
    This indicates a problem with:
    - State structure
    - Missing required fields
    - Invalid field values
    - State transition violations
    
    Phase 4 Enhancement: Includes field-level details for precise debugging.
    When enriched with correlation_id, makes it easy to trace which specific
    request caused the invalid state.
    
    Example:
        if state.get("confidence") > 1.0:
            raise InvalidStateError(
                "Confidence score exceeds valid range",
                invalid_field="confidence",
                expected_value="0.0-1.0",
                actual_value=state["confidence"]
            )
    """
    
    def __init__(
        self,
        message: str,
        invalid_field: Optional[str] = None,
        expected_value: Optional[Any] = None,
        actual_value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        if invalid_field:
            ctx["invalid_field"] = invalid_field
        if expected_value is not None:
            ctx["expected_value"] = expected_value
        if actual_value is not None:
            ctx["actual_value"] = actual_value
        
        super().__init__(
            message=message,
            context=ctx,
            recovery_hint="Validate state structure and fix invalid fields."
        )
        self.invalid_field = invalid_field


class RoutingError(WorkflowException):
    """
    Raised when agent routing fails
    
    This can happen when:
    - Invalid next_agent specified
    - Circular routing detected
    - Max turns exceeded
    - Unknown agent type
    
    Phase 4 Enhancement: Includes agent_history to track routing path.
    When enriched, correlation_id helps trace the entire request flow
    that led to the routing failure.
    
    Example:
        if next_agent not in VALID_AGENTS:
            raise RoutingError(
                f"Invalid agent type: {next_agent}",
                current_agent="router",
                next_agent=next_agent,
                agent_history=state["agent_history"]
            )
    """
    
    def __init__(
        self,
        message: str,
        current_agent: Optional[str] = None,
        next_agent: Optional[str] = None,
        agent_history: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        ctx = context or {}
        if current_agent:
            ctx["current_agent"] = current_agent
        if next_agent:
            ctx["next_agent"] = next_agent
        if agent_history:
            ctx["agent_history"] = agent_history
            ctx["turn_count"] = len(agent_history)
        
        super().__init__(
            message=message,
            context=ctx,
            recovery_hint="Check routing logic and max_turns limit. Prevent circular routing."
        )
        self.current_agent = current_agent
        self.next_agent = next_agent