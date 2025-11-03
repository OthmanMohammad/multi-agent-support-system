
"""
Billing Agent - Handles payments, subscriptions, invoices, refunds
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from state import AgentState
from agents.base import BaseAgent
from knowledge_base import search_articles


class BillingAgent(BaseAgent):
    """
    Billing Agent - Specialist for billing and payment issues.
    
    Handles:
    - Plan upgrades/downgrades
    - Refund requests
    - Invoices and payment info
    - Pricing questions
    """
    
    def __init__(self):
        super().__init__(
            agent_type="billing",
            model="claude-3-5-sonnet-20241022",  # Better reasoning
            temperature=0.3
        )
    
    def process(self, state: AgentState) -> AgentState:
        """
        Process billing-related requests
        
        Args:
            state: Current state
            
        Returns:
            Updated state with billing response
        """
        print(f"\n{'='*60}")
        print(f"💰 BILLING AGENT PROCESSING")
        print(f"{'='*60}")
        
        # Add to history
        state = self.add_to_history(state)
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        # Get message and intent
        message = state["current_message"]
        intent = state.get("primary_intent", "billing_upgrade")
        
        print(f"Message: {message[:100]}...")
        print(f"Intent: {intent}")
        
        # Search KB for billing articles
        kb_results = search_articles(
            message,
            category="billing",
            limit=3
        )
        state["kb_results"] = kb_results
        
        if kb_results:
            print(f"✓ Found {len(kb_results)} billing articles")
        
        # Generate response
        response = self.generate_response(message, intent, kb_results, state)
        
        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["next_agent"] = None  # End conversation
        state["status"] = "resolved"
        
        print(f"\n✓ Response generated ({len(response)} chars)")
        
        return state
    
    def generate_response(
        self,
        message: str,
        intent: str,
        kb_results: list,
        state: AgentState
    ) -> str:
        """
        Generate billing response using Claude
        
        Args:
            message: User's message
            intent: Classified intent
            kb_results: KB search results
            state: Current state
            
        Returns:
            Response text
        """
        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant billing articles:\n"
            for i, article in enumerate(kb_results, 1):
                kb_context += f"\n{i}. {article['title']}\n{article['content']}\n"
        
        # Get customer info
        customer_plan = state.get("customer_metadata", {}).get("plan", "free")
        
        system_prompt = f"""You are a billing specialist for a SaaS project management tool.

Current customer plan: {customer_plan}

Our pricing:
- FREE: $0/month - 3 projects, 5 team members, 100MB storage
- BASIC: $10/month per user - Unlimited projects, 25 team members, 10GB storage
- PREMIUM: $25/month per user - Everything + Advanced analytics, API access, 100GB storage

Guidelines:
1. Be helpful and friendly
2. Explain pricing clearly
3. For upgrades: Explain benefits and next steps
4. For refunds: Explain our 30-day money-back guarantee
5. For invoices: Explain how to access in Settings > Billing
6. Cite KB articles when relevant

Be concise but complete."""

        user_prompt = f"""Customer message: {message}

Intent: {intent}
{kb_context}

Provide a helpful response."""

        response = self.call_llm(system_prompt, user_prompt, max_tokens=500)
        
        return response


if __name__ == "__main__":
    # Test billing agent
    print("=" * 60)
    print("TESTING BILLING AGENT")
    print("=" * 60)
    
    from state import create_initial_state
    
    # Create test state (as if routed from router)
    state = create_initial_state("I want to upgrade to premium plan")
    state["primary_intent"] = "billing_upgrade"
    state["current_agent"] = "router"
    state["agent_history"] = ["router"]
    
    # Process with billing agent
    billing = BillingAgent()
    result = billing.process(state)
    
    print(f"\n{'='*60}")
    print("RESULT")
    print(f"{'='*60}")
    print(f"Response:\n{result['agent_response']}")
    print(f"\nStatus: {result['status']}")
    print(f"Next Agent: {result.get('next_agent', 'END')}")