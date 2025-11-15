"""
Payment Troubleshooter - Debugs failed payments and provides solutions.

This agent diagnoses payment failures and guides customers through resolution,
handling declined cards, expired cards, 3DS failures, and fraud flags.
"""

from typing import Dict, Any, Optional, List

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("payment_troubleshooter", tier="essential", category="billing")
class PaymentTroubleshooter(BaseAgent):
    """
    Payment Troubleshooter Agent.

    Handles payment failure diagnosis and resolution:
    - Declined cards
    - Expired cards
    - Insufficient funds
    - 3D Secure authentication failures
    - Fraud flags and security holds
    - Bank authorization issues
    """

    # Error code mapping
    ERROR_CODES = {
        "card_declined": {
            "description": "Your card was declined by your bank",
            "category": "card_issue",
            "severity": "high"
        },
        "expired_card": {
            "description": "Your card has expired",
            "category": "card_issue",
            "severity": "high"
        },
        "insufficient_funds": {
            "description": "Insufficient funds in account",
            "category": "funds",
            "severity": "high"
        },
        "3ds_failed": {
            "description": "3D Secure authentication failed",
            "category": "authentication",
            "severity": "medium"
        },
        "3ds_timeout": {
            "description": "3D Secure authentication timed out",
            "category": "authentication",
            "severity": "medium"
        },
        "fraud_suspected": {
            "description": "Transaction flagged as potential fraud",
            "category": "fraud",
            "severity": "high"
        },
        "card_not_supported": {
            "description": "Card type not supported",
            "category": "card_issue",
            "severity": "high"
        },
        "incorrect_cvc": {
            "description": "Incorrect CVC/CVV code",
            "category": "card_issue",
            "severity": "medium"
        },
        "incorrect_zip": {
            "description": "Incorrect billing ZIP code",
            "category": "card_issue",
            "severity": "medium"
        },
        "processing_error": {
            "description": "Payment processor error",
            "category": "system",
            "severity": "medium"
        },
        "rate_limit": {
            "description": "Too many payment attempts",
            "category": "system",
            "severity": "low"
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="payment_troubleshooter",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE
            ],
            kb_category="billing",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process payment failure troubleshooting.

        Args:
            state: Current state with payment failure details

        Returns:
            Updated state with diagnosis and solution
        """
        self.logger.info("payment_troubleshooter_processing_started")

        # Update state
        state = self.update_state(state)

        user_message = state.get("current_message", "")
        customer_metadata = state.get("customer_metadata", {})

        # Get payment error code from entities or metadata
        payment_error = self._extract_payment_error(state, customer_metadata)

        self.logger.debug(
            "payment_troubleshooting_details",
            message_preview=user_message[:100],
            payment_error=payment_error,
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"]
        )

        # Diagnose issue
        diagnosis = self._diagnose_payment_failure(payment_error, customer_metadata)

        # Get solution steps
        solution = self._get_solution(diagnosis, customer_metadata)

        # Build response
        response = self._format_troubleshooting_response(
            diagnosis,
            solution,
            customer_metadata
        )

        state["agent_response"] = response
        state["payment_diagnosis"] = diagnosis["category"]
        state["payment_error_code"] = payment_error
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "payment_troubleshooting_completed",
            customer_id=state.get("customer_id"),
            error_code=payment_error,
            category=diagnosis["category"]
        )

        return state

    def _extract_payment_error(
        self,
        state: AgentState,
        customer_metadata: Dict
    ) -> str:
        """
        Extract payment error code from state or metadata.

        Args:
            state: Current state
            customer_metadata: Customer data

        Returns:
            Error code string
        """
        # Check entities first
        entities = state.get("entities", {})
        if "payment_error_code" in entities:
            return entities["payment_error_code"]

        # Check customer metadata
        if "last_payment_error" in customer_metadata:
            return customer_metadata["last_payment_error"]

        # Try to infer from message
        message = state.get("current_message", "").lower()

        if "declined" in message or "denied" in message:
            return "card_declined"
        elif "expired" in message:
            return "expired_card"
        elif "3d secure" in message or "3ds" in message or "authentication" in message:
            return "3ds_failed"
        elif "fraud" in message:
            return "fraud_suspected"
        elif "insufficient" in message or "not enough" in message:
            return "insufficient_funds"
        elif "cvc" in message or "cvv" in message or "security code" in message:
            return "incorrect_cvc"
        elif "zip" in message or "postal code" in message:
            return "incorrect_zip"
        else:
            return "card_declined"  # Default

    def _diagnose_payment_failure(
        self,
        error_code: str,
        customer_metadata: Dict
    ) -> Dict:
        """
        Diagnose payment failure.

        Args:
            error_code: Payment error code
            customer_metadata: Customer data

        Returns:
            Dict with diagnosis details
        """
        error_info = self.ERROR_CODES.get(
            error_code,
            {
                "description": "Unknown payment error",
                "category": "unknown",
                "severity": "medium"
            }
        )

        self.logger.debug(
            "payment_diagnosis",
            error_code=error_code,
            category=error_info["category"],
            severity=error_info["severity"]
        )

        return {
            "error_code": error_code,
            "description": error_info["description"],
            "category": error_info["category"],
            "severity": error_info["severity"]
        }

    def _get_solution(
        self,
        diagnosis: Dict,
        customer_metadata: Dict
    ) -> Dict:
        """
        Get solution steps based on diagnosis.

        Args:
            diagnosis: Diagnosis details
            customer_metadata: Customer data

        Returns:
            Dict with solution steps and help text
        """
        category = diagnosis["category"]

        if category == "card_issue":
            if diagnosis["error_code"] == "expired_card":
                steps = [
                    "Update your payment method with a new card",
                    "Go to Settings → Billing → Payment Method",
                    "Click 'Update Card' and enter new card details",
                    "Click 'Save' to update"
                ]
                help_text = "Your card has expired. Please update it with a current card."

            elif diagnosis["error_code"] == "incorrect_cvc":
                steps = [
                    "Re-enter your payment information",
                    "Double-check the CVC/CVV code (3-4 digits on back of card)",
                    "Make sure you're entering it correctly",
                    "Try the payment again"
                ]
                help_text = "The security code (CVC/CVV) doesn't match. Please verify and try again."

            elif diagnosis["error_code"] == "incorrect_zip":
                steps = [
                    "Update your billing address",
                    "Go to Settings → Billing → Billing Address",
                    "Enter the ZIP code that matches your card's billing address",
                    "Save and try payment again"
                ]
                help_text = "The ZIP code doesn't match your card's billing address."

            else:  # Generic card issue
                steps = [
                    "Contact your bank to authorize the transaction",
                    "Try a different payment method",
                    "Update your card information in Settings → Billing",
                    "If issue persists, contact our support team"
                ]
                help_text = "Your card was declined. This usually requires contacting your bank."

        elif category == "authentication":
            if "timeout" in diagnosis["error_code"]:
                steps = [
                    "Try the payment again",
                    "When the authentication popup appears, complete it quickly",
                    "Make sure you have access to your phone for SMS/app authentication",
                    "Ensure popup blockers aren't blocking the authentication window"
                ]
                help_text = "The 3D Secure authentication timed out. Please try again and complete the authentication promptly."
            else:
                steps = [
                    "Check your phone for an authentication request from your bank",
                    "Approve the transaction in your banking app",
                    "Try the payment again",
                    "Make sure you complete the 3D Secure authentication when prompted"
                ]
                help_text = "3D Secure authentication helps protect against fraud. Please complete it when prompted."

        elif category == "funds":
            steps = [
                "Check your account balance",
                "Add funds to your account",
                "Try a different payment method",
                "Contact your bank if you believe this is an error"
            ]
            help_text = "There aren't sufficient funds in your account. Please add funds or use a different payment method."

        elif category == "fraud":
            steps = [
                "Contact your bank to verify the transaction",
                "Confirm with your bank that you authorized this payment",
                "Ask them to remove the fraud flag",
                "Try the payment again after bank confirmation"
            ]
            help_text = "This transaction was flagged for security. Please contact your bank to authorize it."

        elif category == "system":
            if "rate_limit" in diagnosis["error_code"]:
                steps = [
                    "Wait 15-30 minutes before trying again",
                    "Too many payment attempts can trigger security measures",
                    "If urgent, contact our support team for assistance"
                ]
                help_text = "Too many payment attempts detected. Please wait before trying again."
            else:
                steps = [
                    "Wait a few minutes and try again",
                    "If issue persists, try a different payment method",
                    "Contact our support team if problem continues"
                ]
                help_text = "There was a temporary processing error. Please try again."

        else:  # Unknown
            steps = [
                "Try the payment again",
                "Try a different payment method",
                "Contact our support team for assistance"
            ]
            help_text = "We encountered an unexpected issue. Please try again or contact support."

        return {
            "steps": steps,
            "help_text": help_text
        }

    def _format_troubleshooting_response(
        self,
        diagnosis: Dict,
        solution: Dict,
        customer_metadata: Dict
    ) -> str:
        """
        Format troubleshooting response.

        Args:
            diagnosis: Diagnosis details
            solution: Solution steps
            customer_metadata: Customer data

        Returns:
            Formatted response message
        """
        steps_formatted = "\n".join([f"{i+1}. {step}" for i, step in enumerate(solution["steps"])])

        message = f"""I see your payment failed. Let me help you resolve this.

**What happened:**
{diagnosis['description']}

**How to fix it:**

{steps_formatted}

**Additional information:**
{solution['help_text']}

**Quick links:**
- Update payment method: Settings → Billing → Payment Method
- View payment history: Settings → Billing → Payment History
- Contact support: help@ourcompany.com

If you continue to have issues after following these steps, please let me know and I can escalate this to our payment specialist team.

Is there anything else I can help you with?"""

        return message


if __name__ == "__main__":
    # Test payment troubleshooter
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING PAYMENT TROUBLESHOOTER")
        print("=" * 60)

        troubleshooter = PaymentTroubleshooter()

        # Test 1: Card declined
        state1 = create_initial_state(
            "My payment was declined",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "last_payment_error": "card_declined"
                }
            }
        )

        result1 = await troubleshooter.process(state1)

        print(f"\n{'='*60}")
        print("TEST 1: Card Declined")
        print(f"{'='*60}")
        print(f"Diagnosis: {result1.get('payment_diagnosis')}")
        print(f"Error code: {result1.get('payment_error_code')}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: 3DS authentication failed
        state2 = create_initial_state(
            "3D Secure authentication failed",
            context={
                "customer_metadata": {
                    "plan": "basic"
                }
            }
        )
        state2["entities"] = {"payment_error_code": "3ds_failed"}

        result2 = await troubleshooter.process(state2)

        print(f"\n{'='*60}")
        print("TEST 2: 3DS Failed")
        print(f"{'='*60}")
        print(f"Diagnosis: {result2.get('payment_diagnosis')}")
        print(f"\nResponse:\n{result2['agent_response'][:300]}...")

        # Test 3: Expired card
        state3 = create_initial_state(
            "My card expired",
            context={
                "customer_metadata": {
                    "plan": "premium"
                }
            }
        )

        result3 = await troubleshooter.process(state3)

        print(f"\n{'='*60}")
        print("TEST 3: Expired Card")
        print(f"{'='*60}")
        print(f"Diagnosis: {result3.get('payment_diagnosis')}")
        print(f"\nResponse:\n{result3['agent_response'][:300]}...")

    asyncio.run(test())
