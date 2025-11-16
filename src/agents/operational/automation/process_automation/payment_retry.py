"""
Payment Retry Agent - TASK-2218

Auto-retries failed payment transactions with exponential backoff,
card update requests, and dunning management.
"""

from typing import Dict, Any
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("payment_retry", tier="operational", category="automation")
class PaymentRetryAgent(BaseAgent):
    """Payment Retry Agent - Auto-retries failed payments."""

    RETRY_SCHEDULE = [1, 3, 7, 14]  # Days between retries

    def __init__(self):
        config = AgentConfig(
            name="payment_retry",
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
        """Retry failed payment."""
        self.logger.info("payment_retry_started")
        state = self.update_state(state)

        customer_metadata = state.get("customer_metadata", {})
        payment_data = state.get("entities", {})

        # Retry payment
        retry_result = await self._retry_payment(customer_metadata, payment_data)

        # If still failed, schedule next retry or request card update
        if retry_result['status'] == 'failed':
            next_action = await self._handle_failed_retry(retry_result, customer_metadata)
        else:
            next_action = None

        response = f"""**Payment Retry {retry_result['status'].title()}**

Transaction ID: {retry_result['transaction_id']}
Amount: ${payment_data.get('amount', 0):,.2f}
Attempt: {retry_result['attempt_number']}
Status: {retry_result['status'].title()}

"""
        if next_action:
            response += f"Next retry scheduled for: {next_action['next_retry_date']}"

        state["agent_response"] = response
        state["retry_result"] = retry_result
        state["response_confidence"] = 0.93
        state["status"] = "resolved"

        self.logger.info("payment_retry_completed", status=retry_result['status'])
        return state

    async def _retry_payment(self, customer: Dict, payment: Dict) -> Dict:
        """Attempt to retry payment."""
        import random
        success = random.choice([True, False])  # Mock 50% success rate

        return {
            "transaction_id": f"TXN-{datetime.utcnow().timestamp()}",
            "status": "success" if success else "failed",
            "attempt_number": payment.get("retry_count", 1),
            "attempted_at": datetime.utcnow().isoformat()
        }

    async def _handle_failed_retry(self, retry_result: Dict, customer: Dict) -> Dict:
        """Handle failed retry - schedule next or request card update."""
        attempt = retry_result['attempt_number']

        if attempt < len(self.RETRY_SCHEDULE):
            next_retry = datetime.utcnow() + timedelta(days=self.RETRY_SCHEDULE[attempt])
            return {
                "action": "schedule_retry",
                "next_retry_date": next_retry.strftime('%Y-%m-%d')
            }
        else:
            return {
                "action": "request_card_update",
                "notification_sent": True
            }
