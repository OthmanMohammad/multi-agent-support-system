"""
Unit tests for Intent Classifier.

Tests hierarchical intent classification, confidence scoring,
entity extraction, and alternative intent detection.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-102)
"""

import pytest
from unittest.mock import AsyncMock
import json

from src.agents.essential.routing.intent_classifier import (
    IntentClassifier,
    create_intent_classifier
)
from src.workflow.state import AgentState, create_initial_state


@pytest.fixture
def classifier():
    """Create IntentClassifier instance for testing."""
    return IntentClassifier()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Test message",
        customer_id="test_customer_123"
    )


class TestIntentClassifierInitialization:
    """Test Intent Classifier initialization and configuration."""

    def test_intent_classifier_initialization(self, classifier):
        """Test that Intent Classifier initializes with correct configuration."""
        assert classifier.config.name == "intent_classifier"
        assert classifier.config.type.value == "router"
        assert classifier.config.model == "claude-3-haiku-20240307"
        assert classifier.config.temperature == 0.1
        assert classifier.config.max_tokens == 400
        assert classifier.config.tier == "essential"

    def test_intent_classifier_has_required_capabilities(self, classifier):
        """Test that Intent Classifier has required capabilities."""
        from src.agents.base.agent_types import AgentCapability

        capabilities = classifier.config.capabilities
        assert AgentCapability.ROUTING in capabilities
        assert AgentCapability.CONTEXT_AWARE in capabilities
        assert AgentCapability.ENTITY_EXTRACTION in capabilities

    def test_create_intent_classifier_helper(self):
        """Test helper function creates valid instance."""
        classifier = create_intent_classifier()
        assert isinstance(classifier, IntentClassifier)
        assert classifier.config.name == "intent_classifier"


class TestBillingIntentClassification:
    """Test billing-related intent classification."""

    @pytest.mark.asyncio
    async def test_classifies_billing_upgrade(self, classifier):
        """Test: Billing upgrade intent → support/billing/subscription/upgrade"""
        state = create_initial_state(
            message="I want to upgrade to Premium",
            context={"customer_metadata": {"plan": "basic"}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "subcategory": "subscription",
            "action": "upgrade",
            "confidence_scores": {
                "domain": 0.98,
                "category": 0.95,
                "subcategory": 0.92,
                "action": 0.90
            },
            "entities": {"plan_name": "premium"},
            "reasoning": "User requesting plan upgrade"
        }))

        result = await classifier.process(state)

        assert result["intent_domain"] == "support"
        assert result["intent_category"] == "billing"
        assert result["intent_subcategory"] == "subscription"
        assert result["intent_action"] == "upgrade"
        assert result["intent_confidence_scores"]["overall"] > 0.9
        assert "meta_router" not in result["agent_history"]  # Shouldn't be there
        assert "intent_classifier" in result["agent_history"]

    @pytest.mark.asyncio
    async def test_classifies_billing_cancel(self, classifier):
        """Test: Cancel subscription → support/billing/subscription/cancel"""
        state = create_initial_state(
            message="I need to cancel my subscription",
            context={"customer_metadata": {"plan": "premium"}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "subcategory": "subscription",
            "action": "cancel",
            "confidence_scores": {
                "domain": 0.99,
                "category": 0.97,
                "subcategory": 0.95,
                "action": 0.93
            },
            "reasoning": "User requesting subscription cancellation"
        }))

        result = await classifier.process(state)

        assert result["intent_domain"] == "support"
        assert result["intent_category"] == "billing"
        assert result["intent_action"] == "cancel"

    @pytest.mark.asyncio
    async def test_classifies_payment_failed(self, classifier):
        """Test: Failed payment → support/billing/payment/failed_payment"""
        state = create_initial_state(
            message="My payment didn't go through",
            context={"customer_metadata": {"plan": "basic"}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "subcategory": "payment",
            "action": "failed_payment",
            "confidence_scores": {
                "domain": 0.97,
                "category": 0.94,
                "subcategory": 0.91,
                "action": 0.89
            },
            "reasoning": "User reporting failed payment"
        }))

        result = await classifier.process(state)

        assert result["intent_category"] == "billing"
        assert result["intent_subcategory"] == "payment"
        assert result["intent_action"] == "failed_payment"

    @pytest.mark.asyncio
    async def test_classifies_invoice_request(self, classifier):
        """Test: Invoice request → support/billing/invoice/request_invoice"""
        state = create_initial_state(
            message="Can you send me an invoice for last month?",
            context={}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "subcategory": "invoice",
            "action": "request_invoice",
            "confidence_scores": {
                "domain": 0.96,
                "category": 0.93,
                "subcategory": 0.90,
                "action": 0.88
            },
            "reasoning": "User requesting invoice"
        }))

        result = await classifier.process(state)

        assert result["intent_subcategory"] == "invoice"
        assert result["intent_action"] == "request_invoice"


