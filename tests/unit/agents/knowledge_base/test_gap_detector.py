"""
Unit tests for KB Gap Detector agent.
"""

import pytest
from src.agents.essential.knowledge_base.gap_detector import KBGapDetector
from src.workflow.state import create_initial_state


class TestKBGapDetector:
    """Test suite for KB Gap Detector agent"""

    @pytest.fixture
    def kb_gap_detector(self):
        """KB Gap Detector instance"""
        return KBGapDetector()

    def test_initialization(self, kb_gap_detector):
        """Test KB Gap Detector initializes correctly"""
        assert kb_gap_detector.config.name == "kb_gap_detector"
        assert kb_gap_detector.config.model == "claude-3-haiku-20240307"
        assert kb_gap_detector.LOW_MATCH_THRESHOLD == 0.7

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Database connection pool event loop conflict - needs isolation fix")
    async def test_detect_gaps_insufficient_data(self, kb_gap_detector, mock_db_session):
        """Test gap detection with insufficient data"""
        gaps = await kb_gap_detector.detect_gaps(days=30, min_frequency=100)

        assert isinstance(gaps, list)

    def test_calculate_priority(self, kb_gap_detector):
        """Test priority calculation"""
        queries = ["q1", "q2", "q3", "q4", "q5"]
        analysis = {"category": "billing"}

        priority = kb_gap_detector._calculate_priority(queries, analysis)

        assert 0 <= priority <= 100
        assert isinstance(priority, (int, float))

    @pytest.mark.asyncio
    async def test_analyze_cluster(self, kb_gap_detector, mock_llm):
        """Test cluster analysis"""
        queries = [
            "How do I export data?",
            "Can I export my data?",
            "Data export instructions?"
        ]

        gap = await kb_gap_detector._analyze_cluster(queries)

        assert "topic" in gap
        assert "suggested_article_title" in gap
        assert "category" in gap
        assert "frequency" in gap
        assert "priority_score" in gap

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Database connection pool event loop conflict - needs isolation fix")
    async def test_process_updates_state(self, kb_gap_detector, mock_db_session):
        """Test process method updates state"""
        state = create_initial_state(message="test", context={})
        state["gap_detection_days"] = 30
        state["gap_min_frequency"] = 5

        updated_state = await kb_gap_detector.process(state)

        assert "kb_gaps" in updated_state
        assert "gaps_detected" in updated_state
