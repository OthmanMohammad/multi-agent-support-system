"""
Unit tests for Audit Logger Agent.

Tests audit logging, event tracking, and compliance reporting.
Part of: TASK-2303 Security Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.security.audit_logger import AuditLoggerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create AuditLoggerAgent instance."""
    return AuditLoggerAgent()


class TestAuditLoggerInitialization:
    """Test Audit Logger initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "audit_logger"
        assert agent.config.tier == "operational"


class TestAuditLogging:
    """Test audit logging logic."""

    @pytest.mark.asyncio
    async def test_successful_audit_logging(self, agent):
        """Test successful audit log creation."""
        state = create_initial_state(
            message="Log audit event",
            context={}
        )
        state["entities"] = {
            "event_type": "data_access",
            "user_id": "USER-123",
            "resource": "customer_data",
            "action": "read"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_security_event_logging(self, agent):
        """Test security event logging."""
        state = create_initial_state(message="Log security event", context={})
        state["entities"] = {
            "event_type": "failed_login",
            "severity": "high"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_compliance_audit_trail(self, agent):
        """Test compliance audit trail generation."""
        state = create_initial_state(message="Generate audit trail", context={})
        state["entities"] = {
            "trail_type": "compliance",
            "time_period": "last_30_days"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_event_type(self, agent):
        """Test handling of missing event type."""
        state = create_initial_state(message="Log event", context={})
        state["entities"] = {"user_id": "USER-123"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
