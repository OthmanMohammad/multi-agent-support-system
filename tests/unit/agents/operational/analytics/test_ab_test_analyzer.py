"""
Unit tests for A/B Test Analyzer Agent.

Tests A/B test analysis, statistical significance, and winner determination.
Part of: TASK-2017 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.ab_test_analyzer import ABTestAnalyzerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ABTestAnalyzerAgent instance."""
    return ABTestAnalyzerAgent()


class TestABTestAnalyzerInitialization:
    """Test A/B Test Analyzer initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "ab_test_analyzer"
        assert agent.config.tier == "operational"


class TestABTestAnalysis:
    """Test A/B test analysis logic."""

    @pytest.mark.asyncio
    async def test_successful_ab_test_analysis(self, agent):
        """Test successful A/B test analysis."""
        state = create_initial_state(
            message="Analyze A/B test results",
            context={}
        )
        state["entities"] = {"test_id": "test_123"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_statistical_significance_check(self, agent):
        """Test statistical significance checking."""
        state = create_initial_state(
            message="Check statistical significance",
            context={}
        )
        state["entities"] = {"significance_level": 0.95}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_winner_determination(self, agent):
        """Test winner determination."""
        state = create_initial_state(
            message="Determine test winner",
            context={}
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_inconclusive_test(self, agent):
        """Test handling of inconclusive test results."""
        state = create_initial_state(message="Analyze test", context={})
        state["entities"] = {"sample_size": 10}  # Too small

        result = await agent.process(state)

        assert result["status"] == "resolved"
