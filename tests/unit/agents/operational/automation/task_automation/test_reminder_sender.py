"""
Unit tests for Reminder Sender Agent.

Tests reminder creation, scheduling, and delivery.
Part of: TASK-2204 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.task_automation.reminder_sender import ReminderSenderAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ReminderSenderAgent instance."""
    return ReminderSenderAgent()


class TestReminderSenderInitialization:
    """Test Reminder Sender initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "reminder_sender"
        assert agent.config.tier == "operational"


class TestReminderSending:
    """Test reminder sending logic."""

    @pytest.mark.asyncio
    async def test_successful_reminder_creation(self, agent):
        """Test successful reminder creation."""
        state = create_initial_state(
            message="Set a reminder",
            context={}
        )
        state["entities"] = {
            "reminder_type": "payment",
            "recipient": "customer@example.com",
            "schedule": "2025-01-25"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_recurring_reminder(self, agent):
        """Test recurring reminder creation."""
        state = create_initial_state(message="Set recurring reminder", context={})
        state["entities"] = {
            "reminder_type": "renewal",
            "recurrence": "monthly"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_schedule(self, agent):
        """Test handling of missing schedule."""
        state = create_initial_state(message="Set reminder", context={})
        state["entities"] = {"reminder_type": "payment"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
