"""
Support Domain Router - Route support queries to specialized sub-teams.

Routes support domain queries to 5 specialized categories:
billing, technical, usage, integration, account.

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


@AgentRegistry.register("support_domain_router", tier="essential", category="routing")
class SupportDomainRouter(RoutingAgent):
    """
    Support Domain Router - Route to specialized support categories.

    Routes to 5 support categories:
    - billing: Subscriptions, payments, invoices, refunds, plan changes
    - technical: Bugs, errors, performance, crashes, sync issues
    - usage: How-to questions, feature education, best practices
    - integration: Third-party integrations, API, webhooks, SSO
    - account: Login, permissions, security, data management
    """

    # Valid support categories
    SUPPORT_CATEGORIES = [
        "billing",      # Subscription, payment, invoice issues
        "technical",    # Bugs, errors, performance problems
        "usage",        # How-to, feature questions
        "integration",  # Third-party integrations, API
        "account"       # Login, permissions, security
    ]

    def __init__(self, **kwargs):
        """Initialize Support Domain Router."""
        config = AgentConfig(
            name="support_domain_router",
            type=AgentType.ROUTER,
            temperature=0.1,  # Consistent routing
            max_tokens=200,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="support_domain_router"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="support_domain_router", agent_type="router")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for support domain routing.

        Returns:
            System prompt with routing taxonomy
        """
        return """You are a support domain routing system. Classify support queries into one of 5 categories.

**Support Categories:**

1. **billing**
   - Subscription management: upgrade, downgrade, cancel, pause, reactivate
   - Payment issues: failed payment, update card, billing cycle
   - Invoices: request invoice, invoice questions, tax documents
   - Pricing: plan comparison, discounts, custom pricing
   - Refunds: refund request, credit request

2. **technical**
   - Bugs: crashes, errors, freezes, unexpected behavior
   - Performance: slow loading, timeouts, lag
   - Sync issues: data not syncing, conflicts, delays
   - Platform issues: mobile, web, desktop app problems
   - Data loss: missing data, corruption

3. **usage**
   - How-to questions: "How do I...", feature usage
   - Feature education: explaining features, capabilities
   - Best practices: workflow optimization, tips
   - Training: onboarding, tutorials, documentation
   - Feature requests: suggestions, enhancement ideas

4. **integration**
   - Third-party integrations: Slack, Salesforce, GitHub, etc.
   - API: API access, endpoints, authentication
   - Webhooks: webhook setup, debugging
   - SSO: single sign-on, SAML, OAuth
   - Import/Export: data migration, CSV export

5. **account**
   - Login issues: can't login, password reset, 2FA
   - Permissions: user roles, access control, sharing
   - Security: account security, suspicious activity
   - Data management: delete account, export data, GDPR
   - User management: add/remove users, team management

**Routing Rules:**
- If message mentions money/payment/subscription → billing
- If message mentions crash/error/bug/not working → technical
- If message mentions "how do I" or "can I" → usage
- If message mentions third-party tool or API → integration
- If message mentions login/password/permissions → account
- Consider extracted entities (problem, integration, action, etc.)
- Default to technical if unclear and negative sentiment
- Default to usage if unclear and neutral/positive sentiment

**Context Considerations:**
- Intent category can help disambiguate
- Extracted entities (integration, action, problem) provide clues
- Urgency doesn't change category, but note it

**Output Format (JSON only, no extra text):**
{{
    "category": "technical",
    "confidence": 0.95,
    "reasoning": "Message describes crash and error, clearly technical issue"
}}

Output ONLY valid JSON. Choose exactly ONE category."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Route support query to specialized category.

        Args:
            state: Current agent state with message and context

        Returns:
            Updated state with support_category field
        """
        try:
            start_time = datetime.now()

            # Update state with agent history
            state = self.update_state(state)

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("support_router_empty_message")
                state["support_category"] = "usage"
                state["support_category_confidence"] = 0.5
                state["next_agent"] = "usage"  # Route to usage agent as fallback
                return state

            # Build context for routing
            context_parts = []

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
                context_parts.append(f"Urgency: {state.get('urgency', 'medium')}")

            context_str = "\n".join(context_parts) if context_parts else ""

            # Call LLM for routing
            prompt = f"""Route this support query to the correct category.

Message: {message}

{context_str if context_str else ""}

Classify into: billing, technical, usage, integration, or account."""

            response = await self.call_llm(
                system_prompt=self._get_system_prompt(),
                user_message=prompt
            )

            # Parse response
            routing = self._parse_response(response)

            # Validate category
            category = routing.get("category", "usage").lower()
            if category not in self.SUPPORT_CATEGORIES:
                self.logger.warning(
                    "invalid_support_category",
                    category=category,
                    defaulting_to="usage"
                )
                category = "usage"

            confidence = routing.get("confidence", 0.8)
            reasoning = routing.get("reasoning", "")

            # Update state
            state["support_category"] = category
            state["support_category_confidence"] = confidence
            state["support_category_reasoning"] = reasoning

            # Map category to actual agent for routing
            category_to_agent = {
                "billing": "billing",
                "technical": "technical",
                "usage": "usage",
                "integration": "api",
                "account": "technical"  # Account issues go to technical
            }
            state["next_agent"] = category_to_agent.get(category, "escalation")

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            state["support_routing_metadata"] = {
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model
            }

            self.logger.info(
                "support_query_routed",
                category=category,
                next_agent=state["next_agent"],
                confidence=confidence,
                latency_ms=latency_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "support_routing_failed",
                error=str(e),
                error_type=type(e).__name__
            )

            # Fallback to usage category
            state["support_category"] = "usage"
            state["support_category_confidence"] = 0.5
            state["support_category_reasoning"] = "Fallback due to routing error"
            state["next_agent"] = "usage"  # Route to usage agent as fallback
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
                    "support_router_invalid_type",
                    type=type(routing).__name__
                )
                return {"category": "usage", "confidence": 0.5}

            return routing

        except json.JSONDecodeError as e:
            self.logger.warning(
                "support_router_invalid_json",
                response_preview=response[:100],
                error=str(e)
            )
            return {"category": "usage", "confidence": 0.5}


# Helper function to create instance
def create_support_domain_router(**kwargs) -> SupportDomainRouter:
    """
    Create SupportDomainRouter instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured SupportDomainRouter instance
    """
    return SupportDomainRouter(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_support_domain_router():
        """Test Support Domain Router with sample queries."""
        print("=" * 60)
        print("TESTING SUPPORT DOMAIN ROUTER")
        print("=" * 60)

        router = SupportDomainRouter()

        # Test cases covering all categories
        test_cases = [
            {
                "message": "I want to upgrade my plan to Premium",
                "expected_category": "billing"
            },
            {
                "message": "The app crashes when I try to export data",
                "expected_category": "technical"
            },
            {
                "message": "How do I create a new project?",
                "expected_category": "usage"
            },
            {
                "message": "The Slack integration isn't working",
                "expected_category": "integration"
            },
            {
                "message": "I can't login to my account",
                "expected_category": "account"
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test['message']}")
            print(f"{'='*60}")

            state = create_initial_state(message=test["message"])

            result = await router.process(state)

            print(f"\n✓ Routing Decision:")
            print(f"  Category: {result['support_category']}")
            print(f"  Confidence: {result['support_category_confidence']:.2%}")
            print(f"  Expected: {test['expected_category']}")
            print(f"  Match: {'✓' if result['support_category'] == test['expected_category'] else '✗'}")

    # Run tests
    asyncio.run(test_support_domain_router())