"""Tests for SecurityContextProvider"""

import pytest
from uuid import uuid4

from src.services.infrastructure.context_enrichment.providers.internal.security_context import (
    SecurityContextProvider
)


@pytest.mark.asyncio
async def test_security_context_basic(mock_uow):
    """Test basic security context fetch"""
    provider = SecurityContextProvider()

    mock_uow.audit_logs.find_by.return_value = []

    data = await provider._fetch_with_session(
        customer_id=uuid4(),
        session=mock_uow.session
    )

    assert "failed_logins" in data or "security_posture" in data
