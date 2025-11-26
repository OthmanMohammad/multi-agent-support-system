"""
Entity Extractor - Extract structured entities from messages.

Extracts plan names, amounts, dates, team sizes, features, competitors,
integrations, tech stack, actions, and problems from user messages.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-103)
"""

from typing import Dict, Any, Optional, List
import json
import re
from datetime import datetime, timedelta
import structlog

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.base.agent_types import AgentType, AgentCapability
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

logger = structlog.get_logger(__name__)


@AgentRegistry.register("entity_extractor", tier="essential", category="routing")
class EntityExtractor(BaseAgent):
    """
    Entity Extractor - Structured entity extraction from user messages.

    Extracts and validates 10+ entity types:
    - plan_name: free, basic, premium, enterprise
    - amount: $50, $1000, 20%, etc.
    - feature: api, webhooks, reports, sso, audit_logs
    - date: next month, jan 15, 2025-01-15
    - team_size: 10 users, 50 seats, 25 people
    - competitor: Asana, Monday, ClickUp, Jira
    - integration: Slack, Salesforce, GitHub, Zapier
    - tech_stack: Python, React, AWS, Docker
    - action: upgrade, downgrade, cancel, export
    - problem: crash, slow, not working, error
    """

    # Valid values for constrained entity types
    VALID_PLANS = ["free", "basic", "premium", "enterprise"]
    VALID_ACTIONS = [
        "upgrade", "downgrade", "cancel", "pause", "reactivate",
        "export", "import", "create", "delete", "update",
        "share", "invite", "compare", "schedule"
    ]
    VALID_FEATURES = [
        "api", "webhooks", "reports", "sso", "audit_logs",
        "export", "import", "analytics", "collaboration",
        "automation", "integrations", "security", "backup"
    ]
    KNOWN_COMPETITORS = [
        "asana", "monday", "clickup", "jira", "trello",
        "notion", "basecamp", "wrike", "smartsheet", "airtable"
    ]
    KNOWN_INTEGRATIONS = [
        "slack", "salesforce", "github", "zapier", "google calendar",
        "microsoft teams", "jira", "confluence", "hubspot", "zendesk"
    ]

    def __init__(self, **kwargs):
        """Initialize Entity Extractor with extraction capabilities."""
        config = AgentConfig(
            name="entity_extractor",
            type=AgentType.ANALYZER,
             # Fast and accurate
            temperature=0.1,  # Low for consistent extraction
            max_tokens=300,  # Moderate for entity lists
            capabilities=[
                AgentCapability.ENTITY_EXTRACTION,
                AgentCapability.CONTEXT_AWARE
            ],
            system_prompt_template=self._get_system_prompt(),
            tier="essential",
            role="entity_extractor"
        )
        super().__init__(config=config, **kwargs)
        self.logger = logger.bind(agent="entity_extractor", agent_type="analyzer")

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for entity extraction.

        Returns:
            System prompt with entity types and extraction rules
        """
        return """You are an entity extraction system. Extract structured information from user messages.

**Entity Types to Extract:**

1. **plan_name**: Subscription plan mentioned
   - Values: free, basic, premium, enterprise
   - Examples: "upgrade to Premium", "on the Free plan"

2. **amount**: Money amounts or percentages
   - Examples: $50, $1000, 20%, €99, 100 dollars

3. **feature**: Product features mentioned
   - Examples: api, webhooks, reports, sso, audit_logs, export, import, analytics

4. **date**: Dates or time references
   - Examples: "next month", "jan 15", "2025-01-15", "in 30 days", "tomorrow"
   - Return in ISO format when possible (YYYY-MM-DD)

5. **team_size**: Number of users/seats/people
   - Examples: "10 users", "50 seats", "25 people", "team of 30"
   - Extract the numeric value

6. **competitor**: Competitor products mentioned
   - Examples: Asana, Monday, ClickUp, Jira, Trello, Notion, Basecamp

7. **integration**: Third-party integrations
   - Examples: Slack, Salesforce, GitHub, Zapier, Google Calendar, Microsoft Teams

8. **tech_stack**: Technologies or platforms
   - Examples: Python, JavaScript, React, Node, AWS, Docker, Kubernetes

