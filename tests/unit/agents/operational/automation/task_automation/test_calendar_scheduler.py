"""
Unit tests for Calendar Scheduler Agent.

Tests calendar event creation, scheduling, and updates.
Part of: TASK-2202 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.task_automation.calendar_scheduler import CalendarSchedulerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CalendarSchedulerAgent instance."""
    return CalendarSchedulerAgent()


class TestCalendarSchedulerInitialization:
    """Test Calendar Scheduler initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "calendar_scheduler"
        assert agent.config.tier == "operational"


class TestEventScheduling:
    """Test event scheduling logic."""

    @pytest.mark.asyncio
    async def test_successful_event_creation(self, agent):
        """Test successful calendar event creation."""
        state = create_initial_state(
            message="Schedule a meeting",
            context={}
        )
        state["entities"] = {
            "event_type": "meeting",
            "title": "Team sync",
            "date": "2025-01-20",
            "time": "10:00"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_recurring_event_creation(self, agent):
        """Test recurring event creation."""
        state = create_initial_state(message="Schedule recurring meeting", context={})
        state["entities"] = {
            "event_type": "meeting",
            "recurrence": "weekly"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_date(self, agent):
        """Test handling of missing date."""
        state = create_initial_state(message="Schedule event", context={})
        state["entities"] = {"event_type": "meeting"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
