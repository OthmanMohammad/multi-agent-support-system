"""
Unit tests for Payment Troubleshooter Agent.
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.support.billing.payment_troubleshooter import PaymentTroubleshooter
from src.workflow.state import create_initial_state


class TestPaymentTroubleshooter:
    """Test suite for Payment Troubleshooter."""

    @pytest.fixture
    def troubleshooter(self):
        """Create troubleshooter instance for testing."""
        return PaymentTroubleshooter()

    @pytest.fixture
    def base_state(self):
        """Create base state for testing."""
        return create_initial_state(
            "My payment failed",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100
                }
            }
        )

    # Initialization Tests
    def test_initialization(self, troubleshooter):
        """Test agent initializes correctly."""
        assert troubleshooter.config.name == "payment_troubleshooter"
        assert troubleshooter.config.type.value == "specialist"
        assert troubleshooter.config.tier == "essential"
        assert len(troubleshooter.ERROR_CODES) > 0

    def test_error_codes_structure(self, troubleshooter):
        """Test error codes have correct structure."""
        for code, info in troubleshooter.ERROR_CODES.items():
            assert "description" in info
            assert "category" in info
            assert "severity" in info

    # Error Extraction Tests
    def test_extract_payment_error_from_entities(self, troubleshooter, base_state):
        """Test extracting error code from entities."""
        base_state["entities"] = {"payment_error_code": "card_declined"}

        error_code = troubleshooter._extract_payment_error(
            base_state,
            base_state["customer_metadata"]
        )

        assert error_code == "card_declined"

    def test_extract_payment_error_from_metadata(self, troubleshooter, base_state):
        """Test extracting error code from customer metadata."""
        base_state["customer_metadata"]["last_payment_error"] = "expired_card"

        error_code = troubleshooter._extract_payment_error(
            base_state,
            base_state["customer_metadata"]
        )

        assert error_code == "expired_card"

    def test_extract_payment_error_from_message_declined(self, troubleshooter, base_state):
        """Test inferring 'declined' from message."""
        base_state["current_message"] = "My card was declined"

        error_code = troubleshooter._extract_payment_error(
            base_state,
            base_state["customer_metadata"]
        )

        assert error_code == "card_declined"

    def test_extract_payment_error_from_message_expired(self, troubleshooter, base_state):
        """Test inferring 'expired' from message."""
        base_state["current_message"] = "My card has expired"

        error_code = troubleshooter._extract_payment_error(
            base_state,
            base_state["customer_metadata"]
        )

        assert error_code == "expired_card"

    def test_extract_payment_error_from_message_3ds(self, troubleshooter, base_state):
        """Test inferring '3DS failure' from message."""
        base_state["current_message"] = "3D Secure authentication failed"

        error_code = troubleshooter._extract_payment_error(
            base_state,
            base_state["customer_metadata"]
        )

        assert error_code == "3ds_failed"

    # Diagnosis Tests
    def test_diagnose_card_declined(self, troubleshooter):
        """Test diagnosing card declined error."""
        diagnosis = troubleshooter._diagnose_payment_failure("card_declined", {})

        assert diagnosis["error_code"] == "card_declined"
        assert diagnosis["category"] == "card_issue"
        assert "declined" in diagnosis["description"].lower()

    def test_diagnose_3ds_failed(self, troubleshooter):
        """Test diagnosing 3DS failure."""
        diagnosis = troubleshooter._diagnose_payment_failure("3ds_failed", {})

        assert diagnosis["category"] == "authentication"
        assert "3d secure" in diagnosis["description"].lower()

    def test_diagnose_insufficient_funds(self, troubleshooter):
        """Test diagnosing insufficient funds."""
        diagnosis = troubleshooter._diagnose_payment_failure("insufficient_funds", {})

        assert diagnosis["category"] == "funds"
        assert "insufficient" in diagnosis["description"].lower()

    def test_diagnose_fraud_suspected(self, troubleshooter):
        """Test diagnosing fraud flag."""
        diagnosis = troubleshooter._diagnose_payment_failure("fraud_suspected", {})

        assert diagnosis["category"] == "fraud"
        assert "fraud" in diagnosis["description"].lower()

    def test_diagnose_unknown_error(self, troubleshooter):
        """Test diagnosing unknown error code."""
        diagnosis = troubleshooter._diagnose_payment_failure("unknown_code", {})

        assert diagnosis["category"] == "unknown"
        assert diagnosis["description"] == "Unknown payment error"

    # Solution Tests
    def test_get_solution_card_issue_expired(self, troubleshooter):
        """Test solution for expired card."""
        diagnosis = {
            "error_code": "expired_card",
            "category": "card_issue"
        }

        solution = troubleshooter._get_solution(diagnosis, {})

        assert len(solution["steps"]) > 0
        assert "update" in solution["help_text"].lower()
        assert any("update" in step.lower() for step in solution["steps"])

    def test_get_solution_card_issue_cvc(self, troubleshooter):
        """Test solution for incorrect CVC."""
        diagnosis = {
            "error_code": "incorrect_cvc",
            "category": "card_issue"
        }

        solution = troubleshooter._get_solution(diagnosis, {})

        assert "cvc" in solution["help_text"].lower() or "cvv" in solution["help_text"].lower()

    def test_get_solution_authentication(self, troubleshooter):
        """Test solution for authentication failure."""
        diagnosis = {
            "error_code": "3ds_failed",
            "category": "authentication"
        }

        solution = troubleshooter._get_solution(diagnosis, {})

        assert "3d secure" in solution["help_text"].lower() or "authentication" in solution["help_text"].lower()
        assert len(solution["steps"]) > 0

    def test_get_solution_authentication_timeout(self, troubleshooter):
        """Test solution for authentication timeout."""
        diagnosis = {
            "error_code": "3ds_timeout",
            "category": "authentication"
        }

        solution = troubleshooter._get_solution(diagnosis, {})

        assert "timeout" in solution["help_text"].lower() or "quickly" in solution["help_text"].lower()

    def test_get_solution_funds(self, troubleshooter):
        """Test solution for insufficient funds."""
        diagnosis = {
            "error_code": "insufficient_funds",
            "category": "funds"
        }

        solution = troubleshooter._get_solution(diagnosis, {})

        assert "funds" in solution["help_text"].lower() or "balance" in solution["help_text"].lower()

    def test_get_solution_fraud(self, troubleshooter):
        """Test solution for fraud flag."""
        diagnosis = {
            "error_code": "fraud_suspected",
            "category": "fraud"
        }

        solution = troubleshooter._get_solution(diagnosis, {})

        assert "bank" in solution["help_text"].lower()
        assert "fraud" in solution["help_text"].lower() or "security" in solution["help_text"].lower()

    def test_get_solution_rate_limit(self, troubleshooter):
        """Test solution for rate limit error."""
        diagnosis = {
            "error_code": "rate_limit",
            "category": "system"
        }

        solution = troubleshooter._get_solution(diagnosis, {})

        assert "wait" in solution["help_text"].lower()

    # Main Processing Tests
    @pytest.mark.asyncio
    async def test_process_card_declined(self, troubleshooter, base_state):
        """Test processing card declined error."""
        base_state["entities"] = {"payment_error_code": "card_declined"}

        result = await troubleshooter.process(base_state)

        assert result["payment_diagnosis"] == "card_issue"
        assert result["payment_error_code"] == "card_declined"
        assert "declined" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_expired_card(self, troubleshooter, base_state):
        """Test processing expired card error."""
        base_state["current_message"] = "My card expired"

        result = await troubleshooter.process(base_state)

        assert result["payment_diagnosis"] == "card_issue"
        assert "update" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_process_3ds_failure(self, troubleshooter, base_state):
        """Test processing 3DS authentication failure."""
        base_state["entities"] = {"payment_error_code": "3ds_failed"}

        result = await troubleshooter.process(base_state)

        assert result["payment_diagnosis"] == "authentication"
        assert "3d secure" in result["agent_response"].lower() or "authentication" in result["agent_response"].lower()

    # Response Formatting Tests
    def test_format_troubleshooting_response(self, troubleshooter):
        """Test formatting of troubleshooting response."""
        diagnosis = {
            "description": "Card was declined",
            "category": "card_issue",
            "severity": "high"
        }
        solution = {
            "steps": ["Step 1", "Step 2", "Step 3"],
            "help_text": "Contact your bank"
        }

        response = troubleshooter._format_troubleshooting_response(
            diagnosis,
            solution,
            {}
        )

        assert "what happened" in response.lower()
        assert "how to fix" in response.lower()
        assert "step 1" in response.lower()
        assert "step 2" in response.lower()
        assert "contact your bank" in response.lower()

    # Edge Cases
    @pytest.mark.asyncio
    async def test_missing_error_info(self, troubleshooter, base_state):
        """Test handling completely missing error information."""
        # No error code in entities or metadata
        result = await troubleshooter.process(base_state)

        # Should default to card_declined
        assert "agent_response" in result
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_multiple_error_indicators(self, troubleshooter, base_state):
        """Test when message has multiple error indicators."""
        base_state["current_message"] = "My card was declined and it's expired"

        result = await troubleshooter.process(base_state)

        # Should pick one (likely 'declined' as it comes first)
        assert result["payment_diagnosis"] in ["card_issue"]

    # Integration Tests
    @pytest.mark.asyncio
    async def test_full_card_declined_flow(self, troubleshooter):
        """Test complete flow for card declined."""
        state = create_initial_state(
            "My payment was declined by the bank",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250,
                    "last_payment_error": "card_declined"
                }
            }
        )

        result = await troubleshooter.process(state)

        assert result["payment_diagnosis"] == "card_issue"
        assert result["response_confidence"] == 0.9
        assert "bank" in result["agent_response"].lower()
        assert "settings" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_full_3ds_flow(self, troubleshooter):
        """Test complete flow for 3DS failure."""
        state = create_initial_state(
            "3D Secure authentication didn't work",
            context={
                "customer_metadata": {
                    "plan": "basic",
                    "mrr": 100
                }
            }
        )

        result = await troubleshooter.process(state)

        assert result["payment_diagnosis"] == "authentication"
        assert "authentication" in result["agent_response"].lower() or "3d secure" in result["agent_response"].lower()
