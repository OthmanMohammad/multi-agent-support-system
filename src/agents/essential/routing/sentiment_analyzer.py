"""
Sentiment Analyzer - Detect emotion, urgency, and satisfaction in messages.

Analyzes sentiment (-1 to 1), emotion categories, urgency levels,
and customer satisfaction to inform routing and response strategy.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-104)
"""

from typing import Dict, Any, Optional
import json
import re
from datetime import datetime
import structlog

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@AgentRegistry.register("sentiment_analyzer", tier="essential", category="routing")
class SentimentAnalyzer(BaseAgent):
    """
    Sentiment Analyzer - Emotion and urgency detection.

    Analyzes messages for:
    - Sentiment Score: -1.0 (very negative) to +1.0 (very positive)
    - Emotion: angry, frustrated, concerned, neutral, satisfied, happy, excited
    - Urgency: low, medium, high, critical
    - Satisfaction: 0.0 (very dissatisfied) to 1.0 (very satisfied)
    - Politeness: 0.0 (rude) to 1.0 (very polite)

    Use Cases:
    - Route urgent/angry messages to senior agents
    - Prioritize critical issues
    - Adjust tone/empathy of responses
    - Track customer sentiment trends
    """

    # Emotion categories
    EMOTIONS = [
        "angry",        # Hostile, aggressive language
        "frustrated",   # Annoyed, impatient
        "concerned",    # Worried, anxious
        "neutral",      # Factual, no strong emotion
        "satisfied",    # Content, pleased
        "happy",        # Positive, delighted
        "excited"       # Enthusiastic, eager
    ]

    # Urgency levels
    URGENCY_LEVELS = ["low", "medium", "high", "critical"]

    def __init__(self, **kwargs):
        """Initialize Sentiment Analyzer with emotion detection capabilities."""
        config = AgentConfig(
            name="sentiment_analyzer",
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307",  # Fast and accurate
            temperature=0.2,  # Low but allows nuance
            max_tokens=250,  # Moderate for detailed analysis
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="sentiment_analyzer"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="sentiment_analyzer", agent_type="analyzer")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for sentiment analysis.

        Returns:
            System prompt with sentiment analysis instructions
        """
        return """You are a sentiment analysis system. Analyze the emotional content, urgency, and satisfaction level of customer messages.

**Analysis Dimensions:**

1. **Sentiment Score** (-1.0 to 1.0):
   - -1.0 to -0.6: Very negative (angry, hostile)
   - -0.6 to -0.2: Negative (frustrated, disappointed)
   - -0.2 to 0.2: Neutral (factual, informational)
   - 0.2 to 0.6: Positive (satisfied, pleased)
   - 0.6 to 1.0: Very positive (happy, excited)

2. **Emotion** (primary emotion detected):
   - angry: Hostile, aggressive, threatening language
   - frustrated: Annoyed, impatient, fed up
   - concerned: Worried, anxious, uncertain
   - neutral: Factual, business-like, no strong emotion
   - satisfied: Content, pleased with service
   - happy: Positive, delighted, grateful
   - excited: Enthusiastic, eager, looking forward

3. **Urgency** (how quickly this needs attention):
   - low: General inquiry, no time pressure
   - medium: Important but not time-sensitive
   - high: Time-sensitive, affecting business
   - critical: Immediate action required, severe impact

   **Urgency Indicators:**
   - Keywords: "urgent", "asap", "immediately", "critical", "emergency", "now"
   - Business impact: "can't work", "losing money", "deadline"
   - Escalation: "been waiting", "third time", "still not fixed"
   - Account risk: High-value customers, churn risk

4. **Satisfaction** (0.0 to 1.0):
   - 0.0 to 0.3: Very dissatisfied (considering leaving, angry)
   - 0.3 to 0.5: Dissatisfied (frustrated, disappointed)
   - 0.5 to 0.7: Neutral (no strong feelings)
   - 0.7 to 0.9: Satisfied (pleased, content)
   - 0.9 to 1.0: Very satisfied (delighted, would recommend)

5. **Politeness** (0.0 to 1.0):
   - 0.0 to 0.3: Rude, hostile, demanding
   - 0.3 to 0.6: Blunt, impatient
   - 0.6 to 0.8: Professional, courteous
   - 0.8 to 1.0: Very polite, grateful

**Context Considerations:**
- Account health: Low health scores amplify negative sentiment
- Churn risk: High churn risk increases urgency
- Plan tier: Enterprise customers may warrant higher urgency
- Previous interactions: Repeat issues increase frustration

**Output Format (JSON only, no extra text):**
{{
    "sentiment_score": -0.8,
    "emotion": "frustrated",
    "urgency": "high",
    "satisfaction": 0.2,
    "politeness": 0.5,
    "indicators": {{
        "negative_keywords": ["broken", "not working", "frustrated"],
        "urgency_keywords": ["urgent", "asap"],
        "business_impact": true,
        "repeat_issue": false
    }},
    "reasoning": "Customer expresses frustration with broken feature, urgent language used"
}}

