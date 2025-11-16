"""
Conversation Analyzer Agent - Analyzes conversation patterns and extracts insights.

This agent performs deep analysis of conversation data to identify patterns, trends,
and opportunities for improvement. It examines message flows, customer sentiment,
agent performance, and resolution patterns.

Key Capabilities:
- Conversation flow pattern analysis
- Customer sentiment trajectory tracking
- Agent response quality assessment
- Issue resolution pattern identification
- Customer behavior profiling
- Multi-turn conversation dynamics

Part of: EPIC-004 Learning & Improvement Swarm (TASK-4050)
"""

from typing import Dict, Any, List, Optional, Tuple
import structlog
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.services.infrastructure.agent_registry import AgentRegistry
from src.database.session import get_db
from src.database.models.conversation import Conversation
from src.database.models.message import Message

logger = structlog.get_logger(__name__)


@AgentRegistry.register("conversation_analyzer", tier="advanced", category="learning")
class ConversationAnalyzerAgent(BaseAgent):
    """
    Conversation Analyzer - Extracts insights from conversation patterns.

    This agent analyzes conversations to understand:
    - Common conversation flows and patterns
    - Sentiment progression throughout conversations
    - Message count and length patterns
    - Agent handoff patterns
    - Resolution success factors
    - Customer communication styles
    """

    def __init__(self):
        config = AgentConfig(
            name="conversation_analyzer",
            type=AgentType.ANALYZER,
            model="claude-3-sonnet-20240229",
            temperature=0.3,
            max_tokens=4000,
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.ANALYTICS
            ],
            tier="advanced",
            system_prompt_template=self._get_system_prompt()
        )
        super().__init__(config)
        self.logger = logger.bind(agent="conversation_analyzer")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for conversation analysis."""
        return """You are an expert conversation analyst specialized in customer support interactions.

Your role is to analyze conversation patterns and extract actionable insights for improving customer experience and agent performance.

**Analysis Framework:**

1. **Conversation Flow Analysis**
   - Typical conversation length and structure
   - Common opening/closing patterns
   - Message exchange dynamics
   - Response time patterns

2. **Sentiment Analysis**
   - Initial sentiment distribution
   - Sentiment progression patterns
   - Sentiment improvement/degradation factors
   - Correlation with resolution success

3. **Resolution Pattern Analysis**
   - Characteristics of successful resolutions
   - Common failure patterns
   - Escalation triggers
   - Time-to-resolution factors

4. **Agent Performance Patterns**
   - High-performing agent characteristics
   - Common agent mistakes or gaps
   - Effective response strategies
   - Knowledge base utilization patterns

5. **Customer Behavior Patterns**
   - Communication style variations
   - Question complexity patterns
   - Engagement levels
   - Follow-up behavior

**Output Format:**

Provide structured analysis with:
- Pattern Name: Clear identifier
- Frequency: How often this pattern occurs
- Characteristics: Defining features
- Impact: Effect on outcomes (resolution, CSAT, time)
- Recommendations: How to leverage or address this pattern

**Data Provided:**
{analysis_data}

