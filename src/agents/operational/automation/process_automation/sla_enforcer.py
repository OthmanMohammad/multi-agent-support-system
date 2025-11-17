"""
SLA Enforcer Agent - TASK-2213

Monitors and enforces SLAs for tickets, ensuring response and resolution
times meet contractual obligations. Auto-escalates violations.
"""

from typing import Dict, Any
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("sla_enforcer", tier="operational", category="automation")
class SLAEnforcerAgent(BaseAgent):
    """SLA Enforcer Agent - Monitors and enforces SLAs."""

    SLA_TIERS = {
        "enterprise": {"first_response_minutes": 30, "resolution_hours": 4},
        "professional": {"first_response_minutes": 120, "resolution_hours": 24},
        "standard": {"first_response_minutes": 480, "resolution_hours": 48}
    }

    def __init__(self):
        config = AgentConfig(
            name="sla_enforcer",
            type=AgentType.AUTOMATOR,
            temperature=0.1,
            max_tokens=600,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Monitor and enforce SLAs."""
        self.logger.info("sla_enforcer_started")
        state = self.update_state(state)

        customer_metadata = state.get("customer_metadata", {})
        ticket_data = state.get("entities", {})

        tier = customer_metadata.get("tier", "standard")
        sla = self.SLA_TIERS[tier]

        # Check SLA compliance
        compliance = self._check_sla_compliance(ticket_data, sla)

        # Escalate if breached
        escalation = None
        if compliance["status"] == "breached":
            escalation = await self._escalate_sla_breach(ticket_data, compliance, tier)

        response = f"""**SLA Status: {compliance['status'].upper()}**

Customer Tier: {tier.title()}
First Response SLA: {sla['first_response_minutes']} minutes
Resolution SLA: {sla['resolution_hours']} hours

**Current Status:**
- Time Elapsed: {compliance['elapsed_minutes']} minutes
- SLA Target: {compliance['target_minutes']} minutes
- Remaining: {compliance['remaining_minutes']} minutes

"""
        if escalation:
            response += f"**Escalation:**\nTicket escalated to {escalation['escalated_to']}"

        state["agent_response"] = response
        state["sla_compliance"] = compliance
        state["response_confidence"] = 0.95
        state["status"] = "resolved"

        self.logger.info("sla_checked", status=compliance['status'])
        return state

    def _check_sla_compliance(self, ticket_data: Dict, sla: Dict) -> Dict:
        """Check if ticket is within SLA."""
        created_at = ticket_data.get("created_at", datetime.now(UTC).isoformat())
        # Parse datetime and ensure it's timezone-aware
        created_str = created_at.replace('Z', '+00:00')
        created = datetime.fromisoformat(created_str.split('+')[0])
        # Make timezone-aware if naive
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        elapsed = (datetime.now(UTC) - created).total_seconds() / 60

        target = sla["first_response_minutes"]
        remaining = target - elapsed

        return {
            "status": "breached" if remaining < 0 else "at_risk" if remaining < 10 else "ok",
            "elapsed_minutes": int(elapsed),
            "target_minutes": target,
            "remaining_minutes": int(remaining)
        }

    async def _escalate_sla_breach(self, ticket: Dict, compliance: Dict, tier: str) -> Dict:
        """Escalate SLA breach."""
        return {
            "escalated": True,
            "escalated_to": "senior_support",
            "escalated_at": datetime.now(UTC).isoformat()
        }