Analyze ONLY the message content and context. Output valid JSON."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze sentiment, emotion, and urgency of the message.

        Args:
            state: Current agent state with message and context

        Returns:
            Updated state with sentiment analysis fields
        """
        try:
            start_time = datetime.now()

            # Update state with agent history
            state = self.update_state(state)

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("sentiment_analyzer_empty_message")
                state.update(self._get_default_sentiment())
                return state

            # Get customer context for enhanced analysis
            customer_context = state.get("customer_metadata", {})

            # Call LLM for sentiment analysis
            context_str = self._format_customer_context(customer_context)
            prompt = f"""Analyze the sentiment of this message.

Message: {message}

{context_str if context_str else ""}

Provide sentiment analysis in JSON format."""

            response = await self.call_llm(
                system_prompt=self._get_system_prompt(),
                user_message=prompt
            )

            # Parse response
            analysis = self._parse_response(response)

            # Validate and normalize
            analysis = self._validate_analysis(analysis)

            # Apply context-based adjustments
            analysis = self._adjust_for_context(analysis, customer_context)

            # Update state with sentiment fields
            state["sentiment_score"] = analysis["sentiment_score"]
            state["emotion"] = analysis["emotion"]
            state["urgency"] = analysis["urgency"]
            state["satisfaction"] = analysis["satisfaction"]
            state["politeness"] = analysis.get("politeness", 0.7)
            state["sentiment_indicators"] = analysis.get("indicators", {})
            state["sentiment_reasoning"] = analysis.get("reasoning", "")

            # Calculate latency
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            # Store metadata
            state["sentiment_metadata"] = {
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model,
                "context_used": bool(context_str)
            }

            self.logger.info(
                "sentiment_analyzed",
                sentiment=analysis["sentiment_score"],
                emotion=analysis["emotion"],
                urgency=analysis["urgency"],
                satisfaction=analysis["satisfaction"],
                latency_ms=latency_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "sentiment_analysis_failed",
                error=str(e),
                error_type=type(e).__name__
            )

            # Fallback to neutral sentiment
            state.update(self._get_default_sentiment())
            return state

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into sentiment analysis.

        Args:
            response: LLM response (should be JSON)

        Returns:
            Dictionary with sentiment analysis
        """
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                lines = cleaned_response.split("\n")
                cleaned_response = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                )

            # Parse JSON
            analysis = json.loads(cleaned_response)

            # Ensure it's a dict
            if not isinstance(analysis, dict):
                self.logger.warning(
                    "sentiment_analyzer_invalid_type",
                    type=type(analysis).__name__
                )
                return self._get_default_sentiment()

            return analysis

        except json.JSONDecodeError as e:
            self.logger.warning(
                "sentiment_analyzer_invalid_json",
                response_preview=response[:100],
                error=str(e)
            )
            return self._get_default_sentiment()

    def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize sentiment analysis.

        Args:
            analysis: Raw sentiment analysis

        Returns:
            Validated and normalized analysis
        """
        validated = {}

        # Validate sentiment_score (-1.0 to 1.0)
        sentiment = analysis.get("sentiment_score", 0.0)
        try:
            sentiment = float(sentiment)
            validated["sentiment_score"] = max(-1.0, min(1.0, sentiment))
        except (ValueError, TypeError):
            validated["sentiment_score"] = 0.0

        # Validate emotion
        emotion = str(analysis.get("emotion", "neutral")).lower()
        if emotion in self.EMOTIONS:
            validated["emotion"] = emotion
        else:
            # Default based on sentiment score
            if validated["sentiment_score"] < -0.5:
                validated["emotion"] = "angry"
            elif validated["sentiment_score"] < -0.2:
                validated["emotion"] = "frustrated"
            elif validated["sentiment_score"] > 0.5:
                validated["emotion"] = "happy"
            else:
                validated["emotion"] = "neutral"

        # Validate urgency
        urgency = str(analysis.get("urgency", "medium")).lower()
        if urgency in self.URGENCY_LEVELS:
            validated["urgency"] = urgency
        else:
            validated["urgency"] = "medium"

        # Validate satisfaction (0.0 to 1.0)
        satisfaction = analysis.get("satisfaction", 0.5)
        try:
            satisfaction = float(satisfaction)
            validated["satisfaction"] = max(0.0, min(1.0, satisfaction))
        except (ValueError, TypeError):
            validated["satisfaction"] = 0.5

        # Validate politeness (0.0 to 1.0)
        politeness = analysis.get("politeness", 0.7)
        try:
            politeness = float(politeness)
            validated["politeness"] = max(0.0, min(1.0, politeness))
        except (ValueError, TypeError):
            validated["politeness"] = 0.7

        # Pass through indicators and reasoning
        validated["indicators"] = analysis.get("indicators", {})
        validated["reasoning"] = analysis.get("reasoning", "")

        return validated

    def _adjust_for_context(
        self,
        analysis: Dict[str, Any],
        customer_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust sentiment analysis based on customer context.

        Args:
            analysis: Validated sentiment analysis
            customer_context: Customer metadata

        Returns:
            Context-adjusted analysis
        """
        # Amplify negative sentiment for high churn risk customers
        churn_risk = customer_context.get("churn_risk", 0.0)
        if churn_risk > 0.7 and analysis["sentiment_score"] < 0:
            analysis["sentiment_score"] = max(-1.0, analysis["sentiment_score"] - 0.1)
            analysis["urgency"] = self._escalate_urgency(analysis["urgency"])

        # Increase urgency for low health score customers
        health_score = customer_context.get("health_score", 100)
        if health_score < 40 and analysis["urgency"] in ["low", "medium"]:
            analysis["urgency"] = "high"

        # Increase urgency for enterprise customers with issues
        plan = customer_context.get("plan", "free")
        if plan == "enterprise" and analysis["sentiment_score"] < -0.3:
            analysis["urgency"] = self._escalate_urgency(analysis["urgency"])

        return analysis

    def _escalate_urgency(self, current_urgency: str) -> str:
        """
        Escalate urgency to next level.

        Args:
            current_urgency: Current urgency level

        Returns:
            Escalated urgency level
        """
        escalation = {
            "low": "medium",
            "medium": "high",
            "high": "critical",
            "critical": "critical"
        }
        return escalation.get(current_urgency, "medium")

    def _format_customer_context(self, context: Dict[str, Any]) -> str:
        """
        Format customer context for LLM prompt.

        Args:
            context: Customer metadata

        Returns:
            Formatted context string
        """
        if not context:
            return ""

        parts = ["Customer Context:"]

        if "plan" in context:
            parts.append(f"- Plan: {context['plan']}")

        if "health_score" in context:
            parts.append(f"- Health Score: {context['health_score']}/100")

        if "churn_risk" in context:
            risk_pct = int(context['churn_risk'] * 100)
            parts.append(f"- Churn Risk: {risk_pct}%")

        if "team_size" in context:
            parts.append(f"- Team Size: {context['team_size']}")

        if "mrr" in context:
            parts.append(f"- MRR: ${context['mrr']}")

        return "\n".join(parts) if len(parts) > 1 else ""

    def _get_default_sentiment(self) -> Dict[str, Any]:
        """
        Get default neutral sentiment analysis.

        Returns:
            Default sentiment values
        """
        return {
            "sentiment_score": 0.0,
            "emotion": "neutral",
            "urgency": "medium",
            "satisfaction": 0.5,
            "politeness": 0.7,
            "sentiment_indicators": {},
            "sentiment_reasoning": "Default neutral sentiment (analysis failed)",
            "sentiment_metadata": {
                "latency_ms": 0,
                "timestamp": datetime.now().isoformat(),
                "model": self.config.model,
                "fallback": True
            }
        }


