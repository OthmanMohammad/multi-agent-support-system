"""
Unit tests for Query Builder Agent.

Tests SQL query generation, optimization, and validation.
Part of: TASK-2021 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.query_builder import QueryBuilderAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create QueryBuilderAgent instance."""
    return QueryBuilderAgent()


class TestQueryBuilderInitialization:
    """Test Query Builder initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "query_builder"
        assert agent.config.tier == "operational"


class TestQueryGeneration:
    """Test query generation logic."""

    @pytest.mark.asyncio
    async def test_successful_query_generation(self, agent):
        """Test successful SQL query generation."""
        state = create_initial_state(
            message="Generate query for customer metrics",
            context={}
        )
        state["entities"] = {"query_type": "select"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_aggregation_query_generation(self, agent):
        """Test aggregation query generation."""
        state = create_initial_state(
            message="Generate aggregation query",
            context={}
        )
        state["entities"] = {"aggregation": "sum"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_join_query_generation(self, agent):
        """Test join query generation."""
        state = create_initial_state(
            message="Generate join query",
            context={}
        )
        state["entities"] = {"query_type": "join"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_invalid_query_type(self, agent):
        """Test handling of invalid query type."""
        state = create_initial_state(message="Generate query", context={})
        state["entities"] = {"query_type": "invalid"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
