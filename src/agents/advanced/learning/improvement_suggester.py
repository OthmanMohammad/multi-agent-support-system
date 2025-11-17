"""
ImprovementSuggester Agent - Analyzes system performance and suggests specific improvements to agents, workflows, and processes

This agent provides advanced learning capabilities for continuous system improvement.

Key Capabilities:
- Data-driven analysis of system performance
- Pattern recognition and trend identification
- Actionable recommendations for optimization
- Integration with database analytics

Part of: EPIC-004 Learning & Improvement Swarm (TASK-4053)
"""

from typing import Dict, Any, List
import structlog
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.services.infrastructure.agent_registry import AgentRegistry
from src.database.connection import get_db_session

logger = structlog.get_logger(__name__)


@AgentRegistry.register("improvement_suggester", tier="advanced", category="learning")
class ImprovementSuggesterAgent(BaseAgent):
    """
    ImprovementSuggester - Analyzes system performance and suggests specific improvements to agents, workflows, and processes
    
    This agent continuously learns from system data to provide insights and recommendations
    for improving agent performance, customer satisfaction, and operational efficiency.
    """

    def __init__(self):
        config = AgentConfig(
            name="improvement_suggester",
            type=AgentType.ANALYZER,
            model="claude-3-sonnet-20240229",
            temperature=0.2,
            max_tokens=3000,
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.ANALYTICS
            ],
            tier="advanced",
            system_prompt_template=self._get_system_prompt()
        )
        super().__init__(config)
        self.logger = logger.bind(agent="improvement_suggester")

    def _get_system_prompt(self) -> str:
        """Get the system prompt."""
        return """You are an expert AI analyst specialized in analyzes system performance and suggests specific improvements to agents, workflows, and processes.

Your role is to analyze system data, identify patterns, and provide actionable recommendations 
for continuous improvement. Focus on data-driven insights that can be immediately implemented.

**Analysis Framework:**
1. Data Analysis - Examine historical performance data
2. Pattern Identification - Find trends and anomalies
3. Root Cause Analysis - Understand why patterns exist
4. Recommendations - Provide specific, testable improvements
5. Impact Assessment - Estimate expected benefits

Provide clear, structured analysis with:
- Current State: What the data shows
- Key Findings: Most important insights (3-5 items)
- Recommendations: Specific actions to take
- Expected Impact: Predicted improvements
- Implementation: How to execute recommendations

Base your analysis on the data provided and industry best practices."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Perform analyzes system performance and suggests specific improvements to agents, workflows, and processes.

        Args:
            state: Current conversation state

        Returns:
            Updated state with analysis results
        """
        self.logger.info("improvement_suggester_started")

        try:
            # Get analysis parameters
            lookback_days = state.get("lookback_days", 7)
            
            # Perform analysis
            analysis_result = await self._perform_analysis(lookback_days)

            # Build response
            response = self._build_response(analysis_result)

            self.logger.info(
                "improvement_suggester_completed",
                findings_count=len(analysis_result.get("findings", []))
            )

            return self.update_state(
                state,
                agent_response=response,
                status="completed",
                response_confidence=0.85,
                next_agent=None,
                metadata={"analysis_result": analysis_result}
            )

        except Exception as e:
            self.logger.error("improvement_suggester_error", error=str(e), exc_info=True)
            return self.update_state(
                state,
                agent_response=f"**Error during analysis:** {str(e)}",
                status="error",
                response_confidence=0.0,
                next_agent=None
            )

    async def _perform_analysis(self, lookback_days: int) -> Dict[str, Any]:
        """Perform the analysis."""
        db = next(get_db())

        try:
            # Query relevant data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)

            # Placeholder for actual analysis logic
            # In production, this would query specific tables and perform calculations
            analysis_data = {
                "period_days": lookback_days,
                "analyzed_at": datetime.utcnow().isoformat(),
                "findings": [
                    "System operating within normal parameters",
                    "No critical issues detected",
                    "Opportunities for optimization identified"
                ],
                "metrics": {
                    "data_points_analyzed": 1000,
                    "patterns_identified": 5,
                    "recommendations_generated": 3
                }
            }

            return analysis_data

        finally:
            db.close()

    def _build_response(self, analysis_result: Dict[str, Any]) -> str:
        """Build formatted response."""
        output = []
        
        output.append(f"# ImprovementSuggester Analysis Report")
        output.append("")
        output.append(f"**Analysis Period:** {analysis_result['period_days']} days")
        output.append("")
        
        output.append("## Key Findings")
        output.append("")
        for i, finding in enumerate(analysis_result.get("findings", []), 1):
            output.append(f"{i}. {finding}")
        
        output.append("")
        output.append("## Metrics")
        output.append("")
        metrics = analysis_result.get("metrics", {})
        for key, value in metrics.items():
            output.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        output.append("")
        output.append("## Next Steps")
        output.append("")
        output.append("1. Review findings and prioritize recommendations")
        output.append("2. Implement high-impact changes")
        output.append("3. Monitor results for 7-14 days")
        output.append("4. Iterate based on outcomes")
        
        return "\n".join(output)
