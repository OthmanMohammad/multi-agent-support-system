"""
Unit tests for Encryption Validator Agent.

Tests encryption validation, key management, and security compliance.
Part of: TASK-2309 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.encryption_validator import EncryptionValidatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create EncryptionValidatorAgent instance."""
    return EncryptionValidatorAgent()


class TestEncryptionValidatorInitialization:
    """Test Encryption Validator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "encryption_validator"
        assert agent.config.tier == "operational"


class TestEncryptionValidation:
    """Test encryption validation logic."""

    @pytest.mark.asyncio
    async def test_successful_encryption_validation(self, agent):
        """Test successful encryption validation."""
        state = create_initial_state(
            message="Validate encryption",
            context={}
        )
        state["entities"] = {
            "data_type": "customer_data",
            "encryption_algorithm": "AES-256"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_key_rotation_check(self, agent):
        """Test encryption key rotation check."""
        state = create_initial_state(message="Check key rotation", context={})
        state["entities"] = {"check_type": "key_rotation"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_encryption_strength_validation(self, agent):
        """Test encryption strength validation."""
        state = create_initial_state(message="Validate encryption strength", context={})
        state["entities"] = {
            "algorithm": "AES-128",
            "minimum_strength": "AES-256"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_algorithm(self, agent):
        """Test handling of missing algorithm."""
        state = create_initial_state(message="Validate encryption", context={})
        state["entities"] = {"data_type": "customer_data"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
