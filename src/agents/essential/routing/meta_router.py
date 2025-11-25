"""
Meta Router Agent - Top-level domain classification.

Routes user messages to appropriate domain: Support, Sales, or Customer Success.
This is the entry point for all conversations in the multi-agent system.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-101)
"""

from typing import Dict, Any, Optional
import json
import time
import structlog

from src.agents.base.base_agent import BaseAgent, RoutingAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability, Domain
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@AgentRegistry.register("meta_router", tier="essential", category="routing")
class MetaRouter(RoutingAgent):
    """
    Meta Router - Top-level domain classifier.

    Routes messages to:
    - Support: Problems, how-to questions, billing issues, technical issues
    - Sales: Pricing, demos, upgrades (new customers), competitive questions
    - Customer Success: Value concerns, adoption issues, retention, expansion

    This is the FIRST agent in the routing chain. All conversations start here.
    """

    def __init__(self, **kwargs):
        """Initialize Meta Router with optimized configuration for fast routing."""
        config = AgentConfig(
            name="meta_router",
            type=AgentType.ROUTER,
             # Fast and cost-effective
            temperature=0.1,  # Low temperature for consistent routing
            max_tokens=200,   # Short responses for quick routing
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="meta_router"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="meta_router", agent_type="router")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for domain classification.

        Returns:
            System prompt with classification rules and examples
        """
        return """You are a meta router that classifies customer messages into business domains.

Your job is to classify each message into ONE domain:

**SUPPORT** - Customer has a problem or question
Examples:
- Technical issues (crashes, bugs, sync problems, performance)
- Billing issues (charges, invoices, payments, refunds)
- How-to questions (using features, setup, configuration)
- Account issues (login, password, access, security)
- Integration issues (API, webhooks, OAuth)
- Data issues (export, import, recovery)

**SALES** - Pricing, demos, upgrades (NEW customers), competitive questions
Examples:
- Pricing inquiries ("How much does Premium cost?")
- Demo requests ("Can I see a demo?")
- Plan upgrades from FREE users
- Competitive comparisons ("How do you compare to Asana?")
- Feature availability questions (pre-purchase)
- Trial questions from prospects

**CUSTOMER_SUCCESS** - Existing paying customers with value/adoption concerns
Examples:
- Not seeing value / considering cancellation
- Low engagement / team not using product
- Onboarding help for paid customers
- Expansion opportunities (upsell/cross-sell for existing customers)
- Renewal discussions
- Feature requests from engaged customers

**Customer Context**: {customer_context}

**Classification Rules**:
1. If customer has a PROBLEM → support
2. If customer wants to BUY or UPGRADE (and is on FREE plan) → sales
3. If PAYING customer questions VALUE or is at-risk → customer_success
4. If PAYING customer wants to upgrade → support (billing)
5. If ambiguous → default to support
6. Use customer context (plan, health_score, churn_risk) to inform decision

**Output Format** (JSON only, no extra text):
{{
    "domain": "support" | "sales" | "customer_success",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of why this domain",
    "next_agent": "support_domain_router" | "sales_domain_router" | "cs_domain_router"
}}

