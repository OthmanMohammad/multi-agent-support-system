"""
Customer Domain Specifications - Business rules as composable objects
"""

from typing import TYPE_CHECKING
from src.core.specifications import Specification

if TYPE_CHECKING:
    from typing import Dict, Any


class CustomerIsActive(Specification['Dict[str, Any]']):
    """
    Customer is not blocked/suspended
    
    Note: We check metadata dict rather than Customer model
    to keep this pure (no database dependency)
    """
    
    def is_satisfied_by(self, customer_data: 'Dict[str, Any]') -> bool:
        blocked = customer_data.get('blocked', False)
        suspended = customer_data.get('suspended', False)
        return not (blocked or suspended)
    
    def reason_not_satisfied(self, customer_data: 'Dict[str, Any]') -> str:
        if customer_data.get('blocked'):
            return "Customer account is blocked"
        if customer_data.get('suspended'):
            return "Customer account is suspended"
        return "Customer is not active"


class WithinRateLimit(Specification['Dict[str, Any]']):
    """Customer is within rate limit"""
    
    def __init__(self, limit: int):
        self.limit = limit
    
    def is_satisfied_by(self, data: 'Dict[str, Any]') -> bool:
        count = data.get('conversation_count', 0)
        return count < self.limit
    
    def reason_not_satisfied(self, data: 'Dict[str, Any]') -> str:
        count = data.get('conversation_count', 0)
        return f"Rate limit exceeded: {count}/{self.limit} conversations"


class HasValidPlan(Specification['str']):
    """Plan is in allowed list"""
    
    def __init__(self, valid_plans: list[str] = None):
        self.valid_plans = valid_plans or ["free", "basic", "premium", "enterprise"]
    
    def is_satisfied_by(self, plan: str) -> bool:
        return plan in self.valid_plans
    
    def reason_not_satisfied(self, plan: str) -> str:
        return f"Plan '{plan}' is not valid. Must be one of {self.valid_plans}"


class CanUpgradePlan(Specification['Dict[str, Any]']):
    """Can customer upgrade to target plan"""
    
    def __init__(self, target_plan: str):
        self.target_plan = target_plan
        # Plan hierarchy: free < basic < premium < enterprise
        self.plan_hierarchy = {
            "free": 0,
            "basic": 1,
            "premium": 2,
            "enterprise": 3
        }
    
    def is_satisfied_by(self, data: 'Dict[str, Any]') -> bool:
        current_plan = data.get('current_plan', 'free')
        
        current_level = self.plan_hierarchy.get(current_plan, 0)
        target_level = self.plan_hierarchy.get(self.target_plan, 0)
        
        return target_level > current_level
    
    def reason_not_satisfied(self, data: 'Dict[str, Any]') -> str:
        current_plan = data.get('current_plan', 'free')
        return f"Cannot upgrade from {current_plan} to {self.target_plan}"


class CanDowngradePlan(Specification['Dict[str, Any]']):
    """Can customer downgrade to target plan"""
    
    def __init__(self, target_plan: str):
        self.target_plan = target_plan
        self.plan_hierarchy = {
            "free": 0,
            "basic": 1,
            "premium": 2,
            "enterprise": 3
        }
    
    def is_satisfied_by(self, data: 'Dict[str, Any]') -> bool:
        current_plan = data.get('current_plan', 'free')
        
        current_level = self.plan_hierarchy.get(current_plan, 0)
        target_level = self.plan_hierarchy.get(self.target_plan, 0)
        
        return target_level < current_level
    
    def reason_not_satisfied(self, data: 'Dict[str, Any]') -> str:
        current_plan = data.get('current_plan', 'free')
        return f"Cannot downgrade from {current_plan} to {self.target_plan}"