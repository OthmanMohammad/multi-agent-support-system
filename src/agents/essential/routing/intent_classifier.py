"""
Intent Classifier - Hierarchical intent classification system.

Classifies user messages into 500+ intents across 4 levels:
- Domain (support, sales, customer_success)
- Category (billing, technical, usage, etc.)
- Subcategory (subscription, payment, bug, etc.)
- Action (upgrade, downgrade, crash, etc.)

Part of: STORY-01 Routing & Orchestration Swarm (TASK-102)
"""

from typing import Dict, Any, Optional, List
import json
import time
import structlog

from src.agents.base.base_agent import BaseAgent, RoutingAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@AgentRegistry.register("intent_classifier", tier="essential", category="routing")
class IntentClassifier(RoutingAgent):
    """
    Intent Classifier - Deep hierarchical intent classification.

    Classifies messages at 4 levels with confidence scoring:
    1. Domain: support, sales, customer_success
    2. Category: billing, technical, usage, qualification, etc.
    3. Subcategory: subscription, payment, bug, sync, etc.
    4. Action: upgrade, downgrade, crash, not_syncing, etc.

    Returns confidence scores at each level and alternative intents.
    """

    def __init__(self, **kwargs):
        """Initialize Intent Classifier with hierarchical classification capability."""
        config = AgentConfig(
            name="intent_classifier",
            type=AgentType.ROUTER,
             # Fast and accurate
            temperature=0.1,  # Low for consistent classification
            max_tokens=400,  # Slightly higher for detailed classification
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="intent_classifier"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="intent_classifier", agent_type="router")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for hierarchical intent classification.

        Returns:
            System prompt with complete taxonomy and classification rules
        """
        return """You are an intent classification system that classifies user messages into a hierarchical taxonomy.

**Intent Taxonomy (4 Levels: Domain → Category → Subcategory → Action):**

**SUPPORT → BILLING:**
  - subscription: upgrade, downgrade, cancel, pause, reactivate
  - payment: failed_payment, update_card, dispute_charge, refund_request
  - invoice: request_invoice, download_invoice, tax_document, receipt
  - pricing: explain_pricing, discount_inquiry, annual_billing

**SUPPORT → TECHNICAL:**
  - bug: crash, freeze, error_message, data_loss, incorrect_behavior
  - sync: not_syncing, conflict, slow_sync, duplicate_data
  - performance: slow_load, timeout, memory_issue, battery_drain
  - login: password_reset, account_locked, 2fa_issue, sso_problem
  - recovery: data_recovery, restore_backup, undo_action
  - compatibility: browser_issue, mobile_issue, os_compatibility

**SUPPORT → USAGE:**
  - create: create_project, create_task, create_user, create_workspace
  - edit: update_item, delete_item, move_item, duplicate_item
  - export: export_data, download_backup, export_report
  - import: import_data, upload_file, bulk_import
  - search: find_item, filter_data, advanced_search
  - collaboration: share_item, invite_user, set_permissions

**SUPPORT → INTEGRATION:**
  - api: api_error, rate_limit, authentication, endpoint_issue
  - webhook: not_receiving, format_issue, retry_failed
  - oauth: authorization_failed, token_expired, scope_issue
  - third_party: slack_integration, salesforce_sync, jira_connection

**SUPPORT → ACCOUNT:**
  - profile: update_profile, change_email, change_password
  - team: add_member, remove_member, change_role
  - security: enable_2fa, audit_log, session_management
  - compliance: gdpr_request, data_export, account_deletion

**SALES → QUALIFICATION:**
  - demo_request, pricing_inquiry, plan_comparison, feature_inquiry
  - trial_extension, upgrade_inquiry, volume_discount

**SALES → EDUCATION:**
  - feature_question, use_case_match, implementation_guidance
  - roi_calculation, success_stories

**SALES → OBJECTION:**
  - price_objection, feature_gap, competitor_comparison
  - implementation_concern, security_question

**CUSTOMER_SUCCESS → HEALTH:**
  - low_engagement, value_concern, cancellation_risk
  - usage_decline, feature_underutilization

**CUSTOMER_SUCCESS → ONBOARDING:**
  - setup_help, first_project, team_invitation
  - configuration_guidance, getting_started