Be concise. Output ONLY valid JSON, no markdown or extra text."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Process the message and classify domain.

        This is the main entry point for all conversations. Classifies the message
        into one of three domains and routes to the appropriate domain router.

        Args:
            state: Current agent state with message and context

        Returns:
            Updated state with domain classification and routing decision
        """
        start_time = time.time()

        self.logger.info(
            "meta_router_processing_started",
            conversation_id=state.get("conversation_id"),
            message_preview=state.get("current_message", "")[:50]
        )

        try:
            # Update state with agent history
            state = self.update_state(state)

            # Get customer context (if available)
            customer_context = state.get("customer_metadata", {})

            # Format context for prompt
            context_str = self._format_customer_context(customer_context)

            # Build system prompt with context
            system_prompt = self._get_system_prompt().format(
                customer_context=context_str
            )

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("meta_router_empty_message")
                return self._handle_empty_message(state)

            # Get conversation history for context-aware routing
            conversation_history = self.get_conversation_context(state)

            self.logger.debug(
                "meta_router_conversation_context",
                history_length=len(conversation_history)
            )

            # Call LLM for classification with conversation history
            response = await self.call_llm(
                system_prompt=system_prompt,
                user_message=f"Classify this message:\n\n{message}",
                conversation_history=conversation_history
            )

            # Parse response
            classification = self._parse_response(response)

            # Add metadata
            latency_ms = int((time.time() - start_time) * 1000)
            classification["metadata"] = {
                "model": self.config.model,
                "latency_ms": latency_ms,
                "tokens_used": getattr(self, "_last_tokens_used", 0)
            }

            # Update state with classification results
            state = self._update_state_with_classification(state, classification)

            self.logger.info(
                "meta_router_classification_complete",
                domain=classification["domain"],
                confidence=classification["confidence"],
                next_agent=classification["next_agent"],
                latency_ms=latency_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "meta_router_failed",
                error=str(e),
                error_type=type(e).__name__,
                conversation_id=state.get("conversation_id")
            )

            # Fallback to support domain
            return self._handle_error(state, e)

    def _format_customer_context(self, context: Dict[str, Any]) -> str:
        """
        Format customer context for prompt injection.

        Args:
            context: Customer metadata dictionary

        Returns:
            Formatted context string for prompt
        """
        if not context:
            return "No customer context available"

        parts = []

        # Plan information
        if "plan" in context:
            parts.append(f"Plan: {context['plan']}")

        # Health score
        if "health_score" in context:
            score = context['health_score']
            parts.append(f"Health Score: {score}/100")

        # MRR (Monthly Recurring Revenue)
        if "mrr" in context:
            parts.append(f"MRR: ${context['mrr']}")

        # Churn risk
        if "churn_risk" in context:
            risk = context['churn_risk']
            risk_label = "high" if risk > 0.7 else "medium" if risk > 0.4 else "low"
            parts.append(f"Churn Risk: {risk_label} ({risk:.2f})")

        # Account age
        if "account_age_days" in context:
            days = context['account_age_days']
            parts.append(f"Account Age: {days} days")

        # Last login
        if "last_login" in context:
            parts.append(f"Last Login: {context['last_login']}")

        return "\n".join(parts) if parts else "No relevant context"

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured classification.

        Handles both JSON responses and text responses with fallback logic.

        Args:
            response: LLM response (should be JSON)

        Returns:
            Classification dictionary with domain, confidence, reasoning, next_agent

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # Remove markdown code blocks
                lines = cleaned_response.split("\n")
                cleaned_response = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                )

            # Try to parse as JSON
            classification = json.loads(cleaned_response)

            # Validate required fields
            required_fields = ["domain", "confidence", "reasoning"]
            for field in required_fields:
                if field not in classification:
                    raise ValueError(f"Missing required field: {field}")

            # Validate domain
            valid_domains = ["support", "sales", "customer_success"]
            if classification["domain"] not in valid_domains:
                self.logger.warning(
                    "meta_router_invalid_domain",
                    domain=classification["domain"],
                    valid_domains=valid_domains
                )
                # Default to support
                classification["domain"] = "support"

            # Add next_agent if not present
            if "next_agent" not in classification:
                domain = classification["domain"]
                classification["next_agent"] = f"{domain}_domain_router"

            # Ensure confidence is between 0 and 1
            classification["confidence"] = max(0.0, min(1.0, float(classification["confidence"])))

            return classification

        except json.JSONDecodeError as e:
            self.logger.warning(
                "meta_router_invalid_json",
                response_preview=response[:200],
                error=str(e)
            )

            # Try to extract domain from text (fallback)
            return self._extract_domain_from_text(response)

    def _extract_domain_from_text(self, response: str) -> Dict[str, Any]:
        """
        Extract domain from text response when JSON parsing fails.

        This is a fallback mechanism for robustness.

        Args:
            response: Text response from LLM

        Returns:
            Classification dictionary with extracted domain
        """
        response_lower = response.lower()

        # Try to find domain keywords
        if "customer_success" in response_lower or "customer success" in response_lower:
            domain = "customer_success"
        elif "sales" in response_lower:
            domain = "sales"
        elif "support" in response_lower:
            domain = "support"
        else:
            domain = "support"  # Default to support

        self.logger.info(
            "meta_router_fallback_extraction",
            domain=domain,
            method="text_analysis"
        )

        return {
            "domain": domain,
            "confidence": 0.6,  # Lower confidence for fallback
            "reasoning": "Fallback classification due to JSON parsing error",
            "next_agent": f"{domain}_domain_router"
        }

    def _update_state_with_classification(
        self,
        state: AgentState,
        classification: Dict[str, Any]
    ) -> AgentState:
        """
        Update agent state with classification results.

        Args:
            state: Current agent state
            classification: Classification results from LLM

        Returns:
            Updated agent state
        """
        state.update({
            "domain": classification["domain"],
            "domain_confidence": classification["confidence"],
            "domain_reasoning": classification["reasoning"],
            "next_agent": classification["next_agent"],
            "routing_metadata": classification.get("metadata", {})
        })

        return state

    def _handle_empty_message(self, state: AgentState) -> AgentState:
        """
        Handle edge case of empty message.

        Args:
            state: Current agent state

        Returns:
            Updated state with default routing to support
        """
        state.update({
            "domain": "support",
            "domain_confidence": 0.5,
            "domain_reasoning": "Empty message - defaulting to support",
            "next_agent": "support_domain_router",
            "routing_metadata": {"error": "empty_message"}
        })

        return state

    def _handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """
        Handle errors during classification with graceful fallback.

        Args:
            state: Current agent state
            error: Exception that occurred

        Returns:
            Updated state with fallback routing to support
        """
        state.update({
            "domain": "support",
            "domain_confidence": 0.5,
            "domain_reasoning": f"Error in classification: {str(error)}",
            "next_agent": "support_domain_router",
            "routing_metadata": {
                "error": str(error),
                "error_type": type(error).__name__
            }
        })

        return state

    async def classify_and_route(self, state: AgentState) -> AgentState:
        """
        Implementation of RoutingAgent abstract method.

        This is an alias for process() to satisfy the RoutingAgent interface.

        Args:
            state: Current agent state

        Returns:
            Updated state with routing decision
        """
        return await self.process(state)


# Helper function to create instance
def create_meta_router(**kwargs) -> MetaRouter:
    """
    Create MetaRouter instance.

    Args:
        **kwargs: Additional arguments passed to MetaRouter constructor

    Returns:
        Configured MetaRouter instance
    """
    return MetaRouter(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_meta_router():
        """Test Meta Router with sample messages."""
        print("=" * 60)
        print("TESTING META ROUTER AGENT")
        print("=" * 60)

        router = MetaRouter()

        # Test cases covering all three domains
        test_cases = [
            # Support domain
            {
                "message": "My app is crashing when I try to export data",
                "context": {"plan": "premium", "health_score": 85},
                "expected_domain": "support"
            },
            {
                "message": "I was charged twice this month",
                "context": {"plan": "basic", "mrr": 10},
                "expected_domain": "support"
            },
            {
                "message": "How do I reset my password?",
                "context": {"plan": "free"},
                "expected_domain": "support"
            },

            # Sales domain
            {
                "message": "How much does Premium cost for 50 users?",
                "context": {"plan": "free", "account_age_days": 5},
                "expected_domain": "sales"
            },
            {
                "message": "I'd like to schedule a demo of your product",
                "context": {"plan": "free"},
                "expected_domain": "sales"
            },
            {
                "message": "How does this compare to Asana?",
                "context": {"plan": "free"},
                "expected_domain": "sales"
            },

            # Customer Success domain
            {
                "message": "We're not getting the value we expected from the product",
                "context": {"plan": "premium", "health_score": 35, "churn_risk": 0.8},
                "expected_domain": "customer_success"
            },
            {
                "message": "Our team isn't really using the product",
                "context": {"plan": "basic", "health_score": 40},
                "expected_domain": "customer_success"
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test['message'][:50]}...")
            print(f"{'='*60}")

            state = create_initial_state(
                message=test["message"],
                context={"customer_metadata": test["context"]}
            )

            result = await router.process(state)

            print(f"\n✓ Domain: {result['domain']}")
            print(f"✓ Confidence: {result['domain_confidence']:.2%}")
            print(f"✓ Reasoning: {result['domain_reasoning']}")
            print(f"✓ Next Agent: {result['next_agent']}")
            print(f"✓ Latency: {result['routing_metadata'].get('latency_ms', 0)}ms")

            # Validate expectation
            if result['domain'] == test['expected_domain']:
                print(f"✓ PASS: Correctly classified as {test['expected_domain']}")
            else:
                print(f"✗ FAIL: Expected {test['expected_domain']}, got {result['domain']}")

    # Run tests
    asyncio.run(test_meta_router())
    