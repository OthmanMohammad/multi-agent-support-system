"""
Tests for Customer Domain Specifications

These tests verify business rules for customer operations.
"""
import pytest
from services.domain.customer.specifications import (
    CustomerIsActive,
    WithinRateLimit,
    HasValidPlan,
    CanUpgradePlan,
    CanDowngradePlan,
)


class TestCustomerIsActive:
    """Tests for CustomerIsActive specification"""
    
    def test_active_customer_satisfies(self):
        """Active customer (not blocked/suspended) satisfies"""
        customer_data = {
            "blocked": False,
            "suspended": False
        }
        spec = CustomerIsActive()
        
        assert spec.is_satisfied_by(customer_data)
    
    def test_blocked_customer_not_satisfies(self):
        """Blocked customer does not satisfy"""
        customer_data = {
            "blocked": True,
            "suspended": False
        }
        spec = CustomerIsActive()
        
        assert not spec.is_satisfied_by(customer_data)
        reason = spec.reason_not_satisfied(customer_data)
        assert "blocked" in reason.lower()
    
    def test_suspended_customer_not_satisfies(self):
        """Suspended customer does not satisfy"""
        customer_data = {
            "blocked": False,
            "suspended": True
        }
        spec = CustomerIsActive()
        
        assert not spec.is_satisfied_by(customer_data)
        reason = spec.reason_not_satisfied(customer_data)
        assert "suspended" in reason.lower()
    
    def test_blocked_and_suspended_customer_not_satisfies(self):
        """Blocked and suspended customer does not satisfy"""
        customer_data = {
            "blocked": True,
            "suspended": True
        }
        spec = CustomerIsActive()
        
        assert not spec.is_satisfied_by(customer_data)
    
    def test_missing_fields_treated_as_active(self):
        """Missing blocked/suspended fields treated as False"""
        customer_data = {}
        spec = CustomerIsActive()
        
        assert spec.is_satisfied_by(customer_data)


class TestWithinRateLimit:
    """Tests for WithinRateLimit specification"""
    
    def test_within_limit_satisfies(self):
        """Count below limit satisfies"""
        data = {"conversation_count": 5}
        spec = WithinRateLimit(limit=10)
        
        assert spec.is_satisfied_by(data)
    
    def test_at_limit_not_satisfies(self):
        """Count at limit does not satisfy"""
        data = {"conversation_count": 10}
        spec = WithinRateLimit(limit=10)
        
        assert not spec.is_satisfied_by(data)
        reason = spec.reason_not_satisfied(data)
        assert "10/10" in reason
    
    def test_over_limit_not_satisfies(self):
        """Count over limit does not satisfy"""
        data = {"conversation_count": 15}
        spec = WithinRateLimit(limit=10)
        
        assert not spec.is_satisfied_by(data)
        reason = spec.reason_not_satisfied(data)
        assert "exceeded" in reason.lower()
    
    def test_zero_count_satisfies(self):
        """Zero count satisfies"""
        data = {"conversation_count": 0}
        spec = WithinRateLimit(limit=10)
        
        assert spec.is_satisfied_by(data)
    
    def test_missing_count_treated_as_zero(self):
        """Missing count treated as 0"""
        data = {}
        spec = WithinRateLimit(limit=10)
        
        assert spec.is_satisfied_by(data)
    
    @pytest.mark.parametrize("limit,count,expected", [
        (10, 9, True),    # Just under
        (10, 10, False),  # At limit
        (10, 11, False),  # Over limit
        (100, 50, True),  # Well under
        (1, 0, True),     # Zero with limit 1
        (1, 1, False),    # At limit 1
    ])
    def test_various_limits_and_counts(self, limit, count, expected):
        """Various combinations of limits and counts"""
        data = {"conversation_count": count}
        spec = WithinRateLimit(limit=limit)
        
        assert spec.is_satisfied_by(data) == expected


class TestHasValidPlan:
    """Tests for HasValidPlan specification"""
    
    @pytest.mark.parametrize("plan", [
        "free",
        "basic",
        "premium",
        "enterprise",
    ])
    def test_valid_plans_satisfy(self, plan):
        """Valid plan values satisfy"""
        spec = HasValidPlan()
        
        assert spec.is_satisfied_by(plan)
    
    @pytest.mark.parametrize("plan", [
        "invalid",
        "pro",
        "starter",
        "trial",
        "",
    ])
    def test_invalid_plans_not_satisfy(self, plan):
        """Invalid plan values do not satisfy"""
        spec = HasValidPlan()
        
        assert not spec.is_satisfied_by(plan)
        reason = spec.reason_not_satisfied(plan)
        assert "not valid" in reason.lower()
    
    def test_custom_valid_plans(self):
        """Custom valid plans list works"""
        spec = HasValidPlan(valid_plans=["starter", "pro"])
        
        assert spec.is_satisfied_by("starter")
        assert spec.is_satisfied_by("pro")
        assert not spec.is_satisfied_by("free")
        assert not spec.is_satisfied_by("enterprise")


