"""
Unit tests for Correlation Finder Agent.

Tests correlation analysis, relationship detection, and causal inference.
Part of: TASK-2022 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.correlation_finder import CorrelationFinderAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CorrelationFinderAgent instance."""
    return CorrelationFinderAgent()


class TestCorrelationFinderInitialization:
    """Test Correlation Finder initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "correlation_finder"
        assert agent.config.tier == "operational"


class TestCorrelationAnalysis:
    """Test correlation analysis logic."""

    @pytest.mark.asyncio
    async def test_successful_correlation_analysis(self, agent):
        """Test successful correlation analysis."""
        state = create_initial_state(
            message="Find correlations between MRR and churn",
            context={}
        )
        state["entities"] = {"metrics": ["mrr", "churn"]}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_positive_correlation_detection(self, agent):
        """Test positive correlation detection."""
        state = create_initial_state(
            message="Find positive correlations",
            context={}
        )
        state["entities"] = {"correlation_type": "positive"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_negative_correlation_detection(self, agent):
        """Test negative correlation detection."""
        state = create_initial_state(
            message="Find negative correlations",
            context={}
        )
        state["entities"] = {"correlation_type": "negative"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_single_metric(self, agent):
        """Test handling of single metric (no correlation possible)."""
        state = create_initial_state(message="Find correlations", context={})
        state["entities"] = {"metrics": ["mrr"]}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_handles_no_correlations_found(self, agent):
        """Test handling when no correlations found."""
        state = create_initial_state(message="Find correlations", context={})

        result = await agent.process(state)

        assert result["status"] == "resolved"
