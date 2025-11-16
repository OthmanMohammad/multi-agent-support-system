"""
Unit tests for Deduplicator Agent.

Tests duplicate detection, merging, and data cleanup.
Part of: TASK-2208 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.data_automation.deduplicator import DeduplicatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create DeduplicatorAgent instance."""
    return DeduplicatorAgent()


class TestDeduplicatorInitialization:
    """Test Deduplicator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "deduplicator"
        assert agent.config.tier == "operational"


class TestDeduplication:
    """Test deduplication logic."""

    @pytest.mark.asyncio
    async def test_successful_duplicate_detection(self, agent):
        """Test successful duplicate detection."""
        state = create_initial_state(
            message="Find duplicates",
            context={}
        )
        state["entities"] = {
            "dataset": "customers",
            "match_fields": ["email", "phone"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_duplicate_merging(self, agent):
        """Test duplicate record merging."""
        state = create_initial_state(message="Merge duplicates", context={})
        state["entities"] = {
            "action": "merge",
            "records": ["REC-1", "REC-2"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_duplicates(self, agent):
        """Test handling when no duplicates found."""
        state = create_initial_state(message="Find duplicates", context={})
        state["entities"] = {"dataset": "customers"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
