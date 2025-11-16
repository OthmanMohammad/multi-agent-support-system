"""
Unit tests for Report Generator Agent.

Tests report generation, formatting, and distribution.
Part of: TASK-2018 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.report_generator import ReportGeneratorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ReportGeneratorAgent instance."""
    return ReportGeneratorAgent()


class TestReportGeneratorInitialization:
    """Test Report Generator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "report_generator"
        assert agent.config.tier == "operational"


class TestReportGeneration:
    """Test report generation logic."""

    @pytest.mark.asyncio
    async def test_successful_report_generation(self, agent):
        """Test successful report generation."""
        state = create_initial_state(
            message="Generate monthly report",
            context={}
        )
        state["entities"] = {"report_type": "monthly"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_executive_summary_generation(self, agent):
        """Test executive summary generation."""
        state = create_initial_state(
            message="Generate executive summary",
            context={}
        )
        state["entities"] = {"report_type": "executive"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_detailed_report_generation(self, agent):
        """Test detailed report generation."""
        state = create_initial_state(
            message="Generate detailed report",
            context={}
        )
        state["entities"] = {"detail_level": "detailed"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_data(self, agent):
        """Test handling of missing data in reports."""
        state = create_initial_state(message="Generate report", context={})

        result = await agent.process(state)

        assert result["status"] == "resolved"
