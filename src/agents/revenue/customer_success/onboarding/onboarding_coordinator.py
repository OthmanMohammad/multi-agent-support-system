"""
Onboarding Coordinator Agent - TASK-2021

Coordinates end-to-end onboarding process, tracks milestones, and measures time-to-value.
Orchestrates kickoff, training, data migration, and success validation phases.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("onboarding_coordinator", tier="revenue", category="customer_success")
class OnboardingCoordinatorAgent(BaseAgent):
    """
    Onboarding Coordinator Agent.

    Coordinates complete onboarding journey:
    - Kickoff phase (days 1-7): Initial setup and goal alignment
    - Training phase (days 8-21): User training and feature adoption
    - Migration phase (days 22-35): Data migration and integration
    - Validation phase (days 36-45): Success criteria validation
    - Handoff phase (day 46+): Transition to ongoing CSM
    """

    # Onboarding phases
    PHASES = {
        "kickoff": {"duration_days": 7, "weight": 20},
        "training": {"duration_days": 14, "weight": 25},
        "migration": {"duration_days": 14, "weight": 30},
        "validation": {"duration_days": 10, "weight": 15},
        "handoff": {"duration_days": 5, "weight": 10}
    }

    # Time-to-value benchmarks (days)
    TTV_BENCHMARKS = {
        "excellent": 30,
        "good": 45,
        "acceptable": 60,
        "delayed": 90
    }

    def __init__(self):
        config = AgentConfig(
            name="onboarding_coordinator",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",
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
        Coordinate onboarding process and track progress.

        Args:
            state: Current agent state with onboarding data

        Returns:
            Updated state with coordination status and recommendations
        """
        self.logger.info("onboarding_coordination_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        onboarding_data = state.get("entities", {}).get("onboarding_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "onboarding_coordination_details",
            customer_id=customer_id,
            current_phase=onboarding_data.get("current_phase"),
            days_elapsed=onboarding_data.get("days_elapsed", 0)
        )

        # Analyze onboarding status
        coordination_analysis = self._analyze_onboarding_status(
            onboarding_data,
            customer_metadata
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(coordination_analysis)

        # Calculate next steps
        next_steps = self._determine_next_steps(coordination_analysis)

        # Build response
        response = self._format_coordination_report(
            coordination_analysis,
            recommendations,
            next_steps
        )

        state["agent_response"] = response
        state["onboarding_status"] = coordination_analysis["overall_status"]
        state["current_phase"] = coordination_analysis["current_phase"]
        state["completion_percentage"] = coordination_analysis["completion_percentage"]
        state["projected_ttv"] = coordination_analysis["projected_ttv_days"]
        state["coordination_analysis"] = coordination_analysis
        state["response_confidence"] = 0.92
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "onboarding_coordination_completed",
            customer_id=customer_id,
            status=coordination_analysis["overall_status"],
            completion_pct=coordination_analysis["completion_percentage"],
            projected_ttv=coordination_analysis["projected_ttv_days"]
        )

        return state

    def _analyze_onboarding_status(
        self,
        onboarding_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze current onboarding status and progress.

        Args:
            onboarding_data: Onboarding metrics and milestones
            customer_metadata: Customer profile data

        Returns:
            Comprehensive onboarding analysis
        """
        start_date_str = onboarding_data.get("start_date")
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow()

        days_elapsed = (datetime.utcnow() - start_date).days

        current_phase = onboarding_data.get("current_phase", "kickoff")
        milestones = onboarding_data.get("milestones_completed", [])
        total_milestones = onboarding_data.get("total_milestones", 10)

        # Calculate completion percentage
        milestones_completed = len(milestones)
        completion_percentage = int((milestones_completed / total_milestones) * 100)

        # Calculate phase progress
        phase_progress = self._calculate_phase_progress(current_phase, days_elapsed)

        # Determine if on track
        expected_completion_pct = self._calculate_expected_completion(days_elapsed)
        is_on_track = completion_percentage >= expected_completion_pct - 10

        # Project time-to-value
        projected_ttv_days = self._project_ttv(
            days_elapsed,
            completion_percentage,
            is_on_track
        )

        # Identify blockers
        blockers = self._identify_blockers(onboarding_data, is_on_track)

        # Calculate health indicators
        health_indicators = self._calculate_health_indicators(
            onboarding_data,
            is_on_track,
            days_elapsed
        )

        # Determine overall status
        overall_status = self._determine_overall_status(
            is_on_track,
            blockers,
            days_elapsed,
            completion_percentage
        )

        return {
            "overall_status": overall_status,
            "current_phase": current_phase,
            "days_elapsed": days_elapsed,
            "completion_percentage": completion_percentage,
            "milestones_completed": milestones_completed,
            "total_milestones": total_milestones,
            "phase_progress": phase_progress,
            "is_on_track": is_on_track,
            "expected_completion_pct": expected_completion_pct,
            "projected_ttv_days": projected_ttv_days,
            "ttv_benchmark": self._get_ttv_benchmark(projected_ttv_days),
            "blockers": blockers,
            "health_indicators": health_indicators,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_phase_progress(self, current_phase: str, days_elapsed: int) -> Dict[str, Any]:
        """Calculate progress within current phase."""
        phase_info = self.PHASES.get(current_phase, self.PHASES["kickoff"])

        # Calculate cumulative days for previous phases
        cumulative_days = 0
        for phase_name, phase_data in self.PHASES.items():
            if phase_name == current_phase:
                break
            cumulative_days += phase_data["duration_days"]

        days_in_phase = days_elapsed - cumulative_days
        phase_duration = phase_info["duration_days"]
        phase_progress_pct = min(int((days_in_phase / phase_duration) * 100), 100)

        return {
            "phase": current_phase,
            "days_in_phase": days_in_phase,
            "phase_duration": phase_duration,
            "progress_percentage": phase_progress_pct
        }

    def _calculate_expected_completion(self, days_elapsed: int) -> int:
        """Calculate expected completion percentage based on days elapsed."""
        # Typical 45-day onboarding
        return min(int((days_elapsed / 45) * 100), 100)

    def _project_ttv(
        self,
        days_elapsed: int,
        completion_percentage: int,
        is_on_track: bool
    ) -> int:
        """Project time-to-value in days."""
        if completion_percentage == 0:
            return 60  # Default estimate

        # Calculate current velocity
        days_per_percent = days_elapsed / completion_percentage if completion_percentage > 0 else 1
        remaining_percent = 100 - completion_percentage

        # Project remaining days
        remaining_days = int(days_per_percent * remaining_percent)

        # Add buffer if not on track
        if not is_on_track:
            remaining_days = int(remaining_days * 1.3)

        return days_elapsed + remaining_days

    def _get_ttv_benchmark(self, projected_ttv: int) -> str:
        """Get benchmark category for projected TTV."""
        if projected_ttv <= self.TTV_BENCHMARKS["excellent"]:
            return "excellent"
        elif projected_ttv <= self.TTV_BENCHMARKS["good"]:
            return "good"
        elif projected_ttv <= self.TTV_BENCHMARKS["acceptable"]:
            return "acceptable"
        else:
            return "delayed"

    def _identify_blockers(
        self,
        onboarding_data: Dict[str, Any],
        is_on_track: bool
    ) -> List[Dict[str, str]]:
        """Identify blockers affecting onboarding progress."""
        blockers = []

        # Check for specific blocker indicators
        if onboarding_data.get("kickoff_delayed", False):
            blockers.append({
                "blocker": "Kickoff call not completed",
                "severity": "high",
                "impact": "Cannot proceed with training until goals are aligned"
            })

        if onboarding_data.get("training_attendance_low", False):
            blockers.append({
                "blocker": "Low training attendance",
                "severity": "medium",
                "impact": "Users not gaining required product knowledge"
            })

        if onboarding_data.get("data_migration_stuck", False):
            blockers.append({
                "blocker": "Data migration blocked",
                "severity": "critical",
                "impact": "Cannot validate success criteria without complete data"
            })

        if onboarding_data.get("technical_issues", False):
            blockers.append({
                "blocker": "Technical integration issues",
                "severity": "high",
                "impact": "Product functionality limited"
            })

        if not is_on_track and not blockers:
            blockers.append({
                "blocker": "Behind schedule - cause unclear",
                "severity": "medium",
                "impact": "Need to investigate root cause of delays"
            })

        return blockers

    def _calculate_health_indicators(
        self,
        onboarding_data: Dict[str, Any],
        is_on_track: bool,
        days_elapsed: int
    ) -> Dict[str, str]:
        """Calculate health indicators for onboarding."""
        return {
            "schedule_health": "on_track" if is_on_track else "at_risk",
            "engagement_health": onboarding_data.get("engagement_level", "medium"),
            "technical_health": onboarding_data.get("technical_status", "good"),
            "stakeholder_health": onboarding_data.get("stakeholder_engagement", "active")
        }

    def _determine_overall_status(
        self,
        is_on_track: bool,
        blockers: List[Dict[str, str]],
        days_elapsed: int,
        completion_percentage: int
    ) -> str:
        """Determine overall onboarding status."""
        critical_blockers = [b for b in blockers if b["severity"] == "critical"]
        high_blockers = [b for b in blockers if b["severity"] == "high"]

        if critical_blockers:
            return "critical"
        elif high_blockers and not is_on_track:
            return "at_risk"
        elif not is_on_track or high_blockers:
            return "needs_attention"
        elif is_on_track and completion_percentage > 70:
            return "excellent"
        else:
            return "on_track"

    def _generate_recommendations(
        self,
        coordination_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate coordination recommendations."""
        recommendations = []

        status = coordination_analysis["overall_status"]
        blockers = coordination_analysis.get("blockers", [])
        current_phase = coordination_analysis["current_phase"]

        # Critical status recommendations
        if status == "critical":
            recommendations.append({
                "action": "Escalate to executive sponsor immediately",
                "priority": "critical",
                "owner": "VP Customer Success",
                "timeline": "Within 24 hours"
            })

        # Blocker-specific recommendations
        for blocker in blockers:
            if "migration" in blocker["blocker"].lower():
                recommendations.append({
                    "action": "Assign technical resource to unblock data migration",
                    "priority": "high",
                    "owner": "Solutions Engineer",
                    "timeline": "Within 2 days"
                })
            elif "training" in blocker["blocker"].lower():
                recommendations.append({
                    "action": "Schedule makeup training sessions",
                    "priority": "medium",
                    "owner": "Training Coordinator",
                    "timeline": "This week"
                })

        # Phase-specific recommendations
        if current_phase == "kickoff":
            recommendations.append({
                "action": "Complete success criteria documentation",
                "priority": "high",
                "owner": "Kickoff Facilitator",
                "timeline": "Before next phase"
            })
        elif current_phase == "validation":
            recommendations.append({
                "action": "Prepare handoff documentation for CSM",
                "priority": "high",
                "owner": "Onboarding Coordinator",
                "timeline": "Before completion"
            })

        return recommendations[:5]  # Top 5 recommendations

    def _determine_next_steps(
        self,
        coordination_analysis: Dict[str, Any]
    ) -> List[str]:
        """Determine next steps in onboarding journey."""
        next_steps = []
        current_phase = coordination_analysis["current_phase"]
        phase_progress = coordination_analysis["phase_progress"]

        if phase_progress["progress_percentage"] >= 80:
            # Ready to move to next phase
            phase_sequence = list(self.PHASES.keys())
            current_index = phase_sequence.index(current_phase)
            if current_index < len(phase_sequence) - 1:
                next_phase = phase_sequence[current_index + 1]
                next_steps.append(f"Prepare for {next_phase} phase transition")
                next_steps.append(f"Complete remaining {current_phase} milestones")
        else:
            next_steps.append(f"Continue {current_phase} phase activities")
            next_steps.append(f"Target {100 - phase_progress['progress_percentage']}% remaining in {current_phase}")

        # Add specific actions based on blockers
        if coordination_analysis["blockers"]:
            next_steps.insert(0, "Address identified blockers as top priority")

        return next_steps[:4]

    def _format_coordination_report(
        self,
        coordination_analysis: Dict[str, Any],
        recommendations: List[Dict[str, str]],
        next_steps: List[str]
    ) -> str:
        """Format onboarding coordination report."""
        status = coordination_analysis["overall_status"]

        status_emoji = {
            "excellent": "????",
            "on_track": "???",
            "needs_attention": "??????",
            "at_risk": "????",
            "critical": "????"
        }

        ttv_emoji = {
            "excellent": "????",
            "good": "???",
            "acceptable": "??????",
            "delayed": "???"
        }

        report = f"""**{status_emoji.get(status, '????')} Onboarding Coordination Report**

**Overall Status:** {status.replace('_', ' ').title()}
**Current Phase:** {coordination_analysis['current_phase'].title()}
**Days Elapsed:** {coordination_analysis['days_elapsed']}
**Completion:** {coordination_analysis['completion_percentage']}% ({coordination_analysis['milestones_completed']}/{coordination_analysis['total_milestones']} milestones)

**Phase Progress:**
- {coordination_analysis['phase_progress']['phase'].title()} Phase: {coordination_analysis['phase_progress']['progress_percentage']}%
- Days in Phase: {coordination_analysis['phase_progress']['days_in_phase']}/{coordination_analysis['phase_progress']['phase_duration']}

**Time-to-Value Projection:**
- Projected TTV: {coordination_analysis['projected_ttv_days']} days {ttv_emoji.get(coordination_analysis['ttv_benchmark'], '??????')}
- Benchmark: {coordination_analysis['ttv_benchmark'].title()}
- On Track: {'Yes' if coordination_analysis['is_on_track'] else 'No'}

**Health Indicators:**
"""
        for indicator, value in coordination_analysis['health_indicators'].items():
            report += f"- {indicator.replace('_', ' ').title()}: {value.replace('_', ' ').title()}\n"

        # Blockers
        if coordination_analysis.get("blockers"):
            report += "\n**???? Active Blockers:**\n"
            for blocker in coordination_analysis["blockers"][:3]:
                report += f"- **{blocker['blocker']}** ({blocker['severity']} severity)\n"
                report += f"  Impact: {blocker['impact']}\n"

        # Next steps
        if next_steps:
            report += "\n**???? Next Steps:**\n"
            for i, step in enumerate(next_steps, 1):
                report += f"{i}. {step}\n"

        # Recommendations
        if recommendations:
            report += "\n**???? Recommended Actions:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                report += f"{i}. **{rec['action']}**\n"
                report += f"   - Priority: {rec['priority'].upper()}\n"
                report += f"   - Owner: {rec['owner']}\n"
                report += f"   - Timeline: {rec['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Onboarding Coordinator Agent (TASK-2021)")
        print("=" * 70)

        agent = OnboardingCoordinatorAgent()

        # Test 1: On-track onboarding
        print("\n\nTest 1: On-Track Onboarding")
        print("-" * 70)

        state1 = create_initial_state(
            "Coordinate onboarding for this customer",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {"plan": "enterprise"}
            }
        )
        state1["entities"] = {
            "onboarding_data": {
                "start_date": (datetime.utcnow() - timedelta(days=15)).isoformat(),
                "current_phase": "training",
                "milestones_completed": ["kickoff_complete", "success_plan_created", "training_scheduled"],
                "total_milestones": 10,
                "engagement_level": "high",
                "technical_status": "good",
                "stakeholder_engagement": "active"
            }
        }

        result1 = await agent.process(state1)

        print(f"Status: {result1['onboarding_status']}")
        print(f"Phase: {result1['current_phase']}")
        print(f"Completion: {result1['completion_percentage']}%")
        print(f"Projected TTV: {result1['projected_ttv']} days")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: At-risk onboarding
        print("\n\n" + "=" * 70)
        print("Test 2: At-Risk Onboarding")
        print("-" * 70)

        state2 = create_initial_state(
            "Check onboarding status",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {"plan": "premium"}
            }
        )
        state2["entities"] = {
            "onboarding_data": {
                "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "current_phase": "migration",
                "milestones_completed": ["kickoff_complete", "training_scheduled"],
                "total_milestones": 10,
                "data_migration_stuck": True,
                "training_attendance_low": True,
                "engagement_level": "low",
                "technical_status": "issues",
                "stakeholder_engagement": "minimal"
            }
        }

        result2 = await agent.process(state2)

        print(f"Status: {result2['onboarding_status']}")
        print(f"Phase: {result2['current_phase']}")
        print(f"Completion: {result2['completion_percentage']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