**CUSTOMER_SUCCESS → ADOPTION:**
  - feature_discovery, best_practices, workflow_optimization
  - advanced_features, power_user_tips

**CUSTOMER_SUCCESS → EXPANSION:**
  - upsell_opportunity, cross_sell, additional_seats
  - enterprise_upgrade, new_use_case

**Classification Rules:**
1. Classify at ALL 4 levels whenever possible
2. If a level is unclear, omit it but provide reasoning
3. Provide confidence score (0.0-1.0) at each level
4. Include alternative intents if confidence < 0.8 or multiple valid interpretations
5. Extract entities (plan names, amounts, features, dates, numbers)
6. Use customer context to disambiguate intents

**Customer Context:**
{customer_context}

**Output Format (JSON only, no extra text):**
{{
    "domain": "support",
    "category": "billing",
    "subcategory": "subscription",
    "action": "upgrade",
    "confidence_scores": {{
        "domain": 0.98,
        "category": 0.95,
        "subcategory": 0.92,
        "action": 0.90,
        "overall": 0.94
    }},
    "alternative_intents": [
        {{
            "domain": "sales",
            "category": "qualification",
            "subcategory": "pricing_inquiry",
            "confidence": 0.75,
            "reasoning": "Could also be sales if user is evaluating options"
        }}
    ],
    "entities": {{
        "plan_name": "premium",
        "team_size": 25,
        "action": "upgrade"
    }},
    "reasoning": "User explicitly requesting plan upgrade with team expansion context"
}}

