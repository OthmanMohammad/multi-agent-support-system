"""
User Activation Agent - TASK-2032

Activates inactive users, re-engages dormant accounts, and measures DAU/MAU improvements
to increase product stickiness and reduce seat waste.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("user_activation", tier="revenue", category="customer_success")
class UserActivationAgent(BaseAgent):
    """
    User Activation Agent.

    Drives user activation by:
    - Identifying inactive and dormant users
    - Creating personalized re-engagement campaigns
    - Tracking activation improvements (DAU/MAU)
    - Reducing seat waste
    - Measuring time-to-first-value for new users
    - Analyzing activation drop-off points
    """

    # User activity states
    USER_STATES = {
        "active": {"last_login_days": 7, "engagement": "high"},
        "occasional": {"last_login_days": 14, "engagement": "medium"},
        "inactive": {"last_login_days": 30, "engagement": "low"},
        "dormant": {"last_login_days": 60, "engagement": "none"},
        "zombie": {"last_login_days": 90, "engagement": "none"}
    }

    # Activation benchmarks
    ACTIVATION_BENCHMARKS = {
        "excellent": 80,  # 80%+ DAU/MAU ratio
        "good": 60,
        "acceptable": 40,
        "poor": 20
    }

    def __init__(self):
        config = AgentConfig(
            name="user_activation",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=600,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze user activation and generate re-engagement strategies.

        Args:
            state: Current agent state with user activity data

        Returns:
            Updated state with activation analysis and recommendations
        """
        self.logger.info("user_activation_analysis_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        user_activity_data = state.get("entities", {}).get("user_activity_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "user_activation_details",
            customer_id=customer_id,
            total_seats=user_activity_data.get("total_seats", 0),
            active_users=user_activity_data.get("active_users", 0)
        )

        # Analyze user activation
        activation_analysis = self._analyze_user_activation(
            user_activity_data,
            customer_metadata
        )

        # Generate re-engagement strategy
        reengagement_strategy = self._create_reengagement_strategy(
            activation_analysis,
            customer_metadata
        )

        # Calculate impact metrics
        impact_metrics = self._calculate_activation_impact(activation_analysis)

        # Format response
        response = self._format_activation_report(
            activation_analysis,
            reengagement_strategy,
            impact_metrics
        )

        state["agent_response"] = response
        state["activation_rate"] = activation_analysis["activation_rate"]
        state["inactive_users_count"] = activation_analysis["inactive_count"]
        state["dormant_users_count"] = activation_analysis["dormant_count"]
        state["dau_mau_ratio"] = activation_analysis.get("dau_mau_ratio", 0)
        state["activation_analysis"] = activation_analysis
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "user_activation_analysis_completed",
            customer_id=customer_id,
            activation_rate=activation_analysis["activation_rate"],
            inactive_count=activation_analysis["inactive_count"],
            dormant_count=activation_analysis["dormant_count"]
        )

        return state

    def _analyze_user_activation(
        self,
        user_activity_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze user activation patterns.

        Args:
            user_activity_data: User activity metrics
            customer_metadata: Customer profile data

        Returns:
            Comprehensive activation analysis
        """
        total_seats = user_activity_data.get("total_seats", 0)
        active_users = user_activity_data.get("active_users", 0)
        dau = user_activity_data.get("dau", 0)
        mau = user_activity_data.get("mau", 0)
        user_list = user_activity_data.get("users", [])

        # Categorize users by activity state
        users_by_state = self._categorize_users(user_list)

        # Calculate activation metrics
        activation_rate = (active_users / total_seats * 100) if total_seats > 0 else 0
        dau_mau_ratio = (dau / mau * 100) if mau > 0 else 0

        # Determine activation health
        activation_health = self._determine_activation_health(activation_rate)

        # Identify at-risk users (inactive + dormant)
        inactive_count = len(users_by_state.get("inactive", []))
        dormant_count = len(users_by_state.get("dormant", []))
        zombie_count = len(users_by_state.get("zombie", []))

        at_risk_count = inactive_count + dormant_count + zombie_count

        # Calculate seat waste
        seat_waste_pct = ((total_seats - active_users) / total_seats * 100) if total_seats > 0 else 0

        # Analyze activation trends
        previous_active = user_activity_data.get("previous_month_active_users", active_users)
        activation_trend = self._calculate_trend(active_users, previous_active)

        # Identify activation barriers
        barriers = self._identify_activation_barriers(
            users_by_state,
            user_activity_data,
            activation_rate
        )

        return {
            "total_seats": total_seats,
            "active_users": active_users,
            "activation_rate": round(activation_rate, 1),
            "activation_health": activation_health,
            "dau": dau,
            "mau": mau,
            "dau_mau_ratio": round(dau_mau_ratio, 1),
            "users_by_state": users_by_state,
            "inactive_count": inactive_count,
            "dormant_count": dormant_count,
            "zombie_count": zombie_count,
            "at_risk_count": at_risk_count,
            "seat_waste_percentage": round(seat_waste_pct, 1),
            "activation_trend": activation_trend,
            "barriers": barriers,
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _categorize_users(self, user_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize users by activity state."""
        categorized = {
            "active": [],
            "occasional": [],
            "inactive": [],
            "dormant": [],
            "zombie": []
        }

        for user in user_list:
            last_login = user.get("last_login_date")
            if not last_login:
                categorized["zombie"].append(user)
                continue

            try:
                last_login_dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                days_since_login = (datetime.now(UTC) - last_login_dt).days

                for state, criteria in self.USER_STATES.items():
                    if days_since_login <= criteria["last_login_days"]:
                        categorized[state].append(user)
                        break
                else:
                    categorized["zombie"].append(user)

            except (ValueError, AttributeError):
                categorized["zombie"].append(user)

        return categorized

    def _determine_activation_health(self, activation_rate: float) -> str:
        """Determine activation health status."""
        if activation_rate >= self.ACTIVATION_BENCHMARKS["excellent"]:
            return "excellent"
        elif activation_rate >= self.ACTIVATION_BENCHMARKS["good"]:
            return "good"
        elif activation_rate >= self.ACTIVATION_BENCHMARKS["acceptable"]:
            return "acceptable"
        else:
            return "poor"

    def _calculate_trend(self, current: int, previous: int) -> Dict[str, Any]:
        """Calculate activation trend."""
        if previous > 0:
            change_pct = ((current - previous) / previous) * 100
        else:
            change_pct = 0

        direction = "improving" if change_pct > 5 else "stable" if change_pct >= -5 else "declining"

        return {
            "direction": direction,
            "change_percentage": round(change_pct, 1),
            "change_count": current - previous
        }

    def _identify_activation_barriers(
        self,
        users_by_state: Dict[str, List[Dict[str, Any]]],
        user_activity_data: Dict[str, Any],
        activation_rate: float
    ) -> List[str]:
        """Identify barriers to user activation."""
        barriers = []

        # Check for high dormant rate
        total_users = sum(len(users) for users in users_by_state.values())
        dormant_rate = (len(users_by_state.get("dormant", [])) / total_users * 100) if total_users > 0 else 0

        if dormant_rate > 20:
            barriers.append("High dormant user rate suggests poor onboarding or unclear value prop")

        # Check for zombie users
        if len(users_by_state.get("zombie", [])) > 0:
            barriers.append(f"{len(users_by_state['zombie'])} users never logged in - invitation or access issues")

        # Check for low DAU/MAU
        dau = user_activity_data.get("dau", 0)
        mau = user_activity_data.get("mau", 0)
        if mau > 0 and (dau / mau) < 0.3:
            barriers.append("Low DAU/MAU ratio indicates users log in infrequently")

        # Check for low overall activation
        if activation_rate < 40:
            barriers.append("Low activation rate - consider seat optimization or user training")

        if not barriers:
            barriers.append("No significant activation barriers detected")

        return barriers

    def _create_reengagement_strategy(
        self,
        activation_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create personalized re-engagement strategy."""
        users_by_state = activation_analysis["users_by_state"]
        activation_health = activation_analysis["activation_health"]

        strategy = {
            "priority": "low",
            "campaigns": [],
            "target_groups": [],
            "expected_improvement": 0
        }

        # Zombie users - never logged in
        if users_by_state.get("zombie"):
            strategy["campaigns"].append({
                "name": "Never-Logged-In Recovery",
                "target": "zombie",
                "tactics": [
                    "Resend invitation emails with personalized message",
                    "Direct outreach from CSM to verify access",
                    "Offer guided setup session"
                ],
                "priority": "high",
                "target_count": len(users_by_state["zombie"])
            })
            strategy["target_groups"].append("zombie")

        # Dormant users - haven't logged in 60+ days
        if users_by_state.get("dormant") and len(users_by_state["dormant"]) > 0:
            strategy["campaigns"].append({
                "name": "Dormant User Reactivation",
                "target": "dormant",
                "tactics": [
                    "Send 'We Miss You' email with new feature highlights",
                    "Offer 1:1 refresher training session",
                    "Share recent customer success stories"
                ],
                "priority": "high",
                "target_count": len(users_by_state["dormant"])
            })
            strategy["target_groups"].append("dormant")

        # Inactive users - haven't logged in 30+ days
        if users_by_state.get("inactive") and len(users_by_state["inactive"]) > 0:
            strategy["campaigns"].append({
                "name": "Inactive User Nudge",
                "target": "inactive",
                "tactics": [
                    "Send reminder email with quick-win use cases",
                    "In-app notifications for their team members",
                    "Highlight features they haven't tried"
                ],
                "priority": "medium",
                "target_count": len(users_by_state["inactive"])
            })
            strategy["target_groups"].append("inactive")

        # Occasional users - make them regular
        if users_by_state.get("occasional") and len(users_by_state["occasional"]) >= 5:
            strategy["campaigns"].append({
                "name": "Occasional to Active Conversion",
                "target": "occasional",
                "tactics": [
                    "Email series on advanced features",
                    "Create habit-forming workflows",
                    "Invite to user community"
                ],
                "priority": "low",
                "target_count": len(users_by_state["occasional"])
            })
            strategy["target_groups"].append("occasional")

        # Set overall priority
        if activation_health in ["poor", "acceptable"]:
            strategy["priority"] = "critical"
        elif len(strategy["target_groups"]) >= 2:
            strategy["priority"] = "high"
        else:
            strategy["priority"] = "medium"

        # Estimate improvement
        total_at_risk = activation_analysis["at_risk_count"]
        strategy["expected_improvement"] = min(50, total_at_risk // 2)  # Conservative estimate

        return strategy

    def _calculate_activation_impact(self, activation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate impact of improving activation."""
        total_seats = activation_analysis["total_seats"]
        current_active = activation_analysis["active_users"]
        at_risk = activation_analysis["at_risk_count"]

        # Potential seat recovery
        potential_recovery = min(at_risk, at_risk // 2)  # Conservative 50% recovery

        # Potential activation rate improvement
        potential_active = current_active + potential_recovery
        potential_activation_rate = (potential_active / total_seats * 100) if total_seats > 0 else 0

        improvement_pct = potential_activation_rate - activation_analysis["activation_rate"]

        # Retention impact
        retention_impact = "high" if improvement_pct > 20 else "medium" if improvement_pct > 10 else "low"

        # Revenue protection (seat waste reduction)
        current_waste = activation_analysis["seat_waste_percentage"]
        potential_waste = ((total_seats - potential_active) / total_seats * 100) if total_seats > 0 else 0
        waste_reduction = current_waste - potential_waste

        return {
            "potential_recovery": potential_recovery,
            "potential_activation_rate": round(potential_activation_rate, 1),
            "improvement_percentage": round(improvement_pct, 1),
            "retention_impact": retention_impact,
            "waste_reduction_percentage": round(waste_reduction, 1)
        }

    def _format_activation_report(
        self,
        activation_analysis: Dict[str, Any],
        reengagement_strategy: Dict[str, Any],
        impact_metrics: Dict[str, Any]
    ) -> str:
        """Format user activation report."""
        health = activation_analysis["activation_health"]

        health_emoji = {
            "excellent": "????",
            "good": "???",
            "acceptable": "??????",
            "poor": "????"
        }

        report = f"""**{health_emoji.get(health, '????')} User Activation Analysis**

**Activation Health:** {health.upper()}
**Activation Rate:** {activation_analysis['activation_rate']}% ({activation_analysis['active_users']}/{activation_analysis['total_seats']} seats)
**Seat Waste:** {activation_analysis['seat_waste_percentage']}%

**Engagement Metrics:**
- Daily Active Users (DAU): {activation_analysis['dau']}
- Monthly Active Users (MAU): {activation_analysis['mau']}
- DAU/MAU Ratio: {activation_analysis['dau_mau_ratio']}%

**User Distribution:**
"""

        # User state breakdown
        for state in ["active", "occasional", "inactive", "dormant", "zombie"]:
            count = len(activation_analysis["users_by_state"].get(state, []))
            if count > 0:
                state_icon = "????" if state == "active" else "????" if state == "occasional" else "????" if state == "inactive" else "????"
                report += f"- {state_icon} {state.title()}: {count} users\n"

        # Activation trend
        trend = activation_analysis["activation_trend"]
        trend_icon = "????" if trend["direction"] == "improving" else "??????" if trend["direction"] == "stable" else "????"
        report += f"\n**Activation Trend:** {trend_icon} {trend['direction'].title()}\n"
        report += f"- Change: {trend['change_percentage']:+.1f}% ({trend['change_count']:+d} users)\n"

        # Barriers
        if activation_analysis.get("barriers"):
            report += "\n**???? Activation Barriers:**\n"
            for barrier in activation_analysis["barriers"][:3]:
                report += f"- {barrier}\n"

        # Re-engagement strategy
        if reengagement_strategy["campaigns"]:
            report += f"\n**???? Re-engagement Strategy ({reengagement_strategy['priority'].upper()} Priority)**\n"
            for campaign in reengagement_strategy["campaigns"][:3]:
                report += f"\n**{campaign['name']}** (Target: {campaign['target_count']} users)\n"
                for tactic in campaign["tactics"][:2]:
                    report += f"- {tactic}\n"

        # Impact projection
        report += f"\n**???? Potential Impact:**\n"
        report += f"- Recoverable Users: {impact_metrics['potential_recovery']}\n"
        report += f"- Target Activation Rate: {impact_metrics['potential_activation_rate']}%\n"
        report += f"- Improvement: +{impact_metrics['improvement_percentage']}%\n"
        report += f"- Seat Waste Reduction: -{impact_metrics['waste_reduction_percentage']}%\n"
        report += f"- Retention Impact: {impact_metrics['retention_impact'].title()}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing User Activation Agent (TASK-2032)")
        print("=" * 70)

        agent = UserActivationAgent()

        # Test 1: Poor activation scenario
        print("\n\nTest 1: Poor User Activation")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze user activation",
            context={
                "customer_id": "cust_poor_activation",
                "customer_metadata": {"plan": "enterprise"}
            }
        )
        state1["entities"] = {
            "user_activity_data": {
                "total_seats": 50,
                "active_users": 15,
                "dau": 8,
                "mau": 18,
                "previous_month_active_users": 20,
                "users": [
                    {"id": f"user_{i}", "last_login_date": (datetime.now(UTC) - timedelta(days=i*3)).isoformat()}
                    for i in range(1, 31)
                ] + [
                    {"id": f"zombie_{i}", "last_login_date": None}
                    for i in range(1, 21)
                ]
            }
        }

        result1 = await agent.process(state1)

        print(f"Activation Rate: {result1['activation_rate']}%")
        print(f"Inactive Users: {result1['inactive_users_count']}")
        print(f"Dormant Users: {result1['dormant_users_count']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Good activation scenario
        print("\n\n" + "=" * 70)
        print("Test 2: Good User Activation")
        print("-" * 70)

        state2 = create_initial_state(
            "Check user activation",
            context={
                "customer_id": "cust_good_activation",
                "customer_metadata": {"plan": "premium"}
            }
        )
        state2["entities"] = {
            "user_activity_data": {
                "total_seats": 30,
                "active_users": 25,
                "dau": 20,
                "mau": 26,
                "previous_month_active_users": 23,
                "users": [
                    {"id": f"user_{i}", "last_login_date": (datetime.now(UTC) - timedelta(days=i)).isoformat()}
                    for i in range(1, 31)
                ]
            }
        }

        result2 = await agent.process(state2)

        print(f"Activation Rate: {result2['activation_rate']}%")
        print(f"DAU/MAU Ratio: {result2['dau_mau_ratio']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