class TestTechnicalIntentClassification:
    """Test technical support intent classification."""

    @pytest.mark.asyncio
    async def test_classifies_crash(self, classifier):
        """Test: App crash → support/technical/bug/crash"""
        state = create_initial_state(
            message="The app crashes when I export data",
            context={}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "technical",
            "subcategory": "bug",
            "action": "crash",
            "confidence_scores": {
                "domain": 0.99,
                "category": 0.97,
                "subcategory": 0.95,
                "action": 0.93
            },
            "entities": {"feature": "export"},
            "reasoning": "User reporting crash bug during export"
        }))

        result = await classifier.process(state)

        assert result["intent_domain"] == "support"
        assert result["intent_category"] == "technical"
        assert result["intent_subcategory"] == "bug"
        assert result["intent_action"] == "crash"

    @pytest.mark.asyncio
    async def test_classifies_sync_issue(self, classifier):
        """Test: Sync problem → support/technical/sync/not_syncing"""
        state = create_initial_state(
            message="My data isn't syncing across devices",
            context={}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "technical",
            "subcategory": "sync",
            "action": "not_syncing",
            "confidence_scores": {
                "domain": 0.98,
                "category": 0.96,
                "subcategory": 0.94,
                "action": 0.92
            },
            "reasoning": "User reporting sync issue"
        }))

        result = await classifier.process(state)

        assert result["intent_category"] == "technical"
        assert result["intent_subcategory"] == "sync"
        assert result["intent_action"] == "not_syncing"

    @pytest.mark.asyncio
    async def test_classifies_performance_slow(self, classifier):
        """Test: Performance issue → support/technical/performance/slow_load"""
        state = create_initial_state(
            message="The app is really slow, takes forever to load",
            context={}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "technical",
            "subcategory": "performance",
            "action": "slow_load",
            "confidence_scores": {
                "domain": 0.97,
                "category": 0.95,
                "subcategory": 0.93,
                "action": 0.91
            },
            "reasoning": "User reporting slow performance"
        }))

        result = await classifier.process(state)

        assert result["intent_subcategory"] == "performance"
        assert result["intent_action"] == "slow_load"

    @pytest.mark.asyncio
    async def test_classifies_login_password_reset(self, classifier):
        """Test: Login issue → support/technical/login/password_reset"""
        state = create_initial_state(
            message="I forgot my password and can't log in",
            context={}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "technical",
            "subcategory": "login",
            "action": "password_reset",
            "confidence_scores": {
                "domain": 0.99,
                "category": 0.96,
                "subcategory": 0.94,
                "action": 0.92
            },
            "reasoning": "User needs password reset"
        }))

        result = await classifier.process(state)

        assert result["intent_subcategory"] == "login"
        assert result["intent_action"] == "password_reset"


