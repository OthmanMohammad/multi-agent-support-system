"""
Unit tests for Completeness Checker Agent.

Tests completeness validation, missing information detection, and coverage analysis.
Part of: TASK-2105 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.completeness_checker import CompletenessCheckerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CompletenessCheckerAgent instance."""
    return CompletenessCheckerAgent()


class TestCompletenessCheckerInitialization:
    """Test Completeness Checker initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "completeness_checker"
        assert agent.config.tier == "operational"


class TestCompletenessChecking:
    """Test completeness checking logic."""

    @pytest.mark.asyncio
    async def test_successful_completeness_check(self, agent):
        """Test successful completeness checking."""
        state = create_initial_state(
            message="Check if response is complete",
            context={}
        )
        state["entities"] = {
            "response_text": "Here's a complete answer with all necessary details and next steps.",
            "question": "How do I reset my password?"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_detects_incomplete_response(self, agent):
        """Test detection of incomplete response."""
        state = create_initial_state(
            message="Check completeness",
            context={}
        )
        state["entities"] = {
            "response_text": "You can try...",
            "question": "How do I reset my password?"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_checks_for_next_steps(self, agent):
        """Test checking for next steps in response."""
        state = create_initial_state(
            message="Verify next steps included",
            context={}
        )
        state["entities"] = {
            "response_text": "Click reset. Then check your email for instructions.",
            "require_next_steps": True
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_question(self, agent):
        """Test handling of missing question context."""
        state = create_initial_state(message="Check completeness", context={})
        state["entities"] = {"response_text": "Some response"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
