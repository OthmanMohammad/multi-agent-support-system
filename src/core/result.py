"""
Result Pattern - Railway Oriented Programming

This module implements the Result pattern for error handling without exceptions.
Results represent either success (with a value) or failure (with an error).

The Result pattern enables:
- Explicit error handling in type signatures
- Composition of operations that may fail
- Railway-oriented programming (success/failure tracks)
- No hidden control flow from exceptions

Example:
    >>> result = Result.ok(42)
    >>> result.is_success
    True
    >>> result.value
    42
    
    >>> error_result = Result.fail(Error("NOT_FOUND", "Item not found"))
    >>> error_result.is_failure
    True
    >>> error_result.error.code
    'NOT_FOUND'
    
    >>> # Chaining operations
    >>> result = (
    ...     get_user(user_id)
    ...     .map(lambda user: user.email)
    ...     .bind(send_email)
    ... )

References:
    - Railway Oriented Programming: https://fsharpforfunandprofit.com/rop/
    - Rust Result type: https://doc.rust-lang.org/std/result/
"""

from typing import TypeVar, Generic, Optional, Callable, Union
from dataclasses import dataclass, field
import traceback as tb

__all__ = ["Error", "Result"]

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E", bound="Error")


@dataclass(frozen=True)
class Error:
    """
    Structured error with code, message, and optional details
    
    Attributes:
        code: Machine-readable error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Human-readable error message
        details: Optional dict with additional context (field names, values, etc.)
        stacktrace: Optional stacktrace for debugging (not exposed to users)
    
    Example:
        >>> error = Error(
        ...     code="VALIDATION_ERROR",
        ...     message="Email is required",
        ...     details={"field": "email"}
        ... )
        >>> error.code
        'VALIDATION_ERROR'
        >>> error.user_message
        'Email is required'
    """
    
    code: str
    message: str
    details: Optional[dict] = None
    stacktrace: Optional[str] = field(default=None, repr=False)
    
    @property
    def user_message(self) -> str:
        """Get user-friendly error message (safe to expose to clients)"""
        return self.message
    
    def to_dict(self) -> dict:
        """
        Serialize error to dictionary (for API responses)
        
        Note: Excludes stacktrace for security (internal debugging only)
        
        Returns:
            Dict with code, message, and details
        """
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details or {}
        }
    
    def with_details(self, **kwargs) -> "Error":
        """
        Create a new error with additional details
        
        Args:
            **kwargs: Additional detail fields
            
        Returns:
            New Error instance with merged details
            
        Example:
            >>> error = Error("VALIDATION_ERROR", "Invalid input")
            >>> error = error.with_details(field="email", value="invalid")
            >>> error.details
            {'field': 'email', 'value': 'invalid'}
        """
        merged_details = {**(self.details or {}), **kwargs}
        return Error(
            code=self.code,
            message=self.message,
            details=merged_details,
            stacktrace=self.stacktrace
        )
    
    @staticmethod
    def from_exception(exc: Exception, code: str = "INTERNAL_ERROR") -> "Error":
        """
        Create Error from an exception
        
        Args:
            exc: Exception to convert
            code: Error code to use
            
        Returns:
            Error with exception details
        """
        return Error(
            code=code,
            message=str(exc),
            details={"exception_type": type(exc).__name__},
            stacktrace=tb.format_exc()
        )
    
    def __str__(self) -> str:
        """String representation for logging"""
        details_str = f", details={self.details}" if self.details else ""
        return f"{self.code}: {self.message}{details_str}"


