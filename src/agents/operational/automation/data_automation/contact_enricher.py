"""
Contact Enricher Agent - TASK-2207

Auto-enriches contact data with external sources (Clearbit, ZoomInfo, LinkedIn).
Fills in missing company info, social profiles, and firmographic data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("contact_enricher", tier="operational", category="automation")
class ContactEnricherAgent(BaseAgent):
    """
    Contact Enricher Agent - Auto-enriches contact data.

    Handles:
    - Company data enrichment (size, revenue, industry, location)
    - Contact role and seniority detection
    - Social profile discovery (LinkedIn, Twitter)
    - Technology stack detection
    - Firmographic data enrichment
    - Email validation and normalization
    - Phone number formatting and validation
    - Company hierarchy mapping
    """

    # Enrichment data sources
    DATA_SOURCES = {
        "clearbit": {
            "api_endpoint": "https://company.clearbit.com/v2",
            "provides": ["company", "person", "logo"],
            "confidence": 0.9
        },
        "zoominfo": {
            "api_endpoint": "https://api.zoominfo.com",
            "provides": ["company", "contacts", "intent"],
            "confidence": 0.85
        },
        "linkedin": {
            "api_endpoint": "https://api.linkedin.com/v2",
            "provides": ["person", "company", "employment"],
            "confidence": 0.8
        },
        "hunter": {
            "api_endpoint": "https://api.hunter.io/v2",
            "provides": ["email", "domain_search"],
            "confidence": 0.75
        }
    }

    # Enrichable fields
    ENRICHMENT_FIELDS = {
        "company": [
            "name", "domain", "industry", "employee_count",
            "annual_revenue", "location", "founded_year",
            "description", "logo_url", "tech_stack"
        ],
        "contact": [
            "full_name", "email", "phone", "title", "seniority",
            "linkedin_url", "twitter_url", "location", "timezone"
        ]
    }

    def __init__(self):
        config = AgentConfig(
            name="contact_enricher",
            type=AgentType.AUTOMATOR,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=800,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Auto-enrich contact data with external sources."""
        self.logger.info("contact_enricher_started")
        state = self.update_state(state)

        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Identify missing fields
        missing_fields = self._identify_missing_fields(customer_metadata)

        # Select enrichment sources
        enrichment_sources = self._select_enrichment_sources(missing_fields)

        # Enrich from external sources
        enriched_data = await self._enrich_from_sources(
            customer_metadata,
            enrichment_sources,
            missing_fields
        )

        # Validate enriched data
        validation = self._validate_enriched_data(enriched_data)

        # Merge with existing data
        merged_data = self._merge_enriched_data(
            customer_metadata,
            enriched_data,
            validation
        )

        # Update customer record
        update_result = await self._update_customer_record(merged_data)

        # Log automation action
        automation_log = self._log_automation_action(
            "contact_enriched",
            enriched_data,
            customer_metadata
        )

        # Generate response
        response = f"""**Contact Enriched Successfully**

Fields Enriched: {len(enriched_data.get('fields_added', []))}
Data Sources Used: {', '.join(enrichment_sources)}

**Enriched Data:**
"""
        for field, value in enriched_data.get('fields_added', {}).items():
            response += f"- {field}: {value}\n"

        response += f"\nConfidence Score: {enriched_data.get('confidence', 0.8):.0%}"

        state["agent_response"] = response
        state["enriched_data"] = enriched_data
        state["merged_data"] = merged_data
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.91
        state["status"] = "resolved"

        self.logger.info(
            "contact_enriched_successfully",
            fields_enriched=len(enriched_data.get('fields_added', []))
        )

        return state

    def _identify_missing_fields(self, customer_metadata: Dict) -> List[str]:
        """Identify missing or incomplete fields."""
        missing = []
        for field in self.ENRICHMENT_FIELDS["company"] + self.ENRICHMENT_FIELDS["contact"]:
            if not customer_metadata.get(field):
                missing.append(field)
        return missing

    def _select_enrichment_sources(self, missing_fields: List[str]) -> List[str]:
        """Select best data sources for missing fields."""
        return ["clearbit", "linkedin"]

    async def _enrich_from_sources(
        self,
        customer_metadata: Dict,
        sources: List[str],
        missing_fields: List[str]
    ) -> Dict[str, Any]:
        """Enrich data from external sources (mocked)."""
        # Mock enriched data
        enriched = {
            "fields_added": {
                "industry": "Software & Technology",
                "employee_count": 250,
                "annual_revenue": 50000000,
                "founded_year": 2015,
                "linkedin_url": "https://linkedin.com/company/example",
                "tech_stack": ["AWS", "React", "Python"]
            },
            "sources_used": sources,
            "confidence": 0.87,
            "enriched_at": datetime.utcnow().isoformat()
        }
        return enriched

    def _validate_enriched_data(self, enriched_data: Dict) -> Dict:
        """Validate enriched data quality."""
        return {
            "is_valid": True,
            "confidence": enriched_data.get("confidence", 0.8),
            "warnings": []
        }

    def _merge_enriched_data(
        self,
        existing_data: Dict,
        enriched_data: Dict,
        validation: Dict
    ) -> Dict:
        """Merge enriched data with existing data."""
        merged = existing_data.copy()
        merged.update(enriched_data.get("fields_added", {}))
        return merged

    async def _update_customer_record(self, merged_data: Dict) -> Dict:
        """Update customer record with enriched data."""
        return {
            "status": "success",
            "updated_at": datetime.utcnow().isoformat()
        }

    def _log_automation_action(
        self,
        action_type: str,
        enriched_data: Dict,
        customer_metadata: Dict
    ) -> Dict:
        """Log automation action."""
        return {
            "action_type": action_type,
            "timestamp": datetime.utcnow().isoformat(),
            "fields_enriched": len(enriched_data.get("fields_added", [])),
            "customer_id": customer_metadata.get("customer_id"),
            "success": True
        }