class TestSalesIntentClassification:
    """Test sales-related intent classification."""

    @pytest.mark.asyncio
    async def test_classifies_demo_request(self, classifier):
        """Test: Demo request → sales/qualification/demo_request"""
        state = create_initial_state(
            message="I'd like to schedule a demo",
            context={"customer_metadata": {"plan": "free"}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "sales",
            "category": "qualification",
            "subcategory": "demo_request",
            "confidence_scores": {
                "domain": 0.96,
                "category": 0.94,
                "subcategory": 0.92
            },
            "reasoning": "User requesting product demo"
        }))

        result = await classifier.process(state)

        assert result["intent_domain"] == "sales"
        assert result["intent_category"] == "qualification"
        assert result["intent_subcategory"] == "demo_request"

    @pytest.mark.asyncio
    async def test_classifies_pricing_inquiry(self, classifier):
        """Test: Pricing question → sales/qualification/pricing_inquiry"""
        state = create_initial_state(
            message="What's the pricing for 50 users?",
            context={"customer_metadata": {"plan": "free"}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "sales",
            "category": "qualification",
            "subcategory": "pricing_inquiry",
            "confidence_scores": {
                "domain": 0.95,
                "category": 0.92,
                "subcategory": 0.90
            },
            "entities": {"team_size": 50},
            "reasoning": "User inquiring about pricing"
        }))

        result = await classifier.process(state)

        assert result["intent_domain"] == "sales"
        assert result["intent_subcategory"] == "pricing_inquiry"

    @pytest.mark.asyncio
    async def test_classifies_competitor_comparison(self, classifier):
        """Test: Competitor comparison → sales/objection/competitor_comparison"""
        state = create_initial_state(
            message="How does this compare to Asana?",
            context={}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "sales",
            "category": "objection",
            "subcategory": "competitor_comparison",
            "confidence_scores": {
                "domain": 0.93,
                "category": 0.90,
                "subcategory": 0.88
            },
            "entities": {"competitor": "Asana"},
            "reasoning": "User comparing with competitor"
        }))

        result = await classifier.process(state)

        assert result["intent_category"] == "objection"
        assert result["intent_subcategory"] == "competitor_comparison"


class TestCustomerSuccessIntentClassification:
    """Test customer success intent classification."""

    @pytest.mark.asyncio
    async def test_classifies_value_concern(self, classifier):
        """Test: Value concern → customer_success/health/value_concern"""
        state = create_initial_state(
            message="We're not seeing the ROI we expected",
            context={"customer_metadata": {"plan": "enterprise", "health_score": 30}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "customer_success",
            "category": "health",
            "subcategory": "value_concern",
            "confidence_scores": {
                "domain": 0.95,
                "category": 0.92,
                "subcategory": 0.90
            },
            "reasoning": "Customer expressing value concerns"
        }))

        result = await classifier.process(state)

        assert result["intent_domain"] == "customer_success"
        assert result["intent_category"] == "health"
        assert result["intent_subcategory"] == "value_concern"

    @pytest.mark.asyncio
    async def test_classifies_onboarding_help(self, classifier):
        """Test: Onboarding → customer_success/onboarding/setup_help"""
        state = create_initial_state(
            message="How do we get started with our first project?",
            context={"customer_metadata": {"plan": "basic", "account_age_days": 2}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "customer_success",
            "category": "onboarding",
            "subcategory": "first_project",
            "confidence_scores": {
                "domain": 0.94,
                "category": 0.91,
                "subcategory": 0.89
            },
            "reasoning": "New customer needs onboarding help"
        }))

        result = await classifier.process(state)

        assert result["intent_category"] == "onboarding"


