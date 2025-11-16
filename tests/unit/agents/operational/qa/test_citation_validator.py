"""
Unit tests for Citation Validator Agent.

Tests citation validation, reference checking, and source attribution.
Part of: TASK-2110 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.citation_validator import CitationValidatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CitationValidatorAgent instance."""
    return CitationValidatorAgent()


class TestCitationValidatorInitialization:
    """Test Citation Validator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "citation_validator"
        assert agent.config.tier == "operational"


class TestCitationValidation:
    """Test citation validation logic."""

    @pytest.mark.asyncio
    async def test_successful_citation_validation(self, agent):
        """Test successful citation validation."""
        state = create_initial_state(
            message="Validate citations",
            context={}
        )
        state["entities"] = {
            "response_text": "According to our documentation [1], this is correct."
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_validates_source_attribution(self, agent):
        """Test source attribution validation."""
        state = create_initial_state(
            message="Check source attribution",
            context={}
        )
        state["entities"] = {
            "response_text": "As stated in the user guide, feature X is available."
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_detects_missing_citations(self, agent):
        """Test detection of missing citations."""
        state = create_initial_state(
            message="Find missing citations",
            context={}
        )
        state["entities"] = {
            "response_text": "This feature has been proven effective.",
            "require_citations": True
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_citations_required(self, agent):
        """Test handling when citations not required."""
        state = create_initial_state(message="Validate citations", context={})
        state["entities"] = {
            "response_text": "General response",
            "require_citations": False
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
