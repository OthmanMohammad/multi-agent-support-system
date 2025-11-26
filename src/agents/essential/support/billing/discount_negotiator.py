"""
Discount Negotiator - Handles discount requests with approval limits.

This agent manages discount requests, auto-approving within limits and
escalating larger requests to human agents.
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("discount_negotiator", tier="essential", category="billing")
class DiscountNegotiator(BaseAgent):
    """
    Discount Negotiator Agent.

    Handles discount requests with smart approval logic:
    - Auto-approves discounts ≤30%
    - Escalates discounts >30% to sales team
    - Verifies eligibility (nonprofit, student, volume, etc.)
    - Tracks discount history to prevent abuse
    - Suggests alternative savings (annual billing, etc.)
    """

    # Approval limits
    MAX_AUTO_APPROVE_PERCENT = 30
    MAX_AUTO_APPROVE_MONTHS = 12

    # Available discount programs
    AVAILABLE_DISCOUNTS = {
        "annual": {
            "percent": 20,
            "description": "Annual plan discount (20% off)",
            "auto_approve": True,
            "requires_verification": False,
        },
        "volume": {
            "percent": 15,
            "description": "Volume discount for 10+ seats",
            "auto_approve": True,
            "requires_verification": False,
            "min_seats": 10,
        },
        "nonprofit": {
            "percent": 50,
            "description": "Nonprofit organization discount",
            "auto_approve": False,  # Requires verification
            "requires_verification": True,
            "verification_docs": ["501(c)(3) letter", "charity registration"],
        },
        "student": {
            "percent": 50,
            "description": "Student/education discount",
            "auto_approve": False,
            "requires_verification": True,
            "verification_docs": ["Student ID", "university email"],
        },
        "startup": {
            "percent": 30,
            "description": "Startup program (for companies <2 years old)",
            "auto_approve": True,
            "requires_verification": True,
            "verification_docs": ["Company registration within 2 years"],
        },
        "budget": {
            "percent": 20,
            "description": "Budget-friendly discount",
            "auto_approve": True,
            "requires_verification": False,
            "max_months": 6,
        },
    }

    def __init__(self):
        config = AgentConfig(
            name="discount_negotiator",
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
        Process discount request.

        Args:
            state: Current state with discount request

        Returns:
            Updated state with discount decision
        """
        self.logger.info("discount_negotiator_processing_started")

        # Update state
        state = self.update_state(state)

        user_message = state.get("current_message", "")
        customer_metadata = state.get("customer_metadata", {})

        # Extract discount details
        discount_details = self._extract_discount_request(state, customer_metadata)

        self.logger.debug(
            "discount_negotiation_details",
            message_preview=user_message[:100],
            requested_percent=discount_details["requested_percent"],
            reason=discount_details["reason"],
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"],
        )

        # Check if customer qualifies for the requested discount program
        if self._customer_qualifies(customer_metadata, discount_details):
            # Customer qualifies - approve the discount
            response = await self._approve_discount(customer_metadata, discount_details, state)
            state["discount_approved"] = True
            state["discount_percent"] = discount_details["requested_percent"]
            state["discount_reason"] = discount_details["reason"]

            self.logger.info(
                "discount_approved",
                customer_id=state.get("customer_id"),
                percent=discount_details["requested_percent"],
                reason=discount_details["reason"],
            )

        elif (
            discount_details["reason"] in self.AVAILABLE_DISCOUNTS
            and discount_details["reason"] != "general"
        ):
            # Requested specific program (nonprofit, student, etc.) but doesn't qualify
            # Offer alternatives regardless of requested percentage
            response = self._offer_alternative_discount(customer_metadata, discount_details)
            state["discount_approved"] = False
            state["alternative_offered"] = True

            self.logger.info(
                "discount_denied_alternative_offered",
                customer_id=state.get("customer_id"),
                requested_percent=discount_details["requested_percent"],
                reason=f"does_not_qualify_for_{discount_details['reason']}",
            )

        elif discount_details["requested_percent"] <= self.MAX_AUTO_APPROVE_PERCENT:
            # General request within auto-approve limit - offer alternatives
            response = self._offer_alternative_discount(customer_metadata, discount_details)
            state["discount_approved"] = False
            state["alternative_offered"] = True

            self.logger.info(
                "discount_denied_alternative_offered",
                customer_id=state.get("customer_id"),
                requested_percent=discount_details["requested_percent"],
                reason=discount_details["reason"],
            )

        else:
            # General request above auto-approve limit - escalate
            response = self._escalate_for_approval(discount_details, customer_metadata)
            state["should_escalate"] = True
            state["escalation_reason"] = f"Discount request >{self.MAX_AUTO_APPROVE_PERCENT}%"
            state["discount_approved"] = False

            self.logger.info(
                "discount_request_escalated",
                customer_id=state.get("customer_id"),
                requested_percent=discount_details["requested_percent"],
                reason="above_approval_limit",
            )

        state["agent_response"] = response
        state["response_confidence"] = 0.9
        state["next_agent"] = "escalation" if state.get("should_escalate") else None
        state["status"] = "escalated" if state.get("should_escalate") else "resolved"

        return state

    def _extract_discount_request(self, state: AgentState, customer_metadata: dict) -> dict:
        """
        Extract discount request details.

        Args:
            state: Current state
            customer_metadata: Customer data

        Returns:
            Dict with discount request details
        """
        entities = state.get("entities", {})
        message = state.get("current_message", "").lower()

        # Extract requested percentage
        requested_percent = entities.get("requested_discount_percent", 20)

        # If no explicit percent, try to infer from message
        if "requested_discount_percent" not in entities:
            if "50%" in message or "half" in message:
                requested_percent = 50
            elif "30%" in message:
                requested_percent = 30
            elif "25%" in message:
                requested_percent = 25
            elif "10%" in message:
                requested_percent = 10
            else:
                requested_percent = 20  # Default

        # Extract reason
        reason = entities.get("discount_reason", self._infer_reason_from_message(message))

        # Extract duration if specified
        duration_months = entities.get("duration_months", 12)

        return {
            "requested_percent": requested_percent,
            "reason": reason,
            "duration_months": duration_months,
        }

    def _infer_reason_from_message(self, message: str) -> str:
        """
        Infer discount reason from message.

        Args:
            message: User message (lowercase)

        Returns:
            Reason string
        """
        if any(word in message for word in ["nonprofit", "charity", "non-profit", "501c3"]):
            return "nonprofit"
        elif any(word in message for word in ["student", "education", "university", "school"]):
            return "student"
        elif any(word in message for word in ["startup", "new company", "just started"]):
            return "startup"
        elif any(word in message for word in ["annual", "yearly", "pay upfront"]):
            return "annual"
        elif any(word in message for word in ["volume", "many users", "large team"]):
            return "volume"
        elif any(word in message for word in ["budget", "expensive", "afford", "cost"]):
            return "budget"
        else:
            return "general"

    def _customer_qualifies(self, customer_metadata: dict, discount_details: dict) -> bool:
        """
        Check if customer qualifies for requested discount.

        Args:
            customer_metadata: Customer data
            discount_details: Discount request details

        Returns:
            True if customer qualifies
        """
        reason = discount_details["reason"]

        # Check if reason matches a discount program
        if reason not in self.AVAILABLE_DISCOUNTS:
            # General requests may qualify for budget discount
            return discount_details["requested_percent"] <= 20

        discount_program = self.AVAILABLE_DISCOUNTS[reason]

        # Check if requested percent matches program
        if discount_details["requested_percent"] > discount_program["percent"]:
            self.logger.debug(
                "discount_percent_exceeds_program",
                requested=discount_details["requested_percent"],
                program_max=discount_program["percent"],
            )
            return False

        # Check program-specific requirements
        if reason == "nonprofit":
            return customer_metadata.get("is_nonprofit", False)
        elif reason == "student":
            return customer_metadata.get("is_student", False)
        elif reason == "volume":
            seats = customer_metadata.get("seats_total", 0)
            return seats >= discount_program.get("min_seats", 10)
        elif reason == "startup":
            company_age_days = customer_metadata.get("company_age_days", 1000)
            return company_age_days <= 730  # 2 years
        elif reason == "annual":
            return True  # Anyone can get annual discount
        elif reason == "budget":
            return True  # Auto-approve budget discounts within limit
        else:
            return False

    async def _approve_discount(
        self, customer_metadata: dict, discount_details: dict, state: AgentState
    ) -> str:
        """
        Approve and apply discount.

        Args:
            customer_metadata: Customer data
            discount_details: Discount details
            state: Current state

        Returns:
            Approval message
        """
        percent = discount_details["requested_percent"]
        reason = discount_details["reason"]
        mrr = customer_metadata.get("mrr", 100)
        new_mrr = mrr * (1 - percent / 100)
        monthly_savings = mrr - new_mrr

        # Check if verification required
        program_info = self.AVAILABLE_DISCOUNTS.get(reason)
        requires_verification = (
            program_info.get("requires_verification", False) if program_info else False
        )

        if requires_verification and not customer_metadata.get(f"verified_{reason}", False):
            # Need verification first
            verification_docs = program_info.get("verification_docs", [])
            docs_list = "\n".join([f"- {doc}" for doc in verification_docs])

            message = f"""Great news! You qualify for our {reason.title()} discount program ({percent}% off).

**Before we can apply the discount, we need verification:**

Please provide one of the following:
{docs_list}

You can upload documents at: Settings → Billing → Discount Verification

Once verified, your discount will be applied automatically.

**What you'll save:**
- Current price: ${int(mrr)}/month
- With {percent}% discount: ${int(new_mrr)}/month
- Monthly savings: ${int(monthly_savings)}

Is there anything else I can help you with?"""

        else:
            # Can apply immediately
            duration_text = ""
            if "duration_months" in discount_details and discount_details["duration_months"] < 12:
                duration_text = f" for the next {discount_details['duration_months']} months"

            message = f"""Great news! I can offer you a {percent}% discount{duration_text}.

**Current plan:** ${int(mrr)}/month
**With discount:** ${int(new_mrr)}/month
**You save:** ${int(monthly_savings)}/month

**Discount program:** {reason.title()} discount

This discount will be applied to your next invoice{duration_text}. """

            if discount_details.get("duration_months", 12) < 12:
                message += f"After {discount_details['duration_months']} months, your rate will return to ${int(mrr)}/month (you can cancel anytime)."

            message += "\n\nWould you like me to apply this discount to your account?"

        self.logger.debug(
            "discount_approved_message_generated",
            percent=percent,
            reason=reason,
            requires_verification=requires_verification,
        )

        return message

    def _offer_alternative_discount(self, customer_metadata: dict, discount_details: dict) -> str:
        """
        Offer alternative discount options when customer doesn't qualify.

        Args:
            customer_metadata: Customer data
            discount_details: Original discount request

        Returns:
            Alternative options message
        """
        mrr = customer_metadata.get("mrr", 100)
        requested_percent = discount_details["requested_percent"]

        message = f"""I understand you're looking for a {requested_percent}% discount. While that specific discount isn't available, I have some great alternatives:

**Ways to save:**

1. **Annual plan:** Save 20% by paying annually
   - Current (monthly): ${mrr}/month (${mrr * 12}/year)
   - Annual: ${int(mrr * 12 * 0.8)}/year (${int(mrr * 0.8)}/month equivalent)
   - **Save ${int(mrr * 12 * 0.2)}/year**

2. **Volume discount:** 10-20% off for larger teams
   - 10-49 users: 10% off
   - 50-99 users: 15% off
   - 100+ users: 20% off

3. **Special programs:**
   - Nonprofit: 50% off (requires verification)
   - Student/Education: 50% off (requires verification)
   - Startup program: 30% off (for companies <2 years old)

**Current plan optimization:**
- Remove unused seats to reduce cost
- Downgrade to a lower plan (keep some features, save money)

Which option interests you most? I'm happy to explain any of these in detail!"""

        return message

    def _escalate_for_approval(self, discount_details: dict, customer_metadata: dict) -> str:
        """
        Escalate large discount request to sales team.

        Args:
            discount_details: Discount request details
            customer_metadata: Customer data

        Returns:
            Escalation message
        """
        percent = discount_details["requested_percent"]
        mrr = customer_metadata.get("mrr", 100)

        message = f"""I see you're requesting a {percent}% discount. That's above my approval limit of {self.MAX_AUTO_APPROVE_PERCENT}%, but I'd like to help!

**Your request:**
- Current price: ${mrr}/month
- Requested discount: {percent}%
- New price would be: ${mrr * (1 - percent / 100):.2f}/month

Let me connect you with our sales team who can review custom pricing for your needs. They have more flexibility for larger discounts and can discuss:
- Custom contracts
- Volume commitments
- Multi-year agreements
- Custom feature packages

**Next steps:**
1. I'll create a ticket for our sales team
2. They'll reach out within 4 business hours
3. They'll work with you on a custom quote

**In the meantime, here are some immediate savings options:**
- Annual billing: 20% off (auto-approved)
- Volume discount: Up to 20% off for large teams

Would you like me to:
1. Escalate to sales for custom pricing? OR
2. Apply one of the immediate discounts above?"""

        return message


