"""
Agent Workflow Engine - Pure AI coordination, NO business logic

This is the main entry point for executing agent workflows. It coordinates
multi-agent interactions using LangGraph and returns structured results.

Key Principles:
- STATELESS: No instance state between calls
- NO BUSINESS LOGIC: That belongs in domain services
- NO DATABASE OPERATIONS: That belongs in infrastructure services  
- PURE AI COORDINATION: Execute workflows and return results

This engine is called by application services which handle:
- Transaction management
- Database persistence
- Business logic orchestration
"""
import asyncio
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from workflow.graph import SupportGraph
from workflow.state import AgentState, create_initial_state
from workflow.result_handler import AgentResultHandler
from workflow.state_manager import WorkflowStateManager
from workflow.exceptions import (
    AgentExecutionError,
    AgentTimeoutError,
    RoutingError,
    InvalidStateError
)

logger = logging.getLogger(__name__)


class AgentWorkflowEngine:
    """
    Agent Workflow Engine - Coordinates multi-agent AI workflows
    
    Responsibilities:
    - Execute LangGraph workflows
    - Manage agent state
    - Handle timeouts and retries
    - Return structured results
    
    NOT responsible for:
    - Business logic (handled by domain services)
    - Database operations (handled by infrastructure services)
    - Transaction management (handled by application services)
    
    This is a STATELESS workflow coordinator:
    - No instance state between calls
    - No database access
    - Pure AI coordination
    
    Example usage:
        engine = AgentWorkflowEngine(timeout=30, max_retries=2)
        result = await engine.execute(
            message="I want to upgrade my plan",
            context={"customer_id": "user123"}
        )
        # result is a structured dict ready for use
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 2,
        enable_logging: bool = True
    ):
        """
        Initialize workflow engine
        
        Args:
            timeout: Maximum execution time in seconds (default: 30)
            max_retries: Number of retry attempts on failure (default: 2)
            enable_logging: Enable detailed logging (default: True)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_logging = enable_logging
        
        # Initialize components
        self.graph = SupportGraph()
        self.result_handler = AgentResultHandler()
        self.state_manager = WorkflowStateManager()
        
        logger.info(
            f"AgentWorkflowEngine initialized "
            f"(timeout={timeout}s, retries={max_retries})"
        )
    
    async def execute(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent workflow for a message
        
        This is the main entry point for workflow execution. It:
        1. Creates initial state from context
        2. Runs LangGraph workflow with timeout and retries
        3. Parses and validates results
        4. Returns structured output
        
        The workflow is STATELESS - all context must be provided
        in the context parameter. Results are returned, not stored.
        
        Args:
            message: User's message to process
            context: Optional context dictionary with:
                - conversation_id: Continue existing conversation
                - customer_id: Customer identifier
                - customer_metadata: Customer info (plan, tier, etc.)
                - conversation_history: Previous messages
                
        Returns:
            Dict with:
                - agent_response: str - Agent's response text
                - agent_history: List[str] - Agents involved in order
                - current_agent: str - Last agent that processed
                - primary_intent: str - Classified intent
                - intent_confidence: float - Confidence (0-1)
                - sentiment: float - Sentiment (-1 to 1)
                - kb_results: List[Dict] - KB articles used
                - kb_articles_used: List[str] - KB article titles
                - status: str - Conversation status (active/resolved/escalated)
                - should_escalate: bool - Escalation needed
                - escalation_reason: str - Why escalate (if applicable)
                - response_confidence: float - Response confidence (0-1)
                - turn_count: int - Number of turns
                - tools_used: List[str] - Tools called
                - entities: Dict - Extracted entities
                - conversation_id: str - Conversation ID
                - customer_id: str - Customer ID
                - raw_state: Dict - Sanitized state for debugging
                
        Raises:
            AgentTimeoutError: If workflow exceeds timeout after all retries
            AgentExecutionError: If workflow fails after all retries
            InvalidStateError: If state is invalid
        
        Example:
            result = await engine.execute(
                message="How do I upgrade?",
                context={
                    "customer_id": "user123",
                    "customer_metadata": {"plan": "free"}
                }
            )
            print(result["agent_response"])
        """
        if self.enable_logging:
            logger.info(f"Executing workflow for message: '{message[:50]}...'")
        
        # Create initial state
        try:
            initial_state = self.state_manager.create_initial_state(
                message=message,
                context=context or {}
            )
        except InvalidStateError as e:
            logger.error(f"Failed to create initial state: {e}")
            raise
        
        # Execute with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                if self.enable_logging and attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{self.max_retries}")
                
                # Run workflow with timeout
                final_state = await self._execute_with_timeout(
                    initial_state,
                    timeout=self.timeout
                )
                
                # Parse and validate result
                result = self.result_handler.parse_result(final_state)
                self.result_handler.validate_result(result)
                
                if self.enable_logging:
                    logger.info(
                        f"Workflow completed successfully "
                        f"(attempt={attempt + 1}, "
                        f"intent={result['primary_intent']}, "
                        f"confidence={result['intent_confidence']:.2f}, "
                        f"agents={result['agent_history']})"
                    )
                
                return result
                
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    logger.warning(
                        f"Workflow timeout on attempt {attempt + 1}/{self.max_retries + 1}, retrying..."
                    )
                    # Wait a bit before retrying
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Workflow timeout after all {self.max_retries + 1} attempts")
                    raise AgentTimeoutError(
                        f"Workflow exceeded timeout of {self.timeout}s "
                        f"after {self.max_retries + 1} attempts",
                        timeout_seconds=self.timeout
                    )
            
            except InvalidStateError:
                # Don't retry on validation errors
                logger.error("State validation failed - not retrying")
                raise
            
            except Exception as e:
                if attempt < self.max_retries:
                    logger.warning(
                        f"Workflow error on attempt {attempt + 1}/{self.max_retries + 1}: {e}, retrying..."
                    )
                    # Wait a bit before retrying
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.error(f"Workflow failed after all {self.max_retries + 1} attempts: {e}")
                    raise AgentExecutionError(
                        f"Workflow failed after {self.max_retries + 1} attempts: {e}",
                        original_error=e
                    ) from e
    
    async def _execute_with_timeout(
        self,
        initial_state: AgentState,
        timeout: int
    ) -> AgentState:
        """
        Execute workflow with timeout (internal method)
        
        Args:
            initial_state: Initial state to execute
            timeout: Timeout in seconds
            
        Returns:
            Final state after execution
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        try:
            # Run graph with timeout
            # LangGraph invoke is synchronous, so we wrap it
            final_state = await asyncio.wait_for(
                self._run_graph(initial_state),
                timeout=timeout
            )
            return final_state
            
        except asyncio.TimeoutError:
            logger.error(f"Workflow timeout after {timeout}s")
            raise
    
    async def _run_graph(self, state: AgentState) -> AgentState:
        """
        Run LangGraph workflow (wrapper for async execution)
        
        LangGraph's invoke() is synchronous, so we run it in
        an executor to make it async-compatible.
        
        Args:
            state: Initial state
            
        Returns:
            Final state after graph execution
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.graph.app.invoke,
            state
        )
    
    def classify_intent(self, message: str) -> Dict[str, Any]:
        """
        Classify intent without full workflow execution
        
        This is a lightweight operation that just runs the router
        agent to get intent classification, without executing the
        full workflow.
        
        Useful for:
        - Pre-routing decisions
        - Analytics and logging
        - Intent-based filtering
        
        Args:
            message: User message to classify
            
        Returns:
            Dict with:
                - intent: Classified intent category
                - confidence: Confidence score (0-1)
                - sentiment: Sentiment score (-1 to 1)
        
        Example:
            classification = engine.classify_intent("I want to upgrade")
            if classification["confidence"] > 0.8:
                # High confidence, proceed
        """
        from agents.router import RouterAgent
        
        # Create minimal state
        state = create_initial_state(message)
        
        # Run just router
        router = RouterAgent()
        result_state = router.process(state)
        
        return {
            "intent": result_state.get("primary_intent"),
            "confidence": result_state.get("intent_confidence", 0.0),
            "sentiment": result_state.get("sentiment", 0.0)
        }
    
    def route_to_agent(
        self,
        intent: str,
        confidence: float
    ) -> Optional[str]:
        """
        Determine which agent to route to based on intent
        
        This implements the routing logic extracted from the router
        agent for testing and reuse.
        
        Args:
            intent: Classified intent
            confidence: Confidence score (0-1)
            
        Returns:
            Agent name or None (for direct answer by router)
        
        Example:
            agent = engine.route_to_agent("billing_upgrade", 0.9)
            # Returns "billing"
        """
        # Low confidence -> escalate
        if confidence < 0.5:
            return "escalation"
        
        # High confidence, simple query -> end (router answers)
        if confidence > 0.8 and self._is_simple_query(intent):
            return None
        
        # Route to specialist based on intent
        routing_map = {
            "billing_upgrade": "billing",
            "billing_downgrade": "billing",
            "billing_refund": "billing",
            "billing_invoice": "billing",
            "technical_bug": "technical",
            "technical_sync": "technical",
            "technical_performance": "technical",
            "feature_create": "usage",
            "feature_edit": "usage",
            "feature_invite": "usage",
            "feature_export": "usage",
            "integration_api": "api",
            "integration_webhook": "api",
            "account_login": "technical",
            "general_inquiry": "escalation"
        }
        
        return routing_map.get(intent, "escalation")
    
    def should_escalate(self, state: AgentState) -> bool:
        """
        Determine if conversation should escalate to human
        
        Escalation triggers:
        - Low confidence (< 0.4)
        - Too many turns (> 5)
        - Very negative sentiment (< -0.7)
        - Explicit escalation flag set
        
        Args:
            state: Current agent state
            
        Returns:
            True if should escalate to human
        
        Example:
            if engine.should_escalate(state):
                # Hand off to human agent
        """
        # Check confidence
        if state.get("response_confidence", 1.0) < 0.4:
            if self.enable_logging:
                logger.info("Escalation triggered: low confidence")
            return True
        
        # Check turn count
        if state.get("turn_count", 0) > 5:
            if self.enable_logging:
                logger.info("Escalation triggered: max turns exceeded")
            return True
        
        # Check sentiment
        if state.get("sentiment", 0.0) < -0.7:
            if self.enable_logging:
                logger.info("Escalation triggered: negative sentiment")
            return True
        
        # Check explicit flag
        if state.get("should_escalate", False):
            if self.enable_logging:
                logger.info("Escalation triggered: explicit flag")
            return True
        
        return False
    
    def _is_simple_query(self, intent: str) -> bool:
        """
        Check if intent represents a simple query (internal)
        
        Simple queries can be answered directly by the router
        without routing to a specialist.
        """
        simple_intents = ["general_inquiry"]
        return intent in simple_intents
    
    def get_confidence_level(self, state: AgentState) -> float:
        """
        Get overall confidence level from state
        
        Combines intent confidence and response confidence.
        
        Args:
            state: Agent state
            
        Returns:
            Combined confidence score (0-1)
        """
        intent_conf = state.get("intent_confidence", 0.0)
        response_conf = state.get("response_confidence", 0.0)
        
        # Average of both confidences
        return (intent_conf + response_conf) / 2.0


if __name__ == "__main__":
    # Test the workflow engine
    print("=" * 70)
    print("TESTING AGENT WORKFLOW ENGINE")
    print("=" * 70)
    
    import asyncio
    
    async def test_engine():
        # Initialize engine
        engine = AgentWorkflowEngine(timeout=30, max_retries=2)
        
        # Test case 1: Normal execution
        print("\n" + "="*70)
        print("TEST 1: Normal Execution")
        print("="*70)
        
        result = await engine.execute(
            message="I want to upgrade to premium",
            context={"customer_id": "test_user"}
        )
        
        print(f"\n✓ Workflow completed")
        print(f"  Intent: {result['primary_intent']}")
        print(f"  Confidence: {result['intent_confidence']:.2f}")
        print(f"  Agents: {' → '.join(result['agent_history'])}")
        print(f"  Status: {result['status']}")
        print(f"  Response: {result['agent_response'][:100]}...")
        
        # Test case 2: Intent classification only
        print("\n" + "="*70)
        print("TEST 2: Intent Classification Only")
        print("="*70)
        
        classification = engine.classify_intent("How do I export my data?")
        print(f"\n✓ Intent classified")
        print(f"  Intent: {classification['intent']}")
        print(f"  Confidence: {classification['confidence']:.2f}")
        print(f"  Sentiment: {classification['sentiment']:+.2f}")
        
        # Test case 3: Routing decision
        print("\n" + "="*70)
        print("TEST 3: Routing Decision")
        print("="*70)
        
        agent = engine.route_to_agent("billing_upgrade", 0.95)
        print(f"\n✓ Routing determined")
        print(f"  Intent: billing_upgrade (confidence: 0.95)")
        print(f"  Route to: {agent.upper() if agent else 'END (router answers)'}")
        
        print("\n" + "="*70)
        print("✓ All tests passed!")
        print("="*70)
    
    # Run async tests
    asyncio.run(test_engine())