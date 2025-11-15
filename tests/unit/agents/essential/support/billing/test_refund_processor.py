"""
Unit tests for Refund Processor Agent.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.agents.essential.support.billing.refund_processor import RefundProcessor
from src.workflow.state import create_initial_state


class TestRefundProcessor:
    """Test suite for Refund Processor."""

    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return RefundProcessor()

    @pytest.fixture
    def eligible_state(self):
        """Create state for eligible refund."""
        return create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "billing_cycle": "monthly",
                    "subscription_created_at": (datetime.now() - timedelta(days=15)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "active",
                    "email": "test@example.com"
                }
            }
        )

    @pytest.fixture
    def ineligible_state(self):
        """Create state for ineligible refund (past 30 days)."""
        return create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "subscription_created_at": (datetime.now() - timedelta(days=45)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "active"
                }
            }
        )

    # Initialization Tests
    def test_initialization(self, processor):
        """Test agent initializes correctly."""
        assert processor.config.name == "refund_processor"
        assert processor.config.type.value == "specialist"
        assert processor.config.temperature == 0.1
        assert processor.MONEY_BACK_GUARANTEE_DAYS == 30

    # Eligibility Tests
    def test_check_eligibility_within_30_days(self, processor, eligible_state):
        """Test eligibility check for subscription within 30 days."""
        eligibility = processor._check_eligibility(
            eligible_state["customer_metadata"],
            eligible_state
        )

        assert eligibility["eligible"] is True
        assert eligibility["within_money_back_period"] is True
        assert eligibility["no_previous_refunds"] is True
        assert eligibility["account_good_standing"] is True

    def test_check_eligibility_past_30_days(self, processor, ineligible_state):
        """Test eligibility check for old subscription."""
        eligibility = processor._check_eligibility(
            ineligible_state["customer_metadata"],
            ineligible_state
        )

        assert eligibility["eligible"] is False
        assert eligibility["within_money_back_period"] is False

    def test_check_eligibility_previous_refund(self, processor):
        """Test ineligibility due to previous refund."""
        state = create_initial_state(
            "I need another refund",
            context={
                "customer_metadata": {
                    "subscription_created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "previous_refund_count": 1,
                    "account_status": "active"
                }
            }
        )

        eligibility = processor._check_eligibility(
            state["customer_metadata"],
            state
        )

        assert eligibility["eligible"] is False
        assert eligibility["no_previous_refunds"] is False

    def test_check_eligibility_bad_account_status(self, processor):
        """Test ineligibility due to bad account status."""
        state = create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "subscription_created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "suspended"
                }
            }
        )

        eligibility = processor._check_eligibility(
            state["customer_metadata"],
            state
        )

        assert eligibility["eligible"] is False
        assert eligibility["account_good_standing"] is False

    # Refund Calculation Tests
    def test_calculate_full_refund_monthly(self, processor):
        """Test full refund calculation for monthly plan."""
        customer_metadata = {
            "mrr": 100,
            "billing_cycle": "monthly"
        }
        eligibility = {"refund_type": "full"}

        amount = processor._calculate_refund(customer_metadata, eligibility)

        assert amount == 100

    def test_calculate_full_refund_annual(self, processor):
        """Test full refund calculation for annual plan."""
        customer_metadata = {
            "mrr": 100,
            "billing_cycle": "annual"
        }
        eligibility = {"refund_type": "full"}

        amount = processor._calculate_refund(customer_metadata, eligibility)

        assert amount == 1200  # 100 * 12

    def test_calculate_prorated_refund(self, processor):
        """Test prorated refund calculation."""
        customer_metadata = {
            "mrr": 100,
            "months_remaining": 6,
            "monthly_rate": 100
        }
        eligibility = {"refund_type": "prorated"}

        amount = processor._calculate_refund(customer_metadata, eligibility)

        assert amount == 600  # 100 * 6

    # Main Processing Tests
    @pytest.mark.asyncio
    async def test_process_eligible_refund(self, processor, eligible_state):
        """Test processing eligible refund request."""
        result = await processor.process(eligible_state)

        assert result["refund_processed"] is True
        assert result["refund_amount"] == 100
        assert "processed successfully" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_ineligible_refund(self, processor, ineligible_state):
        """Test processing ineligible refund request."""
        result = await processor.process(ineligible_state)

        assert result["refund_processed"] is False
        assert result["refund_amount"] == 0
        assert "not eligible" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    # Explanation Tests
    def test_explain_ineligibility_multiple_reasons(self, processor):
        """Test explanation with multiple reasons."""
        eligibility = {
            "within_money_back_period": False,
            "no_previous_refunds": False,
            "account_good_standing": True,
            "days_since_purchase": 45
        }

        explanation = processor._explain_ineligibility(eligibility)

        assert "30-day" in explanation.lower()
        assert "already received a refund" in explanation.lower()
        assert "alternative" in explanation.lower()

    def test_explain_ineligibility_single_reason(self, processor):
        """Test explanation with single reason."""
        eligibility = {
            "within_money_back_period": False,
            "no_previous_refunds": True,
            "account_good_standing": True,
            "days_since_purchase": 35
        }

        explanation = processor._explain_ineligibility(eligibility)

        assert "35 days old" in explanation
        assert "alternative" in explanation.lower()

    # Edge Cases
    @pytest.mark.asyncio
    async def test_missing_email_in_metadata(self, processor):
        """Test handling missing email in customer metadata."""
        state = create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "subscription_created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "active",
                    "mrr": 50,
                    "billing_cycle": "monthly"
                }
            }
        )

        result = await processor.process(state)

        assert "agent_response" in result
        # Should handle gracefully even without email

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, processor):
        """Test handling invalid date format."""
        state = create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "subscription_created_at": "invalid-date",
                    "previous_refund_count": 0,
                    "account_status": "active",
                    "mrr": 50
                }
            }
        )

        # Should not raise exception
        result = await processor.process(state)
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_zero_mrr(self, processor):
        """Test refund with zero MRR (free plan)."""
        state = create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "plan": "free",
                    "mrr": 0,
                    "billing_cycle": "monthly",
                    "subscription_created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "active"
                }
            }
        )

        result = await processor.process(state)

        assert result["refund_amount"] == 0

    # Integration Tests
    @pytest.mark.asyncio
    async def test_annual_plan_full_refund(self, processor):
        """Test full refund for annual plan within 30 days."""
        state = create_initial_state(
            "I want a refund on my annual plan",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 200,
                    "billing_cycle": "annual",
                    "subscription_created_at": (datetime.now() - timedelta(days=20)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "active",
                    "email": "annual@example.com"
                }
            }
        )

        result = await processor.process(state)

        assert result["refund_processed"] is True
        assert result["refund_amount"] == 2400  # 200 * 12
        assert "2400" in result["agent_response"]
