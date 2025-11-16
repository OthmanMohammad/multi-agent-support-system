"""
Unit tests for Policy Checker Agent.

Tests policy compliance checking and guideline validation.
Part of: TASK-2103 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.policy_checker import PolicyCheckerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create PolicyCheckerAgent instance."""
    return PolicyCheckerAgent()


class TestPolicyCheckerInitialization:
    """Test Policy Checker initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "policy_checker"
        assert agent.config.tier == "operational"


class TestPolicyChecking:
    """Test policy checking logic."""

    @pytest.mark.asyncio
    async def test_successful_policy_checking(self, agent):
        """Test successful policy compliance checking."""
        state = create_initial_state(
            message="Check policy compliance",
            context={}
        )
        state["entities"] = {"response_text": "Compliant response text"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_privacy_policy_check(self, agent):
        """Test privacy policy compliance."""
        state = create_initial_state(
            message="Check privacy compliance",
            context={}
        )
        state["entities"] = {
            "response_text": "We protect your data.",
            "policy_type": "privacy"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_refund_policy_check(self, agent):
        """Test refund policy compliance."""
        state = create_initial_state(
            message="Check refund policy",
            context={}
        )
        state["entities"] = {
            "response_text": "You can request a refund within 30 days.",
            "policy_type": "refund"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_policy_type(self, agent):
        """Test handling of missing policy type."""
        state = create_initial_state(message="Check policy", context={})
        state["entities"] = {"response_text": "Some text"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
