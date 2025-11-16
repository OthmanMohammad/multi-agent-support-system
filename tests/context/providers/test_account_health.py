"""Tests for AccountHealthProvider"""

import pytest
from uuid import uuid4

from src.services.infrastructure.context_enrichment.providers.internal.account_health import (
    AccountHealthProvider
)


@pytest.mark.asyncio
async def test_account_health_basic():
    """Test basic account health fetch"""
    provider = AccountHealthProvider()

    data = await provider.fetch(customer_id=str(uuid4()))

    assert "red_flags" in data
    assert "yellow_flags" in data
    assert "green_flags" in data
