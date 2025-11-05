"""
Unit tests for BaseService

Tests cover:
- Service initialization
- Async operation execution
- Sync operation execution
- Exception handling
- Validation helpers
- Email and UUID validation
- Logging
"""

import pytest
import asyncio
from uuid import uuid4

from services.base import BaseService, handle_exceptions
from core.result import Result
from core.errors import ValidationError, InternalError


class TestServiceForTesting(BaseService):
    """Concrete service class for testing"""
    
    def sync_success(self) -> Result[str]:
        """Sync operation that succeeds"""
        return Result.ok("success")
    
    async def async_success(self) -> Result[str]:
        """Async operation that succeeds"""
        await asyncio.sleep(0.001)
        return Result.ok("async_success")
    
    def sync_failure(self) -> Result[str]:
        """Sync operation that returns failure"""
        return Result.fail(ValidationError(
            message="Test failure",
            field="test"
        ))
    
    @handle_exceptions("test_operation")
    def sync_with_exception(self) -> Result[str]:
        """Sync operation that raises exception"""
        raise ValueError("Test exception")
    
    @handle_exceptions("test_async_operation")
    async def async_with_exception(self) -> Result[str]:
        """Async operation that raises exception"""
        await asyncio.sleep(0.001)
        raise ValueError("Test async exception")


class TestBaseServiceInitialization:
    """Test suite for BaseService initialization"""
    
    def test_service_initialization(self):
        """Test service initializes with logger"""
        service = TestServiceForTesting()
        
        assert service.logger is not None
        assert service.logger.name == "TestServiceForTesting"
    
    def test_service_repr(self):
        """Test service string representation"""
        service = TestServiceForTesting()
        
        repr_str = repr(service)
        
        assert "TestServiceForTesting" in repr_str


class TestAsyncOperations:
    """Test suite for async operations"""
    
    @pytest.mark.asyncio
    async def test_async_success_operation(self):
        """Test successful async operation"""
        service = TestServiceForTesting()
        
        result = await service.async_success()
        
        assert result.is_success
        assert result.value == "async_success"
    
    @pytest.mark.asyncio
    async def test_async_exception_handling(self):
        """Test async operation with exception handling"""
        service = TestServiceForTesting()
        
        result = await service.async_with_exception()
        
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"
        assert "test_async_operation" in result.error.details["operation"]
    
    @pytest.mark.asyncio
    async def test_execute_async_success(self):
        """Test execute_async with successful operation"""
        service = TestServiceForTesting()
        
        async def async_op():
            await asyncio.sleep(0.001)
            return "result"
        
        result = await service.execute_async(async_op, "test_op")
        
        assert result.is_success
        assert result.value == "result"
    
    @pytest.mark.asyncio
    async def test_execute_async_failure(self):
        """Test execute_async with failing operation"""
        service = TestServiceForTesting()
        
        async def async_op():
            await asyncio.sleep(0.001)
            raise ValueError("Operation failed")
        
        result = await service.execute_async(async_op, "test_op")
        
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"


class TestSyncOperations:
    """Test suite for sync operations"""
    
    def test_sync_success_operation(self):
        """Test successful sync operation"""
        service = TestServiceForTesting()
        
        result = service.sync_success()
        
        assert result.is_success
        assert result.value == "success"
    
    def test_sync_failure_operation(self):
        """Test sync operation returning failure"""
        service = TestServiceForTesting()
        
        result = service.sync_failure()
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
    
    def test_sync_exception_handling(self):
        """Test sync operation with exception handling"""
        service = TestServiceForTesting()
        
        result = service.sync_with_exception()
        
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"
        assert "test_operation" in result.error.details["operation"]
    
    def test_execute_success(self):
        """Test execute with successful operation"""
        service = TestServiceForTesting()
        
        def sync_op():
            return "result"
        
        result = service.execute(sync_op, "test_op")
        
        assert result.is_success
        assert result.value == "result"
    
    def test_execute_failure(self):
        """Test execute with failing operation"""
        service = TestServiceForTesting()
        
        def sync_op():
            raise ValueError("Operation failed")
        
        result = service.execute(sync_op, "test_op")
        
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"