Identify 5-7 most significant conversation patterns and provide actionable recommendations."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze conversation patterns and extract insights.

        Args:
            state: Current conversation state

        Returns:
            Updated state with conversation analysis
        """
        self.logger.info("conversation_analyzer_started")

        try:
            # Get analysis parameters
            lookback_days = state.get("lookback_days", 7)
            min_conversations = state.get("min_conversations", 100)
            analysis_type = state.get("analysis_type", "comprehensive")  # comprehensive, sentiment, flow

            # Gather conversation data
            analysis_data = await self._analyze_conversations(
                lookback_days=lookback_days,
                min_conversations=min_conversations
            )

            if not analysis_data or analysis_data["total_conversations"] < min_conversations:
                return self.update_state(
                    state,
                    agent_response=f"**Insufficient conversation data for analysis.** Need at least {min_conversations} conversations.",
                    status="completed",
                    response_confidence=0.5,
                    next_agent=None
                )

            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(analysis_data, analysis_type)

            # Get LLM analysis
            analysis_state = state.copy()
            analysis_state["user_message"] = analysis_prompt
            analysis_state["analysis_data"] = analysis_data

            llm_response = await self.call_llm(analysis_state)

            # Build final response
            final_response = self._build_final_response(
                llm_response,
                analysis_data,
                analysis_type
            )

            self.logger.info(
                "conversation_analyzer_completed",
                conversations_analyzed=analysis_data["total_conversations"],
                patterns_identified=analysis_data.get("pattern_count", 0)
            )

            return self.update_state(
                state,
                agent_response=final_response,
                status="completed",
                response_confidence=0.85,
                next_agent=None,
                metadata={
                    "analysis_data": analysis_data,
                    "analysis_period_days": lookback_days
                }
            )

        except Exception as e:
            self.logger.error("conversation_analyzer_error", error=str(e), exc_info=True)
            return self.update_state(
                state,
                agent_response=f"**Error during conversation analysis:** {str(e)}",
                status="error",
                response_confidence=0.0,
                next_agent=None
            )

    async def _analyze_conversations(
        self,
        lookback_days: int,
        min_conversations: int
    ) -> Dict[str, Any]:
        """Analyze conversation patterns from database."""
        db = next(get_db())

        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)

            # Query conversations
            conversations = db.query(Conversation).filter(
                Conversation.started_at >= start_date
            ).all()

            if len(conversations) < min_conversations:
                return {
                    "total_conversations": len(conversations),
                    "insufficient_data": True
                }

            # Analyze patterns
            flow_patterns = self._analyze_flow_patterns(conversations)
            sentiment_patterns = self._analyze_sentiment_patterns(conversations)
            resolution_patterns = self._analyze_resolution_patterns(conversations)
            agent_patterns = self._analyze_agent_patterns(conversations)

            return {
                "total_conversations": len(conversations),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "flow_patterns": flow_patterns,
                "sentiment_patterns": sentiment_patterns,
                "resolution_patterns": resolution_patterns,
                "agent_patterns": agent_patterns,
                "pattern_count": (
                    len(flow_patterns) +
                    len(sentiment_patterns) +
                    len(resolution_patterns) +
                    len(agent_patterns)
                )
            }

        finally:
            db.close()

    def _analyze_flow_patterns(self, conversations: List[Conversation]) -> Dict[str, Any]:
        """Analyze conversation flow patterns."""
        message_counts = []
        durations = []
        agent_handoffs = []

        for conv in conversations:
            # Message count
            message_count = len(conv.messages)
            message_counts.append(message_count)

            # Duration
            if conv.ended_at and conv.started_at:
                duration = (conv.ended_at - conv.started_at).total_seconds()
                durations.append(duration)

            # Agent handoffs
            if conv.agents_involved:
                agent_handoffs.append(len(conv.agents_involved))

        return {
            "avg_message_count": sum(message_counts) / len(message_counts) if message_counts else 0,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "avg_agent_handoffs": sum(agent_handoffs) / len(agent_handoffs) if agent_handoffs else 0,
            "message_count_distribution": {
                "short (1-3)": sum(1 for c in message_counts if c <= 3),
                "medium (4-10)": sum(1 for c in message_counts if 4 <= c <= 10),
                "long (11+)": sum(1 for c in message_counts if c > 10)
            }
        }

    def _analyze_sentiment_patterns(self, conversations: List[Conversation]) -> Dict[str, Any]:
        """Analyze sentiment patterns."""
        sentiment_scores = []
        sentiment_improvements = 0
        sentiment_degradations = 0

        for conv in conversations:
            if conv.sentiment_avg:
                sentiment_scores.append(conv.sentiment_avg)

            # Check sentiment trajectory (if messages have sentiment)
            if len(conv.messages) >= 2:
                sentiments = [m.sentiment for m in conv.messages if m.sentiment is not None]
                if len(sentiments) >= 2:
                    if sentiments[-1] > sentiments[0]:
                        sentiment_improvements += 1
                    elif sentiments[-1] < sentiments[0]:
                        sentiment_degradations += 1

        return {
            "avg_sentiment": sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
            "sentiment_improvement_rate": (
                sentiment_improvements / len(conversations) if conversations else 0
            ),
            "sentiment_degradation_rate": (
                sentiment_degradations / len(conversations) if conversations else 0
            ),
            "sentiment_distribution": {
                "positive (>0.3)": sum(1 for s in sentiment_scores if s > 0.3),
                "neutral (-0.3 to 0.3)": sum(1 for s in sentiment_scores if -0.3 <= s <= 0.3),
                "negative (<-0.3)": sum(1 for s in sentiment_scores if s < -0.3)
            }
        }

    def _analyze_resolution_patterns(self, conversations: List[Conversation]) -> Dict[str, Any]:
        """Analyze resolution patterns."""
        resolved_count = sum(1 for c in conversations if c.status in ["resolved", "closed"])
        resolution_times = [
            c.resolution_time_seconds
            for c in conversations
            if c.resolution_time_seconds
        ]

        # Intent-based resolution rates
        intent_resolutions = defaultdict(lambda: {"total": 0, "resolved": 0})
        for conv in conversations:
            if conv.primary_intent:
                intent_resolutions[conv.primary_intent]["total"] += 1
                if conv.status in ["resolved", "closed"]:
                    intent_resolutions[conv.primary_intent]["resolved"] += 1

        return {
            "resolution_rate": resolved_count / len(conversations) if conversations else 0,
            "avg_resolution_time": sum(resolution_times) / len(resolution_times) if resolution_times else 0,
            "by_intent": {
                intent: {
                    "resolution_rate": data["resolved"] / data["total"] if data["total"] > 0 else 0,
                    "count": data["total"]
                }
                for intent, data in intent_resolutions.items()
            }
        }

    def _analyze_agent_patterns(self, conversations: List[Conversation]) -> Dict[str, Any]:
        """Analyze agent involvement patterns."""
        agent_involvement = Counter()
        kb_usage_count = 0

        for conv in conversations:
            if conv.agents_involved:
                for agent in conv.agents_involved:
                    agent_involvement[agent] += 1

            if conv.kb_articles_used:
                kb_usage_count += 1

        top_agents = agent_involvement.most_common(10)

        return {
            "top_agents": [
                {"name": agent, "conversation_count": count}
                for agent, count in top_agents
            ],
            "kb_usage_rate": kb_usage_count / len(conversations) if conversations else 0,
            "avg_agents_per_conversation": (
                sum(len(c.agents_involved) for c in conversations) / len(conversations)
                if conversations else 0
            )
        }

    def _build_analysis_prompt(
        self,
        analysis_data: Dict[str, Any],
        analysis_type: str
    ) -> str:
        """Build LLM analysis prompt."""
        prompt = f"""Analyze the following conversation pattern data and provide insights:

