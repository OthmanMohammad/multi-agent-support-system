"""
Integration tests for KB quality assurance flow (Quality Checker → Updater).
"""

import pytest
from datetime import datetime, timedelta
from src.agents.essential.knowledge_base import KBQualityChecker, KBUpdater
from src.workflow.state import create_initial_state
from src.database.models import KBArticle


# Skip all tests - JSONB columns in models are not supported by SQLite
pytestmark = pytest.mark.skip(
    reason="KB integration tests require PostgreSQL (JSONB columns not supported by SQLite)"
)


class TestKBQualityFlow:
    """Test end-to-end KB quality assurance flow"""

    @pytest.mark.asyncio
    async def test_quality_check_and_update_detection(self, test_db_session, sample_kb_articles):
        """Test flow: quality check → identify updates needed"""
        quality_checker = KBQualityChecker()
        updater = KBUpdater()

        # Get an article to check
        article = sample_kb_articles[2]  # The older, lower quality one

        # Step 1: Run quality check
        state = create_initial_state(message="test", context={})
        state["article_to_check"] = {
            "article_id": article.article_id,
            "title": article.title,
            "content": article.content,
            "updated_at": article.updated_at.isoformat()
        }

        state = await quality_checker.process(state)

        assert "quality_check_result" in state
        quality_result = state["quality_check_result"]

        # Step 2: Check if update needed based on quality
        article_dict = {
            "article_id": article.article_id,
            "title": article.title,
            "content": article.content,
            "quality_score": quality_result.get("overall_score", article.quality_score),
            "helpfulness_ratio": article.helpfulness_ratio,
            "updated_at": article.updated_at.isoformat()
        }

        update_check = await updater.check_needs_update(article_dict)

        assert "needs_update" in update_check
        assert isinstance(update_check["needs_update"], bool)

        if update_check["needs_update"]:
            assert "reasons" in update_check
            assert len(update_check["reasons"]) > 0
            assert "update_priority" in update_check

    @pytest.mark.asyncio
    async def test_identify_articles_needing_updates(self, test_db_session, sample_kb_articles):
        """Test identifying all articles needing updates"""
        updater = KBUpdater()

        state = create_initial_state(message="test", context={})
        state["update_check_days"] = 365  # Check articles from last year

        state = await updater.process(state)

        assert "articles_needing_update" in state
        articles = state["articles_needing_update"]

        # Should identify some articles needing updates
        assert isinstance(articles, list)

        # Each article should have update metadata
        for article in articles:
            assert "article_id" in article
            assert "update_priority" in article
            assert "reasons" in article

    @pytest.mark.asyncio
    async def test_quality_score_calculation(self, test_db_session):
        """Test quality scoring for different article types"""
        quality_checker = KBQualityChecker()

        # High quality article
        good_article = {
            "article_id": "kb_good",
            "title": "Comprehensive Guide to API Authentication",
            "content": """
# API Authentication

## Overview
This guide covers authentication methods.

## Prerequisites
- Active account
- API access enabled

## Step-by-Step Instructions
1. Navigate to Settings
2. Generate API key
3. Use in requests

## Example
```python
headers = {'Authorization': 'Bearer YOUR_KEY'}
```

## Troubleshooting
If you encounter errors, check:
- Key is valid
- Permissions are correct
            """,
            "updated_at": datetime.now().isoformat()
        }

        state = create_initial_state(message="test", context={})
        state["article_to_check"] = good_article

        state = await quality_checker.process(state)

        good_result = state["quality_check_result"]
        assert good_result["overall_score"] >= 70  # Should score well

        # Poor quality article
        poor_article = {
            "article_id": "kb_poor",
            "title": "Login",
            "content": "Just login to your account.",
            "updated_at": datetime.now().isoformat()
        }

        state2 = create_initial_state(message="test", context={})
        state2["article_to_check"] = poor_article

        state2 = await quality_checker.process(state2)

        poor_result = state2["quality_check_result"]
        assert poor_result["overall_score"] < good_result["overall_score"]

    @pytest.mark.asyncio
    async def test_detect_missing_elements(self, test_db_session):
        """Test detection of missing article elements"""
        quality_checker = KBQualityChecker()

        # Article missing examples
        article = {
            "article_id": "kb_no_examples",
            "title": "How to Use API",
            "content": "The API is easy to use. Just send requests.",
            "updated_at": datetime.now().isoformat()
        }

        state = create_initial_state(message="test", context={})
        state["article_to_check"] = article

        state = await quality_checker.process(state)

        result = state["quality_check_result"]
        assert "issues" in result

        # Should flag missing examples
        issues = [issue["type"] for issue in result["issues"]]
        assert "missing_examples" in issues or "incomplete" in issues

    @pytest.mark.asyncio
    async def test_detect_deprecated_content(self, test_db_session):
        """Test detection of deprecated features in content"""
        updater = KBUpdater()

        # Article with deprecated references
        old_article = {
            "article_id": "kb_deprecated",
            "title": "Using Dashboard v1",
            "content": "Navigate to Dashboard v1 and click the old Settings panel.",
            "quality_score": 80,
            "helpfulness_ratio": 0.8,
            "updated_at": (datetime.now() - timedelta(days=100)).isoformat()
        }

        update_check = await updater.check_needs_update(old_article)

        assert update_check["needs_update"] is True

        # Should identify deprecated features
        reasons = [r["type"] for r in update_check["reasons"]]
        assert "deprecated_feature" in reasons or "age" in reasons

    @pytest.mark.asyncio
    async def test_prioritize_updates_by_severity(self, test_db_session, sample_kb_articles):
        """Test that updates are prioritized correctly"""
        updater = KBUpdater()

        # Create articles with different severity levels
        critical_article = {
            "article_id": "kb_critical",
            "title": "Critical Article",
            "content": "Old content with Dashboard v1 references",
            "quality_score": 50,
            "helpfulness_ratio": 0.3,
            "updated_at": (datetime.now() - timedelta(days=400)).isoformat()
        }

        low_priority_article = {
            "article_id": "kb_low",
            "title": "Recent Good Article",
            "content": "Recent content that's helpful",
            "quality_score": 85,
            "helpfulness_ratio": 0.9,
            "updated_at": (datetime.now() - timedelta(days=10)).isoformat()
        }

        critical_check = await updater.check_needs_update(critical_article)
        low_check = await updater.check_needs_update(low_priority_article)

        # Critical should have higher priority
        if critical_check["needs_update"] and low_check["needs_update"]:
            priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            critical_priority = priority_map.get(critical_check["update_priority"], 0)
            low_priority = priority_map.get(low_check["update_priority"], 0)
            assert critical_priority > low_priority

    @pytest.mark.asyncio
    async def test_quality_flow_with_feedback_data(self, test_db_session, sample_kb_articles):
        """Test quality assessment considering user feedback"""
        quality_checker = KBQualityChecker()
        updater = KBUpdater()

        # Article with poor feedback
        article = sample_kb_articles[2]  # Lower helpfulness ratio

        # Quality check
        state = create_initial_state(message="test", context={})
        state["article_to_check"] = {
            "article_id": article.article_id,
            "title": article.title,
            "content": article.content,
            "helpfulness_ratio": article.helpfulness_ratio,
            "quality_score": article.quality_score,
            "updated_at": article.updated_at.isoformat()
        }

        state = await quality_checker.process(state)

        # Update check considering feedback
        article_dict = {
            "article_id": article.article_id,
            "title": article.title,
            "content": article.content,
            "quality_score": article.quality_score,
            "helpfulness_ratio": article.helpfulness_ratio,
            "updated_at": article.updated_at.isoformat()
        }

        update_check = await updater.check_needs_update(article_dict)

        # Low helpfulness should trigger update recommendation
        if article.helpfulness_ratio < 0.7:
            assert update_check["needs_update"] is True
            reasons = [r["type"] for r in update_check["reasons"]]
            assert "low_helpfulness" in reasons

    @pytest.mark.asyncio
    async def test_generate_improvement_suggestions(self, test_db_session):
        """Test generation of specific improvement suggestions"""
        updater = KBUpdater()

        article = {
            "article_id": "kb_needs_improvement",
            "title": "Brief Article",
            "content": "Short content without examples or details.",
            "quality_score": 55,
            "helpfulness_ratio": 0.5,
            "updated_at": (datetime.now() - timedelta(days=250)).isoformat()
        }

        update_check = await updater.check_needs_update(article)

        assert "suggestions" in update_check

        if update_check["needs_update"]:
            suggestions = update_check["suggestions"]
            assert len(suggestions) > 0
            # Suggestions should be actionable strings
            assert all(isinstance(s, str) for s in suggestions)

    @pytest.mark.asyncio
    async def test_estimate_update_effort(self, test_db_session):
        """Test effort estimation for updates"""
        updater = KBUpdater()

        # Article needing minor updates
        minor_update = {
            "article_id": "kb_minor",
            "title": "Good Article",
            "content": "Well-written content with examples",
            "quality_score": 75,
            "helpfulness_ratio": 0.75,
            "updated_at": (datetime.now() - timedelta(days=200)).isoformat()
        }

        # Article needing major updates
        major_update = {
            "article_id": "kb_major",
            "title": "Poor Article",
            "content": "Use Dashboard v1 for old features",
            "quality_score": 45,
            "helpfulness_ratio": 0.35,
            "updated_at": (datetime.now() - timedelta(days=500)).isoformat()
        }

        minor_check = await updater.check_needs_update(minor_update)
        major_check = await updater.check_needs_update(major_update)

        # Both should have effort estimates
        if minor_check["needs_update"]:
            assert "estimated_effort" in minor_check

        if major_check["needs_update"]:
            assert "estimated_effort" in major_check

    @pytest.mark.asyncio
    async def test_batch_quality_assessment(self, test_db_session, sample_kb_articles):
        """Test assessing quality of multiple articles"""
        quality_checker = KBQualityChecker()

        results = []

        for article in sample_kb_articles[:3]:
            state = create_initial_state(message="test", context={})
            state["article_to_check"] = {
                "article_id": article.article_id,
                "title": article.title,
                "content": article.content,
                "updated_at": article.updated_at.isoformat()
            }

            state = await quality_checker.process(state)

            results.append({
                "article_id": article.article_id,
                "quality_score": state["quality_check_result"]["overall_score"]
            })

        # Should have results for all articles
        assert len(results) == 3

        # Scores should be reasonable (0-100)
        for result in results:
            assert 0 <= result["quality_score"] <= 100
