"""
Integration tests for infrastructure services
Tests with real database (test DB) but mocked external services
"""
import pytest
from uuid import uuid4

from database.unit_of_work import get_unit_of_work
from services.infrastructure.customer_service import CustomerInfrastructureService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_customer_service_integration():
    """Test customer service with real database"""
    async with get_unit_of_work() as uow:
        service = CustomerInfrastructureService(uow)
        
        # Create customer
        email = f"test_{uuid4().hex[:8]}@example.com"
        result = await service.get_or_create_by_email(email, "Test User")
        
        assert result.is_success
        assert result.value.email == email
        
        # Get by email
        result2 = await service.get_by_email(email)
        assert result2.is_success
        assert result2.value.email == email