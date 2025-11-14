"""
Unit tests for Entity Extractor.

Tests extraction of 10+ entity types, validation, normalization,
and edge case handling.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-103)
"""

import pytest
from unittest.mock import AsyncMock
import json

from src.agents.essential.routing.entity_extractor import (
    EntityExtractor,
    create_entity_extractor
)
from src.workflow.state import AgentState, create_initial_state


@pytest.fixture
def extractor():
    """Create EntityExtractor instance for testing."""
    return EntityExtractor()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Test message",
        customer_id="test_customer_123"
    )


class TestEntityExtractorInitialization:
    """Test Entity Extractor initialization and configuration."""

    def test_entity_extractor_initialization(self, extractor):
        """Test that Entity Extractor initializes with correct configuration."""
        assert extractor.config.name == "entity_extractor"
        assert extractor.config.type.value == "analyzer"
        assert extractor.config.model == "claude-3-haiku-20240307"
        assert extractor.config.temperature == 0.1
        assert extractor.config.max_tokens == 300
        assert extractor.config.tier == "essential"

    def test_entity_extractor_has_required_capabilities(self, extractor):
        """Test that Entity Extractor has required capabilities."""
        from src.agents.base.agent_types import AgentCapability

        capabilities = extractor.config.capabilities
        assert AgentCapability.ENTITY_EXTRACTION in capabilities

    def test_create_entity_extractor_helper(self):
        """Test helper function creates valid instance."""
        extractor = create_entity_extractor()
        assert isinstance(extractor, EntityExtractor)
        assert extractor.config.name == "entity_extractor"

    def test_has_valid_plans_list(self, extractor):
        """Test that valid plans list is defined."""
        assert "free" in extractor.VALID_PLANS
        assert "basic" in extractor.VALID_PLANS
        assert "premium" in extractor.VALID_PLANS
        assert "enterprise" in extractor.VALID_PLANS


class TestPlanNameExtraction:
    """Test plan name entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_premium_plan(self, extractor):
        """Test: Extract 'premium' plan name."""
        state = create_initial_state(
            message="I want to upgrade to Premium"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "plan_name": "premium",
            "action": "upgrade"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["plan_name"] == "premium"

    @pytest.mark.asyncio
    async def test_extracts_enterprise_plan(self, extractor):
        """Test: Extract 'enterprise' plan name."""
        state = create_initial_state(
            message="Switch to Enterprise plan"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "plan_name": "enterprise",
            "action": "upgrade"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["plan_name"] == "enterprise"

    @pytest.mark.asyncio
    async def test_normalizes_plan_name_case(self, extractor):
        """Test: Plan name normalized to lowercase."""
        state = create_initial_state(message="PREMIUM plan")

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "plan_name": "PREMIUM"
        }))

        result = await extractor.process(state)

        # Should be normalized to lowercase
        assert result["extracted_entities"]["plan_name"] == "premium"

    @pytest.mark.asyncio
    async def test_rejects_invalid_plan_name(self, extractor):
        """Test: Invalid plan names are rejected."""
        state = create_initial_state(message="test")

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "plan_name": "invalid_plan"
        }))

        result = await extractor.process(state)

        # Invalid plan should not be included
        assert "plan_name" not in result["extracted_entities"]


class TestTeamSizeExtraction:
    """Test team size entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_numeric_team_size(self, extractor):
        """Test: Extract numeric team size."""
        state = create_initial_state(
            message="For 25 users"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "team_size": 25
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["team_size"] == 25
        assert isinstance(result["extracted_entities"]["team_size"], int)

    @pytest.mark.asyncio
    async def test_extracts_team_size_from_string(self, extractor):
        """Test: Extract team size from string like '50 seats'."""
        state = create_initial_state(
            message="Need 50 seats"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "team_size": "50 seats"
        }))

        result = await extractor.process(state)

        # Should extract numeric value
        assert result["extracted_entities"]["team_size"] == 50

    @pytest.mark.asyncio
    async def test_handles_invalid_team_size(self, extractor):
        """Test: Invalid team size is handled gracefully."""
        state = create_initial_state(message="test")

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "team_size": "invalid"
        }))

        result = await extractor.process(state)

        # Invalid team size should not be included
        assert "team_size" not in result["extracted_entities"]


