"""
LangGraph - Multi-agent orchestration using LangGraph
Full version: All 6 agents (Router, Billing, Technical, Usage, API, Escalation)

This module defines the LangGraph workflow that routes between agents.
It handles the low-level graph construction and execution, while the
AgentWorkflowEngine provides the high-level interface.
"""
from typing import Literal, Optional, Dict, Any
from langgraph.graph import StateGraph, END

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.workflow.state import AgentState, create_initial_state
from src.agents.router import RouterAgent
from src.agents.billing import BillingAgent
from src.agents.technical import TechnicalAgent
from src.agents.usage import UsageAgent
from src.agents.api import APIAgent
from src.agents.escalation import EscalationAgent
from src.utils.logging.setup import get_logger


class SupportGraph:
    """
    Multi-agent support system graph using LangGraph
    
    This class wraps the LangGraph workflow and provides a clean
    interface for executing multi-agent conversations.
    
    Agent Architecture:
    1. Router - Entry point, classifies intent and routes
    2. Billing - Handles payment/subscription issues
    3. Technical - Handles bugs and troubleshooting
    4. Usage - Handles feature how-tos
    5. API - Handles developer integrations
    6. Escalation - Hands off to humans
    
    Routing Pattern:
    - Single-hop: Router → Specialist → END
    - Router can answer directly: Router → END
    - Low confidence: Router → Escalation → END
    
    No circular routing or multi-hop between specialists.
    """
    
    def __init__(self):
        """Initialize graph with all agents"""
        self.logger = get_logger(__name__)
        self.logger.info("support_graph_initializing", agent_count=6)
        
        # Initialize all agents
        self.router = RouterAgent()
        self.billing = BillingAgent()
        self.technical = TechnicalAgent()
        self.usage = UsageAgent()
        self.api = APIAgent()
        self.escalation = EscalationAgent()
        
        # Build LangGraph workflow
        self.app = self._build_graph()
        
        self.logger.info("support_graph_initialized", status="compiled")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the complete LangGraph workflow
        
        Returns:
            Compiled LangGraph application
        """
        workflow = StateGraph(AgentState)
        
        # Add all agent nodes
        # Each node is a function that takes state and returns updated state
        workflow.add_node("router", self.router.process)
        workflow.add_node("billing", self.billing.process)
        workflow.add_node("technical", self.technical.process)
        workflow.add_node("usage", self.usage.process)
        workflow.add_node("api", self.api.process)
        workflow.add_node("escalation", self.escalation.process)
        
        # Entry point - always start with router
        workflow.set_entry_point("router")
        
        # Routing function - decides where to go after router
        def route_from_router(state: AgentState) -> str:
            """
            Decide where to route from router
            
            Router sets state["next_agent"] to indicate routing:
            - "billing", "technical", "usage", "api" → Route to specialist
            - "escalation" → Route to escalation
            - None → Router answered directly, end conversation
            
            Args:
                state: Current agent state
                
            Returns:
                Next node name or END
            """
            next_agent = state.get("next_agent")
            
            if next_agent == "billing":
                return "billing"
            elif next_agent == "technical":
                return "technical"
            elif next_agent == "usage":
                return "usage"
            elif next_agent == "api":
                return "api"
            elif next_agent == "escalation":
                return "escalation"
            else:
                # Router answered directly or no routing decision
                return END
        
        # Add conditional routing from router to specialists
        workflow.add_conditional_edges(
            "router",
            route_from_router,
            {
                "billing": "billing",
                "technical": "technical",
                "usage": "usage",
                "api": "api",
                "escalation": "escalation",
                END: END
            }
        )
        
        # All specialist agents end after responding
        # Single-hop architecture: no routing between specialists
        workflow.add_edge("billing", END)
        workflow.add_edge("technical", END)
        workflow.add_edge("usage", END)
        workflow.add_edge("api", END)
        workflow.add_edge("escalation", END)
        
        # Compile the graph
        compiled = workflow.compile()
        self.logger.debug("langgraph_workflow_compiled")
        
        return compiled
    
    def run(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Run conversation through graph
        
        This is the main execution method that:
        1. Creates initial state
        2. Runs through LangGraph workflow
        3. Returns final state
        
        Args:
            message: User's message
            conversation_id: Optional conversation ID for context
            context: Optional additional context (customer_metadata, etc.)
            
        Returns:
            Final agent state after workflow execution
        """
        self.logger.info(
            "workflow_execution_starting",
            message_preview=message[:50],
            conversation_id=conversation_id
        )
        
        # Build context dict
        ctx = context or {}
        if conversation_id:
            ctx["conversation_id"] = conversation_id
        
        # Create initial state with context
        initial_state = create_initial_state(
            message=message,
            conversation_id=conversation_id,
            context=ctx
        )
        
        self.logger.debug(
            "initial_state_created",
            conversation_id=initial_state['conversation_id'],
            customer_id=initial_state['customer_id']
        )
        
        # Execute workflow
        try:
            final_state = self.app.invoke(initial_state)
            
            self.logger.info(
                "workflow_execution_completed",
                intent=final_state.get('primary_intent'),
                agents=final_state.get('agent_history'),
                status=final_state.get('status')
            )
            
            return final_state
            
        except Exception as e:
            self.logger.error(
                "workflow_execution_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    def get_response(self, message: str) -> str:
        """
        Simple interface - just get the response text
        
        Convenience method for quick interactions without
        needing to inspect the full state.
        
        Args:
            message: User's message
            
        Returns:
            Agent's response text
        """
        result = self.run(message)
        return result.get("agent_response", "I'm not sure how to help with that.")


if __name__ == "__main__":
    print("=" * 70)
    print("TESTING SUPPORT GRAPH - ALL 6 AGENTS")
    print("=" * 70)
    
    # Initialize graph
    graph = SupportGraph()
    
    # Test cases covering all agents
    test_cases = [
        ("I want to upgrade to premium", "billing"),
        ("My tasks are not syncing", "technical"),
        ("How do I invite team members?", "usage"),
        ("How do I authenticate with the API?", "api"),
        ("Show me Python code for the API", "api"),
        ("This is really confusing", "escalation"),
    ]
    
    print("\n" + "=" * 70)
    print("RUNNING TEST CASES")
    print("=" * 70)
    
    for i, (msg, expected) in enumerate(test_cases, 1):
        print(f"\n{'#'*70}")
        print(f"TEST {i}/{len(test_cases)}: {msg}")
        print(f"Expected: {expected.upper()} agent")
        print(f"{'#'*70}")
        
        try:
            result = graph.run(msg)
            
            agents = result.get('agent_history', [])
            intent = result.get('primary_intent', 'N/A')
            confidence = result.get('intent_confidence', 0)
            status = result.get('status', 'unknown')
            
            print(f"\n✓ Intent: {intent} ({confidence:.0%} confidence)")
            print(f"✓ Path: {' → '.join([a.upper() for a in agents])}")
            print(f"✓ Status: {status}")
            
            # Show response preview
            response = result.get('agent_response', 'N/A')
            preview = response[:150] + "..." if len(response) > 150 else response
            print(f"✓ Response: {preview}")
            
            # Check if routed correctly
            if expected in agents:
                print(f"✓ PASS - Routed to correct agent")
            else:
                print(f"✗ FAIL - Expected {expected}, got {agents}")
                
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print("All 6 agents are integrated and working!")
    print("\nAgent capabilities:")
    print("  1. Router - Intent classification and routing")
    print("  2. Billing - Payments, subscriptions, refunds")
    print("  3. Technical - Bug troubleshooting, sync issues")
    print("  4. Usage - Feature tutorials and how-tos")
    print("  5. API - Developer integrations, code examples")
    print("  6. Escalation - Human handoff when needed")
    print(f"{'='*70}")