"""
Unit tests for KB Updater agent.
"""

import pytest
from datetime import datetime, timedelta
from src.agents.essential.knowledge_base.updater import KBUpdater
from src.workflow.state import create_initial_state


class TestKBUpdater:
    """Test suite for KB Updater agent"""

    @pytest.fixture
    def kb_updater(self):
        """KB Updater instance"""
        return KBUpdater()

    def test_initialization(self, kb_updater):
        """Test KB Updater initializes correctly"""
        assert kb_updater.config.name == "kb_updater"
        assert kb_updater.AGE_THRESHOLD_DAYS == 180

    def test_check_age_old_article(self, kb_updater):
        """Test age check for old article"""
        old_date = (datetime.now() - timedelta(days=400)).isoformat()
        article = {"updated_at": old_date}

        age_check = kb_updater._check_age(article)

        assert age_check is not None
        assert age_check["type"] == "age"
        assert age_check["severity"] in ["medium", "high"]

    def test_check_age_recent_article(self, kb_updater):
        """Test age check for recent article"""
        recent_date = (datetime.now() - timedelta(days=30)).isoformat()
        article = {"updated_at": recent_date}

        age_check = kb_updater._check_age(article)

        assert age_check is None

    def test_check_quality_low_score(self, kb_updater):
        """Test quality check for low quality article"""
        article = {"quality_score": 60}

        quality_check = kb_updater._check_quality(article)

        assert quality_check is not None
        assert quality_check["type"] == "low_quality"

    def test_check_helpfulness_low_ratio(self, kb_updater):
        """Test helpfulness check"""
        article = {"helpfulness_ratio": 0.35}

        helpfulness_check = kb_updater._check_helpfulness(article)

        assert helpfulness_check is not None
        assert helpfulness_check["type"] == "low_helpfulness"

    def test_check_deprecated_features(self, kb_updater):
        """Test deprecated feature detection"""
        article = {
            "content": "Navigate to Dashboard v1 and click Settings..."
        }

        deprecated_checks = kb_updater._check_deprecated_features(article)

        assert isinstance(deprecated_checks, list)

    def test_calculate_priority_high_severity(self, kb_updater):
        """Test priority calculation with high severity issues"""
        reasons = [
            {"severity": "high"},
            {"severity": "high"}
        ]

        priority = kb_updater._calculate_priority(reasons)

        assert priority == "high"

    def test_generate_suggestions(self, kb_updater):
        """Test suggestion generation"""
        reasons = [
            {"type": "age", "detail": "18 months old"},
            {"type": "deprecated_feature", "detail": "Dashboard v1"}
        ]

        suggestions = kb_updater._generate_suggestions(reasons, {})

        assert len(suggestions) > 0
        assert any("update" in s.lower() for s in suggestions)

    def test_estimate_effort(self, kb_updater):
        """Test effort estimation"""
        high_effort_reasons = [
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"}
        ]

        effort = kb_updater._estimate_effort(high_effort_reasons)

        assert "hour" in effort.lower()

    @pytest.mark.asyncio
    async def test_check_needs_update_multiple_issues(self, kb_updater):
        """Test full check with multiple issues"""
        old_date = (datetime.now() - timedelta(days=400)).isoformat()
        article = {
            "article_id": "kb_123",
            "title": "Old Article",
            "content": "Use Dashboard v1...",
            "updated_at": old_date,
            "quality_score": 60,
            "helpfulness_ratio": 0.4
        }

        result = await kb_updater.check_needs_update(article)

        assert result["needs_update"] is True
        assert len(result["reasons"]) >= 1
        assert result["update_priority"] in ["low", "medium", "high", "critical"]
