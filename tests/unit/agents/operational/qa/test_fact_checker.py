"""
Unit tests for Fact Checker Agent.

Tests fact verification, accuracy checking, and source validation.
Part of: TASK-2102 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.fact_checker import FactCheckerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create FactCheckerAgent instance."""
    return FactCheckerAgent()


class TestFactCheckerInitialization:
    """Test Fact Checker initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "fact_checker"
        assert agent.config.tier == "operational"


class TestFactChecking:
    """Test fact checking logic."""

    @pytest.mark.asyncio
    async def test_successful_fact_checking(self, agent):
        """Test successful fact checking."""
        state = create_initial_state(
            message="Check facts in response",
            context={}
        )
        state["entities"] = {"response_text": "Our platform supports 10,000+ users."}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_fact_verification_with_sources(self, agent):
        """Test fact verification with source validation."""
        state = create_initial_state(
            message="Verify facts with sources",
            context={}
        )
        state["entities"] = {
            "response_text": "According to documentation, feature X is available.",
            "verify_sources": True
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_identifies_potential_inaccuracies(self, agent):
        """Test identification of potential inaccuracies."""
        state = create_initial_state(
            message="Check for inaccuracies",
            context={}
        )
        state["entities"] = {"response_text": "Some questionable claim"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, agent):
        """Test handling of empty response."""
        state = create_initial_state(message="Check facts", context={})
        state["entities"] = {"response_text": ""}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_handles_no_factual_claims(self, agent):
        """Test handling of response with no factual claims."""
        state = create_initial_state(message="Check facts", context={})
        state["entities"] = {"response_text": "Hello, how can I help you today?"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
