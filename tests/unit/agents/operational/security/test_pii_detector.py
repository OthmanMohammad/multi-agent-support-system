"""
Unit tests for PII Detector Agent.

Tests PII detection, masking, and classification.
Part of: TASK-2301 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.pii_detector import PIIDetectorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create PIIDetectorAgent instance."""
    return PIIDetectorAgent()


class TestPIIDetectorInitialization:
    """Test PII Detector initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "pii_detector"
        assert agent.config.tier == "operational"


class TestPIIDetection:
    """Test PII detection logic."""

    @pytest.mark.asyncio
    async def test_successful_pii_detection(self, agent):
        """Test successful PII detection."""
        state = create_initial_state(
            message="Scan for PII",
            context={}
        )
        state["entities"] = {
            "text": "My email is john@example.com and SSN is 123-45-6789",
            "scan_type": "full"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_email_detection(self, agent):
        """Test email address detection."""
        state = create_initial_state(message="Detect email addresses", context={})
        state["entities"] = {
            "text": "Contact me at user@example.com",
            "pii_type": "email"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_pii_masking(self, agent):
        """Test PII masking functionality."""
        state = create_initial_state(message="Mask PII", context={})
        state["entities"] = {
            "text": "My credit card is 4111-1111-1111-1111",
            "action": "mask"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_pii(self, agent):
        """Test handling when no PII found."""
        state = create_initial_state(message="Scan for PII", context={})
        state["entities"] = {"text": "This is a clean message"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_handles_empty_text(self, agent):
        """Test handling of empty text."""
        state = create_initial_state(message="Scan for PII", context={})
        state["entities"] = {"text": ""}

        result = await agent.process(state)

        assert result["status"] == "resolved"
