"""
Pricing Explainer - Explains pricing, compares plans, and calculates costs.

This agent helps customers understand pricing tiers, compare plans,
calculate costs for their team size, and understand volume discounts.
"""

from typing import Dict, Any, Optional, List

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("pricing_explainer", tier="essential", category="billing")
class PricingExplainer(BaseAgent):
    """
    Pricing Explainer Agent.

    Handles pricing-related queries:
    - Plan comparisons
    - Cost calculations for team sizes
    - Feature differences between plans
    - Volume discounts
    - Annual vs monthly pricing
    """

    # Plan definitions
    PLANS = {
        "free": {
            "price": 0,
            "seats": 1,
            "seats_description": "1 user",
            "projects": 3,
            "storage": "100MB",
            "features": [
                "Basic project management",
                "Task lists and boards",
                "File attachments (100MB)",
                "Community support",
                "Mobile app access"
            ]
        },
        "basic": {
            "price": 10,
            "seats": 25,
            "seats_description": "Up to 25 users",
            "projects": "unlimited",
            "storage": "10GB",
            "features": [
                "Everything in Free",
                "Unlimited projects",
                "10GB storage per user",
                "Calendar integration",
                "Email support",
                "Standard integrations (Slack, Google Drive)",
                "Basic reporting",
                "Custom fields"
            ]
        },
        "premium": {
            "price": 25,
            "seats": "unlimited",
            "seats_description": "Unlimited users",
            "projects": "unlimited",
            "storage": "100GB",
            "features": [
                "Everything in Basic",
                "100GB storage per user",
                "Advanced analytics & reporting",
                "API access",
                "Priority support (24/7)",
                "Custom integrations",
                "Advanced automation",
                "Time tracking",
                "Gantt charts",
                "Advanced security features",
                "Custom workflows"
            ]
        },
        "enterprise": {
            "price": "custom",
            "seats": "unlimited",
            "seats_description": "Unlimited users",
            "projects": "unlimited",
            "storage": "unlimited",
            "features": [
                "Everything in Premium",
                "Unlimited storage",
                "Dedicated account manager",
                "SLA guarantee (99.9% uptime)",
                "Advanced security & compliance (SOC 2, HIPAA)",
                "Custom contracts",
                "On-premise deployment option",
                "White-label options",
                "Advanced admin controls",
                "Custom training sessions"
            ]
        }
    }

    # Volume discounts
    VOLUME_DISCOUNTS = {
        "10_users": {"min_seats": 10, "discount": 10, "description": "10% off for 10-49 users"},
        "50_users": {"min_seats": 50, "discount": 15, "description": "15% off for 50-99 users"},
        "100_users": {"min_seats": 100, "discount": 20, "description": "20% off for 100+ users"}
    }

    # Annual discount
    ANNUAL_DISCOUNT = 20  # 20% off for annual billing

    def __init__(self):
        config = AgentConfig(
            name="pricing_explainer",
            type=AgentType.SPECIALIST,
            temperature=0.3,
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
        Process pricing inquiry.

        Args:
            state: Current state with pricing query

        Returns:
            Updated state with pricing explanation
        """
        self.logger.info("pricing_explainer_processing_started")

        # Update state
        state = self.update_state(state)

        user_message = state.get("current_message", "")
        customer_metadata = state.get("customer_metadata", {})

        # Determine query type
        query_type = self._determine_query_type(user_message, state)

        self.logger.debug(
            "pricing_query_details",
            message_preview=user_message[:100],
            query_type=query_type,
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"]
        )

        # Generate appropriate response
        if query_type == "compare":
            plans_to_compare = self._extract_plans_to_compare(state)
            response = self._compare_plans(plans_to_compare)
        elif query_type == "calculate":
            response = self._calculate_cost(state, customer_metadata)
        elif query_type == "volume_discount":
            response = self._explain_volume_discount(state)
        elif query_type == "annual_vs_monthly":
            response = self._explain_annual_vs_monthly(state, customer_metadata)
        elif query_type == "features":
            response = self._explain_plan_features(state)
        else:
            # General pricing overview
            response = self._general_pricing_overview()

        state["agent_response"] = response
        state["pricing_query_type"] = query_type
        state["response_confidence"] = 0.95
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "pricing_explanation_completed",
            customer_id=state.get("customer_id"),
            query_type=query_type
        )

        return state

    def _determine_query_type(self, message: str, state: AgentState) -> str:
        """
        Determine pricing query type.

        Args:
            message: User message
            state: Current state

        Returns:
            Query type string
        """
        message_lower = message.lower()

        # Check entities
        entities = state.get("entities", {})
        if "pricing_query_type" in entities:
            return entities["pricing_query_type"]

        # Check message keywords
        if any(word in message_lower for word in ["compare", "difference", "vs", "versus"]):
            return "compare"
        elif any(word in message_lower for word in ["calculate", "cost", "how much", "price for"]):
            return "calculate"
        elif any(word in message_lower for word in ["volume", "bulk", "discount", "many users"]):
            return "volume_discount"
        elif any(word in message_lower for word in ["annual", "yearly", "monthly"]):
            return "annual_vs_monthly"
        elif any(word in message_lower for word in ["features", "what's included", "what do i get"]):
            return "features"
        else:
            return "overview"

    def _extract_plans_to_compare(self, state: AgentState) -> List[str]:
        """
        Extract plans to compare from state.

        Args:
            state: Current state

        Returns:
            List of plan names
        """
        entities = state.get("entities", {})

        if "plans_to_compare" in entities:
            return entities["plans_to_compare"]

        # Default comparison
        current_plan = state.get("customer_metadata", {}).get("plan", "free")

        if current_plan == "free":
            return ["free", "basic"]
        elif current_plan == "basic":
            return ["basic", "premium"]
        else:
            return ["basic", "premium"]

    def _compare_plans(self, plans: List[str]) -> str:
        """
        Compare multiple plans.

        Args:
            plans: List of plan names to compare

        Returns:
            Formatted comparison
        """
        comparison = "**Plan Comparison:**\n\n"

        for plan_name in plans:
            if plan_name not in self.PLANS:
                continue

            plan = self.PLANS[plan_name]
            price_str = f"${plan['price']}/user/month" if plan['price'] != "custom" else "Custom pricing"

            comparison += f"**{plan_name.title()} Plan:** {price_str}\n"
            comparison += f"- Users: {plan['seats_description']}\n"
            comparison += f"- Projects: {plan['projects']}\n"
            comparison += f"- Storage: {plan['storage']}\n"
            comparison += f"- Key features:\n"

            for feature in plan['features'][:5]:  # Show first 5 features
                comparison += f"  • {feature}\n"

            comparison += "\n"

        comparison += "\n**Need help deciding?** I can help you choose the right plan based on your team size and needs. Just let me know!"

        return comparison

    def _calculate_cost(self, state: AgentState, customer_metadata: Dict) -> str:
        """
        Calculate cost for specific team size.

        Args:
            state: Current state
            customer_metadata: Customer data

        Returns:
            Cost calculation with breakdown
        """
        entities = state.get("entities", {})

        # Extract parameters
        plan = entities.get("desired_plan", customer_metadata.get("plan", "basic"))
        team_size = entities.get("team_size", 5)
        billing_cycle = entities.get("billing_cycle", "monthly")

        if plan not in self.PLANS:
            plan = "basic"

        plan_info = self.PLANS[plan]

        # Calculate base cost
        if plan_info["price"] == "custom":
            return f"""For {plan.title()} plan with {team_size} users, we'll need to create a custom quote.

**What's included:**
{chr(10).join(f'- {feature}' for feature in plan_info['features'][:8])}

I can connect you with our sales team to discuss pricing and your specific needs.
Would you like me to set up a call?"""

        monthly_per_user = plan_info["price"]
        monthly_total = monthly_per_user * team_size

        # Apply volume discount
        volume_discount = self._get_volume_discount(team_size)
        if volume_discount > 0:
            monthly_total_discounted = monthly_total * (1 - volume_discount / 100)
            volume_savings = monthly_total - monthly_total_discounted
        else:
            monthly_total_discounted = monthly_total
            volume_savings = 0

        if billing_cycle == "annual":
            annual_total = monthly_total_discounted * 12
            annual_discount_amount = annual_total * (self.ANNUAL_DISCOUNT / 100)
            annual_total_final = annual_total - annual_discount_amount
            monthly_equivalent = annual_total_final / 12

            response = f"""**Cost Calculation for {plan.title()} Plan:**

**Team size:** {team_size} users
**Billing cycle:** Annual

**Monthly calculation:**
- Base: ${monthly_per_user}/user × {team_size} users = ${monthly_total:.2f}/month
"""
            if volume_savings > 0:
                response += f"- Volume discount ({volume_discount}%): -${volume_savings:.2f}/month\n"
                response += f"- Subtotal: ${monthly_total_discounted:.2f}/month\n"

            response += f"""
**Annual pricing:**
- Annual subtotal: ${annual_total:.2f}/year
- Annual discount (20%): -${annual_discount_amount:.2f}/year
- **Total: ${annual_total_final:.2f}/year (${monthly_equivalent:.2f}/month equivalent)**

**You save:** ${(monthly_total * 12) - annual_total_final:.2f}/year by paying annually!

Would you like to proceed with the {plan.title()} plan?"""

        else:  # Monthly
            response = f"""**Cost Calculation for {plan.title()} Plan:**

**Team size:** {team_size} users
**Billing cycle:** Monthly

**Breakdown:**
- Base: ${monthly_per_user}/user × {team_size} users = ${monthly_total:.2f}/month
"""
            if volume_savings > 0:
                response += f"- Volume discount ({volume_discount}%): -${volume_savings:.2f}/month\n"
                response += f"- **Monthly total: ${monthly_total_discounted:.2f}/month**\n"
            else:
                response += f"- **Monthly total: ${monthly_total:.2f}/month**\n"

            # Show annual savings
            annual_if_switched = monthly_total_discounted * 12 * (1 - self.ANNUAL_DISCOUNT / 100)
            annual_savings = (monthly_total_discounted * 12) - annual_if_switched

            response += f"""
**💡 Pro tip:** Switch to annual billing and save ${annual_savings:.2f}/year (20% off)!
Annual price would be: ${annual_if_switched:.2f}/year (${annual_if_switched/12:.2f}/month equivalent)

Would you like to proceed with the {plan.title()} plan?"""

        return response

    def _get_volume_discount(self, team_size: int) -> int:
        """
        Get volume discount percentage for team size.

        Args:
            team_size: Number of users

        Returns:
            Discount percentage
        """
        if team_size >= 100:
            return 20
        elif team_size >= 50:
            return 15
        elif team_size >= 10:
            return 10
        else:
            return 0

    def _explain_volume_discount(self, state: AgentState) -> str:
        """
        Explain volume discount structure.

        Args:
            state: Current state

        Returns:
            Volume discount explanation
        """
        response = """**Volume Discounts:**

We offer automatic discounts based on your team size:

- **10-49 users:** 10% off
- **50-99 users:** 15% off
- **100+ users:** 20% off

**How it works:**
1. Discounts apply automatically when you add users
2. No special codes or requests needed
3. Applies to both monthly and annual billing
4. Can be combined with annual discount for even more savings!

**Example:**
- 10 users on Basic plan ($10/user):
  - Without discount: $100/month
  - With 10% discount: $90/month
  - **You save: $10/month ($120/year)**

Want me to calculate the exact cost for your team? Just let me know how many users you have!"""

        return response

    def _explain_annual_vs_monthly(self, state: AgentState, customer_metadata: Dict) -> str:
        """
        Explain annual vs monthly billing.

        Args:
            state: Current state
            customer_metadata: Customer data

        Returns:
            Annual vs monthly explanation
        """
        current_plan = customer_metadata.get("plan", "basic")
        current_mrr = customer_metadata.get("mrr", 100)

        annual_price = current_mrr * 12 * (1 - self.ANNUAL_DISCOUNT / 100)
        monthly_price_annual = current_mrr * 12
        annual_savings = monthly_price_annual - annual_price

        response = f"""**Annual vs Monthly Billing:**

**Monthly billing:**
- Pay month-to-month
- Cancel anytime
- Price: ${current_mrr}/month (${monthly_price_annual}/year)

**Annual billing:**
- Pay once per year
- **20% discount (same as 2 months free!)**
- Price: ${annual_price:.2f}/year (${annual_price/12:.2f}/month equivalent)
- **You save: ${annual_savings:.2f}/year**

**Current plan ({current_plan.title()}):**
- Monthly: ${current_mrr}/month × 12 = ${monthly_price_annual}/year
- Annual: ${annual_price:.2f}/year
- **Annual saves you: ${annual_savings:.2f}**

**Benefits of annual billing:**
✓ 20% cost savings
✓ Budget certainty for the year
✓ No monthly billing notifications
✓ Same cancellation policy (prorated refund if needed)

Would you like to switch to annual billing and start saving?"""

        return response

    def _explain_plan_features(self, state: AgentState) -> str:
        """
        Explain features of a specific plan.

        Args:
            state: Current state

        Returns:
            Feature explanation
        """
        entities = state.get("entities", {})
        plan = entities.get("plan", "basic")

        if plan not in self.PLANS:
            plan = "basic"

        plan_info = self.PLANS[plan]
        price_str = f"${plan_info['price']}/user/month" if plan_info['price'] != "custom" else "Custom pricing"

        response = f"""**{plan.title()} Plan - {price_str}**

**Capacity:**
- Users: {plan_info['seats_description']}
- Projects: {plan_info['projects']}
- Storage: {plan_info['storage']}

**Features:**
"""
        for feature in plan_info['features']:
            response += f"✓ {feature}\n"

        response += f"""
**Best for:**
"""
        if plan == "free":
            response += "- Individuals or very small teams\n- Testing our platform\n- Personal projects"
        elif plan == "basic":
            response += "- Small to medium teams (up to 25 users)\n- Growing businesses\n- Standard project management needs"
        elif plan == "premium":
            response += "- Medium to large teams\n- Advanced analytics needs\n- API integrations required\n- Priority support needed"
        else:  # enterprise
            response += "- Large organizations (100+ users)\n- Enterprise security requirements\n- Custom needs and dedicated support\n- On-premise or white-label options"

        response += "\n\nWant to see how this compares to other plans? Just ask!"

        return response

    def _general_pricing_overview(self) -> str:
        """
        Provide general pricing overview.

        Returns:
            Overview of all plans
        """
        response = """**Pricing Overview:**

We have 4 plans to fit every team size and need:

**Free Plan - $0**
- 1 user, 3 projects, 100MB storage
- Perfect for individuals getting started

**Basic Plan - $10/user/month**
- Up to 25 users, unlimited projects, 10GB storage
- Great for small teams

**Premium Plan - $25/user/month**
- Unlimited users, advanced features, 100GB storage
- Best for growing teams

**Enterprise Plan - Custom pricing**
- Everything unlimited, dedicated support
- Built for large organizations

**Special offers:**
💰 Save 20% with annual billing
💰 Volume discounts (10-20% off for larger teams)

Want me to:
- Compare specific plans?
- Calculate cost for your team?
- Explain features in detail?

Just let me know!"""

        return response


if __name__ == "__main__":
    # Test pricing explainer
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING PRICING EXPLAINER")
        print("=" * 60)

        explainer = PricingExplainer()

        # Test 1: Compare plans
        state1 = create_initial_state(
            "What's the difference between Basic and Premium?",
            context={
                "customer_metadata": {
                    "plan": "free"
                }
            }
        )
        state1["entities"] = {"plans_to_compare": ["basic", "premium"]}

        result1 = await explainer.process(state1)

        print(f"\n{'='*60}")
        print("TEST 1: Compare Plans")
        print(f"{'='*60}")
        print(f"Query type: {result1.get('pricing_query_type')}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Calculate cost
        state2 = create_initial_state(
            "How much for 15 users on Premium plan, paid annually?",
            context={
                "customer_metadata": {
                    "plan": "basic"
                }
            }
        )
        state2["entities"] = {
            "desired_plan": "premium",
            "team_size": 15,
            "billing_cycle": "annual"
        }

        result2 = await explainer.process(state2)

        print(f"\n{'='*60}")
        print("TEST 2: Calculate Cost")
        print(f"{'='*60}")
        print(f"Query type: {result2.get('pricing_query_type')}")
        print(f"\nResponse:\n{result2['agent_response']}")

        # Test 3: Volume discounts
        state3 = create_initial_state(
            "Do you offer volume discounts?",
            context={
                "customer_metadata": {
                    "plan": "basic"
                }
            }
        )

        result3 = await explainer.process(state3)

        print(f"\n{'='*60}")
        print("TEST 3: Volume Discounts")
        print(f"{'='*60}")
        print(f"Query type: {result3.get('pricing_query_type')}")
        print(f"\nResponse:\n{result3['agent_response'][:300]}...")

    asyncio.run(test())
