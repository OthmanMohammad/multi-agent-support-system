"""
Integration tests for Entity Extractor with real LLM calls.

These tests use the actual Anthropic API and verify real-world extraction.
They are marked with @pytest.mark.integration and require ANTHROPIC_API_KEY.

Part of: STORY-01 Routing & Orchestration Swarm (TASK-103)
"""

import pytest
import os

from src.agents.essential.routing.entity_extractor import EntityExtractor
from src.workflow.state import create_initial_state


# Skip these tests - they require real LLM calls and produce inconsistent results in CI
pytestmark = pytest.mark.skip(
    reason="Entity extractor integration tests require real LLM and stable API responses"
)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestEntityExtractorIntegration:
    """Integration tests with real LLM calls."""

    @pytest.fixture
    def extractor(self):
        """Create EntityExtractor with real Anthropic client."""
        return EntityExtractor()

    @pytest.mark.asyncio
    async def test_real_llm_plan_and_team_size(self, extractor):
        """Test real LLM extraction of plan and team size."""
        state = create_initial_state(
            message="I want to upgrade to Premium for a team of 25 users next month"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Extracted Entities:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract plan, team_size, date, action
        assert "plan_name" in entities
        assert entities["plan_name"] == "premium"

        assert "team_size" in entities
        assert entities["team_size"] >= 20  # Should be around 25

        assert "action" in entities

    @pytest.mark.asyncio
    async def test_real_llm_competitor_extraction(self, extractor):
        """Test real LLM extraction of competitor."""
        state = create_initial_state(
            message="How does your pricing compare to Asana and Monday.com?"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Competitor Extraction:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract competitor and action
        assert "competitor" in entities or "action" in entities

    @pytest.mark.asyncio
    async def test_real_llm_integration_and_problem(self, extractor):
        """Test real LLM extraction of integration and problem."""
        state = create_initial_state(
            message="The Slack integration is not working properly - it keeps crashing"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Integration & Problem Extraction:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract integration and problem
        assert "integration" in entities
        assert "problem" in entities

    @pytest.mark.asyncio
    async def test_real_llm_tech_stack_extraction(self, extractor):
        """Test real LLM extraction of tech stack."""
        state = create_initial_state(
            message="Our React application running on AWS is experiencing slow performance"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Tech Stack Extraction:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract tech_stack and problem
        assert "tech_stack" in entities or "problem" in entities

    @pytest.mark.asyncio
    async def test_real_llm_amount_extraction(self, extractor):
        """Test real LLM extraction of amounts."""
        state = create_initial_state(
            message="What's the $99 per month plan include? Any discounts for 50 seats?"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Amount Extraction:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract amount and team_size
        assert "amount" in entities or "team_size" in entities

    @pytest.mark.asyncio
    async def test_real_llm_action_extraction(self, extractor):
        """Test real LLM extraction of actions."""
        state = create_initial_state(
            message="I need to cancel my subscription and export all my data"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Action Extraction:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract action
        assert "action" in entities

    @pytest.mark.asyncio
    async def test_real_llm_feature_extraction(self, extractor):
        """Test real LLM extraction of features."""
        state = create_initial_state(
            message="How do I set up webhooks and enable the API for my account?"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Feature Extraction:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract feature
        assert "feature" in entities

    @pytest.mark.asyncio
    async def test_real_llm_no_entities(self, extractor):
        """Test real LLM with message containing no entities."""
        state = create_initial_state(
            message="Hello, how are you today?"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ No Entities Message:")
        print(f"  Entities extracted: {len(entities)}")
        print(f"  {entities}")

        # Should return few or no entities
        assert isinstance(entities, dict)

    @pytest.mark.asyncio
    async def test_real_llm_complex_message(self, extractor):
        """Test real LLM with complex multi-entity message."""
        state = create_initial_state(
            message="We need to upgrade from Basic to Enterprise for our team of 100 "
                   "developers using Python and React, and we need better API access"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Complex Message Extraction:")
        for key, value in entities.items():
            print(f"  {key}: {value}")

        # Should extract multiple entities
        assert len(entities) >= 3, f"Expected 3+ entities, got {len(entities)}"

    @pytest.mark.asyncio
    async def test_real_llm_batch_precision(self, extractor):
        """Test extraction precision on a batch of messages."""
        test_cases = [
            {
                "message": "Upgrade to premium",
                "expected_entities": ["plan_name", "action"]
            },
            {
                "message": "For 50 users",
                "expected_entities": ["team_size"]
            },
            {
                "message": "Slack integration broken",
                "expected_entities": ["integration", "problem"]
            },
            {
                "message": "$99/month",
                "expected_entities": ["amount"]
            },
            {
                "message": "Compare to Asana",
                "expected_entities": ["competitor", "action"]
            },
        ]

        correct = 0
        total = len(test_cases)

        for i, test in enumerate(test_cases, 1):
            state = create_initial_state(message=test["message"])

            result = await extractor.process(state)
            entities = result["extracted_entities"]

            # Check if at least one expected entity was found
            found = any(key in entities for key in test["expected_entities"])

            if found:
                correct += 1
                status = "✓"
            else:
                status = "✗"

            print(f"{status} Test {i}: '{test['message']}'")
            print(f"   Expected: {test['expected_entities']}")
            print(f"   Got: {list(entities.keys())}")

        precision = (correct / total) * 100
        print(f"\n✓ Overall Precision: {precision:.1f}% ({correct}/{total})")

        # Should achieve >80% precision
        assert precision >= 80, f"Precision too low: {precision:.1f}%"

    @pytest.mark.asyncio
    async def test_real_llm_entity_count(self, extractor):
        """Test that appropriate number of entities are extracted."""
        state = create_initial_state(
            message="Upgrade to Enterprise for 100 users at $50 per seat"
        )

        result = await extractor.process(state)
        entities = result["extracted_entities"]

        print(f"\n✓ Entity Count:")
        print(f"  Entities: {entities}")
        print(f"  Count: {len(entities)}")

        # Should extract multiple relevant entities
        assert len(entities) >= 2, "Should extract at least 2 entities"
