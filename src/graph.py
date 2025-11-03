"""
LangGraph - Multi-agent orchestration
Full version: All 5 agents
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
from agents.technical import TechnicalAgent
from agents.usage import UsageAgent
from agents.escalation import EscalationAgent


class SupportGraph:
    """
    Multi-agent support system graph
    
    Agents:
    1. Router - Classifies and routes
    2. Billing - Payment/subscription issues
    3. Technical - Bugs and troubleshooting
    4. Usage - Feature how-tos
    5. Escalation - Hand off to humans
    """
    
    def __init__(self):
        """Initialize graph with all agents"""
        print("Initializing Support Graph with all agents...")
        
        # Initialize all agents
        self.router = RouterAgent()
        self.billing = BillingAgent()
        self.technical = TechnicalAgent()
        self.usage = UsageAgent()
        self.escalation = EscalationAgent()
        
        # Build graph
        self.app = self._build_graph()
        
        print("✓ Full graph compiled with 5 agents!")
    
    def _build_graph(self) -> StateGraph:
        """Build the complete LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add all agent nodes
        workflow.add_node("router", self.router.process)
        workflow.add_node("billing", self.billing.process)
        workflow.add_node("technical", self.technical.process)
        workflow.add_node("usage", self.usage.process)
        workflow.add_node("escalation", self.escalation.process)
        
        # Entry point
        workflow.set_entry_point("router")
        
        # Routing function
        def route_from_router(state: AgentState) -> str:
            """Decide where to route from router"""
            next_agent = state.get("next_agent")
            
            if next_agent == "billing":
                return "billing"
            elif next_agent == "technical":
                return "technical"
            elif next_agent == "usage":
                return "usage"
            elif next_agent == "escalation":
                return "escalation"
            else:
                # Router answered directly
                return END
        
        # Add conditional routing from router
        workflow.add_conditional_edges(
            "router",
            route_from_router,
            {
                "billing": "billing",
                "technical": "technical",
                "usage": "usage",
                "escalation": "escalation",
                END: END
            }
        )
        
        # All specialists end after responding
        workflow.add_edge("billing", END)
        workflow.add_edge("technical", END)
        workflow.add_edge("usage", END)
        workflow.add_edge("escalation", END)
        
        # Compile
        return workflow.compile()
    
    def run(self, message: str, conversation_id: str = None) -> AgentState:
        """Run conversation through graph"""
        initial_state = create_initial_state(
            message=message,
            conversation_id=conversation_id
        )
        
        print(f"\n{'='*70}")
        print(f"🚀 RUNNING SUPPORT GRAPH")
        print(f"{'='*70}")
        print(f"User: {message}")
        print(f"{'='*70}")
        
        final_state = self.app.invoke(initial_state)
        
        print(f"\n{'='*70}")
        print(f"✓ COMPLETE")
        print(f"{'='*70}")
        
        return final_state
    
    def get_response(self, message: str) -> str:
        """Simple interface"""
        result = self.run(message)
        return result.get("agent_response", "I'm not sure how to help with that.")


if __name__ == "__main__":
    print("=" * 70)
    print("TESTING FULL SUPPORT GRAPH - ALL AGENTS")
    print("=" * 70)
    
    graph = SupportGraph()
    
    test_cases = [
        ("I want to upgrade to premium", "billing"),
        ("My tasks are not syncing", "technical"),
        ("How do I invite team members?", "usage"),
        ("This is confusing", "escalation"),
    ]
    
    for i, (msg, expected) in enumerate(test_cases, 1):
        print(f"\n{'#'*70}")
        print(f"TEST {i}: {msg}")
        print(f"Expected: {expected.upper()} agent")
        print(f"{'#'*70}")
        
        result = graph.run(msg)
        
        agents = result.get('agent_history', [])
        intent = result.get('primary_intent', 'N/A')
        
        print(f"\n✓ Intent: {intent}")
        print(f"✓ Path: {' → '.join([a.upper() for a in agents])}")
        print(f"✓ Response: {result.get('agent_response', 'N/A')[:100]}...")
        
        if expected in agents:
            print(f"✓ PASS - Routed to correct agent")
        else:
            print(f"✗ FAIL - Expected {expected}, got {agents}")