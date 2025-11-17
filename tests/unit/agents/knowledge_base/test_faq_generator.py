"""
Unit tests for FAQ Generator agent.
"""

import pytest
from src.agents.essential.knowledge_base.faq_generator import FAQGenerator
from src.workflow.state import create_initial_state


class TestFAQGenerator:
    """Test suite for FAQ Generator agent"""

    @pytest.fixture
    def faq_generator(self):
        """FAQ Generator instance"""
        return FAQGenerator()

    def test_initialization(self, faq_generator):
        """Test FAQ Generator initializes correctly"""
        assert faq_generator.config.name == "faq_generator"
        assert faq_generator.config.model == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_generate_faqs_no_questions(self, faq_generator, mock_db_session):
        """Test FAQ generation with no common questions"""
        faqs = await faq_generator.generate_faqs(days=30, min_frequency=100, limit=5)

        assert isinstance(faqs, list)

    @pytest.mark.asyncio
    async def test_generate_faq_entry(self, faq_generator, mock_llm):
        """Test FAQ entry generation"""
        cluster = [
            {"question": "How do I upgrade?", "count": 10},
            {"question": "Can I upgrade my plan?", "count": 8}
        ]

        faq = await faq_generator._generate_faq_entry(cluster)

        assert "question" in faq
        assert "answer" in faq or "status" in faq
        assert faq.get("frequency", 0) >= 0

    @pytest.mark.asyncio
    async def test_generate_faq_entry_with_error(self, faq_generator):
        """Test FAQ generation handles errors"""
        cluster = [
            {"question": "Test question", "count": 5}
        ]

        # This should handle the error gracefully
        faq = await faq_generator._generate_faq_entry(cluster)

        assert "question" in faq or "status" in faq

    @pytest.mark.asyncio
    async def test_process_updates_state(self, faq_generator, mock_db_session):
        """Test process method updates state"""
        state = create_initial_state(message="test", context={})
        state["faq_generation_days"] = 30
        state["faq_min_frequency"] = 10
        state["faq_limit"] = 5

        updated_state = await faq_generator.process(state)

        assert "generated_faqs" in updated_state
        assert "faqs_count" in updated_state