@dataclass(frozen=True)
class Result(Generic[T]):
    """
    Result of an operation - either success with value or failure with error
    
    This implements Railway Oriented Programming where operations return Results
    instead of raising exceptions, making the happy path and error path explicit.
    
    Attributes:
        _value: The success value (None if failure)
        _error: The error (None if success)
    
    Type Parameters:
        T: The type of the success value
    
    Example:
        >>> # Creating results
        >>> success = Result.ok(42)
        >>> failure = Result.fail(Error("NOT_FOUND", "Item not found"))
        
        >>> # Checking results
        >>> if success.is_success:
        ...     print(success.value)
        42
        
        >>> # Chaining operations (Railway Oriented Programming)
        >>> result = (
        ...     get_user(user_id)
        ...     .map(lambda user: user.email)
        ...     .bind(validate_email)
        ...     .bind(send_email)
        ... )
        
        >>> # Safe value access with default
        >>> email = result.or_else("default@example.com")
    
    Implementation Notes:
        - Uses private _value and _error to enforce invariant: exactly one is set
        - Immutable (frozen dataclass) for safety
        - Generic type parameter T for type safety
        - Properties prevent invalid state access
    """
    
    _value: Optional[T] = None
    _error: Optional[Error] = None
    
    def __post_init__(self):
        """Validate that exactly one of value or error is set"""
        has_value = self._value is not None
        has_error = self._error is not None
        
        if has_value and has_error:
            raise ValueError(
                "Result cannot have both value and error. "
                "Use Result.ok() or Result.fail() to create instances."
            )
        
        if not has_value and not has_error:
            raise ValueError(
                "Result must have either value or error. "
                "Use Result.ok() or Result.fail() to create instances."
            )
    
    @property
    def is_success(self) -> bool:
        """Check if result is successful (has value)"""
        return self._error is None
    
    @property
    def is_failure(self) -> bool:
        """Check if result is a failure (has error)"""
        return self._error is not None
    
    @property
    def value(self) -> T:
        """
        Get the success value
        
        Raises:
            ValueError: If result is a failure (has error)
            
        Returns:
            The success value
            
        Example:
            >>> result = Result.ok(42)
            >>> result.value
            42
            
            >>> failed = Result.fail(Error("ERROR", "Failed"))
            >>> failed.value  # Raises ValueError
        """
        if self.is_failure:
            raise ValueError(
                f"Cannot get value from failed result. "
                f"Error: {self._error}"
            )
        return self._value
    
    @property
    def error(self) -> Error:
        """
        Get the error
        
        Raises:
            ValueError: If result is successful (has value)
            
        Returns:
            The error
            
        Example:
            >>> result = Result.fail(Error("ERROR", "Failed"))
            >>> result.error.code
            'ERROR'
            
            >>> success = Result.ok(42)
            >>> success.error  # Raises ValueError
        """
        if self.is_success:
            raise ValueError(
                "Cannot get error from successful result. "
                f"Value: {self._value}"
            )
        return self._error
    
    @staticmethod
    def ok(value: T) -> "Result[T]":
        """
        Create a successful result
        
        Args:
            value: The success value
            
        Returns:
            Successful Result containing the value
            
        Example:
            >>> result = Result.ok(42)
            >>> result.is_success
            True
            >>> result.value
            42
        """
        return Result(_value=value)
    
    @staticmethod
    def fail(error: Error) -> "Result[T]":
        """
        Create a failed result
        
        Args:
            error: The error
            
        Returns:
            Failed Result containing the error
            
        Example:
            >>> result = Result.fail(Error("NOT_FOUND", "User not found"))
            >>> result.is_failure
            True
            >>> result.error.code
            'NOT_FOUND'
        """
        return Result(_error=error)
    
    def map(self, func: Callable[[T], U]) -> "Result[U]":
        """
        Transform the value if successful (functor map operation)
        
        If result is failure, returns same error without calling func.
        If result is success, applies func to value and wraps in Result.
        
        Args:
            func: Function to transform the value (T -> U)
            
        Returns:
            New Result with transformed value, or same error
            
        Example:
            >>> result = Result.ok(5).map(lambda x: x * 2)
            >>> result.value
            10
            
            >>> failed = Result.fail(Error("ERROR", "Failed"))
            >>> failed.map(lambda x: x * 2).is_failure
            True
        """
        if self.is_failure:
            return Result.fail(self._error)
        
        try:
            new_value = func(self._value)
            return Result.ok(new_value)
        except Exception as e:
            return Result.fail(Error.from_exception(
                e,
                code="TRANSFORMATION_ERROR"
            ))
    
    def bind(self, func: Callable[[T], "Result[U]"]) -> "Result[U]":
        """
        Chain operations that return Results (monadic bind operation)
        
        This enables Railway Oriented Programming by chaining operations
        that may fail, automatically short-circuiting on first failure.
        
        Args:
            func: Function that returns a Result (T -> Result[U])
            
        Returns:
            Result from function, or same error
            
        Example:
            >>> def validate_positive(x: int) -> Result[int]:
            ...     if x > 0:
            ...         return Result.ok(x)
            ...     return Result.fail(Error("INVALID", "Must be positive"))
            
            >>> result = (
            ...     Result.ok(5)
            ...     .bind(validate_positive)
            ...     .map(lambda x: x * 2)
            ... )
            >>> result.value
            10
            
            >>> # Failure short-circuits
            >>> result = (
            ...     Result.ok(-5)
            ...     .bind(validate_positive)  # Fails here
            ...     .map(lambda x: x * 2)     # Not executed
            ... )
            >>> result.is_failure
            True
        """
        if self.is_failure:
            return Result.fail(self._error)
        
        try:
            return func(self._value)
        except Exception as e:
            return Result.fail(Error.from_exception(
                e,
                code="OPERATION_ERROR"
            ))
    
    def map_error(self, func: Callable[[Error], Error]) -> "Result[T]":
        """
        Transform the error if failed
        
        Args:
            func: Function to transform the error
            
        Returns:
            Same value or transformed error
            
        Example:
            >>> result = Result.fail(Error("ERROR", "Failed"))
            >>> result = result.map_error(
            ...     lambda e: e.with_details(context="user_service")
            ... )
            >>> result.error.details
            {'context': 'user_service'}
        """
        if self.is_success:
            return Result.ok(self._value)
        
        try:
            new_error = func(self._error)
            return Result.fail(new_error)
        except Exception as e:
            # If error transformation fails, keep original error
            return Result.fail(self._error)
    
    def or_else(self, default: T) -> T:
        """
        Get value or return default if failed
        
        Args:
            default: Default value to use on failure
            
        Returns:
            Value if success, default if failure
            
        Example:
            >>> Result.ok(42).or_else(0)
            42
            >>> Result.fail(Error("ERROR", "Failed")).or_else(0)
            0
        """
        return self._value if self.is_success else default
    
    def or_else_get(self, func: Callable[[Error], T]) -> T:
        """
        Get value or compute from error if failed
        
        Args:
            func: Function to compute default from error
            
        Returns:
            Value if success, computed value if failure
            
        Example:
            >>> success = Result.ok(42)
            >>> success.or_else_get(lambda e: 0)
            42
            
            >>> failed = Result.fail(Error("NOT_FOUND", "Missing"))
            >>> failed.or_else_get(lambda e: -1 if e.code == "NOT_FOUND" else 0)
            -1
        """
        return self._value if self.is_success else func(self._error)
    
    def unwrap(self) -> T:
        """
        Unwrap value or raise exception (use sparingly!)
        
        This breaks the Result pattern by raising exceptions.
        Prefer pattern matching or or_else() instead.
        
        Raises:
            RuntimeError: If result is a failure
            
        Returns:
            The value
            
        Example:
            >>> Result.ok(42).unwrap()
            42
            >>> Result.fail(Error("ERROR", "Failed")).unwrap()
            Traceback (most recent call last):
            RuntimeError: Result unwrap failed: ERROR: Failed
        """
        if self.is_failure:
            raise RuntimeError(f"Result unwrap failed: {self._error}")
        return self._value
    
    def expect(self, message: str) -> T:
        """
        Unwrap value or raise exception with custom message
        
        Args:
            message: Custom error message
            
        Raises:
            RuntimeError: If result is a failure
            
        Returns:
            The value
            
        Example:
            >>> Result.ok(42).expect("Should have value")
            42
            >>> Result.fail(Error("ERROR", "Failed")).expect("Expected success")
            Traceback (most recent call last):
            RuntimeError: Expected success: ERROR: Failed
        """
        if self.is_failure:
            raise RuntimeError(f"{message}: {self._error}")
        return self._value
    
    def __bool__(self) -> bool:
        """
        Allow using Result in boolean context
        
        Example:
            >>> if Result.ok(42):
            ...     print("Success!")
            Success!
            >>> if not Result.fail(Error("ERROR", "Failed")):
            ...     print("Failed!")
            Failed!
        """
        return self.is_success
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        if self.is_success:
            return f"Result.ok({self._value!r})"
        return f"Result.fail({self._error!r})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if not isinstance(other, Result):
            return False
        return self._value == other._value and self._error == other._error


