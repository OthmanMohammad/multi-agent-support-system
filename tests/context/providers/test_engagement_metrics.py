"""Tests for EngagementMetricsProvider"""

import pytest
from uuid import uuid4

from src.services.infrastructure.context_enrichment.providers.internal.engagement_metrics import (
    EngagementMetricsProvider
)


@pytest.mark.asyncio
async def test_engagement_metrics_basic(mock_uow):
    """Test basic engagement metrics fetch"""
    provider = EngagementMetricsProvider()

    mock_uow.usage_events.find_by.return_value = []
    mock_uow.feature_usage.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    assert "login_frequency" in data
    assert "last_login" in data
