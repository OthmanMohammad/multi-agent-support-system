"""
Escalation Decider - Decide when to escalate to human agents.

Evaluates 7 escalation triggers to determine when AI should hand off
to human agents for better customer experience.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-109)
"""

from typing import Dict, Any, Optional, List, Literal
import re
from datetime import datetime
import structlog

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)

# Type aliases
UrgencyLevel = Literal["low", "medium", "high", "critical"]
EscalationTeam = Literal["tier2_support", "specialist", "management", "executive"]


@AgentRegistry.register("escalation_decider", tier="essential", category="routing")
class EscalationDecider(BaseAgent):
    """
    Escalation Decider - Determine when to escalate to human.

    Evaluates 7 escalation triggers:
    1. Low Confidence: Agent confidence < 0.4
    2. Negative Sentiment: Sentiment score < -0.7 (very angry)
    3. Too Many Turns: Conversation > 5 turns without resolution
    4. Explicit Request: Customer explicitly asks for human
    5. High-Value Customer: Enterprise customer with complex issue
    6. Regulatory/Legal: GDPR, legal threats, compliance
    7. Critical Bug: Production down, data loss, severe impact

    Returns escalation decision with reasons, urgency, and suggested team.
    """

    # Escalation thresholds
    CONFIDENCE_THRESHOLD = 0.4
    SENTIMENT_THRESHOLD = -0.7
    MAX_TURNS_THRESHOLD = 5
    COMPLEXITY_THRESHOLD = 7

    # Trigger categories
    TRIGGERS = [
        "low_confidence",
        "very_negative_sentiment",
        "too_many_turns",
        "explicit_request",
        "high_value_customer",
        "regulatory_legal",
        "critical_bug"
    ]

    # Keywords for detection
    HUMAN_REQUEST_KEYWORDS = [
        "human", "person", "agent", "representative", "manager",
        "supervisor", "speak to someone", "talk to someone",
        "real person", "actual person"
    ]

    LEGAL_KEYWORDS = [
        "gdpr", "lawyer", "attorney", "legal action", "sue",
        "lawsuit", "compliance", "regulation", "data protection",
        "privacy violation", "breach", "report you"
    ]

    CRITICAL_KEYWORDS = [
        "production down", "system down", "can't access",
        "data loss", "lost data", "deleted", "critical",
        "emergency", "urgent", "asap", "immediately"
    ]

    def __init__(self, **kwargs):
        """Initialize Escalation Decider."""
        config = AgentConfig(
            name="escalation_decider",
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=200,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template="",  # Escalation uses rule-based logic
            tier="essential",
            role="escalation_decider"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="escalation_decider", agent_type="analyzer")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process escalation decision.

        Args:
            state: Current agent state

        Returns:
            Updated state with escalation decision
        """
        try:
            start_time = datetime.now()

            # Update state with agent history
            state = self.update_state(state)

            # Evaluate escalation
            escalation_result = await self.should_escalate(state)

            # Update state with escalation decision
            state["should_escalate"] = escalation_result["should_escalate"]
            state["escalation_reasons"] = escalation_result["reasons"]
            state["escalation_urgency"] = escalation_result["urgency"]
            state["escalation_suggested_team"] = escalation_result["suggested_team"]
            state["escalation_trigger_details"] = escalation_result["trigger_details"]

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            state["escalation_metadata"] = {
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
                "num_triggers": len(escalation_result["reasons"])
            }

            self.logger.info(
                "escalation_evaluated",
                should_escalate=escalation_result["should_escalate"],
                reasons=escalation_result["reasons"],
                urgency=escalation_result["urgency"],
                latency_ms=latency_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "escalation_evaluation_failed",
                error=str(e),
                error_type=type(e).__name__
            )

            # Safe fallback: don't escalate if evaluation fails
            state["should_escalate"] = False
            state["escalation_reasons"] = []
            state["escalation_urgency"] = "medium"
            return state

    async def should_escalate(self, state: AgentState) -> Dict[str, Any]:
        """
        Determine if escalation to human is needed.

        Evaluates all 7 triggers and returns comprehensive decision.

        Args:
            state: Current agent state

        Returns:
            Dictionary with escalation decision, reasons, urgency, team
        """
        reasons = []
        trigger_details = {}

        # Get message for keyword analysis
        message = state.get("current_message", "").lower()

        # Trigger 1: Low Confidence
        confidence = state.get("confidence", 1.0)
        if confidence < self.CONFIDENCE_THRESHOLD:
            reasons.append("low_confidence")
            trigger_details["low_confidence"] = {
                "confidence": confidence,
                "threshold": self.CONFIDENCE_THRESHOLD
            }

        # Trigger 2: Very Negative Sentiment
        sentiment = state.get("sentiment_score", 0.0)
        if sentiment < self.SENTIMENT_THRESHOLD:
            reasons.append("very_negative_sentiment")
            trigger_details["very_negative_sentiment"] = {
                "sentiment_score": sentiment,
                "threshold": self.SENTIMENT_THRESHOLD,
                "emotion": state.get("emotion", "unknown")
            }

        # Trigger 3: Too Many Turns
        turn_count = state.get("turn_count", 0)
        if turn_count > self.MAX_TURNS_THRESHOLD:
            reasons.append("too_many_turns")
            trigger_details["too_many_turns"] = {
                "turn_count": turn_count,
                "threshold": self.MAX_TURNS_THRESHOLD
            }

        # Trigger 4: Explicit Request for Human
        if self._detect_human_request(message):
            reasons.append("explicit_request")
            matched_keywords = [
                kw for kw in self.HUMAN_REQUEST_KEYWORDS
                if kw in message
            ]
            trigger_details["explicit_request"] = {
                "matched_keywords": matched_keywords
            }

        # Trigger 5: High-Value Customer with Complex Issue
        if self._is_high_value_complex(state):
            reasons.append("high_value_customer")
            customer_metadata = state.get("customer_metadata", {})
            trigger_details["high_value_customer"] = {
                "plan": customer_metadata.get("plan"),
                "complexity_score": state.get("complexity_score"),
                "mrr": customer_metadata.get("mrr")
            }

        # Trigger 6: Regulatory/Legal
        if self._detect_legal_issue(message):
            reasons.append("regulatory_legal")
            matched_keywords = [
                kw for kw in self.LEGAL_KEYWORDS
                if kw in message
            ]
            trigger_details["regulatory_legal"] = {
                "matched_keywords": matched_keywords
            }

        # Trigger 7: Critical Bug/Production Issue
        if self._detect_critical_issue(message, state):
            reasons.append("critical_bug")
            matched_keywords = [
                kw for kw in self.CRITICAL_KEYWORDS
                if kw in message
            ]
            trigger_details["critical_bug"] = {
                "matched_keywords": matched_keywords,
                "urgency": state.get("urgency")
            }

        # Determine if should escalate
        should_escalate = len(reasons) > 0

        # Calculate urgency
        urgency = self._calculate_urgency(reasons, state)

        # Suggest team
        suggested_team = self._suggest_team(reasons, state)

        return {
            "should_escalate": should_escalate,
            "reasons": reasons,
            "urgency": urgency,
            "suggested_team": suggested_team,
            "trigger_details": trigger_details,
            "recommendation": self._generate_recommendation(reasons, urgency, suggested_team)
        }

    def _detect_human_request(self, message: str) -> bool:
        """
        Detect if customer explicitly requested human.

        Args:
            message: Customer message (lowercase)

        Returns:
            True if human requested
        """
        for keyword in self.HUMAN_REQUEST_KEYWORDS:
            if keyword in message:
                return True
        return False

    def _is_high_value_complex(self, state: AgentState) -> bool:
        """
        Check if high-value customer with complex issue.

        Args:
            state: Current state

        Returns:
            True if enterprise customer with complex issue
        """
        customer_metadata = state.get("customer_metadata", {})
        plan = customer_metadata.get("plan", "free")
        complexity = state.get("complexity_score", 0)
        mrr = customer_metadata.get("mrr", 0)

        # Enterprise plan OR high MRR
        is_high_value = (plan == "enterprise") or (mrr > 5000)

        # Complex issue
        is_complex = complexity >= self.COMPLEXITY_THRESHOLD

        return is_high_value and is_complex

    def _detect_legal_issue(self, message: str) -> bool:
        """
        Detect regulatory/legal mentions.

        Args:
            message: Customer message (lowercase)

        Returns:
            True if legal issue detected
        """
        for keyword in self.LEGAL_KEYWORDS:
            if keyword in message:
                return True
        return False

    def _detect_critical_issue(self, message: str, state: AgentState) -> bool:
        """
        Detect critical production issues.

        Args:
            message: Customer message (lowercase)
            state: Current state

        Returns:
            True if critical issue detected
        """
        # Check keywords
        has_critical_keyword = any(
            keyword in message
            for keyword in self.CRITICAL_KEYWORDS
        )

        # Check urgency from sentiment analyzer
        urgency = state.get("urgency", "medium")
        is_critical_urgency = urgency == "critical"

        return has_critical_keyword or is_critical_urgency

    def _calculate_urgency(
        self,
        reasons: List[str],
        state: AgentState
    ) -> UrgencyLevel:
        """
        Calculate escalation urgency.

        Args:
            reasons: List of escalation reasons
            state: Current state

        Returns:
            Urgency level
        """
        # Critical urgency triggers
        critical_triggers = ["critical_bug", "regulatory_legal"]
        if any(trigger in reasons for trigger in critical_triggers):
            return "critical"

        # High urgency triggers
        high_triggers = ["very_negative_sentiment", "high_value_customer"]
        if any(trigger in reasons for trigger in high_triggers):
            return "high"

        # Medium urgency triggers
        medium_triggers = ["explicit_request", "too_many_turns"]
        if any(trigger in reasons for trigger in medium_triggers):
            return "medium"

        # Low confidence alone = low urgency
        if "low_confidence" in reasons:
            return "low"

        # Default
        return "medium"

    def _suggest_team(
        self,
        reasons: List[str],
        state: AgentState
    ) -> EscalationTeam:
        """
        Suggest which team should handle escalation.

        Args:
            reasons: List of escalation reasons
            state: Current state

        Returns:
            Suggested team
        """
        # Executive team for legal/regulatory
        if "regulatory_legal" in reasons:
            return "executive"

        # Management for high-value customers
        if "high_value_customer" in reasons:
            customer_metadata = state.get("customer_metadata", {})
            mrr = customer_metadata.get("mrr", 0)
            if mrr > 10000:
                return "executive"
            else:
                return "management"

        # Specialist for critical bugs
        if "critical_bug" in reasons:
            return "specialist"

        # Tier 2 for other escalations
        return "tier2_support"

    def _generate_recommendation(
        self,
        reasons: List[str],
        urgency: UrgencyLevel,
        suggested_team: EscalationTeam
    ) -> str:
        """
        Generate human-readable recommendation.

        Args:
            reasons: Escalation reasons
            urgency: Urgency level
            suggested_team: Suggested team

        Returns:
            Recommendation text
        """
        if not reasons:
            return "No escalation needed. Continue with AI agent."

        reason_str = ", ".join(reasons)
        return (
            f"Escalate to {suggested_team} with {urgency} urgency. "
            f"Triggers: {reason_str}."
        )

    def get_escalation_summary(self, state: AgentState) -> str:
        """
        Get human-readable escalation summary.

        Args:
            state: Current state with escalation decision

        Returns:
            Summary text
        """
        if not state.get("should_escalate", False):
            return "✓ No escalation needed"

        reasons = state.get("escalation_reasons", [])
        urgency = state.get("escalation_urgency", "medium")
        team = state.get("escalation_suggested_team", "tier2_support")

        summary = f"⚠️ ESCALATE to {team} ({urgency} urgency)\n"
        summary += f"Triggers ({len(reasons)}):\n"

        for reason in reasons:
            summary += f"  - {reason}\n"

        return summary


# Helper function to create instance
def create_escalation_decider(**kwargs) -> EscalationDecider:
    """
    Create EscalationDecider instance.

    Args:
        **kwargs: Additional arguments

    Returns:
        Configured EscalationDecider instance
    """
    return EscalationDecider(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_escalation_decider():
        """Test Escalation Decider with various scenarios."""
        print("=" * 60)
        print("TESTING ESCALATION DECIDER")
        print("=" * 60)

        decider = EscalationDecider()

        # Test scenarios
        test_cases = [
            {
                "name": "No Escalation",
                "state": create_initial_state(
                    message="How do I export data?",
                    context={"confidence": 0.9, "sentiment_score": 0.0}
                ),
                "expected": False
            },
            {
                "name": "Low Confidence",
                "state": create_initial_state(
                    message="Complex query",
                    context={"confidence": 0.3}
                ),
                "expected": True
            },
            {
                "name": "Very Negative Sentiment",
                "state": create_initial_state(
                    message="This is TERRIBLE!",
                    context={"sentiment_score": -0.9, "emotion": "angry"}
                ),
                "expected": True
            },
            {
                "name": "Explicit Human Request",
                "state": create_initial_state(
                    message="I want to speak to a human agent please",
                    context={}
                ),
                "expected": True
            },
            {
                "name": "Legal Issue",
                "state": create_initial_state(
                    message="This is a GDPR violation, I'm contacting my lawyer",
                    context={}
                ),
                "expected": True
            },
            {
                "name": "Critical Production Issue",
                "state": create_initial_state(
                    message="URGENT: Production system is down!",
                    context={"urgency": "critical"}
                ),
                "expected": True
            }
        ]

        for test in test_cases:
            print(f"\n{'='*60}")
            print(f"TEST: {test['name']}")
            print(f"{'='*60}")

            # Add state fields
            test_state = test["state"]
            for key, value in test["state"].items():
                if key not in ["current_message", "customer_metadata"]:
                    test_state[key] = value

            result = await decider.process(test_state)

            print(f"Message: {test_state['current_message'][:50]}...")
            print(f"Should Escalate: {result['should_escalate']}")
            print(f"Reasons: {result.get('escalation_reasons', [])}")
            print(f"Urgency: {result.get('escalation_urgency', 'N/A')}")
            print(f"Team: {result.get('escalation_suggested_team', 'N/A')}")
            print(f"Expected: {test['expected']}")
            print(f"Match: {'✓' if result['should_escalate'] == test['expected'] else '✗'}")

            # Print summary
            summary = decider.get_escalation_summary(result)
            print(f"\nSummary:\n{summary}")

    # Run tests
    asyncio.run(test_escalation_decider())
