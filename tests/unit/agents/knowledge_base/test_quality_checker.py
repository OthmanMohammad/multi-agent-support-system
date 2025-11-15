"""
Unit tests for KB Quality Checker agent.
"""

import pytest
from src.agents.essential.knowledge_base.quality_checker import KBQualityChecker
from src.workflow.state import create_initial_state


class TestKBQualityChecker:
    """Test suite for KB Quality Checker agent"""

    @pytest.fixture
    def kb_quality_checker(self):
        """KB Quality Checker instance"""
        return KBQualityChecker()

    def test_initialization(self, kb_quality_checker):
        """Test KB Quality Checker initializes correctly"""
        assert kb_quality_checker.config.name == "kb_quality_checker"
        assert kb_quality_checker.config.model == "claude-3-haiku-20240307"

    def test_check_completeness(self, kb_quality_checker):
        """Test completeness check"""
        content = """
## Overview
Complete overview.

## Steps
1. Step one
2. Step two

## Examples
Example here.

## Notes
Important notes.
        """

        score = kb_quality_checker._check_completeness(content)
        assert score >= 50
        assert score <= 100

    def test_check_examples(self, kb_quality_checker):
        """Test examples check detects code blocks"""
        content = """
Here's an example:

```python
print("Hello")
```

Use `inline_code` for small snippets.

![Screenshot](image.png)
        """

        score = kb_quality_checker._check_examples(content)
        assert score > 0

    def test_check_formatting(self, kb_quality_checker):
        """Test formatting check"""
        content = """
# Main Heading

## Section 1
- List item 1
- List item 2

**Bold text** and *italic text*.
        """

        score = kb_quality_checker._check_formatting(content)
        assert score >= 50

    @pytest.mark.asyncio
    async def test_check_quality(self, kb_quality_checker, mock_llm, sample_kb_article):
        """Test complete quality check"""
        quality_report = await kb_quality_checker.check_quality(sample_kb_article)

        assert "quality_score" in quality_report
        assert 0 <= quality_report["quality_score"] <= 100
        assert "scores" in quality_report
        assert "issues" in quality_report
        assert "strengths" in quality_report

    def test_needs_update_old_article(self, kb_quality_checker):
        """Test needs update for old article"""
        from datetime import datetime, timedelta

        old_date = (datetime.now() - timedelta(days=200)).isoformat()
        article = {"updated_at": old_date}

        assert kb_quality_checker._needs_update(article) is True

    def test_needs_update_recent_article(self, kb_quality_checker):
        """Test needs update for recent article"""
        from datetime import datetime, timedelta

        recent_date = (datetime.now() - timedelta(days=30)).isoformat()
        article = {"updated_at": recent_date}

        assert kb_quality_checker._needs_update(article) is False
