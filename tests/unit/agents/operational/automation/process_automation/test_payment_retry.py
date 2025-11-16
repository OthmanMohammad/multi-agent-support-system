"""
Unit tests for Payment Retry Agent.

Tests payment retry logic, scheduling, and notification.
Part of: TASK-2218 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.payment_retry import PaymentRetryAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create PaymentRetryAgent instance."""
    return PaymentRetryAgent()


class TestPaymentRetryInitialization:
    """Test Payment Retry initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "payment_retry"
        assert agent.config.tier == "operational"


class TestPaymentRetry:
    """Test payment retry logic."""

    @pytest.mark.asyncio
    async def test_successful_payment_retry(self, agent):
        """Test successful payment retry."""
        state = create_initial_state(
            message="Retry failed payment",
            context={}
        )
        state["entities"] = {
            "payment_id": "PAY-123",
            "customer_id": "CUST-123"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_retry_scheduling(self, agent):
        """Test payment retry scheduling."""
        state = create_initial_state(message="Schedule payment retry", context={})
        state["entities"] = {
            "payment_id": "PAY-123",
            "retry_schedule": "progressive"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_max_retries_exceeded(self, agent):
        """Test handling when max retries exceeded."""
        state = create_initial_state(message="Retry payment", context={})
        state["entities"] = {
            "payment_id": "PAY-123",
            "retry_count": 5
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
