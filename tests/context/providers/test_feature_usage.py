"""Tests for FeatureUsageProvider"""

import pytest
from uuid import uuid4

from src.services.infrastructure.context_enrichment.providers.internal.feature_usage import (
    FeatureUsageProvider
)


@pytest.mark.asyncio
async def test_feature_usage_basic(mock_uow):
    """Test basic feature usage fetch"""
    provider = FeatureUsageProvider()

    mock_uow.feature_usage.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    assert "active_features" in data or "feature_adoption" in data
