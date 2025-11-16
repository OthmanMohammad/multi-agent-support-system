"""
Unit tests for Compliance Checker Agent.

Tests compliance validation, regulation checking, and reporting.
Part of: TASK-2304 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.compliance_checker import ComplianceCheckerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ComplianceCheckerAgent instance."""
    return ComplianceCheckerAgent()


class TestComplianceCheckerInitialization:
    """Test Compliance Checker initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "compliance_checker"
        assert agent.config.tier == "operational"


class TestComplianceChecking:
    """Test compliance checking logic."""

    @pytest.mark.asyncio
    async def test_successful_compliance_check(self, agent):
        """Test successful compliance check."""
        state = create_initial_state(
            message="Check GDPR compliance",
            context={}
        )
        state["entities"] = {
            "regulation": "gdpr",
            "scope": "data_processing"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_hipaa_compliance(self, agent):
        """Test HIPAA compliance checking."""
        state = create_initial_state(message="Check HIPAA compliance", context={})
        state["entities"] = {"regulation": "hipaa"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_compliance_report_generation(self, agent):
        """Test compliance report generation."""
        state = create_initial_state(message="Generate compliance report", context={})
        state["entities"] = {
            "report_type": "full",
            "regulations": ["gdpr", "ccpa"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_unknown_regulation(self, agent):
        """Test handling of unknown regulation."""
        state = create_initial_state(message="Check compliance", context={})
        state["entities"] = {"regulation": "unknown"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
