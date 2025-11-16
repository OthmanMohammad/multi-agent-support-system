"""
Unit tests for Code Validator Agent.

Tests code snippet validation, syntax checking, and security scanning.
Part of: TASK-2106 QA Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.qa.code_validator import CodeValidatorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create CodeValidatorAgent instance."""
    return CodeValidatorAgent()


class TestCodeValidatorInitialization:
    """Test Code Validator initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "code_validator"
        assert agent.config.tier == "operational"


class TestCodeValidation:
    """Test code validation logic."""

    @pytest.mark.asyncio
    async def test_successful_code_validation(self, agent):
        """Test successful code validation."""
        state = create_initial_state(
            message="Validate code snippet",
            context={}
        )
        state["entities"] = {
            "response_text": "Here's the code: ```python\nprint('Hello')\n```",
            "language": "python"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_syntax_validation(self, agent):
        """Test syntax validation."""
        state = create_initial_state(
            message="Check syntax",
            context={}
        )
        state["entities"] = {
            "code": "print('valid syntax')",
            "language": "python"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_security_scanning(self, agent):
        """Test security scanning of code."""
        state = create_initial_state(
            message="Scan code for security issues",
            context={}
        )
        state["entities"] = {
            "code": "password = 'hardcoded123'",
            "check_security": True
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_code_in_response(self, agent):
        """Test handling of response with no code."""
        state = create_initial_state(message="Validate code", context={})
        state["entities"] = {"response_text": "No code here"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
