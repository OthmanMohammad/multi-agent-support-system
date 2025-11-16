"""
Unit tests for Invoice Sender Agent.

Tests invoice generation, sending, and tracking.
Part of: TASK-2217 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.invoice_sender import InvoiceSenderAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create InvoiceSenderAgent instance."""
    return InvoiceSenderAgent()


class TestInvoiceSenderInitialization:
    """Test Invoice Sender initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "invoice_sender"
        assert agent.config.tier == "operational"


class TestInvoiceSending:
    """Test invoice sending logic."""

    @pytest.mark.asyncio
    async def test_successful_invoice_sending(self, agent):
        """Test successful invoice sending."""
        state = create_initial_state(
            message="Send invoice",
            context={}
        )
        state["entities"] = {
            "invoice_id": "INV-123",
            "customer_email": "customer@example.com"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_automated_invoice_generation(self, agent):
        """Test automated invoice generation and sending."""
        state = create_initial_state(message="Generate and send invoice", context={})
        state["entities"] = {
            "customer_id": "CUST-123",
            "amount": 500,
            "period": "2025-01"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_invoice_id(self, agent):
        """Test handling of missing invoice ID."""
        state = create_initial_state(message="Send invoice", context={})
        state["entities"] = {"customer_email": "customer@example.com"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
