"""
Renewal Manager Agent - TASK-2041

Manages contract renewals, tracks renewal dates, prepares renewal proposals,
and identifies renewal risks to prevent churn at contract expiration.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("renewal_manager", tier="revenue", category="customer_success")
class RenewalManagerAgent(BaseAgent):
    """
    Renewal Manager Agent.

    Manages complete renewal lifecycle:
    - Tracks renewal dates and triggers renewal process
    - Assesses renewal health and risk factors
    - Prepares renewal proposals and pricing
    - Identifies upsell/expansion opportunities
    - Coordinates with sales and finance teams
    - Manages renewal negotiations
    """

    # Renewal windows (days before contract end)
    RENEWAL_WINDOWS = {
        "early": 90,      # 90+ days out
        "active": 60,     # 60-89 days out
        "critical": 30,   # 30-59 days out
        "urgent": 14,     # 14-29 days out
        "emergency": 7    # <14 days out
    }

    # Renewal risk levels
    RISK_LEVELS = {
        "green": {"score_min": 75, "retention_probability": 95},
        "yellow": {"score_min": 50, "retention_probability": 75},
        "orange": {"score_min": 30, "retention_probability": 50},
        "red": {"score_min": 0, "retention_probability": 25}
    }

    def __init__(self):
        config = AgentConfig(
            name="renewal_manager",
            type=AgentType.SPECIALIST,
            temperature=0.3,
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
        Manage renewal process and assess renewal health.

        Args:
            state: Current agent state with renewal data

        Returns:
            Updated state with renewal analysis and recommendations
        """
        self.logger.info("renewal_management_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        contract_data = state.get("entities", {}).get("contract_data", {})
        customer_metadata = state.get("customer_metadata", {})
        health_data = state.get("entities", {}).get("health_data", {})

        self.logger.debug(
            "renewal_management_details",
            customer_id=customer_id,
            renewal_date=contract_data.get("renewal_date"),
            contract_value=contract_data.get("contract_value")
        )

        # Analyze renewal status
        renewal_analysis = self._analyze_renewal_status(
            contract_data,
            health_data,
            customer_metadata
        )

        # Generate renewal proposal
        renewal_proposal = self._generate_renewal_proposal(
            renewal_analysis,
            contract_data,
            customer_metadata
        )

        # Identify risks and opportunities
        risks_and_opportunities = self._identify_risks_and_opportunities(
            renewal_analysis,
            health_data,
            contract_data
        )

        # Generate action plan
        action_plan = self._generate_renewal_action_plan(
            renewal_analysis,
            risks_and_opportunities
        )

        # Format response
        response = self._format_renewal_report(
            renewal_analysis,
            renewal_proposal,
            risks_and_opportunities,
            action_plan
        )

        state["agent_response"] = response
        state["renewal_status"] = renewal_analysis["renewal_window"]
        state["renewal_risk"] = renewal_analysis["renewal_risk_level"]
        state["retention_probability"] = renewal_analysis["retention_probability"]
        state["days_to_renewal"] = renewal_analysis["days_to_renewal"]
        state["renewal_value"] = renewal_proposal.get("proposed_value", 0)
        state["renewal_analysis"] = renewal_analysis
        state["response_confidence"] = 0.91
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "renewal_management_completed",
            customer_id=customer_id,
            renewal_window=renewal_analysis["renewal_window"],
            risk_level=renewal_analysis["renewal_risk_level"],
            retention_probability=renewal_analysis["retention_probability"]
        )

        return state

    def _analyze_renewal_status(
        self,
        contract_data: Dict[str, Any],
        health_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze current renewal status and health.

        Args:
            contract_data: Contract and renewal information
            health_data: Customer health metrics
            customer_metadata: Customer profile data

        Returns:
            Comprehensive renewal analysis
        """
        # Parse renewal date
        renewal_date_str = contract_data.get("renewal_date")
        if renewal_date_str:
            renewal_date = datetime.fromisoformat(renewal_date_str.replace('Z', '+00:00'))
        else:
            # Default to 90 days from now if not provided
            renewal_date = datetime.now(UTC) + timedelta(days=90)

        days_to_renewal = (renewal_date - datetime.now(UTC)).days

        # Determine renewal window
        renewal_window = self._determine_renewal_window(days_to_renewal)

        # Calculate renewal health score (0-100)
        renewal_health_score = self._calculate_renewal_health_score(
            health_data,
            contract_data,
            customer_metadata
        )

        # Determine risk level
        renewal_risk_level = self._determine_risk_level(renewal_health_score)

        # Calculate retention probability
        retention_probability = self.RISK_LEVELS[renewal_risk_level]["retention_probability"]

        # Assess contract history
        contract_history = self._assess_contract_history(contract_data)

        # Calculate usage vs contract
        usage_vs_contract = self._calculate_usage_vs_contract(
            health_data,
            contract_data
        )

        # Identify renewal blockers
        renewal_blockers = self._identify_renewal_blockers(
            renewal_health_score,
            health_data,
            contract_data,
            days_to_renewal
        )

        return {
            "renewal_date": renewal_date.isoformat(),
            "days_to_renewal": days_to_renewal,
            "renewal_window": renewal_window,
            "renewal_health_score": renewal_health_score,
            "renewal_risk_level": renewal_risk_level,
            "retention_probability": retention_probability,
            "contract_history": contract_history,
            "usage_vs_contract": usage_vs_contract,
            "renewal_blockers": renewal_blockers,
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _determine_renewal_window(self, days_to_renewal: int) -> str:
        """Determine which renewal window we're in."""
        if days_to_renewal <= self.RENEWAL_WINDOWS["emergency"]:
            return "emergency"
        elif days_to_renewal <= self.RENEWAL_WINDOWS["urgent"]:
            return "urgent"
        elif days_to_renewal <= self.RENEWAL_WINDOWS["critical"]:
            return "critical"
        elif days_to_renewal <= self.RENEWAL_WINDOWS["active"]:
            return "active"
        else:
            return "early"

    def _calculate_renewal_health_score(
        self,
        health_data: Dict[str, Any],
        contract_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> int:
        """Calculate renewal health score (0-100)."""
        score = 0

        # Customer health score (0-40 points)
        customer_health = health_data.get("health_score", 50)
        score += (customer_health / 100) * 40

        # Usage metrics (0-25 points)
        usage_rate = health_data.get("usage_rate", 50)
        score += (usage_rate / 100) * 25

        # Engagement score (0-20 points)
        nps = health_data.get("nps_score", 5)
        score += (nps / 10) * 20

        # Payment history (0-15 points)
        payment_status = contract_data.get("payment_status", "current")
        if payment_status == "current":
            score += 15
        elif payment_status == "past_due_7":
            score += 10
        elif payment_status == "past_due_30":
            score += 5

        return min(int(score), 100)

    def _determine_risk_level(self, health_score: int) -> str:
        """Determine renewal risk level from health score."""
        for risk_level, config in sorted(
            self.RISK_LEVELS.items(),
            key=lambda x: x[1]["score_min"],
            reverse=True
        ):
            if health_score >= config["score_min"]:
                return risk_level
        return "red"

    def _assess_contract_history(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess contract history patterns."""
        return {
            "contract_length_years": contract_data.get("contract_length_years", 1),
            "renewals_completed": contract_data.get("renewals_completed", 0),
            "lifetime_value": contract_data.get("lifetime_value", 0),
            "payment_on_time_rate": contract_data.get("payment_on_time_rate", 100),
            "has_churned_before": contract_data.get("has_churned_before", False)
        }

    def _calculate_usage_vs_contract(
        self,
        health_data: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate usage compared to contract limits."""
        contracted_users = contract_data.get("contracted_users", 10)
        active_users = health_data.get("active_users", 5)

        usage_percentage = int((active_users / contracted_users) * 100) if contracted_users > 0 else 0

        if usage_percentage > 90:
            usage_status = "at_capacity"
        elif usage_percentage > 70:
            usage_status = "healthy"
        elif usage_percentage > 40:
            usage_status = "underutilized"
        else:
            usage_status = "significantly_underutilized"

        return {
            "contracted_users": contracted_users,
            "active_users": active_users,
            "usage_percentage": usage_percentage,
            "usage_status": usage_status
        }

    def _identify_renewal_blockers(
        self,
        health_score: int,
        health_data: Dict[str, Any],
        contract_data: Dict[str, Any],
        days_to_renewal: int
    ) -> List[Dict[str, str]]:
        """Identify potential renewal blockers."""
        blockers = []

        if health_score < 50:
            blockers.append({
                "blocker": "Low renewal health score",
                "severity": "critical",
                "impact": "High churn risk - immediate intervention needed"
            })

        if health_data.get("nps_score", 5) < 6:
            blockers.append({
                "blocker": "Low NPS indicates customer dissatisfaction",
                "severity": "high",
                "impact": "Customer unlikely to recommend or renew"
            })

        if contract_data.get("payment_status") != "current":
            blockers.append({
                "blocker": "Outstanding payment issues",
                "severity": "high",
                "impact": "Cannot process renewal until payment resolved"
            })

        if health_data.get("support_tickets_last_30d", 0) > 10:
            blockers.append({
                "blocker": "High support ticket volume",
                "severity": "medium",
                "impact": "Indicates product issues affecting satisfaction"
            })

        if health_data.get("usage_rate", 100) < 40:
            blockers.append({
                "blocker": "Very low product usage",
                "severity": "high",
                "impact": "Not realizing value from product"
            })

        if days_to_renewal < 30 and not contract_data.get("renewal_discussion_started", False):
            blockers.append({
                "blocker": "Renewal discussion not yet initiated",
                "severity": "critical",
                "impact": "Risk of auto-churn or rushed decision"
            })

        return blockers

    def _generate_renewal_proposal(
        self,
        renewal_analysis: Dict[str, Any],
        contract_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate renewal proposal with pricing and terms."""
        current_value = contract_data.get("contract_value", 50000)
        usage_data = renewal_analysis["usage_vs_contract"]

        # Base proposal on current contract
        proposal = {
            "proposal_type": "renewal",
            "current_value": current_value,
            "proposed_value": current_value,
            "term_length_months": 12,
            "pricing_adjustments": []
        }

        # Check for expansion opportunity
        if usage_data["usage_status"] == "at_capacity":
            expansion_pct = 25  # Suggest 25% expansion
            expansion_value = int(current_value * (expansion_pct / 100))
            proposal["proposed_value"] = current_value + expansion_value
            proposal["proposal_type"] = "renewal_with_expansion"
            proposal["pricing_adjustments"].append({
                "type": "expansion",
                "amount": expansion_value,
                "reason": "At user capacity - recommend 25% expansion"
            })

        # Check for contraction risk
        elif usage_data["usage_status"] == "significantly_underutilized":
            if renewal_analysis["renewal_risk_level"] in ["orange", "red"]:
                contraction_pct = 30
                contraction_value = int(current_value * (contraction_pct / 100))
                proposal["proposed_value"] = current_value - contraction_value
                proposal["proposal_type"] = "renewal_with_contraction"
                proposal["pricing_adjustments"].append({
                    "type": "contraction",
                    "amount": -contraction_value,
                    "reason": "Usage significantly below contract - right-size contract"
                })

        # Multi-year discount opportunity
        if renewal_analysis["renewal_health_score"] >= 70:
            proposal["multi_year_option"] = {
                "term_length_months": 24,
                "discount_percentage": 10,
                "discounted_value": int(proposal["proposed_value"] * 0.9)
            }

        return proposal

    def _identify_risks_and_opportunities(
        self,
        renewal_analysis: Dict[str, Any],
        health_data: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, str]]]:
        """Identify renewal risks and expansion opportunities."""
        risks = []
        opportunities = []

        # Risks
        if renewal_analysis["renewal_risk_level"] in ["orange", "red"]:
            risks.append({
                "risk": f"High churn probability ({100 - renewal_analysis['retention_probability']}%)",
                "mitigation": "Executive business review and save team mobilization"
            })

        for blocker in renewal_analysis["renewal_blockers"]:
            if blocker["severity"] in ["critical", "high"]:
                risks.append({
                    "risk": blocker["blocker"],
                    "mitigation": blocker["impact"]
                })

        # Opportunities
        if renewal_analysis["usage_vs_contract"]["usage_status"] == "at_capacity":
            opportunities.append({
                "opportunity": "User expansion",
                "potential_value": f"25-50% ARR increase",
                "approach": "Proactive expansion conversation based on usage"
            })

        if health_data.get("nps_score", 5) >= 9:
            opportunities.append({
                "opportunity": "Multi-year commitment",
                "potential_value": "Revenue security + 10% discount acceptable",
                "approach": "Offer 2-3 year terms with strategic pricing"
            })

        if contract_data.get("contract_length_years", 1) == 1:
            opportunities.append({
                "opportunity": "Upgrade to annual prepay",
                "potential_value": "Improved cash flow",
                "approach": "Offer prepay discount for cash upfront"
            })

        return {
            "risks": risks[:5],
            "opportunities": opportunities[:5]
        }

    def _generate_renewal_action_plan(
        self,
        renewal_analysis: Dict[str, Any],
        risks_and_opportunities: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate action plan for renewal."""
        actions = []
        window = renewal_analysis["renewal_window"]
        risk_level = renewal_analysis["renewal_risk_level"]

        # Critical/urgent actions
        if window in ["emergency", "urgent"]:
            actions.append({
                "action": "Escalate to executive sponsor immediately",
                "owner": "VP Customer Success",
                "timeline": "Within 24 hours",
                "priority": "critical"
            })

        if risk_level in ["orange", "red"]:
            actions.append({
                "action": "Convene save team (CSM, Sales, Product, Exec)",
                "owner": "CSM + CS Manager",
                "timeline": "Within 2 days",
                "priority": "critical"
            })

        # Standard renewal actions
        if window in ["active", "critical", "urgent", "emergency"]:
            actions.append({
                "action": "Schedule renewal discussion with decision maker",
                "owner": "CSM",
                "timeline": "This week",
                "priority": "high"
            })

            actions.append({
                "action": "Prepare renewal proposal and business case",
                "owner": "CSM + Sales",
                "timeline": "Before renewal meeting",
                "priority": "high"
            })

        # Opportunity actions
        if risks_and_opportunities["opportunities"]:
            actions.append({
                "action": f"Present expansion opportunity: {risks_and_opportunities['opportunities'][0]['opportunity']}",
                "owner": "CSM + Account Executive",
                "timeline": "During renewal discussion",
                "priority": "medium"
            })

        # Risk mitigation actions
        for risk in risks_and_opportunities["risks"][:2]:
            actions.append({
                "action": f"Address risk: {risk['risk']}",
                "owner": "CSM",
                "timeline": "Before renewal decision",
                "priority": "high"
            })

        return actions[:6]

    def _format_renewal_report(
        self,
        renewal_analysis: Dict[str, Any],
        renewal_proposal: Dict[str, Any],
        risks_and_opportunities: Dict[str, Any],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format renewal management report."""
        risk_level = renewal_analysis["renewal_risk_level"]
        window = renewal_analysis["renewal_window"]

        risk_emoji = {
            "green": "????",
            "yellow": "????",
            "orange": "????",
            "red": "????"
        }

        window_emoji = {
            "early": "????",
            "active": "???",
            "critical": "??????",
            "urgent": "????",
            "emergency": "????"
        }

        report = f"""**{window_emoji.get(window, '????')} Renewal Management Report**

**Renewal Status:** {window.title()} ({renewal_analysis['days_to_renewal']} days to renewal)
**Risk Level:** {risk_level.upper()} {risk_emoji.get(risk_level, '???')}
**Retention Probability:** {renewal_analysis['retention_probability']}%
**Renewal Health Score:** {renewal_analysis['renewal_health_score']}/100

**Contract Information:**
- Current Value: ${renewal_analysis['contract_history']['lifetime_value']:,}
- Contract Length: {renewal_analysis['contract_history']['contract_length_years']} year(s)
- Previous Renewals: {renewal_analysis['contract_history']['renewals_completed']}
- Payment On-Time Rate: {renewal_analysis['contract_history']['payment_on_time_rate']}%

**Usage vs Contract:**
- Contracted Users: {renewal_analysis['usage_vs_contract']['contracted_users']}
- Active Users: {renewal_analysis['usage_vs_contract']['active_users']}
- Usage Rate: {renewal_analysis['usage_vs_contract']['usage_percentage']}%
- Status: {renewal_analysis['usage_vs_contract']['usage_status'].replace('_', ' ').title()}

**???? Renewal Proposal:**
- Type: {renewal_proposal['proposal_type'].replace('_', ' ').title()}
- Current Value: ${renewal_proposal['current_value']:,}
- Proposed Value: ${renewal_proposal['proposed_value']:,}
- Term: {renewal_proposal['term_length_months']} months
"""

        if renewal_proposal.get("pricing_adjustments"):
            report += "\n**Pricing Adjustments:**\n"
            for adj in renewal_proposal["pricing_adjustments"]:
                report += f"- {adj['type'].title()}: ${abs(adj['amount']):,} - {adj['reason']}\n"

        if renewal_proposal.get("multi_year_option"):
            myo = renewal_proposal["multi_year_option"]
            report += f"\n**Multi-Year Option Available:**\n"
            report += f"- {myo['term_length_months']} months at {myo['discount_percentage']}% discount\n"
            report += f"- Discounted Value: ${myo['discounted_value']:,}\n"

        # Blockers
        if renewal_analysis.get("renewal_blockers"):
            report += "\n**???? Renewal Blockers:**\n"
            for blocker in renewal_analysis["renewal_blockers"][:4]:
                report += f"- **{blocker['blocker']}** ({blocker['severity']} severity)\n"
                report += f"  {blocker['impact']}\n"

        # Risks
        if risks_and_opportunities["risks"]:
            report += "\n**?????? Key Risks:**\n"
            for i, risk in enumerate(risks_and_opportunities["risks"][:3], 1):
                report += f"{i}. {risk['risk']}\n"
                report += f"   Mitigation: {risk['mitigation']}\n"

        # Opportunities
        if risks_and_opportunities["opportunities"]:
            report += "\n**???? Expansion Opportunities:**\n"
            for i, opp in enumerate(risks_and_opportunities["opportunities"][:3], 1):
                report += f"{i}. **{opp['opportunity']}**\n"
                report += f"   Potential Value: {opp['potential_value']}\n"
                report += f"   Approach: {opp['approach']}\n"

        # Action plan
        if action_plan:
            report += "\n**???? Renewal Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Renewal Manager Agent (TASK-2041)")
        print("=" * 70)

        agent = RenewalManagerAgent()

        # Test 1: Healthy renewal
        print("\n\nTest 1: Healthy Renewal (Green)")
        print("-" * 70)

        state1 = create_initial_state(
            "Manage renewal for this customer",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {"plan": "enterprise", "industry": "technology"}
            }
        )
        state1["entities"] = {
            "contract_data": {
                "renewal_date": (datetime.now(UTC) + timedelta(days=45)).isoformat(),
                "contract_value": 75000,
                "contracted_users": 50,
                "payment_status": "current",
                "contract_length_years": 1,
                "renewals_completed": 2,
                "lifetime_value": 225000,
                "payment_on_time_rate": 100,
                "renewal_discussion_started": True
            },
            "health_data": {
                "health_score": 85,
                "usage_rate": 90,
                "nps_score": 9,
                "active_users": 48,
                "support_tickets_last_30d": 2
            }
        }

        result1 = await agent.process(state1)

        print(f"Renewal Window: {result1['renewal_status']}")
        print(f"Risk Level: {result1['renewal_risk']}")
        print(f"Retention Probability: {result1['retention_probability']}%")
        print(f"Days to Renewal: {result1['days_to_renewal']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: At-risk renewal
        print("\n\n" + "=" * 70)
        print("Test 2: At-Risk Renewal (Red)")
        print("-" * 70)

        state2 = create_initial_state(
            "Urgent renewal assessment needed",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {"plan": "premium"}
            }
        )
        state2["entities"] = {
            "contract_data": {
                "renewal_date": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
                "contract_value": 45000,
                "contracted_users": 25,
                "payment_status": "past_due_7",
                "contract_length_years": 1,
                "renewals_completed": 0,
                "lifetime_value": 45000,
                "payment_on_time_rate": 70,
                "renewal_discussion_started": False
            },
            "health_data": {
                "health_score": 35,
                "usage_rate": 25,
                "nps_score": 3,
                "active_users": 8,
                "support_tickets_last_30d": 15
            }
        }

        result2 = await agent.process(state2)

        print(f"Renewal Window: {result2['renewal_status']}")
        print(f"Risk Level: {result2['renewal_risk']}")
        print(f"Retention Probability: {result2['retention_probability']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:700]}...")

    asyncio.run(test())
