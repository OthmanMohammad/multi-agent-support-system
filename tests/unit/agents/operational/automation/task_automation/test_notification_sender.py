"""
Unit tests for Notification Sender Agent.

Tests notification creation, routing, and delivery.
Part of: TASK-2205 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.task_automation.notification_sender import NotificationSenderAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create NotificationSenderAgent instance."""
    return NotificationSenderAgent()


class TestNotificationSenderInitialization:
    """Test Notification Sender initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "notification_sender"
        assert agent.config.tier == "operational"


class TestNotificationSending:
    """Test notification sending logic."""

    @pytest.mark.asyncio
    async def test_successful_notification_sending(self, agent):
        """Test successful notification sending."""
        state = create_initial_state(
            message="Send notification",
            context={}
        )
        state["entities"] = {
            "notification_type": "alert",
            "recipient": "user@example.com",
            "message": "System update available"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_multi_channel_notification(self, agent):
        """Test multi-channel notification sending."""
        state = create_initial_state(message="Send multi-channel notification", context={})
        state["entities"] = {
            "channels": ["email", "sms", "push"],
            "message": "Important update"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_message(self, agent):
        """Test handling of missing message."""
        state = create_initial_state(message="Send notification", context={})
        state["entities"] = {"recipient": "user@example.com"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
