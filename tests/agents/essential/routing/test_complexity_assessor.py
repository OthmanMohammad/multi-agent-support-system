"""
Unit tests for Complexity Assessor.

Tests complexity scoring, multi-agent collaboration detection,
and resolution time estimation.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-106)
"""

import pytest
import json
from unittest.mock import AsyncMock

from src.agents.essential.routing.complexity_assessor import ComplexityAssessor
from src.workflow.state import create_initial_state


class TestComplexityAssessor:
    """Test suite for Complexity Assessor."""

    @pytest.fixture
    def assessor(self):
        """Create ComplexityAssessor instance for testing."""
        return ComplexityAssessor()

    def test_initialization(self, assessor):
        """Test ComplexityAssessor initializes correctly."""
        assert assessor.config.name == "complexity_assessor"
        assert assessor.config.type.value == "analyzer"
        assert assessor.config.model == "claude-3-haiku-20240307"
        assert assessor.config.temperature == 0.2
        assert assessor.config.max_tokens == 300

    def test_complexity_levels_defined(self, assessor):
        """Test complexity levels are defined."""
        expected_levels = {
            (1, 3): "simple",
            (4, 6): "moderate",
            (7, 8): "complex",
            (9, 10): "very_complex"
        }
        assert assessor.COMPLEXITY_LEVELS == expected_levels

    # ==================== Simple Complexity Tests ====================

    @pytest.mark.asyncio
    async def test_simple_query_assessment(self, assessor):
        """Test assessment of simple query."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 2,
                "complexity_level": "simple",
                "multi_agent_needed": False,
                "estimated_resolution_time": "quick",
                "skill_requirements": [],
                "complexity_factors": ["Single straightforward question"],
                "reasoning": "Simple how-to question"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="How do I reset my password?",
            context={}
        )

        result = await assessor.process(state)

        assert result["complexity_score"] == 2
        assert result["complexity_level"] == "simple"
        assert result["multi_agent_needed"] is False
        assert result["estimated_resolution_time"] == "quick"

    # ==================== Moderate Complexity Tests ====================

    @pytest.mark.asyncio
    async def test_moderate_query_assessment(self, assessor):
        """Test assessment of moderate complexity query."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium",
                "skill_requirements": ["technical_support"],
                "complexity_factors": ["Requires investigation"],
                "reasoning": "Technical issue requiring investigation"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="Why isn't the sync feature working?",
            context={}
        )

        result = await assessor.process(state)

        assert result["complexity_score"] == 5
        assert result["complexity_level"] == "moderate"
        assert result["estimated_resolution_time"] == "medium"

    # ==================== Complex Query Tests ====================

    @pytest.mark.asyncio
    async def test_complex_query_assessment(self, assessor):
        """Test assessment of complex query."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 7,
                "complexity_level": "complex",
                "multi_agent_needed": True,
                "estimated_resolution_time": "long",
                "skill_requirements": ["technical_support", "billing_specialist"],
                "complexity_factors": [
                    "Cross-domain issue",
                    "Multiple systems involved"
                ],
                "reasoning": "Technical issue affecting billing"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="The export feature crashes and I'm being charged incorrectly",
            context={}
        )

        result = await assessor.process(state)

        assert result["complexity_score"] == 7
        assert result["complexity_level"] == "complex"
        assert result["multi_agent_needed"] is True
        assert result["estimated_resolution_time"] == "long"
        assert len(result["skill_requirements"]) == 2

    # ==================== Very Complex Query Tests ====================

    @pytest.mark.asyncio
    async def test_very_complex_query_assessment(self, assessor):
        """Test assessment of very complex query."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 9,
                "complexity_level": "very_complex",
                "multi_agent_needed": True,
                "estimated_resolution_time": "long",
                "skill_requirements": [
                    "technical_support",
                    "integration_expert",
                    "customer_success",
                    "security_specialist"
                ],
                "complexity_factors": [
                    "Enterprise migration",
                    "Custom SSO setup",
                    "Multi-system integration",
                    "Training required"
                ],
                "reasoning": "Complex enterprise onboarding with multiple requirements"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="We need to migrate from Asana, set up custom SSO, integrate with Salesforce and Jira, and train 200 users",
            context={"customer_metadata": {"plan": "enterprise", "team_size": 200}}
        )

        result = await assessor.process(state)

        assert result["complexity_score"] == 9
        assert result["complexity_level"] == "very_complex"
        assert result["multi_agent_needed"] is True
        assert len(result["skill_requirements"]) >= 3

    # ==================== Auto Multi-Agent Logic Tests ====================

    @pytest.mark.asyncio
    async def test_auto_multi_agent_for_high_complexity(self, assessor):
        """Test multi-agent automatically set for complexity >= 8."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 8,
                "complexity_level": "complex",
                "multi_agent_needed": False,  # LLM says false
                "estimated_resolution_time": "long",
                "skill_requirements": ["technical_support"],
                "complexity_factors": []
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Complex issue", context={})
        result = await assessor.process(state)

        # Should be auto-set to true despite LLM saying false
        assert result["multi_agent_needed"] is True

    # ==================== Context Adjustment Tests ====================

    @pytest.mark.asyncio
    async def test_enterprise_complex_enables_multi_agent(self, assessor):
        """Test enterprise customer with complex issue enables multi-agent."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 6,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium",
                "skill_requirements": []
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="Technical issue",
            context={"customer_metadata": {"plan": "enterprise"}}
        )

        result = await assessor.process(state)

        # Enterprise + complexity >= 6 → multi-agent needed
        assert result["multi_agent_needed"] is True

    @pytest.mark.asyncio
    async def test_high_churn_risk_escalates_complexity(self, assessor):
        """Test high churn risk escalates complexity."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium",
                "skill_requirements": []
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="Issue with the product",
            context={"customer_metadata": {"churn_risk": 0.85}}
        )

        result = await assessor.process(state)

        # Churn risk > 0.7 and complexity >= 5 → escalate and enable multi-agent
        assert result["complexity_score"] >= 5
        assert result["multi_agent_needed"] is True

    @pytest.mark.asyncio
    async def test_low_health_score_enables_multi_agent(self, assessor):
        """Test low health score enables multi-agent support."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium",
                "skill_requirements": []
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="Need help",
            context={"customer_metadata": {"health_score": 30}}
        )

        result = await assessor.process(state)

        # Health < 40 and complexity >= 5 → multi-agent
        assert result["multi_agent_needed"] is True

    @pytest.mark.asyncio
    async def test_critical_urgency_enables_multi_agent(self, assessor):
        """Test critical urgency enables multi-agent for faster resolution."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 6,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium",
                "skill_requirements": []
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Urgent issue", context={})
        state["urgency"] = "critical"

        result = await assessor.process(state)

        # Critical + complexity >= 6 → multi-agent
        assert result["multi_agent_needed"] is True

    # ==================== Validation Tests ====================

    @pytest.mark.asyncio
    async def test_complexity_score_clamped_to_range(self, assessor):
        """Test complexity score is clamped to 1-10."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 15,  # Invalid: too high
                "complexity_level": "very_complex",
                "multi_agent_needed": True,
                "estimated_resolution_time": "long"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await assessor.process(state)

        # Should be clamped to 10
        assert result["complexity_score"] == 10

    @pytest.mark.asyncio
    async def test_complexity_level_derived_from_score(self, assessor):
        """Test complexity level is derived from score."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 7,
                "complexity_level": "wrong_level",  # Will be overridden
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await assessor.process(state)

        # Score 7 → complex
        assert result["complexity_level"] == "complex"

    @pytest.mark.asyncio
    async def test_resolution_time_derived_from_complexity(self, assessor):
        """Test resolution time derived from complexity if invalid."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 8,
                "complexity_level": "complex",
                "multi_agent_needed": True,
                "estimated_resolution_time": "invalid_time"  # Invalid
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        result = await assessor.process(state)

        # Score 8 → long
        assert result["estimated_resolution_time"] == "long"

    # ==================== Error Handling Tests ====================

    @pytest.mark.asyncio
    async def test_empty_message_returns_default_assessment(self, assessor):
        """Test empty message returns default assessment."""
        state = create_initial_state(message="", context={})

        result = await assessor.process(state)

        assert result["complexity_score"] == 5
        assert result["complexity_level"] == "moderate"
        assert result["multi_agent_needed"] is False
        assert result["estimated_resolution_time"] == "medium"

    @pytest.mark.asyncio
    async def test_llm_failure_returns_default_assessment(self, assessor):
        """Test LLM failure returns default assessment gracefully."""
        assessor.call_llm = AsyncMock(side_effect=Exception("API Error"))

        state = create_initial_state(message="Test", context={})

        result = await assessor.process(state)

        # Should fallback to moderate complexity
        assert result["complexity_score"] == 5
        assert result["complexity_level"] == "moderate"
        assert "complexity_metadata" in result

    @pytest.mark.asyncio
    async def test_invalid_json_returns_default_assessment(self, assessor):
        """Test invalid JSON response returns default assessment."""
        assessor.call_llm = AsyncMock(return_value="Not valid JSON!")

        state = create_initial_state(message="Test", context={})

        result = await assessor.process(state)

        assert result["complexity_score"] == 5
        assert result["complexity_level"] == "moderate"

    # ==================== State Management Tests ====================

    @pytest.mark.asyncio
    async def test_state_fields_populated(self, assessor):
        """Test all expected state fields are populated."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 6,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium",
                "skill_requirements": ["technical_support"],
                "complexity_factors": ["Test factor"],
                "reasoning": "Test reasoning"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})

        result = await assessor.process(state)

        # Check all expected fields are present
        assert "complexity_score" in result
        assert "complexity_level" in result
        assert "multi_agent_needed" in result
        assert "estimated_resolution_time" in result
        assert "skill_requirements" in result
        assert "complexity_factors" in result
        assert "complexity_reasoning" in result
        assert "complexity_metadata" in result

    @pytest.mark.asyncio
    async def test_metadata_includes_latency(self, assessor):
        """Test metadata includes latency measurement."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})

        result = await assessor.process(state)

        metadata = result["complexity_metadata"]
        assert "latency_ms" in metadata
        assert isinstance(metadata["latency_ms"], int)
        assert metadata["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_agent_history_updated(self, assessor):
        """Test agent history is updated after processing."""
        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})

        result = await assessor.process(state)

        assert "complexity_assessor" in result["agent_history"]

    # ==================== Context Building Tests ====================

    @pytest.mark.asyncio
    async def test_context_includes_routing_info(self, assessor):
        """Test context includes routing information."""
        async def mock_llm(*args, user_message="", **kwargs):
            # Verify context includes domain and category
            assert "Domain:" in user_message or "Context:" in user_message
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        state["intent_domain"] = "support"
        state["intent_category"] = "technical"

        await assessor.process(state)

    @pytest.mark.asyncio
    async def test_context_includes_sentiment(self, assessor):
        """Test context includes sentiment information."""
        async def mock_llm(*args, user_message="", **kwargs):
            assert "Emotion:" in user_message or "emotion" in user_message.lower()
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(message="Test", context={})
        state["emotion"] = "angry"
        state["urgency"] = "high"

        await assessor.process(state)

    # ==================== Helper Method Tests ====================

    def test_get_default_assessment(self, assessor):
        """Test default assessment values."""
        default = assessor._get_default_assessment()

        assert default["complexity_score"] == 5
        assert default["complexity_level"] == "moderate"
        assert default["multi_agent_needed"] is False
        assert default["estimated_resolution_time"] == "medium"
        assert "complexity_metadata" in default


