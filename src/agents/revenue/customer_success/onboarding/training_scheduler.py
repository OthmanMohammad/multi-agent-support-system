"""
Training Scheduler Agent - TASK-2023

Schedules training sessions, tracks attendance, and measures training effectiveness.
Ensures users gain required product proficiency during onboarding.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("training_scheduler", tier="revenue", category="customer_success")
class TrainingSchedulerAgent(BaseAgent):
    """
    Training Scheduler Agent.

    Manages training program:
    - Session scheduling and calendar management
    - Attendance tracking and follow-up
    - Training effectiveness measurement
    - Certification and proficiency validation
    - Makeup session coordination
    """

    # Training session types
    SESSION_TYPES = {
        "admin_training": {"duration_mins": 90, "max_attendees": 10},
        "user_training": {"duration_mins": 60, "max_attendees": 50},
        "technical_training": {"duration_mins": 120, "max_attendees": 5},
        "advanced_features": {"duration_mins": 90, "max_attendees": 15},
    }

    # Attendance thresholds
    ATTENDANCE_THRESHOLDS = {"excellent": 90, "good": 75, "acceptable": 60, "poor": 40}

    def __init__(self):
        config = AgentConfig(
            name="training_scheduler",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=450,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Manage training schedule and track effectiveness.

        Args:
            state: Current agent state with training data

        Returns:
            Updated state with training status and recommendations
        """
        self.logger.info("training_scheduling_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        training_data = state.get("entities", {}).get("training_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "training_scheduling_details",
            customer_id=customer_id,
            sessions_scheduled=len(training_data.get("scheduled_sessions", [])),
            sessions_completed=len(training_data.get("completed_sessions", [])),
        )

        # Analyze training status
        training_analysis = self._analyze_training_status(training_data, customer_metadata)

        # Generate recommendations
        recommendations = self._generate_recommendations(training_analysis)

        # Build response
        response = self._format_training_report(training_analysis, recommendations)

        state["agent_response"] = response
        state["training_status"] = training_analysis["status"]
        state["training_completion"] = training_analysis["completion_percentage"]
        state["attendance_rate"] = training_analysis["avg_attendance_rate"]
        state["training_analysis"] = training_analysis
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "training_scheduling_completed",
            customer_id=customer_id,
            training_status=training_analysis["status"],
            completion_pct=training_analysis["completion_percentage"],
        )

        return state

    def _analyze_training_status(
        self, training_data: dict[str, Any], customer_metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze training program status and effectiveness.

        Args:
            training_data: Training sessions and attendance data
            customer_metadata: Customer profile data

        Returns:
            Training analysis with metrics and insights
        """
        scheduled_sessions = training_data.get("scheduled_sessions", [])
        completed_sessions = training_data.get("completed_sessions", [])
        total_users = customer_metadata.get("total_users", 10)

        # Calculate completion
        total_required_sessions = 4  # Standard onboarding training
        sessions_completed_count = len(completed_sessions)
        completion_percentage = int((sessions_completed_count / total_required_sessions) * 100)

        # Calculate attendance metrics
        attendance_metrics = self._calculate_attendance_metrics(completed_sessions, total_users)

        # Calculate effectiveness
        effectiveness_score = self._calculate_effectiveness(training_data, attendance_metrics)

        # Identify issues
        issues = self._identify_training_issues(
            scheduled_sessions, completed_sessions, attendance_metrics
        )

        # Determine status
        status = self._determine_training_status(
            completion_percentage,
            attendance_metrics["avg_attendance_rate"],
            effectiveness_score,
            issues,
        )

        # Check if makeup sessions needed
        makeup_needed = (
            attendance_metrics["avg_attendance_rate"] < self.ATTENDANCE_THRESHOLDS["acceptable"]
        )

        return {
            "status": status,
            "completion_percentage": completion_percentage,
            "sessions_completed": sessions_completed_count,
            "total_required_sessions": total_required_sessions,
            "sessions_scheduled": len(scheduled_sessions),
            "avg_attendance_rate": attendance_metrics["avg_attendance_rate"],
            "attendance_category": attendance_metrics["category"],
            "users_trained": attendance_metrics["unique_attendees"],
            "total_users": total_users,
            "effectiveness_score": effectiveness_score,
            "makeup_sessions_needed": makeup_needed,
            "issues": issues,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    def _calculate_attendance_metrics(
        self, completed_sessions: list[dict[str, Any]], total_users: int
    ) -> dict[str, Any]:
        """Calculate attendance metrics across sessions."""
        if not completed_sessions:
            return {
                "avg_attendance_rate": 0,
                "category": "poor",
                "unique_attendees": 0,
                "total_attendances": 0,
            }

        total_attendance = 0
        total_expected = 0
        unique_attendees = set()

        for session in completed_sessions:
            attended = session.get("attended_count", 0)
            invited = session.get("invited_count", total_users)

            total_attendance += attended
            total_expected += invited

            # Track unique attendees
            attendee_ids = session.get("attendee_ids", [])
            unique_attendees.update(attendee_ids)

        avg_attendance_rate = (
            int(total_attendance / total_expected * 100) if total_expected > 0 else 0
        )

        # Determine category
        category = "poor"
        for cat, threshold in sorted(
            self.ATTENDANCE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        ):
            if avg_attendance_rate >= threshold:
                category = cat
                break

        return {
            "avg_attendance_rate": avg_attendance_rate,
            "category": category,
            "unique_attendees": len(unique_attendees),
            "total_attendances": total_attendance,
        }

    def _calculate_effectiveness(
        self, training_data: dict[str, Any], attendance_metrics: dict[str, Any]
    ) -> int:
        """Calculate training effectiveness score (0-100)."""
        score = 0

        # Attendance contributes 40 points
        score += int(attendance_metrics["avg_attendance_rate"] * 0.4)

        # Quiz/assessment scores contribute 30 points
        quiz_scores = training_data.get("quiz_scores", [])
        if quiz_scores:
            avg_quiz = sum(quiz_scores) / len(quiz_scores)
            score += int(avg_quiz * 0.3)
        else:
            score += 15  # Baseline if no quizzes

        # Post-training surveys contribute 30 points
        satisfaction_score = training_data.get("training_satisfaction", 7)
        score += int((satisfaction_score / 10) * 30)

        return min(score, 100)

    def _identify_training_issues(
        self,
        scheduled_sessions: list[dict[str, Any]],
        completed_sessions: list[dict[str, Any]],
        attendance_metrics: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Identify issues with training program."""
        issues = []

        # Low attendance issue
        if attendance_metrics["avg_attendance_rate"] < self.ATTENDANCE_THRESHOLDS["acceptable"]:
            issues.append(
                {
                    "issue": "Low attendance rate",
                    "severity": "high",
                    "impact": f"Only {attendance_metrics['avg_attendance_rate']}% attendance - users missing critical training",
                }
            )

        # No sessions scheduled
        if not scheduled_sessions and len(completed_sessions) < 4:
            issues.append(
                {
                    "issue": "Training sessions not scheduled",
                    "severity": "critical",
                    "impact": "Cannot complete onboarding without training program",
                }
            )

        # Sessions behind schedule
        if scheduled_sessions:
            overdue = [s for s in scheduled_sessions if self._is_session_overdue(s)]
            if overdue:
                issues.append(
                    {
                        "issue": f"{len(overdue)} sessions overdue",
                        "severity": "medium",
                        "impact": "Training timeline at risk",
                    }
                )

        # Low user coverage
        user_coverage = (
            attendance_metrics["unique_attendees"] / 10
        ) * 100  # Assuming 10 users baseline
        if user_coverage < 50:
            issues.append(
                {
                    "issue": "Low user coverage",
                    "severity": "high",
                    "impact": f"Only {attendance_metrics['unique_attendees']} users trained - need broader participation",
                }
            )

        return issues

    def _is_session_overdue(self, session: dict[str, Any]) -> bool:
        """Check if a session is overdue."""
        scheduled_date_str = session.get("scheduled_date")
        if not scheduled_date_str:
            return False

        try:
            scheduled_date = datetime.fromisoformat(scheduled_date_str.replace("Z", "+00:00"))
            return datetime.now(UTC) > scheduled_date
        except Exception:
            return False

    def _determine_training_status(
        self,
        completion_pct: int,
        attendance_rate: int,
        effectiveness: int,
        issues: list[dict[str, str]],
    ) -> str:
        """Determine overall training status."""
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]

        if critical_issues:
            return "blocked"
        elif completion_pct >= 100 and effectiveness >= 80:
            return "completed_excellent"
        elif completion_pct >= 100:
            return "completed"
        elif high_issues and attendance_rate < 60:
            return "at_risk"
        elif completion_pct >= 50:
            return "in_progress"
        else:
            return "not_started"

    def _generate_recommendations(self, training_analysis: dict[str, Any]) -> list[dict[str, str]]:
        """Generate training recommendations."""
        recommendations = []

        status = training_analysis["status"]
        issues = training_analysis.get("issues", [])

        # Status-based recommendations
        if status == "blocked":
            recommendations.append(
                {
                    "action": "Schedule all required training sessions immediately",
                    "priority": "critical",
                    "owner": "Training Scheduler",
                    "timeline": "Within 2 days",
                }
            )

        if status == "at_risk":
            recommendations.append(
                {
                    "action": "Investigate attendance barriers and reschedule sessions",
                    "priority": "high",
                    "owner": "Training Scheduler",
                    "timeline": "This week",
                }
            )

        # Issue-based recommendations
        for issue in issues:
            if "Low attendance" in issue["issue"]:
                recommendations.append(
                    {
                        "action": "Schedule makeup training sessions for no-shows",
                        "priority": "high",
                        "owner": "Training Scheduler",
                        "timeline": "Next week",
                    }
                )
            elif "not scheduled" in issue["issue"].lower():
                recommendations.append(
                    {
                        "action": "Create and publish training calendar",
                        "priority": "critical",
                        "owner": "Training Scheduler",
                        "timeline": "Within 48 hours",
                    }
                )

        # Proactive recommendations
        if training_analysis["makeup_sessions_needed"]:
            recommendations.append(
                {
                    "action": "Offer on-demand training resources for missed sessions",
                    "priority": "medium",
                    "owner": "Training Scheduler",
                    "timeline": "This week",
                }
            )

        if status in ["completed", "completed_excellent"]:
            recommendations.append(
                {
                    "action": "Issue training completion certificates to users",
                    "priority": "low",
                    "owner": "Training Scheduler",
                    "timeline": "Within 1 week",
                }
            )

        return recommendations[:5]

    def _format_training_report(
        self, training_analysis: dict[str, Any], recommendations: list[dict[str, str]]
    ) -> str:
        """Format training scheduler report."""
        status = training_analysis["status"]

        status_emoji = {
            "completed_excellent": "????",
            "completed": "???",
            "in_progress": "????",
            "at_risk": "??????",
            "blocked": "????",
            "not_started": "????",
        }

        report = f"""**{status_emoji.get(status, "????")} Training Scheduler Report**

**Status:** {status.replace("_", " ").title()}
**Completion:** {training_analysis["completion_percentage"]}% ({training_analysis["sessions_completed"]}/{training_analysis["total_required_sessions"]} sessions)

**Attendance Metrics:**
- Average Attendance Rate: {training_analysis["avg_attendance_rate"]}% ({training_analysis["attendance_category"].title()})
- Users Trained: {training_analysis["users_trained"]}/{training_analysis["total_users"]}
- Sessions Scheduled: {training_analysis["sessions_scheduled"]}

**Effectiveness:**
- Training Effectiveness Score: {training_analysis["effectiveness_score"]}/100
- Makeup Sessions Needed: {"Yes" if training_analysis["makeup_sessions_needed"] else "No"}
"""

        # Issues
        if training_analysis.get("issues"):
            report += "\n**?????? Training Issues:**\n"
            for issue in training_analysis["issues"]:
                report += f"- **{issue['issue']}** ({issue['severity']} severity)\n"
                report += f"  Impact: {issue['impact']}\n"

        # Recommendations
        if recommendations:
            report += "\n**???? Recommended Actions:**\n"
            for i, rec in enumerate(recommendations[:4], 1):
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
        print("Testing Training Scheduler Agent (TASK-2023)")
        print("=" * 70)

        agent = TrainingSchedulerAgent()

        # Test 1: Training in progress, good attendance
        print("\n\nTest 1: Training In Progress - Good Attendance")
        print("-" * 70)

        state1 = create_initial_state(
            "Check training status",
            context={"customer_id": "cust_123", "customer_metadata": {"total_users": 15}},
        )
        state1["entities"] = {
            "training_data": {
                "scheduled_sessions": [
                    {
                        "type": "admin_training",
                        "scheduled_date": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
                    },
                    {
                        "type": "user_training",
                        "scheduled_date": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
                    },
                ],
                "completed_sessions": [
                    {
                        "type": "admin_training",
                        "attended_count": 12,
                        "invited_count": 15,
                        "attendee_ids": [f"user_{i}" for i in range(12)],
                    },
                    {
                        "type": "user_training",
                        "attended_count": 14,
                        "invited_count": 15,
                        "attendee_ids": [f"user_{i}" for i in range(14)],
                    },
                ],
                "quiz_scores": [85, 90, 78, 88],
                "training_satisfaction": 8,
            }
        }

        result1 = await agent.process(state1)

        print(f"Status: {result1['training_status']}")
        print(f"Completion: {result1['training_completion']}%")
        print(f"Attendance: {result1['attendance_rate']}%")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Training at risk - poor attendance
        print("\n\n" + "=" * 70)
        print("Test 2: Training At Risk - Poor Attendance")
        print("-" * 70)

        state2 = create_initial_state(
            "Assess training issues",
            context={"customer_id": "cust_456", "customer_metadata": {"total_users": 20}},
        )
        state2["entities"] = {
            "training_data": {
                "scheduled_sessions": [],
                "completed_sessions": [
                    {
                        "type": "admin_training",
                        "attended_count": 5,
                        "invited_count": 20,
                        "attendee_ids": [f"user_{i}" for i in range(5)],
                    }
                ],
                "quiz_scores": [60, 55],
                "training_satisfaction": 5,
            }
        }

        result2 = await agent.process(state2)

        print(f"Status: {result2['training_status']}")
        print(f"Completion: {result2['training_completion']}%")
        print(f"Attendance: {result2['attendance_rate']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
