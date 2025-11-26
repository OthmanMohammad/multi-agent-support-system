"""
Sales Domain Router - Route sales queries to specialized sub-teams.

Routes sales domain queries to 4 specialized categories:
qualification, education, objection, progression.

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
        "education",  # Product demos, feature education
        "objection",  # Pricing concerns, competitor comparison
        "progression",  # Trial conversion, closing deals
    ]

    # Valid agent names for each category
    VALID_AGENTS = {
        "qualification": ["inbound_qualifier", "bant_qualifier"],
        "education": [
            "feature_explainer",
            "demo_scheduler",
            "value_proposition",
            "use_case_matcher",
            "roi_calculator",
        ],
        "objection": [
            "price_objection_handler",
            "competitor_comparison_handler",
            "integration_objection_handler",
            "security_objection_handler",
            "timing_objection_handler",
            "feature_gap_handler",
        ],
        "progression": ["closer", "trial_optimizer", "proposal_generator", "contract_negotiator"],
    }

    # Default agent for each category (fallback)
    DEFAULT_AGENTS = {
        "qualification": "inbound_qualifier",
        "education": "feature_explainer",
        "objection": "price_objection_handler",
        "progression": "closer",
    }

    def __init__(self, **kwargs):
        """Initialize Sales Domain Router."""
        config = AgentConfig(
            name="sales_domain_router",
            type=AgentType.ROUTER,
            temperature=0.1,  # Consistent routing
            max_tokens=200,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="sales_domain_router",
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="sales_domain_router", agent_type="router")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for sales domain routing.

        Returns:
            System prompt with routing taxonomy and specific agent selection
        """
        return """You are a sales domain routing system. Route sales queries to the SPECIFIC specialist agent.

**Available Sales Agents (choose exactly ONE):**

## QUALIFICATION Agents:
- **inbound_qualifier**: Initial inquiries, "tell me about your product", company info gathering
- **bant_qualifier**: Budget/Authority/Need/Timeline questions, serious buyer qualification

## EDUCATION Agents:
- **feature_explainer**: Feature questions, "what integrations do you have?", "how does X work?", capabilities
- **demo_scheduler**: Schedule demos, "can I see a demo?", demo requests
- **value_proposition**: ROI discussions, business value, benefits, outcomes
- **use_case_matcher**: Industry examples, success stories, "how do companies like us use this?"
- **roi_calculator**: Specific ROI calculations, cost savings, payback period

## OBJECTION Agents:
- **price_objection_handler**: "Too expensive", pricing concerns, need discounts, budget constraints
- **competitor_comparison_handler**: Competitor mentions (Trello, Asana, Monday, Jira), "vs X", switching from another tool
- **integration_objection_handler**: Integration concerns, "does it work with X?", API questions, connectivity
- **security_objection_handler**: Security concerns, compliance, data protection, SOC2, GDPR
- **timing_objection_handler**: "Not ready", "maybe later", timing concerns
- **feature_gap_handler**: Missing features, "do you have X?", feature limitations

## PROGRESSION Agents:
- **closer**: Ready to buy, "let's proceed", final purchase decision
- **trial_optimizer**: Trial conversion, extending trial, trial-related questions
- **proposal_generator**: Custom proposals, enterprise quotes, formal pricing
- **contract_negotiator**: Contract terms, legal review, custom agreements

**Routing Rules:**
1. Feature/capability questions → feature_explainer
2. Demo scheduling → demo_scheduler
3. Competitor mentions (Trello, Asana, Monday, Jira, etc.) → competitor_comparison_handler
4. Integration/API questions → integration_objection_handler (or feature_explainer if just exploring)
5. Pricing concerns → price_objection_handler
6. Security/compliance questions → security_objection_handler
7. Initial exploratory → inbound_qualifier
8. Ready to buy signals → closer

**Output Format (JSON only, no extra text):**
{{
    "agent": "feature_explainer",
    "category": "education",
    "confidence": 0.92,
    "reasoning": "Customer asking about integrations - this is a feature capabilities question"
}}

Output ONLY valid JSON. Choose exactly ONE agent."""

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
                state["next_agent"] = "escalation"  # Route to escalation as fallback
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

            # Get conversation history for context-aware routing
            conversation_history = self.get_conversation_context(state)

            self.logger.debug(
                "sales_router_conversation_context", history_length=len(conversation_history)
            )

            # Call LLM for routing
            prompt = f"""Route this sales query to the correct category.

Message: {message}

{context_str if context_str else ""}

Classify into: qualification, education, objection, or progression.
Consider any previous conversation context when making your routing decision."""

            response = await self.call_llm(
                system_prompt=self._get_system_prompt(),
                user_message=prompt,
                conversation_history=conversation_history,
            )

            # Parse response
            routing = self._parse_response(response)

            # Get agent and category from response
            agent = routing.get("agent", "").lower()
            category = routing.get("category", "qualification").lower()
            confidence = routing.get("confidence", 0.8)
            reasoning = routing.get("reasoning", "")

            # Validate category
            if category not in self.SALES_CATEGORIES:
                self.logger.warning(
                    "invalid_sales_category", category=category, defaulting_to="qualification"
                )
                category = "qualification"

            # Validate agent - must be in the valid agents list
            all_valid_agents = []
            for agents in self.VALID_AGENTS.values():
                all_valid_agents.extend(agents)

            if agent not in all_valid_agents:
                self.logger.warning(
                    "invalid_sales_agent",
                    agent=agent,
                    category=category,
                    defaulting_to=self.DEFAULT_AGENTS.get(category),
                )
                agent = self.DEFAULT_AGENTS.get(category, "inbound_qualifier")

            # Update state
            state["sales_category"] = category
            state["sales_category_confidence"] = confidence
            state["sales_category_reasoning"] = reasoning
            state["selected_agent"] = agent

            # Route directly to the specific agent
            state["next_agent"] = agent

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            state["sales_routing_metadata"] = {
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model,
            }

            self.logger.info(
                "sales_query_routed",
                category=category,
                next_agent=state["next_agent"],
                confidence=confidence,
                latency_ms=latency_ms,
            )

            return state

        except Exception as e:
            self.logger.error("sales_routing_failed", error=str(e), error_type=type(e).__name__)

            # Fallback to qualification category
            state["sales_category"] = "qualification"
            state["sales_category_confidence"] = 0.5
            state["sales_category_reasoning"] = "Fallback due to routing error"
            state["next_agent"] = "escalation"  # Route to escalation as fallback
            return state

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
                self.logger.warning("sales_router_invalid_type", type=type(routing).__name__)
                return {"category": "qualification", "confidence": 0.5}

            return routing

        except json.JSONDecodeError as e:
            self.logger.warning(
                "sales_router_invalid_json", response_preview=response[:100], error=str(e)
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
                "expected_category": "qualification",
            },
            {
                "message": "Can you show me how the reporting feature works?",
                "context": {"plan": "free"},
                "expected_category": "education",
            },
            {
                "message": "How does your pricing compare to Asana?",
                "context": {"plan": "free"},
                "expected_category": "objection",
            },
            {
                "message": "We're ready to move forward with the Enterprise plan",
                "context": {"plan": "free", "team_size": 100},
                "expected_category": "progression",
            },
            {
                "message": "Can I schedule a demo for next week?",
                "context": {},
                "expected_category": "education",
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
            print(f"  Category: {result['sales_category']}")
            print(f"  Confidence: {result['sales_category_confidence']:.2%}")
            print(f"  Expected: {test['expected_category']}")
            print(
                f"  Match: {'✓' if result['sales_category'] == test['expected_category'] else '✗'}"
            )

    # Run tests
    asyncio.run(test_sales_domain_router())
