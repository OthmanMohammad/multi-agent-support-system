"""
Billing Agent - Handles payments, subscriptions, invoices, refunds.

Specialist for all billing-related inquiries including upgrades,
downgrades, refunds, invoices, and pricing questions.
"""

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("billing_agent", tier="essential", category="billing")
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
        config = AgentConfig(
            name="billing_agent",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE
            ],
            kb_category="billing",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process billing-related requests.

        Args:
            state: Current state

        Returns:
            Updated state with billing response
        """
        self.logger.info("billing_agent_processing_started")

        # Update state
        state = self.update_state(state)

        # Get message and intent
        message = state["current_message"]
        intent = state.get("primary_intent", "billing_upgrade")

        self.logger.debug(
            "billing_processing_message",
            message_preview=message[:100],
            intent=intent,
            turn_count=state["turn_count"]
        )

        # Search KB for billing articles
        kb_results = await self.search_knowledge_base(
            message,
            category="billing",
            limit=3
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info(
                "billing_kb_articles_found",
                count=len(kb_results),
                top_score=kb_results[0].get("similarity_score", 0) if kb_results else 0
            )
        else:
            self.logger.warning(
                "billing_no_kb_articles_found",
                intent=intent
            )

        # Generate response
        response = await self.generate_response(message, intent, kb_results, state)

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["primary_intent"] = intent  # Track primary intent
        state["intent_confidence"] = 0.9  # Track confidence in intent classification
        state["next_agent"] = None  # End conversation
        state["status"] = "resolved"

        self.logger.info(
            "billing_response_generated",
            response_length=len(response),
            status="resolved"
        )

        return state

    async def generate_response(
        self,
        message: str,
        intent: str,
        kb_results: list,
        state: AgentState
    ) -> str:
        """
        Generate billing response using Claude.

        Args:
            message: User's message
            intent: Classified intent
            kb_results: KB search results
            state: Current state

        Returns:
            Response text
        """
        self.logger.debug(
            "billing_response_generation_started",
            intent=intent,
            kb_articles_count=len(kb_results)
        )

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

        response = await self.call_llm(system_prompt, user_prompt, max_tokens=500)

        self.logger.debug(
            "billing_llm_response_received",
            response_length=len(response)
        )

        return response


if __name__ == "__main__":
    # Test billing agent
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING BILLING AGENT")
        print("=" * 60)

        # Create test state (as if routed from router)
        state = create_initial_state("I want to upgrade to premium plan")
        state["primary_intent"] = "billing_upgrade"
        state["current_agent"] = "router"
        state["agent_history"] = ["router"]

        # Process with billing agent
        billing = BillingAgent()
        result = await billing.process(state)

        print(f"\n{'='*60}")
        print("RESULT")
        print(f"{'='*60}")
        print(f"Response:\n{result['agent_response']}")
        print(f"\nStatus: {result['status']}")
        print(f"Next Agent: {result.get('next_agent', 'END')}")

    asyncio.run(test())
