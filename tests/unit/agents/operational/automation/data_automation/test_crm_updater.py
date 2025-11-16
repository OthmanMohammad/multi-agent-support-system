"""
Unit tests for CRM Updater Agent.

Tests CRM data updates, synchronization, and validation.
Part of: TASK-2206 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.data_automation.crm_updater import CRMUpdaterAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CRMUpdaterAgent instance."""
    return CRMUpdaterAgent()


class TestCRMUpdaterInitialization:
    """Test CRM Updater initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "crm_updater"
        assert agent.config.tier == "operational"


class TestCRMUpdates:
    """Test CRM update logic."""

    @pytest.mark.asyncio
    async def test_successful_crm_update(self, agent):
        """Test successful CRM data update."""
        state = create_initial_state(
            message="Update CRM record",
            context={}
        )
        state["entities"] = {
            "customer_id": "CUST-123",
            "field": "status",
            "value": "active"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_batch_crm_update(self, agent):
        """Test batch CRM updates."""
        state = create_initial_state(message="Batch update CRM", context={})
        state["entities"] = {
            "update_type": "batch",
            "records": ["CUST-123", "CUST-456"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_crm_sync(self, agent):
        """Test CRM synchronization."""
        state = create_initial_state(message="Sync CRM data", context={})
        state["entities"] = {"sync_type": "full"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_customer_id(self, agent):
        """Test handling of missing customer ID."""
        state = create_initial_state(message="Update CRM", context={})
        state["entities"] = {"field": "status"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
