"""
Kickoff Facilitator Agent - TASK-2022

Facilitates kickoff calls, sets clear expectations, and creates comprehensive success plans.
Ensures alignment on goals, timelines, and success criteria.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("kickoff_facilitator", tier="revenue", category="customer_success")
class KickoffFacilitatorAgent(BaseAgent):
    """
    Kickoff Facilitator Agent.

    Manages kickoff process:
    - Pre-kickoff preparation and stakeholder identification
    - Kickoff meeting facilitation and documentation
    - Success plan creation with measurable goals
    - Timeline establishment and milestone definition
    - Stakeholder alignment and role clarification
    """

    # Success criteria templates
    SUCCESS_CRITERIA_CATEGORIES = [
        "user_adoption",
        "feature_utilization",
        "business_outcomes",
        "technical_integration",
        "team_proficiency"
    ]

    # Kickoff readiness checklist
    READINESS_CHECKLIST = [
        "stakeholders_identified",
        "technical_contacts_confirmed",
        "goals_documented",
        "current_process_mapped",
        "timeline_agreed"
    ]

    def __init__(self):
        config = AgentConfig(
            name="kickoff_facilitator",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=500,
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
        Facilitate kickoff process and create success plan.

        Args:
            state: Current agent state with kickoff data

        Returns:
            Updated state with kickoff status and success plan
        """
        self.logger.info("kickoff_facilitation_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        kickoff_data = state.get("entities", {}).get("kickoff_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "kickoff_facilitation_details",
            customer_id=customer_id,
            kickoff_status=kickoff_data.get("status"),
            stakeholders_count=len(kickoff_data.get("stakeholders", []))
        )

        # Analyze kickoff readiness or status
        kickoff_analysis = self._analyze_kickoff_status(kickoff_data, customer_metadata)

        # Generate success plan
        success_plan = self._generate_success_plan(kickoff_data, customer_metadata)

        # Create action items
        action_items = self._create_action_items(kickoff_analysis, success_plan)

        # Build response
        response = self._format_kickoff_report(
            kickoff_analysis,
            success_plan,
            action_items
        )

        state["agent_response"] = response
        state["kickoff_status"] = kickoff_analysis["status"]
        state["kickoff_readiness"] = kickoff_analysis.get("readiness_score", 0)
        state["success_plan"] = success_plan
        state["kickoff_analysis"] = kickoff_analysis
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "kickoff_facilitation_completed",
            customer_id=customer_id,
            kickoff_status=kickoff_analysis["status"],
            readiness_score=kickoff_analysis.get("readiness_score", 0)
        )

        return state

    def _analyze_kickoff_status(
        self,
        kickoff_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze kickoff readiness or completion status.

        Args:
            kickoff_data: Kickoff meeting and preparation data
            customer_metadata: Customer profile data

        Returns:
            Kickoff status analysis
        """
        kickoff_status = kickoff_data.get("status", "not_scheduled")
        stakeholders = kickoff_data.get("stakeholders", [])
        goals_defined = kickoff_data.get("goals_defined", False)
        technical_contacts = kickoff_data.get("technical_contacts", [])

        # Check readiness checklist
        checklist_items = kickoff_data.get("readiness_checklist", {})
        completed_items = sum(1 for item in self.READINESS_CHECKLIST
                            if checklist_items.get(item, False))
        readiness_score = int((completed_items / len(self.READINESS_CHECKLIST)) * 100)

        # Identify gaps
        gaps = []
        if not stakeholders or len(stakeholders) < 2:
            gaps.append({
                "gap": "Insufficient stakeholder engagement",
                "impact": "May lack executive sponsorship"
            })
        if not technical_contacts:
            gaps.append({
                "gap": "No technical contacts identified",
                "impact": "Integration and migration will be delayed"
            })
        if not goals_defined:
            gaps.append({
                "gap": "Business goals not documented",
                "impact": "Cannot measure success or demonstrate value"
            })

        # Determine overall status
        if kickoff_status == "completed" and readiness_score >= 80:
            overall_status = "excellent"
        elif kickoff_status == "completed":
            overall_status = "completed_with_gaps"
        elif kickoff_status == "scheduled" and readiness_score >= 60:
            overall_status = "ready"
        elif kickoff_status == "scheduled":
            overall_status = "needs_preparation"
        else:
            overall_status = "not_ready"

        return {
            "status": overall_status,
            "kickoff_meeting_status": kickoff_status,
            "readiness_score": readiness_score,
            "stakeholders_count": len(stakeholders),
            "technical_contacts_count": len(technical_contacts),
            "goals_defined": goals_defined,
            "gaps": gaps,
            "checklist_completion": f"{completed_items}/{len(self.READINESS_CHECKLIST)}",
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _generate_success_plan(
        self,
        kickoff_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive success plan."""
        plan = customer_metadata.get("plan", "premium")
        industry = customer_metadata.get("industry", "general")

        # Define success criteria by category
        success_criteria = {}

        # User Adoption
        success_criteria["user_adoption"] = {
            "target": "80% of licensed users active within 30 days",
            "measurement": "DAU/MAU ratio",
            "timeline_days": 30
        }

        # Feature Utilization
        success_criteria["feature_utilization"] = {
            "target": "5+ core features actively used",
            "measurement": "Feature adoption tracking",
            "timeline_days": 45
        }

        # Business Outcomes
        goals = kickoff_data.get("business_goals", [])
        if goals:
            success_criteria["business_outcomes"] = {
                "target": goals[0] if goals else "Achieve primary business objective",
                "measurement": "Customer-defined KPIs",
                "timeline_days": 60
            }
        else:
            success_criteria["business_outcomes"] = {
                "target": "20% efficiency improvement in key workflow",
                "measurement": "Time-to-completion metrics",
                "timeline_days": 60
            }

        # Technical Integration
        success_criteria["technical_integration"] = {
            "target": "Complete integration with existing systems",
            "measurement": "API connections and data sync",
            "timeline_days": 35
        }

        # Team Proficiency
        success_criteria["team_proficiency"] = {
            "target": "All users complete core training",
            "measurement": "Training completion rate",
            "timeline_days": 21
        }

        # Define milestones
        milestones = [
            {"name": "Kickoff completed", "day": 0, "owner": "Kickoff Facilitator"},
            {"name": "Training sessions scheduled", "day": 7, "owner": "Training Scheduler"},
            {"name": "Initial training completed", "day": 21, "owner": "Training Scheduler"},
            {"name": "Data migration completed", "day": 35, "owner": "Data Migration Specialist"},
            {"name": "Success criteria validated", "day": 45, "owner": "Success Validator"},
            {"name": "Handoff to CSM", "day": 50, "owner": "Onboarding Coordinator"}
        ]

        return {
            "success_criteria": success_criteria,
            "milestones": milestones,
            "target_completion_days": 50,
            "created_at": datetime.now(UTC).isoformat()
        }

    def _create_action_items(
        self,
        kickoff_analysis: Dict[str, Any],
        success_plan: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create action items based on kickoff analysis."""
        action_items = []

        status = kickoff_analysis["status"]
        gaps = kickoff_analysis.get("gaps", [])

        # Status-based actions
        if status == "not_ready":
            action_items.append({
                "action": "Schedule kickoff call with key stakeholders",
                "priority": "high",
                "owner": "Kickoff Facilitator",
                "due": "Within 3 days"
            })

        if status == "needs_preparation":
            action_items.append({
                "action": "Complete pre-kickoff preparation checklist",
                "priority": "high",
                "owner": "Kickoff Facilitator",
                "due": "Before kickoff meeting"
            })

        # Gap-based actions
        for gap in gaps:
            if "stakeholder" in gap["gap"].lower():
                action_items.append({
                    "action": "Identify and engage executive sponsor",
                    "priority": "high",
                    "owner": "Account Executive",
                    "due": "Before kickoff"
                })
            elif "technical" in gap["gap"].lower():
                action_items.append({
                    "action": "Connect with IT team and identify technical contacts",
                    "priority": "high",
                    "owner": "Solutions Engineer",
                    "due": "Within 5 days"
                })
            elif "goals" in gap["gap"].lower():
                action_items.append({
                    "action": "Document business goals and success metrics",
                    "priority": "critical",
                    "owner": "Kickoff Facilitator",
                    "due": "Before training phase"
                })

        # Standard post-kickoff actions
        if status in ["completed_with_gaps", "excellent"]:
            action_items.append({
                "action": "Distribute success plan to all stakeholders",
                "priority": "medium",
                "owner": "Kickoff Facilitator",
                "due": "Within 24 hours"
            })
            action_items.append({
                "action": "Transition to Training Scheduler for next phase",
                "priority": "medium",
                "owner": "Onboarding Coordinator",
                "due": "Immediately"
            })

        return action_items[:5]

    def _format_kickoff_report(
        self,
        kickoff_analysis: Dict[str, Any],
        success_plan: Dict[str, Any],
        action_items: List[Dict[str, str]]
    ) -> str:
        """Format kickoff facilitation report."""
        status = kickoff_analysis["status"]

        status_emoji = {
            "excellent": "????",
            "completed_with_gaps": "???",
            "ready": "????",
            "needs_preparation": "??????",
            "not_ready": "????"
        }

        report = f"""**{status_emoji.get(status, '????')} Kickoff Facilitation Report**

**Status:** {status.replace('_', ' ').title()}
**Kickoff Meeting:** {kickoff_analysis['kickoff_meeting_status'].replace('_', ' ').title()}
**Readiness Score:** {kickoff_analysis['readiness_score']}%

**Stakeholder Engagement:**
- Stakeholders Identified: {kickoff_analysis['stakeholders_count']}
- Technical Contacts: {kickoff_analysis['technical_contacts_count']}
- Business Goals Defined: {'Yes' if kickoff_analysis['goals_defined'] else 'No'}

**Readiness Checklist:** {kickoff_analysis['checklist_completion']} items completed
"""

        # Gaps
        if kickoff_analysis.get("gaps"):
            report += "\n**?????? Identified Gaps:**\n"
            for gap in kickoff_analysis["gaps"]:
                report += f"- **{gap['gap']}**\n"
                report += f"  Impact: {gap['impact']}\n"

        # Success Plan
        report += "\n**???? Success Plan Overview:**\n"
        report += f"- Target Completion: {success_plan['target_completion_days']} days\n"
        report += f"- Success Criteria Categories: {len(success_plan['success_criteria'])}\n"
        report += f"- Milestones: {len(success_plan['milestones'])}\n"

        report += "\n**Key Success Criteria:**\n"
        for category, criteria in list(success_plan['success_criteria'].items())[:3]:
            report += f"- {category.replace('_', ' ').title()}: {criteria['target']}\n"

        # Milestones
        report += "\n**???? Key Milestones:**\n"
        for milestone in success_plan['milestones'][:4]:
            report += f"- Day {milestone['day']}: {milestone['name']} ({milestone['owner']})\n"

        # Action Items
        if action_items:
            report += "\n**???? Action Items:**\n"
            for i, item in enumerate(action_items[:4], 1):
                report += f"{i}. **{item['action']}**\n"
                report += f"   - Priority: {item['priority'].upper()}\n"
                report += f"   - Owner: {item['owner']}\n"
                report += f"   - Due: {item['due']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Kickoff Facilitator Agent (TASK-2022)")
        print("=" * 70)

        agent = KickoffFacilitatorAgent()

        # Test 1: Ready for kickoff
        print("\n\nTest 1: Ready for Kickoff")
        print("-" * 70)

        state1 = create_initial_state(
            "Facilitate kickoff for new customer",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {
                    "plan": "enterprise",
                    "industry": "fintech"
                }
            }
        )
        state1["entities"] = {
            "kickoff_data": {
                "status": "scheduled",
                "stakeholders": ["CTO", "VP Operations", "Product Manager"],
                "technical_contacts": ["Lead Engineer", "DevOps Lead"],
                "goals_defined": True,
                "business_goals": ["Reduce customer onboarding time by 40%"],
                "readiness_checklist": {
                    "stakeholders_identified": True,
                    "technical_contacts_confirmed": True,
                    "goals_documented": True,
                    "current_process_mapped": True,
                    "timeline_agreed": False
                }
            }
        }

        result1 = await agent.process(state1)

        print(f"Status: {result1['kickoff_status']}")
        print(f"Readiness: {result1['kickoff_readiness']}%")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Not ready for kickoff
        print("\n\n" + "=" * 70)
        print("Test 2: Not Ready - Gaps Identified")
        print("-" * 70)

        state2 = create_initial_state(
            "Assess kickoff readiness",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {"plan": "premium"}
            }
        )
        state2["entities"] = {
            "kickoff_data": {
                "status": "not_scheduled",
                "stakeholders": ["Product Manager"],
                "technical_contacts": [],
                "goals_defined": False,
                "readiness_checklist": {
                    "stakeholders_identified": False,
                    "technical_contacts_confirmed": False,
                    "goals_documented": False,
                    "current_process_mapped": False,
                    "timeline_agreed": False
                }
            }
        }

        result2 = await agent.process(state2)

        print(f"Status: {result2['kickoff_status']}")
        print(f"Readiness: {result2['kickoff_readiness']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
