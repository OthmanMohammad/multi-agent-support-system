"""
Feedback Loop Agent - TASK-2044

Collects customer feedback, routes to appropriate product/engineering teams,
tracks implementation, and closes the loop with customers.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("feedback_loop", tier="revenue", category="customer_success")
class FeedbackLoopAgent(BaseAgent):
    """
    Feedback Loop Agent.

    Manages customer feedback lifecycle:
    - Collects and categorizes feedback
    - Routes feedback to appropriate teams (Product, Engineering, Support)
    - Tracks feedback implementation status
    - Closes loop with customers when implemented
    - Measures feedback-to-implementation cycle time
    - Prioritizes high-impact feedback
    """

    # Feedback categories
    FEEDBACK_CATEGORIES = {
        "feature_request": {"route_to": "product", "priority_boost": 10},
        "bug_report": {"route_to": "engineering", "priority_boost": 15},
        "usability_issue": {"route_to": "product", "priority_boost": 5},
        "integration_request": {"route_to": "engineering", "priority_boost": 8},
        "documentation": {"route_to": "product", "priority_boost": 3},
        "performance": {"route_to": "engineering", "priority_boost": 12},
        "general_feedback": {"route_to": "product", "priority_boost": 0}
    }

    # Implementation status
    IMPLEMENTATION_STATUS = [
        "received", "triaged", "planned", "in_progress",
        "completed", "released", "closed_loop"
    ]

    def __init__(self):
        config = AgentConfig(
            name="feedback_loop",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            max_tokens=600,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process customer feedback through the feedback loop.

        Args:
            state: Current agent state with feedback data

        Returns:
            Updated state with routing and tracking information
        """
        self.logger.info("feedback_loop_processing_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        feedback_data = state.get("entities", {}).get("feedback_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "feedback_loop_details",
            customer_id=customer_id,
            feedback_type=feedback_data.get("feedback_type"),
            priority=feedback_data.get("priority")
        )

        # Categorize and route feedback
        routing_analysis = self._categorize_and_route_feedback(
            feedback_data,
            customer_metadata
        )

        # Track existing feedback if provided
        tracking_info = self._track_feedback_status(feedback_data)

        # Generate follow-up actions
        follow_up_actions = self._generate_follow_up_actions(
            routing_analysis,
            tracking_info
        )

        # Format response
        response = self._format_feedback_report(
            routing_analysis,
            tracking_info,
            follow_up_actions
        )

        state["agent_response"] = response
        state["feedback_category"] = routing_analysis["category"]
        state["route_to_team"] = routing_analysis["route_to"]
        state["feedback_priority"] = routing_analysis["priority_score"]
        state["implementation_status"] = tracking_info.get("status", "received")
        state["routing_analysis"] = routing_analysis
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "feedback_loop_processed",
            customer_id=customer_id,
            category=routing_analysis["category"],
            route_to=routing_analysis["route_to"],
            priority=routing_analysis["priority_score"]
        )

        return state

    def _categorize_and_route_feedback(
        self,
        feedback_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Categorize feedback and determine routing."""
        feedback_text = feedback_data.get("feedback_text", "")
        feedback_type = feedback_data.get("feedback_type", "general_feedback")

        # Categorize if not already categorized
        if feedback_type not in self.FEEDBACK_CATEGORIES:
            feedback_type = self._auto_categorize_feedback(feedback_text)

        category_config = self.FEEDBACK_CATEGORIES.get(
            feedback_type,
            self.FEEDBACK_CATEGORIES["general_feedback"]
        )

        # Determine routing
        route_to = category_config["route_to"]

        # Calculate priority score (0-100)
        priority_score = self._calculate_feedback_priority(
            feedback_data,
            customer_metadata,
            category_config["priority_boost"]
        )

        # Determine urgency
        urgency = "high" if priority_score >= 75 else "medium" if priority_score >= 50 else "low"

        # Estimate impact
        impact = self._estimate_feedback_impact(
            feedback_type,
            customer_metadata,
            priority_score
        )

        return {
            "category": feedback_type,
            "route_to": route_to,
            "priority_score": priority_score,
            "urgency": urgency,
            "impact": impact,
            "requires_response": priority_score >= 60,
            "sla_days": 3 if urgency == "high" else 7 if urgency == "medium" else 14,
            "routed_at": datetime.now(UTC).isoformat()
        }

    def _auto_categorize_feedback(self, feedback_text: str) -> str:
        """Auto-categorize feedback based on text analysis."""
        text_lower = feedback_text.lower()

        if any(word in text_lower for word in ["bug", "error", "broken", "crash", "not working"]):
            return "bug_report"
        elif any(word in text_lower for word in ["slow", "performance", "speed", "loading"]):
            return "performance"
        elif any(word in text_lower for word in ["integrate", "integration", "api", "connect"]):
            return "integration_request"
        elif any(word in text_lower for word in ["feature", "capability", "add", "want", "need"]):
            return "feature_request"
        elif any(word in text_lower for word in ["confusing", "hard to use", "ux", "ui", "difficult"]):
            return "usability_issue"
        elif any(word in text_lower for word in ["documentation", "docs", "help", "guide"]):
            return "documentation"
        else:
            return "general_feedback"

    def _calculate_feedback_priority(
        self,
        feedback_data: Dict[str, Any],
        customer_metadata: Dict[str, Any],
        category_boost: int
    ) -> int:
        """Calculate feedback priority score."""
        priority = 50  # Base priority

        # Category boost
        priority += category_boost

        # Customer tier boost
        plan = customer_metadata.get("plan", "basic")
        plan_boost = {"enterprise": 20, "premium": 15, "professional": 10, "basic": 5, "free": 0}
        priority += plan_boost.get(plan, 5)

        # Customer health boost (at-risk customers get priority)
        health_score = customer_metadata.get("health_score", 70)
        if health_score < 50:
            priority += 15  # At-risk customer
        elif health_score < 70:
            priority += 8

        # Affected users boost
        affected_users = feedback_data.get("affected_users", 1)
        if affected_users > 100:
            priority += 15
        elif affected_users > 10:
            priority += 10
        elif affected_users > 1:
            priority += 5

        # Explicit priority override
        explicit_priority = feedback_data.get("priority", "medium")
        if explicit_priority == "critical":
            priority += 20
        elif explicit_priority == "high":
            priority += 10

        return min(priority, 100)

    def _estimate_feedback_impact(
        self,
        feedback_type: str,
        customer_metadata: Dict[str, Any],
        priority_score: int
    ) -> str:
        """Estimate business impact of feedback."""
        if priority_score >= 80:
            return "high"
        elif priority_score >= 60:
            return "medium"
        else:
            return "low"

    def _track_feedback_status(
        self,
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track feedback implementation status."""
        feedback_id = feedback_data.get("feedback_id", "new")
        current_status = feedback_data.get("status", "received")

        # Calculate days in current status
        status_updated_at = feedback_data.get("status_updated_at")
        if status_updated_at:
            status_date = datetime.fromisoformat(status_updated_at.replace('Z', '+00:00'))
            days_in_status = (datetime.now(UTC) - status_date).days
        else:
            days_in_status = 0

        # Check if overdue
        expected_cycle_time_days = feedback_data.get("expected_cycle_time_days", 30)
        submission_date = feedback_data.get("submitted_at")
        if submission_date:
            submit_date = datetime.fromisoformat(submission_date.replace('Z', '+00:00'))
            total_days = (datetime.now(UTC) - submit_date).days
            is_overdue = total_days > expected_cycle_time_days
        else:
            total_days = 0
            is_overdue = False

        return {
            "feedback_id": feedback_id,
            "status": current_status,
            "days_in_status": days_in_status,
            "total_days_open": total_days,
            "is_overdue": is_overdue,
            "expected_cycle_time_days": expected_cycle_time_days,
            "needs_customer_update": days_in_status >= 14 and current_status != "closed_loop"
        }

    def _generate_follow_up_actions(
        self,
        routing_analysis: Dict[str, Any],
        tracking_info: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate follow-up actions for feedback."""
        actions = []

        # Routing action
        if routing_analysis["route_to"]:
            actions.append({
                "action": f"Route to {routing_analysis['route_to'].title()} team",
                "owner": "CSM",
                "timeline": f"Within {routing_analysis['sla_days']} days",
                "priority": routing_analysis["urgency"]
            })

        # Customer communication
        if routing_analysis["requires_response"]:
            actions.append({
                "action": "Acknowledge feedback receipt with customer",
                "owner": "CSM",
                "timeline": "Within 24 hours",
                "priority": "high"
            })

        # Status update action
        if tracking_info.get("needs_customer_update"):
            actions.append({
                "action": "Provide status update to customer",
                "owner": "CSM",
                "timeline": "Immediately",
                "priority": "high"
            })

        # Implementation tracking
        if tracking_info.get("status") == "completed":
            actions.append({
                "action": "Close loop with customer - notify of implementation",
                "owner": "CSM",
                "timeline": "This week",
                "priority": "medium"
            })

        # Escalation for overdue items
        if tracking_info.get("is_overdue"):
            actions.append({
                "action": "Escalate overdue feedback to Product Manager",
                "owner": "CS Manager",
                "timeline": "Immediately",
                "priority": "high"
            })

        return actions[:5]

    def _format_feedback_report(
        self,
        routing_analysis: Dict[str, Any],
        tracking_info: Dict[str, Any],
        follow_up_actions: List[Dict[str, str]]
    ) -> str:
        """Format feedback loop report."""
        priority = routing_analysis["priority_score"]

        priority_emoji = "????" if priority >= 75 else "????" if priority >= 50 else "????"

        report = f"""**???? Feedback Loop Report**

**Category:** {routing_analysis['category'].replace('_', ' ').title()}
**Route To:** {routing_analysis['route_to'].title()} Team
**Priority Score:** {priority}/100 {priority_emoji}
**Urgency:** {routing_analysis['urgency'].upper()}
**Impact:** {routing_analysis['impact'].title()}
**Response Required:** {'Yes' if routing_analysis['requires_response'] else 'No'}
**SLA:** {routing_analysis['sla_days']} days

**???? Tracking Information:**
"""

        if tracking_info.get("feedback_id") != "new":
            report += f"- Feedback ID: {tracking_info['feedback_id']}\n"
            report += f"- Current Status: {tracking_info['status'].replace('_', ' ').title()}\n"
            report += f"- Days in Status: {tracking_info['days_in_status']}\n"
            report += f"- Total Days Open: {tracking_info['total_days_open']}\n"
            report += f"- Overdue: {'Yes ??????' if tracking_info['is_overdue'] else 'No'}\n"
            report += f"- Needs Customer Update: {'Yes' if tracking_info['needs_customer_update'] else 'No'}\n"
        else:
            report += "- Status: New Feedback - Not Yet Tracked\n"

        # Follow-up actions
        if follow_up_actions:
            report += "\n**???? Follow-Up Actions:**\n"
            for i, action in enumerate(follow_up_actions, 1):
                priority_icon = "????" if action["priority"] == "high" else "????" if action["priority"] == "medium" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Feedback Loop Agent (TASK-2044)")
        print("=" * 70)

        agent = FeedbackLoopAgent()

        # Test 1: New high-priority feedback
        print("\n\nTest 1: New High-Priority Feature Request")
        print("-" * 70)

        state1 = create_initial_state(
            "Process customer feedback",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {
                    "plan": "enterprise",
                    "health_score": 45
                }
            }
        )
        state1["entities"] = {
            "feedback_data": {
                "feedback_type": "feature_request",
                "feedback_text": "We need advanced analytics dashboard with custom metrics",
                "affected_users": 50,
                "priority": "high"
            }
        }

        result1 = await agent.process(state1)

        print(f"Category: {result1['feedback_category']}")
        print(f"Route To: {result1['route_to_team']}")
        print(f"Priority: {result1['feedback_priority']}/100")
        print(f"Status: {result1['implementation_status']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Existing feedback tracking
        print("\n\n" + "=" * 70)
        print("Test 2: Track Existing Feedback (Overdue)")
        print("-" * 70)

        state2 = create_initial_state(
            "Check feedback status",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {"plan": "premium", "health_score": 72}
            }
        )
        state2["entities"] = {
            "feedback_data": {
                "feedback_id": "FB-12345",
                "feedback_type": "bug_report",
                "feedback_text": "Login page crashes on mobile",
                "status": "planned",
                "status_updated_at": (datetime.now(UTC) - timedelta(days=25)).isoformat(),
                "submitted_at": (datetime.now(UTC) - timedelta(days=45)).isoformat(),
                "expected_cycle_time_days": 30,
                "affected_users": 150,
                "priority": "critical"
            }
        }

        result2 = await agent.process(state2)

        print(f"Category: {result2['feedback_category']}")
        print(f"Priority: {result2['feedback_priority']}/100")
        print(f"Status: {result2['implementation_status']}")
        print(f"\nResponse:\n{result2['agent_response']}")

    asyncio.run(test())