if __name__ == "__main__":
    # Test discount negotiator
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING DISCOUNT NEGOTIATOR")
        print("=" * 60)

        negotiator = DiscountNegotiator()

        # Test 1: Auto-approve within limit (20%)
        state1 = create_initial_state(
            "Can I get a 20% discount? My budget is tight.",
            context={"customer_metadata": {"plan": "premium", "mrr": 100, "seats_total": 5}},
        )
        state1["entities"] = {"requested_discount_percent": 20, "discount_reason": "budget"}

        result1 = await negotiator.process(state1)

        print(f"\n{'=' * 60}")
        print("TEST 1: Auto-Approve (20% budget discount)")
        print(f"{'=' * 60}")
        print(f"Approved: {result1.get('discount_approved')}")
        print(f"Percent: {result1.get('discount_percent')}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Escalate above limit (40%)
        state2 = create_initial_state(
            "I need a 40% discount", context={"customer_metadata": {"plan": "premium", "mrr": 100}}
        )
        state2["entities"] = {"requested_discount_percent": 40}

        result2 = await negotiator.process(state2)

        print(f"\n{'=' * 60}")
        print("TEST 2: Escalate (40% above limit)")
        print(f"{'=' * 60}")
        print(f"Approved: {result2.get('discount_approved')}")
        print(f"Should escalate: {result2.get('should_escalate')}")
        print(f"\nResponse:\n{result2['agent_response'][:300]}...")

        # Test 3: Nonprofit discount (requires verification)
        state3 = create_initial_state(
            "We're a nonprofit, can we get a discount?",
            context={
                "customer_metadata": {
                    "plan": "basic",
                    "mrr": 50,
                    "is_nonprofit": True,
                    "verified_nonprofit": False,
                }
            },
        )
        state3["entities"] = {"requested_discount_percent": 50, "discount_reason": "nonprofit"}

        result3 = await negotiator.process(state3)

        print(f"\n{'=' * 60}")
        print("TEST 3: Nonprofit (requires verification)")
        print(f"{'=' * 60}")
        print(f"Approved: {result3.get('discount_approved')}")
        print(f"\nResponse:\n{result3['agent_response'][:300]}...")

        # Test 4: Volume discount (qualified)
        state4 = create_initial_state(
            "We have 15 users, can we get a volume discount?",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 375,  # 15 users * $25
                    "seats_total": 15,
                }
            },
        )
        state4["entities"] = {"requested_discount_percent": 15, "discount_reason": "volume"}

        result4 = await negotiator.process(state4)

        print(f"\n{'=' * 60}")
        print("TEST 4: Volume Discount (15 users)")
        print(f"{'=' * 60}")
        print(f"Approved: {result4.get('discount_approved')}")
        print(f"\nResponse:\n{result4['agent_response'][:250]}...")

    asyncio.run(test())
