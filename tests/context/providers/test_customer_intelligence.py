"""Tests for CustomerIntelligenceProvider"""

import pytest
from uuid import uuid4
from datetime import datetime

from src.services.infrastructure.context_enrichment.providers.internal.customer_intelligence import (
    CustomerIntelligenceProvider
)


@pytest.mark.asyncio
async def test_customer_intelligence_basic(mock_uow, sample_database_customer, sample_database_subscription):
    """Test basic customer intelligence fetch"""
    provider = CustomerIntelligenceProvider()

    # Setup mocks
    mock_uow.customers.get_by_id.return_value = sample_database_customer
    mock_uow.subscriptions.find_by.return_value = [sample_database_subscription]
    mock_uow.customer_segments.find_by.return_value = []
    mock_uow.customer_health_events.find_by.return_value = []
    mock_uow.customer_notes.find_by.return_value = []
    mock_uow.customer_contacts.find_by.return_value = []

    # Fetch
    data = await provider._fetch_with_session(
        customer_id=sample_database_customer.id,
        session=mock_uow.session
    )

    # Assertions
    assert "company_name" in data
    assert "plan" in data
    assert "mrr" in data
    assert "health_score" in data


@pytest.mark.asyncio
async def test_customer_intelligence_with_segments(mock_uow, sample_database_customer):
    """Test customer intelligence with segments"""
    from unittest.mock import MagicMock

    provider = CustomerIntelligenceProvider()

    # Create mock segments
    segment1 = MagicMock()
    segment1.segment_name = "enterprise"
    segment2 = MagicMock()
    segment2.segment_name = "high_value"

    mock_uow.customers.get_by_id.return_value = sample_database_customer
    mock_uow.subscriptions.find_by.return_value = []
    mock_uow.customer_segments.find_by.return_value = [segment1, segment2]
    mock_uow.customer_health_events.find_by.return_value = []
    mock_uow.customer_notes.find_by.return_value = []
    mock_uow.customer_contacts.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=sample_database_customer.id,
        session=mock_uow.session
    )

    assert "segments" in data
    assert "enterprise" in data["segments"]
    assert "high_value" in data["segments"]


@pytest.mark.asyncio
async def test_customer_intelligence_fallback(mock_uow):
    """Test fallback when customer not found"""
    provider = CustomerIntelligenceProvider()

    # Customer not found
    mock_uow.customers.get_by_id.return_value = None

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    # Should return fallback data
    assert "company_name" in data
    assert "plan" in data
    assert data["plan"] == "free"
