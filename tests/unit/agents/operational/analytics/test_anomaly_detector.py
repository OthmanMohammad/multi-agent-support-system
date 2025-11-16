"""
Unit tests for Anomaly Detector Agent.

Tests anomaly detection, threshold analysis, and alerting.
Part of: TASK-2013 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.agents.operational.analytics.anomaly_detector import AnomalyDetectorAgent
from src.workflow.state import create_initial_state


@pytest.fixture
def agent():
    """Create AnomalyDetectorAgent instance."""
    return AnomalyDetectorAgent()


class TestAnomalyDetectorInitialization:
    """Test Anomaly Detector initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.config.name == "anomaly_detector"
        assert agent.config.tier == "operational"


class TestAnomalyDetection:
    """Test anomaly detection logic."""

    @pytest.mark.asyncio
    async def test_successful_anomaly_detection(self, agent):
        """Test successful anomaly detection."""
        state = create_initial_state(
            message="Detect anomalies in MRR",
            context={}
        )
        state["entities"] = {"metric": "mrr", "time_period": "last_30_days"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result

    @pytest.mark.asyncio
    async def test_spike_detection(self, agent):
        """Test detection of metric spikes."""
        state = create_initial_state(
            message="Detect spikes in API requests",
            context={}
        )
        state["entities"] = {"metric": "api_requests", "detection_type": "spike"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_drop_detection(self, agent):
        """Test detection of metric drops."""
        state = create_initial_state(
            message="Detect drops in active users",
            context={}
        )
        state["entities"] = {"metric": "active_users", "detection_type": "drop"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_trend_anomaly_detection(self, agent):
        """Test detection of trend anomalies."""
        state = create_initial_state(
            message="Detect unusual trends",
            context={}
        )
        state["entities"] = {"detection_type": "trend"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestThresholdAnalysis:
    """Test threshold-based anomaly detection."""

    @pytest.mark.asyncio
    async def test_static_threshold_detection(self, agent):
        """Test static threshold anomaly detection."""
        state = create_initial_state(message="Check static thresholds", context={})
        state["entities"] = {"threshold_type": "static"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_dynamic_threshold_detection(self, agent):
        """Test dynamic threshold anomaly detection."""
        state = create_initial_state(message="Check dynamic thresholds", context={})
        state["entities"] = {"threshold_type": "dynamic"}

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handles_no_anomalies(self, agent):
        """Test handling when no anomalies detected."""
        state = create_initial_state(message="Detect anomalies", context={})

        result = await agent.process(state)

        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_handles_missing_metric(self, agent):
        """Test handling of missing metric."""
        state = create_initial_state(message="Detect anomalies", context={})
        state["entities"] = {}

        result = await agent.process(state)

        assert result["status"] == "resolved"
