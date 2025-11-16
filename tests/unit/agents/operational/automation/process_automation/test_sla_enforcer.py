"""
Unit tests for SLA Enforcer Agent.

Tests SLA monitoring, enforcement, and violation tracking.
Part of: TASK-2213 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.sla_enforcer import SLAEnforcerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create SLAEnforcerAgent instance."""
    return SLAEnforcerAgent()


class TestSLAEnforcerInitialization:
    """Test SLA Enforcer initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "sla_enforcer"
        assert agent.config.tier == "operational"


class TestSLAEnforcement:
    """Test SLA enforcement logic."""

    @pytest.mark.asyncio
    async def test_successful_sla_check(self, agent):
        """Test successful SLA compliance check."""
        state = create_initial_state(
            message="Check SLA compliance",
            context={}
        )
        state["entities"] = {
            "ticket_id": "TICK-123",
            "sla_type": "response_time"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_sla_violation_detection(self, agent):
        """Test SLA violation detection."""
        state = create_initial_state(message="Check for SLA violations", context={})
        state["entities"] = {"check_type": "violations"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_sla_type(self, agent):
        """Test handling of missing SLA type."""
        state = create_initial_state(message="Check SLA", context={})
        state["entities"] = {"ticket_id": "TICK-123"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
