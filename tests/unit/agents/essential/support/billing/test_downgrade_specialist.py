"""
Unit tests for Subscription Downgrade Specialist Agent.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.essential.support.billing.downgrade_specialist import SubscriptionDowngradeSpecialist
from src.workflow.state import create_initial_state


class TestSubscriptionDowngradeSpecialist:
    """Test suite for Subscription Downgrade Specialist."""

    @pytest.fixture
    def specialist(self):
        """Create specialist instance for testing."""
        return SubscriptionDowngradeSpecialist()

    @pytest.fixture
    def base_state(self):
        """Create base state for testing."""
        return create_initial_state(
            "I want to downgrade to basic plan",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250,
                    "seats_used": 10,
                    "seats_total": 15,
                    "health_score": 65
                }
            }
        )

    # Initialization Tests
    def test_initialization(self, specialist):
        """Test agent initializes correctly."""
        assert specialist.config.name == "downgrade_specialist"
        assert specialist.config.type.value == "specialist"
        assert specialist.config.tier == "essential"
        assert specialist.MAX_DISCOUNT_PERCENT == 20
        assert specialist.MAX_DISCOUNT_MONTHS == 6

    # Main Processing Tests
    @pytest.mark.asyncio
    async def test_retention_offer_for_budget_reason(self, specialist, base_state):
        """Test retention offer when reason is budget."""
        base_state["entities"] = {"target_plan": "basic"}
        base_state["current_message"] = "I want to downgrade, it's too expensive"

        result = await specialist.process(base_state)

        assert result["retention_offered"] is True
        assert "discount" in result["agent_response"].lower()
        assert result["retention_tactic"] == "discount_20_percent_6_months"
        assert result["retention_attempt"] == 1
        assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_retention_offer_for_not_using_features(self, specialist, base_state):
        """Test retention offer when not using features."""
        base_state["current_message"] = "I'm not using the advanced features"
        base_state["entities"] = {"target_plan": "basic"}

        result = await specialist.process(base_state)

        assert result["retention_offered"] is True
        assert result["retention_tactic"] == "feature_education"
        assert "feature" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_retention_offer_for_too_many_seats(self, specialist, base_state):
        """Test retention offer when too many seats."""
        base_state["current_message"] = "We have too many seats, team size reduced"
        base_state["entities"] = {"target_plan": "basic"}

        result = await specialist.process(base_state)

        assert result["retention_offered"] is True
        assert result["retention_tactic"] == "remove_unused_seats"
        assert "seats" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_retention_accepted(self, specialist, base_state):
        """Test when user accepts retention offer."""
        base_state["current_message"] = "Yes, that sounds good"
        base_state["retention_attempt"] = 1
        base_state["retention_tactic"] = "discount_20_percent_6_months"

        result = await specialist.process(base_state)

        assert result["retention_successful"] is True
        assert "applied" in result["agent_response"].lower() or "discount" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_retention_rejected_process_downgrade(self, specialist, base_state):
        """Test downgrade processed when retention rejected."""
        base_state["current_message"] = "No, just downgrade me please"
        base_state["retention_attempt"] = 1
        base_state["entities"] = {"target_plan": "basic"}

        result = await specialist.process(base_state)

        assert result["retention_successful"] is False
        assert result["downgrade_processed"] is True
        assert result["status"] == "resolved"

    # Helper Method Tests
    def test_extract_downgrade_reason_budget(self, specialist):
        """Test extracting budget reason from message."""
        reason = specialist._extract_downgrade_reason("It's too expensive for us")
        assert reason == "too_expensive"

    def test_extract_downgrade_reason_features(self, specialist):
        """Test extracting not using features reason."""
        reason = specialist._extract_downgrade_reason("We're not using the advanced features")
        assert reason == "not_using_features"

    def test_extract_downgrade_reason_seats(self, specialist):
        """Test extracting seats reason."""
        reason = specialist._extract_downgrade_reason("We have too many seats")
        assert reason == "too_many_seats"

    def test_get_lost_features(self, specialist):
        """Test getting lost features."""
        lost = specialist._get_lost_features("premium", "basic")
        assert "Advanced reporting" in lost or "API access" in lost
        assert len(lost) > 0

    def test_get_lost_features_same_plan(self, specialist):
        """Test no features lost for same plan."""
        lost = specialist._get_lost_features("basic", "basic")
        assert "No features will be lost" in lost

    def test_accepted_retention_positive(self, specialist):
        """Test detecting positive retention acceptance."""
        assert specialist._accepted_retention("Yes, that sounds good") is True
        assert specialist._accepted_retention("ok") is True
        assert specialist._accepted_retention("I'll take it") is True

    def test_accepted_retention_negative(self, specialist):
        """Test detecting negative retention acceptance."""
        assert specialist._accepted_retention("No, just downgrade") is False
        assert specialist._accepted_retention("Not interested") is False
        assert specialist._accepted_retention("Proceed with downgrade") is False

    def test_accepted_retention_ambiguous(self, specialist):
        """Test ambiguous responses default to rejection."""
        assert specialist._accepted_retention("Maybe later") is False
        assert specialist._accepted_retention("I'll think about it") is False

    # Edge Cases
    @pytest.mark.asyncio
    async def test_missing_customer_metadata(self, specialist):
        """Test handling missing customer metadata."""
        state = create_initial_state("Downgrade please")
        state["customer_metadata"] = {}

        result = await specialist.process(state)

        assert "agent_response" in result
        assert result["retention_offered"] is True

    @pytest.mark.asyncio
    async def test_get_next_billing_date(self, specialist):
        """Test billing date calculation."""
        date_str = specialist._get_next_billing_date()
        assert isinstance(date_str, str)
        assert len(date_str) > 0

    # Integration Tests
    @pytest.mark.asyncio
    async def test_full_retention_flow_accepted(self, specialist):
        """Test full flow: request -> retention offer -> accept."""
        # Step 1: Initial request
        state1 = create_initial_state(
            "I want to downgrade, it's too expensive",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250
                }
            }
        )
        state1["entities"] = {"target_plan": "basic"}

        result1 = await specialist.process(state1)
        assert result1["retention_offered"] is True

        # Step 2: Accept retention
        state2 = result1.copy()
        state2["current_message"] = "Yes, please!"
        state2["turn_count"] = 1

        result2 = await specialist.process(state2)
        assert result2["retention_successful"] is True
        assert result2["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_full_retention_flow_rejected(self, specialist):
        """Test full flow: request -> retention offer -> reject -> downgrade."""
        # Step 1: Initial request
        state1 = create_initial_state(
            "I want to downgrade",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250
                }
            }
        )
        state1["entities"] = {"target_plan": "basic"}

        result1 = await specialist.process(state1)
        assert result1["retention_offered"] is True

        # Step 2: Reject retention
        state2 = result1.copy()
        state2["current_message"] = "No, just downgrade please"
        state2["turn_count"] = 1

        result2 = await specialist.process(state2)
        assert result2["retention_successful"] is False
        assert result2["downgrade_processed"] is True
        assert result2["status"] == "resolved"
