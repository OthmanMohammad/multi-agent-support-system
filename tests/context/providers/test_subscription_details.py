"""Tests for SubscriptionDetailsProvider"""

import pytest
from uuid import uuid4

from src.services.infrastructure.context_enrichment.providers.internal.subscription_details import (
    SubscriptionDetailsProvider
)


@pytest.mark.asyncio
async def test_subscription_details_basic(mock_uow, sample_database_subscription):
    """Test basic subscription details fetch"""
    provider = SubscriptionDetailsProvider()

    mock_uow.subscriptions.find_by.return_value = [sample_database_subscription]
    mock_uow.invoices.find_by.return_value = []
    mock_uow.payments.find_by.return_value = []
    mock_uow.credits.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    assert "subscription" in data
    assert "billing" in data
    assert "payment_health" in data
    assert data["subscription"]["plan"] == "enterprise"


@pytest.mark.asyncio
async def test_subscription_details_fallback(mock_uow):
    """Test fallback when no subscription"""
    provider = SubscriptionDetailsProvider()

    mock_uow.subscriptions.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    assert "subscription" in data
    assert data["subscription"]["plan"] == "free"
