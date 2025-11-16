"""
Unit tests for Cohort Analyzer Agent.

Tests cohort analysis, retention tracking, and segment comparison.
Part of: TASK-2015 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.cohort_analyzer import CohortAnalyzerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CohortAnalyzerAgent instance."""
    return CohortAnalyzerAgent()


class TestCohortAnalyzerInitialization:
    """Test Cohort Analyzer initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "cohort_analyzer"
        assert agent.config.tier == "operational"


class TestCohortAnalysis:
    """Test cohort analysis logic."""

    @pytest.mark.asyncio
    async def test_successful_cohort_analysis(self, agent):
        """Test successful cohort analysis."""
        state = create_initial_state(
            message="Analyze customer cohorts",
            context={}
        )
        state["entities"] = {"cohort_type": "monthly", "metric": "retention"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_retention_cohort_analysis(self, agent):
        """Test retention cohort analysis."""
        state = create_initial_state(
            message="Analyze retention by cohort",
            context={}
        )
        state["entities"] = {"analysis_type": "retention"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_revenue_cohort_analysis(self, agent):
        """Test revenue cohort analysis."""
        state = create_initial_state(
            message="Analyze revenue by cohort",
            context={}
        )
        state["entities"] = {"analysis_type": "revenue"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestCohortSegmentation:
    """Test cohort segmentation."""

    @pytest.mark.asyncio
    async def test_monthly_cohorts(self, agent):
        """Test monthly cohort segmentation."""
        state = create_initial_state(message="Create monthly cohorts", context={})
        state["entities"] = {"cohort_period": "monthly"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_weekly_cohorts(self, agent):
        """Test weekly cohort segmentation."""
        state = create_initial_state(message="Create weekly cohorts", context={})
        state["entities"] = {"cohort_period": "weekly"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_small_cohorts(self, agent):
        """Test handling of small cohort sizes."""
        state = create_initial_state(message="Analyze cohorts", context={})
        state["entities"] = {"min_cohort_size": 1}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_handles_missing_cohort_type(self, agent):
        """Test handling of missing cohort type."""
        state = create_initial_state(message="Analyze cohorts", context={})
        state["entities"] = {}

        result = await agent.process(state)

        assert result["status"] == "resolved"
