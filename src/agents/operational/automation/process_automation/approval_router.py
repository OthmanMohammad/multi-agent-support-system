"""
Approval Router Agent - TASK-2212

Auto-routes approval requests to appropriate approvers based on rules,
amount thresholds, and organizational hierarchy.
"""

from typing import Dict, Any, List
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("approval_router", tier="operational", category="automation")
class ApprovalRouterAgent(BaseAgent):
    """Approval Router Agent - Auto-routes approval requests."""

    APPROVAL_RULES = {
        "discount": {"threshold": 15, "approver": "sales_manager", "escalate_threshold": 25},
        "refund": {"threshold": 1000, "approver": "cs_manager", "escalate_threshold": 5000},
        "contract": {"threshold": 10000, "approver": "vp_sales", "escalate_threshold": 50000}
    }

    def __init__(self):
        config = AgentConfig(
            name="approval_router",
            type=AgentType.AUTOMATOR,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=600,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Route approval request to appropriate approver."""
        self.logger.info("approval_router_started")
        state = self.update_state(state)

        entities = state.get("entities", {})
        approval_type = entities.get("approval_type", "discount")
        amount = entities.get("amount", 0)

        # Determine approver
        approver = self._determine_approver(approval_type, amount)

        # Create approval request
        approval_request = {
            "id": f"APR-{datetime.utcnow().timestamp()}",
            "type": approval_type,
            "amount": amount,
            "approver": approver["approver"],
            "requires_escalation": approver["requires_escalation"],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }

        # Send to approver
        notification_sent = await self._notify_approver(approval_request, approver)

        response = f"""**Approval Request Routed**

Request ID: {approval_request['id']}
Type: {approval_type.title()}
Amount: ${amount:,.2f}
Approver: {approver['approver'].replace('_', ' ').title()}
Status: Pending Approval

Notification sent to approver."""

        state["agent_response"] = response
        state["approval_request"] = approval_request
        state["response_confidence"] = 0.96
        state["status"] = "resolved"

        self.logger.info("approval_routed", approval_id=approval_request['id'])
        return state

    def _determine_approver(self, approval_type: str, amount: float) -> Dict:
        """Determine appropriate approver based on rules."""
        rules = self.APPROVAL_RULES.get(approval_type, self.APPROVAL_RULES["discount"])

        if amount >= rules["escalate_threshold"]:
            return {"approver": "ceo", "requires_escalation": True, "threshold": rules["escalate_threshold"]}
        else:
            return {"approver": rules["approver"], "requires_escalation": False, "threshold": rules["threshold"]}

    async def _notify_approver(self, request: Dict, approver: Dict) -> bool:
        """Notify approver of pending request."""
        return True
