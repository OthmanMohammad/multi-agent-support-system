"""
Unit tests for Data Validator Agent.

Tests data validation, quality checks, and compliance verification.
Part of: TASK-2209 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.data_automation.data_validator import DataValidatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create DataValidatorAgent instance."""
    return DataValidatorAgent()


class TestDataValidatorInitialization:
    """Test Data Validator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "data_validator"
        assert agent.config.tier == "operational"


class TestDataValidation:
    """Test data validation logic."""

    @pytest.mark.asyncio
    async def test_successful_data_validation(self, agent):
        """Test successful data validation."""
        state = create_initial_state(
            message="Validate customer data",
            context={}
        )
        state["entities"] = {
            "dataset": "customers",
            "validation_rules": ["email_format", "phone_format"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_format_validation(self, agent):
        """Test format validation."""
        state = create_initial_state(message="Validate email format", context={})
        state["entities"] = {
            "field": "email",
            "value": "user@example.com"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_invalid_data(self, agent):
        """Test handling of invalid data."""
        state = create_initial_state(message="Validate data", context={})
        state["entities"] = {
            "field": "email",
            "value": "invalid-email"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
