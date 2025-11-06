"""
Agent Result Handler - Parse and validate agent workflow outputs

Converts internal agent state to structured output suitable for
consumption by application services. Ensures results are complete
and valid before returning to callers.
"""
from typing import Dict, Any, List, Optional
import logging

from workflow.state import AgentState
from workflow.exceptions import InvalidStateError

logger = logging.getLogger(__name__)


class AgentResultHandler:
    """
    Parse and validate agent workflow results
    
    Responsibilities:
    - Convert AgentState to structured output
    - Extract metadata (intent, sentiment, confidence)
    - Validate result completeness
    - Handle malformed agent responses
    - Sanitize state for storage
    
    NOT responsible for:
    - Storing results (infrastructure handles that)
    - Business logic (domain services handle that)
    - Workflow execution (engine handles that)
    """
    
    def __init__(self):
        """Initialize result handler"""
        logger.debug("ResultHandler initialized")
    
    def parse_result(self, state: AgentState) -> Dict[str, Any]:
        """
        Parse final state into structured result
        
        This converts the internal AgentState into a clean,
        well-structured dictionary suitable for API responses
        and database storage.
        
        Args:
            state: Final agent state after workflow execution
            
        Returns:
            Structured result dictionary with:
                - agent_response: The response text
                - agent_history: List of agents involved
                - primary_intent: Classified intent
                - intent_confidence: Confidence score
                - sentiment: Sentiment score
                - kb_results: KB articles used
                - status: Conversation status
                - should_escalate: Escalation flag
                - metadata: Additional metadata
                - raw_state: Sanitized state (for debugging)
        """
        logger.debug("Parsing result from final state")
        
        # Extract core response data
        result = {
            # Response
            "agent_response": state.get("agent_response", ""),
            
            # Routing
            "agent_history": state.get("agent_history", []),
            "current_agent": state.get("current_agent"),
            
            # Classification
            "primary_intent": state.get("primary_intent"),
            "intent_confidence": state.get("intent_confidence", 0.0),
            "sentiment": state.get("sentiment", 0.0),
            
            # Knowledge Base
            "kb_results": state.get("kb_results", []),
            "kb_articles_used": self._extract_kb_articles(state),
            
            # Status
            "status": state.get("status", "active"),
            "should_escalate": state.get("should_escalate", False),
            "escalation_reason": state.get("escalation_reason"),
            
            # Metadata
            "response_confidence": state.get("response_confidence", 0.0),
            "turn_count": state.get("turn_count", 0),
            "tools_used": state.get("tools_used", []),
            "entities": state.get("entities", {}),
            
            # Conversation context
            "conversation_id": state.get("conversation_id"),
            "customer_id": state.get("customer_id"),
            
            # Full state (sanitized for debugging)
            "raw_state": self._sanitize_state(state)
        }
        
        logger.debug(
            f"Result parsed: intent={result['primary_intent']}, "
            f"confidence={result['intent_confidence']:.2f}, "
            f"status={result['status']}"
        )
        
        return result
    
    def extract_metadata(self, state: AgentState) -> Dict[str, Any]:
        """
        Extract just metadata from state (lightweight)
        
        Useful for logging, metrics, and quick checks without
        parsing the full result.
        
        Args:
            state: Agent state
            
        Returns:
            Metadata dictionary
        """
        return {
            "primary_intent": state.get("primary_intent"),
            "intent_confidence": state.get("intent_confidence", 0.0),
            "sentiment": state.get("sentiment", 0.0),
            "agents_involved": state.get("agent_history", []),
            "kb_articles_count": len(state.get("kb_results", [])),
            "turn_count": state.get("turn_count", 0),
            "status": state.get("status", "active"),
            "should_escalate": state.get("should_escalate", False)
        }
    
    def validate_result(self, result: Dict[str, Any]) -> None:
        """
        Validate result structure and completeness
        
        Ensures the result meets minimum quality standards before
        being returned to the caller.
        
        Args:
            result: Parsed result from parse_result()
            
        Raises:
            InvalidStateError: If result is invalid or incomplete
        """
        logger.debug("Validating result")
        
        # Check required fields exist
        required_fields = [
            "agent_response",
            "agent_history",
            "primary_intent",
            "status"
        ]
        
        missing = [f for f in required_fields if f not in result]
        if missing:
            raise InvalidStateError(
                f"Missing required fields in result: {missing}",
                context={"missing_fields": missing}
            )
        
        # Validate response not empty (warning only)
        if not result.get("agent_response") or not result["agent_response"].strip():
            logger.warning("Agent response is empty - this may indicate a problem")
        
        # Validate confidence range
        confidence = result.get("intent_confidence", 0.0)
        if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
            raise InvalidStateError(
                f"Invalid intent_confidence: {confidence} (must be 0.0-1.0)",
                invalid_field="intent_confidence",
                expected_value="0.0-1.0",
                actual_value=confidence
            )
        
        # Validate response confidence range
        response_conf = result.get("response_confidence", 0.0)
        if not isinstance(response_conf, (int, float)) or not 0.0 <= response_conf <= 1.0:
            raise InvalidStateError(
                f"Invalid response_confidence: {response_conf} (must be 0.0-1.0)",
                invalid_field="response_confidence",
                expected_value="0.0-1.0",
                actual_value=response_conf
            )
        
        # Validate sentiment range
        sentiment = result.get("sentiment", 0.0)
        if not isinstance(sentiment, (int, float)) or not -1.0 <= sentiment <= 1.0:
            raise InvalidStateError(
                f"Invalid sentiment: {sentiment} (must be -1.0 to 1.0)",
                invalid_field="sentiment",
                expected_value="-1.0 to 1.0",
                actual_value=sentiment
            )
        
        # Validate status
        valid_statuses = ["active", "resolved", "escalated"]
        if result["status"] not in valid_statuses:
            raise InvalidStateError(
                f"Invalid status: {result['status']}",
                invalid_field="status",
                expected_value=valid_statuses,
                actual_value=result["status"]
            )
        
        # Validate agent history not empty (should have at least router)
        if not result.get("agent_history"):
            logger.warning("agent_history is empty - workflow may not have executed properly")
        
        logger.debug("Result validation passed")
    
    def get_kb_articles(self, state: AgentState) -> List[Dict]:
        """
        Extract KB articles from state
        
        Args:
            state: Agent state
            
        Returns:
            List of KB article dictionaries
        """
        return state.get("kb_results", [])
    
    def get_agent_path(self, state: AgentState) -> List[str]:
        """
        Get agent routing path
        
        Args:
            state: Agent state
            
        Returns:
            List of agent names in order visited
        """
        return state.get("agent_history", [])
    
    def _extract_kb_articles(self, state: AgentState) -> List[str]:
        """
        Extract KB article titles (internal)
        
        Args:
            state: Agent state
            
        Returns:
            List of article titles
        """
        kb_results = state.get("kb_results", [])
        titles = []
        
        for article in kb_results:
            if isinstance(article, dict) and "title" in article:
                titles.append(article["title"])
        
        return titles
    
    def _sanitize_state(self, state: AgentState) -> Dict[str, Any]:
        """
        Sanitize state for storage (remove large objects)
        
        Creates a lightweight version of state suitable for
        storage and debugging, without large fields like
        full KB article content.
        
        Args:
            state: Agent state
            
        Returns:
            Sanitized state dictionary
        """
        sanitized = dict(state)
        
        # Remove or truncate large fields
        if "kb_results" in sanitized:
            # Keep count but remove full content
            kb_count = len(sanitized["kb_results"])
            sanitized["kb_results_count"] = kb_count
            # Keep just titles
            sanitized["kb_article_titles"] = self._extract_kb_articles(state)
            # Remove full results
            del sanitized["kb_results"]
        
        # Truncate long messages
        if "messages" in sanitized:
            # Keep count but truncate content
            message_count = len(sanitized["messages"])
            sanitized["message_count"] = message_count
            # Keep just last few messages
            sanitized["messages"] = sanitized["messages"][-3:] if sanitized["messages"] else []
        
        # Remove sensitive data if present
        if "customer_metadata" in sanitized:
            # Keep but sanitize
            metadata = sanitized["customer_metadata"]
            if isinstance(metadata, dict):
                # Remove any potentially sensitive fields
                sensitive_fields = ["email", "phone", "credit_card", "ssn"]
                for field in sensitive_fields:
                    if field in metadata:
                        metadata[field] = "[REDACTED]"
        
        return sanitized


