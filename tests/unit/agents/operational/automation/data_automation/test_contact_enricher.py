"""
Unit tests for Contact Enricher Agent.

Tests contact data enrichment, validation, and enhancement.
Part of: TASK-2207 Automation Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.automation.data_automation.contact_enricher import ContactEnricherAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create ContactEnricherAgent instance."""
    return ContactEnricherAgent()


class TestContactEnricherInitialization:
    """Test Contact Enricher initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "contact_enricher"
        assert agent.config.tier == "operational"


class TestContactEnrichment:
    """Test contact enrichment logic."""

    @pytest.mark.asyncio
    async def test_successful_contact_enrichment(self, agent):
        """Test successful contact enrichment."""
        state = create_initial_state(
            message="Enrich contact data",
            context={}
        )
        state["entities"] = {
            "email": "user@example.com",
            "enrich_fields": ["company", "title", "location"]
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_company_enrichment(self, agent):
        """Test company data enrichment."""
        state = create_initial_state(message="Enrich company data", context={})
        state["entities"] = {
            "domain": "example.com",
            "enrich_type": "company"
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_email(self, agent):
        """Test handling of missing email."""
        state = create_initial_state(message="Enrich contact", context={})
        state["entities"] = {"enrich_fields": ["company"]}

        result = await agent.process(state)

        assert result["status"] == "resolved"
