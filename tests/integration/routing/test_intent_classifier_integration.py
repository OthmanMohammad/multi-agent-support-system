"""
Integration tests for Intent Classifier with real LLM calls.

These tests use the actual Anthropic API and verify real-world behavior.
They are marked with @pytest.mark.integration and require ANTHROPIC_API_KEY.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-102)
"""

import pytest
import os

from src.agents.essential.routing.intent_classifier import IntentClassifier
from src.workflow.state import create_initial_state


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestIntentClassifierIntegration:
    """Integration tests with real LLM calls."""

    @pytest.fixture
    def classifier(self):
        """Create IntentClassifier with real Anthropic client."""
        return IntentClassifier()

    @pytest.mark.asyncio
    async def test_real_llm_billing_upgrade(self, classifier):
        """Test real LLM call for billing upgrade intent."""
        state = create_initial_state(
            message="I want to upgrade my plan to Premium for a team of 25 people",
            context={"customer_metadata": {"plan": "basic", "team_size": 10}}
        )

        result = await classifier.process(state)

        print(f"\n✓ Billing Upgrade Classification:")
        print(f"  Domain: {result['intent_domain']}")
        print(f"  Category: {result['intent_category']}")
        print(f"  Subcategory: {result.get('intent_subcategory', 'N/A')}")
        print(f"  Action: {result.get('intent_action', 'N/A')}")
        print(f"  Confidence: {result['intent_confidence_scores']['overall']:.2%}")
        print(f"  Entities: {result.get('intent_entities', {})}")

        assert result["intent_domain"] == "support"
        assert result["intent_category"] == "billing"
        assert result["intent_confidence_scores"]["overall"] >= 0.80

    @pytest.mark.asyncio
    async def test_real_llm_technical_crash(self, classifier):
        """Test real LLM call for technical crash intent."""
        state = create_initial_state(
            message="The application crashes every time I try to export my data. This is urgent!",
            context={"customer_metadata": {"plan": "premium"}}
        )

        result = await classifier.process(state)

        print(f"\n✓ Technical Crash Classification:")
        print(f"  Domain: {result['intent_domain']}")
        print(f"  Category: {result['intent_category']}")
        print(f"  Subcategory: {result.get('intent_subcategory', 'N/A')}")
        print(f"  Action: {result.get('intent_action', 'N/A')}")
        print(f"  Confidence: {result['intent_confidence_scores']['overall']:.2%}")

        assert result["intent_domain"] == "support"
        assert result["intent_category"] == "technical"
        assert result["intent_confidence_scores"]["overall"] >= 0.80

    @pytest.mark.asyncio
    async def test_real_llm_sales_demo(self, classifier):
        """Test real LLM call for sales demo request."""
        state = create_initial_state(
            message="I'd like to schedule a product demo to see if this fits our team's needs",
            context={"customer_metadata": {"plan": "free"}}
        )

        result = await classifier.process(state)

        print(f"\n✓ Sales Demo Classification:")
        print(f"  Domain: {result['intent_domain']}")
        print(f"  Category: {result['intent_category']}")
        print(f"  Subcategory: {result.get('intent_subcategory', 'N/A')}")
        print(f"  Confidence: {result['intent_confidence_scores']['overall']:.2%}")

        assert result["intent_domain"] == "sales"
        assert result["intent_category"] == "qualification"
        assert result["intent_confidence_scores"]["overall"] >= 0.80

    @pytest.mark.asyncio
    async def test_real_llm_customer_success_value(self, classifier):
        """Test real LLM call for customer success value concern."""
        state = create_initial_state(
            message="After 3 months, we're still not seeing the ROI we were promised. Our team engagement is low.",
            context={
                "customer_metadata": {
                    "plan": "enterprise",
                    "health_score": 30,
                    "churn_risk": 0.85
                }
            }
        )

        result = await classifier.process(state)

        print(f"\n✓ Value Concern Classification:")
        print(f"  Domain: {result['intent_domain']}")
        print(f"  Category: {result['intent_category']}")
        print(f"  Subcategory: {result.get('intent_subcategory', 'N/A')}")
        print(f"  Confidence: {result['intent_confidence_scores']['overall']:.2%}")

        assert result["intent_domain"] == "customer_success"
        assert result["intent_category"] == "health"
        assert result["intent_confidence_scores"]["overall"] >= 0.75

    @pytest.mark.asyncio
    async def test_real_llm_entity_extraction(self, classifier):
        """Test that entities are extracted correctly."""
        state = create_initial_state(
            message="We need to upgrade from Basic to Enterprise for 100 users by next month",
            context={"customer_metadata": {"plan": "basic", "team_size": 25}}
        )

        result = await classifier.process(state)

        print(f"\n✓ Entity Extraction:")
        print(f"  Entities: {result.get('intent_entities', {})}")

        entities = result.get("intent_entities", {})
        # Should extract plan name and team size
        assert len(entities) > 0

    @pytest.mark.asyncio
    async def test_real_llm_alternative_intents(self, classifier):
        """Test that alternative intents are provided when appropriate."""
        state = create_initial_state(
            message="How much does it cost?",
            context={"customer_metadata": {"plan": "free"}}
        )

        result = await classifier.process(state)

        print(f"\n✓ Alternative Intents:")
        print(f"  Primary: {result['intent_domain']}/{result['intent_category']}")
        print(f"  Alternatives: {result.get('intent_alternatives', [])}")

        # Ambiguous message might have alternatives
        # Either sales (pricing inquiry) or support (billing)
        assert result["intent_domain"] in ["sales", "support"]

    @pytest.mark.asyncio
    async def test_real_llm_batch_accuracy(self, classifier):
        """Test classification accuracy on a batch of messages."""
        test_cases = [
            {
                "message": "Cancel my subscription",
                "context": {},
                "expected_domain": "support",
                "expected_category": "billing"
            },
            {
                "message": "The app won't sync",
                "context": {},
                "expected_domain": "support",
                "expected_category": "technical"
            },
            {
                "message": "What's the pricing?",
                "context": {"plan": "free"},
                "expected_domain": "sales",
                "expected_category": "qualification"
            },
            {
                "message": "Our team isn't using the product",
                "context": {"plan": "premium", "health_score": 35},
                "expected_domain": "customer_success",
                "expected_category": "health"
            },
            {
                "message": "How do I reset my password?",
                "context": {},
                "expected_domain": "support",
                "expected_category": "technical"
            },
        ]

        correct = 0
        total = len(test_cases)

        for i, test in enumerate(test_cases, 1):
            state = create_initial_state(
                message=test["message"],
                context={"customer_metadata": test["context"]}
            )

            result = await classifier.process(state)

            domain_match = result["intent_domain"] == test["expected_domain"]
            category_match = result["intent_category"] == test["expected_category"]

            if domain_match and category_match:
                correct += 1
                status = "✓"
            else:
                status = "✗"

            print(f"{status} Test {i}: '{test['message'][:40]}...'")
            print(f"   Expected: {test['expected_domain']}/{test['expected_category']}")
            print(f"   Got: {result['intent_domain']}/{result['intent_category']}")
            print(f"   Confidence: {result['intent_confidence_scores']['overall']:.2%}")

        accuracy = (correct / total) * 100
        print(f"\n✓ Overall Accuracy: {accuracy:.1f}% ({correct}/{total})")

        # Should achieve >80% accuracy
        assert accuracy >= 80, f"Accuracy too low: {accuracy:.1f}%"

    @pytest.mark.asyncio
    async def test_real_llm_hierarchical_depth(self, classifier):
        """Test that 4-level hierarchical classification works."""
        state = create_initial_state(
            message="I want to upgrade from Basic to Premium plan",
            context={"customer_metadata": {"plan": "basic"}}
        )

        result = await classifier.process(state)

        print(f"\n✓ Hierarchical Classification:")
        print(f"  Level 1 (Domain): {result.get('intent_domain')}")
        print(f"  Level 2 (Category): {result.get('intent_category')}")
        print(f"  Level 3 (Subcategory): {result.get('intent_subcategory', 'N/A')}")
        print(f"  Level 4 (Action): {result.get('intent_action', 'N/A')}")

        # Should have at least 3 levels classified
        assert result.get("intent_domain") is not None
        assert result.get("intent_category") is not None
        # Subcategory and action may not always be present

    @pytest.mark.asyncio
    async def test_real_llm_confidence_levels(self, classifier):
        """Test that confidence scores are provided at each level."""
        state = create_initial_state(
            message="Please send me last month's invoice",
            context={}
        )

        result = await classifier.process(state)

        print(f"\n✓ Confidence Scores:")
        scores = result.get("intent_confidence_scores", {})
        for level, score in scores.items():
            print(f"  {level}: {score:.2%}")

        # Should have overall confidence
        assert "overall" in scores
        assert 0.0 <= scores["overall"] <= 1.0

    @pytest.mark.asyncio
    async def test_real_llm_latency_acceptable(self, classifier):
        """Test that classification latency is acceptable (<3s)."""
        state = create_initial_state(
            message="My payment failed, please help",
            context={}
        )

        result = await classifier.process(state)

        latency_ms = result["intent_metadata"]["latency_ms"]

        print(f"\n✓ Classification Latency: {latency_ms}ms")

        # Should be fast with Haiku model (<3s)
        assert latency_ms < 3000, f"Classification too slow: {latency_ms}ms"
