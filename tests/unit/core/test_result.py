"""
Unit tests for Result pattern

Tests cover:
- Result creation (ok/fail)
- Value and error access
- Property validation
- Transformation methods (map, bind)
- Error handling
- Helper functions
"""

import pytest
from uuid import uuid4

from core.result import (
    Result,
    Error,
    validation_error,
    not_found_error,
    business_rule_error,
    conflict_error,
)


class TestError:
    """Test suite for Error class"""
    
    def test_error_creation(self):
        """Test basic error creation"""
        error = Error(
            code="TEST_ERROR",
            message="Test message",
            details={"key": "value"}
        )
        
        assert error.code == "TEST_ERROR"
        assert error.message == "Test message"
        assert error.details == {"key": "value"}
        assert error.stacktrace is None
    
    def test_error_without_details(self):
        """Test error creation without details"""
        error = Error(code="ERROR", message="Message")
        
        assert error.details is None
    
    def test_user_message_property(self):
        """Test user_message returns message"""
        error = Error(code="ERROR", message="User friendly message")
        
        assert error.user_message == "User friendly message"
    
    def test_to_dict(self):
        """Test error serialization to dict"""
        error = Error(
            code="ERROR",
            message="Message",
            details={"field": "email"}
        )
        
        result = error.to_dict()
        
        assert result == {
            "code": "ERROR",
            "message": "Message",
            "details": {"field": "email"}
        }
    
    def test_to_dict_without_details(self):
        """Test to_dict with no details"""
        error = Error(code="ERROR", message="Message")
        
        result = error.to_dict()
        
        assert result["details"] == {}
    
    def test_with_details(self):
        """Test adding details to existing error"""
        error = Error(code="ERROR", message="Message")
        
        new_error = error.with_details(field="email", value="test@test.com")
        
        assert new_error.code == "ERROR"
        assert new_error.message == "Message"
        assert new_error.details == {"field": "email", "value": "test@test.com"}
        assert error.details is None  # Original unchanged (immutable)
    
    def test_with_details_merges(self):
        """Test with_details merges with existing details"""
        error = Error(code="ERROR", message="Message", details={"a": 1})
        
        new_error = error.with_details(b=2, c=3)
        
        assert new_error.details == {"a": 1, "b": 2, "c": 3}
    
    def test_from_exception(self):
        """Test creating error from exception"""
        exc = ValueError("Test exception")
        
        error = Error.from_exception(exc)
        
        assert error.code == "INTERNAL_ERROR"
        assert error.message == "Test exception"
        assert error.details["exception_type"] == "ValueError"
        assert error.stacktrace is not None
    
    def test_from_exception_custom_code(self):
        """Test from_exception with custom code"""
        exc = ValueError("Test")
        
        error = Error.from_exception(exc, code="CUSTOM_CODE")
        
        assert error.code == "CUSTOM_CODE"
    
    def test_str_representation(self):
        """Test string representation"""
        error = Error(code="TEST", message="Message", details={"a": 1})
        
        result = str(error)
        
        assert "TEST" in result
        assert "Message" in result
        assert "details=" in result
    
    def test_error_is_immutable(self):
        """Test that Error is immutable (frozen dataclass)"""
        error = Error(code="ERROR", message="Message")
        
        with pytest.raises(AttributeError):
            error.code = "NEW_CODE"


