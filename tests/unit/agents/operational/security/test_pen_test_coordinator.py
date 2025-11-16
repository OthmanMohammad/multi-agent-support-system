"""
Unit tests for Pen Test Coordinator Agent.

Tests penetration testing coordination, scheduling, and reporting.
Part of: TASK-2310 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.pen_test_coordinator import PenTestCoordinatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create PenTestCoordinatorAgent instance."""
    return PenTestCoordinatorAgent()


class TestPenTestCoordinatorInitialization:
    """Test Pen Test Coordinator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "pen_test_coordinator"
        assert agent.config.tier == "operational"


class TestPenTestCoordination:
    """Test penetration test coordination logic."""

    @pytest.mark.asyncio
    async def test_successful_test_scheduling(self, agent):
        """Test successful penetration test scheduling."""
        state = create_initial_state(
            message="Schedule penetration test",
            context={}
        )
        state["entities"] = {
            "test_type": "web_application",
            "scope": "production",
            "schedule_date": "2025-02-01"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_test_execution_coordination(self, agent):
        """Test penetration test execution coordination."""
        state = create_initial_state(message="Coordinate pen test", context={})
        state["entities"] = {
            "test_id": "PT-123",
            "action": "execute"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_findings_report_generation(self, agent):
        """Test findings report generation."""
        state = create_initial_state(message="Generate pen test report", context={})
        state["entities"] = {
            "test_id": "PT-123",
            "report_type": "executive_summary"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_test_type(self, agent):
        """Test handling of missing test type."""
        state = create_initial_state(message="Schedule test", context={})
        state["entities"] = {"scope": "staging"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