# ==================== Integration Tests ====================

class TestComplexityAssessorIntegration:
    """Integration tests for realistic complexity scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_simple_scenario(self):
        """Test realistic simple password reset."""
        assessor = ComplexityAssessor()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 1,
                "complexity_level": "simple",
                "multi_agent_needed": False,
                "estimated_resolution_time": "quick",
                "skill_requirements": [],
                "complexity_factors": ["Simple how-to"],
                "reasoning": "Straightforward password reset"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="How do I reset my password?",
            context={}
        )

        result = await assessor.process(state)

        assert result["complexity_score"] == 1
        assert result["multi_agent_needed"] is False
        assert result["estimated_resolution_time"] == "quick"

    @pytest.mark.asyncio
    async def test_realistic_complex_enterprise_scenario(self):
        """Test realistic complex enterprise scenario."""
        assessor = ComplexityAssessor()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 9,
                "complexity_level": "very_complex",
                "multi_agent_needed": True,
                "estimated_resolution_time": "long",
                "skill_requirements": [
                    "integration_expert",
                    "security_specialist",
                    "customer_success"
                ],
                "complexity_factors": [
                    "Enterprise migration",
                    "Custom SSO",
                    "Multiple integrations",
                    "Large team training"
                ],
                "reasoning": "Complex enterprise onboarding with security and integration requirements"
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="We need to migrate 500 users from Jira, set up SAML SSO, integrate with Salesforce, GitHub, and Slack, and train our teams",
            context={"customer_metadata": {
                "plan": "enterprise",
                "team_size": 500,
                "health_score": 85
            }}
        )

        result = await assessor.process(state)

        assert result["complexity_score"] >= 8
        assert result["multi_agent_needed"] is True
        assert result["estimated_resolution_time"] == "long"
        assert len(result["skill_requirements"]) >= 2

    @pytest.mark.asyncio
    async def test_realistic_at_risk_customer_scenario(self):
        """Test at-risk customer scenario with complexity escalation."""
        assessor = ComplexityAssessor()

        async def mock_llm(*args, **kwargs):
            return json.dumps({
                "complexity_score": 5,
                "complexity_level": "moderate",
                "multi_agent_needed": False,
                "estimated_resolution_time": "medium",
                "skill_requirements": ["technical_support"]
            })

        assessor.call_llm = mock_llm

        state = create_initial_state(
            message="The sync isn't working and we're considering other options",
            context={"customer_metadata": {
                "plan": "enterprise",
                "health_score": 15,
                "churn_risk": 0.95,
                "mrr": 15000
            }}
        )

        state["emotion"] = "frustrated"
        state["urgency"] = "high"

        result = await assessor.process(state)

        # Should be escalated due to high churn risk
        assert result["complexity_score"] >= 5
        assert result["multi_agent_needed"] is True
