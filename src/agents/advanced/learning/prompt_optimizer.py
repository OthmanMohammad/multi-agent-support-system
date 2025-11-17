"""
Prompt Optimizer Agent - Analyzes and optimizes agent prompts for better performance.

This agent analyzes conversation data to identify prompt weaknesses and suggest
improvements. It examines agent performance, response quality, and user satisfaction
to recommend prompt optimizations.

Key Capabilities:
- Analyzes agent performance metrics across conversations
- Identifies low-performing prompt patterns
- Suggests specific prompt improvements
- A/B testing recommendations for prompt variations
- Tracks prompt optimization impact over time

Part of: EPIC-004 Learning & Improvement Swarm (TASK-4056)
"""

from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime, timedelta, UTC
from collections import defaultdict

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.services.infrastructure.agent_registry import AgentRegistry
from src.database.connection import get_db_session
from src.database.models.conversation import Conversation
from src.database.models.message import Message
from src.database.models.agent_performance import AgentPerformance

logger = structlog.get_logger(__name__)


@AgentRegistry.register("prompt_optimizer", tier="advanced", category="learning")
class PromptOptimizerAgent(BaseAgent):
    """
    Prompt Optimizer Agent - Continuously improves agent prompts.

    This agent analyzes conversation outcomes, CSAT scores, resolution times,
    and other metrics to identify prompt optimization opportunities. It provides
    data-driven recommendations for improving agent effectiveness.

    Analysis Dimensions:
    - Response quality and relevance
    - Customer satisfaction scores
    - Resolution time and efficiency
    - Escalation rates
    - Agent confidence levels
    - Knowledge base utilization
    """

    def __init__(self):
        config = AgentConfig(
            name="prompt_optimizer",
            type=AgentType.ANALYZER,
            model="claude-3-sonnet-20240229",
            temperature=0.2,
            max_tokens=4000,
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.ANALYTICS
            ],
            tier="advanced",
            system_prompt_template=self._get_system_prompt()
        )
        super().__init__(config)
        self.logger = logger.bind(agent="prompt_optimizer")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for prompt optimization."""
        return """You are an expert prompt engineer specialized in optimizing AI agent prompts for customer support.

Your role is to analyze agent performance data and recommend specific, actionable prompt improvements.

**Analysis Framework:**

1. **Performance Metrics Analysis**
   - Response quality (CSAT, confidence scores)
   - Resolution efficiency (resolution time, escalation rate)
   - Knowledge utilization (KB usage, citation accuracy)
   - Agent-specific patterns (success rates by agent type)

2. **Prompt Weakness Identification**
   - Low confidence responses
   - High escalation rates
   - Poor CSAT scores
   - Inconsistent behavior
   - Knowledge gaps
   - Tone/empathy issues

3. **Optimization Recommendations**
   - Specific prompt additions/modifications
   - Additional context requirements
   - Better instruction formatting
   - Improved examples and demonstrations
   - Enhanced constraints and guidelines

4. **A/B Testing Suggestions**
   - Testable prompt variations
   - Success metrics to track
   - Statistical significance thresholds
   - Rollback criteria

**Output Format:**

Provide structured recommendations with:
- Current Issue: What problem was identified
- Root Cause: Why this is happening (prompt-related)
- Recommended Change: Specific prompt modification
- Expected Impact: Predicted improvement
- Test Strategy: How to validate the change
- Priority: Critical/High/Medium/Low

**Data Provided:**
{performance_summary}

Provide 3-5 highest-impact optimization recommendations."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze agent prompts and suggest optimizations.

        Args:
            state: Current conversation state

        Returns:
            Updated state with optimization recommendations
        """
        self.logger.info("prompt_optimizer_started")

        try:
            # Get analysis parameters
            lookback_days = state.get("lookback_days", 7)
            min_conversations = state.get("min_conversations", 50)
            target_agent = state.get("target_agent", None)  # Analyze specific agent or all

            # Gather performance data
            performance_summary = await self._analyze_agent_performance(
                lookback_days=lookback_days,
                min_conversations=min_conversations,
                target_agent=target_agent
            )

            # If no data, return early
            if not performance_summary:
                return self.update_state(
                    state,
                    agent_response="**Insufficient data for prompt optimization analysis.** Need at least 50 conversations in the last 7 days.",
                    status="completed",
                    response_confidence=0.5,
                    next_agent=None
                )

            # Build analysis prompt
            analysis_prompt = f"""Analyze the following agent performance data and provide specific prompt optimization recommendations:

