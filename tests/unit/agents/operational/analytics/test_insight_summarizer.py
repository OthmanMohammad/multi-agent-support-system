"""
Unit tests for Insight Summarizer Agent.

Tests insight extraction, summarization, and key findings identification.
Part of: TASK-2019 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.insight_summarizer import InsightSummarizerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create InsightSummarizerAgent instance."""
    return InsightSummarizerAgent()


class TestInsightSummarizerInitialization:
    """Test Insight Summarizer initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "insight_summarizer"
        assert agent.config.tier == "operational"


class TestInsightSummarization:
    """Test insight summarization logic."""

    @pytest.mark.asyncio
    async def test_successful_insight_summarization(self, agent):
        """Test successful insight summarization."""
        state = create_initial_state(
            message="Summarize key insights",
            context={}
        )
        state["entities"] = {"data_source": "analytics"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_key_findings_extraction(self, agent):
        """Test key findings extraction."""
        state = create_initial_state(
            message="Extract key findings",
            context={}
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_actionable_insights_identification(self, agent):
        """Test actionable insights identification."""
        state = create_initial_state(
            message="Identify actionable insights",
            context={}
        )
        state["entities"] = {"insight_type": "actionable"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_insights(self, agent):
        """Test handling when no insights found."""
        state = create_initial_state(message="Summarize insights", context={})

        result = await agent.process(state)

        assert result["status"] == "resolved"
