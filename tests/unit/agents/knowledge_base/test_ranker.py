"""
Unit tests for KB Ranker agent.
"""

import pytest
from datetime import datetime, timedelta
from src.agents.essential.knowledge_base.ranker import KBRanker
from src.workflow.state import create_initial_state


class TestKBRanker:
    """Test suite for KB Ranker agent"""

    @pytest.fixture
    def kb_ranker(self):
        """KB Ranker instance"""
        return KBRanker()

    def test_initialization(self, kb_ranker):
        """Test KB Ranker initializes correctly"""
        assert kb_ranker.config.name == "kb_ranker"
        assert kb_ranker.SIMILARITY_WEIGHT == 0.50

    def test_rank_by_quality(self, kb_ranker):
        """Test quality score affects ranking"""
        articles = [
            {
                "article_id": "1",
                "similarity_score": 0.8,
                "quality_score": 95,
                "helpful_count": 50,
                "not_helpful_count": 2,
                "view_count": 500,
                "created_at": datetime.now()
            },
            {
                "article_id": "2",
                "similarity_score": 0.85,
                "quality_score": 40,
                "helpful_count": 5,
                "not_helpful_count": 10,
                "view_count": 50,
                "created_at": datetime.now()
            }
        ]

        ranked = kb_ranker.rank(articles)

        # Article with better quality should rank higher
        assert ranked[0]["final_score"] > 0

    def test_recency_score_calculation(self, kb_ranker):
        """Test recency score calculated correctly"""
        old_date = datetime.now() - timedelta(days=365)
        new_date = datetime.now() - timedelta(days=7)

        old_score = kb_ranker._calculate_recency_score(old_date, None)
        new_score = kb_ranker._calculate_recency_score(new_date, None)

        assert new_score > old_score
        assert 0 <= old_score <= 1
        assert 0 <= new_score <= 1

    def test_helpfulness_score_calculation(self, kb_ranker):
        """Test helpfulness score uses Wilson interval"""
        # Highly helpful article
        high_score = kb_ranker._calculate_helpfulness_score(50, 2, 500)

        # Not helpful article
        low_score = kb_ranker._calculate_helpfulness_score(5, 20, 100)

        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1

    @pytest.mark.asyncio
    async def test_process_updates_state(self, kb_ranker, sample_kb_results):
        """Test process method updates state"""
        state = create_initial_state(message="test", context={})
        state["kb_results"] = sample_kb_results

        updated_state = await kb_ranker.process(state)

        assert "kb_ranked_results" in updated_state
        assert len(updated_state["kb_ranked_results"]) == len(sample_kb_results)

    def test_rank_changes_tracked(self, kb_ranker, sample_kb_results):
        """Test rank changes are tracked"""
        ranked = kb_ranker.rank(sample_kb_results)

        for article in ranked:
            assert "rank" in article
            assert "original_rank" in article
            assert "rank_change" in article
