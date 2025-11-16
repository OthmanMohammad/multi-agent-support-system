"""
Unit tests for Cleanup Scheduler Agent.

Tests data cleanup, archival, and retention enforcement.
Part of: TASK-2220 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.cleanup_scheduler import CleanupSchedulerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CleanupSchedulerAgent instance."""
    return CleanupSchedulerAgent()


class TestCleanupSchedulerInitialization:
    """Test Cleanup Scheduler initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "cleanup_scheduler"
        assert agent.config.tier == "operational"


class TestCleanupScheduling:
    """Test cleanup scheduling logic."""

    @pytest.mark.asyncio
    async def test_successful_cleanup_scheduling(self, agent):
        """Test successful cleanup scheduling."""
        state = create_initial_state(
            message="Schedule data cleanup",
            context={}
        )
        state["entities"] = {
            "cleanup_type": "old_logs",
            "retention_days": 90,
            "schedule": "daily"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_archival_cleanup(self, agent):
        """Test archival cleanup."""
        state = create_initial_state(message="Archive old data", context={})
        state["entities"] = {
            "cleanup_type": "archive",
            "data_type": "completed_tickets"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_cleanup_type(self, agent):
        """Test handling of missing cleanup type."""
        state = create_initial_state(message="Schedule cleanup", context={})
        state["entities"] = {"schedule": "daily"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