class TestResult:
    """Test suite for Result class"""
    
    def test_ok_creates_successful_result(self):
        """Test Result.ok() creates successful result"""
        result = Result.ok(42)
        
        assert result.is_success
        assert not result.is_failure
        assert result.value == 42
    
    def test_fail_creates_failed_result(self):
        """Test Result.fail() creates failed result"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        assert result.is_failure
        assert not result.is_success
        assert result.error == error
    
    def test_cannot_access_value_on_failure(self):
        """Test accessing value on failed result raises ValueError"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        with pytest.raises(ValueError, match="Cannot get value from failed result"):
            _ = result.value
    
    def test_cannot_access_error_on_success(self):
        """Test accessing error on successful result raises ValueError"""
        result = Result.ok(42)
        
        with pytest.raises(ValueError, match="Cannot get error from successful result"):
            _ = result.error
    
    def test_post_init_validation_both_set(self):
        """Test that Result validates exactly one of value/error is set"""
        with pytest.raises(ValueError, match="must have either value or error"):
            Result(_value=42, _error=Error("ERROR", "Message"))
    
    def test_post_init_validation_neither_set(self):
        """Test that Result requires either value or error"""
        with pytest.raises(ValueError, match="must have either value or error"):
            Result()
    
    def test_map_transforms_success_value(self):
        """Test map() transforms successful value"""
        result = Result.ok(5)
        
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_success
        assert mapped.value == 10
    
    def test_map_preserves_failure(self):
        """Test map() preserves failure without calling function"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        mapped = result.map(lambda x: x * 2)
        
        assert mapped.is_failure
        assert mapped.error == error
    
    def test_map_handles_exceptions(self):
        """Test map() catches exceptions and returns failure"""
        result = Result.ok(5)
        
        def raise_error(x):
            raise ValueError("Transformation failed")
        
        mapped = result.map(raise_error)
        
        assert mapped.is_failure
        assert mapped.error.code == "TRANSFORMATION_ERROR"
    
    def test_bind_chains_successful_operations(self):
        """Test bind() chains operations that return Results"""
        def double(x):
            return Result.ok(x * 2)
        
        result = Result.ok(5).bind(double)
        
        assert result.is_success
        assert result.value == 10
    
    def test_bind_short_circuits_on_failure(self):
        """Test bind() short-circuits when initial result fails"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        def double(x):
            return Result.ok(x * 2)
        
        chained = result.bind(double)
        
        assert chained.is_failure
        assert chained.error == error
    
    def test_bind_propagates_operation_failure(self):
        """Test bind() propagates failure from chained operation"""
        def failing_operation(x):
            return Result.fail(Error("OP_ERROR", "Operation failed"))
        
        result = Result.ok(5).bind(failing_operation)
        
        assert result.is_failure
        assert result.error.code == "OP_ERROR"
    
    def test_bind_handles_exceptions(self):
        """Test bind() catches exceptions in chained operation"""
        def raise_error(x):
            raise ValueError("Operation error")
        
        result = Result.ok(5).bind(raise_error)
        
        assert result.is_failure
        assert result.error.code == "OPERATION_ERROR"
    
    def test_map_error_transforms_error(self):
        """Test map_error() transforms error on failure"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        mapped = result.map_error(
            lambda e: e.with_details(context="test")
        )
        
        assert mapped.is_failure
        assert mapped.error.details == {"context": "test"}
    
    def test_map_error_preserves_success(self):
        """Test map_error() preserves success value"""
        result = Result.ok(42)
        
        mapped = result.map_error(lambda e: e.with_details(a=1))
        
        assert mapped.is_success
        assert mapped.value == 42
    
    def test_or_else_returns_value_on_success(self):
        """Test or_else() returns value when successful"""
        result = Result.ok(42)
        
        value = result.or_else(0)
        
        assert value == 42
    
    def test_or_else_returns_default_on_failure(self):
        """Test or_else() returns default when failed"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        value = result.or_else(0)
        
        assert value == 0
    
    def test_or_else_get_returns_value_on_success(self):
        """Test or_else_get() returns value when successful"""
        result = Result.ok(42)
        
        value = result.or_else_get(lambda e: 0)
        
        assert value == 42
    
    def test_or_else_get_computes_from_error(self):
        """Test or_else_get() computes default from error"""
        error = Error("NOT_FOUND", "Not found")
        result = Result.fail(error)
        
        value = result.or_else_get(
            lambda e: -1 if e.code == "NOT_FOUND" else 0
        )
        
        assert value == -1
    
    def test_unwrap_returns_value_on_success(self):
        """Test unwrap() returns value when successful"""
        result = Result.ok(42)
        
        value = result.unwrap()
        
        assert value == 42
    
    def test_unwrap_raises_on_failure(self):
        """Test unwrap() raises RuntimeError when failed"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        with pytest.raises(RuntimeError, match="Result unwrap failed"):
            result.unwrap()
    
    def test_expect_returns_value_on_success(self):
        """Test expect() returns value when successful"""
        result = Result.ok(42)
        
        value = result.expect("Should have value")
        
        assert value == 42
    
    def test_expect_raises_with_custom_message(self):
        """Test expect() raises with custom message on failure"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        with pytest.raises(RuntimeError, match="Custom message"):
            result.expect("Custom message")
    
    def test_bool_conversion_success(self):
        """Test Result can be used in boolean context (success = True)"""
        result = Result.ok(42)
        
        assert bool(result) is True
        assert result  # Implicit bool conversion
    
    def test_bool_conversion_failure(self):
        """Test Result can be used in boolean context (failure = False)"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        assert bool(result) is False
        assert not result  # Implicit bool conversion
    
    def test_repr_success(self):
        """Test __repr__ for successful result"""
        result = Result.ok(42)
        
        repr_str = repr(result)
        
        assert "Result.ok" in repr_str
        assert "42" in repr_str
    
    def test_repr_failure(self):
        """Test __repr__ for failed result"""
        error = Error("ERROR", "Message")
        result = Result.fail(error)
        
        repr_str = repr(result)
        
        assert "Result.fail" in repr_str
        assert "ERROR" in repr_str
    
    def test_equality_success(self):
        """Test equality comparison for successful results"""
        result1 = Result.ok(42)
        result2 = Result.ok(42)
        result3 = Result.ok(24)
        
        assert result1 == result2
        assert result1 != result3
    
    def test_equality_failure(self):
        """Test equality comparison for failed results"""
        error1 = Error("ERROR", "Message")
        error2 = Error("ERROR", "Message")
        error3 = Error("OTHER", "Message")
        
        result1 = Result.fail(error1)
        result2 = Result.fail(error2)
        result3 = Result.fail(error3)
        
        assert result1 == result2
        assert result1 != result3
    
    def test_result_is_immutable(self):
        """Test that Result is immutable (frozen dataclass)"""
        result = Result.ok(42)
        
        with pytest.raises(AttributeError):
            result._value = 24


class TestHelperFunctions:
    """Test suite for error helper functions"""
    
    def test_validation_error_with_all_params(self):
        """Test validation_error() with all parameters"""
        error = validation_error(
            message="Email is required",
            field="email",
            value="invalid",
        )
        
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Email is required"
        assert error.details["field"] == "email"
        assert error.details["value"] == "invalid"
    
    def test_validation_error_minimal(self):
        """Test validation_error() with minimal parameters"""
        error = validation_error(message="Invalid input")
        
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid input"
        assert error.details is None
    
    def test_not_found_error(self):
        """Test not_found_error() helper"""
        error = not_found_error(resource="Customer", identifier="123")
        
        assert error.code == "NOT_FOUND"
        assert error.message == "Customer not found"
        assert error.details["resource"] == "Customer"
        assert error.details["identifier"] == "123"
    
    def test_business_rule_error_with_rule(self):
        """Test business_rule_error() with rule name"""
        error = business_rule_error(
            message="Cannot resolve without messages",
            rule="ConversationResolutionRule"
        )
        
        assert error.code == "BUSINESS_RULE_VIOLATION"
        assert error.message == "Cannot resolve without messages"
        assert error.details["rule"] == "ConversationResolutionRule"
    
    def test_business_rule_error_without_rule(self):
        """Test business_rule_error() without rule name"""
        error = business_rule_error(message="Rule violated")
        
        assert error.code == "BUSINESS_RULE_VIOLATION"
        assert error.details is None
    
    def test_conflict_error(self):
        """Test conflict_error() helper"""
        error = conflict_error(
            message="Email already exists",
            conflicting_id="user@example.com"
        )
        
        assert error.code == "CONFLICT"
        assert error.message == "Email already exists"
        assert error.details["conflicting_id"] == "user@example.com"


class TestResultChaining:
    """Test complex Result chaining scenarios"""
    
    def test_railway_oriented_programming_success_path(self):
        """Test ROP success path with multiple operations"""
        def parse_int(s: str) -> Result[int]:
            try:
                return Result.ok(int(s))
            except ValueError:
                return Result.fail(validation_error("Invalid integer", value=s))
        
        def validate_positive(n: int) -> Result[int]:
            if n > 0:
                return Result.ok(n)
            return Result.fail(business_rule_error("Must be positive"))
        
        def double(n: int) -> Result[int]:
            return Result.ok(n * 2)
        
        result = (
            parse_int("5")
            .bind(validate_positive)
            .bind(double)
        )
        
        assert result.is_success
        assert result.value == 10
    
    def test_railway_oriented_programming_failure_path(self):
        """Test ROP failure path short-circuits"""
        operations_called = []
        
        def parse_int(s: str) -> Result[int]:
            operations_called.append("parse")
            return Result.fail(validation_error("Invalid"))
        
        def validate_positive(n: int) -> Result[int]:
            operations_called.append("validate")
            return Result.ok(n)
        
        def double(n: int) -> Result[int]:
            operations_called.append("double")
            return Result.ok(n * 2)
        
        result = (
            parse_int("invalid")
            .bind(validate_positive)
            .bind(double)
        )
        
        assert result.is_failure
        assert operations_called == ["parse"]  # Short-circuited


@pytest.mark.parametrize("value,expected", [
    (5, 10),
    (0, 0),
    (-5, -10),
    (100, 200),
])
def test_map_with_various_values(value, expected):
    """Parametrized test for map() with different values"""
    result = Result.ok(value).map(lambda x: x * 2)
    
    assert result.is_success
    assert result.value == expected