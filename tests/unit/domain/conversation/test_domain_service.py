"""
Tests for Conversation Domain Service

These tests verify pure business logic with NO database operations.
All data is passed as parameters - no mocking needed.
"""
import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from services.domain.conversation.domain_service import ConversationDomainService


class TestValidateMessage:
    """Tests for message validation"""
    
    def test_valid_message(self):
        """Valid message passes"""
        service = ConversationDomainService()
        result = service.validate_message("Hello, I need help")
        
        assert result.is_success
    
    def test_empty_message_fails(self):
        """Empty message fails"""
        service = ConversationDomainService()
        result = service.validate_message("")
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"


class TestValidateConversationCreation:
    """Tests for conversation creation validation"""
    
    def test_valid_creation_within_rate_limit(self):
        """Creation succeeds when within rate limit"""
        service = ConversationDomainService()
        
        result = service.validate_conversation_creation(
            customer_plan="free",
            today_conversation_count=5,
            customer_blocked=False
        )
        
        assert result.is_success
    
    def test_blocked_customer_fails(self):
        """Blocked customer cannot create conversation"""
        service = ConversationDomainService()
        
        result = service.validate_conversation_creation(
            customer_plan="free",
            today_conversation_count=0,
            customer_blocked=True
        )
        
        assert result.is_failure
        assert result.error.code == "BUSINESS_RULE_VIOLATION"
        assert "blocked" in result.error.message.lower()
        assert result.error.details["rule"] == "customer_not_blocked"
    
    def test_rate_limit_exceeded_fails(self):
        """Creation fails when rate limit exceeded"""
        service = ConversationDomainService()
        
        result = service.validate_conversation_creation(
            customer_plan="free",
            today_conversation_count=10,  # At limit
            customer_blocked=False
        )
        
        assert result.is_failure
        assert result.error.code == "BUSINESS_RULE_VIOLATION"
        assert "rate limit" in result.error.message.lower()
        assert result.error.details["rule"] == "within_rate_limit"
    
    def test_premium_unlimited_conversations(self):
        """Premium users have unlimited conversations"""
        service = ConversationDomainService()
        
        result = service.validate_conversation_creation(
            customer_plan="premium",
            today_conversation_count=1000,  # Way over free limit
            customer_blocked=False
        )
        
        assert result.is_success
    
    @pytest.mark.parametrize("plan,limit", [
        ("free", 10),
        ("basic", 100),
        ("premium", None),
        ("enterprise", None),
    ])
    def test_rate_limits_by_plan(self, plan, limit):
        """Rate limits are correct for each plan"""
        service = ConversationDomainService()
        
        actual_limit = service.get_rate_limit_for_plan(plan)
        assert actual_limit == limit


class TestCanResolve:
    """Tests for conversation resolution rules"""
    
    def test_valid_conversation_can_resolve(self, active_conversation_with_messages):
        """Active conversation with messages can be resolved"""
        service = ConversationDomainService()
        
        result = service.can_resolve(active_conversation_with_messages)
        
        assert result.is_success
    
    def test_resolved_conversation_cannot_resolve(self, resolved_conversation):
        """Already resolved conversation cannot be resolved"""
        service = ConversationDomainService()
        
        result = service.can_resolve(resolved_conversation)
        
        assert result.is_failure
        assert result.error.code == "BUSINESS_RULE_VIOLATION"
    
    def test_conversation_without_agent_cannot_resolve(self, conversation_without_agent):
        """Conversation without agent cannot be resolved"""
        service = ConversationDomainService()
        
        result = service.can_resolve(conversation_without_agent)
        
        assert result.is_failure


class TestCanEscalate:
    """Tests for conversation escalation rules"""
    
    def test_active_conversation_can_escalate(self, active_conversation_with_messages):
        """Active conversation can be escalated"""
        service = ConversationDomainService()
        
        result = service.can_escalate(active_conversation_with_messages)
        
        assert result.is_success
    
    def test_escalated_conversation_cannot_escalate(self, escalated_conversation):
        """Already escalated conversation cannot be escalated"""
        service = ConversationDomainService()
        
        result = service.can_escalate(escalated_conversation)
        
        assert result.is_failure


class TestCanReopen:
    """Tests for conversation reopen rules"""
    
    def test_resolved_conversation_can_reopen(self, resolved_conversation):
        """Resolved conversation can be reopened"""
        service = ConversationDomainService()
        
        result = service.can_reopen(resolved_conversation)
        
        assert result.is_success
    
    def test_active_conversation_cannot_reopen(self, active_conversation_with_messages):
        """Active conversation cannot be reopened"""
        service = ConversationDomainService()
        
        result = service.can_reopen(active_conversation_with_messages)
        
        assert result.is_failure


