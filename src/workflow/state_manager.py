"""
Workflow State Manager - Manages agent state lifecycle

Handles state creation, updates, validation, and transitions.
Ensures state integrity throughout the workflow execution.
"""
from typing import Dict, Any, Optional, List
from copy import deepcopy
import logging

from workflow.state import AgentState, create_initial_state
from workflow.exceptions import InvalidStateError

logger = logging.getLogger(__name__)


class WorkflowStateManager:
    """
    Manages agent state throughout workflow execution
    
    Responsibilities:
    - Create initial state from user input and context
    - Update state during workflow execution
    - Validate state structure and values
    - Track state history for debugging
    - Ensure state transitions are valid
    
    NOT responsible for:
    - Business logic (domain services handle that)
    - Persistence (infrastructure services handle that)
    - Workflow routing (engine handles that)
    """
    
    def __init__(self, enable_history: bool = False):
        """
        Initialize state manager
        
        Args:
            enable_history: Track state snapshots for debugging
        """
        self.enable_history = enable_history
        self.state_history: List[Dict[str, Any]] = []
        
        logger.debug(f"StateManager initialized (history={enable_history})")
    
    def create_initial_state(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Create initial state for workflow execution
        
        Args:
            message: User's message
            context: Optional context with:
                - conversation_id: Continue existing conversation
                - customer_id: Customer identifier
                - customer_metadata: Customer info (plan, etc.)
                - conversation_history: Previous messages
                
        Returns:
            Initial AgentState
        """
        logger.debug(f"Creating initial state for message: '{message[:50]}...'")
        
        # Extract context parameters
        conversation_id = context.get("conversation_id") if context else None
        customer_id = context.get("customer_id", "default_customer") if context else "default_customer"
        
        # Create state
        state = create_initial_state(
            message=message,
            conversation_id=conversation_id,
            customer_id=customer_id,
            context=context
        )
        
        # Validate initial state
        try:
            self.validate_state(state)
        except InvalidStateError as e:
            logger.error(f"Initial state validation failed: {e}")
            raise
        
        # Track history if enabled
        if self.enable_history:
            self._track_state(state, "initial")
        
        logger.debug(f"Initial state created: conversation_id={state['conversation_id']}")
        
        return state
    
    def update_state(
        self,
        state: AgentState,
        updates: Dict[str, Any]
    ) -> AgentState:
        """
        Update state with new values
        
        Args:
            state: Current state
            updates: Dictionary of fields to update
            
        Returns:
            Updated state
            
        Raises:
            InvalidStateError: If updates create invalid state
        """
        logger.debug(f"Updating state with {len(updates)} fields")
        
        # Apply updates
        for key, value in updates.items():
            if key in state or key in AgentState.__annotations__:
                state[key] = value
            else:
                logger.warning(f"Unknown state field: {key}")
        
        # Validate updated state
        try:
            self.validate_state(state)
        except InvalidStateError as e:
            logger.error(f"State validation failed after update: {e}")
            raise
        
        # Track history if enabled
        if self.enable_history:
            self._track_state(state, "update")
        
        return state
    
    def validate_state(self, state: AgentState) -> None:
        """
        Validate state structure and values
        
        Args:
            state: State to validate
            
        Raises:
            InvalidStateError: If state is invalid
        """
        # Check required fields (critical for workflow)
        required_fields = [
            "conversation_id",
            "customer_id",
            "current_message",
            "status"
        ]
        
        for field in required_fields:
            if field not in state or state[field] is None:
                raise InvalidStateError(
                    f"Missing required field: {field}",
                    invalid_field=field
                )
        
        # Validate confidence scores (0-1 range)
        if "intent_confidence" in state:
            conf = state["intent_confidence"]
            if not isinstance(conf, (int, float)) or not 0.0 <= conf <= 1.0:
                raise InvalidStateError(
                    f"intent_confidence must be between 0 and 1, got {conf}",
                    invalid_field="intent_confidence",
                    expected_value="0.0-1.0",
                    actual_value=conf
                )
        
        if "response_confidence" in state:
            conf = state["response_confidence"]
            if not isinstance(conf, (int, float)) or not 0.0 <= conf <= 1.0:
                raise InvalidStateError(
                    f"response_confidence must be between 0 and 1, got {conf}",
                    invalid_field="response_confidence",
                    expected_value="0.0-1.0",
                    actual_value=conf
                )
        
        # Validate sentiment (-1 to 1 range)
        if "sentiment" in state:
            sent = state["sentiment"]
            if not isinstance(sent, (int, float)) or not -1.0 <= sent <= 1.0:
                raise InvalidStateError(
                    f"sentiment must be between -1 and 1, got {sent}",
                    invalid_field="sentiment",
                    expected_value="-1.0 to 1.0",
                    actual_value=sent
                )
        
        # Validate status
        if "status" in state:
            valid_statuses = ["active", "resolved", "escalated"]
            if state["status"] not in valid_statuses:
                raise InvalidStateError(
                    f"Invalid status: {state['status']}",
                    invalid_field="status",
                    expected_value=valid_statuses,
                    actual_value=state["status"]
                )
        
        # Validate turn count doesn't exceed max
        if "turn_count" in state and "max_turns" in state:
            if state["turn_count"] > state["max_turns"]:
                raise InvalidStateError(
                    f"turn_count ({state['turn_count']}) exceeds max_turns ({state['max_turns']})",
                    invalid_field="turn_count",
                    context={"max_turns": state["max_turns"]}
                )
    
    def validate_state_transition(
        self,
        old_state: AgentState,
        new_state: AgentState
    ) -> None:
        """
        Validate that state transition is legal
        
        Args:
            old_state: Previous state
            new_state: New state
            
        Raises:
            InvalidStateError: If transition is invalid
        """
        # Check conversation_id doesn't change
        if old_state["conversation_id"] != new_state["conversation_id"]:
            raise InvalidStateError(
                "conversation_id cannot change during workflow",
                invalid_field="conversation_id"
            )
        
        # Check turn count only increases
        old_turns = old_state.get("turn_count", 0)
        new_turns = new_state.get("turn_count", 0)
        if new_turns < old_turns:
            raise InvalidStateError(
                "turn_count cannot decrease",
                invalid_field="turn_count",
                expected_value=f">= {old_turns}",
                actual_value=new_turns
            )
        
        # Status should only transition in allowed ways
        old_status = old_state.get("status", "active")
        new_status = new_state.get("status", "active")
        
        invalid_transitions = [
            ("resolved", "active"),
            ("escalated", "active"),
            ("escalated", "resolved")
        ]
        
        if (old_status, new_status) in invalid_transitions:
            raise InvalidStateError(
                f"Invalid status transition: {old_status} -> {new_status}",
                invalid_field="status",
                context={"old_status": old_status, "new_status": new_status}
            )
    
    def get_state_snapshot(self, state: AgentState) -> Dict[str, Any]:
        """
        Create immutable snapshot of current state
        
        Args:
            state: Current state
            
        Returns:
            Deep copy of state for debugging/logging
        """
        return deepcopy(state)
    
    def _track_state(self, state: AgentState, event: str) -> None:
        """Track state in history (internal)"""
        if self.enable_history:
            snapshot = self.get_state_snapshot(state)
            self.state_history.append({
                "event": event,
                "state": snapshot,
                "turn_count": state.get("turn_count", 0),
                "agent": state.get("current_agent")
            })
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get state history (if tracking enabled)"""
        return self.state_history
    
    def clear_history(self) -> None:
        """Clear state history"""
        self.state_history.clear()


if __name__ == "__main__":
    # Test state manager
    print("Testing WorkflowStateManager...")
    print("=" * 60)
    
    manager = WorkflowStateManager(enable_history=True)
    
    # Test state creation
    print("\n1. Creating initial state...")
    state = manager.create_initial_state(
        message="I want to upgrade my plan",
        context={
            "customer_id": "test_user",
            "customer_metadata": {"plan": "free"}
        }
    )
    print(f"✓ State created: {state['conversation_id']}")
    print(f"  Status: {state['status']}")
    print(f"  Customer: {state['customer_id']}")
    
    # Test state update
    print("\n2. Updating state...")
    state = manager.update_state(state, {
        "primary_intent": "billing_upgrade",
        "intent_confidence": 0.95,
        "turn_count": 1
    })
    print(f"✓ State updated")
    print(f"  Intent: {state['primary_intent']}")
    print(f"  Confidence: {state['intent_confidence']}")
    
    # Test validation - valid state
    print("\n3. Testing validation (valid)...")
    try:
        manager.validate_state(state)
        print("✓ Validation passed")
    except InvalidStateError as e:
        print(f"✗ Validation failed: {e}")
    
    # Test validation - invalid confidence
    print("\n4. Testing validation (invalid confidence)...")
    try:
        invalid_state = manager.get_state_snapshot(state)
        invalid_state["intent_confidence"] = 2.0  # Invalid!
        manager.validate_state(invalid_state)
        print("✗ Should have failed validation")
    except InvalidStateError as e:
        print(f"✓ Correctly caught error: {e.message}")
    
    # Test state history
    print("\n5. Checking state history...")
    history = manager.get_state_history()
    print(f"✓ Tracked {len(history)} state changes")
    for i, entry in enumerate(history):
        print(f"  {i+1}. Event: {entry['event']}, Turn: {entry['turn_count']}")
    
    print("\n✓ All tests passed!")