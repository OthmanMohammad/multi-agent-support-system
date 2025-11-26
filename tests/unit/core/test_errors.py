"""
Unit tests for error types

Tests cover:
- All error factory functions
- Error serialization
- Error code constants
- Field validation
"""

import pytest
from uuid import uuid4

from src.core.errors import (
    ValidationError,
    BusinessRuleError,
    NotFoundError,
    ConflictError,
    AuthorizationError,
    RateLimitError,
    InternalError,
    ExternalServiceError,
    ErrorCodes,
)
from src.core.result import Error


class TestValidationError:
    """Test ValidationError factory function"""
    
    def test_with_all_parameters(self):
        """Test ValidationError with all parameters"""
        error = ValidationError(
            message="Email is required",
            field="email",
            value="test@test.com",
            constraint="required"
        )
        
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Email is required"
        assert error.details["field"] == "email"
        assert error.details["value"] == "test@test.com"
        assert error.details["constraint"] == "required"
    
    def test_with_minimal_parameters(self):
        """Test ValidationError with only message"""
        error = ValidationError(message="Invalid input")
        
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"
        assert not error.details or error.details == {}  # Accept None or empty dict
    
    def test_truncates_long_values(self):
        """Test that long values are truncated"""
        long_value = "x" * 200
        error = ValidationError(
            message="Too long",
            field="text",
            value=long_value
        )
        
        assert len(error.details["value"]) == 100
    
    def test_with_extra_details(self):
        """Test ValidationError with extra details"""
        error = ValidationError(
            message="Invalid",
            field="email",
            custom_field="custom_value"
        )
        
        assert error.details["field"] == "email"
        assert error.details["custom_field"] == "custom_value"


class TestBusinessRuleError:
    """Test BusinessRuleError factory function"""
    
    def test_with_rule_and_entity(self):
        """Test BusinessRuleError with rule and entity"""
        error = BusinessRuleError(
            message="Cannot resolve conversation",
            rule="ConversationResolutionRule",
            entity="Conversation"
        )
        
        assert error.code == "BUSINESS_RULE_VIOLATION"
        assert error.message == "Cannot resolve conversation"
        assert error.details["rule"] == "ConversationResolutionRule"
        assert error.details["entity"] == "Conversation"
    
    def test_with_only_message(self):
        """Test BusinessRuleError with only message"""
        error = BusinessRuleError(message="Rule violated")
        
        assert error.code == "BUSINESS_RULE_VIOLATION"
        assert not error.details or error.details == {}  # Accept None or empty dict
    
    def test_with_extra_details(self):
        """Test BusinessRuleError with extra details"""
        error = BusinessRuleError(
            message="Rule failed",
            rule="TestRule",
            expected_state="active",
            actual_state="inactive"
        )
        
        assert error.details["rule"] == "TestRule"
        assert error.details["expected_state"] == "active"
        assert error.details["actual_state"] == "inactive"


class TestNotFoundError:
    """Test NotFoundError factory function"""
    
    def test_with_identifier(self):
        """Test NotFoundError with resource and identifier"""
        error = NotFoundError(
            resource="Customer",
            identifier="user123"
        )
        
        assert error.code == "NOT_FOUND"
        assert error.message == "Customer not found: user123"
        assert error.details["resource"] == "Customer"
        assert error.details["identifier"] == "user123"
    
    def test_without_identifier(self):
        """Test NotFoundError without identifier"""
        error = NotFoundError(resource="Customer")
        
        assert error.message == "Customer not found"
        assert "identifier" not in error.details
    
    def test_with_search_criteria(self):
        """Test NotFoundError with search criteria"""
        error = NotFoundError(
            resource="Conversation",
            search_criteria={"customer_id": "123", "status": "active"}
        )
        
        assert error.details["search_criteria"] == {
            "customer_id": "123",
            "status": "active"
        }
    
    def test_with_both_identifier_and_criteria(self):
        """Test NotFoundError with both identifier and criteria"""
        error = NotFoundError(
            resource="User",
            identifier="user123",
            search_criteria={"status": "active"}
        )
        
        assert error.details["identifier"] == "user123"
        assert error.details["search_criteria"] == {"status": "active"}


class TestConflictError:
    """Test ConflictError factory function"""
    
    def test_with_all_parameters(self):
        """Test ConflictError with all parameters"""
        error = ConflictError(
            message="Email already exists",
            resource="Customer",
            conflicting_id="user@example.com",
            constraint="unique_email"
        )
        
        assert error.code == "CONFLICT"
        assert error.message == "Email already exists"
        assert error.details["resource"] == "Customer"
        assert error.details["conflicting_id"] == "user@example.com"
        assert error.details["constraint"] == "unique_email"
    
    def test_with_minimal_parameters(self):
        """Test ConflictError with only message"""
        error = ConflictError(message="Conflict occurred")
        
        assert error.code == "CONFLICT"
        assert not error.details or error.details == {}  # Accept None or empty dict