{self._format_performance_summary(performance_summary)}

Focus on agents with:
- CSAT < 4.0
- Escalation rate > 15%
- Avg confidence < 0.7
- Resolution time outliers

Provide actionable, testable prompt improvements."""

            # Get LLM recommendations
            optimization_state = state.copy()
            optimization_state["user_message"] = analysis_prompt
            optimization_state["performance_summary"] = performance_summary

            llm_response = await self.call_llm(optimization_state)

            # Enhance response with data insights
            recommendations = self._extract_recommendations(llm_response)

            final_response = self._build_final_response(
                llm_response,
                recommendations,
                performance_summary
            )

            self.logger.info(
                "prompt_optimizer_completed",
                recommendations_count=len(recommendations),
                agents_analyzed=len(performance_summary.get("agent_stats", {}))
            )

            return self.update_state(
                state,
                agent_response=final_response,
                status="completed",
                response_confidence=0.85,
                next_agent=None,
                metadata={
                    "recommendations": recommendations,
                    "performance_summary": performance_summary,
                    "analysis_period_days": lookback_days
                }
            )

        except Exception as e:
            self.logger.error("prompt_optimizer_error", error=str(e), exc_info=True)
            return self.update_state(
                state,
                agent_response=f"**Error during prompt optimization analysis:** {str(e)}",
                status="error",
                response_confidence=0.0,
                next_agent=None
            )

    async def _analyze_agent_performance(
        self,
        lookback_days: int,
        min_conversations: int,
        target_agent: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze agent performance from database.

        Returns:
            Dictionary with performance metrics by agent
        """
        db = next(get_db())

        try:
            # Calculate date range
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=lookback_days)

            # Query conversations with outcomes
            query = db.query(Conversation).filter(
                Conversation.started_at >= start_date,
                Conversation.status.in_(["resolved", "closed"])
            )

            if target_agent:
                query = query.filter(
                    Conversation.agents_involved.contains([target_agent])
                )

            conversations = query.all()

            if len(conversations) < min_conversations:
                return {}

            # Aggregate metrics by agent
            agent_stats = defaultdict(lambda: {
                "conversation_count": 0,
                "avg_csat": 0.0,
                "avg_resolution_time": 0.0,
                "avg_confidence": 0.0,
                "escalation_count": 0,
                "total_messages": 0,
                "sentiment_scores": [],
                "kb_usage_count": 0,
                "csat_scores": [],
                "resolution_times": [],
                "confidence_scores": []
            })

            for conv in conversations:
                # Get primary agent (first agent that handled conversation)
                if not conv.agents_involved:
                    continue

                primary_agent = conv.agents_involved[0]
                stats = agent_stats[primary_agent]

                stats["conversation_count"] += 1

                # CSAT (from conversation metadata)
                csat = conv.extra_metadata.get("csat_score")
                if csat:
                    stats["csat_scores"].append(float(csat))

                # Resolution time
                if conv.resolution_time_seconds:
                    stats["resolution_times"].append(conv.resolution_time_seconds)

                # Sentiment
                if conv.sentiment_avg:
                    stats["sentiment_scores"].append(conv.sentiment_avg)

                # KB usage
                if conv.kb_articles_used:
                    stats["kb_usage_count"] += len(conv.kb_articles_used)

                # Escalations (if handed off to multiple agents)
                if len(conv.agents_involved) > 1:
                    stats["escalation_count"] += 1

                # Message analysis
                for message in conv.messages:
                    if message.agent_name:
                        stats["total_messages"] += 1
                        if message.confidence:
                            stats["confidence_scores"].append(message.confidence)

            # Calculate averages
            for agent, stats in agent_stats.items():
                if stats["csat_scores"]:
                    stats["avg_csat"] = sum(stats["csat_scores"]) / len(stats["csat_scores"])
                if stats["resolution_times"]:
                    stats["avg_resolution_time"] = sum(stats["resolution_times"]) / len(stats["resolution_times"])
                if stats["confidence_scores"]:
                    stats["avg_confidence"] = sum(stats["confidence_scores"]) / len(stats["confidence_scores"])
                if stats["sentiment_scores"]:
                    stats["avg_sentiment"] = sum(stats["sentiment_scores"]) / len(stats["sentiment_scores"])

                stats["escalation_rate"] = (
                    stats["escalation_count"] / stats["conversation_count"]
                    if stats["conversation_count"] > 0 else 0.0
                )

            return {
                "agent_stats": dict(agent_stats),
                "total_conversations": len(conversations),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "lookback_days": lookback_days
            }

        finally:
            db.close()

    def _format_performance_summary(self, summary: Dict[str, Any]) -> str:
        """Format performance summary for LLM analysis."""
        output = []

        output.append(f"**Analysis Period:** {summary['lookback_days']} days")
        output.append(f"**Total Conversations:** {summary['total_conversations']}")
        output.append("")
        output.append("**Agent Performance Metrics:**")
        output.append("")

        # Sort agents by conversation count
        agent_stats = summary["agent_stats"]
        sorted_agents = sorted(
            agent_stats.items(),
            key=lambda x: x[1]["conversation_count"],
            reverse=True
        )

        for agent_name, stats in sorted_agents:
            output.append(f"### {agent_name}")
            output.append(f"- Conversations: {stats['conversation_count']}")
            output.append(f"- Avg CSAT: {stats['avg_csat']:.2f}/5.0")
            output.append(f"- Avg Confidence: {stats['avg_confidence']:.2f}")
            output.append(f"- Escalation Rate: {stats['escalation_rate']*100:.1f}%")
            output.append(f"- Avg Resolution Time: {stats['avg_resolution_time']:.0f}s")
            output.append(f"- KB Articles Used: {stats['kb_usage_count']}")

            # Highlight issues
            issues = []
            if stats['avg_csat'] < 4.0:
                issues.append("?????? Low CSAT")
            if stats['avg_confidence'] < 0.7:
                issues.append("?????? Low Confidence")
            if stats['escalation_rate'] > 0.15:
                issues.append("?????? High Escalation Rate")

            if issues:
                output.append(f"- **Issues:** {', '.join(issues)}")

            output.append("")

        return "\n".join(output)

    def _extract_recommendations(self, llm_response: str) -> List[Dict[str, Any]]:
        """Extract structured recommendations from LLM response."""
        # In a production system, this would parse structured output
        # For now, return a simple list
        return [
            {
                "agent": "auto_detected",
                "priority": "high",
                "category": "prompt_optimization",
                "recommendation": llm_response
            }
        ]

    def _build_final_response(
        self,
        llm_response: str,
        recommendations: List[Dict[str, Any]],
        performance_summary: Dict[str, Any]
    ) -> str:
        """Build final comprehensive response."""
        output = []

        output.append("# ???? Prompt Optimization Analysis")
        output.append("")
        output.append(f"**Analysis Period:** {performance_summary['lookback_days']} days")
        output.append(f"**Conversations Analyzed:** {performance_summary['total_conversations']}")
        output.append("")

        # Add LLM recommendations
        output.append("## ???? Optimization Recommendations")
        output.append("")
        output.append(llm_response)
        output.append("")

        # Add top agents by volume
        output.append("## ???? Agent Performance Summary")
        output.append("")
        agent_stats = performance_summary["agent_stats"]
        top_agents = sorted(
            agent_stats.items(),
            key=lambda x: x[1]["conversation_count"],
            reverse=True
        )[:5]

        for agent_name, stats in top_agents:
            output.append(f"**{agent_name}:** {stats['conversation_count']} convos, "
                        f"CSAT {stats['avg_csat']:.2f}, "
                        f"Confidence {stats['avg_confidence']:.2f}")

        output.append("")
        output.append("## ???? Next Steps")
        output.append("")
        output.append("1. Review and prioritize recommended prompt changes")
        output.append("2. Implement changes in dev/staging environment")
        output.append("3. Set up A/B tests for high-impact optimizations")
        output.append("4. Monitor metrics for 7-14 days post-deployment")
        output.append("5. Roll out successful changes to production")

        return "\n".join(output)
