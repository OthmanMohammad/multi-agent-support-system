"""
Unit tests for Domain Routers (Support, Sales, CS).

Tests routing logic for all three domain-specific routers.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-105)
"""

import pytest
import json
from unittest.mock import AsyncMock

from src.agents.essential.routing.support_domain_router import SupportDomainRouter
from src.agents.essential.routing.sales_domain_router import SalesDomainRouter
from src.agents.essential.routing.cs_domain_router import CSDomainRouter
from src.workflow.state import create_initial_state


# ==================== Support Domain Router Tests ====================

class TestSupportDomainRouter:
    """Test suite for Support Domain Router."""

    @pytest.fixture
    def router(self):
        """Create SupportDomainRouter instance for testing."""
        return SupportDomainRouter()

    def test_initialization(self, router):
        """Test SupportDomainRouter initializes correctly."""
        assert router.config.name == "support_domain_router"
        assert router.config.type.value == "router"
        assert router.config.model == "claude-3-haiku-20240307"
        assert router.config.temperature == 0.1

    def test_support_categories_defined(self, router):
        """Test support categories are defined."""
        expected = ["billing", "technical", "usage", "integration", "account"]
        assert router.SUPPORT_CATEGORIES == expected

    @pytest.mark.asyncio
    async def test_billing_category_routing(self, router):
        """Test routing to billing category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "billing",
                "confidence": 0.95,
                "reasoning": "Subscription upgrade request"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="I want to upgrade my plan to Premium",
            context={}
        )

        result = await router.process(state)

        assert result["support_category"] == "billing"
        assert result["support_category_confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_technical_category_routing(self, router):
        """Test routing to technical category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "technical",
                "confidence": 0.98,
                "reasoning": "Application crash issue"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="The app crashes when I try to export data",
            context={}
        )

        result = await router.process(state)

        assert result["support_category"] == "technical"
        assert result["support_category_confidence"] == 0.98

    @pytest.mark.asyncio
    async def test_usage_category_routing(self, router):
        """Test routing to usage category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "usage",
                "confidence": 0.92,
                "reasoning": "How-to question"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="How do I create a new project?",
            context={}
        )

        result = await router.process(state)

        assert result["support_category"] == "usage"
        assert result["support_category_confidence"] == 0.92

    @pytest.mark.asyncio
    async def test_integration_category_routing(self, router):
        """Test routing to integration category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "integration",
                "confidence": 0.96,
                "reasoning": "Third-party integration issue"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="The Slack integration isn't working",
            context={}
        )

        result = await router.process(state)

        assert result["support_category"] == "integration"

    @pytest.mark.asyncio
    async def test_account_category_routing(self, router):
        """Test routing to account category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "account",
                "confidence": 0.94,
                "reasoning": "Login issue"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="I can't login to my account",
            context={}
        )

        result = await router.process(state)

        assert result["support_category"] == "account"

    @pytest.mark.asyncio
    async def test_invalid_category_defaults_to_usage(self, router):
        """Test invalid category defaults to usage."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "invalid_category",
                "confidence": 0.5
            })

        router.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await router.process(state)

        assert result["support_category"] == "usage"

    @pytest.mark.asyncio
    async def test_empty_message_defaults_to_usage(self, router):
        """Test empty message defaults to usage."""
        state = create_initial_state(message="", context={})
        result = await router.process(state)

        assert result["support_category"] == "usage"
        assert result["support_category_confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_llm_failure_fallback(self, router):
        """Test LLM failure fallback to usage."""
        router.call_llm = AsyncMock(side_effect=Exception("API Error"))

        state = create_initial_state(message="Test", context={})
        result = await router.process(state)

        assert result["support_category"] == "usage"
        assert result["support_category_confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_metadata_populated(self, router):
        """Test routing metadata is populated."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({"category": "billing", "confidence": 0.9})

        router.call_llm = mock_llm

        state = create_initial_state(message="Upgrade plan", context={})
        result = await router.process(state)

        assert "support_routing_metadata" in result
        assert "latency_ms" in result["support_routing_metadata"]


# ==================== Sales Domain Router Tests ====================

class TestSalesDomainRouter:
    """Test suite for Sales Domain Router."""

    @pytest.fixture
    def router(self):
        """Create SalesDomainRouter instance for testing."""
        return SalesDomainRouter()

    def test_initialization(self, router):
        """Test SalesDomainRouter initializes correctly."""
        assert router.config.name == "sales_domain_router"
        assert router.config.type.value == "router"
        assert router.config.model == "claude-3-haiku-20240307"

    def test_sales_categories_defined(self, router):
        """Test sales categories are defined."""
        expected = ["qualification", "education", "objection", "progression"]
        assert router.SALES_CATEGORIES == expected

    @pytest.mark.asyncio
    async def test_qualification_category_routing(self, router):
        """Test routing to qualification category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "qualification",
                "confidence": 0.93,
                "reasoning": "Pricing and team size inquiry"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="What are your pricing options for a team of 50?",
            context={"customer_metadata": {"plan": "free"}}
        )

        result = await router.process(state)

        assert result["sales_category"] == "qualification"
        assert result["sales_category_confidence"] == 0.93

    @pytest.mark.asyncio
    async def test_education_category_routing(self, router):
        """Test routing to education category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "education",
                "confidence": 0.96,
                "reasoning": "Demo request"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="Can you show me how the reporting feature works?",
            context={}
        )

        result = await router.process(state)

        assert result["sales_category"] == "education"

    @pytest.mark.asyncio
    async def test_objection_category_routing(self, router):
        """Test routing to objection category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "objection",
                "confidence": 0.94,
                "reasoning": "Competitor comparison"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="How does your pricing compare to Asana?",
            context={}
        )

        result = await router.process(state)

        assert result["sales_category"] == "objection"

    @pytest.mark.asyncio
    async def test_progression_category_routing(self, router):
        """Test routing to progression category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "progression",
                "confidence": 0.97,
                "reasoning": "Ready to purchase"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="We're ready to move forward with the Enterprise plan",
            context={"customer_metadata": {"plan": "free", "team_size": 100}}
        )

        result = await router.process(state)

        assert result["sales_category"] == "progression"

    @pytest.mark.asyncio
    async def test_invalid_category_defaults_to_qualification(self, router):
        """Test invalid category defaults to qualification."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "invalid_sales_category",
                "confidence": 0.5
            })

        router.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await router.process(state)

        assert result["sales_category"] == "qualification"

    @pytest.mark.asyncio
    async def test_empty_message_defaults_to_qualification(self, router):
        """Test empty message defaults to qualification."""
        state = create_initial_state(message="", context={})
        result = await router.process(state)

        assert result["sales_category"] == "qualification"

    @pytest.mark.asyncio
    async def test_context_includes_plan_and_team_size(self, router):
        """Test context formatting includes plan and team size."""
        async def mock_llm(*args, user_message="", **kwargs):
            # Verify context is included
            assert "Plan: enterprise" in user_message or "enterprise" in user_message
            return json.dumps({"category": "progression", "confidence": 0.9})

        router.call_llm = mock_llm

        state = create_initial_state(
            message="Let's proceed",
            context={"customer_metadata": {"plan": "enterprise", "team_size": 200}}
        )

        await router.process(state)


