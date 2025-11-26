"""
Customer Domain Service - Pure business logic, NO external dependencies
CRITICAL: This is PURE BUSINESS LOGIC

NO database operations
NO external API calls
NO event publishing (just return event objects)
"""

from typing import Any
from uuid import UUID

from src.core.errors import BusinessRuleError
from src.core.result import Result
from src.services.domain.customer.events import (
    CustomerPlanDowngradedEvent,
    CustomerPlanUpgradedEvent,
    RateLimitExceededEvent,
)
from src.services.domain.customer.validators import CustomerValidators


class CustomerDomainService:
    """
    Domain service for customer business logic

    All methods are PURE - same inputs always produce same outputs.
    """

    def __init__(self):
        """Initialize validators"""
        self.validators = CustomerValidators()

    # ===== Validation Methods =====
    def validate_email(self, email: str) -> Result[None]:
        """Validate email format"""
        return self.validators.validate_email(email)

    def validate_plan(self, plan: str) -> Result[None]:
        """Validate plan is in allowed list"""
        return self.validators.validate_plan(plan)

    # ===== Business Rule Methods =====
    def can_create_conversation(
        self, plan: str, today_count: int, customer_blocked: bool = False
    ) -> Result[None]:
        """
        Check if customer can create a conversation

            Business Rules:
        1. Customer must not be blocked
        2. Customer must be within rate limit for their plan

            Args:
            plan: Customer's plan
            today_count: Number of conversations created today
            customer_blocked: Whether customer is blocked

            Returns:
            Result with None if allowed, error otherwise
        """
        # Rule 1: Not blocked
        if customer_blocked:
            return Result.fail(
                BusinessRuleError(
                    message="Customer account is blocked",
                    rule="customer_not_blocked",
                    entity="Customer",
                )
            )

        # Rule 2: Within rate limit
        rate_limit = self.get_rate_limit_for_plan(plan)

        if rate_limit is not None and today_count >= rate_limit:
            return Result.fail(
                BusinessRuleError(
                    message=f"Rate limit exceeded ({rate_limit} conversations/day for {plan} plan)",
                    rule="within_rate_limit",
                    entity="Customer",
                )
            )

        return Result.ok(None)

    def get_rate_limit_for_plan(self, plan: str) -> int | None:
        """
        Get rate limit for plan (business rule)

            Args:
            plan: Customer plan

            Returns:
            Rate limit or None for unlimited
        """
        return {"free": 10, "basic": 100, "premium": None, "enterprise": None}.get(plan, 10)

    def should_suggest_upgrade(self, plan: str, usage_pattern: dict[str, Any]) -> bool:
        """
        Determine if should suggest upgrade to customer

            Business Logic:
        - Free plan: Suggest if hitting rate limits frequently
        - Basic plan: Suggest if using advanced features
        - Premium: Don't suggest (already top tier for most)

            Args:
            plan: Current plan
            usage_pattern: Dict with usage metrics

            Returns:
            True if should suggest upgrade
        """
        if plan == "enterprise":
            return False  # Already at top tier

        if plan == "free":
            # Suggest if they've hit rate limit 3+ times this month
            rate_limit_hits = usage_pattern.get("rate_limit_hits_this_month", 0)
            return rate_limit_hits >= 3

        if plan == "basic":
            # Suggest if they're using "premium" features
            advanced_features_used = usage_pattern.get("advanced_features_used", 0)
            return advanced_features_used >= 5

        if plan == "premium":
            # Suggest enterprise if they have many team members
            team_size = usage_pattern.get("team_size", 0)
            return team_size >= 50

        return False

    def calculate_plan_benefits(self, current_plan: str, target_plan: str) -> dict[str, Any]:
        """
        Calculate what customer gains by upgrading

        Pure function - just data transformation

            Args:
            current_plan: Current plan
            target_plan: Target plan

            Returns:
            Dict with plan comparison
        """
        plan_features = {
            "free": {
                "projects": 3,
                "team_members": 5,
                "storage_gb": 0.1,
                "api_access": False,
                "advanced_analytics": False,
                "priority_support": False,
                "price_per_user": 0,
            },
            "basic": {
                "projects": float("inf"),
                "team_members": 25,
                "storage_gb": 10,
                "api_access": False,
                "advanced_analytics": False,
                "priority_support": False,
                "price_per_user": 10,
            },
            "premium": {
                "projects": float("inf"),
                "team_members": float("inf"),
                "storage_gb": 100,
                "api_access": True,
                "advanced_analytics": True,
                "priority_support": True,
                "price_per_user": 25,
            },
            "enterprise": {
                "projects": float("inf"),
                "team_members": float("inf"),
                "storage_gb": float("inf"),
                "api_access": True,
                "advanced_analytics": True,
                "priority_support": True,
                "price_per_user": "custom",
            },
        }

        current_features = plan_features.get(current_plan, plan_features["free"])
        target_features = plan_features.get(target_plan, plan_features["free"])

        return {
            "current": current_features,
            "target": target_features,
            "gains": {
                key: target_features[key]
                for key in target_features
                if target_features[key] != current_features.get(key)
            },
        }

    def validate_plan_transition(self, current_plan: str, new_plan: str) -> Result[str]:
        """
        Validate if plan transition is allowed

            Business Rules:
        - Can always upgrade (free -> basic -> premium -> enterprise)
        - Can always downgrade
        - Cannot "transition" to same plan

            Args:
            current_plan: Current plan
            new_plan: Target plan

            Returns:
            Result with transition type ("upgrade"/"downgrade") or error
        """
        # Validate both plans
        for plan in [current_plan, new_plan]:
            result = self.validate_plan(plan)
            if result.is_failure:
                return Result.fail(result.error)

        # Check if same plan
        if current_plan == new_plan:
            return Result.fail(
                BusinessRuleError(
                    message=f"Customer is already on {current_plan} plan",
                    rule="different_plan_required",
                    entity="Customer",
                )
            )

        # Determine transition type
        plan_hierarchy = {"free": 0, "basic": 1, "premium": 2, "enterprise": 3}
        current_level = plan_hierarchy[current_plan]
        new_level = plan_hierarchy[new_plan]

        if new_level > current_level:
            return Result.ok("upgrade")
        else:
            return Result.ok("downgrade")

    def calculate_proration(
        self, current_plan: str, new_plan: str, days_remaining: int, team_size: int = 1
    ) -> float:
        """
        Calculate proration amount for plan change

        Pure function - just math

            Args:
            current_plan: Current plan
            new_plan: New plan
            days_remaining: Days left in billing cycle
            team_size: Number of users

            Returns:
            Proration amount (positive = credit, negative = charge)
        """
        plan_prices = {
            "free": 0,
            "basic": 10,
            "premium": 25,
            "enterprise": 50,  # Simplified
        }

        current_price = plan_prices.get(current_plan, 0)
        new_price = plan_prices.get(new_plan, 0)

        # Calculate daily rates
        daily_current = (current_price * team_size) / 30
        daily_new = (new_price * team_size) / 30

        # Proration
        unused_credit = daily_current * days_remaining
        new_charge = daily_new * days_remaining

        return round(new_charge - unused_credit, 2)

    # ===== Event Factory Methods =====
    def create_plan_upgraded_event(
        self,
        customer_id: UUID,
        email: str,
        old_plan: str,
        new_plan: str,
        annual_value_change: float,
    ) -> CustomerPlanUpgradedEvent:
        """Create a CustomerPlanUpgradedEvent"""
        return CustomerPlanUpgradedEvent(
            customer_id=customer_id,
            email=email,
            old_plan=old_plan,
            new_plan=new_plan,
            annual_value_change=annual_value_change,
        )

    def create_plan_downgraded_event(
        self,
        customer_id: UUID,
        email: str,
        old_plan: str,
        new_plan: str,
        annual_value_change: float,
    ) -> CustomerPlanDowngradedEvent:
        """Create a CustomerPlanDowngradedEvent"""
        return CustomerPlanDowngradedEvent(
            customer_id=customer_id,
            email=email,
            old_plan=old_plan,
            new_plan=new_plan,
            annual_value_change=annual_value_change,
        )

    def create_rate_limit_exceeded_event(
        self, customer_id: UUID, email: str, plan: str, limit: int, current_count: int
    ) -> RateLimitExceededEvent:
        """Create a RateLimitExceededEvent"""
        return RateLimitExceededEvent(
            customer_id=customer_id,
            email=email,
            plan=plan,
            limit=limit,
            current_count=current_count,
        )
