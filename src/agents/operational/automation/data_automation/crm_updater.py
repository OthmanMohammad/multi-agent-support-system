"""
CRM Updater Agent - TASK-2206

Auto-updates CRM systems (Salesforce, HubSpot) from customer conversations,
support tickets, and interactions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("crm_updater", tier="operational", category="automation")
class CRMUpdaterAgent(BaseAgent):
    """
    CRM Updater Agent - Auto-updates CRM from conversations.

    Handles:
    - Automatic CRM field updates (contact info, notes, stage, etc.)
    - Activity logging (calls, emails, meetings)
    - Opportunity updates (amount, stage, close date)
    - Lead scoring updates
    - Contact enrichment from conversations
    - Account health score updates
    - Next action and follow-up tracking
    - Custom field population based on conversation analysis
    """

    # Supported CRM systems
    CRM_SYSTEMS = {
        "salesforce": {
            "api_endpoint": "https://api.salesforce.com/services/data/v58.0",
            "objects": ["Contact", "Lead", "Opportunity", "Account", "Case"],
            "max_batch_size": 200
        },
        "hubspot": {
            "api_endpoint": "https://api.hubapi.com",
            "objects": ["contacts", "companies", "deals", "tickets"],
            "max_batch_size": 100
        },
        "pipedrive": {
            "api_endpoint": "https://api.pipedrive.com/v1",
            "objects": ["persons", "organizations", "deals", "activities"],
            "max_batch_size": 500
        }
    }

    # Extractable CRM fields from conversations
    EXTRACTABLE_FIELDS = {
        "contact": [
            "company_size",
            "industry",
            "role",
            "pain_points",
            "use_cases",
            "technical_level",
            "decision_maker"
        ],
        "opportunity": [
            "deal_size",
            "close_date",
            "stage",
            "competitors",
            "budget",
            "timeline",
            "decision_criteria"
        ],
        "account": [
            "health_score",
            "sentiment",
            "engagement_level",
            "churn_risk",
            "expansion_potential",
            "product_usage"
        ]
    }

    # Conversation sentiment to CRM health score mapping
    SENTIMENT_TO_HEALTH = {
        "very_positive": 90,
        "positive": 75,
        "neutral": 50,
        "negative": 30,
        "very_negative": 10
    }

    def __init__(self):
        config = AgentConfig(
            name="crm_updater",
            type=AgentType.AUTOMATOR,
            temperature=0.1,
            max_tokens=1000,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Auto-update CRM from conversations.

        Args:
            state: Current agent state with conversation data

        Returns:
            Updated state with CRM update results
        """
        self.logger.info("crm_updater_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Extract CRM parameters
        crm_system = entities.get("crm_system", customer_metadata.get("crm_system", "salesforce"))
        update_type = entities.get("update_type", "auto")

        self.logger.debug(
            "crm_update_details",
            crm_system=crm_system,
            update_type=update_type
        )

        # Extract insights from conversation
        conversation_insights = await self._extract_conversation_insights(
            message,
            customer_metadata
        )

        # Map insights to CRM fields
        field_updates = self._map_insights_to_crm_fields(
            conversation_insights,
            crm_system,
            customer_metadata
        )

        # Determine what CRM objects to update
        update_targets = self._determine_update_targets(
            field_updates,
            customer_metadata
        )

        # Validate updates
        validation = self._validate_updates(
            field_updates,
            update_targets,
            crm_system
        )

        # Apply updates to CRM
        update_results = await self._update_crm_external(
            crm_system,
            update_targets,
            field_updates,
            validation
        )

        # Log activity in CRM
        activity_log = await self._log_crm_activity(
            crm_system,
            message,
            customer_metadata,
            update_results
        )

        # Log automation action
        automation_log = self._log_automation_action(
            "crm_updated",
            update_results,
            customer_metadata
        )

        # Generate response
        response = self._format_crm_update_response(
            update_results,
            activity_log,
            validation
        )

        state["agent_response"] = response
        state["crm_updates"] = update_results
        state["conversation_insights"] = conversation_insights
        state["field_updates"] = field_updates
        state["activity_log"] = activity_log
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.92
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "crm_updated_successfully",
            crm_system=crm_system,
            objects_updated=len(update_results.get("updated_objects", [])),
            fields_updated=len(field_updates)
        )

        return state

    async def _extract_conversation_insights(
        self,
        message: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Extract CRM-relevant insights from conversation.

        Args:
            message: Conversation message
            customer_metadata: Customer metadata

        Returns:
            Extracted insights
        """
        system_prompt = """You are a CRM data extraction specialist. Extract structured business information from customer conversations.

Extract:
1. Company/contact information (size, industry, role)
2. Pain points and challenges mentioned
3. Use cases and requirements
4. Budget and timeline indicators
5. Decision-making signals
6. Sentiment and engagement level
7. Competitors mentioned
8. Next steps or action items
9. Product interest level
10. Technical requirements

Be precise and extract only factual information mentioned in the conversation."""

        user_prompt = f"""Extract CRM insights from this conversation:

Message: {message}

Current Customer Data:
- Company: {customer_metadata.get('customer_name', 'Unknown')}
- Plan: {customer_metadata.get('plan_name', 'Unknown')}
- Industry: {customer_metadata.get('industry', 'Unknown')}

Return JSON with extracted fields: company_info, pain_points, use_cases, budget_signals, timeline, sentiment, competitors, next_steps, engagement_level, and any other relevant business data."""

        response = await self.call_llm(system_prompt, user_prompt)

        # Parse LLM response
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                insights = json.loads(json_match.group())
            else:
                insights = {
                    "sentiment": "neutral",
                    "engagement_level": "medium"
                }
        except:
            insights = {
                "sentiment": "neutral",
                "engagement_level": "medium"
            }

        # Add metadata
        insights["extracted_at"] = datetime.now(UTC).isoformat()
        insights["source"] = "conversation"

        return insights

    def _map_insights_to_crm_fields(
        self,
        insights: Dict,
        crm_system: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Map conversation insights to CRM field updates.

        Args:
            insights: Extracted insights
            crm_system: CRM system
            customer_metadata: Customer metadata

        Returns:
            Field updates mapped to CRM
        """
        field_updates = {
            "Contact": {},
            "Account": {},
            "Opportunity": {}
        }

        # Map contact fields
        if insights.get("company_info"):
            company_info = insights["company_info"]
            if isinstance(company_info, dict):
                if company_info.get("size"):
                    field_updates["Contact"]["Company_Size__c"] = company_info["size"]
                if company_info.get("industry"):
                    field_updates["Contact"]["Industry"] = company_info["industry"]
                if company_info.get("role"):
                    field_updates["Contact"]["Title"] = company_info["role"]

        # Map account health from sentiment
        if insights.get("sentiment"):
            sentiment = insights["sentiment"]
            health_score = self.SENTIMENT_TO_HEALTH.get(sentiment, 50)
            field_updates["Account"]["Health_Score__c"] = health_score
            field_updates["Account"]["Sentiment__c"] = sentiment

        # Map engagement level
        if insights.get("engagement_level"):
            field_updates["Account"]["Engagement_Level__c"] = insights["engagement_level"]

        # Map opportunity fields
        if insights.get("budget_signals"):
            field_updates["Opportunity"]["Budget_Confirmed__c"] = True
            field_updates["Opportunity"]["Budget_Notes__c"] = str(insights["budget_signals"])

        if insights.get("timeline"):
            field_updates["Opportunity"]["Timeline__c"] = str(insights["timeline"])

        if insights.get("competitors"):
            field_updates["Opportunity"]["Competitors__c"] = ", ".join(
                insights["competitors"] if isinstance(insights["competitors"], list)
                else [str(insights["competitors"])]
            )

        # Add pain points to notes
        if insights.get("pain_points"):
            pain_points_str = ", ".join(
                insights["pain_points"] if isinstance(insights["pain_points"], list)
                else [str(insights["pain_points"])]
            )
            field_updates["Contact"]["Pain_Points__c"] = pain_points_str

        # Add next steps
        if insights.get("next_steps"):
            field_updates["Account"]["Next_Steps__c"] = str(insights["next_steps"])
            field_updates["Account"]["Last_Contact_Date__c"] = datetime.now(UTC).isoformat()

        return field_updates

    def _determine_update_targets(
        self,
        field_updates: Dict,
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """
        Determine which CRM objects to update.

        Args:
            field_updates: Field updates
            customer_metadata: Customer metadata

        Returns:
            List of update targets
        """
        update_targets = []

        # Update Contact
        if field_updates.get("Contact"):
            update_targets.append({
                "object_type": "Contact",
                "record_id": customer_metadata.get("crm_contact_id", "00X000001"),
                "fields": field_updates["Contact"]
            })

        # Update Account
        if field_updates.get("Account"):
            update_targets.append({
                "object_type": "Account",
                "record_id": customer_metadata.get("crm_account_id", "00Y000001"),
                "fields": field_updates["Account"]
            })

        # Update Opportunity if exists
        if field_updates.get("Opportunity") and customer_metadata.get("crm_opportunity_id"):
            update_targets.append({
                "object_type": "Opportunity",
                "record_id": customer_metadata["crm_opportunity_id"],
                "fields": field_updates["Opportunity"]
            })

        return update_targets

    def _validate_updates(
        self,
        field_updates: Dict,
        update_targets: List[Dict],
        crm_system: str
    ) -> Dict[str, Any]:
        """
        Validate CRM updates before applying.

        Args:
            field_updates: Field updates
            update_targets: Update targets
            crm_system: CRM system

        Returns:
            Validation results
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }

        # Check if we have targets
        if not update_targets:
            validation["warnings"].append("No CRM objects to update")

        # Check for required IDs
        for target in update_targets:
            if not target.get("record_id"):
                validation["errors"].append(f"Missing record ID for {target['object_type']}")
                validation["is_valid"] = False

        # Check field values
        for obj_type, fields in field_updates.items():
            if not fields:
                validation["warnings"].append(f"No fields to update for {obj_type}")

        return validation

    async def _update_crm_external(
        self,
        crm_system: str,
        update_targets: List[Dict],
        field_updates: Dict,
        validation: Dict
    ) -> Dict[str, Any]:
        """
        Update CRM via external API (mocked).

        Args:
            crm_system: CRM system
            update_targets: Update targets
            field_updates: Field updates
            validation: Validation results

        Returns:
            Update results
        """
        if not validation.get("is_valid"):
            raise ValueError(f"CRM update validation failed: {validation['errors']}")

        # In production, make actual CRM API calls
        # For now, return mock update results

        updated_objects = []

        for target in update_targets:
            update_record = {
                "object_type": target["object_type"],
                "record_id": target["record_id"],
                "fields_updated": list(target["fields"].keys()),
                "field_count": len(target["fields"]),
                "status": "success",
                "updated_at": datetime.now(UTC).isoformat()
            }
            updated_objects.append(update_record)

            self.logger.info(
                "crm_object_updated",
                crm_system=crm_system,
                object_type=target["object_type"],
                record_id=target["record_id"],
                field_count=len(target["fields"])
            )

        return {
            "crm_system": crm_system,
            "updated_objects": updated_objects,
            "total_objects": len(updated_objects),
            "total_fields": sum(obj["field_count"] for obj in updated_objects),
            "status": "success",
            "timestamp": datetime.now(UTC).isoformat()
        }

    async def _log_crm_activity(
        self,
        crm_system: str,
        message: str,
        customer_metadata: Dict,
        update_results: Dict
    ) -> Dict[str, Any]:
        """
        Log activity/note in CRM.

        Args:
            crm_system: CRM system
            message: Conversation message
            customer_metadata: Customer metadata
            update_results: Update results

        Returns:
            Activity log record
        """
        # Create activity log entry
        activity = {
            "id": f"ACT-{datetime.now(UTC).timestamp()}",
            "type": "Note",
            "subject": "Customer Conversation - Auto-logged",
            "description": f"Conversation logged automatically:\n\n{message[:500]}...",
            "related_to": customer_metadata.get("crm_contact_id"),
            "created_by": "automation",
            "created_at": datetime.now(UTC).isoformat(),
            "metadata": {
                "source": "support_conversation",
                "auto_updates": len(update_results.get("updated_objects", []))
            }
        }

        return activity

    def _log_automation_action(
        self,
        action_type: str,
        update_results: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Log automated action for audit trail."""
        return {
            "action_type": action_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "crm_system": update_results.get("crm_system"),
            "customer_id": customer_metadata.get("customer_id"),
            "success": update_results.get("status") == "success",
            "details": {
                "objects_updated": len(update_results.get("updated_objects", [])),
                "total_fields": update_results.get("total_fields", 0)
            }
        }

    def _format_crm_update_response(
        self,
        update_results: Dict,
        activity_log: Dict,
        validation: Dict
    ) -> str:
        """Format CRM update response."""
        response = f"""**CRM Updated Successfully**

CRM System: {update_results['crm_system'].upper()}
Objects Updated: {update_results['total_objects']}
Total Fields Updated: {update_results['total_fields']}

**Updated Objects:**
"""

        for obj in update_results.get("updated_objects", []):
            response += f"\n{obj['object_type']} (ID: {obj['record_id']})\n"
            response += f"- Fields Updated: {', '.join(obj['fields_updated'])}\n"
            response += f"- Status: {obj['status'].title()}\n"

        response += f"""\n**Activity Logged:**
- Activity ID: {activity_log['id']}
- Type: {activity_log['type']}
- Created: {activity_log['created_at']}
"""

        if validation.get("warnings"):
            response += f"\n**Warnings:** {len(validation['warnings'])}\n"
            for warning in validation["warnings"][:3]:
                response += f"- {warning}\n"

        response += f"\nUpdated: {update_results['timestamp']}"

        return response
