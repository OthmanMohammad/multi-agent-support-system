"""
Unit tests for Escalation Decider.

Tests all 7 escalation triggers, urgency calculation,
and team suggestion logic.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-111)
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.routing.escalation_decider import EscalationDecider
from src.workflow.state import create_initial_state


class TestEscalationDecider:
    """Test suite for Escalation Decider."""

    @pytest.fixture
    def decider(self):
        """Create EscalationDecider instance for testing."""
        return EscalationDecider()

    def test_initialization(self, decider):
        """Test EscalationDecider initializes correctly."""
        assert decider.config.name == "escalation_decider"
        assert decider.config.type.value == "analyzer"
        assert decider.CONFIDENCE_THRESHOLD == 0.4
        assert decider.SENTIMENT_THRESHOLD == -0.7
        assert decider.MAX_TURNS_THRESHOLD == 5

    def test_triggers_defined(self, decider):
        """Test that all triggers are defined."""
        assert len(decider.TRIGGERS) == 7
        expected_triggers = [
            "low_confidence",
            "very_negative_sentiment",
            "too_many_turns",
            "explicit_request",
            "high_value_customer",
            "regulatory_legal",
            "critical_bug"
        ]
        assert decider.TRIGGERS == expected_triggers

    # ==================== Trigger 1: Low Confidence ====================

    @pytest.mark.asyncio
    async def test_low_confidence_trigger(self, decider):
        """Test low confidence escalation trigger."""
        state = create_initial_state(message="Complex query", context={})
        state["confidence"] = 0.3  # Below 0.4 threshold

        result = await decider.should_escalate(state)

        assert result["should_escalate"] is True
        assert "low_confidence" in result["reasons"]
        assert result["trigger_details"]["low_confidence"]["confidence"] == 0.3

    @pytest.mark.asyncio
    async def test_high_confidence_no_trigger(self, decider):
        """Test high confidence doesn't trigger escalation."""
        state = create_initial_state(message="Simple query", context={})
        state["confidence"] = 0.9

        result = await decider.should_escalate(state)

        assert "low_confidence" not in result["reasons"]

    # ==================== Trigger 2: Very Negative Sentiment ====================

    @pytest.mark.asyncio
    async def test_very_negative_sentiment_trigger(self, decider):
        """Test very negative sentiment escalation trigger."""
        state = create_initial_state(message="This is terrible!", context={})
        state["sentiment_score"] = -0.85  # Below -0.7 threshold
        state["emotion"] = "angry"

        result = await decider.should_escalate(state)

        assert result["should_escalate"] is True
        assert "very_negative_sentiment" in result["reasons"]
        assert result["trigger_details"]["very_negative_sentiment"]["sentiment_score"] == -0.85
        assert result["trigger_details"]["very_negative_sentiment"]["emotion"] == "angry"

    @pytest.mark.asyncio
    async def test_neutral_sentiment_no_trigger(self, decider):
        """Test neutral sentiment doesn't trigger escalation."""
        state = create_initial_state(message="Question", context={})
        state["sentiment_score"] = 0.0

        result = await decider.should_escalate(state)

        assert "very_negative_sentiment" not in result["reasons"]

    # ==================== Trigger 3: Too Many Turns ====================

    @pytest.mark.asyncio
    async def test_too_many_turns_trigger(self, decider):
        """Test too many turns escalation trigger."""
        state = create_initial_state(message="Still not resolved", context={})
        state["turn_count"] = 6  # Above 5 threshold

        result = await decider.should_escalate(state)

        assert result["should_escalate"] is True
        assert "too_many_turns" in result["reasons"]
        assert result["trigger_details"]["too_many_turns"]["turn_count"] == 6

    @pytest.mark.asyncio
    async def test_few_turns_no_trigger(self, decider):
        """Test few turns doesn't trigger escalation."""
        state = create_initial_state(message="First question", context={})
        state["turn_count"] = 2

        result = await decider.should_escalate(state)

        assert "too_many_turns" not in result["reasons"]

    # ==================== Trigger 4: Explicit Request ====================

    @pytest.mark.asyncio
    async def test_explicit_human_request_trigger(self, decider):
        """Test explicit human request escalation trigger."""
        messages = [
            "I want to speak to a human",
            "Can I talk to a real person?",
            "Get me an agent please",
            "I need to speak with a manager",
            "Connect me to a representative"
        ]

        for msg in messages:
            state = create_initial_state(message=msg, context={})

            result = await decider.should_escalate(state)

            assert result["should_escalate"] is True, f"Failed for: {msg}"
            assert "explicit_request" in result["reasons"], f"Failed for: {msg}"

    @pytest.mark.asyncio
    async def test_no_explicit_request(self, decider):
        """Test messages without explicit human request."""
        state = create_initial_state(message="How do I reset my password?", context={})

        result = await decider.should_escalate(state)

        assert "explicit_request" not in result["reasons"]

    # ==================== Trigger 5: High-Value Customer ====================

    @pytest.mark.asyncio
    async def test_high_value_customer_enterprise_complex(self, decider):
        """Test high-value customer trigger (enterprise + complex)."""
        state = create_initial_state(message="Complex issue", context={})
        state["customer_metadata"] = {"plan": "enterprise"}
        state["complexity_score"] = 8  # Above 7 threshold

        result = await decider.should_escalate(state)

        assert result["should_escalate"] is True
        assert "high_value_customer" in result["reasons"]

    @pytest.mark.asyncio
    async def test_high_value_customer_high_mrr(self, decider):
        """Test high-value customer trigger (high MRR + complex)."""
        state = create_initial_state(message="Complex issue", context={})
        state["customer_metadata"] = {"mrr": 6000}
        state["complexity_score"] = 8

        result = await decider.should_escalate(state)

        assert result["should_escalate"] is True
        assert "high_value_customer" in result["reasons"]

    @pytest.mark.asyncio
    async def test_enterprise_simple_no_trigger(self, decider):
        """Test enterprise customer with simple issue doesn't trigger."""
        state = create_initial_state(message="Simple question", context={})
        state["customer_metadata"] = {"plan": "enterprise"}
        state["complexity_score"] = 3  # Below 7 threshold

        result = await decider.should_escalate(state)

        assert "high_value_customer" not in result["reasons"]

    # ==================== Trigger 6: Regulatory/Legal ====================

    @pytest.mark.asyncio
    async def test_legal_keywords_trigger(self, decider):
        """Test legal/regulatory keywords trigger escalation."""
        legal_messages = [
            "This is a GDPR violation",
            "I'm contacting my lawyer",
            "I will sue you",
            "Legal action will be taken",
            "This violates data protection",
            "Compliance issue here"
        ]

        for msg in legal_messages:
            state = create_initial_state(message=msg, context={})

            result = await decider.should_escalate(state)

            assert result["should_escalate"] is True, f"Failed for: {msg}"
            assert "regulatory_legal" in result["reasons"], f"Failed for: {msg}"

    @pytest.mark.asyncio
    async def test_no_legal_keywords(self, decider):
        """Test regular message doesn't trigger legal escalation."""
        state = create_initial_state(message="I need help with billing", context={})

        result = await decider.should_escalate(state)

        assert "regulatory_legal" not in result["reasons"]

    # ==================== Trigger 7: Critical Bug ====================

    @pytest.mark.asyncio
    async def test_critical_bug_keywords_trigger(self, decider):
        """Test critical bug keywords trigger escalation."""
        critical_messages = [
            "Production is down!",
            "URGENT: System is not accessible",
            "We lost all our data",
            "Critical emergency",
            "Need help ASAP - system crashed"
        ]

        for msg in critical_messages:
            state = create_initial_state(message=msg, context={})

            result = await decider.should_escalate(state)

            assert result["should_escalate"] is True, f"Failed for: {msg}"
            assert "critical_bug" in result["reasons"], f"Failed for: {msg}"

    @pytest.mark.asyncio
    async def test_critical_urgency_triggers(self, decider):
        """Test critical urgency level triggers escalation."""
        state = create_initial_state(message="Issue with system", context={})
        state["urgency"] = "critical"

        result = await decider.should_escalate(state)

        assert result["should_escalate"] is True
        assert "critical_bug" in result["reasons"]

    # ==================== Urgency Calculation Tests ====================

    @pytest.mark.asyncio
    async def test_urgency_critical_for_critical_triggers(self, decider):
        """Test urgency is critical for critical triggers."""
        state = create_initial_state(message="Production down!", context={})

        result = await decider.should_escalate(state)

        assert result["urgency"] == "critical"

    @pytest.mark.asyncio
    async def test_urgency_critical_for_legal(self, decider):
        """Test urgency is critical for legal issues."""
        state = create_initial_state(message="GDPR violation", context={})

        result = await decider.should_escalate(state)

        assert result["urgency"] == "critical"

    @pytest.mark.asyncio
    async def test_urgency_high_for_negative_sentiment(self, decider):
        """Test urgency is high for very negative sentiment."""
        state = create_initial_state(message="This is terrible", context={})
        state["sentiment_score"] = -0.8

        result = await decider.should_escalate(state)

        assert result["urgency"] == "high"

    @pytest.mark.asyncio
    async def test_urgency_high_for_enterprise(self, decider):
        """Test urgency is high for high-value customers."""
        state = create_initial_state(message="Issue", context={})
        state["customer_metadata"] = {"plan": "enterprise"}
        state["complexity_score"] = 8

        result = await decider.should_escalate(state)

        assert result["urgency"] == "high"

    @pytest.mark.asyncio
    async def test_urgency_medium_for_explicit_request(self, decider):
        """Test urgency is medium for explicit requests."""
        state = create_initial_state(message="I want to speak to a human", context={})

        result = await decider.should_escalate(state)

        assert result["urgency"] == "medium"

    @pytest.mark.asyncio
    async def test_urgency_low_for_low_confidence(self, decider):
        """Test urgency is low for low confidence alone."""
        state = create_initial_state(message="Question", context={})
        state["confidence"] = 0.3

        result = await decider.should_escalate(state)

        assert result["urgency"] == "low"

    # ==================== Team Suggestion Tests ====================

    @pytest.mark.asyncio
    async def test_suggest_executive_for_legal(self, decider):
        """Test executive team suggested for legal issues."""
        state = create_initial_state(message="GDPR violation", context={})

        result = await decider.should_escalate(state)

        assert result["suggested_team"] == "executive"

    @pytest.mark.asyncio
    async def test_suggest_executive_for_high_mrr(self, decider):
        """Test executive team for very high MRR customers."""
        state = create_initial_state(message="Issue", context={})
        state["customer_metadata"] = {"plan": "enterprise", "mrr": 15000}
        state["complexity_score"] = 8

        result = await decider.should_escalate(state)

        assert result["suggested_team"] == "executive"

    @pytest.mark.asyncio
    async def test_suggest_management_for_enterprise(self, decider):
        """Test management team for enterprise customers."""
        state = create_initial_state(message="Issue", context={})
        state["customer_metadata"] = {"plan": "enterprise", "mrr": 5000}
        state["complexity_score"] = 8

        result = await decider.should_escalate(state)

        assert result["suggested_team"] == "management"

    @pytest.mark.asyncio
    async def test_suggest_specialist_for_critical_bug(self, decider):
        """Test specialist team for critical bugs."""
        state = create_initial_state(message="Production down", context={})

        result = await decider.should_escalate(state)

        assert result["suggested_team"] == "specialist"

    @pytest.mark.asyncio
    async def test_suggest_tier2_for_general(self, decider):
        """Test tier2 support for general escalations."""
        state = create_initial_state(message="I want to speak to someone", context={})

        result = await decider.should_escalate(state)

        assert result["suggested_team"] == "tier2_support"

    # ==================== Process Method Tests ====================

    @pytest.mark.asyncio
    async def test_process_populates_state_fields(self, decider):
        """Test process method populates all state fields."""
        state = create_initial_state(message="This is broken", context={})
        state["sentiment_score"] = -0.8

        result = await decider.process(state)

        # Check all expected fields
        assert "should_escalate" in result
        assert "escalation_reasons" in result
        assert "escalation_urgency" in result
        assert "escalation_suggested_team" in result
        assert "escalation_trigger_details" in result
        assert "escalation_metadata" in result

    @pytest.mark.asyncio
    async def test_process_handles_errors_gracefully(self, decider):
        """Test process handles errors without crashing."""
        # Create invalid state that might cause issues
        state = create_initial_state(message="Test", context={})
        state["current_message"] = None  # Invalid

        result = await decider.process(state)

        # Should not crash, should default to no escalation
        assert result["should_escalate"] is False

    # ==================== Helper Method Tests ====================

    def test_detect_human_request_positive(self, decider):
        """Test human request detection for positive cases."""
        messages = [
            "i want to speak to a human",
            "get me a real person",
            "connect me to an agent",
            "i need a manager"
        ]

        for msg in messages:
            assert decider._detect_human_request(msg) is True, f"Failed for: {msg}"

    def test_detect_human_request_negative(self, decider):
        """Test human request detection for negative cases."""
        messages = [
            "how do i reset my password",
            "what is your pricing",
            "i need help with billing"
        ]

        for msg in messages:
            assert decider._detect_human_request(msg) is False, f"Failed for: {msg}"

    def test_detect_legal_issue_positive(self, decider):
        """Test legal issue detection for positive cases."""
        messages = [
            "this is a gdpr violation",
            "i'm calling my lawyer",
            "sue you",
            "compliance issue"
        ]

        for msg in messages:
            assert decider._detect_legal_issue(msg) is True, f"Failed for: {msg}"

    def test_detect_legal_issue_negative(self, decider):
        """Test legal issue detection for negative cases."""
        messages = [
            "i need help with billing",
            "app is not working",
            "how do i upgrade"
        ]

        for msg in messages:
            assert decider._detect_legal_issue(msg) is False, f"Failed for: {msg}"

    def test_get_escalation_summary_no_escalation(self, decider):
        """Test escalation summary when no escalation needed."""
        state = create_initial_state(message="Test", context={})
        state["should_escalate"] = False

        summary = decider.get_escalation_summary(state)

        assert "No escalation needed" in summary

    def test_get_escalation_summary_with_escalation(self, decider):
        """Test escalation summary with escalation."""
        state = create_initial_state(message="Test", context={})
        state["should_escalate"] = True
        state["escalation_reasons"] = ["low_confidence", "too_many_turns"]
        state["escalation_urgency"] = "medium"
        state["escalation_suggested_team"] = "tier2_support"

        summary = decider.get_escalation_summary(state)

        assert "ESCALATE" in summary
        assert "tier2_support" in summary
        assert "medium" in summary
        assert "low_confidence" in summary
        assert "too_many_turns" in summary

    # ==================== Multiple Triggers Tests ====================

    @pytest.mark.asyncio
    async def test_multiple_triggers_combine(self, decider):
        """Test multiple triggers combine correctly."""
        state = create_initial_state(
            message="I want a human this is taking too long",
            context={}
        )
        state["confidence"] = 0.3
        state["turn_count"] = 6

        result = await decider.should_escalate(state)

        # Should have multiple triggers
        assert result["should_escalate"] is True
        assert "low_confidence" in result["reasons"]
        assert "too_many_turns" in result["reasons"]
        assert "explicit_request" in result["reasons"]
        assert len(result["reasons"]) >= 3

    @pytest.mark.asyncio
    async def test_no_triggers_no_escalation(self, decider):
        """Test no triggers means no escalation."""
        state = create_initial_state(message="How do I export data?", context={})
        state["confidence"] = 0.9
        state["sentiment_score"] = 0.0
        state["turn_count"] = 1

        result = await decider.should_escalate(state)

        assert result["should_escalate"] is False
        assert len(result["reasons"]) == 0


