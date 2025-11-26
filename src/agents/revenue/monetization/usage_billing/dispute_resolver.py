"""
Dispute Resolver Agent - TASK-3015

Handles billing disputes and questions with usage data, explanations, and resolutions.
Applies credits and refunds when appropriate to maintain customer satisfaction.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("dispute_resolver", tier="revenue", category="monetization")
class DisputeResolver(BaseAgent):
    """
    Dispute Resolver Agent - Handles billing disputes with data and empathy.

    Handles:
    - Investigate billing disputes
    - Provide detailed charge explanations
    - Analyze usage data for discrepancies
    - Calculate fair resolutions
    - Apply credits and refunds
    - Prevent future disputes
    - Track dispute patterns
    - Escalate complex cases
    """

    # Dispute types and resolutions
    DISPUTE_TYPES = {
        "usage_discrepancy": {
            "description": "Customer disputes usage amount",
            "investigation_steps": [
                "Pull raw usage logs",
                "Compare with customer's records",
                "Check for API/tracking issues",
                "Verify meter accuracy"
            ],
            "resolution_options": ["full_refund", "partial_refund", "no_refund", "usage_correction"],
            "avg_resolution_time_hours": 4
        },
        "pricing_error": {
            "description": "Incorrect pricing or rate applied",
            "investigation_steps": [
                "Review pricing tier applied",
                "Check for promotional rates",
                "Verify plan configuration",
                "Confirm rate changes timeline"
            ],
            "resolution_options": ["full_refund", "credit", "rebill"],
            "avg_resolution_time_hours": 2
        },
        "double_charge": {
            "description": "Customer charged twice",
            "investigation_steps": [
                "Check payment records",
                "Verify invoice duplication",
                "Review billing cycle overlap",
                "Check payment processor logs"
            ],
            "resolution_options": ["full_refund", "immediate"],
            "avg_resolution_time_hours": 1
        },
        "cancellation_charge": {
            "description": "Charged after cancellation",
            "investigation_steps": [
                "Check cancellation date",
                "Verify billing period",
                "Review cancellation policy",
                "Check if proration applied"
            ],
            "resolution_options": ["full_refund", "partial_refund", "no_refund"],
            "avg_resolution_time_hours": 3
        },
        "unexpected_overage": {
            "description": "Surprise overage charges",
            "investigation_steps": [
                "Check overage alert history",
                "Verify usage spike",
                "Review notification delivery",
                "Check customer acknowledgment"
            ],
            "resolution_options": ["partial_refund", "credit", "waive_first_time"],
            "avg_resolution_time_hours": 4
        },
        "unclear_charges": {
            "description": "Customer doesn't understand bill",
            "investigation_steps": [
                "Review invoice line items",
                "Explain each charge",
                "Provide usage breakdown",
                "Clarify pricing model"
            ],
            "resolution_options": ["explanation_only", "goodwill_credit"],
            "avg_resolution_time_hours": 1
        }
    }

    # Resolution policies
    RESOLUTION_POLICIES = {
        "full_refund": {
            "conditions": ["clear_billing_error", "double_charge", "system_issue"],
            "requires_approval": False,
            "max_amount": 10000
        },
        "partial_refund": {
            "conditions": ["shared_responsibility", "first_time_issue", "goodwill"],
            "requires_approval": True,
            "max_amount": 5000,
            "typical_percentage": 0.50
        },
        "credit": {
            "conditions": ["customer_satisfaction", "minor_issue", "explanation_insufficient"],
            "requires_approval": False,
            "max_amount": 1000
        },
        "waive_first_time": {
            "conditions": ["first_overage", "no_alert_received", "small_amount"],
            "requires_approval": False,
            "max_amount": 500
        }
    }

    # Escalation criteria
    ESCALATION_CRITERIA = {
        "high_value": 5000,  # Disputes over $5k escalate
        "repeat_disputes": 3,  # 3+ disputes in 6 months
        "legal_threat": True,  # Customer mentions legal action
        "public_complaint": True,  # Social media/review site mention
    }

    def __init__(self):
        config = AgentConfig(
            name="dispute_resolver",
            type=AgentType.SPECIALIST,
             # Sonnet for nuanced resolution
            temperature=0.3,
            max_tokens=600,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="monetization",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Investigate and resolve billing dispute.

        Args:
            state: Current agent state with dispute details

        Returns:
            Updated state with resolution
        """
        self.logger.info("dispute_resolver_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Classify dispute type
        dispute_type = self._classify_dispute(message, customer_metadata)

        # Extract dispute details
        dispute_details = self._extract_dispute_details(
            message,
            customer_metadata,
            dispute_type
        )

        # Investigate dispute
        investigation = await self._investigate_dispute(
            dispute_type,
            dispute_details,
            customer_metadata
        )

        # Determine if valid dispute
        is_valid_dispute = self._validate_dispute(investigation, dispute_details)

        # Calculate resolution
        resolution = self._calculate_resolution(
            dispute_type,
            investigation,
            is_valid_dispute,
            dispute_details,
            customer_metadata
        )

        # Check if escalation needed
        should_escalate = self._check_escalation_needed(
            resolution,
            dispute_details,
            customer_metadata
        )

        # Generate prevention recommendations
        prevention_steps = self._generate_prevention_steps(
            dispute_type,
            investigation
        )

        # Search KB for dispute resolution guides
        kb_results = await self.search_knowledge_base(
            f"billing dispute resolution {dispute_type}",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_dispute_response(
            message,
            dispute_type,
            investigation,
            is_valid_dispute,
            resolution,
            prevention_steps,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.88
        state["dispute_type"] = dispute_type
        state["dispute_details"] = dispute_details
        state["investigation"] = investigation
        state["is_valid_dispute"] = is_valid_dispute
        state["resolution"] = resolution
        state["prevention_steps"] = prevention_steps
        state["status"] = "resolved"

        # Handle escalation
        if should_escalate:
            state["should_escalate"] = True
            state["escalation_reason"] = f"Billing dispute requires manager approval: {resolution.get('reason', 'Complex case')}"

        self.logger.info(
            "dispute_resolver_completed",
            dispute_type=dispute_type,
            is_valid=is_valid_dispute,
            resolution_type=resolution.get("type"),
            amount=resolution.get("amount", 0),
            escalated=should_escalate
        )

        return state

    def _classify_dispute(self, message: str, customer_metadata: Dict) -> str:
        """Classify the type of billing dispute"""
        message_lower = message.lower()

        # Check for dispute type keywords
        if any(word in message_lower for word in ["double", "twice", "charged twice", "duplicate"]):
            return "double_charge"
        elif any(word in message_lower for word in ["canceled", "cancelled", "after cancellation"]):
            return "cancellation_charge"
        elif any(word in message_lower for word in ["usage", "didn't use", "incorrect usage"]):
            return "usage_discrepancy"
        elif any(word in message_lower for word in ["price", "rate", "wrong amount", "pricing"]):
            return "pricing_error"
        elif any(word in message_lower for word in ["overage", "surprise", "unexpected charge"]):
            return "unexpected_overage"
        elif any(word in message_lower for word in ["don't understand", "unclear", "explain", "what is"]):
            return "unclear_charges"
        else:
            return "unclear_charges"  # Default

    def _extract_dispute_details(
        self,
        message: str,
        customer_metadata: Dict,
        dispute_type: str
    ) -> Dict[str, Any]:
        """Extract details about the dispute"""
        return {
            "disputed_amount": customer_metadata.get("disputed_amount", 0),
            "disputed_invoice_id": customer_metadata.get("disputed_invoice_id"),
            "dispute_date": datetime.now().isoformat(),
            "customer_claim": message,
            "dispute_type": dispute_type,
            "customer_history": customer_metadata.get("dispute_history", [])
        }

    async def _investigate_dispute(
        self,
        dispute_type: str,
        dispute_details: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Investigate the dispute following type-specific steps"""
        investigation = {
            "steps_completed": [],
            "findings": [],
            "supporting_data": {},
            "conclusion": ""
        }

        dispute_config = self.DISPUTE_TYPES.get(dispute_type, {})
        steps = dispute_config.get("investigation_steps", [])

        # Simulate investigation steps
        for step in steps:
            investigation["steps_completed"].append(step)

            # Simulate findings based on step
            if "usage logs" in step.lower():
                investigation["supporting_data"]["usage_logs"] = {
                    "source": "system_metrics",
                    "period": "last_30_days",
                    "verified": True
                }
                investigation["findings"].append("Usage logs verified against system metrics")

            elif "pricing" in step.lower():
                investigation["supporting_data"]["pricing"] = {
                    "plan_rate": customer_metadata.get("plan_rate"),
                    "applied_rate": customer_metadata.get("applied_rate"),
                    "matches": customer_metadata.get("plan_rate") == customer_metadata.get("applied_rate")
                }

            elif "payment" in step.lower():
                investigation["supporting_data"]["payments"] = {
                    "transaction_count": customer_metadata.get("payment_count", 1),
                    "duplicate_found": customer_metadata.get("payment_count", 1) > 1
                }

            elif "cancellation" in step.lower():
                investigation["supporting_data"]["cancellation"] = {
                    "cancellation_date": customer_metadata.get("cancellation_date"),
                    "billing_period_end": customer_metadata.get("period_end"),
                    "within_period": True
                }

        # Draw conclusion
        investigation["conclusion"] = "Investigation completed - findings documented"
        investigation["estimated_resolution_time_hours"] = dispute_config.get("avg_resolution_time_hours", 2)

        return investigation

    def _validate_dispute(
        self,
        investigation: Dict,
        dispute_details: Dict
    ) -> bool:
        """Determine if dispute is valid based on investigation"""
        findings = investigation.get("findings", [])
        supporting_data = investigation.get("supporting_data", {})

        # Check for clear errors
        if "pricing" in supporting_data:
            if not supporting_data["pricing"].get("matches", True):
                return True  # Valid - pricing error

        if "payments" in supporting_data:
            if supporting_data["payments"].get("duplicate_found", False):
                return True  # Valid - double charge

        if "usage_logs" in supporting_data:
            if not supporting_data["usage_logs"].get("verified", True):
                return True  # Valid - usage tracking issue

        # Default to giving benefit of doubt for first-time disputes
        if len(dispute_details.get("customer_history", [])) == 0:
            return True

        return False  # Not clearly valid

    def _calculate_resolution(
        self,
        dispute_type: str,
        investigation: Dict,
        is_valid: bool,
        dispute_details: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate appropriate resolution"""
        resolution = {
            "type": "no_action",
            "amount": 0.0,
            "description": "",
            "requires_approval": False,
            "reasoning": []
        }

        disputed_amount = dispute_details.get("disputed_amount", 0)
        customer_history = dispute_details.get("customer_history", [])

        if not is_valid:
            resolution["type"] = "explanation_only"
            resolution["description"] = "Provide detailed explanation of charges"
            resolution["reasoning"].append("Charges are accurate based on investigation")

            # Goodwill credit for long-time customers
            if customer_metadata.get("account_age_days", 0) > 365:
                resolution["type"] = "credit"
                resolution["amount"] = min(100, disputed_amount * 0.10)  # 10% goodwill credit, max $100
                resolution["description"] = "Goodwill credit for valued customer"
                resolution["reasoning"].append("Goodwill gesture for customer retention")

            return resolution

        # Valid dispute - determine resolution type
        if dispute_type == "double_charge":
            resolution["type"] = "full_refund"
            resolution["amount"] = disputed_amount
            resolution["description"] = "Full refund for duplicate charge"
            resolution["reasoning"].append("Clear system error - duplicate payment")

        elif dispute_type == "pricing_error":
            # Calculate correct amount
            correct_amount = disputed_amount * 0.70  # Assume 30% overcharge
            refund_amount = disputed_amount - correct_amount

            resolution["type"] = "partial_refund"
            resolution["amount"] = refund_amount
            resolution["description"] = "Refund difference from pricing error"
            resolution["reasoning"].append("Incorrect rate applied - corrected")

        elif dispute_type == "unexpected_overage":
            # First-time overage - waive 50%
            if len(customer_history) == 0:
                resolution["type"] = "waive_first_time"
                resolution["amount"] = disputed_amount * 0.50
                resolution["description"] = "First-time overage - 50% waived"
                resolution["reasoning"].append("No prior overage alerts - goodwill gesture")
            else:
                resolution["type"] = "credit"
                resolution["amount"] = disputed_amount * 0.25  # 25% credit
                resolution["description"] = "Partial credit for overage dispute"
                resolution["reasoning"].append("Overage alerts were sent - partial credit as goodwill")

        elif dispute_type == "cancellation_charge":
            # Check if charge was within billing period
            if investigation["supporting_data"].get("cancellation", {}).get("within_period", False):
                resolution["type"] = "explanation_only"
                resolution["description"] = "Charge valid for active billing period"
                resolution["reasoning"].append("Cancellation effective next period per terms")
            else:
                resolution["type"] = "full_refund"
                resolution["amount"] = disputed_amount
                resolution["description"] = "Full refund for post-cancellation charge"
                resolution["reasoning"].append("Charged after cancellation effective date")

        elif dispute_type == "usage_discrepancy":
            resolution["type"] = "partial_refund"
            resolution["amount"] = disputed_amount * 0.50  # 50% refund
            resolution["description"] = "Partial refund due to usage tracking uncertainty"
            resolution["reasoning"].append("Usage logs show discrepancy - split difference")

        else:  # unclear_charges
            resolution["type"] = "credit"
            resolution["amount"] = 50  # Small goodwill credit
            resolution["description"] = "Goodwill credit for confusion"
            resolution["reasoning"].append("Improve invoice clarity")

        # Check approval requirements
        policy = self.RESOLUTION_POLICIES.get(resolution["type"], {})
        if resolution["amount"] > policy.get("max_amount", 0):
            resolution["requires_approval"] = True

        return resolution

    def _check_escalation_needed(
        self,
        resolution: Dict,
        dispute_details: Dict,
        customer_metadata: Dict
    ) -> bool:
        """Check if dispute should be escalated"""

        # High-value disputes
        if resolution.get("amount", 0) >= self.ESCALATION_CRITERIA["high_value"]:
            return True

        # Requires approval
        if resolution.get("requires_approval", False):
            return True

        # Repeat disputes
        if len(dispute_details.get("customer_history", [])) >= self.ESCALATION_CRITERIA["repeat_disputes"]:
            return True

        # Legal threats (would need sentiment analysis in real implementation)
        message = dispute_details.get("customer_claim", "").lower()
        if any(word in message for word in ["lawyer", "attorney", "legal action", "sue"]):
            return True

        return False

    def _generate_prevention_steps(
        self,
        dispute_type: str,
        investigation: Dict
    ) -> List[str]:
        """Generate steps to prevent future similar disputes"""
        prevention = []

        if dispute_type == "unexpected_overage":
            prevention.append("Enable overage alerts at 80% threshold")
            prevention.append("Set up usage monitoring dashboard")
            prevention.append("Review plan limits alignment with usage")

        elif dispute_type == "unclear_charges":
            prevention.append("Provide more detailed invoice line items")
            prevention.append("Send usage summary before bill")
            prevention.append("Improve billing documentation")

        elif dispute_type == "usage_discrepancy":
            prevention.append("Implement usage dashboard for customer visibility")
            prevention.append("Send weekly usage reports")
            prevention.append("Verify tracking accuracy")

        elif dispute_type == "pricing_error":
            prevention.append("Audit pricing configuration")
            prevention.append("Send pricing change notifications")
            prevention.append("Verify rate changes in billing system")

        return prevention

    async def _generate_dispute_response(
        self,
        message: str,
        dispute_type: str,
        investigation: Dict,
        is_valid: bool,
        resolution: Dict,
        prevention_steps: List[str],
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate empathetic dispute resolution response"""

        # Build investigation summary
        investigation_summary = f"""
Dispute Type: {dispute_type.replace('_', ' ').title()}
Investigation Steps: {len(investigation['steps_completed'])}
Findings: {len(investigation['findings'])}
Valid Dispute: {'Yes' if is_valid else 'No'}
"""

        # Build resolution summary
        resolution_summary = f"""
Resolution Type: {resolution['type'].replace('_', ' ').title()}
Amount: ${resolution['amount']:.2f}
Description: {resolution['description']}
Requires Approval: {'Yes' if resolution.get('requires_approval') else 'No'}
"""

        # Build prevention context
        prevention_context = ""
        if prevention_steps:
            prevention_context = "\n\nPrevention Measures:\n"
            prevention_context += "\n".join(f"- {step}" for step in prevention_steps)

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelated Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Dispute Resolver specialist handling billing disputes with empathy and fairness.

Customer: {customer_metadata.get('company', 'Customer')}
{investigation_summary}
{resolution_summary}

Your response should:
1. Acknowledge their concern and apologize for frustration
2. Explain the investigation conducted
3. Present findings clearly and transparently
4. Explain the resolution decision and reasoning
5. Detail what action will be taken (refund, credit, etc.)
6. Provide prevention steps for future
7. Be empathetic and customer-focused
8. Build trust through transparency
9. Thank them for bringing it to attention
10. Offer to answer any follow-up questions

Tone: Empathetic, professional, solution-oriented"""

        user_prompt = f"""Customer dispute: {message}

Investigation Reasoning:
{chr(10).join(f'- {reason}' for reason in resolution.get('reasoning', []))}

{prevention_context}

{kb_context}

Generate an empathetic dispute resolution response."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[]  # Dispute analysis uses request context only
        )
        return response
