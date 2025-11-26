"""
Customer Success Domain Router - Route CS queries to specialized sub-teams.

Routes customer success domain queries to 5 specialized categories:
health, onboarding, adoption, retention, expansion.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-105)
"""

import json
from datetime import datetime
from typing import Any

import structlog

from src.agents.base.agent_types import AgentCapability, AgentType
from src.agents.base.base_agent import AgentConfig, RoutingAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.workflow.state import AgentState

logger = structlog.get_logger(__name__)


@AgentRegistry.register("cs_domain_router", tier="essential", category="routing")
class CSDomainRouter(RoutingAgent):
    """
    Customer Success Domain Router - Route to specialized CS categories.

    Routes to 5 customer success categories:
    - health: Account health monitoring, churn risk, low engagement
    - onboarding: New customer setup, initial training, getting started
    - adoption: Feature adoption, usage optimization, best practices
    - retention: Renewal management, value realization, satisfaction
    - expansion: Upsell opportunities, additional users, new features
    """

    # Valid CS categories
    CS_CATEGORIES = [
        "health",  # Account health, churn risk
        "onboarding",  # Initial setup, training
        "adoption",  # Feature usage, optimization
        "retention",  # Renewals, satisfaction
        "expansion",  # Upsell, growth opportunities
    ]

    def __init__(self, **kwargs):
        """Initialize CS Domain Router."""
        config = AgentConfig(
            name="cs_domain_router",
            type=AgentType.ROUTER,
            temperature=0.1,  # Consistent routing
            max_tokens=200,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="cs_domain_router",
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="cs_domain_router", agent_type="router")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for CS domain routing.

        Returns:
            System prompt with routing taxonomy
        """
        return """You are a customer success domain routing system. Classify CS queries into one of 5 categories.

**Customer Success Categories:**

1. **health**
   - Low engagement: not using product, low activity
   - Churn risk: considering leaving, negative sentiment
   - Value concerns: not seeing ROI, questioning worth
   - Dissatisfaction: unhappy with product/service
   - At-risk signals: reduced usage, missed meetings
   - Competitive threats: looking at alternatives
   - Health score decline: metrics trending down

2. **onboarding**
   - Initial setup: getting started, first steps
   - Account configuration: settings, preferences
   - Team training: educating users, workshops
   - Implementation: deployment, rollout planning
   - Migration: importing data from previous tool
   - First 30/60/90 days: early stage customers
   - Quick wins: achieving initial value

3. **adoption**
   - Feature adoption: using advanced features
   - Usage optimization: improving workflows
   - Best practices: doing things the right way
   - Power user training: advanced techniques
   - Workflow automation: efficiency improvements
   - Integration setup: connecting other tools
   - Engagement increase: getting team to use more

4. **retention**
   - Renewal management: contract coming up
   - Value realization: demonstrating ROI
   - Success metrics: showing progress, wins
   - Relationship building: executive engagement
   - Check-ins: quarterly business reviews
   - Contract concerns: terms, pricing, commitment
   - Competitive defense: addressing competitor threats

5. **expansion**
   - Upsell opportunities: upgrade to higher plan
   - Cross-sell: additional products/features
   - Seat expansion: adding more users
   - New use cases: expanding to other teams/departments
   - Premium features: interested in advanced capabilities
   - Success-based growth: ready for more due to success
   - Land and expand: growing within organization

**Routing Rules:**
- Health score < 50 or churn risk > 0.6 → health
- Account age < 90 days → onboarding
- Low feature usage, optimization questions → adoption
- Renewal within 90 days, satisfaction concerns → retention
- Asking about higher plans, more seats → expansion
- Consider context signals carefully (health score, plan, team size)

**Context Considerations:**
- **Health score**: <40 = health, 40-70 = varies, >70 = adoption/expansion
- **Churn risk**: >0.6 = health, 0.3-0.6 = retention, <0.3 = expansion
- **Plan**: enterprise customers → retention focus
- **Account age**: new → onboarding, established → adoption/expansion
- **Sentiment**: negative → health, positive → expansion