9. **action**: User's intended action
   - Examples: upgrade, downgrade, cancel, export, import, create, delete, compare

10. **problem**: Issues or problems mentioned
    - Examples: crash, slow, not working, error, bug, freeze, timeout

**Extraction Rules:**
1. Extract ALL entities found in the message
2. Normalize values:
   - plan_name: lowercase (Premium → premium)
   - team_size: extract numeric value only (25 users → 25)
   - action: lowercase
   - competitor: normalize capitalization (ASANA → Asana)
3. For dates: try to convert to ISO format (YYYY-MM-DD) if possible
4. If an entity is not found, do NOT include it in the output
5. Multiple entities of same type: return as list
6. Be precise - only extract entities explicitly mentioned

**Output Format (JSON only, no extra text):**
{{
    "plan_name": "premium",
    "team_size": 25,
    "date": "2025-02-01",
    "action": "upgrade",
    "amount": "$99"
}}

Output ONLY valid JSON with the extracted entities. If no entities found, return empty object {{}}."""

    async def process(self, state: AgentState) -> AgentState:
        """
        Extract entities from the message.

        Args:
            state: Current agent state with message

        Returns:
            Updated state with extracted_entities field
        """
        try:
            # Update state with agent history
            state = self.update_state(state)

            # Get message
            message = state.get("current_message", "")

            if not message:
                self.logger.warning("entity_extractor_empty_message")
                state["extracted_entities"] = {}
                return state

            # Get conversation history for context
            conversation_history = self.get_conversation_context(state)

            # Call LLM for extraction
            response = await self.call_llm(
                system_prompt=self._get_system_prompt(),
                user_message=f"Extract entities from this message:\n\n{message}",
                conversation_history=conversation_history
            )

            # Parse response
            entities = self._parse_response(response)

            # Validate and normalize entities
            entities = self._validate_entities(entities)

            # Additional parsing for complex types
            entities = self._parse_special_entities(entities, message)

            # Update state
            state["extracted_entities"] = entities

            self.logger.info(
                "entities_extracted",
                count=len(entities),
                entity_types=list(entities.keys()),
                message_preview=message[:50]
            )

            return state

        except Exception as e:
            self.logger.error(
                "entity_extraction_failed",
                error=str(e),
                error_type=type(e).__name__
            )

            # Fallback to empty entities
            state["extracted_entities"] = {}
            return state

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into entities dictionary.

        Args:
            response: LLM response (should be JSON)

        Returns:
            Dictionary of extracted entities
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

            # Fix double braces (LLM sometimes returns {{ instead of {)
            if cleaned_response.startswith("{{"):
                cleaned_response = cleaned_response[1:]
            if cleaned_response.endswith("}}"):
                cleaned_response = cleaned_response[:-1]

            # Parse JSON
            entities = json.loads(cleaned_response)

            # Ensure it's a dict
            if not isinstance(entities, dict):
                self.logger.warning(
                    "entity_extractor_invalid_type",
                    type=type(entities).__name__
                )
                return {}

            return entities

        except json.JSONDecodeError as e:
            self.logger.warning(
                "entity_extractor_invalid_json",
                response_preview=response[:100],
                error=str(e)
            )
            return {}

    def _validate_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize extracted entities.

        Args:
            entities: Raw extracted entities

        Returns:
            Validated and normalized entities
        """
        validated = {}

        # Validate plan_name
        if "plan_name" in entities:
            plan = str(entities["plan_name"]).lower().strip()
            if plan in self.VALID_PLANS:
                validated["plan_name"] = plan

        # Validate and normalize team_size
        if "team_size" in entities:
            try:
                # Extract numeric value
                team_size = entities["team_size"]
                if isinstance(team_size, str):
                    # Extract numbers from string
                    numbers = re.findall(r'\d+', team_size)
                    if numbers:
                        team_size = int(numbers[0])
                validated["team_size"] = int(team_size)
            except (ValueError, TypeError, IndexError):
                self.logger.debug("entity_extractor_invalid_team_size", value=entities["team_size"])

        # Validate action
        if "action" in entities:
            action = str(entities["action"]).lower().strip()
            # Allow any action, but normalize
            validated["action"] = action

        # Validate feature
        if "feature" in entities:
            feature = str(entities["feature"]).lower().strip()
            validated["feature"] = feature

        # Validate competitor
        if "competitor" in entities:
            competitor = str(entities["competitor"]).strip()
            # Normalize capitalization (first letter uppercase)
            validated["competitor"] = competitor.title()

        # Validate integration
        if "integration" in entities:
            integration = str(entities["integration"]).strip()
            validated["integration"] = integration.title()

        # Validate tech_stack
        if "tech_stack" in entities:
            tech_stack = str(entities["tech_stack"]).strip()
            validated["tech_stack"] = tech_stack

        # Validate problem
        if "problem" in entities:
            problem = str(entities["problem"]).lower().strip()
            validated["problem"] = problem

        # Pass through amount (already validated by LLM)
        if "amount" in entities:
            validated["amount"] = str(entities["amount"])

        # Pass through date (validated by LLM)
        if "date" in entities:
            validated["date"] = str(entities["date"])

        # Pass through any other entities not specifically validated
        for key, value in entities.items():
            if key not in validated and value is not None and value != "":
                validated[key] = value

        return validated

    def _parse_special_entities(
        self,
        entities: Dict[str, Any],
        message: str
    ) -> Dict[str, Any]:
        """
        Parse special entities that need additional processing.

        This is a fallback/enhancement for entities the LLM might miss.

        Args:
            entities: Already extracted entities
            message: Original message

        Returns:
            Enhanced entities dictionary
        """
        # Add billing_cycle if amount is mentioned with period
        if "amount" in entities:
            amount_str = entities["amount"]
            if "month" in message.lower() or "/mo" in message.lower():
                entities["billing_cycle"] = "monthly"
            elif "year" in message.lower() or "/yr" in message.lower():
                entities["billing_cycle"] = "yearly"

        # Add urgency flag if urgent language detected
        urgent_keywords = ["urgent", "asap", "immediately", "critical", "emergency"]
        if any(keyword in message.lower() for keyword in urgent_keywords):
            entities["urgency"] = "high"

        # Add polarity for problems (positive/negative context)
        if "problem" in entities:
            negative_keywords = ["not working", "broken", "failed", "error", "crash"]
            if any(keyword in message.lower() for keyword in negative_keywords):
                entities["severity"] = "high"

        return entities


