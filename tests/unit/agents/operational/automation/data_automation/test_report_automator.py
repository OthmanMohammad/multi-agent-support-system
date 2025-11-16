"""
Unit tests for Report Automator Agent.

Tests automated report generation, scheduling, and distribution.
Part of: TASK-2210 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.data_automation.report_automator import ReportAutomatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ReportAutomatorAgent instance."""
    return ReportAutomatorAgent()


class TestReportAutomatorInitialization:
    """Test Report Automator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "report_automator"
        assert agent.config.tier == "operational"


class TestReportAutomation:
    """Test report automation logic."""

    @pytest.mark.asyncio
    async def test_successful_report_automation(self, agent):
        """Test successful automated report generation."""
        state = create_initial_state(
            message="Automate weekly report",
            context={}
        )
        state["entities"] = {
            "report_type": "weekly_sales",
            "schedule": "every_monday",
            "recipients": ["manager@example.com"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_scheduled_report_generation(self, agent):
        """Test scheduled report generation."""
        state = create_initial_state(message="Schedule report", context={})
        state["entities"] = {
            "report_type": "monthly_metrics",
            "schedule": "first_of_month"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_schedule(self, agent):
        """Test handling of missing schedule."""
        state = create_initial_state(message="Automate report", context={})
        state["entities"] = {"report_type": "sales"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