class TestCalculateResolutionTime:
    """Tests for resolution time calculation"""
    
    def test_resolution_time_calculation(self):
        """Resolution time calculated correctly"""
        service = ConversationDomainService()
        
        started = datetime(2025, 1, 1, 10, 0, 0)
        ended = datetime(2025, 1, 1, 10, 5, 30)  # 5 min 30 sec later
        
        result = service.calculate_resolution_time(started, ended)
        
        assert result == 330  # 5 * 60 + 30
    
    def test_resolution_time_with_default_end(self):
        """Resolution time uses current time if end not provided"""
        service = ConversationDomainService()
        
        started = datetime.now(UTC) - timedelta(minutes=5)
        
        result = service.calculate_resolution_time(started)
        
        # Should be approximately 5 minutes (300 seconds)
        assert 295 <= result <= 305
    
    def test_resolution_time_zero(self):
        """Resolution time can be zero"""
        service = ConversationDomainService()
        
        time = datetime.now(UTC)
        result = service.calculate_resolution_time(time, time)
        
        assert result == 0


class TestDetermineEscalationPriority:
    """Tests for escalation priority calculation"""
    
    def test_enterprise_critical_urgency_negative_sentiment_high_value(self):
        """Highest priority: enterprise + critical + negative + high value"""
        service = ConversationDomainService()
        
        priority = service.determine_escalation_priority(
            customer_plan="enterprise",
            urgency="critical",
            sentiment_avg=-0.8,
            annual_value=50000
        )
        
        assert priority == "critical"
    
    def test_free_low_urgency_positive_sentiment_low_value(self):
        """Lowest priority: free + low + positive + low value"""
        service = ConversationDomainService()
        
        priority = service.determine_escalation_priority(
            customer_plan="free",
            urgency="low",
            sentiment_avg=0.8,
            annual_value=0
        )
        
        assert priority == "low"
    
    def test_premium_high_urgency(self):
        """Premium + high urgency = high priority"""
        service = ConversationDomainService()
        
        priority = service.determine_escalation_priority(
            customer_plan="premium",
            urgency="high",
            sentiment_avg=0.0,
            annual_value=5000
        )
        
        assert priority == "high"
    
    def test_negative_sentiment_increases_priority(self):
        """Negative sentiment adds to priority score"""
        service = ConversationDomainService()
        
        # Same setup but different sentiment
        priority_positive = service.determine_escalation_priority(
            customer_plan="basic",
            urgency="medium",
            sentiment_avg=0.5,
            annual_value=1000
        )
        
        priority_negative = service.determine_escalation_priority(
            customer_plan="basic",
            urgency="medium",
            sentiment_avg=-0.8,
            annual_value=1000
        )
        
        # Negative sentiment should increase priority
        priorities = ["low", "medium", "high", "critical"]
        assert priorities.index(priority_negative) >= priorities.index(priority_positive)
    
    def test_high_account_value_increases_priority(self):
        """High account value increases priority"""
        service = ConversationDomainService()
        
        priority_low_value = service.determine_escalation_priority(
            customer_plan="basic",
            urgency="medium",
            sentiment_avg=0.0,
            annual_value=1000
        )
        
        priority_high_value = service.determine_escalation_priority(
            customer_plan="basic",
            urgency="medium",
            sentiment_avg=0.0,
            annual_value=20000
        )
        
        # High value should increase or maintain priority
        priorities = ["low", "medium", "high", "critical"]
        assert priorities.index(priority_high_value) >= priorities.index(priority_low_value)