class TestAuthorizationError:
    """Test AuthorizationError factory function"""
    
    def test_with_all_parameters(self):
        """Test AuthorizationError with all parameters"""
        error = AuthorizationError(
            message="Cannot delete conversation",
            required_permission="delete:conversation",
            resource="Conversation",
            action="delete"
        )
        
        assert error.code == "AUTHORIZATION_ERROR"
        assert error.message == "Cannot delete conversation"
        assert error.details["required_permission"] == "delete:conversation"
        assert error.details["resource"] == "Conversation"
        assert error.details["action"] == "delete"
        
    def test_with_default_message(self):
        """Test AuthorizationError with default message"""
        error = AuthorizationError()
        
        assert error.message == "Permission denied"
        assert not error.details or error.details == {}  # Accept None or empty dict


class TestRateLimitError:
    """Test RateLimitError factory function"""
    
    def test_with_all_parameters(self):
        """Test RateLimitError with all parameters"""
        error = RateLimitError(
            message="Too many requests",
            limit=100,
            window_seconds=3600,
            retry_after_seconds=300
        )
        
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert error.message == "Too many requests"
        assert error.details["limit"] == 100
        assert error.details["window_seconds"] == 3600
        assert error.details["retry_after_seconds"] == 300
    
    def test_with_default_message(self):
        """Test RateLimitError with default message"""
        error = RateLimitError()
        
        assert error.message == "Rate limit exceeded"


class TestInternalError:
    """Test InternalError factory function"""
    
    def test_with_all_parameters(self):
        """Test InternalError with all parameters"""
        error = InternalError(
            message="Database connection failed",
            operation="create_customer",
            component="CustomerService"
        )
        
        assert error.code == "INTERNAL_ERROR"
        assert error.message == "Database connection failed"
        assert error.details["operation"] == "create_customer"
        assert error.details["component"] == "CustomerService"
    
    def test_with_default_message(self):
        """Test InternalError with default message"""
        error = InternalError()
        
        assert error.message == "An internal error occurred"


class TestExternalServiceError:
    """Test ExternalServiceError factory function"""
    
    def test_with_all_parameters(self):
        """Test ExternalServiceError with all parameters"""
        error = ExternalServiceError(
            message="Vector search failed",
            service="Qdrant",
            operation="search",
            status_code=503,
            is_retryable=True
        )
        
        assert error.code == "EXTERNAL_SERVICE_ERROR"
        assert error.message == "Vector search failed"
        assert error.details["service"] == "Qdrant"
        assert error.details["operation"] == "search"
        assert error.details["status_code"] == 503
        assert error.details["is_retryable"] is True
    
    def test_is_retryable_default_false(self):
        """Test that is_retryable defaults to False"""
        error = ExternalServiceError(
            message="Service failed",
            service="TestService"
        )
        
        assert error.details["is_retryable"] is False


class TestErrorCodes:
    """Test ErrorCodes constants"""
    
    def test_all_codes_defined(self):
        """Test that all expected error codes are defined"""
        assert ErrorCodes.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCodes.BUSINESS_RULE_VIOLATION == "BUSINESS_RULE_VIOLATION"
        assert ErrorCodes.NOT_FOUND == "NOT_FOUND"
        assert ErrorCodes.CONFLICT == "CONFLICT"
        assert ErrorCodes.AUTHORIZATION_ERROR == "AUTHORIZATION_ERROR"
        assert ErrorCodes.RATE_LIMIT_EXCEEDED == "RATE_LIMIT_EXCEEDED"
        assert ErrorCodes.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCodes.EXTERNAL_SERVICE_ERROR == "EXTERNAL_SERVICE_ERROR"
    
    def test_can_use_for_comparison(self):
        """Test that ErrorCodes can be used for pattern matching"""
        error = ValidationError(message="Test")
        
        if error.code == ErrorCodes.VALIDATION_ERROR:
            assert True
        else:
            pytest.fail("ErrorCodes constant didn't match")


@pytest.mark.parametrize("factory,expected_code", [
    (ValidationError, "VALIDATION_ERROR"),
    (BusinessRuleError, "BUSINESS_RULE_VIOLATION"),
    (NotFoundError, "NOT_FOUND"),
    (ConflictError, "CONFLICT"),
    (AuthorizationError, "AUTHORIZATION_ERROR"),
    (RateLimitError, "RATE_LIMIT_EXCEEDED"),
    (InternalError, "INTERNAL_ERROR"),
])
def test_error_factories_return_correct_codes(factory, expected_code):
    """Parametrized test that all factories return correct error codes"""
    if factory == NotFoundError:
        error = factory(resource="Test")
    elif factory == ExternalServiceError:
        error = factory(message="Test", service="Test")
    else:
        error = factory(message="Test")
    
    assert error.code == expected_code