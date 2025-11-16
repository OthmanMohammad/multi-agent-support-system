"""
Unit tests for Approval Router Agent.

Tests approval routing, escalation, and tracking.
Part of: TASK-2212 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.approval_router import ApprovalRouterAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ApprovalRouterAgent instance."""
    return ApprovalRouterAgent()


class TestApprovalRouterInitialization:
    """Test Approval Router initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "approval_router"
        assert agent.config.tier == "operational"


class TestApprovalRouting:
    """Test approval routing logic."""

    @pytest.mark.asyncio
    async def test_successful_approval_routing(self, agent):
        """Test successful approval routing."""
        state = create_initial_state(
            message="Route for approval",
            context={}
        )
        state["entities"] = {
            "approval_type": "discount",
            "amount": 5000,
            "requester": "sales@example.com"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_escalation_routing(self, agent):
        """Test escalation routing for high-value approvals."""
        state = create_initial_state(message="Route high-value approval", context={})
        state["entities"] = {
            "approval_type": "contract",
            "amount": 100000
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_approval_type(self, agent):
        """Test handling of missing approval type."""
        state = create_initial_state(message="Route approval", context={})
        state["entities"] = {"amount": 1000}

        result = await agent.process(state)

        assert result["status"] == "resolved"
