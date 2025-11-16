"""
Unit tests for Onboarding Automator Agent.

Tests automated onboarding, provisioning, and welcome sequences.
Part of: TASK-2215 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.onboarding_automator import OnboardingAutomatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create OnboardingAutomatorAgent instance."""
    return OnboardingAutomatorAgent()


class TestOnboardingAutomatorInitialization:
    """Test Onboarding Automator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "onboarding_automator"
        assert agent.config.tier == "operational"


class TestOnboardingAutomation:
    """Test onboarding automation logic."""

    @pytest.mark.asyncio
    async def test_successful_onboarding(self, agent):
        """Test successful automated onboarding."""
        state = create_initial_state(
            message="Onboard new customer",
            context={}
        )
        state["entities"] = {
            "customer_id": "CUST-123",
            "plan": "premium"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_welcome_sequence(self, agent):
        """Test welcome sequence automation."""
        state = create_initial_state(message="Send welcome sequence", context={})
        state["entities"] = {
            "customer_email": "new@example.com",
            "sequence_type": "welcome"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_customer_info(self, agent):
        """Test handling of missing customer information."""
        state = create_initial_state(message="Onboard customer", context={})
        state["entities"] = {}

        result = await agent.process(state)

        assert result["status"] == "resolved"
