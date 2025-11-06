"""
Workflow Exceptions - Custom exceptions for agent workflow errors

Provides specific exception types for different failure modes in the
workflow engine, with context and recovery hints.
"""
from typing import Optional, Dict, Any


class WorkflowException(Exception):
    """
    Base exception for all workflow-related errors
    
    All workflow exceptions inherit from this, making it easy
    to catch any workflow error with a single except clause.
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


if __name__ == "__main__":
    # Test exceptions
    print("Testing Workflow Exceptions...")
    print("=" * 60)
    
    # Test base exception
    try:
        raise WorkflowException(
            "Test error",
            context={"key": "value"},
            recovery_hint="Do this to fix"
        )
    except WorkflowException as e:
        print(f"✓ WorkflowException: {e}")
    
    # Test agent execution error
    try:
        raise AgentExecutionError(
            "Agent failed",
            agent_name="billing",
            original_error=ValueError("Invalid input")
        )
    except AgentExecutionError as e:
        print(f"✓ AgentExecutionError: {e}")
    
    # Test timeout error
    try:
        raise AgentTimeoutError(
            "Workflow timed out",
            timeout_seconds=30
        )
    except AgentTimeoutError as e:
        print(f"✓ AgentTimeoutError: {e}")
    
    # Test invalid state error
    try:
        raise InvalidStateError(
            "Invalid confidence value",
            invalid_field="confidence",
            expected_value="0.0-1.0",
            actual_value=2.5
        )
    except InvalidStateError as e:
        print(f"✓ InvalidStateError: {e}")
    
    # Test routing error
    try:
        raise RoutingError(
            "Circular routing detected",
            current_agent="billing",
            next_agent="billing",
            agent_history=["router", "billing", "billing"]
        )
    except RoutingError as e:
        print(f"✓ RoutingError: {e}")
    
    print("\n✓ All exceptions working correctly!")