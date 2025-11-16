"""
Unit tests for Handoff Automator Agent.

Tests automated handoffs, transitions, and notifications.
Part of: TASK-2214 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.handoff_automator import HandoffAutomatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create HandoffAutomatorAgent instance."""
    return HandoffAutomatorAgent()


class TestHandoffAutomatorInitialization:
    """Test Handoff Automator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "handoff_automator"
        assert agent.config.tier == "operational"


class TestHandoffAutomation:
    """Test handoff automation logic."""

    @pytest.mark.asyncio
    async def test_successful_handoff(self, agent):
        """Test successful automated handoff."""
        state = create_initial_state(
            message="Handoff to specialist",
            context={}
        )
        state["entities"] = {
            "from_agent": "general_support",
            "to_agent": "billing_specialist",
            "ticket_id": "TICK-123"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_escalation_handoff(self, agent):
        """Test escalation handoff."""
        state = create_initial_state(message="Escalate to manager", context={})
        state["entities"] = {
            "escalation_type": "manager",
            "reason": "customer_request"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_target_agent(self, agent):
        """Test handling of missing target agent."""
        state = create_initial_state(message="Handoff ticket", context={})
        state["entities"] = {"ticket_id": "TICK-123"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
