"""
Risk Alert Agent - TASK-2015

Aggregates risk signals, prioritizes alerts, and routes to appropriate owners.
Manages escalation and SLA tracking for at-risk customers.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("risk_alert", tier="revenue", category="customer_success")
class RiskAlertAgent(BaseAgent):
    """
    Risk Alert Agent.

    Handles:
    - Aggregating multiple risk signals
    - Prioritizing alerts by severity
    - Routing to correct owner (CSM, manager, VP)
    - Setting appropriate SLAs
    - Escalation path management
    """

    # Alert severity levels
    SEVERITY_LEVELS = {
        "critical": {"sla_hours": 4, "escalation": ["csm", "cs_manager", "vp_cs"]},
        "high": {"sla_hours": 24, "escalation": ["csm", "cs_manager"]},
        "medium": {"sla_hours": 72, "escalation": ["csm"]},
        "low": {"sla_hours": 168, "escalation": ["csm"]}
    }

    def __init__(self):
        config = AgentConfig(
            name="risk_alert",
            type=AgentType.SPECIALIST,
            temperature=0.2,
            max_tokens=400,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Generate and route risk alert."""
        self.logger.info("risk_alert_processing_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")

        # Get risk signals
        risk_signals = state.get("entities", {}).get("risk_signals", [])

        # Generate alert
        alert = self._generate_alert(customer_id, risk_signals)

        # Format response
        response = self._format_alert(alert)

        state["agent_response"] = response
        state["alert_severity"] = alert["alert_severity"]
        state["assigned_to"] = alert["assigned_to"]
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "risk_alert_created",
            customer_id=customer_id,
            severity=alert["alert_severity"],
            assigned_to=alert["assigned_to"]
        )

        return state

    def _generate_alert(
        self,
        customer_id: str,
        risk_signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate risk alert from signals."""
        # Determine severity
        severity = self._calculate_severity(risk_signals)

        # Generate title and description
        title, description = self._generate_alert_content(risk_signals)

        # Determine assignment
        assigned_to = self._determine_owner(severity, customer_id)

        # Get SLA and escalation path
        sla_config = self.SEVERITY_LEVELS.get(severity, self.SEVERITY_LEVELS["medium"])

        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(risk_signals, severity)

        return {
            "alert_severity": severity,
            "alert_title": title,
            "description": description,
            "assigned_to": assigned_to,
            "escalation_path": sla_config["escalation"],
            "sla": f"Respond within {sla_config['sla_hours']} hours",
            "recommended_actions": recommended_actions,
            "created_at": datetime.now(UTC).isoformat()
        }

    def _calculate_severity(self, risk_signals: List[Dict[str, Any]]) -> str:
        """Calculate alert severity from risk signals."""
        if not risk_signals:
            return "low"

        # Count signals by type
        critical_signals = sum(1 for s in risk_signals if s.get("type") in ["churn_risk", "payment_failure"])
        high_signals = sum(1 for s in risk_signals if s.get("type") in ["health_decline", "usage_drop"])

        # Aggregate severity
        total_value = sum(s.get("value", 0) for s in risk_signals if isinstance(s.get("value"), (int, float)))

        if critical_signals >= 1 or total_value >= 80:
            return "critical"
        elif high_signals >= 2 or total_value >= 60:
            return "high"
        elif len(risk_signals) >= 2 or total_value >= 40:
            return "medium"
        else:
            return "low"

    def _generate_alert_content(self, risk_signals: List[Dict[str, Any]]) -> tuple:
        """Generate alert title and description."""
        if not risk_signals:
            return "Customer Health Alert", "General health monitoring alert"

        # Use primary signal for title
        primary_signal = risk_signals[0]
        signal_type = primary_signal.get("type", "health_issue")

        title_map = {
            "churn_risk": "High Churn Risk Alert",
            "health_decline": "Customer Health Decline",
            "usage_drop": "Product Usage Declined",
            "payment_failure": "Payment Failure Alert",
            "nps_detractor": "NPS Detractor Alert"
        }

        title = title_map.get(signal_type, "Customer At Risk")

        # Build description
        description = f"{len(risk_signals)} risk signal(s) detected: "
        description += ", ".join([s.get("type", "unknown").replace("_", " ") for s in risk_signals[:3]])

        return title, description

    def _determine_owner(self, severity: str, customer_id: str) -> str:
        """Determine who should be assigned the alert."""
        # In production, this would lookup the CSM from customer record
        # For now, return role-based assignment
        if severity == "critical":
            return "vp_customer_success"
        else:
            return "csm_assigned"

    def _generate_recommended_actions(
        self,
        risk_signals: List[Dict[str, Any]],
        severity: str
    ) -> List[Dict[str, str]]:
        """Generate recommended actions."""
        actions = []

        if severity in ["critical", "high"]:
            actions.append({
                "action": "Immediate customer call to understand issues",
                "priority": "critical",
                "estimated_effort": "1 hour"
            })

        for signal in risk_signals[:3]:
            signal_type = signal.get("type", "")

            if signal_type == "usage_drop":
                actions.append({
                    "action": "Investigate usage drop - review product analytics",
                    "priority": "high",
                    "estimated_effort": "30 minutes"
                })
            elif signal_type == "payment_failure":
                actions.append({
                    "action": "Contact billing to resolve payment issues",
                    "priority": "critical",
                    "estimated_effort": "15 minutes"
                })
            elif signal_type == "nps_detractor":
                actions.append({
                    "action": "Follow up on NPS feedback",
                    "priority": "high",
                    "estimated_effort": "30 minutes"
                })

        return actions[:5]  # Limit to top 5

    def _format_alert(self, alert: Dict[str, Any]) -> str:
        """Format risk alert."""
        severity = alert["alert_severity"]

        # Severity emoji
        emoji = {
            "critical": "????",
            "high": "????",
            "medium": "??????",
            "low": "??????"
        }

        report = f"""**{emoji.get(severity, '????')} {alert['alert_title']}**

**Severity:** {severity.upper()}
**Assigned To:** {alert['assigned_to']}
**SLA:** {alert['sla']}

**Description:**
{alert['description']}

**Escalation Path:**
{' ??? '.join(alert['escalation_path'])}

**???? Recommended Actions:**
"""

        for i, action in enumerate(alert['recommended_actions'], 1):
            report += f"{i}. **{action['action']}**\n"
            report += f"   - Priority: {action['priority'].upper()}\n"
            report += f"   - Estimated Effort: {action['estimated_effort']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("Testing Risk Alert Agent (TASK-2015)")
        print("=" * 60)

        agent = RiskAlertAgent()

        state = create_initial_state("Generate risk alert", context={"customer_id": "cust_123"})
        state["entities"] = {
            "risk_signals": [
                {"type": "churn_risk", "value": 85},
                {"type": "usage_drop", "value": 70},
                {"type": "nps_detractor", "value": 3}
            ]
        }

        result = await agent.process(state)
        print(f"Severity: {result['alert_severity']}")
        print(f"\n{result['agent_response']}")

    asyncio.run(test())
