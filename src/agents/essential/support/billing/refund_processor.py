"""
Refund Processor - Handles refund requests according to company policy.

This agent verifies eligibility, calculates refund amounts, and processes
approved refunds via the billing system.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("refund_processor", tier="essential", category="billing")
class RefundProcessor(BaseAgent):
    """
    Refund Processor Agent.

    Handles refund requests according to company policy:
    - Checks 30-day money-back guarantee eligibility
    - Verifies no previous refunds on account
    - Calculates refund amount (full or prorated)
    - Processes refund via Stripe API
    - Confirms refund to customer
    """

    # Policy constants
    MONEY_BACK_GUARANTEE_DAYS = 30
    MAX_REFUNDS_PER_ACCOUNT = 1

    # Refund policy
    REFUND_POLICY = {
        "money_back_guarantee_days": 30,
        "full_refund_conditions": [
            "Within 30 days of purchase",
            "No previous refund on account",
            "Account in good standing"
        ],
        "prorated_refund_conditions": [
            "Annual plan with >30 days remaining",
            "Billing error or service outage"
        ],
        "no_refund_conditions": [
            "Used service for >30 days",
            "Previous refund requested",
            "Terms of service violation"
        ]
    }

    def __init__(self):
        config = AgentConfig(
            name="refund_processor",
            type=AgentType.SPECIALIST,
            temperature=0.1,  # Low temp for strict policy enforcement
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE
            ],
            kb_category="billing",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process refund request.

        Args:
            state: Current state with refund request

        Returns:
            Updated state with refund decision and confirmation
        """
        self.logger.info("refund_processor_processing_started")

        # Update state
        state = self.update_state(state)

        user_message = state.get("current_message", "")
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "refund_processing_details",
            message_preview=user_message[:100],
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"]
        )

        # Check eligibility
        eligibility = self._check_eligibility(customer_metadata, state)

        if eligibility["eligible"]:
            # Calculate refund amount
            refund_amount = self._calculate_refund(customer_metadata, eligibility)

            # Process refund
            result = await self._process_refund(
                customer_metadata,
                refund_amount,
                state
            )

            state["agent_response"] = result["message"]
            state["refund_processed"] = True
            state["refund_amount"] = refund_amount
            state["response_confidence"] = 0.95

            self.logger.info(
                "refund_approved_and_processed",
                customer_id=state.get("customer_id"),
                amount=refund_amount,
                refund_type=eligibility["refund_type"]
            )

        else:
            # Not eligible - explain why
            state["agent_response"] = self._explain_ineligibility(eligibility)
            state["refund_processed"] = False
            state["refund_amount"] = 0
            state["response_confidence"] = 0.95

            self.logger.info(
                "refund_denied",
                customer_id=state.get("customer_id"),
                reasons=[k for k, v in eligibility.items() if k.startswith("within_") or k.startswith("no_") or k.startswith("account_") and not v]
            )

        state["next_agent"] = None
        state["status"] = "resolved"

        return state

    def _check_eligibility(
        self,
        customer_metadata: Dict,
        state: AgentState
    ) -> Dict:
        """
        Check if customer eligible for refund.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with eligibility status and details
        """
        customer_id = state.get("customer_id", "unknown")

        # Get subscription creation date
        subscription_created = customer_metadata.get(
            "subscription_created_at",
            datetime.now().isoformat()
        )

        # Parse date (handle both string and datetime)
        if isinstance(subscription_created, str):
            try:
                created_date = datetime.fromisoformat(subscription_created.replace('Z', '+00:00'))
            except ValueError:
                # Fallback to now if parsing fails
                created_date = datetime.now()
        else:
            created_date = subscription_created

        # Calculate days since purchase
        days_since_purchase = (datetime.now() - created_date.replace(tzinfo=None)).days

        # Check previous refunds
        previous_refunds = customer_metadata.get("previous_refund_count", 0)

        # Check account status
        account_status = customer_metadata.get("account_status", "active")
        account_good_standing = account_status == "active"

        # Determine eligibility
        within_30_days = days_since_purchase <= self.MONEY_BACK_GUARANTEE_DAYS
        no_previous_refunds = previous_refunds < self.MAX_REFUNDS_PER_ACCOUNT

        eligible = within_30_days and no_previous_refunds and account_good_standing

        self.logger.debug(
            "refund_eligibility_check",
            customer_id=customer_id,
            days_since_purchase=days_since_purchase,
            within_30_days=within_30_days,
            previous_refunds=previous_refunds,
            no_previous_refunds=no_previous_refunds,
            account_good_standing=account_good_standing,
            eligible=eligible
        )

        return {
            "eligible": eligible,
            "days_since_purchase": days_since_purchase,
            "within_money_back_period": within_30_days,
            "no_previous_refunds": no_previous_refunds,
            "account_good_standing": account_good_standing,
            "refund_type": "full" if within_30_days else "prorated"
        }

    def _calculate_refund(
        self,
        customer_metadata: Dict,
        eligibility: Dict
    ) -> float:
        """
        Calculate refund amount.

        Args:
            customer_metadata: Customer data
            eligibility: Eligibility details

        Returns:
            Refund amount in dollars
        """
        refund_type = eligibility["refund_type"]
        mrr = customer_metadata.get("mrr", 0)
        billing_cycle = customer_metadata.get("billing_cycle", "monthly")

        if refund_type == "full":
            # Full refund
            if billing_cycle == "annual":
                refund_amount = mrr * 12
            else:
                refund_amount = mrr

            self.logger.debug(
                "refund_calculated_full",
                amount=refund_amount,
                billing_cycle=billing_cycle
            )

        elif refund_type == "prorated":
            # Prorated refund for annual plans
            months_remaining = customer_metadata.get("months_remaining", 0)
            monthly_rate = customer_metadata.get("monthly_rate", mrr)
            refund_amount = monthly_rate * months_remaining

            self.logger.debug(
                "refund_calculated_prorated",
                amount=refund_amount,
                months_remaining=months_remaining,
                monthly_rate=monthly_rate
            )

        else:
            refund_amount = 0
            self.logger.warning(
                "refund_calculation_unknown_type",
                refund_type=refund_type
            )

        return refund_amount

    async def _process_refund(
        self,
        customer_metadata: Dict,
        amount: float,
        state: AgentState
    ) -> Dict:
        """
        Process refund via Stripe API.

        Args:
            customer_metadata: Customer data
            amount: Refund amount
            state: Current state

        Returns:
            Dict with confirmation message
        """
        customer_id = state.get("customer_id", "unknown")
        customer_email = customer_metadata.get("email", "customer@example.com")

        # In production: Call Stripe API
        # stripe.Refund.create(payment_intent=payment_id, amount=amount)

        self.logger.info(
            "refund_processing_initiated",
            customer_id=customer_id,
            amount=amount,
            email=customer_email
        )

        message = f"""Your refund has been processed successfully.

**Refund Details:**
- Amount: ${amount:.2f}
- Method: Original payment method
- Processing time: 5-7 business days

You'll receive an email confirmation at {customer_email} shortly. Your account will be downgraded to the Free plan immediately.

We're sorry to see you go! If you change your mind, you can always upgrade again. Is there anything else I can help you with?"""

        return {"message": message, "amount": amount}

    def _explain_ineligibility(self, eligibility: Dict) -> str:
        """
        Explain why customer not eligible for refund.

        Args:
            eligibility: Eligibility details with reasons

        Returns:
            Explanation message
        """
        reasons = []

        if not eligibility["within_money_back_period"]:
            days = eligibility["days_since_purchase"]
            reasons.append(
                f"Your subscription is {days} days old (our 30-day money-back guarantee has expired)"
            )

        if not eligibility["no_previous_refunds"]:
            reasons.append(
                "You've already received a refund on this account (limit: 1 refund per account)"
            )

        if not eligibility["account_good_standing"]:
            reasons.append(
                "Your account has outstanding issues that need to be resolved first"
            )

        message = f"""I'm sorry, but your account is not eligible for a refund based on our policy.

**Reason(s):**
{chr(10).join(f'- {r}' for r in reasons)}

**Our refund policy:**
- 30-day money-back guarantee (no questions asked)
- One refund per account lifetime
- Account must be in good standing

**Alternative options:**
- Downgrade to a lower-cost plan (keep some features, reduce cost)
- Pause your subscription (available for annual plans)
- Cancel and keep access until period ends (you've already paid for it)

Would you like to explore any of these options instead? I'm here to help find the best solution for you."""

        return message


