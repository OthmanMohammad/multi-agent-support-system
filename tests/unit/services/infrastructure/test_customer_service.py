"""
Unit tests for CustomerInfrastructureService
"""
import pytest
from uuid import uuid4
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

from src.services.infrastructure.customer_service import CustomerInfrastructureService
from src.core.result import Result
from src.core.errors import NotFoundError, InternalError


@pytest.fixture
def mock_uow():
    """Create mock Unit of Work"""
    uow = MagicMock()
    uow.customers = AsyncMock()
    uow.conversations = AsyncMock()
    uow.current_user_id = None
    return uow


@pytest.fixture
def service(mock_uow):
    """Create service with mock UoW"""
    return CustomerInfrastructureService(mock_uow)


@pytest.mark.asyncio
class TestCustomerInfrastructureService:
    """Test CustomerInfrastructureService"""
    
    async def test_get_by_email_success(self, service, mock_uow):
        """Test getting customer by email - found"""
        # Arrange
        customer = MagicMock()
        customer.email = "test@example.com"
        customer.id = uuid4()
        mock_uow.customers.get_by_email.return_value = customer
        
        # Act
        result = await service.get_by_email("test@example.com")
        
        # Assert
        assert result.is_success
        assert result.value == customer
        mock_uow.customers.get_by_email.assert_called_once_with("test@example.com")
    
    async def test_get_by_email_not_found(self, service, mock_uow):
        """Test getting customer by email - not found"""
        # Arrange
        mock_uow.customers.get_by_email.return_value = None
        
        # Act
        result = await service.get_by_email("notfound@example.com")
        
        # Assert
        assert result.is_success
        assert result.value is None
    
    async def test_get_by_email_error(self, service, mock_uow):
        """Test getting customer by email - database error"""
        # Arrange
        mock_uow.customers.get_by_email.side_effect = Exception("Database error")
        
        # Act
        result = await service.get_by_email("test@example.com")
        
        # Assert
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"
        assert "Failed to fetch customer by email" in result.error.message
    
    async def test_get_by_id_success(self, service, mock_uow):
        """Test getting customer by ID - found"""
        # Arrange
        customer_id = uuid4()
        customer = MagicMock()
        customer.id = customer_id
        mock_uow.customers.get_by_id.return_value = customer
        
        # Act
        result = await service.get_by_id(customer_id)
        
        # Assert
        assert result.is_success
        assert result.value == customer
    
    async def test_get_by_id_not_found(self, service, mock_uow):
        """Test getting customer by ID - not found"""
        # Arrange
        customer_id = uuid4()
        mock_uow.customers.get_by_id.return_value = None
        
        # Act
        result = await service.get_by_id(customer_id)
        
        # Assert
        assert result.is_failure
        assert result.error.code == "NOT_FOUND"
        assert "Customer not found" in result.error.message
    
    async def test_upgrade_plan_success(self, service, mock_uow):
        """Test upgrading customer plan"""
        # Arrange
        customer_id = uuid4()
        updated_customer = MagicMock()
        updated_customer.plan = "premium"
        mock_uow.customers.update.return_value = updated_customer
        
        # Act
        result = await service.upgrade_plan(customer_id, "premium")
        
        # Assert
        assert result.is_success
        assert result.value.plan == "premium"
        mock_uow.customers.update.assert_called_once()
    
    async def test_get_conversation_count_for_date(self, service, mock_uow):
        """Test getting conversation count for date"""
        # Arrange
        customer_id = uuid4()
        mock_uow.conversations.count.return_value = 5
        
        # Act
        result = await service.get_conversation_count_for_date(
            customer_id, 
            datetime.now(UTC)
        )
        
        # Assert
        assert result.is_success
        assert result.value == 5
    
    async def test_block_customer(self, service, mock_uow):
        """Test blocking customer"""
        # Arrange
        customer_id = uuid4()
        customer = MagicMock()
        customer.extra_metadata = {}
        mock_uow.customers.get_by_id.return_value = customer
        mock_uow.customers.update.return_value = customer
        
        # Act
        result = await service.block_customer(customer_id, "Fraud")
        
        # Assert
        assert result.is_success
        mock_uow.customers.update.assert_called_once()