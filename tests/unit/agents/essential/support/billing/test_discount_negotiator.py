"""
Unit tests for Discount Negotiator Agent.
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.support.billing.discount_negotiator import DiscountNegotiator
from src.workflow.state import create_initial_state


class TestDiscountNegotiator:
    """Test suite for Discount Negotiator."""

    @pytest.fixture
    def negotiator(self):
        """Create negotiator instance for testing."""
        return DiscountNegotiator()

    @pytest.fixture
    def base_state(self):
        """Create base state for testing."""
        return create_initial_state(
            "Can I get a discount?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "seats_total": 5
                }
            }
        )

    # Initialization Tests
    def test_initialization(self, negotiator):
        """Test agent initializes correctly."""
        assert negotiator.config.name == "discount_negotiator"
        assert negotiator.config.type.value == "specialist"
        assert negotiator.MAX_AUTO_APPROVE_PERCENT == 30
        assert len(negotiator.AVAILABLE_DISCOUNTS) > 0

    def test_available_discounts_structure(self, negotiator):
        """Test all discount programs have required structure."""
        for program_name, program in negotiator.AVAILABLE_DISCOUNTS.items():
            assert "percent" in program
            assert "description" in program
            assert "auto_approve" in program
            assert "requires_verification" in program

    # Reason Inference Tests
    def test_infer_reason_nonprofit(self, negotiator):
        """Test inferring nonprofit reason."""
        reason = negotiator._infer_reason_from_message("we're a nonprofit organization")
        assert reason == "nonprofit"

    def test_infer_reason_student(self, negotiator):
        """Test inferring student reason."""
        reason = negotiator._infer_reason_from_message("i'm a student at university")
        assert reason == "student"

    def test_infer_reason_startup(self, negotiator):
        """Test inferring startup reason."""
        reason = negotiator._infer_reason_from_message("we just started our company")
        assert reason == "startup"

    def test_infer_reason_budget(self, negotiator):
        """Test inferring budget reason."""
        reason = negotiator._infer_reason_from_message("it's too expensive for our budget")
        assert reason == "budget"

    def test_infer_reason_volume(self, negotiator):
        """Test inferring volume reason."""
        reason = negotiator._infer_reason_from_message("we have many users")
        assert reason == "volume"

    def test_infer_reason_annual(self, negotiator):
        """Test inferring annual reason."""
        reason = negotiator._infer_reason_from_message("if i pay annually can i get discount?")
        assert reason == "annual"

    # Discount Request Extraction Tests
    def test_extract_discount_request_from_entities(self, negotiator, base_state):
        """Test extracting discount request from entities."""
        base_state["entities"] = {
            "requested_discount_percent": 25,
            "discount_reason": "budget"
        }

        details = negotiator._extract_discount_request(
            base_state,
            base_state["customer_metadata"]
        )

        assert details["requested_percent"] == 25
        assert details["reason"] == "budget"

    def test_extract_discount_request_from_message_50(self, negotiator, base_state):
        """Test extracting 50% from message."""
        base_state["current_message"] = "can i get 50% off?"

        details = negotiator._extract_discount_request(
            base_state,
            base_state["customer_metadata"]
        )

        assert details["requested_percent"] == 50

    def test_extract_discount_request_from_message_30(self, negotiator, base_state):
        """Test extracting 30% from message."""
        base_state["current_message"] = "can i get 30% discount?"

        details = negotiator._extract_discount_request(
            base_state,
            base_state["customer_metadata"]
        )

        assert details["requested_percent"] == 30

    def test_extract_discount_request_default(self, negotiator, base_state):
        """Test default discount request."""
        base_state["current_message"] = "can i get a discount?"

        details = negotiator._extract_discount_request(
            base_state,
            base_state["customer_metadata"]
        )

        assert details["requested_percent"] == 20  # Default

    # Qualification Tests
    def test_customer_qualifies_nonprofit(self, negotiator):
        """Test nonprofit qualification."""
        customer_metadata = {"is_nonprofit": True}
        discount_details = {
            "reason": "nonprofit",
            "requested_percent": 50
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is True

    def test_customer_not_qualifies_nonprofit(self, negotiator):
        """Test nonprofit disqualification."""
        customer_metadata = {"is_nonprofit": False}
        discount_details = {
            "reason": "nonprofit",
            "requested_percent": 50
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is False

    def test_customer_qualifies_student(self, negotiator):
        """Test student qualification."""
        customer_metadata = {"is_student": True}
        discount_details = {
            "reason": "student",
            "requested_percent": 50
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is True

    def test_customer_qualifies_volume(self, negotiator):
        """Test volume discount qualification."""
        customer_metadata = {"seats_total": 15}
        discount_details = {
            "reason": "volume",
            "requested_percent": 15
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is True

    def test_customer_not_qualifies_volume(self, negotiator):
        """Test volume discount disqualification (too few seats)."""
        customer_metadata = {"seats_total": 5}
        discount_details = {
            "reason": "volume",
            "requested_percent": 15
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is False

    def test_customer_qualifies_startup(self, negotiator):
        """Test startup qualification."""
        customer_metadata = {"company_age_days": 365}  # 1 year old
        discount_details = {
            "reason": "startup",
            "requested_percent": 30
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is True

    def test_customer_not_qualifies_startup(self, negotiator):
        """Test startup disqualification (too old)."""
        customer_metadata = {"company_age_days": 800}  # >2 years
        discount_details = {
            "reason": "startup",
            "requested_percent": 30
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is False

    def test_customer_qualifies_annual(self, negotiator):
        """Test annual discount (always qualifies)."""
        customer_metadata = {}
        discount_details = {
            "reason": "annual",
            "requested_percent": 20
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is True

    def test_customer_qualifies_budget(self, negotiator):
        """Test budget discount (always qualifies within limit)."""
        customer_metadata = {}
        discount_details = {
            "reason": "budget",
            "requested_percent": 20
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is True

    def test_customer_not_qualifies_exceeds_program_limit(self, negotiator):
        """Test disqualification when requested percent exceeds program limit."""
        customer_metadata = {}
        discount_details = {
            "reason": "budget",
            "requested_percent": 25  # Budget program only allows 20%
        }

        qualifies = negotiator._customer_qualifies(
            customer_metadata,
            discount_details
        )

        assert qualifies is False

    # Main Processing Tests - Auto Approve
    @pytest.mark.asyncio
    async def test_process_auto_approve_within_limit(self, negotiator, base_state):
        """Test auto-approving discount within limit."""
        base_state["entities"] = {
            "requested_discount_percent": 20,
            "discount_reason": "budget"
        }

        result = await negotiator.process(base_state)

        assert result["discount_approved"] is True
        assert result["discount_percent"] == 20
        assert result["discount_reason"] == "budget"
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_auto_approve_nonprofit_verified(self, negotiator):
        """Test auto-approving nonprofit discount with verification."""
        state = create_initial_state(
            "We're a nonprofit, can we get 50% off?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "is_nonprofit": True,
                    "verified_nonprofit": True
                }
            }
        )
        state["entities"] = {
            "requested_discount_percent": 50,
            "discount_reason": "nonprofit"
        }

        result = await negotiator.process(state)

        assert result["discount_approved"] is True
        assert result["discount_percent"] == 50

    @pytest.mark.asyncio
    async def test_process_nonprofit_needs_verification(self, negotiator):
        """Test nonprofit discount requires verification."""
        state = create_initial_state(
            "We're a nonprofit",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "is_nonprofit": True,
                    "verified_nonprofit": False
                }
            }
        )
        state["entities"] = {
            "requested_discount_percent": 50,
            "discount_reason": "nonprofit"
        }

        result = await negotiator.process(state)

        assert result["discount_approved"] is True
        assert "verification" in result["agent_response"].lower()

    # Main Processing Tests - Escalate
    @pytest.mark.asyncio
    async def test_process_escalate_above_limit(self, negotiator, base_state):
        """Test escalating discount above auto-approve limit."""
        base_state["entities"] = {"requested_discount_percent": 40}

        result = await negotiator.process(base_state)

        assert result["should_escalate"] is True
        assert result["discount_approved"] is False
        assert "sales team" in result["agent_response"].lower()
        assert result["status"] == "escalated"

    @pytest.mark.asyncio
    async def test_process_escalate_custom_pricing(self, negotiator, base_state):
        """Test escalating for custom pricing needs."""
        base_state["entities"] = {"requested_discount_percent": 35}

        result = await negotiator.process(base_state)

        assert result["should_escalate"] is True
        assert "custom" in result["agent_response"].lower()

    # Main Processing Tests - Alternative Offers
    @pytest.mark.asyncio
    async def test_process_offer_alternative_not_qualified(self, negotiator):
        """Test offering alternative when not qualified."""
        state = create_initial_state(
            "Can I get a nonprofit discount?",
            context={
                "customer_metadata": {
                    "plan": "basic",
                    "mrr": 50,
                    "is_nonprofit": False  # Not qualified
                }
            }
        )
        state["entities"] = {
            "requested_discount_percent": 50,
            "discount_reason": "nonprofit"
        }

        result = await negotiator.process(state)

        assert result["discount_approved"] is False
        assert result.get("alternative_offered") is True
        assert "alternative" in result["agent_response"].lower() or "annual" in result["agent_response"].lower()

    # Approval Message Tests
    @pytest.mark.asyncio
    async def test_approve_discount_message_format(self, negotiator, base_state):
        """Test discount approval message formatting."""
        discount_details = {
            "requested_percent": 20,
            "reason": "budget",
            "duration_months": 6
        }

        result = await negotiator._approve_discount(
            base_state["customer_metadata"],
            discount_details,
            base_state
        )

        assert "20%" in result
        assert "$80" in result  # 100 - 20%
        assert "$20" in result  # Savings

    # Alternative Offer Tests
    def test_offer_alternative_discount(self, negotiator):
        """Test alternative discount offer."""
        customer_metadata = {"mrr": 100}
        discount_details = {"requested_percent": 25}

        result = negotiator._offer_alternative_discount(
            customer_metadata,
            discount_details
        )

        assert "annual" in result.lower()
        assert "20%" in result
        assert "volume" in result.lower()

    # Escalation Tests
    def test_escalate_for_approval(self, negotiator):
        """Test escalation message."""
        discount_details = {"requested_percent": 40}
        customer_metadata = {"mrr": 100}

        result = negotiator._escalate_for_approval(
            discount_details,
            customer_metadata
        )

        assert "40%" in result
        assert "sales team" in result.lower()
        assert "custom" in result.lower()

    # Edge Cases
    @pytest.mark.asyncio
    async def test_missing_discount_percent_uses_default(self, negotiator, base_state):
        """Test missing discount percent uses default."""
        # No entities provided
        result = await negotiator.process(base_state)

        # Should default to 20%
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_zero_mrr_discount(self, negotiator):
        """Test discount for free plan (zero MRR)."""
        state = create_initial_state(
            "Can I get a discount?",
            context={
                "customer_metadata": {
                    "plan": "free",
                    "mrr": 0
                }
            }
        )
        state["entities"] = {"requested_discount_percent": 20}

        result = await negotiator.process(state)

        # Should handle gracefully
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_volume_discount_with_exact_minimum(self, negotiator):
        """Test volume discount with exactly minimum seats."""
        state = create_initial_state(
            "We have 10 users, can we get a volume discount?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250,
                    "seats_total": 10  # Exactly the minimum
                }
            }
        )
        state["entities"] = {
            "requested_discount_percent": 15,
            "discount_reason": "volume"
        }

        result = await negotiator.process(state)

        assert result["discount_approved"] is True

    # Integration Tests
    @pytest.mark.asyncio
    async def test_full_budget_discount_flow(self, negotiator):
        """Test complete flow for budget discount."""
        state = create_initial_state(
            "It's too expensive, can I get 20% off for 6 months?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250,
                    "seats_total": 10
                }
            }
        )
        state["entities"] = {
            "requested_discount_percent": 20,
            "discount_reason": "budget",
            "duration_months": 6
        }

        result = await negotiator.process(state)

        assert result["discount_approved"] is True
        assert result["discount_percent"] == 20
        assert result["response_confidence"] == 0.9
        assert "$200" in result["agent_response"]  # 250 - 20%

    @pytest.mark.asyncio
    async def test_full_escalation_flow(self, negotiator):
        """Test complete flow for escalation."""
        state = create_initial_state(
            "We need 45% off for our large enterprise deal",
            context={
                "customer_metadata": {
                    "plan": "enterprise",
                    "mrr": 5000
                }
            }
        )
        state["entities"] = {"requested_discount_percent": 45}

        result = await negotiator.process(state)

        assert result["should_escalate"] is True
        assert result["discount_approved"] is False
        assert result["status"] == "escalated"
        assert result["next_agent"] == "escalation"