# ===== Helper Functions for Common Error Types =====

def validation_error(
    message: str,
    field: Optional[str] = None,
    value: Optional[any] = None
) -> Error:
    """
    Create a validation error
    
    Args:
        message: Error message
        field: Field name that failed validation
        value: Invalid value (converted to string)
        
    Returns:
        Error with VALIDATION_ERROR code
        
    Example:
        >>> error = validation_error(
        ...     "Email is required",
        ...     field="email"
        ... )
        >>> error.code
        'VALIDATION_ERROR'
    """
    details = {}
    if field:
        details["field"] = field
    if value is not None:
        details["value"] = str(value)
    
    return Error(
        code="VALIDATION_ERROR",
        message=message,
        details=details if details else None
    )


def not_found_error(resource: str, identifier: str) -> Error:
    """
    Create a not found error
    
    Args:
        resource: Type of resource (e.g., "Customer", "Conversation")
        identifier: Resource identifier
        
    Returns:
        Error with NOT_FOUND code
        
    Example:
        >>> error = not_found_error("Customer", "user123")
        >>> error.message
        'Customer not found'
        >>> error.details
        {'resource': 'Customer', 'identifier': 'user123'}
    """
    return Error(
        code="NOT_FOUND",
        message=f"{resource} not found",
        details={"resource": resource, "identifier": identifier}
    )