class TestEmailValidation:
    """Test suite for email validation"""
    
    @pytest.fixture
    def service(self):
        return TestServiceForTesting()
    
    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", True),
        ("test.user@domain.co.uk", True),
        ("name+tag@example.org", True),
        ("invalid", False),
        ("@example.com", False),
        ("user@", False),
        ("user", False),
        ("user@domain", False),
        ("", False),
        (None, False),
    ])
    def test_email_validation_cases(self, service, email, expected):
        """Parametrized test for email validation"""
        result = service.is_valid_email(email)
        
        assert result == expected


class TestUUIDValidation:
    """Test suite for UUID validation"""
    
    @pytest.fixture
    def service(self):
        return TestServiceForTesting()
    
    def test_valid_uuid(self, service):
        """Test valid UUID string"""
        valid_uuid = str(uuid4())
        
        assert service.is_valid_uuid(valid_uuid) is True
    
    def test_invalid_uuid(self, service):
        """Test invalid UUID string"""
        assert service.is_valid_uuid("not-a-uuid") is False
        assert service.is_valid_uuid("12345") is False
        assert service.is_valid_uuid("") is False
    
    def test_none_uuid(self, service):
        """Test None is invalid UUID"""
        assert service.is_valid_uuid(None) is False


class TestRequireValidation:
    """Test suite for require_* validation helpers"""
    
    @pytest.fixture
    def service(self):
        return TestServiceForTesting()
    
    def test_require_not_none_with_value(self, service):
        """Test require_not_none with valid value"""
        result = service.require_not_none("value", "field_name")
        
        assert result.is_success
    
    def test_require_not_none_with_none(self, service):
        """Test require_not_none with None"""
        result = service.require_not_none(None, "field_name")
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "required" in result.error.message.lower()
        assert result.error.details["field"] == "field_name"
    
    def test_require_not_empty_with_value(self, service):
        """Test require_not_empty with non-empty string"""
        result = service.require_not_empty("value", "field_name")
        
        assert result.is_success
    
    def test_require_not_empty_with_empty(self, service):
        """Test require_not_empty with empty string"""
        result = service.require_not_empty("", "field_name")
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "empty" in result.error.message.lower()
    
    def test_require_not_empty_with_whitespace(self, service):
        """Test require_not_empty with whitespace-only string"""
        result = service.require_not_empty("   ", "field_name")
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"


class TestLogOperation:
    """Test suite for log_operation method"""
    
    def test_log_operation_success(self, caplog):
        """Test logging successful operation"""
        service = TestServiceForTesting()
        
        service.log_operation("test_op", success=True, user_id="123")
        
        assert "test_op" in caplog.text
        assert "succeeded" in caplog.text
    
    def test_log_operation_failure(self, caplog):
        """Test logging failed operation"""
        service = TestServiceForTesting()
        
        service.log_operation("test_op", success=False, error="Test error")
        
        assert "test_op" in caplog.text
        assert "failed" in caplog.text


class TestHandleExceptionsDecorator:
    """Test suite for handle_exceptions decorator"""
    
    def test_decorator_catches_sync_exception(self):
        """Test decorator catches sync exceptions"""
        service = TestServiceForTesting()
        
        result = service.sync_with_exception()
        
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"
    
    @pytest.mark.asyncio
    async def test_decorator_catches_async_exception(self):
        """Test decorator catches async exceptions"""
        service = TestServiceForTesting()
        
        result = await service.async_with_exception()
        
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"
    
    def test_decorator_preserves_function_name(self):
        """Test decorator preserves original function name"""
        service = TestServiceForTesting()
        
        assert service.sync_with_exception.__name__ == "sync_with_exception"
    
    def test_decorator_includes_operation_name(self):
        """Test decorator includes operation name in error"""
        service = TestServiceForTesting()
        
        result = service.sync_with_exception()
        
        assert "test_operation" in result.error.details["operation"]