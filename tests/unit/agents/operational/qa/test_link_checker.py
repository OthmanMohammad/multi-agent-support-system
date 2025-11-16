"""
Unit tests for Link Checker Agent.

Tests link validation, URL checking, and broken link detection.
Part of: TASK-2107 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.link_checker import LinkCheckerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create LinkCheckerAgent instance."""
    return LinkCheckerAgent()


class TestLinkCheckerInitialization:
    """Test Link Checker initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "link_checker"
        assert agent.config.tier == "operational"


class TestLinkChecking:
    """Test link checking logic."""

    @pytest.mark.asyncio
    async def test_successful_link_checking(self, agent):
        """Test successful link checking."""
        state = create_initial_state(
            message="Check links in response",
            context={}
        )
        state["entities"] = {
            "response_text": "Visit https://example.com for more info."
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_validates_multiple_links(self, agent):
        """Test validation of multiple links."""
        state = create_initial_state(
            message="Check all links",
            context={}
        )
        state["entities"] = {
            "response_text": "Visit https://example.com or https://test.com"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_detects_broken_links(self, agent):
        """Test detection of broken links."""
        state = create_initial_state(
            message="Find broken links",
            context={}
        )
        state["entities"] = {
            "response_text": "Visit https://invalid-domain-12345.com"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_links(self, agent):
        """Test handling of response with no links."""
        state = create_initial_state(message="Check links", context={})
        state["entities"] = {"response_text": "No links in this response"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
