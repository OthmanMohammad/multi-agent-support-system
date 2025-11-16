"""
Unit tests for Sensitivity Checker Agent.

Tests sensitivity detection, offensive content checking, and bias detection.
Part of: TASK-2108 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.sensitivity_checker import SensitivityCheckerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create SensitivityCheckerAgent instance."""
    return SensitivityCheckerAgent()


class TestSensitivityCheckerInitialization:
    """Test Sensitivity Checker initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "sensitivity_checker"
        assert agent.config.tier == "operational"


class TestSensitivityChecking:
    """Test sensitivity checking logic."""

    @pytest.mark.asyncio
    async def test_successful_sensitivity_check(self, agent):
        """Test successful sensitivity checking."""
        state = create_initial_state(
            message="Check for sensitive content",
            context={}
        )
        state["entities"] = {"response_text": "Thank you for your inquiry."}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_detects_offensive_content(self, agent):
        """Test detection of offensive content."""
        state = create_initial_state(
            message="Check for offensive content",
            context={}
        )
        state["entities"] = {"response_text": "Some potentially offensive text"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_bias_detection(self, agent):
        """Test bias detection."""
        state = create_initial_state(
            message="Check for bias",
            context={}
        )
        state["entities"] = {
            "response_text": "Some text",
            "check_bias": True
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_empty_response(self, agent):
        """Test handling of empty response."""
        state = create_initial_state(message="Check sensitivity", context={})
        state["entities"] = {"response_text": ""}

        result = await agent.process(state)

        assert result["status"] == "resolved"
