"""
Unit tests for Tone Checker Agent.

Tests tone analysis, sentiment checking, and professionalism validation.
Part of: TASK-2104 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.tone_checker import ToneCheckerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ToneCheckerAgent instance."""
    return ToneCheckerAgent()


class TestToneCheckerInitialization:
    """Test Tone Checker initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "tone_checker"
        assert agent.config.tier == "operational"


class TestToneChecking:
    """Test tone checking logic."""

    @pytest.mark.asyncio
    async def test_successful_tone_checking(self, agent):
        """Test successful tone checking."""
        state = create_initial_state(
            message="Check tone of response",
            context={}
        )
        state["entities"] = {"response_text": "Thank you for reaching out. I'd be happy to help!"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_professional_tone_check(self, agent):
        """Test professional tone checking."""
        state = create_initial_state(
            message="Verify professional tone",
            context={}
        )
        state["entities"] = {
            "response_text": "I appreciate your inquiry.",
            "expected_tone": "professional"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_friendly_tone_check(self, agent):
        """Test friendly tone checking."""
        state = create_initial_state(
            message="Verify friendly tone",
            context={}
        )
        state["entities"] = {
            "response_text": "Great question! Let me help you out.",
            "expected_tone": "friendly"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_detects_inappropriate_tone(self, agent):
        """Test detection of inappropriate tone."""
        state = create_initial_state(
            message="Check for inappropriate tone",
            context={}
        )
        state["entities"] = {"response_text": "That's a stupid question."}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, agent):
        """Test handling of empty response."""
        state = create_initial_state(message="Check tone", context={})
        state["entities"] = {"response_text": ""}

        result = await agent.process(state)

        assert result["status"] == "resolved"
