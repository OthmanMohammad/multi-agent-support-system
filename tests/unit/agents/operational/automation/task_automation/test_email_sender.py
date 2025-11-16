"""
Unit tests for Email Sender Agent.

Tests email composition, sending, and delivery tracking.
Part of: TASK-2203 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.task_automation.email_sender import EmailSenderAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create EmailSenderAgent instance."""
    return EmailSenderAgent()


class TestEmailSenderInitialization:
    """Test Email Sender initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "email_sender"
        assert agent.config.tier == "operational"


class TestEmailSending:
    """Test email sending logic."""

    @pytest.mark.asyncio
    async def test_successful_email_sending(self, agent):
        """Test successful email sending."""
        state = create_initial_state(
            message="Send email to customer",
            context={}
        )
        state["entities"] = {
            "to": "customer@example.com",
            "subject": "Your request",
            "body": "Thank you for contacting us."
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_email_with_template(self, agent):
        """Test email sending with template."""
        state = create_initial_state(message="Send templated email", context={})
        state["entities"] = {
            "to": "customer@example.com",
            "template": "welcome"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_recipient(self, agent):
        """Test handling of missing recipient."""
        state = create_initial_state(message="Send email", context={})
        state["entities"] = {"subject": "Test"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