# Helper function to create instance
def create_sentiment_analyzer(**kwargs) -> SentimentAnalyzer:
    """
    Create SentimentAnalyzer instance.

    Args:
        **kwargs: Additional arguments passed to SentimentAnalyzer constructor

    Returns:
        Configured SentimentAnalyzer instance
    """
    return SentimentAnalyzer(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_sentiment_analyzer():
        """Test Sentiment Analyzer with sample messages."""
        print("=" * 60)
        print("TESTING SENTIMENT ANALYZER")
        print("=" * 60)

        analyzer = SentimentAnalyzer()

        # Test cases covering different sentiment/emotion/urgency
        test_cases = [
            {
                "message": "This is absolutely unacceptable! The app has been broken for 3 days and I can't work!",
                "context": {"plan": "enterprise", "health_score": 25},
                "expected_emotion": "angry",
                "expected_urgency": "critical"
            },
            {
                "message": "The sync feature isn't working properly. Can you help?",
                "context": {},
                "expected_emotion": "neutral",
                "expected_urgency": "medium"
            },
            {
                "message": "Thank you so much! The support team was amazing and fixed everything quickly!",
                "context": {},
                "expected_emotion": "happy",
                "expected_urgency": "low"
            },
            {
                "message": "I've been trying to export data for hours and it keeps failing. This is frustrating.",
                "context": {"plan": "premium"},
                "expected_emotion": "frustrated",
                "expected_urgency": "high"
            },
            {
                "message": "Just wanted to check if there are any updates to the API?",
                "context": {},
                "expected_emotion": "neutral",
                "expected_urgency": "low"
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test['message']}")
            print(f"{'='*60}")

            state = create_initial_state(
                message=test["message"],
                context={"customer_metadata": test["context"]}
            )

            result = await analyzer.process(state)

            print(f"\n✓ Sentiment Analysis:")
            print(f"  Sentiment Score: {result['sentiment_score']:.2f}")
            print(f"  Emotion: {result['emotion']}")
            print(f"  Urgency: {result['urgency']}")
            print(f"  Satisfaction: {result['satisfaction']:.2f}")
            print(f"  Politeness: {result['politeness']:.2f}")
            print(f"  Reasoning: {result.get('sentiment_reasoning', 'N/A')}")
            print(f"  Latency: {result['sentiment_metadata']['latency_ms']}ms")

    # Run tests
    asyncio.run(test_sentiment_analyzer())