# ==================== CS Domain Router Tests ====================

class TestCSDomainRouter:
    """Test suite for CS Domain Router."""

    @pytest.fixture
    def router(self):
        """Create CSDomainRouter instance for testing."""
        return CSDomainRouter()

    def test_initialization(self, router):
        """Test CSDomainRouter initializes correctly."""
        assert router.config.name == "cs_domain_router"
        assert router.config.type.value == "router"
        assert router.config.model == "claude-3-haiku-20240307"

    def test_cs_categories_defined(self, router):
        """Test CS categories are defined."""
        expected = ["health", "onboarding", "adoption", "retention", "expansion"]
        assert router.CS_CATEGORIES == expected

    @pytest.mark.asyncio
    async def test_health_category_routing(self, router):
        """Test routing to health category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "health",
                "confidence": 0.92,
                "reasoning": "Low engagement and churn risk"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="Our team isn't really using the product anymore",
            context={"customer_metadata": {"plan": "enterprise", "health_score": 25, "churn_risk": 0.85}}
        )

        result = await router.process(state)

        assert result["cs_category"] == "health"

    @pytest.mark.asyncio
    async def test_onboarding_category_routing(self, router):
        """Test routing to onboarding category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "onboarding",
                "confidence": 0.95,
                "reasoning": "New customer getting started"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="We just signed up, how do we get started?",
            context={"customer_metadata": {"account_age_days": 5}}
        )

        result = await router.process(state)

        assert result["cs_category"] == "onboarding"

    @pytest.mark.asyncio
    async def test_adoption_category_routing(self, router):
        """Test routing to adoption category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "adoption",
                "confidence": 0.91,
                "reasoning": "Feature usage optimization"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="How can we use automation features more effectively?",
            context={"customer_metadata": {"health_score": 65}}
        )

        result = await router.process(state)

        assert result["cs_category"] == "adoption"

    @pytest.mark.asyncio
    async def test_retention_category_routing(self, router):
        """Test routing to retention category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "retention",
                "confidence": 0.93,
                "reasoning": "Contract renewal discussion"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="Our contract is up for renewal next month",
            context={"customer_metadata": {"plan": "enterprise", "health_score": 75}}
        )

        result = await router.process(state)

        assert result["cs_category"] == "retention"

    @pytest.mark.asyncio
    async def test_expansion_category_routing(self, router):
        """Test routing to expansion category."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "expansion",
                "confidence": 0.96,
                "reasoning": "Upsell opportunity"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="We want to add 50 more seats and explore Enterprise features",
            context={"customer_metadata": {"plan": "premium", "team_size": 100, "health_score": 85}}
        )

        result = await router.process(state)

        assert result["cs_category"] == "expansion"

    @pytest.mark.asyncio
    async def test_health_override_for_high_churn_risk(self, router):
        """Test health category override for high churn risk."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "adoption",  # LLM says adoption
                "confidence": 0.7
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="How do I use feature X?",
            context={"customer_metadata": {"health_score": 30, "churn_risk": 0.85}}
        )

        result = await router.process(state)

        # Should override to health due to high churn risk
        assert result["cs_category"] == "health"

    @pytest.mark.asyncio
    async def test_onboarding_override_for_new_account(self, router):
        """Test onboarding override for very new accounts."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "adoption",
                "confidence": 0.8
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="How does this work?",
            context={"customer_metadata": {"account_age_days": 15}}
        )

        result = await router.process(state)

        # Should override to onboarding for new account
        assert result["cs_category"] == "onboarding"

    @pytest.mark.asyncio
    async def test_context_overrides_logic(self, router):
        """Test _apply_context_overrides method directly."""
        customer_metadata = {
            "health_score": 20,
            "churn_risk": 0.9,
            "account_age_days": 100
        }

        # Should override to health
        result = router._apply_context_overrides(
            "adoption",
            customer_metadata,
            {}
        )

        assert result == "health"

    @pytest.mark.asyncio
    async def test_invalid_category_defaults_to_adoption(self, router):
        """Test invalid category defaults to adoption."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "invalid_cs_category",
                "confidence": 0.5
            })

        router.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await router.process(state)

        assert result["cs_category"] == "adoption"

    @pytest.mark.asyncio
    async def test_empty_message_defaults_to_adoption(self, router):
        """Test empty message defaults to adoption."""
        state = create_initial_state(message="", context={})
        result = await router.process(state)

        assert result["cs_category"] == "adoption"

    @pytest.mark.asyncio
    async def test_metadata_populated(self, router):
        """Test routing metadata is populated."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({"category": "health", "confidence": 0.9})

        router.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await router.process(state)

        assert "cs_routing_metadata" in result
        assert "latency_ms" in result["cs_routing_metadata"]


# ==================== Integration Tests ====================

class TestDomainRoutersIntegration:
    """Integration tests for realistic routing scenarios."""

    @pytest.mark.asyncio
    async def test_support_technical_urgent_scenario(self):
        """Test realistic urgent technical support scenario."""
        router = SupportDomainRouter()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "technical",
                "confidence": 0.98,
                "reasoning": "Critical production bug"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="URGENT: Production system is down, affecting all users!",
            context={"customer_metadata": {"plan": "enterprise"}}
        )

        # Add sentiment context
        state["emotion"] = "angry"
        state["urgency"] = "critical"

        result = await router.process(state)

        assert result["support_category"] == "technical"
        assert result["support_category_confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_sales_progression_ready_to_buy(self):
        """Test realistic sales progression scenario."""
        router = SalesDomainRouter()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "progression",
                "confidence": 0.97,
                "reasoning": "Clear buying signal"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="We've completed the trial and are ready to purchase 200 seats on Enterprise",
            context={"customer_metadata": {"plan": "free", "team_size": 200}}
        )

        # Add sentiment context
        state["emotion"] = "excited"

        result = await router.process(state)

        assert result["sales_category"] == "progression"
        assert result["sales_category_confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_cs_health_at_risk_account(self):
        """Test realistic CS health scenario with at-risk account."""
        router = CSDomainRouter()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "category": "health",
                "confidence": 0.95,
                "reasoning": "Clear churn risk signals"
            })

        router.call_llm = mock_llm

        state = create_initial_state(
            message="We're not seeing the value and considering other options",
            context={"customer_metadata": {
                "plan": "enterprise",
                "health_score": 18,
                "churn_risk": 0.92,
                "mrr": 10000
            }}
        )

        # Add sentiment context
        state["emotion"] = "frustrated"
        state["satisfaction"] = 0.2

        result = await router.process(state)

        assert result["cs_category"] == "health"
        # High confidence expected for clear churn signals
        assert result["cs_category_confidence"] > 0.85
