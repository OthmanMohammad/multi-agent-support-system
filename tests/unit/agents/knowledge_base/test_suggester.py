"""
Unit tests for KB Suggester agent.
"""

import pytest
from src.agents.essential.knowledge_base.suggester import KBSuggester
from src.workflow.state import create_initial_state


class TestKBSuggester:
    """Test suite for KB Suggester agent"""

    @pytest.fixture
    def kb_suggester(self):
        """KB Suggester instance"""
        return KBSuggester()

    def test_initialization(self, kb_suggester):
        """Test KB Suggester initializes correctly"""
        assert kb_suggester.config.name == "kb_suggester"
        assert kb_suggester.config.model == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Database connection pool event loop conflict - needs isolation fix")
    async def test_generate_suggestions_from_gaps(self, kb_suggester):
        """Test suggestion generation from gaps"""
        gaps = [
            {
                "suggested_article_title": "API Authentication Guide",
                "category": "api",
                "frequency": 25,
                "priority_score": 85,
                "key_questions": ["How to authenticate?"]
            }
        ]

        suggestions = await kb_suggester.generate_suggestions(kb_gaps=gaps)

        assert len(suggestions) > 0
        assert suggestions[0]["title"] == "API Authentication Guide"
        assert suggestions[0]["category"] == "api"

    def test_intent_to_title(self, kb_suggester):
        """Test intent to title mapping"""
        title = kb_suggester._intent_to_title("billing_upgrade")

        assert title == "How to Upgrade Your Plan"

    def test_intent_to_category(self, kb_suggester):
        """Test intent to category mapping"""
        assert kb_suggester._intent_to_category("billing_upgrade") == "billing"
        assert kb_suggester._intent_to_category("technical_bug") == "technical"
        assert kb_suggester._intent_to_category("integration_api") == "integrations"

    def test_map_gap_priority(self, kb_suggester):
        """Test gap priority mapping"""
        assert kb_suggester._map_gap_priority(90) == "critical"
        assert kb_suggester._map_gap_priority(70) == "high"
        assert kb_suggester._map_gap_priority(50) == "medium"
        assert kb_suggester._map_gap_priority(30) == "low"

    def test_deduplicate_suggestions(self, kb_suggester):
        """Test suggestion deduplication"""
        suggestions = [
            {"title": "Same Title", "category": "billing"},
            {"title": "Same Title", "category": "technical"},
            {"title": "Different Title", "category": "usage"}
        ]

        unique = kb_suggester._deduplicate_suggestions(suggestions)

        assert len(unique) == 2

    def test_prioritize_suggestions(self, kb_suggester):
        """Test suggestions are prioritized correctly"""
        suggestions = [
            {"priority": "low", "title": "Low", "source": "tickets"},
            {"priority": "high", "title": "High", "source": "gap_detection"},
            {"priority": "critical", "title": "Critical", "source": "gap_detection"}
        ]

        prioritized = kb_suggester._prioritize_suggestions(suggestions)

        assert prioritized[0]["priority"] == "critical"
        assert prioritized[-1]["priority"] == "low"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Database connection pool event loop conflict - needs isolation fix")
    async def test_process_updates_state(self, kb_suggester, mock_db_session):
        """Test process method updates state"""
        state = create_initial_state(message="test", context={})
        state["kb_gaps"] = []
        state["suggestion_days"] = 30

        updated_state = await kb_suggester.process(state)

        assert "kb_suggestions" in updated_state
        assert "suggestions_count" in updated_state
