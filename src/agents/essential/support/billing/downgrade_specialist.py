"""
Subscription Downgrade Specialist - Handles plan downgrades with retention focus.

This agent attempts to retain customers before processing downgrades by offering
discounts, alternative plans, or feature education.
"""

from datetime import datetime, timedelta

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("downgrade_specialist", tier="essential", category="billing")
class SubscriptionDowngradeSpecialist(BaseAgent):
    """
    Subscription Downgrade Specialist Agent.

    Handles downgrades with a strong retention focus:
    - Understands customer's reason for downgrade
    - Attempts retention tactics (discounts, alternatives, education)
    - Explains what features/limits they'll lose
    - Processes downgrade only if retention fails
    - Tracks retention success rate
    """

    # Retention tactics priority order
    RETENTION_TACTICS = [
        "discount_20_percent_6_months",
        "discount_10_percent_annual",
        "remove_unused_seats",
        "annual_plan_discount",
        "feature_education",
    ]

    # Discount limits (without escalation)
    MAX_DISCOUNT_PERCENT = 20
    MAX_DISCOUNT_MONTHS = 6

    # Plan feature mapping
    PLAN_FEATURES = {
        "premium": [
            "Advanced reporting & analytics",
            "API access",
            "Priority support",
            "Custom integrations",
            "Unlimited projects",
            "Advanced security features",
        ],
        "basic": ["Basic reporting", "Email support", "Standard integrations", "Up to 10 projects"],
        "free": ["Limited features", "Community support", "1 project"],
    }

    def __init__(self):
        config = AgentConfig(
            name="downgrade_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="billing",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process downgrade request with retention tactics.

        Args:
            state: AgentState with downgrade request

        Returns:
            Updated state with retention offer or downgrade confirmation
        """
        self.logger.info("downgrade_specialist_processing_started")

        # Update state
        state = self.update_state(state)

        user_message = state.get("current_message", "")
        customer_metadata = state.get("customer_metadata", {})

        # Check if this is first downgrade request or response to retention offer
        retention_attempt = state.get("retention_attempt", 0)

        self.logger.debug(
            "downgrade_processing_details",
            message_preview=user_message[:100],
            retention_attempt=retention_attempt,
            turn_count=state["turn_count"],
        )

        if retention_attempt == 0:
            # First attempt - try retention
            response = await self._attempt_retention(customer_metadata, state)
            state["retention_attempt"] = 1
            state["retention_offered"] = True
            state["retention_tactic"] = response["tactic"]
            state["agent_response"] = response["message"]
            state["next_agent"] = None  # Wait for user response
            state["status"] = "active"

            self.logger.info(
                "retention_offer_made",
                tactic=response["tactic"],
                customer_id=state.get("customer_id"),
            )

        # User responded to retention offer
        elif self._accepted_retention(user_message):
            # Success! Apply retention tactic
            response = await self._apply_retention(
                customer_metadata, state.get("retention_tactic"), state
            )
            state["retention_successful"] = True
            state["agent_response"] = response["message"]
            state["next_agent"] = None
            state["status"] = "resolved"

            self.logger.info(
                "retention_successful",
                customer_id=state.get("customer_id"),
                tactic=state.get("retention_tactic"),
            )

        else:
            # User declined retention - process downgrade
            response = await self._process_downgrade(customer_metadata, state)
            state["retention_successful"] = False
            state["downgrade_processed"] = True
            state["agent_response"] = response["message"]
            state["next_agent"] = None
            state["status"] = "resolved"

            self.logger.info(
                "retention_failed_downgrade_processed", customer_id=state.get("customer_id")
            )

        state["response_confidence"] = 0.9

        return state

    async def _attempt_retention(self, customer_metadata: dict, state: AgentState) -> dict:
        """
        Attempt to retain customer before downgrade.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with retention message and tactic
        """
        current_plan = customer_metadata.get("plan", "premium")
        target_plan = state.get("entities", {}).get("target_plan", "basic")
        mrr = customer_metadata.get("mrr", 250)
        customer_metadata.get("health_score", 50)

        # Extract reason from intent or message analysis
        reason = self._extract_downgrade_reason(state.get("current_message", ""))

        self.logger.debug(
            "retention_analysis",
            current_plan=current_plan,
            target_plan=target_plan,
            reason=reason,
            mrr=mrr,
        )

        # Choose retention tactic based on reason
        if reason in ["too_expensive", "budget"]:
            tactic = "discount_20_percent_6_months"
            discount_amount = int(mrr * 0.2)
            new_price = mrr - discount_amount

            message = f"""I understand budget is a concern. Before downgrading from {current_plan.title()} to {target_plan.title()}, I'd like to offer you an alternative.

**Current plan features you'll lose:**
{self._get_lost_features(current_plan, target_plan)}

**Special offer for you:**
I can give you 20% off your {current_plan.title()} plan for the next 6 months.

- Current price: ${mrr}/month
- Discounted price: ${new_price}/month
- You save: ${discount_amount}/month (${discount_amount * 6} total over 6 months)

This way you keep all your {current_plan.title()} features at a more affordable price.

Would this work better for you?"""

        elif reason in ["not_using_features", "too_complex"]:
            tactic = "feature_education"

            message = f"""I see you're considering downgrading from {current_plan.title()} to {target_plan.title()}.

Before you do, I want to make sure you're aware of all the features available to you. Many customers don't realize how much value they can get from:

- Advanced reporting & analytics
- API access for integrations
- Priority support (faster response times)
- Custom workflows

**Would you like me to show you how to get more value from your current plan?**

I can schedule a quick 15-minute call with our customer success team to help you make the most of your {current_plan.title()} subscription.

Alternatively, if budget is a concern, I can also offer you a 20% discount for 6 months."""

        elif reason in ["too_many_seats", "team_size_reduced"]:
            tactic = "remove_unused_seats"
            seats_used = customer_metadata.get("seats_used", 10)
            seats_total = customer_metadata.get("seats_total", 15)
            seat_price = mrr // seats_total if seats_total > 0 else 25

            new_mrr = seat_price * seats_used

            message = f"""I see you're using {seats_used} out of {seats_total} seats on your {current_plan.title()} plan.

**Instead of downgrading, we can reduce your seat count** to match your team size. This will lower your bill while keeping all {current_plan.title()} features.

- Current: {seats_total} seats at ${mrr}/month
- Proposed: {seats_used} seats at ${new_mrr}/month
- You save: ${mrr - new_mrr}/month

Would this work better than downgrading to {target_plan.title()}?"""

        else:
            # Default: offer discount
            tactic = "discount_10_percent_annual"

            message = f"""I understand you want to downgrade from {current_plan.title()} to {target_plan.title()}.

**What you'll lose:**
{self._get_lost_features(current_plan, target_plan)}

**Alternative option:**
If you switch to an annual plan, I can give you 20% off (same as paying for 10 months, getting 2 free). This would make your {current_plan.title()} plan more affordable.

- Monthly plan: ${mrr}/month (${mrr * 12}/year)
- Annual plan: ${int(mrr * 12 * 0.8)}/year (${int(mrr * 0.8)}/month equivalent)
- You save: ${int(mrr * 12 * 0.2)}/year

Would an annual plan at a discount work better for you?"""

        return {"tactic": tactic, "message": message}

    def _extract_downgrade_reason(self, message: str) -> str:
        """
        Extract downgrade reason from user message.

        Args:
            message: User's message

        Returns:
            Reason category
        """
        message_lower = message.lower()

        if any(
            word in message_lower for word in ["expensive", "cost", "price", "afford", "budget"]
        ):
            return "too_expensive"
        elif any(
            word in message_lower for word in ["not using", "don't use", "complex", "confusing"]
        ):
            return "not_using_features"
        elif any(word in message_lower for word in ["seats", "users", "team size", "people"]):
            return "too_many_seats"
        else:
            return "other"

    def _get_lost_features(self, current_plan: str, target_plan: str) -> str:
        """
        Get list of features customer will lose.

        Args:
            current_plan: Current plan name
            target_plan: Target plan name

        Returns:
            Formatted string of lost features
        """
        current_features = set(self.PLAN_FEATURES.get(current_plan.lower(), []))
        target_features = set(self.PLAN_FEATURES.get(target_plan.lower(), []))

        lost_features = current_features - target_features

        if lost_features:
            return "\n".join([f"- {feature}" for feature in lost_features])
        else:
            return "- No features will be lost"

    def _accepted_retention(self, user_message: str) -> bool:
        """
        Determine if user accepted retention offer.

        Args:
            user_message: User's response

        Returns:
            True if accepted
        """
        user_message_lower = user_message.lower()

        acceptance_phrases = [
            "yes",
            "ok",
            "sure",
            "sounds good",
            "i'll take it",
            "that works",
            "agree",
            "accept",
            "deal",
            "perfect",
        ]

        rejection_phrases = [
            "no",
            "still want to downgrade",
            "not interested",
            "i've decided",
            "just downgrade",
            "proceed with downgrade",
            "no thanks",
            "not for me",
        ]

        # Check for rejection first (stronger signal)
        if any(phrase in user_message_lower for phrase in rejection_phrases):
            self.logger.debug("retention_response_rejected", message_preview=user_message[:50])
            return False

        # Check for acceptance
        if any(phrase in user_message_lower for phrase in acceptance_phrases):
            self.logger.debug("retention_response_accepted", message_preview=user_message[:50])
            return True

        # Ambiguous - assume rejection (don't force retention)
        self.logger.debug("retention_response_ambiguous", message_preview=user_message[:50])
        return False

    async def _apply_retention(
        self, customer_metadata: dict, tactic: str, state: AgentState
    ) -> dict:
        """
        Apply retention tactic (update subscription).

        Args:
            customer_metadata: Customer data
            tactic: Which retention tactic to apply
            state: Current state

        Returns:
            Dict with confirmation message
        """
        customer_id = state.get("customer_id", "unknown")
        mrr = customer_metadata.get("mrr", 250)

        # In production, this would call Stripe/billing API
        # For now, log the action

        if tactic == "discount_20_percent_6_months":
            new_price = int(mrr * 0.8)
            message = f"""Great! I've applied a 20% discount to your Premium plan for the next 6 months.

Your new billing:
- Discounted rate: ${new_price}/month (was ${mrr}/month)
- Discount period: 6 months
- After 6 months: Returns to ${mrr}/month (you can cancel anytime)

You'll see this reflected on your next invoice. Is there anything else I can help with?"""

        elif tactic == "remove_unused_seats":
            seats_used = customer_metadata.get("seats_used", 10)
            seats_total = customer_metadata.get("seats_total", 15)
            seat_price = mrr // seats_total if seats_total > 0 else 25
            new_mrr = seat_price * seats_used

            message = f"""Perfect! I've reduced your seat count to match your current usage.

Your updated plan:
- Seats: {seats_used} (was {seats_total})
- Monthly cost: ${new_mrr}/month (was ${mrr}/month)
- You keep all Premium features

The change will take effect immediately. Anything else I can help with?"""

        elif tactic == "feature_education":
            message = """Excellent! I've scheduled a 15-minute onboarding call with our customer success team.

You'll receive a calendar invite shortly. In the meantime, I've sent you links to:
- Advanced reporting guide
- API documentation
- Video tutorials

This will help you get the most value from your Premium plan. Anything else?"""

        elif tactic == "discount_10_percent_annual":
            annual_price = int(mrr * 12 * 0.8)
            message = f"""Great! I've switched you to an annual plan with a 20% discount.

Your updated billing:
- Annual price: ${annual_price}/year (${int(annual_price / 12)}/month equivalent)
- Was: ${mrr * 12}/year
- You save: ${int(mrr * 12 * 0.2)}/year

Your card will be charged ${annual_price} at your next billing date. Is there anything else I can help with?"""

        else:
            message = """Great! I've applied your retention offer. You'll see the changes on your next invoice.

Is there anything else I can help you with?"""

        self.logger.info("retention_tactic_applied", customer_id=customer_id, tactic=tactic)

        return {"message": message}

    async def _process_downgrade(self, customer_metadata: dict, state: AgentState) -> dict:
        """
        Process downgrade after retention failed.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with downgrade confirmation
        """
        current_plan = customer_metadata.get("plan", "premium")
        target_plan = state.get("entities", {}).get("target_plan", "basic")
        customer_id = state.get("customer_id", "unknown")

        # Calculate new pricing
        new_mrr = 50 if target_plan == "basic" else 0

        # Get next billing date
        next_billing = self._get_next_billing_date()

        # In production, call Stripe/billing API to process downgrade

        message = f"""I've processed your downgrade from {current_plan.title()} to {target_plan.title()}.

**Changes:**
- Effective date: Next billing cycle ({next_billing})
- You'll keep {current_plan.title()} features until then
- New rate: ${new_mrr}/month (was ${customer_metadata.get("mrr", 250)}/month)

**What happens next:**
1. You keep current features until {next_billing}
2. On {next_billing}, plan switches to {target_plan.title()}
3. You'll be charged the new rate

You can always upgrade again anytime. Is there anything else I can help with?"""

        self.logger.info(
            "downgrade_processed",
            customer_id=customer_id,
            from_plan=current_plan,
            to_plan=target_plan,
        )

        return {"message": message}

    def _get_next_billing_date(self) -> str:
        """
        Get next billing cycle date.

        Returns:
            Formatted date string
        """
        next_billing = datetime.now() + timedelta(days=30)
        return next_billing.strftime("%B %d, %Y")


if __name__ == "__main__":
    # Test downgrade specialist
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING DOWNGRADE SPECIALIST")
        print("=" * 60)

        # Test 1: Initial downgrade request
        state = create_initial_state(
            "I want to downgrade to basic, it's too expensive",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 250,
                    "seats_used": 10,
                    "seats_total": 15,
                    "health_score": 65,
                }
            },
        )
        state["entities"] = {"target_plan": "basic"}

        specialist = SubscriptionDowngradeSpecialist()
        result = await specialist.process(state)

        print(f"\n{'=' * 60}")
        print("TEST 1: Initial Request")
        print(f"{'=' * 60}")
        print(f"Response:\n{result['agent_response']}")
        print(f"\nRetention offered: {result.get('retention_offered')}")
        print(f"Tactic: {result.get('retention_tactic')}")

        # Test 2: Accept retention
        state2 = result.copy()
        state2["current_message"] = "Yes, that sounds good!"
        state2["turn_count"] = 1

        result2 = await specialist.process(state2)

        print(f"\n{'=' * 60}")
        print("TEST 2: Accept Retention")
        print(f"{'=' * 60}")
        print(f"Response:\n{result2['agent_response']}")
        print(f"\nRetention successful: {result2.get('retention_successful')}")
        print(f"Status: {result2.get('status')}")

    asyncio.run(test())
