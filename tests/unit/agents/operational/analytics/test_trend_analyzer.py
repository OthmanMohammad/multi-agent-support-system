"""
Unit tests for Trend Analyzer Agent.

Tests trend analysis, forecasting, and pattern recognition.
Part of: TASK-2014 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.trend_analyzer import TrendAnalyzerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create TrendAnalyzerAgent instance."""
    return TrendAnalyzerAgent()


class TestTrendAnalyzerInitialization:
    """Test Trend Analyzer initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "trend_analyzer"
        assert agent.config.tier == "operational"


class TestTrendAnalysis:
    """Test trend analysis logic."""

    @pytest.mark.asyncio
    async def test_successful_trend_analysis(self, agent):
        """Test successful trend analysis."""
        state = create_initial_state(
            message="Analyze MRR trend",
            context={}
        )
        state["entities"] = {"metric": "mrr", "time_period": "last_6_months"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_upward_trend_detection(self, agent):
        """Test detection of upward trends."""
        state = create_initial_state(
            message="Analyze upward trends",
            context={}
        )
        state["entities"] = {"trend_direction": "upward"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_downward_trend_detection(self, agent):
        """Test detection of downward trends."""
        state = create_initial_state(
            message="Analyze downward trends",
            context={}
        )
        state["entities"] = {"trend_direction": "downward"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_seasonal_pattern_detection(self, agent):
        """Test detection of seasonal patterns."""
        state = create_initial_state(
            message="Detect seasonal patterns",
            context={}
        )
        state["entities"] = {"analysis_type": "seasonal"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestForecasting:
    """Test forecasting capabilities."""

    @pytest.mark.asyncio
    async def test_short_term_forecast(self, agent):
        """Test short-term forecasting."""
        state = create_initial_state(message="Forecast next month", context={})
        state["entities"] = {"forecast_period": "1_month"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_long_term_forecast(self, agent):
        """Test long-term forecasting."""
        state = create_initial_state(message="Forecast next year", context={})
        state["entities"] = {"forecast_period": "12_months"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_insufficient_data(self, agent):
        """Test handling of insufficient historical data."""
        state = create_initial_state(message="Analyze trend", context={})
        state["entities"] = {"time_period": "last_1_day"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_handles_missing_metric(self, agent):
        """Test handling of missing metric."""
        state = create_initial_state(message="Analyze trend", context={})
        state["entities"] = {}

        result = await agent.process(state)

        assert result["status"] == "resolved"