class TestConfidenceScoring:
    """Test confidence score calculation and handling."""

    @pytest.mark.asyncio
    async def test_calculates_overall_confidence(self, classifier):
        """Test that overall confidence is calculated when not provided."""
        state = create_initial_state(message="Test", context={})

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "confidence_scores": {
                "domain": 0.95,
                "category": 0.90,
                "subcategory": 0.85,
                "action": 0.80
            }
        }))

        result = await classifier.process(state)

        # Should calculate overall as average
        assert "overall" in result["intent_confidence_scores"]
        overall = result["intent_confidence_scores"]["overall"]
        # Average of 0.95, 0.90, 0.85, 0.80 = 0.875
        assert 0.85 <= overall <= 0.90

    @pytest.mark.asyncio
    async def test_clamps_confidence_scores(self, classifier):
        """Test that confidence scores are clamped to 0-1 range."""
        state = create_initial_state(message="Test", context={})

        # Return scores outside valid range
        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "confidence_scores": {
                "domain": 1.5,  # > 1
                "category": -0.2,  # < 0
                "overall": 0.8
            }
        }))

        result = await classifier.process(state)

        scores = result["intent_confidence_scores"]
        assert scores["domain"] == 1.0  # Clamped to 1.0
        assert scores["category"] == 0.0  # Clamped to 0.0


class TestAlternativeIntents:
    """Test alternative intent detection."""

    @pytest.mark.asyncio
    async def test_provides_alternative_intents(self, classifier):
        """Test that alternative intents are returned."""
        state = create_initial_state(
            message="What's the pricing?",
            context={"customer_metadata": {"plan": "free"}}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "sales",
            "category": "qualification",
            "subcategory": "pricing_inquiry",
            "confidence_scores": {
                "domain": 0.85,
                "category": 0.80,
                "overall": 0.82
            },
            "alternative_intents": [
                {
                    "domain": "support",
                    "category": "billing",
                    "subcategory": "pricing",
                    "confidence": 0.70,
                    "reasoning": "Could also be existing customer asking about billing"
                }
            ]
        }))

        result = await classifier.process(state)

        assert "intent_alternatives" in result
        assert len(result["intent_alternatives"]) > 0
        alt = result["intent_alternatives"][0]
        assert alt["domain"] == "support"
        assert alt["confidence"] == 0.70

    @pytest.mark.asyncio
    async def test_handles_missing_alternative_intents(self, classifier):
        """Test that missing alternative_intents field is handled."""
        state = create_initial_state(message="Test", context={})

        # Don't include alternative_intents in response
        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "confidence_scores": {"overall": 0.9}
        }))

        result = await classifier.process(state)

        # Should default to empty list
        assert "intent_alternatives" in result
        assert result["intent_alternatives"] == []


class TestEntityExtraction:
    """Test entity extraction from messages."""

    @pytest.mark.asyncio
    async def test_extracts_plan_name_entity(self, classifier):
        """Test extraction of plan name entity."""
        state = create_initial_state(
            message="Upgrade to Enterprise for 100 users",
            context={}
        )

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "subcategory": "subscription",
            "action": "upgrade",
            "confidence_scores": {"overall": 0.95},
            "entities": {
                "plan_name": "enterprise",
                "team_size": 100,
                "action": "upgrade"
            }
        }))

        result = await classifier.process(state)

        assert "intent_entities" in result
        entities = result["intent_entities"]
        assert entities["plan_name"] == "enterprise"
        assert entities["team_size"] == 100

    @pytest.mark.asyncio
    async def test_handles_missing_entities(self, classifier):
        """Test that missing entities field is handled."""
        state = create_initial_state(message="Test", context={})

        # Don't include entities in response
        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "confidence_scores": {"overall": 0.9}
        }))

        result = await classifier.process(state)

        # Should default to empty dict
        assert "intent_entities" in result
        assert result["intent_entities"] == {}


