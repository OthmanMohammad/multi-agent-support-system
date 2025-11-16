"""Unit tests for Churn Predictor Agent - TASK-4011"""

import pytest
from datetime import datetime
from src.agents.advanced.predictive.churn_predictor import ChurnPredictorAgent
from src.workflow.state import AgentState


@pytest.mark.asyncio
async def test_churn_predictor_initialization():
    """Test churn predictor agent initialization."""
    agent = ChurnPredictorAgent()

    assert agent.config.name == "churn_predictor"
    assert agent.config.tier == "advanced"
    assert "ChurnPredictorAgent" in str(type(agent))


@pytest.mark.asyncio
async def test_churn_prediction_with_customer_id():
    """Test churn prediction with valid customer ID."""
    agent = ChurnPredictorAgent()

    state = AgentState(
        customer_id="test_customer_123",
        entities={"customer_id": "test_customer_123"},
        conversation_id="conv_123",
        messages=[],
        agent_history=[],
        turn_count=0
    )

    result = await agent.process(state)

    assert result["status"] == "resolved"
    assert "churn_prediction" in result
    assert "churn_probability" in result
    assert "churn_risk" in result
    assert 0.0 <= result["churn_probability"] <= 1.0
    assert result["churn_risk"] in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_churn_prediction_without_customer_id():
    """Test churn prediction fails gracefully without customer ID."""
    agent = ChurnPredictorAgent()

    state = AgentState(
        conversation_id="conv_123",
        messages=[],
        entities={},
        agent_history=[],
        turn_count=0
    )

    result = await agent.process(state)

    assert result["status"] == "failed"
    assert "Error" in result["agent_response"]


@pytest.mark.asyncio
async def test_risk_level_determination():
    """Test risk level determination from probability."""
    agent = ChurnPredictorAgent()

    assert agent._determine_risk_level(0.2) == "low"
    assert agent._determine_risk_level(0.4) == "medium"
    assert agent._determine_risk_level(0.7) == "high"


@pytest.mark.asyncio
async def test_churn_probability_calculation():
    """Test churn probability calculation logic."""
    agent = ChurnPredictorAgent()

    # High-risk features
    high_risk_features = {
        "login_count_30d": 2,
        "days_since_last_login": 20,
        "support_tickets_30d": 8,
        "avg_csat_30d": 2.5,
        "health_score": 30,
        "nps_score": -20,
        "payment_failures_30d": 2,
        "usage_trend_30d": -0.3,
        "feature_adoption_score": 0.2,
        "is_annual_contract": False
    }

    probability = agent._calculate_churn_probability(high_risk_features)
    assert probability > 0.5, "High-risk features should result in high probability"

    # Low-risk features
    low_risk_features = {
        "login_count_30d": 25,
        "days_since_last_login": 1,
        "support_tickets_30d": 1,
        "avg_csat_30d": 4.5,
        "health_score": 85,
        "nps_score": 60,
        "payment_failures_30d": 0,
        "usage_trend_30d": 0.2,
        "feature_adoption_score": 0.8,
        "is_annual_contract": True
    }

    probability = agent._calculate_churn_probability(low_risk_features)
    assert probability < 0.3, "Low-risk features should result in low probability"


@pytest.mark.asyncio
async def test_generate_actions():
    """Test action generation based on risk factors."""
    agent = ChurnPredictorAgent()

    risk_factors = [
        {"factor": "login_count_30d", "value": 2, "importance": 0.25},
        {"factor": "support_tickets_30d", "value": 8, "importance": 0.18}
    ]

    features = {"login_count_30d": 2, "support_tickets_30d": 8}

    actions = agent._generate_actions("high", risk_factors, features)

    assert len(actions) > 0
    assert any("URGENT" in action for action in actions)
    assert isinstance(actions, list)


@pytest.mark.asyncio
async def test_confidence_calculation():
    """Test confidence score calculation."""
    agent = ChurnPredictorAgent()

    complete_features = {f"feature_{i}": i for i in range(25)}
    confidence = agent._calculate_confidence(complete_features)

    assert 0.5 <= confidence <= 1.0
    assert isinstance(confidence, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
