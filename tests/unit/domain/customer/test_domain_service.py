"""
Tests for Customer Domain Service

These tests verify pure business logic with NO database operations.
All data is passed as parameters - no mocking needed.
"""
import pytest
from uuid import uuid4

from services.domain.customer.domain_service import CustomerDomainService


class TestValidateEmail:
    """Tests for email validation"""
    
    def test_valid_email(self):
        """Valid email passes"""
        service = CustomerDomainService()
        result = service.validate_email("user@example.com")
        
        assert result.is_success
    
    def test_invalid_email_fails(self):
        """Invalid email fails"""
        service = CustomerDomainService()
        result = service.validate_email("invalid")
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"


class TestValidatePlan:
    """Tests for plan validation"""
    
    def test_valid_plan(self):
        """Valid plan passes"""
        service = CustomerDomainService()
        result = service.validate_plan("premium")
        
        assert result.is_success
    
    def test_invalid_plan_fails(self):
        """Invalid plan fails"""
        service = CustomerDomainService()
        result = service.validate_plan("invalid")
        
        assert result.is_failure


class TestCanCreateConversation:
    """Tests for conversation creation permission"""
    
    def test_allowed_within_rate_limit(self):
        """Creation allowed when within rate limit"""
        service = CustomerDomainService()
        
        result = service.can_create_conversation(
            plan="free",
            today_count=5,
            customer_blocked=False
        )
        
        assert result.is_success
    
    def test_blocked_customer_cannot_create(self):
        """Blocked customer cannot create conversation"""
        service = CustomerDomainService()
        
        result = service.can_create_conversation(
            plan="free",
            today_count=0,
            customer_blocked=True
        )
        
        assert result.is_failure
        assert result.error.code == "BUSINESS_RULE_VIOLATION"
        assert "blocked" in result.error.message.lower()
    
    def test_rate_limit_exceeded(self):
        """Cannot create when rate limit exceeded"""
        service = CustomerDomainService()
        
        result = service.can_create_conversation(
            plan="free",
            today_count=10,  # At limit
            customer_blocked=False
        )
        
        assert result.is_failure
        assert "rate limit" in result.error.message.lower()
    
    def test_premium_unlimited_conversations(self):
        """Premium customers have unlimited conversations"""
        service = CustomerDomainService()
        
        result = service.can_create_conversation(
            plan="premium",
            today_count=1000,
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
        """Each plan has correct rate limit"""
        service = CustomerDomainService()
        
        actual_limit = service.get_rate_limit_for_plan(plan)
        
        assert actual_limit == limit


class TestGetRateLimitForPlan:
    """Tests for rate limit lookup"""
    
    def test_free_plan_rate_limit(self):
        """Free plan has limit of 10"""
        service = CustomerDomainService()
        
        limit = service.get_rate_limit_for_plan("free")
        
        assert limit == 10
    
    def test_basic_plan_rate_limit(self):
        """Basic plan has limit of 100"""
        service = CustomerDomainService()
        
        limit = service.get_rate_limit_for_plan("basic")
        
        assert limit == 100
    
    def test_premium_plan_unlimited(self):
        """Premium plan has no limit"""
        service = CustomerDomainService()
        
        limit = service.get_rate_limit_for_plan("premium")
        
        assert limit is None
    
    def test_enterprise_plan_unlimited(self):
        """Enterprise plan has no limit"""
        service = CustomerDomainService()
        
        limit = service.get_rate_limit_for_plan("enterprise")
        
        assert limit is None
    
    def test_unknown_plan_defaults_to_free(self):
        """Unknown plan defaults to free plan limit"""
        service = CustomerDomainService()
        
        limit = service.get_rate_limit_for_plan("unknown")
        
        assert limit == 10


class TestShouldSuggestUpgrade:
    """Tests for upgrade suggestion logic"""
    
    def test_free_with_frequent_rate_limits_suggests_upgrade(
        self,
        usage_pattern_frequent_rate_limits
    ):
        """Free users hitting rate limits should see upgrade suggestion"""
        service = CustomerDomainService()
        
        should_suggest = service.should_suggest_upgrade(
            plan="free",
            usage_pattern=usage_pattern_frequent_rate_limits
        )
        
        assert should_suggest is True
    
    def test_free_without_rate_limits_no_suggestion(self):
        """Free users not hitting limits don't see suggestion"""
        service = CustomerDomainService()
        
        usage_pattern = {"rate_limit_hits_this_month": 1}
        should_suggest = service.should_suggest_upgrade(
            plan="free",
            usage_pattern=usage_pattern
        )
        
        assert should_suggest is False
    
    def test_basic_using_advanced_features_suggests_upgrade(
        self,
        usage_pattern_advanced_features
    ):
        """Basic users using many advanced features see suggestion"""
        service = CustomerDomainService()
        
        should_suggest = service.should_suggest_upgrade(
            plan="basic",
            usage_pattern=usage_pattern_advanced_features
        )
        
        assert should_suggest is True
    
    def test_premium_with_large_team_suggests_enterprise(
        self,
        usage_pattern_large_team
    ):
        """Premium users with large teams see enterprise suggestion"""
        service = CustomerDomainService()
        
        should_suggest = service.should_suggest_upgrade(
            plan="premium",
            usage_pattern=usage_pattern_large_team
        )
        
        assert should_suggest is True
    
    def test_enterprise_never_suggests_upgrade(self):
        """Enterprise users never see upgrade suggestions"""
        service = CustomerDomainService()
        
        usage_pattern = {
            "rate_limit_hits_this_month": 100,
            "advanced_features_used": 100,
            "team_size": 1000
        }
        
        should_suggest = service.should_suggest_upgrade(
            plan="enterprise",
            usage_pattern=usage_pattern
        )
        
        assert should_suggest is False


class TestCalculatePlanBenefits:
    """Tests for plan benefit calculation"""
    
    def test_free_to_basic_benefits(self):
        """Calculate benefits of upgrading from free to basic"""
        service = CustomerDomainService()
        
        benefits = service.calculate_plan_benefits(
            current_plan="free",
            target_plan="basic"
        )
        
        assert "current" in benefits
        assert "target" in benefits
        assert "gains" in benefits
        
        # Basic has unlimited projects vs free's 3
        assert benefits["target"]["projects"] == float('inf')
        assert benefits["current"]["projects"] == 3
        assert "projects" in benefits["gains"]
    
    def test_basic_to_premium_benefits(self):
        """Calculate benefits of upgrading from basic to premium"""
        service = CustomerDomainService()
        
        benefits = service.calculate_plan_benefits(
            current_plan="basic",
            target_plan="premium"
        )
        
        # Premium gains API access, analytics, priority support
        assert benefits["gains"]["api_access"] is True
        assert benefits["gains"]["advanced_analytics"] is True
        assert benefits["gains"]["priority_support"] is True
    
    def test_free_to_premium_benefits(self):
        """Calculate benefits of upgrading from free to premium"""
        service = CustomerDomainService()
        
        benefits = service.calculate_plan_benefits(
            current_plan="free",
            target_plan="premium"
        )
        
        # Many gains from free to premium
        assert len(benefits["gains"]) >= 5
    
    def test_premium_to_enterprise_benefits(self):
        """Calculate benefits of upgrading from premium to enterprise"""
        service = CustomerDomainService()
        
        benefits = service.calculate_plan_benefits(
            current_plan="premium",
            target_plan="enterprise"
        )
        
        # Enterprise has infinite storage vs premium's 100GB
        assert benefits["gains"]["storage_gb"] == float('inf')
        assert benefits["gains"]["price_per_user"] == "custom"


class TestValidatePlanTransition:
    """Tests for plan transition validation"""
    
    def test_upgrade_transition(self):
        """Valid upgrade transition"""
        service = CustomerDomainService()
        
        result = service.validate_plan_transition(
            current_plan="free",
            new_plan="basic"
        )
        
        assert result.is_success
        assert result.value == "upgrade"
    
    def test_downgrade_transition(self):
        """Valid downgrade transition"""
        service = CustomerDomainService()
        
        result = service.validate_plan_transition(
            current_plan="premium",
            new_plan="basic"
        )
        
        assert result.is_success
        assert result.value == "downgrade"
    
    def test_same_plan_transition_fails(self):
        """Transition to same plan fails"""
        service = CustomerDomainService()
        
        result = service.validate_plan_transition(
            current_plan="basic",
            new_plan="basic"
        )
        
        assert result.is_failure
        assert result.error.code == "BUSINESS_RULE_VIOLATION"
        assert "already on basic" in result.error.message.lower()
    
    def test_invalid_current_plan_fails(self):
        """Invalid current plan fails validation"""
        service = CustomerDomainService()
        
        result = service.validate_plan_transition(
            current_plan="invalid",
            new_plan="basic"
        )
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
    
    def test_invalid_new_plan_fails(self):
        """Invalid new plan fails validation"""
        service = CustomerDomainService()
        
        result = service.validate_plan_transition(
            current_plan="free",
            new_plan="invalid"
        )
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
    
    @pytest.mark.parametrize("current,new,expected_type", [
        ("free", "basic", "upgrade"),
        ("free", "premium", "upgrade"),
        ("basic", "premium", "upgrade"),
        ("premium", "enterprise", "upgrade"),
        ("basic", "free", "downgrade"),
        ("premium", "free", "downgrade"),
        ("premium", "basic", "downgrade"),
        ("enterprise", "premium", "downgrade"),
    ])
    def test_various_transitions(self, current, new, expected_type):
        """Various plan transitions return correct type"""
        service = CustomerDomainService()
        
        result = service.validate_plan_transition(
            current_plan=current,
            new_plan=new
        )
        
        assert result.is_success
        assert result.value == expected_type


class TestCalculateProration:
    """Tests for proration calculation"""
    
    def test_upgrade_proration_simple(self):
        """Calculate proration for upgrade"""
        service = CustomerDomainService()
        
        # Free to basic, 15 days left, 1 user
        proration = service.calculate_proration(
            current_plan="free",
            new_plan="basic",
            days_remaining=15,
            team_size=1
        )
        
        # Free is $0, basic is $10/month
        # Daily rate: $10/30 = $0.33/day
        # 15 days: $0.33 * 15 = ~$5
        assert 4.0 <= proration <= 6.0
    
    def test_downgrade_proration_credit(self):
        """Downgrade gives credit"""
        service = CustomerDomainService()
        
        # Premium to basic, 15 days left, 1 user
        proration = service.calculate_proration(
            current_plan="premium",
            new_plan="basic",
            days_remaining=15,
            team_size=1
        )
        
        # Premium is $25, basic is $10
        # Should be negative (credit)
        assert proration < 0
    
    def test_proration_with_team_size(self):
        """Proration scales with team size"""
        service = CustomerDomainService()
        
        proration_1_user = service.calculate_proration(
            current_plan="free",
            new_plan="basic",
            days_remaining=15,
            team_size=1
        )
        
        proration_5_users = service.calculate_proration(
            current_plan="free",
            new_plan="basic",
            days_remaining=15,
            team_size=5
        )
        
        # 5 users should be ~5x the cost
        assert abs(proration_5_users - proration_1_user * 5) < 0.5
    
    def test_proration_at_end_of_cycle(self):
        """Proration with 0 days remaining"""
        service = CustomerDomainService()
        
        proration = service.calculate_proration(
            current_plan="free",
            new_plan="basic",
            days_remaining=0,
            team_size=1
        )
        
        assert proration == 0.0
    
    def test_proration_full_cycle(self):
        """Proration with full 30 days"""
        service = CustomerDomainService()
        
        proration = service.calculate_proration(
            current_plan="free",
            new_plan="basic",
            days_remaining=30,
            team_size=1
        )
        
        # Should be approximately the monthly price
        # Basic is $10/month for 1 user
        assert 9.0 <= proration <= 11.0
    
    def test_proration_is_rounded(self):
        """Proration is rounded to 2 decimal places"""
        service = CustomerDomainService()
        
        proration = service.calculate_proration(
            current_plan="free",
            new_plan="basic",
            days_remaining=7,
            team_size=1
        )
        
        # Check it has at most 2 decimal places
        assert proration == round(proration, 2)


class TestEventFactories:
    """Tests for event factory methods"""
    
    def test_create_plan_upgraded_event(self):
        """CustomerPlanUpgradedEvent created correctly"""
        service = CustomerDomainService()
        
        cust_id = uuid4()
        
        event = service.create_plan_upgraded_event(
            customer_id=cust_id,
            email="user@example.com",
            old_plan="free",
            new_plan="premium",
            annual_value_change=300.0
        )
        
        assert event.customer_id == cust_id
        assert event.email == "user@example.com"
        assert event.old_plan == "free"
        assert event.new_plan == "premium"
        assert event.annual_value_change == 300.0
        assert event.event_id is not None
        assert event.occurred_at is not None
    
    def test_create_plan_downgraded_event(self):
        """CustomerPlanDowngradedEvent created correctly"""
        service = CustomerDomainService()
        
        cust_id = uuid4()
        
        event = service.create_plan_downgraded_event(
            customer_id=cust_id,
            email="user@example.com",
            old_plan="premium",
            new_plan="basic",
            annual_value_change=-180.0
        )
        
        assert event.customer_id == cust_id
        assert event.old_plan == "premium"
        assert event.new_plan == "basic"
        assert event.annual_value_change == -180.0
    
    def test_create_rate_limit_exceeded_event(self):
        """RateLimitExceededEvent created correctly"""
        service = CustomerDomainService()
        
        cust_id = uuid4()
        
        event = service.create_rate_limit_exceeded_event(
            customer_id=cust_id,
            email="user@example.com",
            plan="free",
            limit=10,
            current_count=10
        )
        
        assert event.customer_id == cust_id
        assert event.plan == "free"
        assert event.limit == 10
        assert event.current_count == 10