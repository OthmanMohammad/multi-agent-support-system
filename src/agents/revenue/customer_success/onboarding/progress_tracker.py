"""
Progress Tracker Agent - TASK-2025

Tracks onboarding progress across all phases, identifies blockers, and forecasts completion.
Provides real-time visibility into onboarding health and milestone achievement.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("progress_tracker", tier="revenue", category="customer_success")
class ProgressTrackerAgent(BaseAgent):
    """
    Progress Tracker Agent.

    Tracks and reports:
    - Milestone completion status
    - Timeline adherence and delays
    - Blocker identification and impact
    - Completion forecast and risk assessment
    - Phase-by-phase progress breakdown
    """

    # Standard milestone definitions
    STANDARD_MILESTONES = [
        {"name": "Kickoff Call Completed", "phase": "kickoff", "day": 3, "critical": True},
        {"name": "Success Plan Approved", "phase": "kickoff", "day": 5, "critical": True},
        {"name": "Training Sessions Scheduled", "phase": "training", "day": 7, "critical": True},
        {"name": "Admin Training Completed", "phase": "training", "day": 14, "critical": True},
        {"name": "User Training Completed", "phase": "training", "day": 21, "critical": False},
        {"name": "Data Extraction Completed", "phase": "migration", "day": 28, "critical": True},
        {"name": "Data Migration Validated", "phase": "migration", "day": 35, "critical": True},
        {"name": "Success Criteria Met", "phase": "validation", "day": 42, "critical": True},
        {"name": "Customer Sign-off", "phase": "validation", "day": 45, "critical": True},
        {"name": "Handoff to CSM", "phase": "handoff", "day": 48, "critical": True}
    ]

    # Health score thresholds
    HEALTH_THRESHOLDS = {
        "on_track": 80,
        "caution": 60,
        "at_risk": 40
    }

    def __init__(self):
        config = AgentConfig(
            name="progress_tracker",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=500,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Track onboarding progress and identify blockers.

        Args:
            state: Current agent state with progress data

        Returns:
            Updated state with progress tracking and forecasts
        """
        self.logger.info("progress_tracking_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        progress_data = state.get("entities", {}).get("progress_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "progress_tracking_details",
            customer_id=customer_id,
            milestones_completed=len(progress_data.get("completed_milestones", [])),
            blockers_active=len(progress_data.get("blockers", []))
        )

        # Analyze progress
        progress_analysis = self._analyze_progress(progress_data, customer_metadata)

        # Identify blockers
        blockers = self._identify_blockers(progress_data, progress_analysis)

        # Forecast completion
        forecast = self._forecast_completion(progress_analysis, blockers)

        # Build response
        response = self._format_progress_report(
            progress_analysis,
            blockers,
            forecast
        )

        state["agent_response"] = response
        state["progress_status"] = progress_analysis["status"]
        state["progress_percentage"] = progress_analysis["completion_percentage"]
        state["health_score"] = progress_analysis["health_score"]
        state["forecasted_completion"] = forecast["forecasted_date"]
        state["progress_analysis"] = progress_analysis
        state["response_confidence"] = 0.89
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "progress_tracking_completed",
            customer_id=customer_id,
            progress_status=progress_analysis["status"],
            health_score=progress_analysis["health_score"],
            completion_pct=progress_analysis["completion_percentage"]
        )

        return state

    def _analyze_progress(
        self,
        progress_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze onboarding progress against milestones.

        Args:
            progress_data: Progress tracking data
            customer_metadata: Customer profile data

        Returns:
            Progress analysis with metrics
        """
        start_date_str = progress_data.get("onboarding_start_date")
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        else:
            start_date = datetime.utcnow()

        days_elapsed = (datetime.utcnow() - start_date).days

        completed_milestones = progress_data.get("completed_milestones", [])
        total_milestones = len(self.STANDARD_MILESTONES)

        # Calculate completion percentage
        completion_percentage = int((len(completed_milestones) / total_milestones) * 100)

        # Analyze milestone timing
        milestone_timing = self._analyze_milestone_timing(
            completed_milestones,
            days_elapsed
        )

        # Calculate health score
        health_score = self._calculate_health_score(
            completion_percentage,
            milestone_timing,
            days_elapsed
        )

        # Determine status
        status = self._determine_status(health_score, days_elapsed)

        # Identify overdue milestones
        overdue_milestones = self._identify_overdue_milestones(
            completed_milestones,
            days_elapsed
        )

        # Calculate velocity
        velocity = len(completed_milestones) / days_elapsed if days_elapsed > 0 else 0

        return {
            "status": status,
            "completion_percentage": completion_percentage,
            "milestones_completed": len(completed_milestones),
            "total_milestones": total_milestones,
            "days_elapsed": days_elapsed,
            "health_score": health_score,
            "milestone_timing": milestone_timing,
            "overdue_milestones": overdue_milestones,
            "velocity": round(velocity, 2),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _analyze_milestone_timing(
        self,
        completed_milestones: List[str],
        days_elapsed: int
    ) -> Dict[str, Any]:
        """Analyze whether milestones were completed on time."""
        on_time = 0
        late = 0
        critical_late = 0

        for milestone in self.STANDARD_MILESTONES:
            if milestone["name"] in completed_milestones:
                if days_elapsed <= milestone["day"]:
                    on_time += 1
                else:
                    late += 1
                    if milestone["critical"]:
                        critical_late += 1

        return {
            "on_time": on_time,
            "late": late,
            "critical_late": critical_late,
            "on_time_percentage": int((on_time / len(completed_milestones)) * 100) if completed_milestones else 0
        }

    def _calculate_health_score(
        self,
        completion_pct: int,
        milestone_timing: Dict[str, Any],
        days_elapsed: int
    ) -> int:
        """Calculate onboarding health score (0-100)."""
        score = 0

        # Completion contributes 40 points
        score += int(completion_pct * 0.4)

        # On-time delivery contributes 30 points
        on_time_pct = milestone_timing["on_time_percentage"]
        score += int(on_time_pct * 0.3)

        # Critical milestone completion contributes 20 points
        critical_late_penalty = milestone_timing["critical_late"] * 5
        score += max(20 - critical_late_penalty, 0)

        # Timeline adherence contributes 10 points
        expected_progress = min(days_elapsed / 48 * 100, 100)  # 48 day standard
        timeline_adherence = 100 - abs(completion_pct - expected_progress)
        score += int(timeline_adherence * 0.1)

        return min(max(score, 0), 100)

    def _determine_status(self, health_score: int, days_elapsed: int) -> str:
        """Determine overall progress status."""
        if health_score >= self.HEALTH_THRESHOLDS["on_track"]:
            return "on_track"
        elif health_score >= self.HEALTH_THRESHOLDS["caution"]:
            return "caution"
        elif health_score >= self.HEALTH_THRESHOLDS["at_risk"]:
            return "at_risk"
        else:
            return "critical"

    def _identify_overdue_milestones(
        self,
        completed_milestones: List[str],
        days_elapsed: int
    ) -> List[Dict[str, Any]]:
        """Identify overdue milestones."""
        overdue = []

        for milestone in self.STANDARD_MILESTONES:
            if milestone["name"] not in completed_milestones and days_elapsed > milestone["day"]:
                days_overdue = days_elapsed - milestone["day"]
                overdue.append({
                    "name": milestone["name"],
                    "phase": milestone["phase"],
                    "due_day": milestone["day"],
                    "days_overdue": days_overdue,
                    "critical": milestone["critical"]
                })

        return overdue

    def _identify_blockers(
        self,
        progress_data: Dict[str, Any],
        progress_analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify blockers affecting progress."""
        blockers = []

        # Explicit blockers from data
        explicit_blockers = progress_data.get("blockers", [])
        blockers.extend(explicit_blockers)

        # Inferred blockers from overdue milestones
        overdue = progress_analysis.get("overdue_milestones", [])
        critical_overdue = [m for m in overdue if m["critical"]]

        if critical_overdue:
            for milestone in critical_overdue[:2]:
                blockers.append({
                    "blocker": f"Critical milestone overdue: {milestone['name']}",
                    "severity": "high",
                    "impact": f"{milestone['days_overdue']} days behind schedule",
                    "phase": milestone["phase"]
                })

        # Low velocity blocker
        if progress_analysis["velocity"] < 0.15:  # Less than 1 milestone per week
            blockers.append({
                "blocker": "Low milestone completion velocity",
                "severity": "medium",
                "impact": "Progress slower than expected - investigate resource constraints",
                "phase": "general"
            })

        return blockers

    def _forecast_completion(
        self,
        progress_analysis: Dict[str, Any],
        blockers: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Forecast onboarding completion date."""
        velocity = progress_analysis["velocity"]
        milestones_remaining = progress_analysis["total_milestones"] - progress_analysis["milestones_completed"]

        if velocity > 0:
            estimated_days_remaining = int(milestones_remaining / velocity)
        else:
            estimated_days_remaining = 60  # Default estimate

        # Add buffer for blockers
        high_severity_blockers = [b for b in blockers if b.get("severity") == "high"]
        buffer_days = len(high_severity_blockers) * 5

        total_days_remaining = estimated_days_remaining + buffer_days

        forecasted_date = (datetime.utcnow() + timedelta(days=total_days_remaining)).date().isoformat()

        # Determine confidence level
        if progress_analysis["health_score"] >= 80:
            confidence = "high"
        elif progress_analysis["health_score"] >= 60:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "forecasted_date": forecasted_date,
            "days_remaining": total_days_remaining,
            "confidence": confidence,
            "buffer_days": buffer_days
        }

    def _format_progress_report(
        self,
        progress_analysis: Dict[str, Any],
        blockers: List[Dict[str, str]],
        forecast: Dict[str, Any]
    ) -> str:
        """Format progress tracking report."""
        status = progress_analysis["status"]

        status_emoji = {
            "on_track": "???",
            "caution": "??????",
            "at_risk": "????",
            "critical": "????"
        }

        health_color = "????" if progress_analysis["health_score"] >= 80 else "????" if progress_analysis["health_score"] >= 60 else "????"

        report = f"""**{status_emoji.get(status, '????')} Onboarding Progress Tracker**

**Status:** {status.replace('_', ' ').title()}
**Health Score:** {progress_analysis['health_score']}/100 {health_color}

**Overall Progress:**
- Completion: {progress_analysis['completion_percentage']}% ({progress_analysis['milestones_completed']}/{progress_analysis['total_milestones']} milestones)
- Days Elapsed: {progress_analysis['days_elapsed']}
- Velocity: {progress_analysis['velocity']} milestones/day

**Milestone Timing:**
- On-Time Completion: {progress_analysis['milestone_timing']['on_time_percentage']}%
- Late Milestones: {progress_analysis['milestone_timing']['late']}
- Critical Milestones Late: {progress_analysis['milestone_timing']['critical_late']}
"""

        # Overdue milestones
        if progress_analysis.get("overdue_milestones"):
            report += "\n**??? Overdue Milestones:**\n"
            for milestone in progress_analysis["overdue_milestones"][:3]:
                critical_tag = " [CRITICAL]" if milestone["critical"] else ""
                report += f"- {milestone['name']}{critical_tag}\n"
                report += f"  Phase: {milestone['phase'].title()} | {milestone['days_overdue']} days overdue\n"

        # Blockers
        if blockers:
            report += "\n**???? Active Blockers:**\n"
            for blocker in blockers[:3]:
                report += f"- **{blocker['blocker']}** ({blocker.get('severity', 'medium')} severity)\n"
                report += f"  Impact: {blocker['impact']}\n"

        # Forecast
        report += f"\n**???? Completion Forecast:**\n"
        report += f"- Forecasted Completion: {forecast['forecasted_date']}\n"
        report += f"- Days Remaining: {forecast['days_remaining']}\n"
        report += f"- Confidence: {forecast['confidence'].title()}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Progress Tracker Agent (TASK-2025)")
        print("=" * 70)

        agent = ProgressTrackerAgent()

        # Test 1: On track progress
        print("\n\nTest 1: Onboarding On Track")
        print("-" * 70)

        state1 = create_initial_state(
            "Track onboarding progress",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {"plan": "enterprise"}
            }
        )
        state1["entities"] = {
            "progress_data": {
                "onboarding_start_date": (datetime.utcnow() - timedelta(days=20)).isoformat(),
                "completed_milestones": [
                    "Kickoff Call Completed",
                    "Success Plan Approved",
                    "Training Sessions Scheduled",
                    "Admin Training Completed"
                ],
                "blockers": []
            }
        }

        result1 = await agent.process(state1)

        print(f"Status: {result1['progress_status']}")
        print(f"Health Score: {result1['health_score']}/100")
        print(f"Completion: {result1['progress_percentage']}%")
        print(f"Forecasted: {result1['forecasted_completion']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Behind schedule with blockers
        print("\n\n" + "=" * 70)
        print("Test 2: Onboarding Behind Schedule")
        print("-" * 70)

        state2 = create_initial_state(
            "Check progress issues",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {"plan": "premium"}
            }
        )
        state2["entities"] = {
            "progress_data": {
                "onboarding_start_date": (datetime.utcnow() - timedelta(days=35)).isoformat(),
                "completed_milestones": [
                    "Kickoff Call Completed",
                    "Success Plan Approved",
                    "Training Sessions Scheduled"
                ],
                "blockers": [
                    {
                        "blocker": "Customer IT team unavailable",
                        "severity": "high",
                        "impact": "Cannot complete data migration",
                        "phase": "migration"
                    }
                ]
            }
        }

        result2 = await agent.process(state2)

        print(f"Status: {result2['progress_status']}")
        print(f"Health Score: {result2['health_score']}/100")
        print(f"Completion: {result2['progress_percentage']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
