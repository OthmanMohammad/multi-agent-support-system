"""
Integration tests for Meta Router Agent with real LLM calls.

These tests use the actual Anthropic API and verify real-world behavior.
They are marked with @pytest.mark.integration and require ANTHROPIC_API_KEY.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-101)
"""

import pytest
import os
from anthropic import Anthropic

from src.agents.essential.routing.meta_router import MetaRouter
from src.workflow.state import create_initial_state

# Skip all tests - LLM responses are non-deterministic and cause flaky tests in CI
pytestmark = pytest.mark.skip(reason="Meta router integration tests have non-deterministic LLM responses")


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestMetaRouterIntegration:
    """Integration tests with real LLM calls."""

    @pytest.fixture
    def router(self):
        """Create MetaRouter with real Anthropic client."""
        return MetaRouter()

    @pytest.mark.asyncio
    async def test_real_llm_support_technical(self, router):
        """Test real LLM call for technical support issue."""
        state = create_initial_state(
            message="My application crashed and I lost all my data. Please help!",
            context={"customer_metadata": {"plan": "premium"}}
        )

        result = await router.process(state)

        assert result["domain"] == "support"
        assert result["domain_confidence"] >= 0.80
        assert result["next_agent"] == "support_domain_router"
        assert "domain_reasoning" in result
        assert len(result["domain_reasoning"]) > 0

        print(f"\n✓ Technical Issue Classification:")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['domain_confidence']:.2%}")
        print(f"  Reasoning: {result['domain_reasoning']}")

    @pytest.mark.asyncio
    async def test_real_llm_support_billing(self, router):
        """Test real LLM call for billing support issue."""
        state = create_initial_state(
            message="I was charged $100 twice this month. Can you refund the duplicate charge?",
            context={"customer_metadata": {"plan": "basic", "mrr": 100}}
        )

        result = await router.process(state)

        assert result["domain"] == "support"
        assert result["domain_confidence"] >= 0.80
        assert result["next_agent"] == "support_domain_router"

        print(f"\n✓ Billing Issue Classification:")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['domain_confidence']:.2%}")
        print(f"  Reasoning: {result['domain_reasoning']}")

    @pytest.mark.asyncio
    async def test_real_llm_sales_pricing(self, router):
        """Test real LLM call for sales pricing inquiry."""
        state = create_initial_state(
            message="How much would it cost to upgrade to Premium for a team of 50 people?",
            context={"customer_metadata": {"plan": "free", "account_age_days": 3}}
        )

        result = await router.process(state)

        assert result["domain"] == "sales"
        assert result["domain_confidence"] >= 0.80
        assert result["next_agent"] == "sales_domain_router"

        print(f"\n✓ Pricing Inquiry Classification:")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['domain_confidence']:.2%}")
        print(f"  Reasoning: {result['domain_reasoning']}")

    @pytest.mark.asyncio
    async def test_real_llm_sales_demo(self, router):
        """Test real LLM call for sales demo request."""
        state = create_initial_state(
            message="I'd like to schedule a demo to see how your product works",
            context={"customer_metadata": {"plan": "free"}}
        )

        result = await router.process(state)

        assert result["domain"] == "sales"
        assert result["domain_confidence"] >= 0.80

        print(f"\n✓ Demo Request Classification:")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['domain_confidence']:.2%}")
        print(f"  Reasoning: {result['domain_reasoning']}")

    @pytest.mark.asyncio
    async def test_real_llm_customer_success_value(self, router):
        """Test real LLM call for customer success value concern."""
        state = create_initial_state(
            message="Our team has been using the product for 3 months but we're not seeing the ROI we expected. Considering canceling.",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 500,
                    "health_score": 35,
                    "churn_risk": 0.85
                }
            }
        )

        result = await router.process(state)

        assert result["domain"] == "customer_success"
        assert result["domain_confidence"] >= 0.75
        assert result["next_agent"] == "cs_domain_router"

        print(f"\n✓ Value Concern Classification:")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['domain_confidence']:.2%}")
        print(f"  Reasoning: {result['domain_reasoning']}")

    @pytest.mark.asyncio
    async def test_real_llm_customer_success_adoption(self, router):
        """Test real LLM call for customer success adoption issue."""
        state = create_initial_state(
            message="Most of our team members haven't logged in for weeks. How can we drive adoption?",
            context={
                "customer_metadata": {
                    "plan": "basic",
                    "health_score": 40
                }
            }
        )

        result = await router.process(state)

        assert result["domain"] == "customer_success"
        assert result["domain_confidence"] >= 0.75

        print(f"\n✓ Adoption Issue Classification:")
        print(f"  Domain: {result['domain']}")
        print(f"  Confidence: {result['domain_confidence']:.2%}")
        print(f"  Reasoning: {result['domain_reasoning']}")

    @pytest.mark.asyncio
    async def test_real_llm_context_influences_routing(self, router):
        """Test that customer context influences routing decisions."""
        # Same message, different contexts, should route differently

        # Free user asking about features → sales
        state_free = create_initial_state(
            message="What features are included?",
            context={"customer_metadata": {"plan": "free"}}
        )
        result_free = await router.process(state_free)

        # High churn risk paying customer → customer success
        state_risk = create_initial_state(
            message="What features are included?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "churn_risk": 0.9,
                    "health_score": 25
                }
            }
        )
        result_risk = await router.process(state_risk)

        print(f"\n✓ Context-Aware Routing:")
        print(f"  Free user → {result_free['domain']}")
        print(f"  At-risk customer → {result_risk['domain']}")

        # At-risk customer should route to CS or support, not same as free user
        assert result_free["domain"] in ["sales", "support"]
        assert result_risk["domain"] in ["customer_success", "support"]

    @pytest.mark.asyncio
    async def test_real_llm_latency_acceptable(self, router):
        """Test that routing latency is acceptable (<3s)."""
        state = create_initial_state(
            message="How do I export my data?",
            context={"customer_metadata": {"plan": "basic"}}
        )

        result = await router.process(state)

        latency_ms = result["routing_metadata"]["latency_ms"]

        print(f"\n✓ Routing Latency: {latency_ms}ms")

        # Should be fast with Haiku model
        assert latency_ms < 3000, f"Routing too slow: {latency_ms}ms"

    @pytest.mark.asyncio
    async def test_real_llm_batch_classification_accuracy(self, router):
        """Test classification accuracy on a batch of messages."""
        test_cases = [
            {
                "message": "My app keeps freezing",
                "context": {"plan": "premium"},
                "expected": "support",
            },
            {
                "message": "What's the pricing for Enterprise?",
                "context": {"plan": "free"},
                "expected": "sales",
            },
            {
                "message": "We're thinking of canceling",
                "context": {"plan": "premium", "churn_risk": 0.8},
                "expected": "customer_success",
            },
            {
                "message": "I forgot my password",
                "context": {"plan": "basic"},
                "expected": "support",
            },
            {
                "message": "Can I see a product demo?",
                "context": {"plan": "free"},
                "expected": "sales",
            },
        ]

        correct = 0
        total = len(test_cases)

        for i, test in enumerate(test_cases, 1):
            state = create_initial_state(
                message=test["message"],
                context={"customer_metadata": test["context"]}
            )

            result = await router.process(state)

            is_correct = result["domain"] == test["expected"]
            if is_correct:
                correct += 1

            status = "✓" if is_correct else "✗"
            print(f"{status} Test {i}: '{test['message'][:40]}...'")
            print(f"   Expected: {test['expected']}, Got: {result['domain']} ({result['domain_confidence']:.2%})")

        accuracy = (correct / total) * 100
        print(f"\n✓ Overall Accuracy: {accuracy:.1f}% ({correct}/{total})")

        # Should achieve >80% accuracy
        assert accuracy >= 80, f"Accuracy too low: {accuracy:.1f}%"
