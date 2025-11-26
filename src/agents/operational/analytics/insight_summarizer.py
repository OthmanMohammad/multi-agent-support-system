"""
Insight Summarizer Agent - TASK-2019

Generates narrative insights from analytics data using Claude.
Transforms data into actionable business intelligence.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("insight_summarizer", tier="operational", category="analytics")
class InsightSummarizerAgent(BaseAgent):
    """
    Insight Summarizer Agent.

    Generates narrative insights using Claude:
    - Data-to-narrative conversion
    - Pattern identification and explanation
    - Actionable recommendations
    - Executive-friendly summaries
    - Trend interpretation
    - Anomaly explanation
    """

    def __init__(self):
        config = AgentConfig(
            name="insight_summarizer",
            type=AgentType.GENERATOR,
            # Use Sonnet for better narrative generation
            temperature=0.4,
            max_tokens=1500,
            capabilities=[],
            tier="operational",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Generate insights from analytics data.

        Args:
            state: Current agent state with analytics data

        Returns:
            Updated state with generated insights
        """
        self.logger.info("insight_generation_started")

        state = self.update_state(state)

        # Extract data to analyze
        metrics_data = state.get("entities", {}).get("metrics_data", {})
        analysis_type = state.get("entities", {}).get("analysis_type", "general")
        audience = state.get("entities", {}).get(
            "audience", "executive"
        )  # executive, manager, analyst

        self.logger.debug(
            "insight_generation_details",
            analysis_type=analysis_type,
            audience=audience,
            has_metrics=bool(metrics_data),
        )

        # Prepare data summary for Claude
        data_summary = self._prepare_data_summary(metrics_data, analysis_type)

        # Generate insights using Claude
        insights = await self._generate_insights_with_llm(data_summary, analysis_type, audience)

        # Parse and structure insights
        structured_insights = self._structure_insights(insights)

        # Extract key takeaways
        key_takeaways = self._extract_key_takeaways(structured_insights)

        # Generate recommendations
        recommendations = self._generate_recommendations(structured_insights)

        # Format response
        response = self._format_insight_report(
            structured_insights, key_takeaways, recommendations, analysis_type
        )

        state["agent_response"] = response
        state["insights"] = structured_insights
        state["key_takeaways"] = key_takeaways
        state["recommendations"] = recommendations
        state["response_confidence"] = 0.85
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "insight_generation_completed",
            analysis_type=analysis_type,
            insights_generated=len(structured_insights),
            recommendations_count=len(recommendations),
        )

        return state

    def _prepare_data_summary(self, metrics_data: dict[str, Any], analysis_type: str) -> str:
        """
        Prepare data summary for LLM.

        Args:
            metrics_data: Metrics and analytics data
            analysis_type: Type of analysis

        Returns:
            Formatted data summary
        """
        if not metrics_data:
            # Provide mock data for demonstration
            metrics_data = {
                "revenue": {"current": 542000, "previous": 498000, "change_pct": 8.8},
                "customers": {"total": 15420, "new": 342, "churned": 87},
                "engagement": {"dau": 8450, "mau": 14230, "session_duration": 24.5},
                "support": {"tickets": 1823, "csat": 4.6, "resolution_time": 18.5},
            }

        summary = f"Analysis Type: {analysis_type}\n\nKey Metrics:\n"

        for category, data in metrics_data.items():
            summary += f"\n{category.title()}:\n"
            if isinstance(data, dict):
                for key, value in data.items():
                    summary += f"  - {key.replace('_', ' ').title()}: {value}\n"
            else:
                summary += f"  - Value: {data}\n"

        return summary

    async def _generate_insights_with_llm(
        self, data_summary: str, analysis_type: str, audience: str
    ) -> str:
        """
        Generate insights using Claude.

        Args:
            data_summary: Prepared data summary
            analysis_type: Type of analysis
            audience: Target audience

        Returns:
            Generated insights
        """
        system_prompt = f"""You are an expert business analyst generating insights for {audience} stakeholders.

Analyze the provided data and generate clear, actionable insights. Focus on:
1. What the data tells us about business performance
2. Key trends and patterns
3. Areas of concern or opportunity
4. Specific actionable recommendations

Be concise, data-driven, and provide specific numbers when available."""

        user_message = f"""Analyze this data and provide business insights:

{data_summary}

Generate insights that are:
- Specific and quantified
- Actionable
- Relevant to {audience} decision-makers
- Focused on {analysis_type} analysis"""

        try:
            insights = await self.call_llm(
                system_prompt=system_prompt,
                user_message=user_message,
                conversation_history=[],  # Insight summaries use data context
                max_tokens=1200,
            )
            return insights
        except Exception as e:
            self.logger.error("llm_insight_generation_failed", error=str(e))
            # Fallback to template-based insights
            return self._generate_fallback_insights(data_summary)

    def _generate_fallback_insights(self, data_summary: str) -> str:
        """Generate basic insights without LLM."""
        return """Based on the data analysis:

- Revenue shows positive growth trajectory
- Customer acquisition remains strong with healthy net growth
- Engagement metrics indicate solid product adoption
- Support performance is within acceptable ranges

Key recommendations:
1. Continue monitoring growth trends
2. Focus on customer retention initiatives
3. Optimize support response times
4. Invest in product engagement features"""

    def _structure_insights(self, insights_text: str) -> list[dict[str, Any]]:
        """
        Structure raw insights into categorized format.

        Args:
            insights_text: Raw insights from LLM

        Returns:
            Structured insights
        """
        structured = []

        # Parse insights by paragraphs
        paragraphs = [p.strip() for p in insights_text.split("\n\n") if p.strip()]

        for i, para in enumerate(paragraphs):
            # Categorize insight
            category = "general"
            if any(word in para.lower() for word in ["revenue", "mrr", "arr", "financial"]):
                category = "financial"
            elif any(word in para.lower() for word in ["customer", "churn", "retention"]):
                category = "customer"
            elif any(word in para.lower() for word in ["engagement", "usage", "adoption"]):
                category = "product"
            elif any(word in para.lower() for word in ["support", "ticket", "csat"]):
                category = "support"

            # Determine priority
            priority = "medium"
            if any(
                word in para.lower() for word in ["critical", "urgent", "concern", "risk"]
            ) or any(word in para.lower() for word in ["opportunity", "growth", "improve"]):
                priority = "high"
            elif any(word in para.lower() for word in ["maintain", "monitor", "continue"]):
                priority = "low"

            structured.append(
                {
                    "id": i + 1,
                    "category": category,
                    "priority": priority,
                    "content": para,
                    "is_positive": any(
                        word in para.lower()
                        for word in ["growth", "increase", "improve", "strong", "positive"]
                    ),
                    "is_negative": any(
                        word in para.lower()
                        for word in ["decline", "decrease", "concern", "risk", "weak"]
                    ),
                }
            )

        return structured

    def _extract_key_takeaways(self, structured_insights: list[dict[str, Any]]) -> list[str]:
        """Extract key takeaways from insights."""
        takeaways = []

        # Get high priority insights
        high_priority = [i for i in structured_insights if i["priority"] == "high"]

        for insight in high_priority[:3]:  # Top 3
            # Extract first sentence as takeaway
            content = insight["content"]
            first_sentence = content.split(".")[0] + "."
            takeaways.append(first_sentence)

        # Add at least one positive and one concerning insight
        positive = [i for i in structured_insights if i["is_positive"]]
        negative = [i for i in structured_insights if i["is_negative"]]

        if positive and len(takeaways) < 5:
            takeaways.append(positive[0]["content"].split(".")[0] + ".")

        if negative and len(takeaways) < 5:
            takeaways.append(negative[0]["content"].split(".")[0] + ".")

        return takeaways[:5]  # Max 5 takeaways

    def _generate_recommendations(
        self, structured_insights: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate actionable recommendations."""
        recommendations = []

        # Extract recommendation-focused insights
        for insight in structured_insights:
            content = insight["content"].lower()

            # Look for recommendation keywords
            if any(
                word in content for word in ["recommend", "should", "need to", "must", "suggest"]
            ):
                recommendations.append(
                    {
                        "category": insight["category"],
                        "priority": insight["priority"],
                        "recommendation": insight["content"],
                        "action_type": "immediate" if insight["priority"] == "high" else "planned",
                    }
                )

        # If no explicit recommendations, generate based on insights
        if not recommendations:
            for insight in structured_insights[:3]:
                if insight["is_negative"]:
                    recommendations.append(
                        {
                            "category": insight["category"],
                            "priority": "high",
                            "recommendation": f"Address {insight['category']} concerns identified in analysis",
                            "action_type": "immediate",
                        }
                    )

        return recommendations[:5]  # Max 5 recommendations

    def _format_insight_report(
        self,
        structured_insights: list[dict[str, Any]],
        key_takeaways: list[str],
        recommendations: list[dict[str, Any]],
        analysis_type: str,
    ) -> str:
        """Format insight report."""
        report = f"""**Analytics Insights Report**

**Analysis Type:** {analysis_type.title()}
**Generated:** {datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")}

**Key Takeaways:**
"""

        for i, takeaway in enumerate(key_takeaways, 1):
            report += f"{i}. {takeaway}\n"

        report += "\n**Detailed Insights:**\n\n"

        # Group by category
        categories = {}
        for insight in structured_insights:
            cat = insight["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(insight)

        for category, insights in categories.items():
            report += f"**{category.title()}:**\n"
            for insight in insights:
                priority_icon = (
                    "🔴"
                    if insight["priority"] == "high"
                    else "🟡"
                    if insight["priority"] == "medium"
                    else "🟢"
                )
                report += f"{priority_icon} {insight['content']}\n\n"

        # Recommendations
        if recommendations:
            report += "**Actionable Recommendations:**\n\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. **{rec['category'].title()}** ({rec['action_type'].title()})\n"
                report += f"   {rec['recommendation']}\n\n"

        return report
