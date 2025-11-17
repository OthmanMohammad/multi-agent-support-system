"""
Win-Back Agent - TASK-2042

Attempts to win back churned customers by creating personalized win-back offers,
addressing previous issues, and demonstrating product improvements.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("win_back", tier="revenue", category="customer_success")
class WinBackAgent(BaseAgent):
    """
    Win-Back Agent.

    Orchestrates win-back campaigns for churned customers:
    - Analyzes churn reasons and patterns
    - Creates personalized win-back offers
    - Addresses previous pain points
    - Highlights product improvements since churn
    - Manages win-back campaign timing and touchpoints
    - Tracks win-back success rates
    """

    # Win-back windows (months since churn)
    WINBACK_WINDOWS = {
        "immediate": (0, 1),      # 0-1 months
        "short_term": (1, 3),     # 1-3 months
        "medium_term": (3, 6),    # 3-6 months
        "long_term": (6, 12),     # 6-12 months
        "dormant": (12, 24)       # 12-24 months
    }

    # Win-back success probability by window
    WINBACK_PROBABILITY = {
        "immediate": 45,
        "short_term": 30,
        "medium_term": 20,
        "long_term": 10,
        "dormant": 5
    }

    # Churn reason categories
    CHURN_REASONS = {
        "price": {"win_back_strategy": "pricing_concession", "success_rate": 40},
        "product_fit": {"win_back_strategy": "feature_demonstration", "success_rate": 25},
        "support_issues": {"win_back_strategy": "white_glove_support", "success_rate": 50},
        "competition": {"win_back_strategy": "competitive_advantage", "success_rate": 20},
        "business_change": {"win_back_strategy": "new_use_case", "success_rate": 15},
        "usage_low": {"win_back_strategy": "adoption_support", "success_rate": 35}
    }

    def __init__(self):
        config = AgentConfig(
            name="win_back",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            max_tokens=800,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="customer_success",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Create win-back strategy for churned customer.

        Args:
            state: Current agent state with churn data

        Returns:
            Updated state with win-back analysis and campaign
        """
        self.logger.info("win_back_analysis_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        churn_data = state.get("entities", {}).get("churn_data", {})
        customer_metadata = state.get("customer_metadata", {})
        historical_data = state.get("entities", {}).get("historical_data", {})

        self.logger.debug(
            "win_back_analysis_details",
            customer_id=customer_id,
            churn_date=churn_data.get("churn_date"),
            churn_reason=churn_data.get("churn_reason")
        )

        # Analyze win-back potential
        winback_analysis = self._analyze_winback_potential(
            churn_data,
            customer_metadata,
            historical_data
        )

        # Create win-back offer
        winback_offer = self._create_winback_offer(
            winback_analysis,
            churn_data,
            customer_metadata
        )

        # Generate win-back campaign
        winback_campaign = self._generate_winback_campaign(
            winback_analysis,
            winback_offer
        )

        # Prepare issue resolution plan
        resolution_plan = self._create_issue_resolution_plan(
            churn_data,
            winback_analysis
        )

        # Format response
        response = self._format_winback_report(
            winback_analysis,
            winback_offer,
            winback_campaign,
            resolution_plan
        )

        state["agent_response"] = response
        state["winback_probability"] = winback_analysis["winback_success_probability"]
        state["winback_window"] = winback_analysis["winback_window"]
        state["recommended_offer"] = winback_offer.get("offer_type")
        state["winback_value"] = winback_offer.get("offer_value", 0)
        state["winback_analysis"] = winback_analysis
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "win_back_analysis_completed",
            customer_id=customer_id,
            winback_window=winback_analysis["winback_window"],
            success_probability=winback_analysis["winback_success_probability"],
            offer_type=winback_offer.get("offer_type")
        )

        return state

    def _analyze_winback_potential(
        self,
        churn_data: Dict[str, Any],
        customer_metadata: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze potential for winning back this customer.

        Args:
            churn_data: Churn date and reasons
            customer_metadata: Customer profile
            historical_data: Historical engagement and value data

        Returns:
            Comprehensive win-back analysis
        """
        # Parse churn date
        churn_date_str = churn_data.get("churn_date")
        if churn_date_str:
            churn_date = datetime.fromisoformat(churn_date_str.replace('Z', '+00:00'))
        else:
            churn_date = datetime.now(UTC) - timedelta(days=30)

        months_since_churn = (datetime.now(UTC) - churn_date).days / 30

        # Determine win-back window
        winback_window = self._determine_winback_window(months_since_churn)

        # Get base success probability
        base_probability = self.WINBACK_PROBABILITY[winback_window]

        # Analyze churn reason
        churn_reason = churn_data.get("churn_reason", "unknown")
        churn_category = self._categorize_churn_reason(churn_reason)
        churn_config = self.CHURN_REASONS.get(churn_category, {"win_back_strategy": "general_outreach", "success_rate": 20})

        # Calculate adjusted success probability
        winback_success_probability = self._calculate_winback_probability(
            base_probability,
            churn_config["success_rate"],
            historical_data,
            churn_data
        )

        # Assess customer value
        customer_value_tier = self._assess_customer_value(historical_data)

        # Identify what's changed since churn
        improvements_since_churn = self._identify_improvements_since_churn(
            churn_date,
            churn_reason
        )

        # Determine win-back feasibility
        feasibility = self._assess_winback_feasibility(
            winback_success_probability,
            customer_value_tier,
            churn_reason
        )

        return {
            "churn_date": churn_date.isoformat(),
            "months_since_churn": round(months_since_churn, 1),
            "winback_window": winback_window,
            "churn_reason": churn_reason,
            "churn_category": churn_category,
            "winback_strategy": churn_config["win_back_strategy"],
            "winback_success_probability": winback_success_probability,
            "customer_value_tier": customer_value_tier,
            "improvements_since_churn": improvements_since_churn,
            "winback_feasibility": feasibility,
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _determine_winback_window(self, months_since_churn: float) -> str:
        """Determine which win-back window customer falls into."""
        for window, (min_months, max_months) in self.WINBACK_WINDOWS.items():
            if min_months <= months_since_churn < max_months:
                return window
        return "dormant"

    def _categorize_churn_reason(self, churn_reason: str) -> str:
        """Categorize churn reason into standard categories."""
        reason_lower = churn_reason.lower()

        if any(word in reason_lower for word in ["price", "cost", "expensive", "budget"]):
            return "price"
        elif any(word in reason_lower for word in ["feature", "functionality", "capability", "product"]):
            return "product_fit"
        elif any(word in reason_lower for word in ["support", "service", "help", "response"]):
            return "support_issues"
        elif any(word in reason_lower for word in ["competitor", "alternative", "switched"]):
            return "competition"
        elif any(word in reason_lower for word in ["business", "reorganization", "merger", "acquisition"]):
            return "business_change"
        elif any(word in reason_lower for word in ["usage", "adoption", "inactive", "engagement"]):
            return "usage_low"
        else:
            return "unknown"

    def _calculate_winback_probability(
        self,
        base_probability: int,
        churn_reason_probability: int,
        historical_data: Dict[str, Any],
        churn_data: Dict[str, Any]
    ) -> int:
        """Calculate adjusted win-back success probability."""
        # Average base and churn reason probabilities
        probability = (base_probability + churn_reason_probability) / 2

        # Adjust based on historical value
        lifetime_value = historical_data.get("lifetime_value", 0)
        if lifetime_value > 100000:
            probability += 10  # High value customers worth extra effort
        elif lifetime_value > 50000:
            probability += 5

        # Adjust based on tenure
        customer_tenure_months = historical_data.get("customer_tenure_months", 6)
        if customer_tenure_months > 24:
            probability += 8  # Long-term customers easier to win back
        elif customer_tenure_months > 12:
            probability += 5

        # Adjust based on previous engagement
        if historical_data.get("previous_nps_score", 5) >= 8:
            probability += 10  # Were previously satisfied

        # Reduce if churned due to bad experience
        if churn_data.get("churn_sentiment") == "negative":
            probability -= 15

        return min(max(int(probability), 0), 100)

    def _assess_customer_value(self, historical_data: Dict[str, Any]) -> str:
        """Assess customer value tier."""
        lifetime_value = historical_data.get("lifetime_value", 0)

        if lifetime_value >= 100000:
            return "enterprise"
        elif lifetime_value >= 50000:
            return "strategic"
        elif lifetime_value >= 20000:
            return "mid_market"
        else:
            return "smb"

    def _identify_improvements_since_churn(
        self,
        churn_date: datetime,
        churn_reason: str
    ) -> List[str]:
        """Identify product/service improvements since churn."""
        improvements = []

        # In production, this would query actual product changelog
        # For now, generate relevant improvements based on churn reason
        reason_lower = churn_reason.lower()

        if "feature" in reason_lower or "functionality" in reason_lower:
            improvements.append("Launched 15+ new features including advanced analytics and automation")
            improvements.append("New integrations with Salesforce, HubSpot, and Slack")

        if "support" in reason_lower or "service" in reason_lower:
            improvements.append("24/7 premium support now available")
            improvements.append("Average support response time reduced by 60%")
            improvements.append("Dedicated CSM for all accounts over $25k ARR")

        if "price" in reason_lower or "cost" in reason_lower:
            improvements.append("Flexible pricing tiers introduced")
            improvements.append("Usage-based pricing option available")

        if "usage" in reason_lower or "adoption" in reason_lower:
            improvements.append("Comprehensive onboarding program (avg time-to-value: 30 days)")
            improvements.append("In-app guidance and tutorials")

        # Generic improvements
        if not improvements:
            improvements.append("Product performance improved by 40%")
            improvements.append("Enhanced user interface and experience")

        return improvements[:4]

    def _assess_winback_feasibility(
        self,
        probability: int,
        value_tier: str,
        churn_reason: str
    ) -> str:
        """Assess overall feasibility of win-back effort."""
        # High-value customers always worth pursuing
        if value_tier in ["enterprise", "strategic"]:
            if probability >= 30:
                return "highly_recommended"
            elif probability >= 15:
                return "recommended"
            else:
                return "consider"

        # Mid-tier customers
        elif value_tier == "mid_market":
            if probability >= 40:
                return "highly_recommended"
            elif probability >= 25:
                return "recommended"
            else:
                return "low_priority"

        # Lower-value customers
        else:
            if probability >= 50:
                return "recommended"
            elif probability >= 35:
                return "consider"
            else:
                return "not_recommended"

    def _create_winback_offer(
        self,
        winback_analysis: Dict[str, Any],
        churn_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create personalized win-back offer."""
        churn_category = winback_analysis["churn_category"]
        value_tier = winback_analysis["customer_value_tier"]

        offer = {
            "offer_type": "standard_winback",
            "offer_value": 0,
            "offer_components": []
        }

        # Price-based offers
        if churn_category == "price":
            discount_pct = 25 if value_tier in ["enterprise", "strategic"] else 20
            offer["offer_type"] = "pricing_discount"
            offer["offer_components"].append({
                "component": f"{discount_pct}% discount for first 3 months",
                "value": f"{discount_pct}% savings"
            })

        # Product fit offers
        elif churn_category == "product_fit":
            offer["offer_type"] = "enhanced_onboarding"
            offer["offer_components"].extend([
                {"component": "Dedicated onboarding specialist", "value": "$2,000 value"},
                {"component": "Custom feature demonstration", "value": "Personalized"},
                {"component": "30-day trial of premium features", "value": "Risk-free"}
            ])

        # Support issues offers
        elif churn_category == "support_issues":
            offer["offer_type"] = "white_glove_support"
            offer["offer_components"].extend([
                {"component": "Dedicated CSM assigned", "value": "VIP treatment"},
                {"component": "Priority support (4-hour SLA)", "value": "$5,000/year value"},
                {"component": "Weekly check-in calls for 90 days", "value": "Hands-on"}
            ])

        # Competition offers
        elif churn_category == "competition":
            offer["offer_type"] = "competitive_advantage"
            offer["offer_components"].extend([
                {"component": "Feature comparison and gap analysis", "value": "Comprehensive"},
                {"component": "Price match guarantee", "value": "Best value"},
                {"component": "Free migration assistance", "value": "$3,000 value"}
            ])

        # Generic offers
        else:
            discount_pct = 15
            offer["offer_type"] = "win_back_special"
            offer["offer_components"].extend([
                {"component": f"{discount_pct}% win-back discount", "value": f"{discount_pct}% savings"},
                {"component": "No setup fees", "value": "$500 value"},
                {"component": "Flexible contract terms", "value": "Your choice"}
            ])

        # Add trial period for higher-risk win-backs
        if winback_analysis["winback_success_probability"] < 30:
            offer["offer_components"].append({
                "component": "30-day money-back guarantee",
                "value": "Risk-free"
            })

        return offer

    def _generate_winback_campaign(
        self,
        winback_analysis: Dict[str, Any],
        winback_offer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate win-back campaign plan."""
        window = winback_analysis["winback_window"]
        feasibility = winback_analysis["winback_feasibility"]

        campaign = {
            "campaign_type": "win_back",
            "urgency": "high" if window == "immediate" else "medium" if window == "short_term" else "low",
            "touchpoints": [],
            "timeline": "14 days"
        }

        # Immediate window - aggressive outreach
        if window in ["immediate", "short_term"]:
            campaign["touchpoints"] = [
                {"day": 1, "channel": "email", "message": "Personal note from executive sponsor"},
                {"day": 3, "channel": "phone", "message": "CSM outreach call"},
                {"day": 7, "channel": "email", "message": "Win-back offer presentation"},
                {"day": 10, "channel": "phone", "message": "Follow-up call"},
                {"day": 14, "channel": "email", "message": "Final offer reminder"}
            ]

        # Medium-term window
        elif window == "medium_term":
            campaign["timeline"] = "21 days"
            campaign["touchpoints"] = [
                {"day": 1, "channel": "email", "message": "We miss you - what changed?"},
                {"day": 7, "channel": "email", "message": "Product improvements since you left"},
                {"day": 14, "channel": "phone", "message": "Personal outreach"},
                {"day": 21, "channel": "email", "message": "Special win-back offer"}
            ]

        # Long-term or dormant
        else:
            campaign["timeline"] = "30 days"
            campaign["touchpoints"] = [
                {"day": 1, "channel": "email", "message": "Quarterly product update"},
                {"day": 15, "channel": "email", "message": "Customer success story"},
                {"day": 30, "channel": "email", "message": "Re-engagement offer"}
            ]

        return campaign

    def _create_issue_resolution_plan(
        self,
        churn_data: Dict[str, Any],
        winback_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create plan to address previous issues."""
        resolution_steps = []

        churn_reason = churn_data.get("churn_reason", "")
        churn_category = winback_analysis["churn_category"]

        if churn_category == "support_issues":
            resolution_steps.append({
                "issue": "Previous support experience",
                "resolution": "Assign dedicated CSM with direct contact",
                "commitment": "4-hour response SLA guaranteed"
            })

        if churn_category == "product_fit":
            resolution_steps.append({
                "issue": "Missing features or capabilities",
                "resolution": "Demonstrate new features launched since churn",
                "commitment": "Custom implementation plan for specific needs"
            })

        if churn_category == "price":
            resolution_steps.append({
                "issue": "Pricing concerns",
                "resolution": "Flexible pricing options introduced",
                "commitment": "ROI analysis and value demonstration"
            })

        if churn_category == "usage_low":
            resolution_steps.append({
                "issue": "Low adoption and usage",
                "resolution": "Enhanced onboarding and training program",
                "commitment": "Dedicated adoption specialist for 90 days"
            })

        # Generic resolution
        if not resolution_steps:
            resolution_steps.append({
                "issue": churn_reason,
                "resolution": "Comprehensive review and action plan",
                "commitment": "Executive sponsor engagement"
            })

        return resolution_steps

    def _format_winback_report(
        self,
        winback_analysis: Dict[str, Any],
        winback_offer: Dict[str, Any],
        winback_campaign: Dict[str, Any],
        resolution_plan: List[Dict[str, str]]
    ) -> str:
        """Format win-back report."""
        probability = winback_analysis["winback_success_probability"]
        feasibility = winback_analysis["winback_feasibility"]

        feasibility_emoji = {
            "highly_recommended": "????",
            "recommended": "???",
            "consider": "????",
            "low_priority": "??????",
            "not_recommended": "???"
        }

        report = f"""**???? Win-Back Analysis Report**

**Win-Back Feasibility:** {feasibility.replace('_', ' ').title()} {feasibility_emoji.get(feasibility, '????')}
**Success Probability:** {probability}%
**Window:** {winback_analysis['winback_window'].replace('_', ' ').title()} ({winback_analysis['months_since_churn']} months since churn)
**Customer Value Tier:** {winback_analysis['customer_value_tier'].replace('_', ' ').title()}

**Churn Analysis:**
- Reason: {winback_analysis['churn_reason']}
- Category: {winback_analysis['churn_category'].replace('_', ' ').title()}
- Recommended Strategy: {winback_analysis['winback_strategy'].replace('_', ' ').title()}

**???? Win-Back Offer:**
**Offer Type:** {winback_offer['offer_type'].replace('_', ' ').title()}

**Offer Components:**
"""

        for component in winback_offer["offer_components"]:
            report += f"- {component['component']} ({component['value']})\n"

        # Improvements since churn
        if winback_analysis.get("improvements_since_churn"):
            report += "\n**??? What's Changed Since You Left:**\n"
            for improvement in winback_analysis["improvements_since_churn"]:
                report += f"- {improvement}\n"

        # Issue resolution
        if resolution_plan:
            report += "\n**???? Addressing Previous Issues:**\n"
            for step in resolution_plan:
                report += f"\n**Issue:** {step['issue']}\n"
                report += f"**Resolution:** {step['resolution']}\n"
                report += f"**Commitment:** {step['commitment']}\n"

        # Campaign plan
        report += f"\n**???? Win-Back Campaign Plan:**\n"
        report += f"**Timeline:** {winback_campaign['timeline']}\n"
        report += f"**Urgency:** {winback_campaign['urgency'].title()}\n\n"
        report += "**Campaign Touchpoints:**\n"

        for touchpoint in winback_campaign["touchpoints"][:5]:
            report += f"- Day {touchpoint['day']}: {touchpoint['channel'].title()} - {touchpoint['message']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Win-Back Agent (TASK-2042)")
        print("=" * 70)

        agent = WinBackAgent()

        # Test 1: Recent churn - high value
        print("\n\nTest 1: Recent Churn - High Value Customer")
        print("-" * 70)

        state1 = create_initial_state(
            "Create win-back campaign for churned customer",
            context={
                "customer_id": "cust_churned_123",
                "customer_metadata": {"plan": "enterprise", "industry": "finance"}
            }
        )
        state1["entities"] = {
            "churn_data": {
                "churn_date": (datetime.now(UTC) - timedelta(days=20)).isoformat(),
                "churn_reason": "Pricing too high for current budget constraints",
                "churn_sentiment": "neutral"
            },
            "historical_data": {
                "lifetime_value": 120000,
                "customer_tenure_months": 18,
                "previous_nps_score": 8,
                "average_health_score": 75
            }
        }

        result1 = await agent.process(state1)

        print(f"Win-Back Window: {result1['winback_window']}")
        print(f"Success Probability: {result1['winback_probability']}%")
        print(f"Recommended Offer: {result1['recommended_offer']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Long-term churn - support issues
        print("\n\n" + "=" * 70)
        print("Test 2: Long-Term Churn - Support Issues")
        print("-" * 70)

        state2 = create_initial_state(
            "Assess win-back potential",
            context={
                "customer_id": "cust_churned_456",
                "customer_metadata": {"plan": "premium"}
            }
        )
        state2["entities"] = {
            "churn_data": {
                "churn_date": (datetime.now(UTC) - timedelta(days=210)).isoformat(),
                "churn_reason": "Poor support response times and unresolved technical issues",
                "churn_sentiment": "negative"
            },
            "historical_data": {
                "lifetime_value": 35000,
                "customer_tenure_months": 8,
                "previous_nps_score": 4,
                "average_health_score": 42
            }
        }

        result2 = await agent.process(state2)

        print(f"Win-Back Window: {result2['winback_window']}")
        print(f"Success Probability: {result2['winback_probability']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:650]}...")

    asyncio.run(test())
