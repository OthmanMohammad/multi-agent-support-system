"""
Unit tests for Prediction Explainer Agent.

Tests prediction explanation, feature importance, and model interpretation.
Part of: TASK-2020 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.prediction_explainer import PredictionExplainerAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create PredictionExplainerAgent instance."""
    return PredictionExplainerAgent()


class TestPredictionExplainerInitialization:
    """Test Prediction Explainer initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "prediction_explainer"
        assert agent.config.tier == "operational"


class TestPredictionExplanation:
    """Test prediction explanation logic."""

    @pytest.mark.asyncio
    async def test_successful_prediction_explanation(self, agent):
        """Test successful prediction explanation."""
        state = create_initial_state(
            message="Explain churn prediction",
            context={}
        )
        state["entities"] = {"prediction_type": "churn"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_feature_importance_explanation(self, agent):
        """Test feature importance explanation."""
        state = create_initial_state(
            message="Explain feature importance",
            context={}
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_model_interpretation(self, agent):
        """Test model interpretation."""
        state = create_initial_state(
            message="Interpret model results",
            context={}
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_prediction(self, agent):
        """Test handling of missing prediction."""
        state = create_initial_state(message="Explain prediction", context={})

        result = await agent.process(state)

        assert result["status"] == "resolved"
