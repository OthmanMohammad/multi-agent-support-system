"""
Unit tests for Rate Limit Advisor agent.

Tests rate limit topic detection, plan-specific guidance, optimization
strategies, and handling of rate limit errors.

Part of: STORY-006 Integration Specialists Sub-Swarm (TASK-603)
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.support.integration.rate_limit_advisor import RateLimitAdvisor
from src.workflow.state import create_initial_state


@pytest.fixture
def rate_limit_advisor():
    """Create RateLimitAdvisor instance for testing."""
    return RateLimitAdvisor()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Test message",
        context={"customer_metadata": {"plan": "premium"}}
    )


class TestRateLimitAdvisorInitialization:
    """Test Rate Limit Advisor initialization and configuration."""

    def test_initialization(self, rate_limit_advisor):
        """Test that agent initializes with correct configuration."""
        assert rate_limit_advisor.config.name == "rate_limit_advisor"
        assert rate_limit_advisor.config.type.value == "specialist"
        assert rate_limit_advisor.config.model == "claude-3-haiku-20240307"
        assert rate_limit_advisor.config.temperature == 0.3
        assert rate_limit_advisor.config.tier == "essential"

    def test_has_required_capabilities(self, rate_limit_advisor):
        """Test that agent has required capabilities."""
        from src.agents.base.agent_types import AgentCapability

        capabilities = rate_limit_advisor.config.capabilities
        assert AgentCapability.KB_SEARCH in capabilities
        assert AgentCapability.CONTEXT_AWARE in capabilities

    def test_has_rate_limit_data(self, rate_limit_advisor):
        """Test that agent has rate limit data for all plans."""
        assert "free" in rate_limit_advisor.RATE_LIMITS
        assert "basic" in rate_limit_advisor.RATE_LIMITS
        assert "premium" in rate_limit_advisor.RATE_LIMITS
        assert "enterprise" in rate_limit_advisor.RATE_LIMITS


class TestTopicDetection:
    """Test rate limit topic detection."""

    def test_detect_hitting_limit_topic(self, rate_limit_advisor):
        """Test detecting hitting rate limit."""
        topic = rate_limit_advisor._detect_rate_limit_topic("I'm getting 429 errors")
        assert topic == "hitting_limit"

    def test_detect_understand_limits_topic(self, rate_limit_advisor):
        """Test detecting requests to understand limits."""
        topic = rate_limit_advisor._detect_rate_limit_topic("What are my rate limits?")
        assert topic == "understand_limits"

    def test_detect_optimize_topic(self, rate_limit_advisor):
        """Test detecting optimization requests."""
        topic = rate_limit_advisor._detect_rate_limit_topic("How can I optimize my API usage?")
        assert topic == "optimize"

    def test_detect_upgrade_topic(self, rate_limit_advisor):
        """Test detecting upgrade requests."""
        topic = rate_limit_advisor._detect_rate_limit_topic("I need more requests, can I upgrade?")
        assert topic == "upgrade"

    def test_detect_headers_topic(self, rate_limit_advisor):
        """Test detecting rate limit header questions."""
        topic = rate_limit_advisor._detect_rate_limit_topic("What do the X-RateLimit headers mean?")
        assert topic == "headers"


class TestRateLimitProcessing:
    """Test rate limit request processing."""

    @pytest.mark.asyncio
    async def test_process_with_free_plan(self, rate_limit_advisor):
        """Test processing with free plan customer."""
        state = create_initial_state(
            "What are my rate limits?",
            context={"customer_metadata": {"plan": "free"}}
        )

        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert result["customer_plan"] == "free"
        assert "100" in result["agent_response"] or "free" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_with_premium_plan(self, rate_limit_advisor):
        """Test processing with premium plan customer."""
        state = create_initial_state(
            "What are my rate limits?",
            context={"customer_metadata": {"plan": "premium"}}
        )

        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert result["customer_plan"] == "premium"
        assert "10000" in result["agent_response"] or "10,000" in result["agent_response"]
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_hitting_limit(self, rate_limit_advisor):
        """Test processing when customer is hitting limit."""
        state = create_initial_state(
            "Getting 429 rate limit errors",
            context={"customer_metadata": {"plan": "basic"}}
        )

        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert result["rate_limit_topic"] == "hitting_limit"
        assert "429" in result["agent_response"] or "retry" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_optimization_request(self, rate_limit_advisor):
        """Test processing optimization request."""
        state = create_initial_state("How can I optimize my API usage?")

        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert result["rate_limit_topic"] == "optimize"
        assert "webhook" in result["agent_response"].lower() or "cache" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_includes_kb_results(self, rate_limit_advisor):
        """Test that KB results are included in response."""
        state = create_initial_state("Rate limit help")

        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[
            {"title": "Rate Limits Guide", "doc_id": "kb_123"},
            {"title": "API Optimization", "doc_id": "kb_456"}
        ])

        result = await rate_limit_advisor.process(state)

        assert len(result["kb_results"]) == 2
        assert "Related documentation" in result["agent_response"] or "documentation" in result["agent_response"].lower()


class TestGuidanceContent:
    """Test rate limit guidance content."""

    def test_explain_limits_contains_plan_info(self, rate_limit_advisor):
        """Test that limit explanation contains plan-specific info."""
        guide = rate_limit_advisor._guide_explain_limits("premium")

        assert "10000" in guide or "10,000" in guide
        assert "premium" in guide.lower()

    def test_handling_429_contains_retry_logic(self, rate_limit_advisor):
        """Test that 429 handling contains retry logic."""
        guide = rate_limit_advisor._guide_handling_429("basic")

        assert "429" in guide
        assert "retry" in guide.lower()
        assert "exponential" in guide.lower() or "backoff" in guide.lower()

    def test_optimization_contains_strategies(self, rate_limit_advisor):
        """Test that optimization guide contains strategies."""
        guide = rate_limit_advisor._guide_optimization()

        assert "webhook" in guide.lower()
        assert "cache" in guide.lower() or "caching" in guide.lower()
        assert "batch" in guide.lower()

    def test_upgrade_options_contains_plans(self, rate_limit_advisor):
        """Test that upgrade options contains plan information."""
        guide = rate_limit_advisor._guide_upgrade_options("free")

        assert "basic" in guide.lower() or "upgrade" in guide.lower()

    def test_headers_guide_contains_header_info(self, rate_limit_advisor):
        """Test that headers guide contains header information."""
        guide = rate_limit_advisor._guide_rate_limit_headers("premium")

        assert "x-ratelimit" in guide.lower()
        assert "remaining" in guide.lower()


class TestPlanSpecificGuidance:
    """Test plan-specific guidance."""

    def test_free_plan_limits(self, rate_limit_advisor):
        """Test free plan limits are correct."""
        limits = rate_limit_advisor.RATE_LIMITS["free"]

        assert limits["requests_per_hour"] == 100
        assert limits["requests_per_minute"] == 10

    def test_basic_plan_limits(self, rate_limit_advisor):
        """Test basic plan limits are correct."""
        limits = rate_limit_advisor.RATE_LIMITS["basic"]

        assert limits["requests_per_hour"] == 1000
        assert limits["requests_per_minute"] == 50

    def test_premium_plan_limits(self, rate_limit_advisor):
        """Test premium plan limits are correct."""
        limits = rate_limit_advisor.RATE_LIMITS["premium"]

        assert limits["requests_per_hour"] == 10000
        assert limits["requests_per_minute"] == 200

    def test_enterprise_plan_limits(self, rate_limit_advisor):
        """Test enterprise plan limits are correct."""
        limits = rate_limit_advisor.RATE_LIMITS["enterprise"]

        assert limits["requests_per_hour"] == 100000
        assert limits["requests_per_minute"] == 1000


class TestUpgradeSuggestions:
    """Test upgrade suggestions."""

    def test_upgrade_suggestion_for_free(self, rate_limit_advisor):
        """Test upgrade suggestion for free plan."""
        suggestion = rate_limit_advisor._get_upgrade_suggestion("free")

        assert "basic" in suggestion.lower() or "upgrade" in suggestion.lower()

    def test_upgrade_suggestion_for_basic(self, rate_limit_advisor):
        """Test upgrade suggestion for basic plan."""
        suggestion = rate_limit_advisor._get_upgrade_suggestion("basic")

        assert "premium" in suggestion.lower()

    def test_upgrade_suggestion_for_enterprise(self, rate_limit_advisor):
        """Test upgrade suggestion for enterprise plan (highest)."""
        suggestion = rate_limit_advisor._get_upgrade_suggestion("enterprise")

        assert "sales" in suggestion.lower() or "custom" in suggestion.lower()


class TestStateUpdates:
    """Test state updates."""

    @pytest.mark.asyncio
    async def test_updates_agent_history(self, rate_limit_advisor):
        """Test that agent is added to history."""
        state = create_initial_state("Rate limit question")
        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert "rate_limit_advisor" in result["agent_history"]

    @pytest.mark.asyncio
    async def test_sets_high_confidence(self, rate_limit_advisor):
        """Test that response confidence is high."""
        state = create_initial_state("What are my limits?")
        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert result["response_confidence"] >= 0.85

    @pytest.mark.asyncio
    async def test_includes_customer_plan(self, rate_limit_advisor):
        """Test that customer plan is included in result."""
        state = create_initial_state(
            "Rate limits?",
            context={"customer_metadata": {"plan": "premium"}}
        )
        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert result["customer_plan"] == "premium"

    @pytest.mark.asyncio
    async def test_marks_as_resolved(self, rate_limit_advisor):
        """Test that status is marked as resolved."""
        state = create_initial_state("Rate limit help")
        rate_limit_advisor.search_knowledge_base = AsyncMock(return_value=[])

        result = await rate_limit_advisor.process(state)

        assert result["status"] == "resolved"
        assert result["next_agent"] is None
