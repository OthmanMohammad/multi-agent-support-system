"""
QBR Scheduler Agent - TASK-2061

Schedules Quarterly Business Reviews, prepares QBR materials, generates insights,
and coordinates attendees to ensure productive strategic alignment meetings.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("qbr_scheduler", tier="revenue", category="customer_success")
class QBRSchedulerAgent(BaseAgent):
    """
    QBR Scheduler Agent.

    Manages Quarterly Business Reviews by:
    - Scheduling QBRs based on customer tier and renewal timing
    - Preparing comprehensive QBR materials and agendas
    - Generating data-driven insights and recommendations
    - Coordinating internal and external attendees
    - Creating follow-up action plans
    - Tracking QBR completion and outcomes
    """

    # QBR scheduling cadence by customer tier
    QBR_CADENCE = {
        "enterprise": {"frequency_days": 90, "duration_minutes": 60, "executive_required": True},
        "premium": {"frequency_days": 90, "duration_minutes": 45, "executive_required": False},
        "growth": {"frequency_days": 180, "duration_minutes": 30, "executive_required": False},
        "standard": {"frequency_days": 365, "duration_minutes": 30, "executive_required": False}
    }

    # QBR preparation timeline
    PREPARATION_TIMELINE = {
        "materials_preparation": 7,  # Days before QBR
        "send_invitation": 14,       # Days before QBR
        "confirm_attendees": 3,      # Days before QBR
        "final_review": 1            # Days before QBR
    }

    # QBR agenda sections
    AGENDA_SECTIONS = [
        "Business Overview & Updates",
        "Product Usage & Adoption Metrics",
        "Success Wins & Value Realized",
        "Challenges & Opportunities",
        "Roadmap & Future Plans",
        "Action Items & Next Steps"
    ]

    def __init__(self):
        config = AgentConfig(
            name="qbr_scheduler",
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
        Schedule and prepare QBR.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with QBR schedule and materials
        """
        self.logger.info("qbr_scheduling_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        usage_data = state.get("entities", {}).get("usage_data", {})
        business_data = state.get("entities", {}).get("business_data", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})

        self.logger.debug(
            "qbr_scheduling_details",
            customer_id=customer_id,
            tier=customer_metadata.get("tier", "standard")
        )

        # Determine QBR schedule
        qbr_schedule = self._determine_qbr_schedule(
            customer_metadata,
            business_data
        )

        # Prepare QBR materials
        qbr_materials = self._prepare_qbr_materials(
            usage_data,
            business_data,
            engagement_data,
            customer_metadata
        )

        # Generate insights for QBR
        qbr_insights = self._generate_qbr_insights(
            usage_data,
            business_data,
            engagement_data,
            customer_metadata
        )

        # Coordinate attendees
        attendee_plan = self._coordinate_attendees(
            customer_metadata,
            qbr_schedule
        )

        # Create action plan
        qbr_action_plan = self._create_qbr_action_plan(
            qbr_insights,
            customer_metadata
        )

        # Format response
        response = self._format_qbr_report(
            qbr_schedule,
            qbr_materials,
            qbr_insights,
            attendee_plan,
            qbr_action_plan
        )

        state["agent_response"] = response
        state["qbr_scheduled"] = qbr_schedule["next_qbr_date"]
        state["qbr_status"] = qbr_schedule["status"]
        state["qbr_preparation_stage"] = qbr_schedule.get("preparation_stage", "not_started")
        state["qbr_materials"] = qbr_materials
        state["qbr_insights"] = qbr_insights
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "qbr_scheduling_completed",
            customer_id=customer_id,
            next_qbr=qbr_schedule["next_qbr_date"],
            status=qbr_schedule["status"]
        )

        return state

    def _determine_qbr_schedule(
        self,
        customer_metadata: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine QBR schedule based on customer tier and history.

        Args:
            customer_metadata: Customer profile data
            business_data: Business and contract data

        Returns:
            QBR scheduling information
        """
        tier = customer_metadata.get("tier", "standard")
        cadence_config = self.QBR_CADENCE.get(tier, self.QBR_CADENCE["standard"])

        # Get last QBR date
        last_qbr_str = business_data.get("last_qbr_date")
        if last_qbr_str:
            last_qbr_date = datetime.fromisoformat(last_qbr_str.replace('Z', '+00:00'))
        else:
            # No previous QBR - schedule first one
            last_qbr_date = datetime.now(UTC) - timedelta(days=cadence_config["frequency_days"])

        # Calculate next QBR date
        next_qbr_date = last_qbr_date + timedelta(days=cadence_config["frequency_days"])
        days_until_qbr = (next_qbr_date - datetime.now(UTC)).days

        # Determine status and urgency
        if days_until_qbr < 0:
            status = "overdue"
            urgency = "critical"
        elif days_until_qbr <= self.PREPARATION_TIMELINE["send_invitation"]:
            status = "preparation"
            urgency = "high"
        elif days_until_qbr <= 30:
            status = "upcoming"
            urgency = "medium"
        else:
            status = "scheduled"
            urgency = "low"

        # Determine preparation stage
        if days_until_qbr <= self.PREPARATION_TIMELINE["final_review"]:
            preparation_stage = "final_review"
        elif days_until_qbr <= self.PREPARATION_TIMELINE["confirm_attendees"]:
            preparation_stage = "confirm_attendees"
        elif days_until_qbr <= self.PREPARATION_TIMELINE["materials_preparation"]:
            preparation_stage = "prepare_materials"
        elif days_until_qbr <= self.PREPARATION_TIMELINE["send_invitation"]:
            preparation_stage = "send_invitation"
        else:
            preparation_stage = "not_started"

        # Check for renewal alignment
        renewal_date_str = business_data.get("renewal_date")
        renewal_aligned = False
        if renewal_date_str:
            renewal_date = datetime.fromisoformat(renewal_date_str.replace('Z', '+00:00'))
            days_to_renewal = (renewal_date - next_qbr_date).days
            renewal_aligned = abs(days_to_renewal) <= 30  # Within 30 days of renewal

        return {
            "next_qbr_date": next_qbr_date.isoformat(),
            "days_until_qbr": days_until_qbr,
            "status": status,
            "urgency": urgency,
            "preparation_stage": preparation_stage,
            "duration_minutes": cadence_config["duration_minutes"],
            "executive_required": cadence_config["executive_required"],
            "frequency_days": cadence_config["frequency_days"],
            "last_qbr_date": last_qbr_date.isoformat(),
            "renewal_aligned": renewal_aligned,
            "qbr_count": business_data.get("qbr_count", 0) + 1
        }

    def _prepare_qbr_materials(
        self,
        usage_data: Dict[str, Any],
        business_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare comprehensive QBR materials."""
        materials = {
            "agenda": self.AGENDA_SECTIONS.copy(),
            "metrics_summary": self._create_metrics_summary(usage_data, engagement_data),
            "success_wins": self._identify_success_wins(usage_data, engagement_data),
            "challenges": self._identify_challenges(usage_data, engagement_data),
            "recommendations": self._generate_recommendations(usage_data, business_data),
            "presentation_slides": []
        }

        # Generate slide outline
        materials["presentation_slides"] = [
            "Welcome & Agenda",
            "Business Context & Goals Review",
            f"Usage Metrics: {materials['metrics_summary']['active_users']} Active Users",
            f"Feature Adoption: {materials['metrics_summary']['features_adopted']} Features",
            "Success Stories & Wins",
            "Challenges & Mitigation Plans",
            "Upcoming Product Roadmap",
            "Action Items & Next Steps"
        ]

        return materials

    def _create_metrics_summary(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create summary of key metrics for QBR."""
        return {
            "active_users": usage_data.get("active_users", 0),
            "total_users": usage_data.get("total_users", 0),
            "adoption_rate": usage_data.get("adoption_rate", 0),
            "features_adopted": len(usage_data.get("features_used", [])),
            "total_features": usage_data.get("total_features_available", 10),
            "nps_score": engagement_data.get("nps_score", 0),
            "support_tickets": engagement_data.get("support_tickets_last_90d", 0),
            "login_frequency": usage_data.get("average_logins_per_week", 0)
        }

    def _identify_success_wins(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> List[str]:
        """Identify success wins to highlight in QBR."""
        wins = []

        active_users = usage_data.get("active_users", 0)
        total_users = usage_data.get("total_users", 1)
        adoption_rate = (active_users / total_users * 100) if total_users > 0 else 0

        if adoption_rate > 80:
            wins.append(f"Outstanding user adoption: {int(adoption_rate)}% of licensed users active")

        features_used = len(usage_data.get("features_used", []))
        if features_used >= 7:
            wins.append(f"Strong feature adoption: Using {features_used} platform features")

        automation_rules = usage_data.get("automation_rules_active", 0)
        if automation_rules >= 3:
            wins.append(f"Automation mastery: {automation_rules} active automation workflows")

        nps = engagement_data.get("nps_score", 0)
        if nps >= 9:
            wins.append(f"Exceptional satisfaction: NPS score of {nps}/10")

        if not wins:
            wins.append("Successful platform implementation and ongoing usage")

        return wins[:5]

    def _identify_challenges(
        self,
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify challenges to address in QBR."""
        challenges = []

        active_users = usage_data.get("active_users", 0)
        total_users = usage_data.get("total_users", 1)
        adoption_rate = (active_users / total_users * 100) if total_users > 0 else 0

        if adoption_rate < 50:
            challenges.append({
                "challenge": "Low user adoption",
                "impact": f"Only {int(adoption_rate)}% of licenses being used",
                "recommendation": "Launch user activation campaign and training program"
            })

        support_tickets = engagement_data.get("support_tickets_last_90d", 0)
        if support_tickets > 20:
            challenges.append({
                "challenge": "High support volume",
                "impact": f"{support_tickets} tickets in last 90 days",
                "recommendation": "Review common issues and provide targeted training"
            })

        features_used = len(usage_data.get("features_used", []))
        total_features = usage_data.get("total_features_available", 10)
        if features_used < total_features * 0.4:
            challenges.append({
                "challenge": "Limited feature utilization",
                "impact": f"Only {features_used}/{total_features} features being used",
                "recommendation": "Demonstrate advanced capabilities and use cases"
            })

        return challenges[:4]

    def _generate_recommendations(
        self,
        usage_data: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> List[str]:
        """Generate strategic recommendations for QBR."""
        recommendations = []

        # Usage-based recommendations
        active_users = usage_data.get("active_users", 0)
        contracted_users = business_data.get("contracted_users", 10)

        if active_users > contracted_users * 0.9:
            recommendations.append("Consider expanding user licenses - approaching capacity")

        features_used = len(usage_data.get("features_used", []))
        if features_used >= 5:
            recommendations.append("Explore advanced automation features to increase efficiency")

        # Strategic recommendations
        recommendations.append("Schedule department workshops to drive deeper adoption")
        recommendations.append("Identify internal champions to support peer training")

        return recommendations[:5]

    def _generate_qbr_insights(
        self,
        usage_data: Dict[str, Any],
        business_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate data-driven insights for QBR discussion."""
        insights = {
            "usage_trends": self._analyze_usage_trends(usage_data),
            "engagement_trends": self._analyze_engagement_trends(engagement_data),
            "roi_analysis": self._calculate_roi_analysis(usage_data, business_data),
            "benchmarking": self._generate_benchmarking_data(usage_data, customer_metadata)
        }

        return insights

    def _analyze_usage_trends(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze usage trends over time."""
        current_usage = usage_data.get("active_users", 0)
        previous_usage = usage_data.get("previous_quarter_active_users", current_usage)

        if previous_usage > 0:
            usage_change_pct = ((current_usage - previous_usage) / previous_usage) * 100
        else:
            usage_change_pct = 0

        trend = "increasing" if usage_change_pct > 10 else "stable" if usage_change_pct >= -5 else "declining"

        return {
            "current_active_users": current_usage,
            "previous_quarter_users": previous_usage,
            "change_percentage": round(usage_change_pct, 1),
            "trend": trend
        }

    def _analyze_engagement_trends(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement trends."""
        current_nps = engagement_data.get("nps_score", 5)
        previous_nps = engagement_data.get("previous_quarter_nps", current_nps)

        nps_change = current_nps - previous_nps
        sentiment = "improving" if nps_change > 1 else "stable" if nps_change >= -1 else "declining"

        return {
            "current_nps": current_nps,
            "previous_quarter_nps": previous_nps,
            "nps_change": nps_change,
            "sentiment": sentiment
        }

    def _calculate_roi_analysis(
        self,
        usage_data: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate ROI metrics for QBR."""
        automation_rules = usage_data.get("automation_rules_active", 0)
        time_saved_hours = automation_rules * 40  # Est. 40 hours saved per automation per quarter

        contract_value = business_data.get("contract_value", 0)
        active_users = usage_data.get("active_users", 1)
        cost_per_user = contract_value / active_users if active_users > 0 else 0

        return {
            "automation_time_saved_hours": time_saved_hours,
            "estimated_value_realized": time_saved_hours * 50,  # $50/hour value
            "cost_per_active_user": int(cost_per_user),
            "roi_positive": time_saved_hours * 50 > contract_value
        }

    def _generate_benchmarking_data(
        self,
        usage_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate benchmarking data against similar customers."""
        tier = customer_metadata.get("tier", "standard")

        # Simplified benchmarks - would come from analytics in production
        benchmarks = {
            "enterprise": {"avg_adoption": 85, "avg_features": 9, "avg_nps": 8},
            "premium": {"avg_adoption": 75, "avg_features": 7, "avg_nps": 7},
            "growth": {"avg_adoption": 65, "avg_features": 5, "avg_nps": 7},
            "standard": {"avg_adoption": 55, "avg_features": 4, "avg_nps": 6}
        }

        benchmark = benchmarks.get(tier, benchmarks["standard"])
        active_users = usage_data.get("active_users", 0)
        total_users = usage_data.get("total_users", 1)
        actual_adoption = (active_users / total_users * 100) if total_users > 0 else 0

        return {
            "tier": tier,
            "customer_adoption": int(actual_adoption),
            "benchmark_adoption": benchmark["avg_adoption"],
            "vs_benchmark": "above" if actual_adoption > benchmark["avg_adoption"] else "below",
            "benchmark_features": benchmark["avg_features"],
            "benchmark_nps": benchmark["avg_nps"]
        }

    def _coordinate_attendees(
        self,
        customer_metadata: Dict[str, Any],
        qbr_schedule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate QBR attendees."""
        # Internal attendees
        internal_attendees = [
            {"role": "Customer Success Manager", "required": True},
            {"role": "Account Executive", "required": qbr_schedule["executive_required"]}
        ]

        if qbr_schedule["executive_required"]:
            internal_attendees.append({"role": "VP Customer Success", "required": False})

        # External attendees (customer side)
        external_attendees = [
            {"role": "Primary Contact", "required": True},
            {"role": "Technical Lead", "required": True}
        ]

        if qbr_schedule["executive_required"]:
            external_attendees.append({"role": "Executive Sponsor", "required": True})

        return {
            "internal_attendees": internal_attendees,
            "external_attendees": external_attendees,
            "total_attendees": len(internal_attendees) + len(external_attendees),
            "coordination_status": "pending"
        }

    def _create_qbr_action_plan(
        self,
        qbr_insights: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create action plan for QBR preparation and follow-up."""
        actions = []

        # Pre-QBR actions
        actions.append({
            "action": "Send QBR invitation and agenda to customer",
            "owner": "CSM",
            "timeline": "14 days before QBR",
            "priority": "high"
        })

        actions.append({
            "action": "Prepare QBR presentation and materials",
            "owner": "CSM",
            "timeline": "7 days before QBR",
            "priority": "high"
        })

        actions.append({
            "action": "Review customer data and identify discussion topics",
            "owner": "CSM + Analytics",
            "timeline": "7 days before QBR",
            "priority": "medium"
        })

        # Post-QBR actions
        actions.append({
            "action": "Send QBR summary and action items within 24 hours",
            "owner": "CSM",
            "timeline": "1 day after QBR",
            "priority": "high"
        })

        actions.append({
            "action": "Schedule follow-up check-in for action items",
            "owner": "CSM",
            "timeline": "30 days after QBR",
            "priority": "medium"
        })

        return actions

    def _format_qbr_report(
        self,
        qbr_schedule: Dict[str, Any],
        qbr_materials: Dict[str, Any],
        qbr_insights: Dict[str, Any],
        attendee_plan: Dict[str, Any],
        qbr_action_plan: List[Dict[str, str]]
    ) -> str:
        """Format QBR scheduling and preparation report."""
        status = qbr_schedule["status"]
        urgency = qbr_schedule["urgency"]

        status_emoji = {
            "overdue": "????",
            "preparation": "???",
            "upcoming": "????",
            "scheduled": "???"
        }

        urgency_emoji = {
            "critical": "????",
            "high": "????",
            "medium": "????",
            "low": "???"
        }

        next_qbr = datetime.fromisoformat(qbr_schedule["next_qbr_date"])

        report = f"""**{status_emoji.get(status, '????')} Quarterly Business Review (QBR) Planning**

**Status:** {status.title()} {urgency_emoji.get(urgency, '')}
**Next QBR:** {next_qbr.strftime('%B %d, %Y')} ({qbr_schedule['days_until_qbr']} days)
**Duration:** {qbr_schedule['duration_minutes']} minutes
**QBR Number:** #{qbr_schedule['qbr_count']}
**Preparation Stage:** {qbr_schedule['preparation_stage'].replace('_', ' ').title()}

**???? QBR Metrics Summary:**
- Active Users: {qbr_materials['metrics_summary']['active_users']}/{qbr_materials['metrics_summary']['total_users']}
- Features Adopted: {qbr_materials['metrics_summary']['features_adopted']}/{qbr_materials['metrics_summary']['total_features']}
- NPS Score: {qbr_materials['metrics_summary']['nps_score']}/10
- Support Tickets (90d): {qbr_materials['metrics_summary']['support_tickets']}

**???? Success Wins to Highlight:**
"""

        for i, win in enumerate(qbr_materials["success_wins"], 1):
            report += f"{i}. {win}\n"

        # Insights
        report += f"\n**???? Key Insights:**\n"
        usage_trends = qbr_insights["usage_trends"]
        report += f"- User Growth: {usage_trends['change_percentage']:+.1f}% vs last quarter ({usage_trends['trend']})\n"

        engagement_trends = qbr_insights["engagement_trends"]
        report += f"- NPS Change: {engagement_trends['nps_change']:+d} points ({engagement_trends['sentiment']})\n"

        roi = qbr_insights["roi_analysis"]
        report += f"- Time Savings: {roi['automation_time_saved_hours']} hours via automation\n"

        benchmark = qbr_insights["benchmarking"]
        report += f"- vs Benchmark: {benchmark['vs_benchmark'].title()} average for {benchmark['tier']} tier\n"

        # Challenges
        if qbr_materials.get("challenges"):
            report += "\n**?????? Challenges to Address:**\n"
            for i, challenge in enumerate(qbr_materials["challenges"][:3], 1):
                report += f"{i}. **{challenge['challenge']}**\n"
                report += f"   - Impact: {challenge['impact']}\n"
                report += f"   - Recommendation: {challenge['recommendation']}\n"

        # Attendees
        report += f"\n**???? Attendees ({attendee_plan['total_attendees']} expected):**\n"
        report += "Internal: "
        report += ", ".join([att["role"] for att in attendee_plan["internal_attendees"] if att["required"]])
        report += "\nCustomer: "
        report += ", ".join([att["role"] for att in attendee_plan["external_attendees"] if att["required"]])

        # Agenda
        report += "\n\n**???? QBR Agenda:**\n"
        for i, section in enumerate(qbr_materials["agenda"], 1):
            report += f"{i}. {section}\n"

        # Action Plan
        report += "\n**??? Action Plan:**\n"
        for i, action in enumerate(qbr_action_plan[:5], 1):
            priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
            report += f"{i}. **{action['action']}** {priority_icon}\n"
            report += f"   - Owner: {action['owner']}\n"
            report += f"   - Timeline: {action['timeline']}\n"

        if qbr_schedule.get("renewal_aligned"):
            report += "\n**???? Note:** This QBR is aligned with upcoming renewal - excellent opportunity for expansion discussion!"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing QBR Scheduler Agent (TASK-2061)")
        print("=" * 70)

        agent = QBRSchedulerAgent()

        # Test 1: Upcoming QBR for enterprise customer
        print("\n\nTest 1: Enterprise QBR Preparation")
        print("-" * 70)

        state1 = create_initial_state(
            "Schedule and prepare QBR",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {
                    "tier": "enterprise",
                    "company_name": "TechCorp Inc"
                }
            }
        )
        state1["entities"] = {
            "usage_data": {
                "active_users": 95,
                "total_users": 100,
                "features_used": ["reporting", "analytics", "automation", "api", "collaboration",
                                 "dashboards", "integrations", "workflows"],
                "total_features_available": 10,
                "adoption_rate": 95,
                "automation_rules_active": 8,
                "average_logins_per_week": 4.5,
                "previous_quarter_active_users": 85
            },
            "engagement_data": {
                "nps_score": 9,
                "support_tickets_last_90d": 8,
                "previous_quarter_nps": 8
            },
            "business_data": {
                "last_qbr_date": (datetime.now(UTC) - timedelta(days=75)).isoformat(),
                "renewal_date": (datetime.now(UTC) + timedelta(days=45)).isoformat(),
                "contract_value": 120000,
                "contracted_users": 100,
                "qbr_count": 3
            }
        }

        result1 = await agent.process(state1)

        print(f"QBR Status: {result1['qbr_status']}")
        print(f"Next QBR: {result1['qbr_scheduled']}")
        print(f"Preparation Stage: {result1['qbr_preparation_stage']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Overdue QBR
        print("\n\n" + "=" * 70)
        print("Test 2: Overdue QBR")
        print("-" * 70)

        state2 = create_initial_state(
            "QBR scheduling review",
            context={
                "customer_id": "cust_premium_002",
                "customer_metadata": {
                    "tier": "premium",
                    "company_name": "GrowthCo"
                }
            }
        )
        state2["entities"] = {
            "usage_data": {
                "active_users": 45,
                "total_users": 75,
                "features_used": ["reporting", "analytics", "collaboration"],
                "total_features_available": 8,
                "adoption_rate": 60,
                "automation_rules_active": 2,
                "previous_quarter_active_users": 50
            },
            "engagement_data": {
                "nps_score": 7,
                "support_tickets_last_90d": 15,
                "previous_quarter_nps": 8
            },
            "business_data": {
                "last_qbr_date": (datetime.now(UTC) - timedelta(days=120)).isoformat(),
                "contract_value": 45000,
                "contracted_users": 75,
                "qbr_count": 1
            }
        }

        result2 = await agent.process(state2)

        print(f"QBR Status: {result2['qbr_status']}")
        print(f"Days Until QBR: {result2.get('days_to_renewal', 'N/A')}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