class TestAmountExtraction:
    """Test amount entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_dollar_amount(self, extractor):
        """Test: Extract dollar amount."""
        state = create_initial_state(
            message="$99 per month"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "amount": "$99"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["amount"] == "$99"

    @pytest.mark.asyncio
    async def test_extracts_percentage(self, extractor):
        """Test: Extract percentage."""
        state = create_initial_state(
            message="20% discount"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "amount": "20%"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["amount"] == "20%"


class TestActionExtraction:
    """Test action entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_upgrade_action(self, extractor):
        """Test: Extract 'upgrade' action."""
        state = create_initial_state(
            message="I want to upgrade"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "action": "upgrade"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["action"] == "upgrade"

    @pytest.mark.asyncio
    async def test_extracts_cancel_action(self, extractor):
        """Test: Extract 'cancel' action."""
        state = create_initial_state(
            message="Cancel my subscription"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "action": "cancel"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["action"] == "cancel"

    @pytest.mark.asyncio
    async def test_normalizes_action_case(self, extractor):
        """Test: Action normalized to lowercase."""
        state = create_initial_state(message="EXPORT data")

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "action": "EXPORT"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["action"] == "export"


class TestCompetitorExtraction:
    """Test competitor entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_asana(self, extractor):
        """Test: Extract Asana competitor."""
        state = create_initial_state(
            message="How does this compare to Asana?"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "competitor": "Asana",
            "action": "compare"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["competitor"] == "Asana"

    @pytest.mark.asyncio
    async def test_extracts_clickup(self, extractor):
        """Test: Extract ClickUp competitor."""
        state = create_initial_state(
            message="Better than ClickUp?"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "competitor": "ClickUp"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["competitor"] == "Clickup"


class TestIntegrationExtraction:
    """Test integration entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_slack_integration(self, extractor):
        """Test: Extract Slack integration."""
        state = create_initial_state(
            message="Slack integration not working"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "integration": "Slack",
            "problem": "not working"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["integration"] == "Slack"

    @pytest.mark.asyncio
    async def test_extracts_salesforce_integration(self, extractor):
        """Test: Extract Salesforce integration."""
        state = create_initial_state(
            message="Connect with Salesforce"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "integration": "Salesforce"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["integration"] == "Salesforce"


class TestTechStackExtraction:
    """Test tech stack entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_react(self, extractor):
        """Test: Extract React tech stack."""
        state = create_initial_state(
            message="Our React app is having issues"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "tech_stack": "React",
            "problem": "issues"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["tech_stack"] == "React"

    @pytest.mark.asyncio
    async def test_extracts_python(self, extractor):
        """Test: Extract Python tech stack."""
        state = create_initial_state(
            message="Python SDK not working"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "tech_stack": "Python",
            "problem": "not working"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["tech_stack"] == "Python"


class TestProblemExtraction:
    """Test problem entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_crash_problem(self, extractor):
        """Test: Extract 'crash' problem."""
        state = create_initial_state(
            message="App crashes when I export"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "problem": "crash",
            "action": "export"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["problem"] == "crash"

    @pytest.mark.asyncio
    async def test_extracts_slow_problem(self, extractor):
        """Test: Extract 'slow' problem."""
        state = create_initial_state(
            message="The app is really slow"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "problem": "slow"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["problem"] == "slow"


class TestFeatureExtraction:
    """Test feature entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_api_feature(self, extractor):
        """Test: Extract API feature."""
        state = create_initial_state(
            message="How do I use the API?"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "feature": "api"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["feature"] == "api"

    @pytest.mark.asyncio
    async def test_extracts_webhooks_feature(self, extractor):
        """Test: Extract webhooks feature."""
        state = create_initial_state(
            message="Setup webhooks for notifications"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "feature": "webhooks"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["feature"] == "webhooks"


class TestDateExtraction:
    """Test date entity extraction."""

    @pytest.mark.asyncio
    async def test_extracts_date(self, extractor):
        """Test: Extract date."""
        state = create_initial_state(
            message="Upgrade next month"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "date": "2025-02-01",
            "action": "upgrade"
        }))

        result = await extractor.process(state)

        assert result["extracted_entities"]["date"] == "2025-02-01"


class TestMultipleEntities:
    """Test extraction of multiple entities from single message."""

    @pytest.mark.asyncio
    async def test_extracts_multiple_entities(self, extractor):
        """Test: Extract multiple entities from one message."""
        state = create_initial_state(
            message="Upgrade to Premium for 25 users next month"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "plan_name": "premium",
            "team_size": 25,
            "date": "2025-02-01",
            "action": "upgrade"
        }))

        result = await extractor.process(state)

        entities = result["extracted_entities"]
        assert entities["plan_name"] == "premium"
        assert entities["team_size"] == 25
        assert entities["date"] == "2025-02-01"
        assert entities["action"] == "upgrade"
        assert len(entities) == 4

    @pytest.mark.asyncio
    async def test_extracts_competitor_and_amount(self, extractor):
        """Test: Extract competitor and amount."""
        state = create_initial_state(
            message="Compare your $99/month to Asana's pricing"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "amount": "$99",
            "competitor": "Asana",
            "action": "compare"
        }))

        result = await extractor.process(state)

        entities = result["extracted_entities"]
        assert entities["amount"] == "$99"
        assert entities["competitor"] == "Asana"
        assert entities["action"] == "compare"

    @pytest.mark.asyncio
    async def test_extracts_tech_and_integration(self, extractor):
        """Test: Extract tech stack and integration."""
        state = create_initial_state(
            message="Our React app crashes with Slack integration"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "tech_stack": "React",
            "integration": "Slack",
            "problem": "crash"
        }))

        result = await extractor.process(state)

        entities = result["extracted_entities"]
        assert entities["tech_stack"] == "React"
        assert entities["integration"] == "Slack"
        assert entities["problem"] == "crash"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_empty_message(self, extractor):
        """Test: Empty message returns empty entities."""
        state = create_initial_state(message="")

        result = await extractor.process(state)

        assert result["extracted_entities"] == {}

    @pytest.mark.asyncio
    async def test_handles_no_entities(self, extractor):
        """Test: Message with no entities."""
        state = create_initial_state(
            message="Hello, how are you?"
        )

        extractor.call_llm = AsyncMock(return_value=json.dumps({}))

        result = await extractor.process(state)

        assert result["extracted_entities"] == {}

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self, extractor):
        """Test: Invalid JSON response."""
        state = create_initial_state(
            message="Test message"
        )

        extractor.call_llm = AsyncMock(return_value="Not valid JSON")

        result = await extractor.process(state)

        # Should return empty dict on parse failure
        assert result["extracted_entities"] == {}

    @pytest.mark.asyncio
    async def test_handles_llm_error(self, extractor):
        """Test: LLM error handling."""
        state = create_initial_state(
            message="Test message"
        )

        extractor.call_llm = AsyncMock(side_effect=Exception("API Error"))

        result = await extractor.process(state)

        # Should return empty dict on error
        assert result["extracted_entities"] == {}

    @pytest.mark.asyncio
    async def test_handles_markdown_json(self, extractor):
        """Test: JSON wrapped in markdown code blocks."""
        state = create_initial_state(
            message="Upgrade to premium"
        )

        extractor.call_llm = AsyncMock(return_value="""```json
{
    "plan_name": "premium",
    "action": "upgrade"
}
```""")

        result = await extractor.process(state)

        # Should parse correctly despite markdown
        assert result["extracted_entities"]["plan_name"] == "premium"


class TestValidation:
    """Test entity validation logic."""

    def test_validate_entities_normalizes_plan(self, extractor):
        """Test: Plan name validation and normalization."""
        entities = {"plan_name": "PREMIUM"}
        validated = extractor._validate_entities(entities)

        assert validated["plan_name"] == "premium"

    def test_validate_entities_extracts_team_size_number(self, extractor):
        """Test: Team size number extraction."""
        entities = {"team_size": "50 users"}
        validated = extractor._validate_entities(entities)

        assert validated["team_size"] == 50

    def test_validate_entities_normalizes_action(self, extractor):
        """Test: Action normalization."""
        entities = {"action": "UPGRADE"}
        validated = extractor._validate_entities(entities)

        assert validated["action"] == "upgrade"

    def test_validate_entities_title_cases_competitor(self, extractor):
        """Test: Competitor title casing."""
        entities = {"competitor": "asana"}
        validated = extractor._validate_entities(entities)

        assert validated["competitor"] == "Asana"

    def test_validate_entities_filters_empty_values(self, extractor):
        """Test: Empty values are filtered out."""
        entities = {"plan_name": "", "action": "upgrade"}
        validated = extractor._validate_entities(entities)

        assert "plan_name" not in validated
        assert validated["action"] == "upgrade"


class TestStateManagement:
    """Test state management and updates."""

    @pytest.mark.asyncio
    async def test_updates_agent_history(self, extractor):
        """Test: Agent history is updated."""
        state = create_initial_state(message="Test")

        extractor.call_llm = AsyncMock(return_value=json.dumps({}))

        result = await extractor.process(state)

        assert "entity_extractor" in result["agent_history"]
        assert result["current_agent"] == "entity_extractor"

    @pytest.mark.asyncio
    async def test_adds_extracted_entities_to_state(self, extractor):
        """Test: Extracted entities added to state."""
        state = create_initial_state(message="Upgrade to premium")

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "plan_name": "premium",
            "action": "upgrade"
        }))

        result = await extractor.process(state)

        assert "extracted_entities" in result
        assert isinstance(result["extracted_entities"], dict)


class TestSystemPrompt:
    """Test system prompt generation."""

    def test_system_prompt_contains_entity_types(self, extractor):
        """Test: System prompt contains all entity types."""
        prompt = extractor._get_system_prompt()

        # Check for entity types
        assert "plan_name" in prompt
        assert "amount" in prompt
        assert "feature" in prompt
        assert "date" in prompt
        assert "team_size" in prompt
        assert "competitor" in prompt
        assert "integration" in prompt
        assert "tech_stack" in prompt
        assert "action" in prompt
        assert "problem" in prompt

    def test_system_prompt_has_examples(self, extractor):
        """Test: System prompt has examples."""
        prompt = extractor._get_system_prompt()

        assert "Examples" in prompt or "examples" in prompt
        assert "free" in prompt
        assert "premium" in prompt

    def test_system_prompt_has_json_format(self, extractor):
        """Test: System prompt specifies JSON output."""
        prompt = extractor._get_system_prompt()

        assert "JSON" in prompt
        assert "{{" in prompt  # JSON example


class TestSpecialEntityParsing:
    """Test special entity parsing enhancements."""

    @pytest.mark.asyncio
    async def test_adds_billing_cycle_for_monthly_amount(self, extractor):
        """Test: Billing cycle detected from message context."""
        state = create_initial_state(message="$99 per month")

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "amount": "$99"
        }))

        result = await extractor.process(state)

        # billing_cycle should be added by _parse_special_entities
        entities = result["extracted_entities"]
        assert "billing_cycle" in entities
        assert entities["billing_cycle"] == "monthly"

    @pytest.mark.asyncio
    async def test_adds_urgency_flag(self, extractor):
        """Test: Urgency flag added for urgent messages."""
        state = create_initial_state(message="URGENT: App crashed!")

        extractor.call_llm = AsyncMock(return_value=json.dumps({
            "problem": "crash"
        }))

        result = await extractor.process(state)

        # urgency should be added
        entities = result["extracted_entities"]
        assert "urgency" in entities
        assert entities["urgency"] == "high"
