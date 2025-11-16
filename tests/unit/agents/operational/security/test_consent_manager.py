"""
Unit tests for Consent Manager Agent.

Tests consent tracking, preference management, and compliance.
Part of: TASK-2308 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.consent_manager import ConsentManagerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ConsentManagerAgent instance."""
    return ConsentManagerAgent()


class TestConsentManagerInitialization:
    """Test Consent Manager initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "consent_manager"
        assert agent.config.tier == "operational"


class TestConsentManagement:
    """Test consent management logic."""

    @pytest.mark.asyncio
    async def test_successful_consent_tracking(self, agent):
        """Test successful consent tracking."""
        state = create_initial_state(
            message="Track user consent",
            context={}
        )
        state["entities"] = {
            "user_id": "USER-123",
            "consent_type": "marketing",
            "status": "granted"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_consent_withdrawal(self, agent):
        """Test consent withdrawal processing."""
        state = create_initial_state(message="Process consent withdrawal", context={})
        state["entities"] = {
            "user_id": "USER-123",
            "consent_type": "data_processing",
            "action": "withdraw"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_preference_update(self, agent):
        """Test user preference update."""
        state = create_initial_state(message="Update preferences", context={})
        state["entities"] = {
            "user_id": "USER-123",
            "preferences": {"marketing": False, "analytics": True}
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_user_id(self, agent):
        """Test handling of missing user ID."""
        state = create_initial_state(message="Track consent", context={})
        state["entities"] = {"consent_type": "marketing"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