# ==================== Integration Tests ====================

class TestEscalationDeciderIntegration:
    """Integration tests for realistic escalation scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_angry_customer_scenario(self):
        """Test realistic angry customer escalation."""
        decider = EscalationDecider()

        state = create_initial_state(
            message="This is UNACCEPTABLE! I want to speak to a manager NOW!",
            context={"customer_metadata": {"plan": "enterprise"}}
        )
        state["sentiment_score"] = -0.9
        state["emotion"] = "angry"
        state["turn_count"] = 6

        result = await decider.process(state)

        # Should escalate
        assert result["should_escalate"] is True

        # Should have multiple triggers
        assert "very_negative_sentiment" in result["escalation_reasons"]
        assert "too_many_turns" in result["escalation_reasons"]
        assert "explicit_request" in result["escalation_reasons"]

        # Should have high urgency
        assert result["escalation_urgency"] in ["high", "critical"]

    @pytest.mark.asyncio
    async def test_realistic_legal_threat_scenario(self):
        """Test realistic legal threat escalation."""
        decider = EscalationDecider()

        state = create_initial_state(
            message="This is a GDPR violation and I'm contacting my lawyer",
            context={}
        )

        result = await decider.process(state)

        # Should escalate immediately
        assert result["should_escalate"] is True
        assert "regulatory_legal" in result["escalation_reasons"]

        # Should be critical urgency
        assert result["escalation_urgency"] == "critical"

        # Should go to executive team
        assert result["escalation_suggested_team"] == "executive"

    @pytest.mark.asyncio
    async def test_realistic_production_down_scenario(self):
        """Test realistic production down escalation."""
        decider = EscalationDecider()

        state = create_initial_state(
            message="URGENT: Our production system is completely down and we can't access anything!",
            context={"customer_metadata": {"plan": "enterprise", "mrr": 10000}}
        )
        state["urgency"] = "critical"

        result = await decider.process(state)

        # Should escalate
        assert result["should_escalate"] is True
        assert "critical_bug" in result["escalation_reasons"]

        # Should be critical urgency
        assert result["escalation_urgency"] == "critical"

        # Should go to specialist
        assert result["escalation_suggested_team"] == "specialist"
