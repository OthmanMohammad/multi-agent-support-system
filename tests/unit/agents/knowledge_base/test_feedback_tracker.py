"""
Unit tests for KB Feedback Tracker agent.
"""

import pytest
from datetime import datetime
from src.agents.essential.knowledge_base.feedback_tracker import KBFeedbackTracker
from src.workflow.state import create_initial_state
import uuid


class TestKBFeedbackTracker:
    """Test suite for KB Feedback Tracker agent"""

    @pytest.fixture
    def kb_feedback_tracker(self, mock_db_session):
        """KB Feedback Tracker instance"""
        return KBFeedbackTracker()

    def test_initialization(self, kb_feedback_tracker):
        """Test KB Feedback Tracker initializes correctly"""
        assert kb_feedback_tracker.config.name == "kb_feedback_tracker"
        assert kb_feedback_tracker.config.type.value == "utility"

    @pytest.mark.asyncio
    async def test_track_view_event(self, kb_feedback_tracker, mock_db_session):
        """Test tracking article view"""
        article_id = str(uuid.uuid4())

        result = await kb_feedback_tracker.track_event(
            article_id=article_id,
            event_type="viewed"
        )

        assert "tracked" in result
        assert "article_stats" in result

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Database connection pool event loop conflict - needs isolation fix")
    async def test_track_helpful_vote(self, kb_feedback_tracker, mock_db_session):
        """Test tracking helpful vote"""
        article_id = str(uuid.uuid4())

        result = await kb_feedback_tracker.track_event(
            article_id=article_id,
            event_type="helpful"
        )

        assert "tracked" in result

    @pytest.mark.asyncio
    async def test_track_resolution_metrics(self, kb_feedback_tracker, mock_db_session):
        """Test tracking resolution time and CSAT"""
        article_id = str(uuid.uuid4())

        result = await kb_feedback_tracker.track_event(
            article_id=article_id,
            event_type="resolved_with",
            metadata={
                "resolution_time_seconds": 120,
                "csat_score": 5
            }
        )

        assert "tracked" in result

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Database connection pool event loop conflict - needs isolation fix")
    async def test_process_updates_state(self, kb_feedback_tracker, mock_db_session):
        """Test process method updates state"""
        state = create_initial_state(message="test", context={})
        state["article_id"] = str(uuid.uuid4())
        state["event_type"] = "viewed"

        updated_state = await kb_feedback_tracker.process(state)

        assert "current_agent" in updated_state
