"""
Shared fixtures for technical support agent tests.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta


@pytest.fixture
def mock_kb_service():
    """Mock knowledge base service"""
    mock_service = AsyncMock()
    mock_service.search.return_value = [
        {
            "doc_id": "tech_kb_123",
            "title": "How to Fix Crashes",
            "content": "Clear cache and cookies to fix crashes",
            "category": "technical",
            "tags": ["crash", "troubleshooting"],
            "similarity_score": 0.92
        },
        {
            "doc_id": "tech_kb_456",
            "title": "Sync Troubleshooting Guide",
            "content": "Enable sync in settings",
            "category": "technical",
            "tags": ["sync", "data"],
            "similarity_score": 0.85
        }
    ]
    return mock_service


@pytest.fixture
def mock_llm_call(monkeypatch):
    """Mock LLM calls for all agents"""
    async def mock_call_llm(self, system_prompt, user_message, max_tokens=1024, temperature=None):
        return "Mocked LLM response with troubleshooting steps."

    monkeypatch.setattr(
        'src.agents.base.base_agent.BaseAgent.call_llm',
        mock_call_llm
    )


@pytest.fixture
def sample_customer_context():
    """Sample customer context for testing"""
    return {
        "customer_id": "cust_test_123",
        "email": "test@example.com",
        "browser": "Chrome",
        "browser_version": 120,
        "data_size_mb": 50,
        "active_projects": 5,
        "plan": "premium",
        "account_age_days": 180
    }


@pytest.fixture
def sample_crash_data():
    """Sample crash data for testing"""
    return {
        "error_message": "TypeError: Cannot read property 'value' of null",
        "browser": "Chrome",
        "browser_version": "120",
        "reproduction_steps": "Click on dashboard, then click on project",
        "frequency": "every_time"
    }


@pytest.fixture
def sample_sync_status():
    """Sample sync status for testing"""
    return {
        "last_sync": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "pending_items": 0,
        "conflicts": 0,
        "sync_enabled": True,
        "sync_speed": "normal",
        "connection_status": "connected"
    }
