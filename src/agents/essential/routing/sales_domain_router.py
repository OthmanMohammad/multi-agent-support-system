"""
Sales Domain Router - Route sales queries to specialized sub-teams.

Routes sales domain queries to 4 specialized categories:
qualification, education, objection, progression.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-105)
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime
import structlog

from src.agents.base.base_agent import RoutingAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@AgentRegistry.register("sales_domain_router", tier="essential", category="routing")
class SalesDomainRouter(RoutingAgent):
    """
    Sales Domain Router - Route to specialized sales categories.

    Routes to 4 sales categories:
    - qualification: Needs assessment, budget, timeline, fit evaluation
    - education: Product demos, feature education, use cases, value prop
    - objection: Pricing concerns, competitor comparisons, feature gaps
    - progression: Trial conversion, contract negotiation, closing
    """

    # Valid sales categories
    SALES_CATEGORIES = [
        "qualification",  # Needs assessment, fit evaluation
        "education",      # Product demos, feature education
        "objection",      # Pricing concerns, competitor comparison
        "progression"     # Trial conversion, closing deals
    ]

    def __init__(self, **kwargs):
        """Initialize Sales Domain Router."""
        config = AgentConfig(
            name="sales_domain_router",
            type=AgentType.ROUTER,
            model="claude-3-haiku-20240307",
            temperature=0.1,  # Consistent routing
            max_tokens=200,
            capabilities=[
                AgentCapability.ROUTING,
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="sales_domain_router"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="sales_domain_router", agent_type="router")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for sales domain routing.

        Returns:
            System prompt with routing taxonomy
        """
        return """You are a sales domain routing system. Classify sales queries into one of 4 categories.

**Sales Categories:**

1. **qualification**
   - Needs assessment: understanding requirements, pain points
   - Budget evaluation: pricing inquiry, budget discussions
   - Timeline: when they need solution, urgency
   - Decision-making: stakeholders, buying process
   - Fit evaluation: is product right for their needs
   - Company info: team size, industry, use case
   - Initial inquiry: "tell me about your product"

2. **education**
   - Product demos: schedule demo, see product in action
   - Feature education: explain specific features, capabilities
   - Use cases: industry examples, success stories
   - Value proposition: ROI, benefits, outcomes
   - Comparison sheets: feature matrices, what's included
   - Documentation: guides, videos, tutorials
   - Free trial: how to start, trial features

3. **objection**
   - Pricing concerns: too expensive, need discount
   - Competitor comparison: vs Asana, vs Monday.com
   - Feature gaps: missing features, limitations
   - Risk concerns: security, reliability, uptime
   - Implementation concerns: migration, setup difficulty
   - Contract terms: length, cancellation, flexibility
   - Trust issues: company stability, customer support

4. **progression**
   - Trial conversion: ready to buy after trial
   - Plan selection: which plan to choose
   - Contract negotiation: custom pricing, terms
   - Deal closing: ready to purchase, final questions
   - Expansion: add seats, upgrade plan
   - Procurement: purchase order, legal review
   - Commitment signals: "let's move forward", "send contract"

**Routing Rules:**
- Initial exploratory questions → qualification
- "Show me", "demo", "how does X work" → education
- "Too expensive", "vs [competitor]", "concerned about" → objection
- "Ready to buy", "let's proceed", plan selection → progression
- Consider customer plan (free → qualification, paid → progression)
- Consider extracted entities (competitor → objection, amount → qualification/objection)

**Context Considerations:**
- Plan tier: free/trial → qualification/education, paid → progression
- Team size: large teams suggest serious buyers → progression
- Extracted entities provide strong signals
- Emotion: excited → progression, concerned → objection

**Output Format (JSON only, no extra text):**
{{
    "category": "qualification",
    "confidence": 0.92,
    "reasoning": "Customer asking about product fit and team size, classic qualification questions"
}}

Output ONLY valid JSON. Choose exactly ONE category."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Route sales query to specialized category.

        Args:
            state: Current agent state with message and context

        Returns:
            Updated state with sales_category field
        """
        try:
            start_time = datetime.now()

            # Update state with agent history
            state = self.update_state(state)

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("sales_router_empty_message")
                state["sales_category"] = "qualification"
                state["sales_category_confidence"] = 0.5
                return state

            # Build context for routing
            context_parts = []

            # Include customer plan (strong signal)
            customer_metadata = state.get("customer_metadata", {})
            plan = customer_metadata.get("plan", "unknown")
            if plan != "unknown":
                context_parts.append(f"Plan: {plan}")

            if customer_metadata.get("team_size"):
                context_parts.append(f"Team size: {customer_metadata['team_size']}")

            # Include intent if available
            if state.get("intent_category"):
                context_parts.append(f"Intent: {state['intent_category']}")

            # Include extracted entities if available
            if state.get("extracted_entities"):
                entities = state["extracted_entities"]
                context_parts.append(f"Entities: {json.dumps(entities)}")

            # Include sentiment if available
            if state.get("emotion"):
                context_parts.append(f"Emotion: {state['emotion']}")

            context_str = "\n".join(context_parts) if context_parts else ""

            # Call LLM for routing
            prompt = f"""Route this sales query to the correct category.

Message: {message}

{context_str if context_str else ""}

Classify into: qualification, education, objection, or progression."""

            response = await self.call_llm(
                system_prompt=self._get_system_prompt(),
                user_message=prompt
            )

            # Parse response
            routing = self._parse_response(response)

            # Validate category
            category = routing.get("category", "qualification").lower()
            if category not in self.SALES_CATEGORIES:
                self.logger.warning(
                    "invalid_sales_category",
                    category=category,
                    defaulting_to="qualification"
                )
                category = "qualification"

            confidence = routing.get("confidence", 0.8)
            reasoning = routing.get("reasoning", "")

            # Update state
            state["sales_category"] = category
            state["sales_category_confidence"] = confidence
            state["sales_category_reasoning"] = reasoning

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            state["sales_routing_metadata"] = {
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model
            }

            self.logger.info(
                "sales_query_routed",
                category=category,
                confidence=confidence,
                latency_ms=latency_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "sales_routing_failed",
                error=str(e),
                error_type=type(e).__name__
            )

            # Fallback to qualification category
            state["sales_category"] = "qualification"
            state["sales_category_confidence"] = 0.5
            state["sales_category_reasoning"] = "Fallback due to routing error"
            return state

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into routing decision.

        Args:
            response: LLM response (should be JSON)

        Returns:
            Dictionary with category and confidence
        """
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                lines = cleaned_response.split("\n")
                cleaned_response = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                )

            # Parse JSON
            routing = json.loads(cleaned_response)

            # Ensure it's a dict
            if not isinstance(routing, dict):
                self.logger.warning(
                    "sales_router_invalid_type",
                    type=type(routing).__name__
                )
                return {"category": "qualification", "confidence": 0.5}

            return routing

        except json.JSONDecodeError as e:
            self.logger.warning(
                "sales_router_invalid_json",
                response_preview=response[:100],
                error=str(e)
            )
            return {"category": "qualification", "confidence": 0.5}


# Helper function to create instance
def create_sales_domain_router(**kwargs) -> SalesDomainRouter:
    """
    Create SalesDomainRouter instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured SalesDomainRouter instance
    """
    return SalesDomainRouter(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_sales_domain_router():
        """Test Sales Domain Router with sample queries."""
        print("=" * 60)
        print("TESTING SALES DOMAIN ROUTER")
        print("=" * 60)

        router = SalesDomainRouter()

        # Test cases covering all categories
        test_cases = [
            {
                "message": "What are your pricing options for a team of 50?",
                "context": {"plan": "free"},
                "expected_category": "qualification"
            },
            {
                "message": "Can you show me how the reporting feature works?",
                "context": {"plan": "free"},
                "expected_category": "education"
            },
            {
                "message": "How does your pricing compare to Asana?",
                "context": {"plan": "free"},
                "expected_category": "objection"
            },
            {
                "message": "We're ready to move forward with the Enterprise plan",
                "context": {"plan": "free", "team_size": 100},
                "expected_category": "progression"
            },
            {
                "message": "Can I schedule a demo for next week?",
                "context": {},
                "expected_category": "education"
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test['message']}")
            print(f"{'='*60}")

            state = create_initial_state(
                message=test["message"],
                context={"customer_metadata": test.get("context", {})}
            )

            result = await router.process(state)

            print(f"\n✓ Routing Decision:")
            print(f"  Category: {result['sales_category']}")
            print(f"  Confidence: {result['sales_category_confidence']:.2%}")
            print(f"  Expected: {test['expected_category']}")
            print(f"  Match: {'✓' if result['sales_category'] == test['expected_category'] else '✗'}")

    # Run tests
    asyncio.run(test_sales_domain_router())
