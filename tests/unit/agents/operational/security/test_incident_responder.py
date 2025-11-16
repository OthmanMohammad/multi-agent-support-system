"""
Unit tests for Incident Responder Agent.

Tests incident response, escalation, and resolution tracking.
Part of: TASK-2306 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.incident_responder import IncidentResponderAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create IncidentResponderAgent instance."""
    return IncidentResponderAgent()


class TestIncidentResponderInitialization:
    """Test Incident Responder initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "incident_responder"
        assert agent.config.tier == "operational"


class TestIncidentResponse:
    """Test incident response logic."""

    @pytest.mark.asyncio
    async def test_successful_incident_response(self, agent):
        """Test successful incident response."""
        state = create_initial_state(
            message="Respond to security incident",
            context={}
        )
        state["entities"] = {
            "incident_id": "INC-123",
            "incident_type": "data_breach",
            "severity": "critical"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_incident_escalation(self, agent):
        """Test incident escalation."""
        state = create_initial_state(message="Escalate incident", context={})
        state["entities"] = {
            "incident_id": "INC-123",
            "escalate_to": "security_team"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_incident_containment(self, agent):
        """Test incident containment actions."""
        state = create_initial_state(message="Contain incident", context={})
        state["entities"] = {
            "incident_id": "INC-123",
            "containment_action": "isolate_system"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_incident_id(self, agent):
        """Test handling of missing incident ID."""
        state = create_initial_state(message="Respond to incident", context={})
        state["entities"] = {"incident_type": "breach"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
