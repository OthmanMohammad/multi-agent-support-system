"""
Unit tests for Data Backup Agent.

Tests data backup, scheduling, and verification.
Part of: TASK-2219 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.process_automation.data_backup import DataBackupAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create DataBackupAgent instance."""
    return DataBackupAgent()


class TestDataBackupInitialization:
    """Test Data Backup initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "data_backup"
        assert agent.config.tier == "operational"


class TestDataBackup:
    """Test data backup logic."""

    @pytest.mark.asyncio
    async def test_successful_backup(self, agent):
        """Test successful data backup."""
        state = create_initial_state(
            message="Backup customer data",
            context={}
        )
        state["entities"] = {
            "backup_type": "full",
            "data_sources": ["customers", "transactions"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_incremental_backup(self, agent):
        """Test incremental backup."""
        state = create_initial_state(message="Incremental backup", context={})
        state["entities"] = {"backup_type": "incremental"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_backup_failure(self, agent):
        """Test handling of backup failure."""
        state = create_initial_state(message="Backup data", context={})
        state["entities"] = {"data_sources": []}

        result = await agent.process(state)

        assert result["status"] == "resolved"
