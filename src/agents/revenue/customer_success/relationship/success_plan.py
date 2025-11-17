"""
Success Plan Agent - TASK-2065

Creates and manages customer success plans with strategic goals, milestones,
and measurable outcomes to ensure customers achieve desired business value.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("success_plan", tier="revenue", category="customer_success")
class SuccessPlanAgent(BaseAgent):
    """
    Success Plan Agent.

    Manages customer success planning by:
    - Creating comprehensive success plans with goals and milestones
    - Aligning plans with customer business objectives
    - Tracking progress against success criteria
    - Identifying blockers and risks to plan execution
    - Updating plans based on changing priorities
    - Measuring business value and outcomes achieved
    """

    # Success plan components
    PLAN_COMPONENTS = [
        "business_objectives",
        "success_criteria",
        "milestones",
        "value_metrics",
        "stakeholder_alignment",
        "risk_mitigation"
    ]

    # Plan lifecycle stages
    PLAN_STAGES = {
        "planning": {"duration_days": 30, "focus": "Define objectives and success criteria"},
        "execution": {"duration_days": 90, "focus": "Implement and track against milestones"},
        "optimization": {"duration_days": 60, "focus": "Refine approach and maximize value"},
        "renewal": {"duration_days": 30, "focus": "Demonstrate value and plan next phase"}
    }

    # Goal categories
    GOAL_CATEGORIES = {
        "operational_efficiency": "Streamline processes and reduce manual work",
        "revenue_growth": "Drive revenue through better insights and automation",
        "cost_reduction": "Reduce costs through efficiency and optimization",
        "user_adoption": "Increase platform adoption and engagement",
        "strategic_transformation": "Enable strategic business transformation",
        "customer_experience": "Improve end-customer satisfaction and experience"
    }

    # Milestone types
    MILESTONE_TYPES = [
        "onboarding_complete",
        "first_value_realized",
        "adoption_target_met",
        "roi_threshold_achieved",
        "expansion_ready",
        "advocacy_milestone"
    ]

    def __init__(self):
        config = AgentConfig(
            name="success_plan",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",
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
        Create or update customer success plan.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with success plan
        """
        self.logger.info("success_plan_management_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        business_data = state.get("entities", {}).get("business_data", {})
        usage_data = state.get("entities", {}).get("usage_data", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})
        existing_plan = state.get("entities", {}).get("success_plan", {})

        self.logger.debug(
            "success_plan_details",
            customer_id=customer_id,
            has_existing_plan=bool(existing_plan)
        )

        # Create or update success plan
        if existing_plan:
            success_plan = self._update_success_plan(
                existing_plan,
                usage_data,
                engagement_data,
                business_data
            )
        else:
            success_plan = self._create_success_plan(
                customer_metadata,
                business_data
            )

        # Track progress
        progress_analysis = self._track_plan_progress(
            success_plan,
            usage_data,
            engagement_data,
            business_data
        )

        # Identify blockers
        blockers = self._identify_plan_blockers(
            success_plan,
            progress_analysis,
            usage_data
        )

        # Calculate value realization
        value_analysis = self._calculate_value_realization(
            success_plan,
            usage_data,
            business_data
        )

        # Generate recommendations
        recommendations = self._generate_plan_recommendations(
            success_plan,
            progress_analysis,
            blockers
        )

        # Create action plan
        action_plan = self._create_success_action_plan(
            success_plan,
            progress_analysis,
            blockers
        )

        # Format response
        response = self._format_success_plan_report(
            success_plan,
            progress_analysis,
            value_analysis,
            blockers,
            recommendations,
            action_plan
        )

        state["agent_response"] = response
        state["success_plan_stage"] = success_plan["current_stage"]
        state["plan_progress_percentage"] = progress_analysis["overall_progress"]
        state["milestones_completed"] = progress_analysis["milestones_completed"]
        state["value_realized_percentage"] = value_analysis.get("value_realized_pct", 0)
        state["success_plan"] = success_plan
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "success_plan_management_completed",
            customer_id=customer_id,
            plan_stage=success_plan["current_stage"],
            progress=progress_analysis["overall_progress"]
        )

        return state

    def _create_success_plan(
        self,
        customer_metadata: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create new success plan.

        Args:
            customer_metadata: Customer profile data
            business_data: Business and contract data

        Returns:
            New success plan
        """
        tier = customer_metadata.get("tier", "standard")
        industry = customer_metadata.get("industry", "general")

        # Define business objectives based on tier and industry
        objectives = self._define_business_objectives(tier, industry, business_data)

        # Create milestones
        milestones = self._create_milestones(objectives, tier)

        # Define success criteria
        success_criteria = self._define_success_criteria(objectives, tier)

        # Set value metrics
        value_metrics = self._set_value_metrics(objectives, business_data)

        return {
            "plan_id": f"plan_{customer_metadata.get('customer_id', 'new')}_{int(datetime.now(UTC).timestamp())}",
            "created_date": datetime.now(UTC).isoformat(),
            "current_stage": "planning",
            "business_objectives": objectives,
            "success_criteria": success_criteria,
            "milestones": milestones,
            "value_metrics": value_metrics,
            "target_completion_date": (datetime.now(UTC) + timedelta(days=180)).isoformat(),
            "stakeholders": [],
            "status": "active"
        }

    def _define_business_objectives(
        self,
        tier: str,
        industry: str,
        business_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Define business objectives for success plan."""
        objectives = []

        # Primary objective based on tier
        if tier == "enterprise":
            objectives.append({
                "category": "strategic_transformation",
                "objective": f"Enable strategic business transformation in {industry}",
                "priority": "critical",
                "target_date": (datetime.now(UTC) + timedelta(days=180)).isoformat()
            })
        else:
            objectives.append({
                "category": "operational_efficiency",
                "objective": "Streamline operations and improve team productivity",
                "priority": "high",
                "target_date": (datetime.now(UTC) + timedelta(days=90)).isoformat()
            })

        # User adoption objective
        objectives.append({
            "category": "user_adoption",
            "objective": "Achieve 80%+ user adoption across licensed seats",
            "priority": "high",
            "target_date": (datetime.now(UTC) + timedelta(days=60)).isoformat()
        })

        # ROI objective
        contract_value = business_data.get("contract_value", 50000)
        objectives.append({
            "category": "cost_reduction",
            "objective": f"Realize 3x ROI (${contract_value * 3:,}) through efficiency gains",
            "priority": "medium",
            "target_date": (datetime.now(UTC) + timedelta(days=120)).isoformat()
        })

        return objectives

    def _create_milestones(
        self,
        objectives: List[Dict[str, Any]],
        tier: str
    ) -> List[Dict[str, Any]]:
        """Create milestones for success plan."""
        milestones = []

        # 30-day milestones
        milestones.append({
            "name": "Onboarding Complete",
            "type": "onboarding_complete",
            "target_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
            "criteria": "All users trained and actively using platform",
            "status": "pending",
            "completion_date": None
        })

        # 60-day milestones
        milestones.append({
            "name": "First Value Realized",
            "type": "first_value_realized",
            "target_date": (datetime.now(UTC) + timedelta(days=60)).isoformat(),
            "criteria": "Measurable efficiency improvement or time savings",
            "status": "pending",
            "completion_date": None
        })

        # 90-day milestones
        milestones.append({
            "name": "Adoption Target Met",
            "type": "adoption_target_met",
            "target_date": (datetime.now(UTC) + timedelta(days=90)).isoformat(),
            "criteria": "80%+ user adoption and 60%+ feature adoption",
            "status": "pending",
            "completion_date": None
        })

        # 120-day milestones
        if tier in ["enterprise", "premium"]:
            milestones.append({
                "name": "ROI Threshold Achieved",
                "type": "roi_threshold_achieved",
                "target_date": (datetime.now(UTC) + timedelta(days=120)).isoformat(),
                "criteria": "Documented 2x+ return on investment",
                "status": "pending",
                "completion_date": None
            })

        return milestones

    def _define_success_criteria(
        self,
        objectives: List[Dict[str, Any]],
        tier: str
    ) -> List[Dict[str, Any]]:
        """Define success criteria."""
        criteria = [
            {
                "metric": "User Adoption Rate",
                "target": "80%",
                "current": "0%",
                "status": "not_started"
            },
            {
                "metric": "Feature Adoption",
                "target": "60%",
                "current": "0%",
                "status": "not_started"
            },
            {
                "metric": "Time to Value",
                "target": "< 60 days",
                "current": "pending",
                "status": "not_started"
            },
            {
                "metric": "Customer Satisfaction (NPS)",
                "target": "8+",
                "current": "pending",
                "status": "not_started"
            }
        ]

        if tier in ["enterprise", "premium"]:
            criteria.append({
                "metric": "ROI Multiple",
                "target": "3x",
                "current": "pending",
                "status": "not_started"
            })

        return criteria

    def _set_value_metrics(
        self,
        objectives: List[Dict[str, Any]],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Set value metrics to track."""
        contract_value = business_data.get("contract_value", 50000)

        return {
            "target_roi_multiple": 3.0,
            "target_time_savings_hours": 500,
            "target_cost_reduction": contract_value * 0.5,
            "target_revenue_impact": contract_value * 2.0,
            "target_user_adoption": 80,
            "target_nps": 8
        }

    def _update_success_plan(
        self,
        existing_plan: Dict[str, Any],
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing success plan with current progress."""
        # Update success criteria with current values
        for criterion in existing_plan.get("success_criteria", []):
            metric = criterion["metric"]

            if metric == "User Adoption Rate":
                active_users = usage_data.get("active_users", 0)
                total_users = usage_data.get("total_users", 1)
                current_adoption = int((active_users / total_users * 100)) if total_users > 0 else 0
                criterion["current"] = f"{current_adoption}%"
                criterion["status"] = "on_track" if current_adoption >= 60 else "needs_attention"

            elif metric == "Feature Adoption":
                features_used = len(usage_data.get("features_used", []))
                total_features = usage_data.get("total_features_available", 10)
                feature_adoption = int((features_used / total_features * 100)) if total_features > 0 else 0
                criterion["current"] = f"{feature_adoption}%"
                criterion["status"] = "on_track" if feature_adoption >= 50 else "needs_attention"

            elif metric == "Customer Satisfaction (NPS)":
                nps = engagement_data.get("nps_score", 0)
                criterion["current"] = str(nps)
                criterion["status"] = "on_track" if nps >= 7 else "needs_attention"

        # Update milestone completion
        for milestone in existing_plan.get("milestones", []):
            if milestone["status"] == "pending":
                # Check if milestone criteria met
                milestone_met = self._check_milestone_completion(
                    milestone,
                    usage_data,
                    engagement_data
                )

                if milestone_met:
                    milestone["status"] = "completed"
                    milestone["completion_date"] = datetime.now(UTC).isoformat()

        # Update plan stage
        existing_plan["current_stage"] = self._determine_current_stage(existing_plan)
        existing_plan["last_updated"] = datetime.now(UTC).isoformat()

        return existing_plan

    def _check_milestone_completion(
        self,
        milestone: Dict[str, Any],
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> bool:
        """Check if milestone criteria are met."""
        milestone_type = milestone.get("type")

        if milestone_type == "adoption_target_met":
            active_users = usage_data.get("active_users", 0)
            total_users = usage_data.get("total_users", 1)
            adoption = (active_users / total_users * 100) if total_users > 0 else 0
            return adoption >= 80

        elif milestone_type == "first_value_realized":
            # Check if automation or significant usage exists
            automation_rules = usage_data.get("automation_rules_active", 0)
            return automation_rules >= 1

        # Default to not completed
        return False

    def _determine_current_stage(self, plan: Dict[str, Any]) -> str:
        """Determine current stage of success plan."""
        created_date = datetime.fromisoformat(plan["created_date"].replace('Z', '+00:00'))
        days_since_creation = (datetime.now(UTC) - created_date).days

        if days_since_creation <= 30:
            return "planning"
        elif days_since_creation <= 120:
            return "execution"
        elif days_since_creation <= 180:
            return "optimization"
        else:
            return "renewal"

    def _track_plan_progress(
        self,
        success_plan: Dict[str, Any],
        usage_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track progress against success plan."""
        # Count completed milestones
        milestones = success_plan.get("milestones", [])
        completed_milestones = sum(1 for m in milestones if m["status"] == "completed")
        total_milestones = len(milestones)

        # Calculate criteria progress
        criteria = success_plan.get("success_criteria", [])
        on_track_criteria = sum(1 for c in criteria if c.get("status") == "on_track")
        total_criteria = len(criteria)

        # Overall progress
        milestone_progress = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        criteria_progress = (on_track_criteria / total_criteria * 100) if total_criteria > 0 else 0
        overall_progress = int((milestone_progress + criteria_progress) / 2)

        # Determine status
        if overall_progress >= 75:
            status = "on_track"
        elif overall_progress >= 50:
            status = "needs_attention"
        else:
            status = "at_risk"

        return {
            "overall_progress": overall_progress,
            "milestones_completed": completed_milestones,
            "total_milestones": total_milestones,
            "milestone_completion_rate": int(milestone_progress),
            "criteria_on_track": on_track_criteria,
            "total_criteria": total_criteria,
            "criteria_success_rate": int(criteria_progress),
            "status": status
        }

    def _identify_plan_blockers(
        self,
        success_plan: Dict[str, Any],
        progress_analysis: Dict[str, Any],
        usage_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify blockers to success plan execution."""
        blockers = []

        # Check for delayed milestones
        for milestone in success_plan.get("milestones", []):
            if milestone["status"] == "pending":
                target_date = datetime.fromisoformat(milestone["target_date"].replace('Z', '+00:00'))
                if datetime.now(UTC) > target_date:
                    blockers.append({
                        "blocker": f"Delayed milestone: {milestone['name']}",
                        "severity": "high",
                        "impact": "Plan timeline at risk"
                    })

        # Check for low adoption
        active_users = usage_data.get("active_users", 0)
        total_users = usage_data.get("total_users", 1)
        adoption_rate = (active_users / total_users * 100) if total_users > 0 else 0

        if adoption_rate < 50:
            blockers.append({
                "blocker": f"Low user adoption ({int(adoption_rate)}%)",
                "severity": "high",
                "impact": "Success criteria at risk"
            })

        # Check overall progress
        if progress_analysis["status"] == "at_risk":
            blockers.append({
                "blocker": "Overall plan progress below target",
                "severity": "critical",
                "impact": "Success plan execution needs intervention"
            })

        return blockers

    def _calculate_value_realization(
        self,
        success_plan: Dict[str, Any],
        usage_data: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate value realized against plan targets."""
        value_metrics = success_plan.get("value_metrics", {})

        # Calculate actual values
        automation_rules = usage_data.get("automation_rules_active", 0)
        time_saved_hours = automation_rules * 40  # Est. 40 hours per automation

        contract_value = business_data.get("contract_value", 50000)
        estimated_value_realized = time_saved_hours * 50  # $50/hour

        # Calculate percentages
        target_time_savings = value_metrics.get("target_time_savings_hours", 500)
        time_savings_pct = int((time_saved_hours / target_time_savings * 100)) if target_time_savings > 0 else 0

        target_roi = value_metrics.get("target_roi_multiple", 3.0)
        current_roi_multiple = estimated_value_realized / contract_value if contract_value > 0 else 0
        roi_pct = int((current_roi_multiple / target_roi * 100))

        value_realized_pct = int((time_savings_pct + roi_pct) / 2)

        return {
            "value_realized_pct": value_realized_pct,
            "time_saved_hours": time_saved_hours,
            "target_time_savings": target_time_savings,
            "estimated_value": estimated_value_realized,
            "current_roi_multiple": round(current_roi_multiple, 2),
            "target_roi_multiple": target_roi,
            "on_track_for_roi": current_roi_multiple >= (target_roi * 0.5)
        }

    def _generate_plan_recommendations(
        self,
        success_plan: Dict[str, Any],
        progress_analysis: Dict[str, Any],
        blockers: List[Dict[str, str]]
    ) -> List[str]:
        """Generate recommendations for success plan."""
        recommendations = []

        if progress_analysis["status"] in ["needs_attention", "at_risk"]:
            recommendations.append("Schedule success plan review with customer stakeholders")

        if progress_analysis["milestone_completion_rate"] < 50:
            recommendations.append("Focus on completing next milestone - provide targeted support")

        if blockers:
            recommendations.append(f"Address {len(blockers)} identified blockers to get plan back on track")

        if progress_analysis["criteria_success_rate"] >= 75:
            recommendations.append("Strong progress - consider accelerating advanced objectives")

        return recommendations[:4]

    def _create_success_action_plan(
        self,
        success_plan: Dict[str, Any],
        progress_analysis: Dict[str, Any],
        blockers: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Create action plan for success plan execution."""
        actions = []

        # Address critical blockers
        critical_blockers = [b for b in blockers if b["severity"] == "critical"]
        if critical_blockers:
            actions.append({
                "action": "Address critical blockers with customer",
                "owner": "CSM + CS Manager",
                "timeline": "This week",
                "priority": "critical"
            })

        # Review if at risk
        if progress_analysis["status"] == "at_risk":
            actions.append({
                "action": "Conduct success plan review and reset priorities",
                "owner": "CSM",
                "timeline": "Within 3 days",
                "priority": "high"
            })

        # Focus on next milestone
        pending_milestones = [m for m in success_plan.get("milestones", []) if m["status"] == "pending"]
        if pending_milestones:
            next_milestone = pending_milestones[0]
            actions.append({
                "action": f"Drive completion of next milestone: {next_milestone['name']}",
                "owner": "CSM",
                "timeline": "Next 2 weeks",
                "priority": "high"
            })

        # Regular check-in
        actions.append({
            "action": "Weekly success plan progress check-in with customer",
            "owner": "CSM",
            "timeline": "Ongoing",
            "priority": "medium"
        })

        return actions[:5]

    def _format_success_plan_report(
        self,
        success_plan: Dict[str, Any],
        progress_analysis: Dict[str, Any],
        value_analysis: Dict[str, Any],
        blockers: List[Dict[str, str]],
        recommendations: List[str],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format success plan report."""
        stage = success_plan["current_stage"]
        progress = progress_analysis["overall_progress"]
        status = progress_analysis["status"]

        status_emoji = {
            "on_track": "???",
            "needs_attention": "??????",
            "at_risk": "????"
        }

        stage_emoji = {
            "planning": "????",
            "execution": "????",
            "optimization": "??????",
            "renewal": "????"
        }

        report = f"""**{stage_emoji.get(stage, '????')} Customer Success Plan**

**Plan Stage:** {stage.title()}
**Overall Progress:** {progress}% {status_emoji.get(status, '???')}
**Status:** {status.replace('_', ' ').title()}

**Business Objectives:**
"""

        for i, obj in enumerate(success_plan.get("business_objectives", [])[:3], 1):
            priority_icon = "????" if obj["priority"] == "critical" else "????" if obj["priority"] == "high" else "????"
            report += f"{i}. {obj['objective']} {priority_icon}\n"
            report += f"   Category: {obj['category'].replace('_', ' ').title()}\n"

        # Milestones
        report += f"\n**???? Milestones ({progress_analysis['milestones_completed']}/{progress_analysis['total_milestones']} completed):**\n"
        for milestone in success_plan.get("milestones", []):
            status_icon = "???" if milestone["status"] == "completed" else "???"
            target_date = datetime.fromisoformat(milestone["target_date"].replace('Z', '+00:00'))
            report += f"- {milestone['name']} {status_icon}\n"
            report += f"  Target: {target_date.strftime('%b %d, %Y')}\n"

        # Success Criteria
        report += f"\n**???? Success Criteria ({progress_analysis['criteria_on_track']}/{progress_analysis['total_criteria']} on track):**\n"
        for criterion in success_plan.get("success_criteria", []):
            status_icon = "???" if criterion.get("status") == "on_track" else "??????" if criterion.get("status") == "needs_attention" else "???"
            report += f"- {criterion['metric']}: {criterion['current']} / {criterion['target']} {status_icon}\n"

        # Value Realization
        report += f"\n**???? Value Realization:**\n"
        report += f"- Progress: {value_analysis['value_realized_pct']}%\n"
        report += f"- Time Saved: {value_analysis['time_saved_hours']} / {value_analysis['target_time_savings']} hours\n"
        report += f"- Current ROI: {value_analysis['current_roi_multiple']}x / {value_analysis['target_roi_multiple']}x target\n"
        report += f"- Estimated Value: ${value_analysis['estimated_value']:,}\n"

        # Blockers
        if blockers:
            report += "\n**???? Blockers:**\n"
            for i, blocker in enumerate(blockers[:3], 1):
                severity_icon = "????" if blocker["severity"] == "critical" else "????" if blocker["severity"] == "high" else "????"
                report += f"{i}. **{blocker['blocker']}** {severity_icon}\n"
                report += f"   Impact: {blocker['impact']}\n"

        # Recommendations
        if recommendations:
            report += "\n**???? Recommendations:**\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"

        # Action Plan
        if action_plan:
            report += "\n**??? Action Plan:**\n"
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
        print("Testing Success Plan Agent (TASK-2065)")
        print("=" * 70)

        agent = SuccessPlanAgent()

        # Test 1: New success plan
        print("\n\nTest 1: Create New Success Plan")
        print("-" * 70)

        state1 = create_initial_state(
            "Create customer success plan",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {
                    "tier": "enterprise",
                    "industry": "healthcare"
                }
            }
        )
        state1["entities"] = {
            "business_data": {
                "contract_value": 120000
            },
            "usage_data": {
                "active_users": 0,
                "total_users": 100,
                "features_used": [],
                "total_features_available": 10,
                "automation_rules_active": 0
            },
            "engagement_data": {
                "nps_score": 0
            }
        }

        result1 = await agent.process(state1)

        print(f"Plan Stage: {result1['success_plan_stage']}")
        print(f"Progress: {result1['plan_progress_percentage']}%")
        print(f"Milestones Completed: {result1['milestones_completed']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Update existing plan with progress
        print("\n\n" + "=" * 70)
        print("Test 2: Update Success Plan with Progress")
        print("-" * 70)

        existing_plan = {
            "plan_id": "plan_123",
            "created_date": (datetime.now(UTC) - timedelta(days=45)).isoformat(),
            "current_stage": "execution",
            "business_objectives": [
                {
                    "category": "operational_efficiency",
                    "objective": "Streamline operations and improve team productivity",
                    "priority": "high",
                    "target_date": (datetime.now(UTC) + timedelta(days=45)).isoformat()
                }
            ],
            "success_criteria": [
                {"metric": "User Adoption Rate", "target": "80%", "current": "0%", "status": "not_started"},
                {"metric": "Feature Adoption", "target": "60%", "current": "0%", "status": "not_started"}
            ],
            "milestones": [
                {
                    "name": "Onboarding Complete",
                    "type": "onboarding_complete",
                    "target_date": (datetime.now(UTC) - timedelta(days=15)).isoformat(),
                    "criteria": "All users trained",
                    "status": "pending",
                    "completion_date": None
                }
            ],
            "value_metrics": {
                "target_roi_multiple": 3.0,
                "target_time_savings_hours": 500
            },
            "status": "active"
        }

        state2 = create_initial_state(
            "Update success plan",
            context={
                "customer_id": "cust_premium_002",
                "customer_metadata": {
                    "tier": "premium"
                }
            }
        )
        state2["entities"] = {
            "success_plan": existing_plan,
            "business_data": {
                "contract_value": 60000
            },
            "usage_data": {
                "active_users": 65,
                "total_users": 75,
                "features_used": ["reporting", "analytics", "automation", "dashboards"],
                "total_features_available": 8,
                "automation_rules_active": 3
            },
            "engagement_data": {
                "nps_score": 8
            }
        }

        result2 = await agent.process(state2)

        print(f"Plan Stage: {result2['success_plan_stage']}")
        print(f"Progress: {result2['plan_progress_percentage']}%")
        print(f"Value Realized: {result2['value_realized_percentage']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