if __name__ == "__main__":
    # Test refund processor
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING REFUND PROCESSOR")
        print("=" * 60)

        # Test 1: Eligible refund (within 30 days)
        state1 = create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "billing_cycle": "monthly",
                    "subscription_created_at": (datetime.now() - timedelta(days=15)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "active",
                    "email": "test@example.com"
                }
            }
        )

        processor = RefundProcessor()
        result1 = await processor.process(state1)

        print(f"\n{'='*60}")
        print("TEST 1: Eligible Refund (15 days old)")
        print(f"{'='*60}")
        print(f"Refund processed: {result1.get('refund_processed')}")
        print(f"Refund amount: ${result1.get('refund_amount')}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Ineligible refund (past 30 days)
        state2 = create_initial_state(
            "I want a refund",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "subscription_created_at": (datetime.now() - timedelta(days=45)).isoformat(),
                    "previous_refund_count": 0,
                    "account_status": "active"
                }
            }
        )

        result2 = await processor.process(state2)

        print(f"\n{'='*60}")
        print("TEST 2: Ineligible Refund (45 days old)")
        print(f"{'='*60}")
        print(f"Refund processed: {result2.get('refund_processed')}")
        print(f"\nResponse:\n{result2['agent_response']}")

        # Test 3: Previous refund already issued
        state3 = create_initial_state(
            "I need another refund",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "subscription_created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "previous_refund_count": 1,
                    "account_status": "active"
                }
            }
        )

        result3 = await processor.process(state3)

        print(f"\n{'='*60}")
        print("TEST 3: Previous Refund Exists")
        print(f"{'='*60}")
        print(f"Refund processed: {result3.get('refund_processed')}")
        print(f"\nResponse:\n{result3['agent_response'][:200]}...")

    asyncio.run(test())
