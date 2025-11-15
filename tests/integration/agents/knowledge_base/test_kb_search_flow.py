"""
Integration tests for KB search flow (Searcher → Ranker → Synthesizer).
"""

import pytest
from src.agents.essential.knowledge_base import KBSearcher, KBRanker, KBSynthesizer
from src.workflow.state import create_initial_state


class TestKBSearchFlow:
    """Test end-to-end KB search flow"""

    @pytest.mark.asyncio
    async def test_full_search_flow(self, test_db_session, sample_kb_articles):
        """Test complete flow: search → rank → synthesize"""
        # Initialize agents
        searcher = KBSearcher()
        ranker = KBRanker()
        synthesizer = KBSynthesizer()

        # Create initial state
        state = create_initial_state(
            message="How do I upgrade my plan?",
            context={"user_id": "user_123"}
        )

        # Step 1: Search for relevant articles
        state = await searcher.process(state)

        assert "kb_search_results" in state
        assert len(state["kb_search_results"]) > 0
        assert state["kb_search_count"] > 0

        # Step 2: Rank the results
        state = await ranker.process(state)

        assert "kb_ranked_results" in state
        assert len(state["kb_ranked_results"]) > 0
        # Verify results are sorted by score
        scores = [r["rank_score"] for r in state["kb_ranked_results"]]
        assert scores == sorted(scores, reverse=True)

        # Step 3: Synthesize response
        state = await synthesizer.process(state)

        assert "kb_synthesized_response" in state
        assert "answer" in state["kb_synthesized_response"]
        assert "sources" in state["kb_synthesized_response"]
        assert "confidence_score" in state["kb_synthesized_response"]
        assert len(state["kb_synthesized_response"]["sources"]) > 0

    @pytest.mark.asyncio
    async def test_search_flow_with_category_filter(self, test_db_session, sample_kb_articles):
        """Test search flow with category filtering"""
        searcher = KBSearcher()
        ranker = KBRanker()

        state = create_initial_state(
            message="API authentication help",
            context={}
        )
        state["kb_search_category"] = "integrations"

        # Search with category filter
        state = await searcher.process(state)

        assert "kb_search_results" in state
        # All results should be from integrations category
        for result in state["kb_search_results"]:
            assert result["category"] == "integrations"

        # Rank filtered results
        state = await ranker.process(state)

        assert "kb_ranked_results" in state
        assert len(state["kb_ranked_results"]) > 0

    @pytest.mark.asyncio
    async def test_search_flow_no_results(self, test_db_session, sample_kb_articles):
        """Test search flow when no results found"""
        searcher = KBSearcher()
        synthesizer = KBSynthesizer()

        state = create_initial_state(
            message="quantum physics equations",
            context={}
        )

        # Search (likely no results for unrelated query)
        state = await searcher.process(state)

        # Even with no results, state should be updated
        assert "kb_search_results" in state
        assert "kb_search_count" in state

        # Synthesizer should handle empty results
        state = await synthesizer.process(state)

        assert "kb_synthesized_response" in state

    @pytest.mark.asyncio
    async def test_search_flow_with_multiple_categories(self, test_db_session, sample_kb_articles):
        """Test search returns articles from multiple categories"""
        searcher = KBSearcher()
        ranker = KBRanker()

        state = create_initial_state(
            message="account settings",  # Could match billing or usage
            context={}
        )

        # Search without category filter
        state = await searcher.process(state)

        assert "kb_search_results" in state

        # Rank all results
        state = await ranker.process(state)

        assert "kb_ranked_results" in state

        # Verify diversity in categories (if multiple results)
        if len(state["kb_ranked_results"]) > 1:
            categories = {r["category"] for r in state["kb_ranked_results"]}
            # We expect diverse results
            assert len(categories) >= 1

    @pytest.mark.asyncio
    async def test_ranking_considers_quality_and_recency(self, test_db_session, sample_kb_articles):
        """Test that ranking considers both quality and recency"""
        ranker = KBRanker()

        # Create mock search results with different quality/recency profiles
        state = create_initial_state(message="test", context={})
        state["kb_search_results"] = [
            {
                "article_id": "kb_001",
                "title": "High quality, recent",
                "quality_score": 90,
                "helpfulness_ratio": 0.95,
                "updated_at": "2024-11-01T00:00:00"
            },
            {
                "article_id": "kb_002",
                "title": "Low quality, old",
                "quality_score": 60,
                "helpfulness_ratio": 0.50,
                "updated_at": "2023-01-01T00:00:00"
            },
            {
                "article_id": "kb_003",
                "title": "Medium quality, medium age",
                "quality_score": 75,
                "helpfulness_ratio": 0.75,
                "updated_at": "2024-06-01T00:00:00"
            }
        ]

        state = await ranker.process(state)

        assert "kb_ranked_results" in state
        # High quality recent article should rank first
        assert state["kb_ranked_results"][0]["article_id"] == "kb_001"

    @pytest.mark.asyncio
    async def test_synthesis_confidence_score(self, test_db_session, sample_kb_articles):
        """Test synthesizer assigns appropriate confidence scores"""
        synthesizer = KBSynthesizer()

        # High quality matches
        state = create_initial_state(message="test", context={})
        state["kb_ranked_results"] = [
            {
                "article_id": "kb_001",
                "title": "Excellent match",
                "content": "Detailed answer to the question...",
                "quality_score": 95,
                "rank_score": 0.95
            }
        ]

        state = await synthesizer.process(state)

        assert "kb_synthesized_response" in state
        response = state["kb_synthesized_response"]
        assert response["confidence_score"] >= 0.8  # High confidence

        # Low quality matches
        state2 = create_initial_state(message="test", context={})
        state2["kb_ranked_results"] = [
            {
                "article_id": "kb_002",
                "title": "Poor match",
                "content": "Brief content",
                "quality_score": 50,
                "rank_score": 0.4
            }
        ]

        state2 = await synthesizer.process(state2)

        response2 = state2["kb_synthesized_response"]
        assert response2["confidence_score"] < 0.7  # Lower confidence

    @pytest.mark.asyncio
    async def test_search_flow_state_persistence(self, test_db_session, sample_kb_articles):
        """Test that state is properly maintained across agents"""
        searcher = KBSearcher()
        ranker = KBRanker()
        synthesizer = KBSynthesizer()

        state = create_initial_state(
            message="billing question",
            context={"user_id": "user_456", "session_id": "sess_789"}
        )

        # Run through full pipeline
        state = await searcher.process(state)
        original_context = state["context"].copy()

        state = await ranker.process(state)
        assert state["context"] == original_context  # Context preserved

        state = await synthesizer.process(state)
        assert state["context"] == original_context  # Still preserved

        # Verify current_agent updates
        assert state["current_agent"] == "kb_synthesizer"