class TestCalculateCustomerSatisfactionScore:
    """Tests for CSAT calculation"""
    
    def test_perfect_csat_score(self):
        """Perfect metrics result in high CSAT"""
        service = ConversationDomainService()
        
        csat = service.calculate_customer_satisfaction_score(
            sentiment_avg=1.0,         # Perfect sentiment
            resolution_time_seconds=60,  # 1 minute (fast)
            agent_count=1,             # Single agent
            confidence_avg=1.0         # Perfect confidence
        )
        
        assert csat is not None
        assert 4.5 <= csat <= 5.0
    
    def test_poor_csat_score(self):
        """Poor metrics result in low CSAT"""
        service = ConversationDomainService()
        
        csat = service.calculate_customer_satisfaction_score(
            sentiment_avg=-0.8,        # Negative sentiment
            resolution_time_seconds=7200,  # 2 hours (slow)
            agent_count=5,             # Many agent switches
            confidence_avg=0.3         # Low confidence
        )
        
        assert csat is not None
        assert csat < 3.0
    
    def test_csat_requires_sentiment(self):
        """CSAT returns None if no sentiment data"""
        service = ConversationDomainService()
        
        csat = service.calculate_customer_satisfaction_score(
            sentiment_avg=None,
            resolution_time_seconds=300,
            agent_count=1,
            confidence_avg=0.8
        )
        
        assert csat is None
    
    def test_csat_with_missing_optional_fields(self):
        """CSAT calculates with only required fields"""
        service = ConversationDomainService()
        
        csat = service.calculate_customer_satisfaction_score(
            sentiment_avg=0.5,
            resolution_time_seconds=None,
            agent_count=1,
            confidence_avg=None
        )
        
        assert csat is not None
        assert 0.0 <= csat <= 5.0
    
    @pytest.mark.parametrize("resolution_time,expected_min", [
        (200, 4.0),    # < 5 min: score 5
        (600, 3.5),    # < 15 min: score 4
        (1800, 2.5),   # < 1 hour: score 3
        (7200, 1.5),   # > 1 hour: score 2
    ])
    def test_resolution_time_affects_csat(self, resolution_time, expected_min):
        """Resolution time correctly affects CSAT"""
        service = ConversationDomainService()
        
        csat = service.calculate_customer_satisfaction_score(
            sentiment_avg=0.5,
            resolution_time_seconds=resolution_time,
            agent_count=1,
            confidence_avg=0.8
        )
        
        assert csat >= expected_min


class TestEventFactories:
    """Tests for event factory methods"""
    
    def test_create_conversation_resolved_event(self):
        """ConversationResolvedEvent created correctly"""
        service = ConversationDomainService()
        
        conv_id = uuid4()
        cust_id = uuid4()
        
        event = service.create_conversation_resolved_event(
            conversation_id=conv_id,
            customer_id=cust_id,
            resolution_time_seconds=300,
            primary_intent="billing_upgrade",
            agents_involved=["router", "billing"],
            sentiment_avg=0.7
        )
        
        assert event.conversation_id == conv_id
        assert event.customer_id == cust_id
        assert event.resolution_time_seconds == 300
        assert event.primary_intent == "billing_upgrade"
        assert event.agents_involved == ["router", "billing"]
        assert event.sentiment_avg == 0.7
        assert event.event_id is not None
        assert event.occurred_at is not None
    
    def test_create_conversation_escalated_event(self):
        """ConversationEscalatedEvent created correctly"""
        service = ConversationDomainService()
        
        conv_id = uuid4()
        cust_id = uuid4()
        
        event = service.create_conversation_escalated_event(
            conversation_id=conv_id,
            customer_id=cust_id,
            priority="critical",
            reason="Low confidence",
            agents_involved=["router", "technical", "escalation"]
        )
        
        assert event.conversation_id == conv_id
        assert event.customer_id == cust_id
        assert event.priority == "critical"
        assert event.reason == "Low confidence"
        assert len(event.agents_involved) == 3
    
    def test_create_low_confidence_detected_event(self):
        """LowConfidenceDetectedEvent created correctly"""
        service = ConversationDomainService()
        
        conv_id = uuid4()
        cust_id = uuid4()
        msg_id = uuid4()
        
        event = service.create_low_confidence_detected_event(
            conversation_id=conv_id,
            customer_id=cust_id,
            message_id=msg_id,
            confidence=0.3,
            agent_name="technical",
            threshold=0.5
        )
        
        assert event.confidence == 0.3
        assert event.agent_name == "technical"
        assert event.threshold == 0.5
    
    def test_create_negative_sentiment_detected_event(self):
        """NegativeSentimentDetectedEvent created correctly"""
        service = ConversationDomainService()
        
        conv_id = uuid4()
        cust_id = uuid4()
        msg_id = uuid4()
        
        event = service.create_negative_sentiment_detected_event(
            conversation_id=conv_id,
            customer_id=cust_id,
            message_id=msg_id,
            sentiment=-0.7,
            agent_name="billing",
            threshold=-0.5
        )
        
        assert event.sentiment == -0.7
        assert event.agent_name == "billing"
        assert event.threshold == -0.5


class TestValidationMethods:
    """Tests for validation wrapper methods"""
    
    def test_validate_sentiment(self):
        """Sentiment validation works"""
        service = ConversationDomainService()
        
        assert service.validate_sentiment(0.5).is_success
        assert service.validate_sentiment(1.5).is_failure
    
    def test_validate_confidence(self):
        """Confidence validation works"""
        service = ConversationDomainService()
        
        assert service.validate_confidence(0.8).is_success
        assert service.validate_confidence(1.5).is_failure