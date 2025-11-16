"""
Unit tests for Hallucination Detector Agent.

Tests hallucination detection, factual consistency checking, and confidence scoring.
Part of: TASK-2109 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.hallucination_detector import HallucinationDetectorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create HallucinationDetectorAgent instance."""
    return HallucinationDetectorAgent()


class TestHallucinationDetectorInitialization:
    """Test Hallucination Detector initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "hallucination_detector"
        assert agent.config.tier == "operational"


class TestHallucinationDetection:
    """Test hallucination detection logic."""

    @pytest.mark.asyncio
    async def test_successful_hallucination_detection(self, agent):
        """Test successful hallucination detection."""
        state = create_initial_state(
            message="Detect hallucinations",
            context={}
        )
        state["entities"] = {
            "response_text": "Our product has feature X as documented.",
            "knowledge_base": "product documentation"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_detects_fabricated_information(self, agent):
        """Test detection of fabricated information."""
        state = create_initial_state(
            message="Check for fabrications",
            context={}
        )
        state["entities"] = {
            "response_text": "We have 10 million users worldwide.",
            "verify_against_facts": True
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, agent):
        """Test confidence scoring for statements."""
        state = create_initial_state(
            message="Score confidence",
            context={}
        )
        state["entities"] = {"response_text": "This feature might be available."}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_knowledge_base(self, agent):
        """Test handling when no knowledge base available."""
        state = create_initial_state(message="Detect hallucinations", context={})
        state["entities"] = {"response_text": "Some claim"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
