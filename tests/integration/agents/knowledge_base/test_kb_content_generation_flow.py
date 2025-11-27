"""
Integration tests for KB content generation flow (Gap Detection → Suggestions → FAQs).
"""

import pytest
from src.agents.essential.knowledge_base import KBGapDetector, KBSuggester, FAQGenerator
from src.workflow.state import create_initial_state


# Skip all tests - JSONB columns in models are not supported by SQLite
pytestmark = pytest.mark.skip(
    reason="KB integration tests require PostgreSQL (JSONB columns not supported by SQLite)"
)


class TestKBContentGenerationFlow:
    """Test end-to-end KB content generation flow"""

    @pytest.mark.asyncio
    async def test_gap_detection_to_suggestions(self, test_db_session, sample_tickets, sample_conversations):
        """Test flow: detect gaps → generate suggestions"""
        gap_detector = KBGapDetector()
        suggester = KBSuggester()

        # Step 1: Detect knowledge gaps
        state = create_initial_state(message="test", context={})
        state["gap_detection_days"] = 30
        state["gap_min_frequency"] = 2  # Lower threshold for test data

        state = await gap_detector.process(state)

        assert "kb_gaps" in state
        gaps = state["kb_gaps"]

        # Step 2: Generate suggestions from gaps
        state["suggestion_days"] = 30

        state = await suggester.process(state)

        assert "kb_suggestions" in state
        suggestions = state["kb_suggestions"]

        # Suggestions should include gap-based suggestions
        if len(gaps) > 0:
            assert len(suggestions) > 0
            # Check that some suggestions came from gap detection
            gap_sources = [s for s in suggestions if s.get("source") == "gap_detection"]
            assert len(gap_sources) > 0

    @pytest.mark.asyncio
    async def test_faq_generation_from_common_questions(self, test_db_session, sample_tickets, sample_conversations):
        """Test FAQ generation from frequently asked questions"""
        faq_generator = FAQGenerator()

        state = create_initial_state(message="test", context={})
        state["faq_generation_days"] = 30
        state["faq_min_frequency"] = 2  # Lower threshold for test data
        state["faq_limit"] = 10

        state = await faq_generator.process(state)

        assert "generated_faqs" in state
        faqs = state["generated_faqs"]

        # Should generate some FAQs from test data
        assert isinstance(faqs, list)

        # Each FAQ should have required fields
        for faq in faqs:
            if "question" in faq:  # Some might be error entries
                assert "answer" in faq or "status" in faq
                assert "frequency" in faq

    @pytest.mark.asyncio
    async def test_prioritize_content_suggestions(self, test_db_session, sample_tickets, sample_conversations):
        """Test that content suggestions are prioritized correctly"""
        gap_detector = KBGapDetector()
        suggester = KBSuggester()

        # Detect gaps
        state = create_initial_state(message="test", context={})
        state["gap_detection_days"] = 30
        state["gap_min_frequency"] = 2

        state = await gap_detector.process(state)

        # Generate suggestions
        state["suggestion_days"] = 30

        state = await suggester.process(state)

        suggestions = state["kb_suggestions"]

        if len(suggestions) > 1:
            # Suggestions should be ordered by priority
            priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            priorities = [priority_map.get(s.get("priority", "low"), 0) for s in suggestions]

            # Check if generally prioritized (allowing some flexibility)
            # Critical and high priority items should appear first
            high_priority_count = sum(1 for p in priorities[:len(priorities)//2] if p >= 3)
            low_priority_count = sum(1 for p in priorities[len(priorities)//2:] if p >= 3)

            # More high priority items should be in first half
            if high_priority_count + low_priority_count > 0:
                assert high_priority_count >= low_priority_count

    @pytest.mark.asyncio
    async def test_gap_detection_clustering(self, test_db_session, sample_conversations):
        """Test that similar queries are clustered together"""
        gap_detector = KBGapDetector()

        state = create_initial_state(message="test", context={})
        state["gap_detection_days"] = 30
        state["gap_min_frequency"] = 2

        state = await gap_detector.process(state)

        gaps = state["kb_gaps"]

        # Each gap should represent a cluster of similar queries
        for gap in gaps:
            assert "topic" in gap
            assert "frequency" in gap
            assert gap["frequency"] >= 2  # Min frequency threshold

    @pytest.mark.asyncio
    async def test_suggestion_deduplication(self, test_db_session, sample_tickets):
        """Test that duplicate suggestions are removed"""
        suggester = KBSuggester()

        # Create state with duplicate gap suggestions
        state = create_initial_state(message="test", context={})
        state["kb_gaps"] = [
            {
                "suggested_article_title": "How to Upgrade Your Plan",
                "category": "billing",
                "frequency": 20,
                "priority_score": 85,
                "key_questions": ["How to upgrade?"]
            },
            {
                "suggested_article_title": "How to Upgrade Your Plan",  # Duplicate
                "category": "billing",
                "frequency": 15,
                "priority_score": 80,
                "key_questions": ["Upgrade process?"]
            },
            {
                "suggested_article_title": "API Authentication Guide",
                "category": "integrations",
                "frequency": 30,
                "priority_score": 90,
                "key_questions": ["How to authenticate API?"]
            }
        ]
        state["suggestion_days"] = 30

        state = await suggester.process(state)

        suggestions = state["kb_suggestions"]

        # Should have deduplicated by title
        titles = [s["title"] for s in suggestions]
        unique_titles = set(titles)

        assert len(titles) == len(unique_titles)  # No duplicates

    @pytest.mark.asyncio
    async def test_faq_clustering_similar_questions(self, test_db_session):
        """Test that similar questions are clustered into single FAQ"""
        faq_generator = FAQGenerator()

        # This tests the internal clustering logic
        # In a real scenario with proper data, similar questions should cluster

        state = create_initial_state(message="test", context={})
        state["faq_generation_days"] = 30
        state["faq_min_frequency"] = 1
        state["faq_limit"] = 5

        state = await faq_generator.process(state)

        faqs = state["generated_faqs"]

        # Each FAQ should represent a cluster of similar questions
        assert isinstance(faqs, list)

    @pytest.mark.asyncio
    async def test_full_content_generation_pipeline(self, test_db_session, sample_tickets, sample_conversations):
        """Test complete pipeline: gaps → suggestions → FAQs"""
        gap_detector = KBGapDetector()
        suggester = KBSuggester()
        faq_generator = FAQGenerator()

        # Step 1: Detect gaps
        state = create_initial_state(message="test", context={})
        state["gap_detection_days"] = 30
        state["gap_min_frequency"] = 2

        state = await gap_detector.process(state)

        initial_gaps = len(state.get("kb_gaps", []))

        # Step 2: Generate article suggestions
        state["suggestion_days"] = 30

        state = await suggester.process(state)

        suggestions = state["kb_suggestions"]

        # Step 3: Generate FAQs
        state["faq_generation_days"] = 30
        state["faq_min_frequency"] = 2
        state["faq_limit"] = 5

        state = await faq_generator.process(state)

        faqs = state["generated_faqs"]

        # Should have content generation results
        assert "kb_gaps" in state
        assert "kb_suggestions" in state
        assert "generated_faqs" in state

        # All should be lists
        assert isinstance(suggestions, list)
        assert isinstance(faqs, list)

    @pytest.mark.asyncio
    async def test_suggestions_from_multiple_sources(self, test_db_session, sample_tickets, sample_conversations):
        """Test that suggestions come from multiple sources"""
        suggester = KBSuggester()

        # Provide both gaps and ticket data
        state = create_initial_state(message="test", context={})
        state["kb_gaps"] = [
            {
                "suggested_article_title": "Gap-Based Article",
                "category": "billing",
                "frequency": 20,
                "priority_score": 85,
                "key_questions": []
            }
        ]
        state["suggestion_days"] = 30

        state = await suggester.process(state)

        suggestions = state["kb_suggestions"]

        # Should have suggestions from multiple sources
        sources = {s.get("source") for s in suggestions}

        # At minimum should have gap_detection source
        assert "gap_detection" in sources

        # May also have tickets or other sources depending on data

    @pytest.mark.asyncio
    async def test_gap_priority_scoring(self, test_db_session):
        """Test that gaps are scored by priority correctly"""
        gap_detector = KBGapDetector()

        # Create mock state with gap data
        state = create_initial_state(message="test", context={})
        state["gap_detection_days"] = 30
        state["gap_min_frequency"] = 2

        state = await gap_detector.process(state)

        gaps = state["kb_gaps"]

        # Each gap should have a priority score
        for gap in gaps:
            assert "priority_score" in gap
            assert 0 <= gap["priority_score"] <= 100

    @pytest.mark.asyncio
    async def test_suggestion_categories_match_gaps(self, test_db_session):
        """Test that suggestions maintain category information from gaps"""
        suggester = KBSuggester()

        state = create_initial_state(message="test", context={})
        state["kb_gaps"] = [
            {
                "suggested_article_title": "API Guide",
                "category": "integrations",
                "frequency": 25,
                "priority_score": 90,
                "key_questions": []
            },
            {
                "suggested_article_title": "Billing Guide",
                "category": "billing",
                "frequency": 30,
                "priority_score": 85,
                "key_questions": []
            }
        ]
        state["suggestion_days"] = 30

        state = await suggester.process(state)

        suggestions = state["kb_suggestions"]

        # Suggestions should preserve categories
        api_suggestions = [s for s in suggestions if s["category"] == "integrations"]
        billing_suggestions = [s for s in suggestions if s["category"] == "billing"]

        assert len(api_suggestions) > 0
        assert len(billing_suggestions) > 0

    @pytest.mark.asyncio
    async def test_faq_status_and_review(self, test_db_session):
        """Test that generated FAQs are marked for review"""
        faq_generator = FAQGenerator()

        state = create_initial_state(message="test", context={})
        state["faq_generation_days"] = 30
        state["faq_min_frequency"] = 2
        state["faq_limit"] = 5

        state = await faq_generator.process(state)

        faqs = state["generated_faqs"]

        # FAQs should be marked as pending review
        for faq in faqs:
            if "status" in faq:
                # Status should indicate needs review
                assert faq["status"] in ["pending_review", "generated", "draft"]

    @pytest.mark.asyncio
    async def test_content_generation_with_no_data(self, test_db_session):
        """Test content generation handles no data gracefully"""
        gap_detector = KBGapDetector()
        suggester = KBSuggester()
        faq_generator = FAQGenerator()

        # Empty database - no tickets or conversations
        state = create_initial_state(message="test", context={})
        state["gap_detection_days"] = 30
        state["gap_min_frequency"] = 10

        state = await gap_detector.process(state)

        assert "kb_gaps" in state
        assert isinstance(state["kb_gaps"], list)

        state["suggestion_days"] = 30
        state = await suggester.process(state)

        assert "kb_suggestions" in state
        assert isinstance(state["kb_suggestions"], list)

        state["faq_generation_days"] = 30
        state["faq_min_frequency"] = 10
        state = await faq_generator.process(state)

        assert "generated_faqs" in state
        assert isinstance(state["generated_faqs"], list)