# Helper function to create instance
def create_entity_extractor(**kwargs) -> EntityExtractor:
    """
    Create EntityExtractor instance.

    Args:
        **kwargs: Additional arguments passed to EntityExtractor constructor

    Returns:
        Configured EntityExtractor instance
    """
    return EntityExtractor(**kwargs)


# Example usage (for development/testing)
if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test_entity_extractor():
        """Test Entity Extractor with sample messages."""
        print("=" * 60)
        print("TESTING ENTITY EXTRACTOR")
        print("=" * 60)

        extractor = EntityExtractor()

        # Test cases covering different entity types
        test_cases = [
            {
                "message": "I want to upgrade to Premium for 25 users next month",
                "expected": ["plan_name", "team_size", "date", "action"]
            },
            {
                "message": "Compare your $99/month plan to Asana's pricing",
                "expected": ["amount", "competitor", "action"]
            },
            {
                "message": "Our React app crashes when using the Slack integration",
                "expected": ["tech_stack", "integration", "problem"]
            },
            {
                "message": "How do I export data to CSV?",
                "expected": ["action", "feature"]
            },
            {
                "message": "Cancel my subscription please",
                "expected": ["action"]
            },
        ]

        for i, test in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"TEST CASE {i}: {test['message']}")
            print(f"{'='*60}")

            state = create_initial_state(
                message=test["message"],
                context={}
            )

            result = await extractor.process(state)
            entities = result.get("extracted_entities", {})

            print(f"\n✓ Extracted Entities:")
            for key, value in entities.items():
                print(f"  {key}: {value}")

            # Check if expected entities were found
            found_types = set(entities.keys())
            expected_types = set(test["expected"])

            if expected_types.issubset(found_types):
                print(f"\n✓ PASS: Found all expected entity types")
            else:
                missing = expected_types - found_types
                print(f"\n⚠ PARTIAL: Missing entity types: {missing}")

    # Run tests
    asyncio.run(test_entity_extractor())