def business_rule_error(message: str, rule: Optional[str] = None) -> Error:
    """
    Create a business rule violation error
    
    Args:
        message: Error message
        rule: Name of the violated rule
        
    Returns:
        Error with BUSINESS_RULE_VIOLATION code
        
    Example:
        >>> error = business_rule_error(
        ...     "Cannot resolve conversation without agent response",
        ...     rule="ConversationResolutionRule"
        ... )
        >>> error.code
        'BUSINESS_RULE_VIOLATION'
    """
    return Error(
        code="BUSINESS_RULE_VIOLATION",
        message=message,
        details={"rule": rule} if rule else None
    )


def conflict_error(message: str, conflicting_id: Optional[str] = None) -> Error:
    """
    Create a conflict error (e.g., duplicate resource)
    
    Args:
        message: Error message
        conflicting_id: ID of conflicting resource
        
    Returns:
        Error with CONFLICT code
        
    Example:
        >>> error = conflict_error(
        ...     "Customer with this email already exists",
        ...     conflicting_id="user@example.com"
        ... )
        >>> error.code
        'CONFLICT'
    """
    return Error(
        code="CONFLICT",
        message=message,
        details={"conflicting_id": conflicting_id} if conflicting_id else None
    )


if __name__ == "__main__":
    # Self-test
    print("=" * 70)
    print("RESULT PATTERN - SELF TEST")
    print("=" * 70)
    
    # Test success
    print("\n1. Testing successful result...")
    success = Result.ok(42)
    assert success.is_success
    assert success.value == 42
    print(f"   ✓ {success}")
    
    # Test failure
    print("\n2. Testing failed result...")
    failure = Result.fail(Error("TEST_ERROR", "This is a test error"))
    assert failure.is_failure
    assert failure.error.code == "TEST_ERROR"
    print(f"   ✓ {failure}")
    
    # Test map
    print("\n3. Testing map transformation...")
    mapped = Result.ok(5).map(lambda x: x * 2)
    assert mapped.value == 10
    print(f"   ✓ Mapped value: {mapped.value}")
    
    # Test bind (chaining)
    print("\n4. Testing bind (chaining)...")
    def validate_positive(x: int) -> Result[int]:
        if x > 0:
            return Result.ok(x)
        return Result.fail(Error("INVALID", "Must be positive"))
    
    chained = Result.ok(5).bind(validate_positive).map(lambda x: x * 2)
    assert chained.value == 10
    print(f"   ✓ Chained result: {chained.value}")
    
    # Test failure short-circuit
    print("\n5. Testing failure short-circuit...")
    failed_chain = Result.ok(-5).bind(validate_positive).map(lambda x: x * 2)
    assert failed_chain.is_failure
    assert failed_chain.error.code == "INVALID"
    print(f"   ✓ Short-circuited on: {failed_chain.error.code}")
    
    # Test or_else
    print("\n6. Testing or_else...")
    assert Result.ok(42).or_else(0) == 42
    assert Result.fail(Error("ERROR", "Failed")).or_else(0) == 0
    print("   ✓ or_else working correctly")
    
    # Test helper functions
    print("\n7. Testing error helpers...")
    val_error = validation_error("Email required", field="email")
    assert val_error.code == "VALIDATION_ERROR"
    print(f"   ✓ {val_error}")
    
    nf_error = not_found_error("User", "123")
    assert nf_error.code == "NOT_FOUND"
    print(f"   ✓ {nf_error}")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)