**Output Format (JSON only, no extra text):**
{{
    "category": "health",
    "confidence": 0.88,
    "reasoning": "Low health score (25) and high churn risk (0.85) indicate at-risk account"
}}

Output ONLY valid JSON. Choose exactly ONE category."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Route CS query to specialized category.

        Args:
            state: Current agent state with message and context

        Returns:
            Updated state with cs_category field
        """
        try:
            start_time = datetime.now()

            # Update state with agent history
            state = self.update_state(state)

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("cs_router_empty_message")
                state["cs_category"] = "adoption"
                state["cs_category_confidence"] = 0.5
                state["next_agent"] = "escalation"  # Route to escalation as fallback
                return state

            # Build context for routing (CRITICAL for CS routing)
            context_parts = []

            customer_metadata = state.get("customer_metadata", {})

            # Health signals (very important)
            if "health_score" in customer_metadata:
                health = customer_metadata["health_score"]
                context_parts.append(f"Health score: {health}/100")

            if "churn_risk" in customer_metadata:
                risk = customer_metadata["churn_risk"]
                context_parts.append(f"Churn risk: {int(risk * 100)}%")

            # Account context
            if "plan" in customer_metadata:
                context_parts.append(f"Plan: {customer_metadata['plan']}")

            if "account_age_days" in customer_metadata:
                age = customer_metadata["account_age_days"]
                context_parts.append(f"Account age: {age} days")

            if "team_size" in customer_metadata:
                context_parts.append(f"Team size: {customer_metadata['team_size']}")

            # Include intent if available
            if state.get("intent_category"):
                context_parts.append(f"Intent: {state['intent_category']}")

            # Include sentiment if available
            if state.get("emotion"):
                context_parts.append(f"Emotion: {state['emotion']}")
                context_parts.append(f"Satisfaction: {state.get('satisfaction', 0.5):.2f}")

            context_str = "\n".join(context_parts) if context_parts else ""

            # Get conversation history for context-aware routing
            conversation_history = self.get_conversation_context(state)

            self.logger.debug(
                "cs_router_conversation_context", history_length=len(conversation_history)
            )

            # Call LLM for routing
            prompt = f"""Route this customer success query to the correct category.

Message: {message}

{context_str if context_str else ""}

