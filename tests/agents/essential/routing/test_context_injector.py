"""
Unit tests for Context Injector.

Tests context enrichment, prompt injection, and formatting.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-111)
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.agents.essential.routing.context_injector import ContextInjector, EnrichedContext
from src.workflow.state import create_initial_state


class TestContextInjector:
    """Test suite for Context Injector."""

    @pytest.fixture
    def injector(self):
        """Create ContextInjector instance for testing."""
        return ContextInjector()

    def test_initialization(self, injector):
        """Test ContextInjector initializes correctly."""
        assert injector.config.name == "context_injector"
        assert injector.config.type.value == "utility"

    def test_health_thresholds_defined(self, injector):
        """Test health score thresholds are defined."""
        assert injector.HEALTH_EXCELLENT == 80
        assert injector.HEALTH_GOOD == 60
        assert injector.HEALTH_FAIR == 40
        assert injector.HEALTH_POOR == 40

    def test_churn_thresholds_defined(self, injector):
        """Test churn risk thresholds are defined."""
        assert injector.CHURN_LOW == 0.3
        assert injector.CHURN_MEDIUM == 0.6
        assert injector.CHURN_HIGH == 0.6

    # ==================== Context Enrichment Tests ====================

    @pytest.mark.asyncio
    async def test_enrich_context_returns_enriched_context(self, injector):
        """Test enrich_context returns EnrichedContext object."""
        context = await injector.enrich_context(
            customer_id="cust_123",
            conversation_id="conv_456"
        )

        assert isinstance(context, EnrichedContext)
        assert context.customer_id == "cust_123"
        assert context.company_name is not None
        assert context.plan is not None
        assert context.health_score >= 0
        assert 0 <= context.churn_risk <= 1

    @pytest.mark.asyncio
    async def test_process_enriches_state(self, injector):
        """Test process method enriches state."""
        state = create_initial_state(
            message="Test",
            context={"customer_id": "cust_123"}
        )

        result = await injector.process(state)

        # Should have enriched context
        assert "enriched_context" in result
        assert isinstance(result["enriched_context"], EnrichedContext)

        # Should have metadata
        assert "context_injection_metadata" in result
        assert "overhead_ms" in result["context_injection_metadata"]

    @pytest.mark.asyncio
    async def test_process_without_customer_id(self, injector):
        """Test process handles missing customer_id gracefully."""
        state = create_initial_state(message="Test", context={})

        result = await injector.process(state)

        # Should return state unchanged (no crash)
        assert result["current_message"] == "Test"

    # ==================== Prompt Injection Tests ====================

    @pytest.mark.asyncio
    async def test_inject_context_into_prompt(self, injector):
        """Test context injection into system prompt."""
        base_prompt = "You are a billing specialist. Help with billing inquiries."

        enriched_prompt = await injector.inject_context(
            system_prompt=base_prompt,
            customer_id="cust_123"
        )

        # Should contain both context and original prompt
        assert "<customer_context>" in enriched_prompt
        assert "</customer_context>" in enriched_prompt
        assert base_prompt in enriched_prompt

        # Context should come before prompt
        context_start = enriched_prompt.index("<customer_context>")
        prompt_start = enriched_prompt.index(base_prompt)
        assert context_start < prompt_start

    @pytest.mark.asyncio
    async def test_inject_context_includes_customer_data(self, injector):
        """Test injected context includes customer data."""
        base_prompt = "You are a support agent."

        enriched_prompt = await injector.inject_context(
            system_prompt=base_prompt,
            customer_id="cust_123"
        )

        # Should contain key customer information
        assert "Company:" in enriched_prompt
        assert "Plan:" in enriched_prompt
        assert "Health Score:" in enriched_prompt
        assert "Churn Risk:" in enriched_prompt

    @pytest.mark.asyncio
    async def test_inject_context_handles_errors(self, injector):
        """Test context injection handles errors gracefully."""
        # Mock enrich_context to raise exception
        injector.enrich_context = AsyncMock(side_effect=Exception("Test error"))

        base_prompt = "You are a support agent."

        enriched_prompt = await injector.inject_context(
            system_prompt=base_prompt,
            customer_id="cust_123"
        )

        # Should return original prompt on error
        assert enriched_prompt == base_prompt

    # ==================== Context Formatting Tests ====================

    def test_format_context_section_includes_all_fields(self, injector):
        """Test context formatting includes all relevant fields."""
        context = EnrichedContext(
            customer_id="cust_123",
            company_name="Acme Corp",
            plan="enterprise",
            health_score=85,
            churn_risk=0.15,
            churn_risk_label="low",
            ltv=25000,
            mrr=2000,
            team_size=50,
            account_age_days=365,
            last_login="2024-01-14 10:00 AM",
            last_activity="2024-01-14 3:00 PM",
            recent_activity_summary="Very active",
            support_history_summary="5 tickets, all resolved",
            avg_csat=4.8,
            open_tickets=0,
            red_flags=[],
            green_flags=["high_engagement"]
        )

        formatted = injector._format_context_section(context)

        # Check key information is present
        assert "Acme Corp" in formatted
        assert "ENTERPRISE" in formatted
        assert "50 users" in formatted
        assert "85/100" in formatted
        assert "15%" in formatted
        assert "$25,000" in formatted
        assert "$2,000" in formatted

    def test_format_context_section_includes_support_history(self, injector):
        """Test formatting includes support history."""
        context = EnrichedContext(
            customer_id="cust_123",
            company_name="Test Corp",
            plan="premium",
            health_score=70,
            churn_risk=0.3,
            churn_risk_label="low",
            ltv=10000,
            mrr=1000,
            team_size=25,
            account_age_days=180,
            last_login="2024-01-14",
            last_activity="2024-01-14",
            recent_activity_summary="Active",
            support_history_summary="3 tickets in past 30 days",
            avg_csat=4.5,
            open_tickets=1,
            red_flags=[],
            green_flags=[]
        )

        formatted = injector._format_context_section(context)

        assert "Support History:" in formatted
        assert "3 tickets in past 30 days" in formatted
        assert "4.5/5.0" in formatted
        assert "Open Tickets: 1" in formatted

    def test_format_context_section_includes_red_flags(self, injector):
        """Test formatting includes red flags."""
        context = EnrichedContext(
            customer_id="cust_123",
            company_name="Test Corp",
            plan="basic",
            health_score=30,
            churn_risk=0.8,
            churn_risk_label="high",
            ltv=5000,
            mrr=500,
            team_size=10,
            account_age_days=90,
            last_login="2024-01-01",
            last_activity="2024-01-01",
            recent_activity_summary="Low activity",
            support_history_summary="",
            avg_csat=None,
            open_tickets=3,
            red_flags=["low_engagement", "payment_failed", "support_tickets_spike"],
            green_flags=[]
        )

        formatted = injector._format_context_section(context)

        assert "Red Flags:" in formatted
        assert "low_engagement" in formatted
        assert "payment_failed" in formatted
        assert "support_tickets_spike" in formatted

    def test_format_context_section_includes_green_flags(self, injector):
        """Test formatting includes green flags."""
        context = EnrichedContext(
            customer_id="cust_123",
            company_name="Test Corp",
            plan="enterprise",
            health_score=95,
            churn_risk=0.05,
            churn_risk_label="low",
            ltv=50000,
            mrr=5000,
            team_size=100,
            account_age_days=730,
            last_login="2024-01-14",
            last_activity="2024-01-14",
            recent_activity_summary="Very active",
            support_history_summary="",
            avg_csat=None,
            open_tickets=0,
            red_flags=[],
            green_flags=["high_engagement", "paying_customer", "positive_csat", "long_tenure"]
        )

        formatted = injector._format_context_section(context)

        assert "Positive Signals:" in formatted
        assert "high_engagement" in formatted
        assert "paying_customer" in formatted

    # ==================== Health Label Tests ====================

    def test_get_health_label_excellent(self, injector):
        """Test excellent health label."""
        assert injector._get_health_label(90) == "Excellent"
        assert injector._get_health_label(85) == "Excellent"

    def test_get_health_label_good(self, injector):
        """Test good health label."""
        assert injector._get_health_label(75) == "Good"
        assert injector._get_health_label(65) == "Good"

    def test_get_health_label_fair(self, injector):
        """Test fair health label."""
        assert injector._get_health_label(55) == "Fair"
        assert injector._get_health_label(45) == "Fair"

    def test_get_health_label_poor(self, injector):
        """Test poor health label."""
        assert injector._get_health_label(35) == "Poor"
        assert injector._get_health_label(20) == "Poor"

    # ==================== Churn Label Tests ====================

    def test_get_churn_label_low(self, injector):
        """Test low churn risk label."""
        assert injector._get_churn_label(0.1) == "Low Risk"
        assert injector._get_churn_label(0.25) == "Low Risk"

    def test_get_churn_label_medium(self, injector):
        """Test medium churn risk label."""
        assert injector._get_churn_label(0.4) == "Medium Risk"
        assert injector._get_churn_label(0.55) == "Medium Risk"

    def test_get_churn_label_high(self, injector):
        """Test high churn risk label."""
        assert injector._get_churn_label(0.7) == "High Risk"
        assert injector._get_churn_label(0.9) == "High Risk"

    # ==================== Context Summary Tests ====================

    def test_get_context_summary(self, injector):
        """Test context summary generation."""
        context = EnrichedContext(
            customer_id="cust_123",
            company_name="Acme Corp",
            plan="enterprise",
            health_score=85,
            churn_risk=0.2,
            churn_risk_label="low",
            ltv=30000,
            mrr=3000,
            team_size=75,
            account_age_days=500,
            last_login="2024-01-14",
            last_activity="2024-01-14",
            recent_activity_summary="Active",
            support_history_summary="",
            avg_csat=4.7,
            open_tickets=1,
            red_flags=[],
            green_flags=[]
        )

        summary = injector.get_context_summary(context)

        # Check key information
        assert "Acme Corp" in summary
        assert "enterprise" in summary
        assert "85/100" in summary
        assert "20%" in summary
        assert "$3,000" in summary
        assert "$30,000" in summary
        assert "75 users" in summary
        assert "500 days" in summary

    def test_extract_context_from_state(self, injector):
        """Test extracting enriched context from state."""
        state = create_initial_state(message="Test", context={})

        # No context
        context = injector.extract_context_from_state(state)
        assert context is None

        # With context
        enriched = EnrichedContext(
            customer_id="cust_123",
            company_name="Test",
            plan="premium",
            health_score=70,
            churn_risk=0.3,
            churn_risk_label="low",
            ltv=10000,
            mrr=1000,
            team_size=20,
            account_age_days=180,
            last_login="2024-01-14",
            last_activity="2024-01-14",
            recent_activity_summary="",
            support_history_summary="",
            avg_csat=None,
            open_tickets=0,
            red_flags=[],
            green_flags=[]
        )

        state["enriched_context"] = enriched

        extracted = injector.extract_context_from_state(state)
        assert extracted == enriched


# ==================== Integration Tests ====================

class TestContextInjectorIntegration:
    """Integration tests for realistic context injection scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_enterprise_customer_context(self):
        """Test realistic enterprise customer context injection."""
        injector = ContextInjector()

        base_prompt = """You are a customer success manager.
Help enterprise customers maximize value from the product."""

        enriched_prompt = await injector.inject_context(
            system_prompt=base_prompt,
            customer_id="cust_enterprise_123"
        )

        # Should have complete context
        assert "<customer_context>" in enriched_prompt
        assert "Plan:" in enriched_prompt
        assert "Health Score:" in enriched_prompt
        assert "MRR:" in enriched_prompt

        # Original prompt should be preserved
        assert base_prompt in enriched_prompt

    @pytest.mark.asyncio
    async def test_realistic_at_risk_customer_context(self):
        """Test realistic at-risk customer context."""
        injector = ContextInjector()

        # Mock enrich_context to return at-risk customer
        async def mock_enrich(customer_id, conversation_id=None):
            return EnrichedContext(
                customer_id=customer_id,
                company_name="At-Risk Corp",
                plan="enterprise",
                health_score=25,
                churn_risk=0.85,
                churn_risk_label="high",
                ltv=50000,
                mrr=5000,
                team_size=100,
                account_age_days=365,
                last_login="2024-01-01",  # Not recent
                last_activity="2024-01-01",
                recent_activity_summary="Very low activity",
                support_history_summary="10 open tickets",
                avg_csat=2.5,
                open_tickets=10,
                red_flags=["low_engagement", "many_support_tickets", "negative_csat"],
                green_flags=[]
            )

        injector.enrich_context = mock_enrich

        base_prompt = "You are a support agent."

        enriched_prompt = await injector.inject_context(
            system_prompt=base_prompt,
            customer_id="cust_at_risk"
        )

        # Should highlight at-risk status
        assert "25/100" in enriched_prompt  # Low health
        assert "85%" in enriched_prompt  # High churn risk
        assert "Red Flags:" in enriched_prompt
        assert "low_engagement" in enriched_prompt

    @pytest.mark.asyncio
    async def test_realistic_high_value_happy_customer(self):
        """Test realistic high-value happy customer context."""
        injector = ContextInjector()

        # Mock enrich_context
        async def mock_enrich(customer_id, conversation_id=None):
            return EnrichedContext(
                customer_id=customer_id,
                company_name="Happy Corp",
                plan="enterprise",
                health_score=95,
                churn_risk=0.05,
                churn_risk_label="low",
                ltv=100000,
                mrr=10000,
                team_size=200,
                account_age_days=1000,
                last_login="2024-01-14 9:00 AM",
                last_activity="2024-01-14 2:00 PM",
                recent_activity_summary="Very high engagement",
                support_history_summary="Few tickets, all resolved quickly",
                avg_csat=4.9,
                open_tickets=0,
                red_flags=[],
                green_flags=["high_engagement", "excellent_csat", "long_tenure", "high_ltv"]
            )

        injector.enrich_context = mock_enrich

        base_prompt = "You are a support agent."

        enriched_prompt = await injector.inject_context(
            system_prompt=base_prompt,
            customer_id="cust_happy"
        )

        # Should show positive signals
        assert "95/100" in enriched_prompt
        assert "5%" in enriched_prompt
        assert "Positive Signals:" in enriched_prompt
        assert "high_engagement" in enriched_prompt
        assert "excellent_csat" in enriched_prompt

    @pytest.mark.asyncio
    async def test_overhead_is_minimal(self):
        """Test context injection overhead is minimal (<50ms target)."""
        injector = ContextInjector()

        state = create_initial_state(
            message="Test",
            context={"customer_id": "cust_123"}
        )

        result = await injector.process(state)

        # Check overhead
        overhead_ms = result["context_injection_metadata"]["overhead_ms"]

        # Should be very fast (< 50ms is target, but mock should be instant)
        assert overhead_ms < 100  # Generous limit for tests
