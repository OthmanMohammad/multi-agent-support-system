"""
Automation Coach Agent - TASK-2034

Identifies automation opportunities, recommends automation rules, builds workflows,
and measures time savings to drive efficiency and product stickiness.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("automation_coach", tier="revenue", category="customer_success")
class AutomationCoachAgent(BaseAgent):
    """
    Automation Coach Agent.

    Drives automation adoption by:
    - Identifying repetitive manual tasks
    - Recommending automation rules and workflows
    - Calculating time savings from automation
    - Tracking automation ROI
    - Providing automation templates
    - Measuring automation maturity
    """

    # Automation opportunity types
    OPPORTUNITY_TYPES = {
        "task_assignment": {
            "complexity": "low",
            "time_savings_per_instance": 5,  # minutes
            "setup_time": 15,  # minutes
        },
        "status_updates": {"complexity": "low", "time_savings_per_instance": 3, "setup_time": 10},
        "notifications": {"complexity": "low", "time_savings_per_instance": 2, "setup_time": 10},
        "data_sync": {"complexity": "medium", "time_savings_per_instance": 15, "setup_time": 30},
        "approval_workflows": {
            "complexity": "medium",
            "time_savings_per_instance": 20,
            "setup_time": 45,
        },
        "reporting": {"complexity": "medium", "time_savings_per_instance": 30, "setup_time": 60},
        "escalations": {"complexity": "low", "time_savings_per_instance": 10, "setup_time": 20},
        "data_transformation": {
            "complexity": "high",
            "time_savings_per_instance": 25,
            "setup_time": 90,
        },
    }

    # Automation maturity levels
    MATURITY_LEVELS = {
        "manual": {"score_range": (0, 20), "automation_count": 0},
        "basic": {"score_range": (21, 40), "automation_count": 5},
        "intermediate": {"score_range": (41, 65), "automation_count": 15},
        "advanced": {"score_range": (66, 85), "automation_count": 30},
        "expert": {"score_range": (86, 100), "automation_count": 50},
    }

    def __init__(self):
        config = AgentConfig(
            name="automation_coach",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            max_tokens=800,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="customer_success",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze automation opportunities and provide coaching.

        Args:
            state: Current agent state with workflow data

        Returns:
            Updated state with automation recommendations
        """
        self.logger.info("automation_coaching_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        workflow_data = state.get("entities", {}).get("workflow_data", {})
        customer_metadata = state.get("customer_metadata", {})
        current_automations = state.get("entities", {}).get("current_automations", [])

        self.logger.debug(
            "automation_coaching_details",
            customer_id=customer_id,
            current_automations=len(current_automations),
            manual_tasks=workflow_data.get("manual_task_count", 0),
        )

        # Analyze current automation state
        automation_analysis = self._analyze_automation_state(
            workflow_data, current_automations, customer_metadata
        )

        # Identify automation opportunities
        opportunities = self._identify_automation_opportunities(
            workflow_data, automation_analysis, customer_metadata
        )

        # Calculate ROI potential
        roi_analysis = self._calculate_automation_roi(opportunities, workflow_data)

        # Generate automation recommendations
        recommendations = self._generate_automation_recommendations(
            opportunities, automation_analysis, customer_metadata
        )

        # Create implementation roadmap
        roadmap = self._create_automation_roadmap(recommendations, automation_analysis)

        # Format response
        response = self._format_automation_report(
            automation_analysis, opportunities, roi_analysis, recommendations, roadmap
        )

        state["agent_response"] = response
        state["automation_maturity"] = automation_analysis["maturity_level"]
        state["automation_score"] = automation_analysis["automation_score"]
        state["automation_opportunities"] = len(opportunities)
        state["potential_time_savings_hours"] = roi_analysis["monthly_time_savings_hours"]
        state["automation_analysis"] = automation_analysis
        state["response_confidence"] = 0.89
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "automation_coaching_completed",
            customer_id=customer_id,
            maturity=automation_analysis["maturity_level"],
            opportunities=len(opportunities),
            time_savings=roi_analysis["monthly_time_savings_hours"],
        )

        return state

    def _analyze_automation_state(
        self,
        workflow_data: dict[str, Any],
        current_automations: list[dict[str, Any]],
        customer_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze current automation state.

        Args:
            workflow_data: Customer workflow metrics
            current_automations: Existing automation rules
            customer_metadata: Customer profile data

        Returns:
            Comprehensive automation analysis
        """
        automation_count = len(current_automations)
        workflow_data.get("total_workflows", 0)
        manual_tasks = workflow_data.get("manual_task_count", 0)
        automated_tasks = workflow_data.get("automated_task_count", 0)

        # Calculate automation coverage
        total_tasks = manual_tasks + automated_tasks
        automation_coverage = (automated_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate automation score (0-100)
        automation_score = self._calculate_automation_score(
            automation_count, automation_coverage, workflow_data
        )

        # Determine maturity level
        maturity_level = self._determine_maturity_level(automation_score, automation_count)

        # Categorize existing automations
        automations_by_type = self._categorize_automations(current_automations)

        # Calculate usage metrics
        avg_automation_runs = (
            sum(auto.get("run_count", 0) for auto in current_automations) / len(current_automations)
            if current_automations
            else 0
        )

        active_automations = sum(1 for auto in current_automations if auto.get("run_count", 0) > 0)

        # Identify gaps
        automation_gaps = self._identify_automation_gaps(automations_by_type, workflow_data)

        return {
            "automation_score": round(automation_score, 1),
            "maturity_level": maturity_level,
            "automation_count": automation_count,
            "active_automations": active_automations,
            "automation_coverage": round(automation_coverage, 1),
            "manual_tasks": manual_tasks,
            "automated_tasks": automated_tasks,
            "automations_by_type": automations_by_type,
            "avg_automation_runs": round(avg_automation_runs, 1),
            "automation_gaps": automation_gaps,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    def _calculate_automation_score(
        self, automation_count: int, automation_coverage: float, workflow_data: dict[str, Any]
    ) -> float:
        """Calculate overall automation score (0-100)."""
        # Weight factors
        count_score = min(automation_count / 50 * 100, 100)  # Max at 50 automations
        coverage_score = automation_coverage
        complexity_score = self._calculate_complexity_score(workflow_data)

        # Weighted average
        score = (count_score * 0.4) + (coverage_score * 0.4) + (complexity_score * 0.2)

        return min(score, 100)

    def _calculate_complexity_score(self, workflow_data: dict[str, Any]) -> float:
        """Calculate score based on automation complexity."""
        # Higher score for more complex automations
        conditional_automations = workflow_data.get("conditional_automations", 0)
        multi_step_automations = workflow_data.get("multi_step_automations", 0)

        complexity_points = (conditional_automations * 2) + (multi_step_automations * 3)
        return min(complexity_points / 30 * 100, 100)

    def _determine_maturity_level(self, score: float, automation_count: int) -> str:
        """Determine automation maturity level."""
        for level, criteria in self.MATURITY_LEVELS.items():
            score_min, score_max = criteria["score_range"]
            if score_min <= score <= score_max:
                return level
        return "manual"

    def _categorize_automations(self, current_automations: list[dict[str, Any]]) -> dict[str, int]:
        """Categorize existing automations by type."""
        categorized = dict.fromkeys(self.OPPORTUNITY_TYPES.keys(), 0)

        for automation in current_automations:
            auto_type = automation.get("type", "unknown")
            if auto_type in categorized:
                categorized[auto_type] += 1

        return categorized

    def _identify_automation_gaps(
        self, automations_by_type: dict[str, int], workflow_data: dict[str, Any]
    ) -> list[str]:
        """Identify gaps in automation coverage."""
        gaps = []

        # Check for missing automation types
        if automations_by_type.get("task_assignment", 0) == 0:
            gaps.append("No automated task assignment - manual distribution")

        if automations_by_type.get("notifications", 0) < 3:
            gaps.append("Limited notification automation - manual follow-ups")

        if automations_by_type.get("approval_workflows", 0) == 0:
            gaps.append("No approval workflows - bottlenecks in process")

        if automations_by_type.get("reporting", 0) == 0:
            gaps.append("Manual reporting - time-intensive")

        if automations_by_type.get("escalations", 0) == 0:
            gaps.append("No automated escalations - delayed issue resolution")

        return gaps

    def _identify_automation_opportunities(
        self,
        workflow_data: dict[str, Any],
        automation_analysis: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Identify specific automation opportunities."""
        opportunities = []
        automations_by_type = automation_analysis["automations_by_type"]
        industry = customer_metadata.get("industry", "general")

        # Identify opportunities based on workflow patterns
        manual_tasks = workflow_data.get("manual_task_count", 0)

        # Task assignment opportunities
        if manual_tasks > 20 and automations_by_type.get("task_assignment", 0) < 2:
            opportunities.append(
                {
                    "type": "task_assignment",
                    "priority": "high",
                    "frequency_per_month": manual_tasks * 4,  # Weekly pattern
                    "description": "Automate task assignment based on workload or round-robin",
                    "use_case": f"Automatically assign incoming {industry} requests to available team members",
                    "complexity": self.OPPORTUNITY_TYPES["task_assignment"]["complexity"],
                    "estimated_setup_time": self.OPPORTUNITY_TYPES["task_assignment"]["setup_time"],
                }
            )

        # Status update opportunities
        if automations_by_type.get("status_updates", 0) < 3:
            opportunities.append(
                {
                    "type": "status_updates",
                    "priority": "high",
                    "frequency_per_month": 100,
                    "description": "Auto-update status based on conditions or time elapsed",
                    "use_case": "Mark tasks complete when all subtasks finished",
                    "complexity": self.OPPORTUNITY_TYPES["status_updates"]["complexity"],
                    "estimated_setup_time": self.OPPORTUNITY_TYPES["status_updates"]["setup_time"],
                }
            )

        # Notification opportunities
        if automations_by_type.get("notifications", 0) < 5:
            opportunities.append(
                {
                    "type": "notifications",
                    "priority": "medium",
                    "frequency_per_month": 200,
                    "description": "Set up automated notifications for key events",
                    "use_case": "Notify stakeholders when milestones reached or deadlines approach",
                    "complexity": self.OPPORTUNITY_TYPES["notifications"]["complexity"],
                    "estimated_setup_time": self.OPPORTUNITY_TYPES["notifications"]["setup_time"],
                }
            )

        # Approval workflow opportunities
        approval_processes = workflow_data.get("approval_process_count", 0)
        if approval_processes > 5 and automations_by_type.get("approval_workflows", 0) == 0:
            opportunities.append(
                {
                    "type": "approval_workflows",
                    "priority": "high",
                    "frequency_per_month": approval_processes * 4,
                    "description": "Create approval workflows with escalation paths",
                    "use_case": f"Route {industry} approvals to appropriate stakeholders based on criteria",
                    "complexity": self.OPPORTUNITY_TYPES["approval_workflows"]["complexity"],
                    "estimated_setup_time": self.OPPORTUNITY_TYPES["approval_workflows"][
                        "setup_time"
                    ],
                }
            )

        # Reporting opportunities
        if automations_by_type.get("reporting", 0) < 2:
            opportunities.append(
                {
                    "type": "reporting",
                    "priority": "medium",
                    "frequency_per_month": 20,
                    "description": "Automate recurring report generation and delivery",
                    "use_case": "Weekly executive dashboards delivered automatically",
                    "complexity": self.OPPORTUNITY_TYPES["reporting"]["complexity"],
                    "estimated_setup_time": self.OPPORTUNITY_TYPES["reporting"]["setup_time"],
                }
            )

        # Escalation opportunities
        if automations_by_type.get("escalations", 0) == 0:
            opportunities.append(
                {
                    "type": "escalations",
                    "priority": "high",
                    "frequency_per_month": 30,
                    "description": "Auto-escalate overdue or high-priority items",
                    "use_case": "Escalate items stuck in status for >3 days",
                    "complexity": self.OPPORTUNITY_TYPES["escalations"]["complexity"],
                    "estimated_setup_time": self.OPPORTUNITY_TYPES["escalations"]["setup_time"],
                }
            )

        # Sort by priority and potential impact
        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(
            key=lambda x: (priority_order.get(x["priority"], 2), -x["frequency_per_month"])
        )

        return opportunities[:8]

    def _calculate_automation_roi(
        self, opportunities: list[dict[str, Any]], workflow_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate ROI from automation opportunities."""
        total_monthly_savings_minutes = 0
        total_setup_time_minutes = 0

        for opp in opportunities:
            opp_type = opp["type"]
            frequency = opp["frequency_per_month"]

            time_savings_per_instance = self.OPPORTUNITY_TYPES[opp_type][
                "time_savings_per_instance"
            ]
            setup_time = self.OPPORTUNITY_TYPES[opp_type]["setup_time"]

            monthly_savings = frequency * time_savings_per_instance
            total_monthly_savings_minutes += monthly_savings
            total_setup_time_minutes += setup_time

        # Convert to hours
        monthly_time_savings_hours = round(total_monthly_savings_minutes / 60, 1)
        total_setup_hours = round(total_setup_time_minutes / 60, 1)

        # Calculate payback period (months)
        payback_months = (
            (total_setup_hours / monthly_time_savings_hours)
            if monthly_time_savings_hours > 0
            else 0
        )

        # Calculate annual savings
        annual_savings_hours = monthly_time_savings_hours * 12

        # Estimate cost savings (assume $50/hour blended rate)
        annual_cost_savings = int(annual_savings_hours * 50)

        return {
            "monthly_time_savings_hours": monthly_time_savings_hours,
            "annual_time_savings_hours": round(annual_savings_hours, 1),
            "total_setup_hours": total_setup_hours,
            "payback_months": round(payback_months, 1),
            "annual_cost_savings": annual_cost_savings,
            "roi_percentage": int((annual_cost_savings / max(total_setup_hours * 50, 1)) * 100),
        }

    def _generate_automation_recommendations(
        self,
        opportunities: list[dict[str, Any]],
        automation_analysis: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate prioritized automation recommendations."""
        recommendations = []

        for opp in opportunities[:6]:
            opp_info = self.OPPORTUNITY_TYPES[opp["type"]]

            recommendation = {
                "automation_type": opp["type"],
                "priority": opp["priority"],
                "description": opp["description"],
                "use_case": opp["use_case"],
                "implementation_steps": self._get_implementation_steps(opp["type"]),
                "complexity": opp["complexity"],
                "estimated_setup_time": f"{opp['estimated_setup_time']} minutes",
                "time_savings_per_month": f"{round(opp['frequency_per_month'] * opp_info['time_savings_per_instance'] / 60, 1)} hours",
            }

            recommendations.append(recommendation)

        return recommendations

    def _get_implementation_steps(self, automation_type: str) -> list[str]:
        """Get implementation steps for automation type."""
        steps_map = {
            "task_assignment": [
                "Define assignment criteria (workload, skills, round-robin)",
                "Create automation rule with trigger condition",
                "Test with sample tasks before activating",
            ],
            "status_updates": [
                "Identify status transition conditions",
                "Set up automation rule with status change action",
                "Configure notifications for status changes",
            ],
            "notifications": [
                "Define notification triggers and recipients",
                "Customize notification templates",
                "Set up delivery channels (email, in-app, etc.)",
            ],
            "approval_workflows": [
                "Map approval process and stakeholders",
                "Create multi-step workflow with conditions",
                "Configure escalation paths for delays",
            ],
            "reporting": [
                "Design report template and data sources",
                "Schedule report generation frequency",
                "Configure automated delivery to recipients",
            ],
            "escalations": [
                "Define escalation criteria (time, priority, etc.)",
                "Identify escalation recipients and hierarchy",
                "Create automation with escalation actions",
            ],
        }

        return steps_map.get(
            automation_type, ["Define requirements", "Build automation", "Test and deploy"]
        )

    def _create_automation_roadmap(
        self, recommendations: list[dict[str, Any]], automation_analysis: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Create phased automation implementation roadmap."""
        roadmap = {"week_1": [], "week_2_4": [], "month_2_3": []}

        # Week 1: Quick wins (low complexity, high priority)
        for rec in recommendations:
            if rec["complexity"] == "low" and rec["priority"] == "high":
                roadmap["week_1"].append(
                    f"{rec['automation_type'].replace('_', ' ').title()}: {rec['description']}"
                )

        # Weeks 2-4: Medium complexity
        for rec in recommendations:
            if rec["complexity"] == "medium":
                roadmap["week_2_4"].append(
                    f"{rec['automation_type'].replace('_', ' ').title()}: {rec['description']}"
                )

        # Months 2-3: High complexity and optimization
        for rec in recommendations:
            if rec["complexity"] == "high":
                roadmap["month_2_3"].append(
                    f"{rec['automation_type'].replace('_', ' ').title()}: {rec['description']}"
                )

        # Limit items per phase
        roadmap["week_1"] = roadmap["week_1"][:3]
        roadmap["week_2_4"] = roadmap["week_2_4"][:4]
        roadmap["month_2_3"] = roadmap["month_2_3"][:3]

        return roadmap

    def _format_automation_report(
        self,
        automation_analysis: dict[str, Any],
        opportunities: list[dict[str, Any]],
        roi_analysis: dict[str, Any],
        recommendations: list[dict[str, Any]],
        roadmap: dict[str, list[str]],
    ) -> str:
        """Format automation coaching report."""
        maturity = automation_analysis["maturity_level"]
        score = automation_analysis["automation_score"]

        maturity_emoji = {
            "manual": "????",
            "basic": "????",
            "intermediate": "???",
            "advanced": "???",
            "expert": "????",
        }

        report = f"""**{maturity_emoji.get(maturity, "????")} Automation Coaching Report**

**Maturity Level:** {maturity.upper()}
**Automation Score:** {score}/100
**Active Automations:** {automation_analysis["active_automations"]}/{automation_analysis["automation_count"]}
**Coverage:** {automation_analysis["automation_coverage"]}% of tasks automated

**Current State:**
- Manual Tasks: {automation_analysis["manual_tasks"]}
- Automated Tasks: {automation_analysis["automated_tasks"]}
- Avg Automation Runs: {automation_analysis["avg_automation_runs"]}/month

**Automation Gaps:**
"""

        for gap in automation_analysis["automation_gaps"][:4]:
            report += f"- ?????? {gap}\n"

        # ROI Analysis
        report += "\n**???? Automation ROI Opportunity:**\n"
        report += f"- Monthly Time Savings: {roi_analysis['monthly_time_savings_hours']} hours\n"
        report += f"- Annual Time Savings: {roi_analysis['annual_time_savings_hours']} hours\n"
        report += f"- Setup Investment: {roi_analysis['total_setup_hours']} hours\n"
        report += f"- Payback Period: {roi_analysis['payback_months']} months\n"
        report += f"- Annual Cost Savings: ${roi_analysis['annual_cost_savings']:,}\n"
        report += f"- ROI: {roi_analysis['roi_percentage']}%\n"

        # Top opportunities
        if opportunities:
            report += "\n**???? Top Automation Opportunities:**\n"
            for i, opp in enumerate(opportunities[:5], 1):
                priority_icon = "????" if opp["priority"] == "high" else "????"
                report += f"\n{i}. **{opp['type'].replace('_', ' ').title()}** {priority_icon}\n"
                report += f"   - {opp['description']}\n"
                report += f"   - Use Case: {opp['use_case']}\n"
                report += f"   - Complexity: {opp['complexity'].title()}\n"
                report += f"   - Frequency: {opp['frequency_per_month']}/month\n"

        # Implementation recommendations
        if recommendations:
            report += "\n**???? Implementation Guide:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                report += f"\n**{i}. {rec['automation_type'].replace('_', ' ').title()}**\n"
                report += f"- Setup Time: {rec['estimated_setup_time']}\n"
                report += f"- Monthly Savings: {rec['time_savings_per_month']}\n"
                report += "Steps:\n"
                for step in rec["implementation_steps"]:
                    report += f"  ??? {step}\n"

        # Roadmap
        report += "\n**??????? Implementation Roadmap:**\n"
        for phase, items in roadmap.items():
            if items:
                phase_label = (
                    phase.replace("_", " ")
                    .title()
                    .replace("Week", "Week")
                    .replace("Month", "Months")
                )
                report += f"\n**{phase_label}:**\n"
                for item in items:
                    report += f"- {item}\n"

        return report


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Automation Coach Agent (TASK-2034)")
        print("=" * 70)

        agent = AutomationCoachAgent()

        # Test 1: Low automation maturity
        print("\n\nTest 1: Manual/Basic Automation")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze automation opportunities",
            context={
                "customer_id": "cust_manual",
                "customer_metadata": {"plan": "premium", "industry": "healthcare"},
            },
        )
        state1["entities"] = {
            "workflow_data": {
                "total_workflows": 20,
                "manual_task_count": 150,
                "automated_task_count": 10,
                "approval_process_count": 12,
                "conditional_automations": 0,
                "multi_step_automations": 0,
            },
            "current_automations": [
                {"type": "notifications", "run_count": 45},
                {"type": "status_updates", "run_count": 20},
            ],
        }

        result1 = await agent.process(state1)

        print(f"Maturity: {result1['automation_maturity']}")
        print(f"Score: {result1['automation_score']}/100")
        print(f"Opportunities: {result1['automation_opportunities']}")
        print(f"Potential Savings: {result1['potential_time_savings_hours']} hours/month")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Advanced automation
        print("\n\n" + "=" * 70)
        print("Test 2: Advanced Automation")
        print("-" * 70)

        state2 = create_initial_state(
            "Review automation status",
            context={
                "customer_id": "cust_advanced",
                "customer_metadata": {"plan": "enterprise", "industry": "technology"},
            },
        )
        state2["entities"] = {
            "workflow_data": {
                "total_workflows": 50,
                "manual_task_count": 50,
                "automated_task_count": 200,
                "approval_process_count": 8,
                "conditional_automations": 15,
                "multi_step_automations": 10,
            },
            "current_automations": [
                {"type": "task_assignment", "run_count": 120},
                {"type": "status_updates", "run_count": 200},
                {"type": "notifications", "run_count": 350},
                {"type": "approval_workflows", "run_count": 80},
                {"type": "reporting", "run_count": 40},
                {"type": "escalations", "run_count": 25},
            ]
            + [{"type": "notifications", "run_count": 50} for _ in range(20)],
        }

        result2 = await agent.process(state2)

        print(f"Maturity: {result2['automation_maturity']}")
        print(f"Score: {result2['automation_score']}/100")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
