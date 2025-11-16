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

from src.workflow.graph import SupportGraph
from src.workflow.state import AgentState, create_initial_state
from src.workflow.result_handler import AgentResultHandler
from src.workflow.state_manager import WorkflowStateManager
from src.workflow.exceptions import (
    AgentExecutionError,
    AgentTimeoutError,
    RoutingError,
    InvalidStateError
)
from src.utils.logging.setup import get_logger


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
        
        # Phase 5: Structured logger
        self.logger = get_logger(__name__)
        
        self.logger.info(
            "workflow_engine_initialized",
            timeout_seconds=timeout,
            max_retries=max_retries
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
            Dict with agent response, intent, confidence, etc.
                
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
        self.logger.info(
            "workflow_execution_started",
            message_preview=message[:50],
            has_context=context is not None,
            context_keys=list(context.keys()) if context else []
        )
        
        # Create initial state
        try:
            initial_state = self.state_manager.create_initial_state(
                message=message,
                context=context or {}
            )
        except InvalidStateError as e:
            self.logger.error(
                "workflow_state_creation_failed",
                error=str(e),
                exc_info=True
            )
            raise
        
        # Execute with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(
                        "workflow_retry_attempt",
                        attempt=attempt,
                        max_retries=self.max_retries
                    )
                
                # Run workflow with timeout
                final_state = await self._execute_with_timeout(
                    initial_state,
                    timeout=self.timeout
                )
                
                # Parse and validate result
                result = self.result_handler.parse_result(final_state)
                self.result_handler.validate_result(result)
                
                self.logger.info(
                    "workflow_execution_completed",
                    attempt=attempt + 1,
                    intent=result['primary_intent'],
                    confidence=round(result['intent_confidence'], 2),
                    agents=result['agent_history'],
                    status=result['status']
                )
                
                return result
                
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    self.logger.warning(
                        "workflow_timeout_retrying",
                        attempt=attempt + 1,
                        max_attempts=self.max_retries + 1,
                        timeout_seconds=self.timeout
                    )
                    # Wait a bit before retrying
                    await asyncio.sleep(1)
                    continue
                else:
                    self.logger.error(
                        "workflow_timeout_exhausted",
                        total_attempts=self.max_retries + 1,
                        timeout_seconds=self.timeout
                    )
                    raise AgentTimeoutError(
                        f"Workflow exceeded timeout of {self.timeout}s "
                        f"after {self.max_retries + 1} attempts",
                        timeout_seconds=self.timeout
                    )
            
            except InvalidStateError:
                # Don't retry on validation errors
                self.logger.error(
                    "workflow_state_validation_failed",
                    message="State validation failed - not retrying"
                )
                raise
            
            except Exception as e:
                if attempt < self.max_retries:
                    self.logger.warning(
                        "workflow_execution_error_retrying",
                        attempt=attempt + 1,
                        max_attempts=self.max_retries + 1,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    # Wait a bit before retrying
                    await asyncio.sleep(1)
                    continue
                else:
                    self.logger.error(
                        "workflow_execution_failed",
                        total_attempts=self.max_retries + 1,
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
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
            self.logger.error(
                "workflow_timeout",
                timeout_seconds=timeout
            )
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
        from src.agents.essential.routing.meta_router import MetaRouter

        self.logger.debug(
            "intent_classification_requested",
            message_preview=message[:50]
        )

        # Create minimal state
        state = create_initial_state(message)

        # Run just router
        router = MetaRouter()
        result_state = router.process(state)
        
        classification = {
            "intent": result_state.get("primary_intent"),
            "confidence": result_state.get("intent_confidence", 0.0),
            "sentiment": result_state.get("sentiment", 0.0)
        }
        
        self.logger.info(
            "intent_classified",
            intent=classification["intent"],
            confidence=round(classification["confidence"], 2)
        )
        
        return classification
    
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
            self.logger.debug(
                "routing_decision",
                intent=intent,
                confidence=confidence,
                decision="escalate",
                reason="low_confidence"
            )
            return "escalation"
        
        # High confidence, simple query -> end (router answers)
        if confidence > 0.8 and self._is_simple_query(intent):
            self.logger.debug(
                "routing_decision",
                intent=intent,
                confidence=confidence,
                decision="answer_directly",
                reason="high_confidence_simple_query"
            )
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
        
        agent = routing_map.get(intent, "escalation")
        
        self.logger.debug(
            "routing_decision",
            intent=intent,
            confidence=confidence,
            decision="route_to_specialist",
            agent=agent
        )
        
        return agent
    
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
            self.logger.info(
                "escalation_triggered",
                reason="low_confidence",
                confidence=state.get("response_confidence")
            )
            return True
        
        # Check turn count
        if state.get("turn_count", 0) > 5:
            self.logger.info(
                "escalation_triggered",
                reason="max_turns_exceeded",
                turn_count=state.get("turn_count")
            )
            return True
        
        # Check sentiment
        if state.get("sentiment", 0.0) < -0.7:
            self.logger.info(
                "escalation_triggered",
                reason="negative_sentiment",
                sentiment=state.get("sentiment")
            )
            return True
        
        # Check explicit flag
        if state.get("should_escalate", False):
            self.logger.info(
                "escalation_triggered",
                reason="explicit_flag"
            )
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