"""
Unit tests for Ticket Creator Agent.

Tests ticket creation, assignment, and tracking.
Part of: TASK-2201 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.task_automation.ticket_creator import TicketCreatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create TicketCreatorAgent instance."""
    return TicketCreatorAgent()


class TestTicketCreatorInitialization:
    """Test Ticket Creator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "ticket_creator"
        assert agent.config.tier == "operational"


class TestTicketCreation:
    """Test ticket creation logic."""

    @pytest.mark.asyncio
    async def test_successful_ticket_creation(self, agent):
        """Test successful ticket creation."""
        state = create_initial_state(
            message="Create a ticket for password reset",
            context={}
        )
        state["entities"] = {
            "ticket_type": "support",
            "priority": "high",
            "subject": "Password reset request"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_ticket_with_assignment(self, agent):
        """Test ticket creation with assignment."""
        state = create_initial_state(message="Create and assign ticket", context={})
        state["entities"] = {
            "ticket_type": "bug",
            "assign_to": "engineering"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_ticket_priority_setting(self, agent):
        """Test ticket creation with priority."""
        state = create_initial_state(message="Create urgent ticket", context={})
        state["entities"] = {
            "priority": "urgent",
            "subject": "Critical issue"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_subject(self, agent):
        """Test handling of missing subject."""
        state = create_initial_state(message="Create ticket", context={})
        state["entities"] = {"ticket_type": "support"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
