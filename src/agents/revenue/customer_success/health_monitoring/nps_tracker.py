"""
NPS Tracker Agent - TASK-2014

Tracks and analyzes Net Promoter Score trends. Identifies detractors for follow-up
and routes feedback to appropriate teams.
"""

from typing import Dict, Any, List
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("nps_tracker", tier="revenue", category="customer_success")
class NPSTrackerAgent(BaseAgent):
    """
    NPS Tracker Agent.

    Handles:
    - NPS score collection and classification
    - Sentiment analysis of feedback
    - Detractor follow-up routing
    - Trend analysis
    - Feedback categorization
    """

    # NPS categories
    NPS_CATEGORIES = {
        "promoter": (9, 10),
        "passive": (7, 8),
        "detractor": (0, 6)
    }

    def __init__(self):
        config = AgentConfig(
            name="nps_tracker",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=400,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process NPS response."""
        self.logger.info("nps_tracking_started")

        state = self.update_state(state)

        # Get NPS data
        nps_score = state.get("entities", {}).get("nps_score", 7)
        feedback = state.get("entities", {}).get("feedback", "")

        # Analyze NPS
        analysis = self._analyze_nps(nps_score, feedback)

        # Format response
        response = self._format_nps_report(analysis)

        state["agent_response"] = response
        state["nps_classification"] = analysis["classification"]
        state["requires_follow_up"] = analysis["requires_follow_up"]
        state["response_confidence"] = 0.95
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "nps_tracking_completed",
            nps_score=nps_score,
            classification=analysis["classification"]
        )

        return state

    def _analyze_nps(self, nps_score: int, feedback: str) -> Dict[str, Any]:
        """Analyze NPS response."""
        # Classify score
        classification = self._classify_nps(nps_score)

        # Determine follow-up needs
        requires_follow_up = classification == "detractor"
        follow_up_urgency = "high" if nps_score <= 4 else "medium" if classification == "detractor" else "low"

        # Extract feedback themes (simplified)
        feedback_themes = self._extract_themes(feedback)

        # Recommended action
        recommended_action = self._get_recommended_action(classification, nps_score)

        return {
            "classification": classification,
            "nps_score": nps_score,
            "requires_follow_up": requires_follow_up,
            "follow_up_urgency": follow_up_urgency,
            "feedback_themes": feedback_themes,
            "recommended_action": recommended_action
        }

    def _classify_nps(self, score: int) -> str:
        """Classify NPS score."""
        for category, (min_score, max_score) in self.NPS_CATEGORIES.items():
            if min_score <= score <= max_score:
                return category
        return "passive"

    def _extract_themes(self, feedback: str) -> List[str]:
        """Extract themes from feedback text."""
        if not feedback:
            return []

        themes = []
        feedback_lower = feedback.lower()

        # Common themes
        if any(word in feedback_lower for word in ["price", "cost", "expensive"]):
            themes.append("pricing")
        if any(word in feedback_lower for word in ["support", "help", "service"]):
            themes.append("support")
        if any(word in feedback_lower for word in ["feature", "functionality", "capability"]):
            themes.append("features")
        if any(word in feedback_lower for word in ["bug", "error", "issue", "problem"]):
            themes.append("quality")
        if any(word in feedback_lower for word in ["slow", "performance", "lag"]):
            themes.append("performance")

        return themes

    def _get_recommended_action(self, classification: str, score: int) -> str:
        """Get recommended action based on NPS."""
        if classification == "detractor":
            if score <= 4:
                return "CSM to call within 24 hours - critical dissatisfaction"
            else:
                return "CSM follow-up within 48 hours - understand concerns"
        elif classification == "passive":
            return "Monitor and nurture - understand what would make them promoter"
        else:  # promoter
            return "Thank and request testimonial or referral"

    def _format_nps_report(self, analysis: Dict[str, Any]) -> str:
        """Format NPS analysis report."""
        classification = analysis["classification"]
        score = analysis["nps_score"]

        # Classification emoji
        emoji = {"promoter": "????", "passive": "????", "detractor": "????"}

        report = f"""**{emoji.get(classification, '????')} NPS Response Analysis**

**NPS Score:** {score}/10
**Classification:** {classification.title()}
**Follow-up Required:** {"Yes" if analysis["requires_follow_up"] else "No"}
"""

        if analysis["requires_follow_up"]:
            report += f"**Urgency:** {analysis['follow_up_urgency'].upper()}\n"

        if analysis["feedback_themes"]:
            report += f"\n**Feedback Themes:** {', '.join(analysis['feedback_themes'])}\n"

        report += f"\n**???? Recommended Action:**\n{analysis['recommended_action']}"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("Testing NPS Tracker Agent (TASK-2014)")
        print("=" * 60)

        agent = NPSTrackerAgent()

        # Test detractor
        state = create_initial_state("Process NPS")
        state["entities"] = {
            "nps_score": 3,
            "feedback": "Product is too complex, support is slow"
        }

        result = await agent.process(state)
        print(f"Classification: {result['nps_classification']}")
        print(f"\n{result['agent_response']}")

    asyncio.run(test())
