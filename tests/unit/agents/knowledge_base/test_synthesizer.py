"""
Unit tests for KB Synthesizer agent.
"""

import pytest
from src.agents.essential.knowledge_base.synthesizer import KBSynthesizer
from src.workflow.state import create_initial_state


class TestKBSynthesizer:
    """Test suite for KB Synthesizer agent"""

    @pytest.fixture
    def kb_synthesizer(self):
        """KB Synthesizer instance"""
        return KBSynthesizer()

    def test_initialization(self, kb_synthesizer):
        """Test KB Synthesizer initializes correctly"""
        assert kb_synthesizer.config.name == "kb_synthesizer"
        assert kb_synthesizer.config.model == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_synthesize_single_article(self, kb_synthesizer, mock_llm, sample_kb_article):
        """Test synthesis with single article"""
        result = await kb_synthesizer.synthesize(
            user_message="How do I upgrade?",
            kb_articles=[sample_kb_article]
        )

        assert "synthesized_answer" in result
        assert result["synthesis_confidence"] > 0
        assert len(result["sources_used"]) == 1

    @pytest.mark.asyncio
    async def test_synthesize_multiple_articles(self, kb_synthesizer, mock_llm, sample_kb_results):
        """Test synthesis combines multiple articles"""
        result = await kb_synthesizer.synthesize(
            user_message="How do I upgrade and how much?",
            kb_articles=sample_kb_results
        )

        assert len(result["sources_used"]) == len(sample_kb_results)

    @pytest.mark.asyncio
    async def test_process_with_no_articles(self, kb_synthesizer):
        """Test synthesis with no KB articles"""
        state = create_initial_state(message="test", context={})
        state["kb_ranked_results"] = []

        updated_state = await kb_synthesizer.process(state)

        assert updated_state["synthesized_answer"] is None
        assert updated_state["synthesis_confidence"] == 0.0

    def test_confidence_calculation(self, kb_synthesizer):
        """Test confidence calculation"""
        high_quality_articles = [
            {"final_score": 0.95, "article_id": "1"},
            {"final_score": 0.90, "article_id": "2"}
        ]

        low_quality_articles = [
            {"final_score": 0.60, "article_id": "3"}
        ]

        long_answer = "This is a comprehensive answer. " * 20
        short_answer = "Short"

        high_conf = kb_synthesizer._calculate_confidence(high_quality_articles, long_answer)
        low_conf = kb_synthesizer._calculate_confidence(low_quality_articles, short_answer)

        assert high_conf > low_conf