if __name__ == "__main__":
    # Test result handler
    print("Testing AgentResultHandler...")
    print("=" * 60)
    
    handler = AgentResultHandler()
    
    # Create test state
    from workflow.state import create_initial_state
    
    test_state = create_initial_state("Test message")
    test_state.update({
        "agent_response": "Here's how to upgrade your plan...",
        "agent_history": ["router", "billing"],
        "current_agent": "billing",
        "primary_intent": "billing_upgrade",
        "intent_confidence": 0.95,
        "sentiment": 0.5,
        "status": "resolved",
        "response_confidence": 0.9,
        "kb_results": [
            {"title": "How to Upgrade", "content": "..."},
            {"title": "Pricing Plans", "content": "..."}
        ]
    })
    
    # Test parsing
    print("\n1. Testing parse_result...")
    result = handler.parse_result(test_state)
    print(f"✓ Result parsed")
    print(f"  Response: {result['agent_response'][:50]}...")
    print(f"  Agent path: {' → '.join(result['agent_history'])}")
    print(f"  Intent: {result['primary_intent']} ({result['intent_confidence']:.0%})")
    print(f"  KB articles: {len(result['kb_articles_used'])}")
    print(f"  Status: {result['status']}")
    
    # Test metadata extraction
    print("\n2. Testing extract_metadata...")
    metadata = handler.extract_metadata(test_state)
    print(f"✓ Metadata extracted: {len(metadata)} fields")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    # Test validation - valid result
    print("\n3. Testing validate_result (valid)...")
    try:
        handler.validate_result(result)
        print("✓ Validation passed")
    except InvalidStateError as e:
        print(f"✗ Validation failed: {e}")
    
    # Test validation - invalid confidence
    print("\n4. Testing validate_result (invalid)...")
    try:
        invalid_result = result.copy()
        invalid_result["intent_confidence"] = 2.0  # Invalid!
        handler.validate_result(invalid_result)
        print("✗ Should have caught invalid confidence")
    except InvalidStateError as e:
        print(f"✓ Correctly caught error: {e.message}")
    
    # Test sanitization
    print("\n5. Testing state sanitization...")
    sanitized = handler._sanitize_state(test_state)
    print(f"✓ State sanitized")
    print(f"  KB results removed: {'kb_results' not in sanitized}")
    print(f"  KB count preserved: {sanitized.get('kb_results_count')}")
    print(f"  Article titles preserved: {len(sanitized.get('kb_article_titles', []))}")
    
    print("\n✓ All tests passed!")