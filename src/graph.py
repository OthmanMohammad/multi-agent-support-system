"""
LangGraph - Multi-agent orchestration
Simple version: Router → Billing (for testing)
"""
from typing import Literal
from langgraph.graph import StateGraph, END

import sys
from pathlib import Path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from state import AgentState, create_initial_state
from agents.router import RouterAgent
from agents.billing import BillingAgent


class SupportGraph:
    """
    Multi-agent support system graph
    
    Flow:
    1. User message → Router Agent
    2. Router classifies intent
    3. Routes to Billing Agent (for now)
    4. Billing responds
    5. END
    """
    
    def __init__(self):
        """Initialize graph with agents"""
        print("Initializing Support Graph...")
        
        # Initialize agents
        self.router = RouterAgent()
        self.billing = BillingAgent()
        
        # Build graph
        self.app = self._build_graph()
        
        print("✓ Graph compiled and ready!")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow
        
        Returns:
            Compiled graph
        """
        # Create graph with AgentState
        workflow = StateGraph(AgentState)
        
        # Add agent nodes
        workflow.add_node("router", self.router.process)
        workflow.add_node("billing", self.billing.process)
        
        # Set entry point
        workflow.set_entry_point("router")
        
        # Add routing logic
        def route_from_router(state: AgentState) -> Literal["billing", "__end__"]:
            """Decide where to go after router"""
            next_agent = state.get("next_agent")
            
            # For now, only support billing
            if next_agent == "billing":
                return "billing"
            else:
                # Any other case: end (router answered directly or escalation)
                return END
        
        # Add conditional edges from router
        workflow.add_conditional_edges(
            "router",
            route_from_router,
            {
                "billing": "billing",
                END: END
            }
        )
        
        # Billing always ends
        workflow.add_edge("billing", END)
        
        # Compile
        app = workflow.compile()
        
        return app
    
    def run(self, message: str, conversation_id: str = None) -> AgentState:
        """
        Run a conversation through the graph
        
        Args:
            message: User's message
            conversation_id: Optional conversation ID
            
        Returns:
            Final state with response
        """
        # Create initial state
        initial_state = create_initial_state(
            message=message,
            conversation_id=conversation_id
        )
        
        print(f"\n{'='*70}")
        print(f"🚀 RUNNING SUPPORT GRAPH")
        print(f"{'='*70}")
        print(f"User Message: {message}")
        print(f"{'='*70}")
        
        # Run through graph
        final_state = self.app.invoke(initial_state)
        
        print(f"\n{'='*70}")
        print(f"✓ GRAPH EXECUTION COMPLETE")
        print(f"{'='*70}")
        
        return final_state
    
    def get_response(self, message: str) -> str:
        """
        Simple interface: message in, response out
        
        Args:
            message: User's message
            
        Returns:
            Agent's response
        """
        result = self.run(message)
        return result.get("agent_response", "I'm not sure how to help with that.")


if __name__ == "__main__":
    # Test the graph
    print("=" * 70)
    print("TESTING SUPPORT GRAPH")
    print("=" * 70)
    
    # Initialize graph
    graph = SupportGraph()
    
    # Test cases
    test_cases = [
        "I want to upgrade to premium",
        "How much does the basic plan cost?",
        "I need a refund",
        "Can I get an invoice?"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n\n{'#'*70}")
        print(f"TEST CASE {i}/{len(test_cases)}")
        print(f"{'#'*70}")
        
        # Run through graph
        result = graph.run(message)
        
        # Display results
        print(f"\n{'='*70}")
        print(f"RESULTS")
        print(f"{'='*70}")
        print(f"Intent: {result.get('primary_intent', 'N/A')}")
        print(f"Confidence: {result.get('intent_confidence', 0):.2%}")
        print(f"Agent Path: {' → '.join(result.get('agent_history', []))}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"\n--- RESPONSE ---")
        print(result.get('agent_response', 'No response'))
        print(f"{'='*70}")
        
        # Small pause for readability
        input("\nPress Enter for next test...")