class TestCanUpgradePlan:
    """Tests for CanUpgradePlan specification"""
    
    @pytest.mark.parametrize("current,target,expected", [
        ("free", "basic", True),
        ("free", "premium", True),
        ("free", "enterprise", True),
        ("basic", "premium", True),
        ("basic", "enterprise", True),
        ("premium", "enterprise", True),
        ("basic", "free", False),  # Downgrade, not upgrade
        ("premium", "free", False),
        ("premium", "basic", False),
        ("free", "free", False),  # Same plan
        ("basic", "basic", False),
    ])
    def test_upgrade_transitions(self, current, target, expected):
        """Various upgrade transitions"""
        data = {"current_plan": current}
        spec = CanUpgradePlan(target_plan=target)
        
        assert spec.is_satisfied_by(data) == expected
    
    def test_upgrade_from_free_to_basic(self):
        """Free to basic is valid upgrade"""
        data = {"current_plan": "free"}
        spec = CanUpgradePlan(target_plan="basic")
        
        assert spec.is_satisfied_by(data)
    
    def test_cannot_upgrade_to_same_plan(self):
        """Cannot upgrade to same plan"""
        data = {"current_plan": "premium"}
        spec = CanUpgradePlan(target_plan="premium")
        
        assert not spec.is_satisfied_by(data)
    
    def test_cannot_upgrade_to_lower_plan(self):
        """Cannot upgrade to lower tier plan"""
        data = {"current_plan": "premium"}
        spec = CanUpgradePlan(target_plan="basic")
        
        assert not spec.is_satisfied_by(data)
        reason = spec.reason_not_satisfied(data)
        assert "cannot upgrade from premium to basic" in reason.lower()
    
    def test_enterprise_to_enterprise_fails(self):
        """Enterprise to enterprise (same) fails"""
        data = {"current_plan": "enterprise"}
        spec = CanUpgradePlan(target_plan="enterprise")
        
        assert not spec.is_satisfied_by(data)


class TestCanDowngradePlan:
    """Tests for CanDowngradePlan specification"""
    
    @pytest.mark.parametrize("current,target,expected", [
        ("basic", "free", True),
        ("premium", "free", True),
        ("premium", "basic", True),
        ("enterprise", "free", True),
        ("enterprise", "basic", True),
        ("enterprise", "premium", True),
        ("free", "basic", False),  # Upgrade, not downgrade
        ("free", "premium", False),
        ("basic", "premium", False),
        ("free", "free", False),  # Same plan
        ("premium", "premium", False),
    ])
    def test_downgrade_transitions(self, current, target, expected):
        """Various downgrade transitions"""
        data = {"current_plan": current}
        spec = CanDowngradePlan(target_plan=target)
        
        assert spec.is_satisfied_by(data) == expected
    
    def test_downgrade_from_premium_to_basic(self):
        """Premium to basic is valid downgrade"""
        data = {"current_plan": "premium"}
        spec = CanDowngradePlan(target_plan="basic")
        
        assert spec.is_satisfied_by(data)
    
    def test_cannot_downgrade_to_higher_plan(self):
        """Cannot downgrade to higher tier plan"""
        data = {"current_plan": "basic"}
        spec = CanDowngradePlan(target_plan="premium")
        
        assert not spec.is_satisfied_by(data)
        reason = spec.reason_not_satisfied(data)
        assert "cannot downgrade from basic to premium" in reason.lower()
    
    def test_cannot_downgrade_to_same_plan(self):
        """Cannot downgrade to same plan"""
        data = {"current_plan": "basic"}
        spec = CanDowngradePlan(target_plan="basic")
        
        assert not spec.is_satisfied_by(data)


class TestSpecificationComposition:
    """Tests for specification composition with customer specs"""
    
    def test_active_and_within_limit(self):
        """Customer is active AND within rate limit"""
        data = {
            "blocked": False,
            "suspended": False,
            "conversation_count": 5
        }
        
        spec = CustomerIsActive().and_(WithinRateLimit(limit=10))
        
        assert spec.is_satisfied_by(data)
    
    def test_active_but_over_limit(self):
        """Customer is active but over rate limit"""
        data = {
            "blocked": False,
            "suspended": False,
            "conversation_count": 15
        }
        
        spec = CustomerIsActive().and_(WithinRateLimit(limit=10))
        
        assert not spec.is_satisfied_by(data)
    
    def test_blocked_and_over_limit(self):
        """Customer is blocked and over limit - both fail"""
        data = {
            "blocked": True,
            "suspended": False,
            "conversation_count": 15
        }
        
        spec = CustomerIsActive().and_(WithinRateLimit(limit=10))
        
        assert not spec.is_satisfied_by(data)
        reason = spec.reason_not_satisfied(data)
        # Should mention both failures
        assert "blocked" in reason.lower()
        assert "exceeded" in reason.lower()