class TestContextHandling:
    """Test customer context handling."""

    def test_format_customer_context_complete(self, classifier):
        """Test formatting context with all fields."""
        context = {
            "plan": "premium",
            "health_score": 75,
            "team_size": 50,
            "mrr": 1000,
            "churn_risk": 0.3,
            "account_age_days": 365
        }

        formatted = classifier._format_customer_context(context)

        assert "Plan: premium" in formatted
        assert "Health Score: 75/100" in formatted
        assert "Team Size: 50 users" in formatted
        assert "MRR: $1000" in formatted
        assert "Churn Risk: low" in formatted
        assert "Account Age: 365 days" in formatted

    def test_format_customer_context_partial(self, classifier):
        """Test formatting context with only some fields."""
        context = {"plan": "basic", "team_size": 10}

        formatted = classifier._format_customer_context(context)

        assert "Plan: basic" in formatted
        assert "Team Size: 10 users" in formatted
        assert "MRR" not in formatted

    def test_format_customer_context_empty(self, classifier):
        """Test formatting empty context."""
        formatted = classifier._format_customer_context({})
        assert formatted == "No customer context available"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_empty_message(self, classifier):
        """Test handling of empty message."""
        state = create_initial_state(message="", customer_id="test")

        result = await classifier.process(state)

        assert result["intent_domain"] == "support"
        assert result["intent_category"] == "general"
        assert result["intent_confidence_scores"]["overall"] == 0.3

    @pytest.mark.asyncio
    async def test_handles_llm_error(self, classifier):
        """Test handling of LLM errors."""
        state = create_initial_state(message="Test", customer_id="test")

        classifier.call_llm = AsyncMock(side_effect=Exception("API Error"))

        result = await classifier.process(state)

        # Should fallback gracefully
        assert result["intent_domain"] == "support"
        assert result["intent_category"] == "general"
        assert result["intent_confidence_scores"]["overall"] == 0.3

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self, classifier):
        """Test handling of invalid JSON response."""
        state = create_initial_state(message="Test", customer_id="test")

        classifier.call_llm = AsyncMock(return_value="Not valid JSON at all")

        result = await classifier.process(state)

        # Should use text extraction fallback
        assert result["intent_domain"] in ["support", "sales", "customer_success"]
        assert result["intent_confidence_scores"]["overall"] <= 0.5

    @pytest.mark.asyncio
    async def test_handles_missing_required_fields(self, classifier):
        """Test handling of response missing required fields."""
        state = create_initial_state(message="Test", customer_id="test")

        # Missing confidence_scores
        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing"
        }))

        result = await classifier.process(state)

        # Should use fallback
        assert result["intent_domain"] in ["support", "sales", "customer_success"]


class TestStateManagement:
    """Test state management and updates."""

    @pytest.mark.asyncio
    async def test_updates_agent_history(self, classifier):
        """Test that agent history is updated."""
        state = create_initial_state(message="Test", customer_id="test")

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "confidence_scores": {"overall": 0.9}
        }))

        result = await classifier.process(state)

        assert "intent_classifier" in result["agent_history"]
        assert result["current_agent"] == "intent_classifier"

    @pytest.mark.asyncio
    async def test_adds_metadata(self, classifier):
        """Test that metadata is added to state."""
        state = create_initial_state(message="Test", customer_id="test")

        classifier.call_llm = AsyncMock(return_value=json.dumps({
            "domain": "support",
            "category": "billing",
            "confidence_scores": {"overall": 0.9}
        }))

        result = await classifier.process(state)

        assert "intent_metadata" in result
        assert "latency_ms" in result["intent_metadata"]
        assert "model" in result["intent_metadata"]


class TestSystemPrompt:
    """Test system prompt generation."""

    def test_system_prompt_contains_taxonomy(self, classifier):
        """Test that system prompt contains complete taxonomy."""
        prompt = classifier._get_system_prompt()

        # Check for domains
        assert "SUPPORT" in prompt
        assert "SALES" in prompt
        assert "CUSTOMER_SUCCESS" in prompt

        # Check for categories
        assert "billing" in prompt.lower()
        assert "technical" in prompt.lower()
        assert "usage" in prompt.lower()

        # Check for subcategories
        assert "subscription" in prompt.lower()
        assert "payment" in prompt.lower()
        assert "bug" in prompt.lower()
        assert "sync" in prompt.lower()

        # Check for output format
        assert "confidence_scores" in prompt
        assert "entities" in prompt
        assert "alternative_intents" in prompt
