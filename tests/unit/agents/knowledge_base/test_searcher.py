"""
Unit tests for KB Searcher agent.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.agents.essential.knowledge_base.searcher import KBSearcher
from src.workflow.state import create_initial_state


class TestKBSearcher:
    """Test suite for KB Searcher agent"""

    @pytest.fixture
    def kb_searcher(self, mock_qdrant):
        """KB Searcher with mocked Qdrant"""
        with patch('src.agents.essential.knowledge_base.searcher.VectorStore') as mock_vs:
            mock_vs.return_value = mock_qdrant
            return KBSearcher()

    def test_initialization(self, kb_searcher):
        """Test KB Searcher initializes correctly"""
        assert kb_searcher.config.name == "kb_searcher"
        assert kb_searcher.config.type.value == "utility"

    def test_search_returns_results(self, kb_searcher, mock_qdrant):
        """Test search returns results above similarity threshold"""
        results = kb_searcher.search(
            query="How do I upgrade?",
            limit=5,
            min_similarity=0.7
        )

        assert len(results) > 0
        assert all(r["similarity_score"] >= 0.7 for r in results)

    def test_search_filters_by_category(self, kb_searcher, mock_qdrant):
        """Test category filtering works"""
        results = kb_searcher.search(
            query="billing",
            category="billing",
            limit=5
        )

        assert all(r["category"] == "billing" for r in results)

    def test_search_with_no_results(self, kb_searcher, mock_qdrant):
        """Test search with no matching articles"""
        mock_qdrant.search.return_value = []

        results = kb_searcher.search(
            query="nonexistent query",
            min_similarity=0.9
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_process_updates_state(self, kb_searcher, mock_qdrant):
        """Test process method updates state correctly"""
        state = create_initial_state(
            message="How do I upgrade my plan?",
            context={"kb_search_limit": 3}
        )

        updated_state = await kb_searcher.process(state)

        assert "kb_results" in updated_state
        assert "kb_search_latency_ms" in updated_state
        assert updated_state["current_agent"] == "kb_searcher"

    @pytest.mark.asyncio
    async def test_search_by_intent(self, kb_searcher, mock_qdrant):
        """Test search by intent mapping"""
        results = await kb_searcher.search_by_intent(
            intent="billing_upgrade",
            user_message="How to upgrade?",
            limit=3
        )

        assert isinstance(results, list)
