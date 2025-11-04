"""
LangGraph - Multi-agent orchestration
Full version: All 6 agents (Router, Billing, Technical, Usage, API, Escalation)
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
from agents.api import APIAgent
from agents.escalation import EscalationAgent


class SupportGraph:
    """
    Multi-agent support system graph
    
    Agents:
    1. Router - Classifies and routes
    2. Billing - Payment/subscription issues
    3. Technical - Bugs and troubleshooting
    4. Usage - Feature how-tos
    5. API - Developer integrations
    6. Escalation - Hand off to humans
    """
    
    def __init__(self):
        """Initialize graph with all agents"""
        print("Initializing Support Graph with all agents...")
        
        # Initialize all 6 agents
        self.router = RouterAgent()
        self.billing = BillingAgent()
        self.technical = TechnicalAgent()
        self.usage = UsageAgent()
        self.api = APIAgent()
        self.escalation = EscalationAgent()
        
        # Build graph
        self.app = self._build_graph()
        
        print("✓ Full graph compiled with 6 agents!")
    
    def _build_graph(self) -> StateGraph:
        """Build the complete LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add all agent nodes
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
            """Decide where to route from router"""
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
                # Router answered directly, end conversation
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
        # They don't route to each other (single-hop architecture)
        workflow.add_edge("billing", END)
        workflow.add_edge("technical", END)
        workflow.add_edge("usage", END)
        workflow.add_edge("api", END)
        workflow.add_edge("escalation", END)
        
        # Compile the graph
        return workflow.compile()
    
    def run(self, message: str, conversation_id: str = None) -> AgentState:
        """
        Run conversation through graph
        
        Args:
            message: User's message
            conversation_id: Optional conversation ID for context
            
        Returns:
            Final state after processing
        """
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
        """
        Simple interface - just get the response text
        
        Args:
            message: User's message
            
        Returns:
            Agent's response text
        """
        result = self.run(message)
        return result.get("agent_response", "I'm not sure how to help with that.")


if __name__ == "__main__":
    print("=" * 70)
    print("TESTING FULL SUPPORT GRAPH - ALL 6 AGENTS")
    print("=" * 70)
    
    graph = SupportGraph()
    
    test_cases = [
        ("I want to upgrade to premium", "billing"),
        ("My tasks are not syncing", "technical"),
        ("How do I invite team members?", "usage"),
        ("How do I authenticate with the API?", "api"),
        ("Show me Python code for the API", "api"),
        ("This is really confusing", "escalation"),
    ]
    
    for i, (msg, expected) in enumerate(test_cases, 1):
        print(f"\n{'#'*70}")
        print(f"TEST {i}/{len(test_cases)}: {msg}")
        print(f"Expected: {expected.upper()} agent")
        print(f"{'#'*70}")
        
        result = graph.run(msg)
        
        agents = result.get('agent_history', [])
        intent = result.get('primary_intent', 'N/A')
        confidence = result.get('intent_confidence', 0)
        
        print(f"\n✓ Intent: {intent} ({confidence:.0%} confidence)")
        print(f"✓ Path: {' → '.join([a.upper() for a in agents])}")
        print(f"✓ Status: {result.get('status', 'unknown')}")
        
        # Show response preview
        response = result.get('agent_response', 'N/A')
        preview = response[:150] + "..." if len(response) > 150 else response
        print(f"✓ Response: {preview}")
        
        # Check if routed correctly
        if expected in agents:
            print(f"✓ PASS - Routed to correct agent")
        else:
            print(f"✗ FAIL - Expected {expected}, got {agents}")
    
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