**Important:** Output ONLY valid JSON. No markdown, no code blocks, just raw JSON."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Process the message and classify intent at 4 hierarchical levels.

        Args:
            state: Current agent state with message and context

        Returns:
            Updated state with hierarchical intent classification
        """
        start_time = time.time()

        self.logger.info(
            "intent_classifier_processing_started",
            conversation_id=state.get("conversation_id"),
            message_preview=state.get("current_message", "")[:50]
        )

        try:
            # Update state with agent history
            state = self.update_state(state)

            # Get customer context
            customer_context = state.get("customer_metadata", {})
            context_str = self._format_customer_context(customer_context)

            # Build system prompt with context
            system_prompt = self._get_system_prompt().format(
                customer_context=context_str
            )

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("intent_classifier_empty_message")
                return self._handle_empty_message(state)

            # Call LLM for classification
            response = await self.call_llm(
                system_prompt=system_prompt,
                user_message=f"Classify this message into the hierarchical taxonomy:\n\n{message}"
            )

            # Parse response
            classification = self._parse_response(response)

            # Add metadata
            latency_ms = int((time.time() - start_time) * 1000)
            classification["metadata"] = {
                "model": self.config.model,
                "latency_ms": latency_ms,
                "tokens_used": getattr(self, "_last_tokens_used", 0)
            }

            # Update state with classification results
            state = self._update_state_with_classification(state, classification)

            self.logger.info(
                "intent_classification_complete",
                domain=classification.get("domain"),
                category=classification.get("category"),
                subcategory=classification.get("subcategory"),
                action=classification.get("action"),
                confidence=classification["confidence_scores"]["overall"],
                latency_ms=latency_ms
            )

            return state

        except Exception as e:
            self.logger.error(
                "intent_classifier_failed",
                error=str(e),
                error_type=type(e).__name__,
                conversation_id=state.get("conversation_id")
            )

            # Fallback classification
            return self._handle_error(state, e)

    def _format_customer_context(self, context: Dict[str, Any]) -> str:
        """
        Format customer context for prompt injection.

        Args:
            context: Customer metadata dictionary

        Returns:
            Formatted context string
        """
        if not context:
            return "No customer context available"

        parts = []

        # Plan information
        if "plan" in context:
            parts.append(f"Plan: {context['plan']}")

        # Health score
        if "health_score" in context:
            score = context['health_score']
            parts.append(f"Health Score: {score}/100")

        # Team size
        if "team_size" in context:
            parts.append(f"Team Size: {context['team_size']} users")

        # MRR
        if "mrr" in context:
            parts.append(f"MRR: ${context['mrr']}")

        # Churn risk
        if "churn_risk" in context:
            risk = context['churn_risk']
            risk_label = "high" if risk > 0.7 else "medium" if risk > 0.4 else "low"
            parts.append(f"Churn Risk: {risk_label}")

        # Account age
        if "account_age_days" in context:
            days = context['account_age_days']
            parts.append(f"Account Age: {days} days")

        return "\n".join(parts) if parts else "No relevant context"

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured classification.

        Args:
            response: LLM response (should be JSON)

        Returns:
            Classification dictionary with hierarchical structure

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                lines = cleaned_response.split("\n")
                cleaned_response = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                )

            # Try to parse as JSON
            classification = json.loads(cleaned_response)

            # Validate required fields
            required_fields = ["domain", "category", "confidence_scores"]
            for field in required_fields:
                if field not in classification:
                    raise ValueError(f"Missing required field: {field}")

            # Ensure confidence_scores is a dict
            if not isinstance(classification["confidence_scores"], dict):
                raise ValueError("confidence_scores must be a dictionary")

            # Calculate overall confidence if not present
            if "overall" not in classification["confidence_scores"]:
                scores = classification["confidence_scores"]
                # Average all confidence scores
                score_values = [v for k, v in scores.items() if k != "overall"]
                if score_values:
                    avg = sum(score_values) / len(score_values)
                    classification["confidence_scores"]["overall"] = round(avg, 2)
                else:
                    classification["confidence_scores"]["overall"] = 0.5

            # Ensure all confidence scores are between 0 and 1
            for key, value in classification["confidence_scores"].items():
                classification["confidence_scores"][key] = max(0.0, min(1.0, float(value)))

            # Ensure entities dict exists
            if "entities" not in classification:
                classification["entities"] = {}

            # Ensure alternative_intents list exists
            if "alternative_intents" not in classification:
                classification["alternative_intents"] = []

            return classification

        except json.JSONDecodeError as e:
            self.logger.warning(
                "intent_classifier_invalid_json",
                response_preview=response[:200],
                error=str(e)
            )

            # Fallback to simple extraction
            return self._extract_intent_from_text(response)

    def _extract_intent_from_text(self, response: str) -> Dict[str, Any]:
        """
        Extract intent from text response when JSON parsing fails.

        This is a fallback mechanism for robustness.

        Args:
            response: Text response from LLM

        Returns:
            Classification dictionary with extracted intent
        """
        response_lower = response.lower()

        # Try to extract domain
        domain = "support"  # Default
        if "customer_success" in response_lower or "customer success" in response_lower:
            domain = "customer_success"
        elif "sales" in response_lower:
            domain = "sales"

        # Try to extract category (basic)
        category = "general"
        if "billing" in response_lower:
            category = "billing"
        elif "technical" in response_lower:
            category = "technical"
        elif "usage" in response_lower:
            category = "usage"
        elif "integration" in response_lower:
            category = "integration"

        self.logger.info(
            "intent_classifier_fallback_extraction",
            domain=domain,
            category=category,
            method="text_analysis"
        )

        return {
            "domain": domain,
            "category": category,
            "confidence_scores": {
                "domain": 0.5,
                "category": 0.5,
                "overall": 0.5
            },
            "entities": {},
            "alternative_intents": [],
            "reasoning": "Fallback classification due to JSON parsing error"
        }

    def _update_state_with_classification(
        self,
        state: AgentState,
        classification: Dict[str, Any]
    ) -> AgentState:
        """
        Update agent state with classification results.

        Args:
            state: Current agent state
            classification: Classification results from LLM

        Returns:
            Updated agent state
        """
        state.update({
            "intent_domain": classification.get("domain"),
            "intent_category": classification.get("category"),
            "intent_subcategory": classification.get("subcategory"),
            "intent_action": classification.get("action"),
            "intent_confidence_scores": classification["confidence_scores"],
            "intent_alternatives": classification.get("alternative_intents", []),
            "intent_entities": classification.get("entities", {}),
            "intent_reasoning": classification.get("reasoning", ""),
            "intent_metadata": classification.get("metadata", {})
        })

        return state

    def _handle_empty_message(self, state: AgentState) -> AgentState:
        """
        Handle edge case of empty message.

        Args:
            state: Current agent state

        Returns:
            Updated state with default classification
        """
        state.update({
            "intent_domain": "support",
            "intent_category": "general",
            "intent_confidence_scores": {
                "domain": 0.3,
                "category": 0.3,
                "overall": 0.3
            },
            "intent_entities": {},
            "intent_alternatives": [],
            "intent_reasoning": "Empty message - default classification",
            "intent_metadata": {"error": "empty_message"}
        })

        return state

    def _handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """
        Handle errors during classification with graceful fallback.

        Args:
            state: Current agent state
            error: Exception that occurred

        Returns:
            Updated state with fallback classification
        """
        state.update({
            "intent_domain": "support",
            "intent_category": "general",
            "intent_confidence_scores": {
                "overall": 0.3
            },
            "intent_entities": {},
            "intent_alternatives": [],
            "intent_reasoning": f"Fallback due to error: {str(error)}",
            "intent_metadata": {
                "error": str(error),
                "error_type": type(error).__name__
            }
        })

        return state

    async def classify_and_route(self, state: AgentState) -> AgentState:
        """
        Implementation of RoutingAgent abstract method.

        This is an alias for process() to satisfy the RoutingAgent interface.

        Args:
            state: Current agent state

        Returns:
            Updated state with classification
        """
        return await self.process(state)


# Helper function to create instance
def create_intent_classifier(**kwargs) -> IntentClassifier:
    """
    Create IntentClassifier instance.

    Args:
        **kwargs: Additional arguments passed to IntentClassifier constructor

    Returns:
        Configured IntentClassifier instance
    """
    return IntentClassifier(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_intent_classifier():
        """Test Intent Classifier with sample messages."""
        print("=" * 60)
        print("TESTING INTENT CLASSIFIER")
        print("=" * 60)

        classifier = IntentClassifier()

        # Test cases covering different intent types
        test_cases = [
            # Billing intents
            {
                "message": "I want to upgrade to Premium for 25 users",
                "context": {"plan": "basic", "team_size": 10},
                "expected": {"domain": "support", "category": "billing", "action": "upgrade"}
            },
            {
                "message": "Cancel my subscription please",
                "context": {"plan": "premium"},
                "expected": {"domain": "support", "category": "billing", "action": "cancel"}
            },

            # Technical intents
            {
                "message": "The app crashes when I try to export data",
                "context": {"plan": "premium"},
                "expected": {"domain": "support", "category": "technical", "subcategory": "bug"}
            },
            {
                "message": "My data is not syncing across devices",
                "context": {},
                "expected": {"domain": "support", "category": "technical", "subcategory": "sync"}
            },

            # Sales intents
            {
                "message": "I'd like to schedule a demo of your product",
                "context": {"plan": "free"},
                "expected": {"domain": "sales", "category": "qualification"}
            },

            # Customer Success intents
            {
                "message": "We're not getting the ROI we expected",
                "context": {"plan": "enterprise", "health_score": 30},
                "expected": {"domain": "customer_success", "category": "health"}
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test['message'][:50]}...")
            print(f"{'='*60}")

            state = create_initial_state(
                message=test["message"],
                context={"customer_metadata": test["context"]}
            )

            result = await classifier.process(state)

            print(f"\n✓ Classification:")
            print(f"  Domain: {result.get('intent_domain')}")
            print(f"  Category: {result.get('intent_category')}")
            print(f"  Subcategory: {result.get('intent_subcategory', 'N/A')}")
            print(f"  Action: {result.get('intent_action', 'N/A')}")
            print(f"  Confidence: {result.get('intent_confidence_scores', {}).get('overall', 0):.2%}")
            print(f"  Entities: {result.get('intent_entities', {})}")
            print(f"  Reasoning: {result.get('intent_reasoning', '')[:100]}")

            # Check if matches expected
            expected = test["expected"]
            matches = all([
                result.get("intent_domain") == expected.get("domain"),
                result.get("intent_category") == expected.get("category")
            ])

            status = "✓ PASS" if matches else "✗ FAIL"
            print(f"\n{status}")

    # Run tests
    asyncio.run(test_intent_classifier())