Classify into: health, onboarding, adoption, retention, or expansion.
Consider any previous conversation context when making your routing decision."""

            response = await self.call_llm(
                system_prompt=self._get_system_prompt(),
                user_message=prompt,
                conversation_history=conversation_history,
            )

            # Parse response
            routing = self._parse_response(response)

            # Validate category
            category = routing.get("category", "adoption").lower()
            if category not in self.CS_CATEGORIES:
                self.logger.warning(
                    "invalid_cs_category", category=category, defaulting_to="adoption"
                )
                category = "adoption"

            # Override based on strong context signals
            category = self._apply_context_overrides(category, customer_metadata, state)

            confidence = routing.get("confidence", 0.8)
            reasoning = routing.get("reasoning", "")

            # Update state
            state["cs_category"] = category
            state["cs_category_confidence"] = confidence
            state["cs_category_reasoning"] = reasoning

            # Map category to actual agent for routing
            category_to_agent = {
                "health": "cs_health",  # health_score
                "onboarding": "cs_onboarding",  # onboarding_coordinator
                "adoption": "cs_adoption",  # feature_adoption
                "retention": "cs_retention",  # renewal_manager
                "expansion": "cs_expansion",  # upsell_identifier
            }
            state["next_agent"] = category_to_agent.get(category, "escalation")

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            state["cs_routing_metadata"] = {
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model,
            }

            self.logger.info(
                "cs_query_routed",
                category=category,
                next_agent=state["next_agent"],
                confidence=confidence,
                latency_ms=latency_ms,
            )

            return state

        except Exception as e:
            self.logger.error("cs_routing_failed", error=str(e), error_type=type(e).__name__)

            # Fallback to adoption category
            state["cs_category"] = "adoption"
            state["cs_category_confidence"] = 0.5
            state["cs_category_reasoning"] = "Fallback due to routing error"
            state["next_agent"] = "escalation"  # Route to escalation as fallback
            return state

    def _apply_context_overrides(
        self, category: str, customer_metadata: dict[str, Any], state: AgentState
    ) -> str:
        """
        Apply context-based overrides to routing decision.

        Args:
            category: Initial category from LLM
            customer_metadata: Customer context
            state: Current state

        Returns:
            Potentially overridden category
        """
        # Critical health signals override other decisions
        health_score = customer_metadata.get("health_score", 100)
        churn_risk = customer_metadata.get("churn_risk", 0.0)

        # High churn risk or very low health → always route to health
        if churn_risk > 0.7 or health_score < 35:
            self.logger.info(
                "cs_router_health_override",
                original_category=category,
                health_score=health_score,
                churn_risk=churn_risk,
            )
            return "health"

        # Very new accounts → onboarding
        account_age = customer_metadata.get("account_age_days", 999)
        if account_age < 30:
            return "onboarding"

        return category

    def _parse_response(self, response: str) -> dict[str, Any]:
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
                    line for line in lines if not line.strip().startswith("```")
                )

            # Parse JSON
            routing = json.loads(cleaned_response)

            # Ensure it's a dict
            if not isinstance(routing, dict):
                self.logger.warning("cs_router_invalid_type", type=type(routing).__name__)
                return {"category": "adoption", "confidence": 0.5}

            return routing

        except json.JSONDecodeError as e:
            self.logger.warning(
                "cs_router_invalid_json", response_preview=response[:100], error=str(e)
            )
            return {"category": "adoption", "confidence": 0.5}


# Helper function to create instance
def create_cs_domain_router(**kwargs) -> CSDomainRouter:
    """
    Create CSDomainRouter instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured CSDomainRouter instance
    """
    return CSDomainRouter(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test_cs_domain_router():
        """Test CS Domain Router with sample queries."""
        print("=" * 60)
        print("TESTING CS DOMAIN ROUTER")
        print("=" * 60)

        router = CSDomainRouter()

        # Test cases covering all categories
        test_cases = [
            {
                "message": "Our team isn't really using the product anymore",
                "context": {"plan": "enterprise", "health_score": 25, "churn_risk": 0.85},
                "expected_category": "health",
            },
            {
                "message": "We just signed up, how do we get started?",
                "context": {"plan": "premium", "account_age_days": 5},
                "expected_category": "onboarding",
            },
            {
                "message": "How can we use automation features more effectively?",
                "context": {"plan": "premium", "health_score": 65},
                "expected_category": "adoption",
            },
            {
                "message": "Our contract is up for renewal next month",
                "context": {"plan": "enterprise", "health_score": 75},
                "expected_category": "retention",
            },
            {
                "message": "We want to add 50 more seats and explore Enterprise features",
                "context": {"plan": "premium", "team_size": 100, "health_score": 85},
                "expected_category": "expansion",
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'=' * 60}")
            print(f"TEST CASE {i}: {test['message']}")
            print(f"{'=' * 60}")

            state = create_initial_state(
                message=test["message"], context={"customer_metadata": test.get("context", {})}
            )

            result = await router.process(state)

            print("\n✓ Routing Decision:")
            print(f"  Category: {result['cs_category']}")
            print(f"  Confidence: {result['cs_category_confidence']:.2%}")
            print(f"  Expected: {test['expected_category']}")
            print(f"  Match: {'✓' if result['cs_category'] == test['expected_category'] else '✗'}")

    # Run tests
    asyncio.run(test_cs_domain_router())
