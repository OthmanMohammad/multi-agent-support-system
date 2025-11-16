"""Tests for SupportHistoryProvider"""

import pytest
from uuid import uuid4

from src.services.infrastructure.context_enrichment.providers.internal.support_history import (
    SupportHistoryProvider
)


@pytest.mark.asyncio
async def test_support_history_basic(mock_uow):
    """Test basic support history fetch"""
    provider = SupportHistoryProvider()

    mock_uow.conversations.find_by.return_value = []
    mock_uow.messages.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    assert "total_conversations" in data
    assert "open_tickets" in data
