"""
Usage Monitor Agent - TASK-2013

Monitors product usage patterns, detects anomalies, and identifies feature adoption gaps.
Tracks DAU/MAU metrics and benchmarks against cohorts.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("usage_monitor", tier="revenue", category="customer_success")
class UsageMonitorAgent(BaseAgent):
    """
    Usage Monitor Agent.

    Monitors:
    - DAU/MAU metrics and trends
    - Feature adoption rates
    - Seat utilization
    - Usage anomalies (sudden drops or spikes)
    - Cohort benchmarking
    """

    def __init__(self):
        config = AgentConfig(
            name="usage_monitor",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=400,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Monitor product usage and detect anomalies."""
        self.logger.info("usage_monitoring_started")

        state = self.update_state(state)

        # Get usage data
        current_usage = state.get("entities", {}).get("current_period_usage", {})
        previous_usage = state.get("entities", {}).get("previous_period_usage", {})

        # Analyze usage
        analysis = self._analyze_usage(current_usage, previous_usage)

        # Format response
        response = self._format_usage_report(analysis)

        state["agent_response"] = response
        state["usage_status"] = analysis["status"]
        state["usage_analysis"] = analysis
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "usage_monitoring_completed",
            usage_status=analysis["status"],
            anomaly_detected=analysis.get("anomaly_detected", False)
        )

        return state

    def _analyze_usage(
        self,
        current: Dict[str, Any],
        previous: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze usage patterns and detect anomalies."""
        dau_current = current.get("dau", 0)
        mau_current = current.get("mau", 0)
        total_seats = current.get("total_seats", 1)

        dau_previous = previous.get("dau", dau_current)
        mau_previous = previous.get("mau", mau_current)

        # Calculate changes
        dau_change = ((dau_current - dau_previous) / dau_previous * 100) if dau_previous > 0 else 0
        mau_change = ((mau_current - mau_previous) / mau_previous * 100) if mau_previous > 0 else 0

        # Calculate seat utilization
        seat_utilization = (mau_current / total_seats * 100) if total_seats > 0 else 0

        # Detect anomalies
        anomaly_detected = False
        anomaly_type = None

        if dau_change < -30:  # 30% drop
            anomaly_detected = True
            anomaly_type = "significant_decline"
        elif dau_change > 50:  # 50% spike
            anomaly_detected = True
            anomaly_type = "usage_spike"

        # Determine status
        if dau_change < -20:
            status = "declining"
        elif dau_change > 10:
            status = "growing"
        else:
            status = "stable"

        # Recommended action
        recommended_action = self._get_recommended_action(
            status, anomaly_detected, seat_utilization
        )

        return {
            "status": status,
            "dau_current": dau_current,
            "mau_current": mau_current,
            "dau_change_pct": round(dau_change, 1),
            "mau_change_pct": round(mau_change, 1),
            "seat_utilization_pct": round(seat_utilization, 1),
            "anomaly_detected": anomaly_detected,
            "anomaly_type": anomaly_type,
            "recommended_action": recommended_action
        }

    def _get_recommended_action(
        self,
        status: str,
        anomaly: bool,
        seat_utilization: float
    ) -> str:
        """Get recommended action based on usage analysis."""
        if anomaly and status == "declining":
            return "Investigate usage drop immediately - possible team turnover or product issue"
        elif status == "declining":
            return "Monitor declining usage - schedule check-in with customer"
        elif seat_utilization < 40:
            return "Low seat utilization - potential downgrade risk or expansion opportunity"
        elif status == "growing":
            return "Positive growth - identify upsell opportunity"
        else:
            return "Usage stable - continue monitoring"

    def _format_usage_report(self, analysis: Dict[str, Any]) -> str:
        """Format usage monitoring report."""
        status_emoji = {
            "declining": "????",
            "stable": "??????",
            "growing": "????"
        }

        report = f"""**{status_emoji.get(analysis['status'], '????')} Usage Monitoring Report**

**Status:** {analysis['status'].title()}

**Current Metrics:**
- Daily Active Users (DAU): {analysis['dau_current']}
- Monthly Active Users (MAU): {analysis['mau_current']}
- Seat Utilization: {analysis['seat_utilization_pct']}%

**Changes:**
- DAU Change: {analysis['dau_change_pct']:+.1f}%
- MAU Change: {analysis['mau_change_pct']:+.1f}%
"""

        if analysis["anomaly_detected"]:
            report += f"\n**?????? Anomaly Detected:** {analysis['anomaly_type'].replace('_', ' ').title()}\n"

        report += f"\n**???? Recommended Action:**\n{analysis['recommended_action']}"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("Testing Usage Monitor Agent (TASK-2013)")
        print("=" * 60)

        agent = UsageMonitorAgent()

        state = create_initial_state("Monitor usage")
        state["entities"] = {
            "current_period_usage": {"dau": 10, "mau": 15, "total_seats": 20},
            "previous_period_usage": {"dau": 18, "mau": 20}
        }

        result = await agent.process(state)
        print(f"Status: {result['usage_status']}")
        print(f"\n{result['agent_response']}")

    asyncio.run(test())
