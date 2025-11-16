"""Tests for SalesPipelineProvider"""

import pytest
from uuid import uuid4

from src.services.infrastructure.context_enrichment.providers.internal.sales_pipeline import (
    SalesPipelineProvider
)


@pytest.mark.asyncio
async def test_sales_pipeline_basic(mock_uow):
    """Test basic sales pipeline fetch"""
    provider = SalesPipelineProvider()

    mock_uow.deals.find_by.return_value = []
    mock_uow.sales_activities.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    assert "pipeline_value" in data or "open_deals" in data
