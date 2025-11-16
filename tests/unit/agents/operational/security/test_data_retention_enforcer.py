"""
Unit tests for Data Retention Enforcer Agent.

Tests data retention policy enforcement, cleanup, and compliance.
Part of: TASK-2307 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.data_retention_enforcer import DataRetentionEnforcerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create DataRetentionEnforcerAgent instance."""
    return DataRetentionEnforcerAgent()


class TestDataRetentionEnforcerInitialization:
    """Test Data Retention Enforcer initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "data_retention_enforcer"
        assert agent.config.tier == "operational"


class TestDataRetentionEnforcement:
    """Test data retention enforcement logic."""

    @pytest.mark.asyncio
    async def test_successful_retention_check(self, agent):
        """Test successful retention policy check."""
        state = create_initial_state(
            message="Check retention compliance",
            context={}
        )
        state["entities"] = {
            "data_type": "customer_logs",
            "retention_period": "90_days"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_expired_data_deletion(self, agent):
        """Test expired data deletion."""
        state = create_initial_state(message="Delete expired data", context={})
        state["entities"] = {
            "data_type": "temporary_files",
            "action": "delete"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_retention_policy_application(self, agent):
        """Test retention policy application."""
        state = create_initial_state(message="Apply retention policy", context={})
        state["entities"] = {
            "policy_id": "POL-123",
            "scope": "all_data"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_data_type(self, agent):
        """Test handling of missing data type."""
        state = create_initial_state(message="Check retention", context={})
        state["entities"] = {"retention_period": "30_days"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
