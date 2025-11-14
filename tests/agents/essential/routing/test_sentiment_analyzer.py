"""
Unit tests for Sentiment Analyzer.

Tests emotion detection, urgency assessment, and satisfaction scoring.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-104)
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.agents.essential.routing.sentiment_analyzer import SentimentAnalyzer
from src.workflow.state import create_initial_state


class TestSentimentAnalyzer:
    """Test suite for Sentiment Analyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create SentimentAnalyzer instance for testing."""
        return SentimentAnalyzer()

    @pytest.fixture
    def mock_llm_angry(self):
        """Mock LLM response for angry sentiment."""
        async def mock(*args, **kwargs):
            return json.dumps({
                "sentiment_score": -0.85,
                "emotion": "angry",
                "urgency": "critical",
                "satisfaction": 0.15,
                "politeness": 0.3,
                "indicators": {
                    "negative_keywords": ["unacceptable", "broken"],
                    "urgency_keywords": ["urgent", "immediately"],
                    "business_impact": True
                },
                "reasoning": "Highly negative language with urgency indicators"
            })
        return mock

    @pytest.fixture
    def mock_llm_happy(self):
        """Mock LLM response for happy sentiment."""
        async def mock(*args, **kwargs):
            return json.dumps({
                "sentiment_score": 0.9,
                "emotion": "happy",
                "urgency": "low",
                "satisfaction": 0.95,
                "politeness": 0.95,
                "indicators": {},
                "reasoning": "Positive, grateful language"
            })
        return mock

    @pytest.fixture
    def mock_llm_neutral(self):
        """Mock LLM response for neutral sentiment."""
        async def mock(*args, **kwargs):
            return json.dumps({
                "sentiment_score": 0.0,
                "emotion": "neutral",
                "urgency": "medium",
                "satisfaction": 0.5,
                "politeness": 0.7,
                "indicators": {},
                "reasoning": "Factual, business-like tone"
            })
        return mock

    # ==================== Initialization Tests ====================

    def test_initialization(self, analyzer):
        """Test SentimentAnalyzer initializes correctly."""
        assert analyzer.config.name == "sentiment_analyzer"
        assert analyzer.config.type.value == "analyzer"
        assert analyzer.config.model == "claude-3-haiku-20240307"
        assert analyzer.config.temperature == 0.2
        assert analyzer.config.max_tokens == 250

    def test_emotions_defined(self, analyzer):
        """Test that emotion categories are defined."""
        expected_emotions = [
            "angry", "frustrated", "concerned", "neutral",
            "satisfied", "happy", "excited"
        ]
        assert analyzer.EMOTIONS == expected_emotions

    def test_urgency_levels_defined(self, analyzer):
        """Test that urgency levels are defined."""
        expected_urgency = ["low", "medium", "high", "critical"]
        assert analyzer.URGENCY_LEVELS == expected_urgency

    # ==================== Angry Sentiment Tests ====================

    @pytest.mark.asyncio
    async def test_angry_sentiment_detection(self, analyzer, mock_llm_angry):
        """Test detection of angry sentiment."""
        analyzer.call_llm = mock_llm_angry

        state = create_initial_state(
            message="This is absolutely unacceptable! Fix it now!",
            context={}
        )

        result = await analyzer.process(state)

        assert result["sentiment_score"] == -0.85
        assert result["emotion"] == "angry"
        assert result["urgency"] == "critical"
        assert result["satisfaction"] == 0.15
        assert result["politeness"] == 0.3

    @pytest.mark.asyncio
    async def test_angry_with_enterprise_context(self, analyzer, mock_llm_angry):
        """Test angry sentiment with enterprise customer context."""
        analyzer.call_llm = mock_llm_angry

        state = create_initial_state(
            message="This is unacceptable!",
            context={"customer_metadata": {"plan": "enterprise", "health_score": 25}}
        )

        result = await analyzer.process(state)

        # Should detect angry emotion
        assert result["emotion"] == "angry"
        assert result["urgency"] == "critical"

    # ==================== Happy Sentiment Tests ====================

    @pytest.mark.asyncio
    async def test_happy_sentiment_detection(self, analyzer, mock_llm_happy):
        """Test detection of happy sentiment."""
        analyzer.call_llm = mock_llm_happy

        state = create_initial_state(
            message="Thank you so much! This is amazing!",
            context={}
        )

        result = await analyzer.process(state)

        assert result["sentiment_score"] == 0.9
        assert result["emotion"] == "happy"
        assert result["urgency"] == "low"
        assert result["satisfaction"] == 0.95
        assert result["politeness"] == 0.95

    # ==================== Neutral Sentiment Tests ====================

    @pytest.mark.asyncio
    async def test_neutral_sentiment_detection(self, analyzer, mock_llm_neutral):
        """Test detection of neutral sentiment."""
        analyzer.call_llm = mock_llm_neutral

        state = create_initial_state(
            message="Can you provide an update on the feature request?",
            context={}
        )

        result = await analyzer.process(state)

        assert result["sentiment_score"] == 0.0
        assert result["emotion"] == "neutral"
        assert result["urgency"] == "medium"
        assert result["satisfaction"] == 0.5

    # ==================== Context Adjustment Tests ====================

    @pytest.mark.asyncio
    async def test_churn_risk_amplifies_negative_sentiment(self, analyzer):
        """Test high churn risk amplifies negative sentiment."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": -0.5,
                "emotion": "frustrated",
                "urgency": "medium",
                "satisfaction": 0.3,
                "politeness": 0.5,
                "indicators": {}
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(
            message="Not happy with the service",
            context={"customer_metadata": {"churn_risk": 0.85}}
        )

        result = await analyzer.process(state)

        # Sentiment should be amplified (more negative)
        assert result["sentiment_score"] <= -0.5
        # Urgency should be escalated
        assert result["urgency"] in ["high", "critical"]

    @pytest.mark.asyncio
    async def test_low_health_score_increases_urgency(self, analyzer):
        """Test low health score increases urgency."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": -0.3,
                "emotion": "frustrated",
                "urgency": "low",
                "satisfaction": 0.4,
                "politeness": 0.6,
                "indicators": {}
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(
            message="Having some issues",
            context={"customer_metadata": {"health_score": 30}}
        )

        result = await analyzer.process(state)

        # Urgency should be escalated to high
        assert result["urgency"] == "high"

    @pytest.mark.asyncio
    async def test_enterprise_negative_escalates_urgency(self, analyzer):
        """Test enterprise customer with negative sentiment escalates urgency."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": -0.4,
                "emotion": "frustrated",
                "urgency": "medium",
                "satisfaction": 0.3,
                "politeness": 0.5,
                "indicators": {}
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(
            message="This is frustrating",
            context={"customer_metadata": {"plan": "enterprise"}}
        )

        result = await analyzer.process(state)

        # Urgency should be escalated
        assert result["urgency"] in ["high", "critical"]

    # ==================== Validation Tests ====================

    @pytest.mark.asyncio
    async def test_sentiment_score_clamped_to_range(self, analyzer):
        """Test sentiment score is clamped to -1.0 to 1.0."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": 15.0,  # Invalid: too high
                "emotion": "happy",
                "urgency": "low",
                "satisfaction": 0.9,
                "politeness": 0.9
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await analyzer.process(state)

        # Should be clamped to 1.0
        assert result["sentiment_score"] == 1.0

    @pytest.mark.asyncio
    async def test_invalid_emotion_defaults_based_on_sentiment(self, analyzer):
        """Test invalid emotion defaults based on sentiment score."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": -0.7,
                "emotion": "invalid_emotion",
                "urgency": "medium",
                "satisfaction": 0.2,
                "politeness": 0.5
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await analyzer.process(state)

        # Should default to angry (sentiment < -0.5)
        assert result["emotion"] == "angry"

    @pytest.mark.asyncio
    async def test_invalid_urgency_defaults_to_medium(self, analyzer):
        """Test invalid urgency defaults to medium."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": 0.0,
                "emotion": "neutral",
                "urgency": "super_urgent",  # Invalid
                "satisfaction": 0.5,
                "politeness": 0.7
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await analyzer.process(state)

        assert result["urgency"] == "medium"

    @pytest.mark.asyncio
    async def test_satisfaction_clamped_to_range(self, analyzer):
        """Test satisfaction is clamped to 0.0 to 1.0."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": 0.8,
                "emotion": "happy",
                "urgency": "low",
                "satisfaction": 2.5,  # Invalid: too high
                "politeness": 0.9
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await analyzer.process(state)

        # Should be clamped to 1.0
        assert result["satisfaction"] == 1.0

    # ==================== Error Handling Tests ====================

    @pytest.mark.asyncio
    async def test_empty_message_returns_neutral_sentiment(self, analyzer):
        """Test empty message returns neutral sentiment."""
        state = create_initial_state(message="", context={})

        result = await analyzer.process(state)

        assert result["sentiment_score"] == 0.0
        assert result["emotion"] == "neutral"
        assert result["urgency"] == "medium"
        assert result["satisfaction"] == 0.5

    @pytest.mark.asyncio
    async def test_llm_failure_returns_neutral_sentiment(self, analyzer):
        """Test LLM failure returns neutral sentiment gracefully."""
        analyzer.call_llm = AsyncMock(side_effect=Exception("API Error"))

        state = create_initial_state(message="Test message", context={})

        result = await analyzer.process(state)

        # Should fallback to neutral
        assert result["sentiment_score"] == 0.0
        assert result["emotion"] == "neutral"
        assert result["urgency"] == "medium"
        assert "sentiment_metadata" in result

    @pytest.mark.asyncio
    async def test_invalid_json_returns_neutral_sentiment(self, analyzer):
        """Test invalid JSON response returns neutral sentiment."""
        analyzer.call_llm = AsyncMock(return_value="Not valid JSON!")

        state = create_initial_state(message="Test", context={})

        result = await analyzer.process(state)

        assert result["sentiment_score"] == 0.0
        assert result["emotion"] == "neutral"

    # ==================== State Management Tests ====================

    @pytest.mark.asyncio
    async def test_state_fields_populated(self, analyzer, mock_llm_neutral):
        """Test all expected state fields are populated."""
        analyzer.call_llm = mock_llm_neutral

        state = create_initial_state(message="Test", context={})

        result = await analyzer.process(state)

        # Check all expected fields are present
        assert "sentiment_score" in result
        assert "emotion" in result
        assert "urgency" in result
        assert "satisfaction" in result
        assert "politeness" in result
        assert "sentiment_indicators" in result
        assert "sentiment_reasoning" in result
        assert "sentiment_metadata" in result

    @pytest.mark.asyncio
    async def test_metadata_includes_latency(self, analyzer, mock_llm_neutral):
        """Test metadata includes latency measurement."""
        analyzer.call_llm = mock_llm_neutral

        state = create_initial_state(message="Test", context={})

        result = await analyzer.process(state)

        metadata = result["sentiment_metadata"]
        assert "latency_ms" in metadata
        assert isinstance(metadata["latency_ms"], int)
        assert metadata["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_agent_history_updated(self, analyzer, mock_llm_neutral):
        """Test agent history is updated after processing."""
        analyzer.call_llm = mock_llm_neutral

        state = create_initial_state(message="Test", context={})

        result = await analyzer.process(state)

        assert "sentiment_analyzer" in result["agent_history"]

    # ==================== Helper Method Tests ====================

    def test_format_customer_context_with_full_context(self, analyzer):
        """Test context formatting with all fields."""
        context = {
            "plan": "enterprise",
            "health_score": 75,
            "churn_risk": 0.3,
            "team_size": 50,
            "mrr": 5000
        }

        result = analyzer._format_customer_context(context)

        assert "Plan: enterprise" in result
        assert "Health Score: 75/100" in result
        assert "Churn Risk: 30%" in result
        assert "Team Size: 50" in result
        assert "MRR: $5000" in result

    def test_format_customer_context_empty(self, analyzer):
        """Test context formatting with empty context."""
        result = analyzer._format_customer_context({})
        assert result == ""

    def test_escalate_urgency(self, analyzer):
        """Test urgency escalation logic."""
        assert analyzer._escalate_urgency("low") == "medium"
        assert analyzer._escalate_urgency("medium") == "high"
        assert analyzer._escalate_urgency("high") == "critical"
        assert analyzer._escalate_urgency("critical") == "critical"

    def test_get_default_sentiment(self, analyzer):
        """Test default sentiment values."""
        default = analyzer._get_default_sentiment()

        assert default["sentiment_score"] == 0.0
        assert default["emotion"] == "neutral"
        assert default["urgency"] == "medium"
        assert default["satisfaction"] == 0.5
        assert default["politeness"] == 0.7
        assert "sentiment_metadata" in default

    # ==================== Emotion Range Tests ====================

    @pytest.mark.asyncio
    async def test_frustrated_emotion(self, analyzer):
        """Test frustrated emotion detection."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": -0.3,
                "emotion": "frustrated",
                "urgency": "medium",
                "satisfaction": 0.4,
                "politeness": 0.6
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(message="This is frustrating", context={})
        result = await analyzer.process(state)

        assert result["emotion"] == "frustrated"
        assert -0.6 < result["sentiment_score"] < -0.2

    @pytest.mark.asyncio
    async def test_excited_emotion(self, analyzer):
        """Test excited emotion detection."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": 0.85,
                "emotion": "excited",
                "urgency": "low",
                "satisfaction": 0.9,
                "politeness": 0.9
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(message="This is amazing!", context={})
        result = await analyzer.process(state)

        assert result["emotion"] == "excited"
        assert result["sentiment_score"] > 0.6


class TestSentimentAnalyzerIntegration:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_urgent_angry_scenario(self):
        """Test realistic urgent angry customer scenario."""
        analyzer = SentimentAnalyzer()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": -0.9,
                "emotion": "angry",
                "urgency": "critical",
                "satisfaction": 0.1,
                "politeness": 0.2,
                "indicators": {
                    "negative_keywords": ["broken", "days", "can't work"],
                    "urgency_keywords": ["urgent", "immediately"],
                    "business_impact": True
                },
                "reasoning": "Severe issue with business impact, hostile tone"
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(
            message="This is URGENT! The app has been broken for 3 days and we can't work!",
            context={"customer_metadata": {"plan": "enterprise", "health_score": 20, "churn_risk": 0.9}}
        )

        result = await analyzer.process(state)

        assert result["emotion"] == "angry"
        assert result["urgency"] == "critical"
        assert result["sentiment_score"] < -0.5
        assert result["satisfaction"] < 0.3

    @pytest.mark.asyncio
    async def test_realistic_positive_scenario(self):
        """Test realistic positive customer feedback."""
        analyzer = SentimentAnalyzer()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "sentiment_score": 0.92,
                "emotion": "happy",
                "urgency": "low",
                "satisfaction": 0.95,
                "politeness": 0.98,
                "indicators": {},
                "reasoning": "Grateful, positive feedback"
            })

        analyzer.call_llm = mock_llm

        state = create_initial_state(
            message="Thank you so much for the quick help! You've been amazing!",
            context={}
        )

        result = await analyzer.process(state)

        assert result["emotion"] == "happy"
        assert result["sentiment_score"] > 0.8
        assert result["satisfaction"] > 0.9
        assert result["urgency"] == "low"