**Conversation Flow Patterns:**
- Average messages per conversation: {analysis_data['flow_patterns']['avg_message_count']:.1f}
- Average duration: {analysis_data['flow_patterns']['avg_duration_seconds']/60:.1f} minutes
- Average agent handoffs: {analysis_data['flow_patterns']['avg_agent_handoffs']:.2f}

Message Length Distribution:
{self._format_dict(analysis_data['flow_patterns']['message_count_distribution'])}

**Sentiment Patterns:**
- Average sentiment: {analysis_data['sentiment_patterns']['avg_sentiment']:.2f}
- Sentiment improvement rate: {analysis_data['sentiment_patterns']['sentiment_improvement_rate']*100:.1f}%
- Sentiment degradation rate: {analysis_data['sentiment_patterns']['sentiment_degradation_rate']*100:.1f}%

Sentiment Distribution:
{self._format_dict(analysis_data['sentiment_patterns']['sentiment_distribution'])}

**Resolution Patterns:**
- Overall resolution rate: {analysis_data['resolution_patterns']['resolution_rate']*100:.1f}%
- Average resolution time: {analysis_data['resolution_patterns']['avg_resolution_time']/60:.1f} minutes

Top Intents by Resolution Rate:
{self._format_intent_data(analysis_data['resolution_patterns']['by_intent'])}

**Agent Patterns:**
- KB usage rate: {analysis_data['agent_patterns']['kb_usage_rate']*100:.1f}%
- Agents per conversation: {analysis_data['agent_patterns']['avg_agents_per_conversation']:.2f}

Top Agents:
{self._format_agent_list(analysis_data['agent_patterns']['top_agents'])}

Based on this data, identify key patterns, trends, and actionable recommendations for improving conversation outcomes."""

        return prompt

    def _format_dict(self, data: Dict) -> str:
        """Format dictionary for display."""
        return "\n".join(f"  - {k}: {v}" for k, v in data.items())

    def _format_intent_data(self, intent_data: Dict) -> str:
        """Format intent resolution data."""
        sorted_intents = sorted(
            intent_data.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]

        return "\n".join(
            f"  - {intent}: {data['resolution_rate']*100:.1f}% ({data['count']} convos)"
            for intent, data in sorted_intents
        )

    def _format_agent_list(self, agents: List[Dict]) -> str:
        """Format agent list."""
        return "\n".join(
            f"  - {agent['name']}: {agent['conversation_count']} conversations"
            for agent in agents[:5]
        )

    def _build_final_response(
        self,
        llm_response: str,
        analysis_data: Dict[str, Any],
        analysis_type: str
    ) -> str:
        """Build final comprehensive response."""
        output = []

        output.append("# ???? Conversation Pattern Analysis")
        output.append("")
        output.append(f"**Period:** {analysis_data['total_conversations']} conversations analyzed")
        output.append("")

        output.append("## ???? Key Insights")
        output.append("")
        output.append(llm_response)
        output.append("")

        output.append("## ???? Quick Stats")
        output.append("")
        output.append(f"- **Avg Messages:** {analysis_data['flow_patterns']['avg_message_count']:.1f}")
        output.append(f"- **Avg Duration:** {analysis_data['flow_patterns']['avg_duration_seconds']/60:.1f} min")
        output.append(f"- **Resolution Rate:** {analysis_data['resolution_patterns']['resolution_rate']*100:.1f}%")
        output.append(f"- **KB Usage:** {analysis_data['agent_patterns']['kb_usage_rate']*100:.1f}%")

        return "\n".join(output)
