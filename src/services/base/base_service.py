"""
Base Service - Foundation for all service classes

Provides common functionality for service layer including:
- Result-based error handling
- Transaction awareness
- Logging
- Common helper methods

All service classes should inherit from BaseService.
"""

from typing import TypeVar, Generic, Optional, Callable, Any
from uuid import UUID
import logging
from functools import wraps

from core.result import Result, Error
from core.errors import InternalError

__all__ = ["BaseService"]

T = TypeVar("T")


def handle_exceptions(operation_name: str = "operation"):
    """
    Decorator to handle exceptions and convert to Result
    
    Wraps service methods to catch exceptions and return Result.fail()
    instead of raising. This enables Railway Oriented Programming.
    
    Args:
        operation_name: Name of operation for error messages
    
    Example:
        >>> class MyService(BaseService):
        ...     @handle_exceptions("create_user")
        ...     def create_user(self, email: str) -> Result[User]:
        ...         user = User(email=email)
        ...         return Result.ok(user)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Result:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get logger from first arg (self)
                logger = getattr(args[0], 'logger', logging.getLogger(__name__))
                logger.error(
                    f"Error in {operation_name}: {e}",
                    exc_info=True
                )
                return Result.fail(InternalError(
                    message=f"Failed to {operation_name}",
                    operation=operation_name,
                    component=args[0].__class__.__name__
                ))
        return wrapper
    return decorator


class BaseService:
    """
    Base class for all service layer classes
    
    Services contain business logic and coordinate between repositories,
    domain models, and external services. They return Result objects
    instead of raising exceptions.
    
    Features:
    - Result-based error handling (no exceptions in business logic)
    - Structured logging with service context
    - Common helper methods
    - Transaction awareness (when used with UnitOfWork)
    
    Example:
        >>> class CustomerService(BaseService):
        ...     def __init__(self, customer_repo: CustomerRepository):
        ...         super().__init__()
        ...         self.customer_repo = customer_repo
        ...     
        ...     def create_customer(self, email: str) -> Result[Customer]:
        ...         # Validation
        ...         if not self.is_valid_email(email):
        ...             return Result.fail(ValidationError(
        ...                 message="Invalid email format",
        ...                 field="email",
        ...                 value=email
        ...             ))
        ...         
        ...         # Business logic
        ...         customer = self.customer_repo.create(email=email)
        ...         return Result.ok(customer)
    """
    
    def __init__(self):
        """Initialize base service with logger"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"{self.__class__.__name__} initialized")
    
    # ===== Helper Methods =====
    
    def is_valid_email(self, email: str) -> bool:
        """
        Validate email format (basic check)
        
        Args:
            email: Email address to validate
        
        Returns:
            True if email appears valid
        
        Note:
            This is a basic check. For production, use a proper
            email validation library like email-validator.
        """
        if not email or '@' not in email:
            return False
        
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain:
            return False
        
        if '.' not in domain:
            return False
        
        return True
    
    def is_valid_uuid(self, value: str) -> bool:
        """
        Check if string is valid UUID
        
        Args:
            value: String to check
        
        Returns:
            True if valid UUID format
        """
        try:
            UUID(value)
            return True
        except (ValueError, TypeError, AttributeError):
            return False
    
    def log_operation(
        self,
        operation: str,
        success: bool,
        **context
    ) -> None:
        """
        Log service operation with context
        
        Args:
            operation: Name of operation
            success: Whether operation succeeded
            **context: Additional context to log
        
        Example:
            >>> self.log_operation(
            ...     "create_customer",
            ...     success=True,
            ...     customer_id=customer.id,
            ...     email=customer.email
            ... )
        """
        level = logging.INFO if success else logging.ERROR
        status = "succeeded" if success else "failed"
        
        self.logger.log(
            level,
            f"{operation} {status}",
            extra={"operation": operation, "success": success, **context}
        )
    
    def execute(
        self,
        operation: Callable[[], T],
        operation_name: str = "operation"
    ) -> Result[T]:
        """
        Execute operation and wrap result
        
        Catches exceptions and converts them to Result.fail().
        Use this for operations that might raise exceptions.
        
        Args:
            operation: Callable that returns a value
            operation_name: Name for error messages
        
        Returns:
            Result wrapping the operation outcome
        
        Example:
            >>> def do_something_risky():
            ...     # ... code that might raise ...
            ...     return value
            >>> 
            >>> result = self.execute(do_something_risky, "do_something")
            >>> if result.is_success:
            ...     value = result.value
        """
        try:
            value = operation()
            self.log_operation(operation_name, success=True)
            return Result.ok(value)
        except Exception as e:
            self.logger.error(
                f"Error in {operation_name}: {e}",
                exc_info=True
            )
            self.log_operation(operation_name, success=False, error=str(e))
            return Result.fail(InternalError(
                message=f"Failed to {operation_name}",
                operation=operation_name,
                component=self.__class__.__name__
            ))
    
    # ===== Validation Helpers =====
    
    def require_not_none(
        self,
        value: Any,
        field_name: str
    ) -> Result[None]:
        """
        Validate that value is not None
        
        Args:
            value: Value to check
            field_name: Name of field for error message
        
        Returns:
            Result.ok(None) if valid, Result.fail() if None
        
        Example:
            >>> result = self.require_not_none(customer_id, "customer_id")
            >>> if result.is_failure:
            ...     return result  # Early return with validation error
        """
        from core.errors import ValidationError
        
        if value is None:
            return Result.fail(ValidationError(
                message=f"{field_name} is required",
                field=field_name,
                constraint="required"
            ))
        return Result.ok(None)
    
    def require_not_empty(
        self,
        value: str,
        field_name: str
    ) -> Result[None]:
        """
        Validate that string is not empty
        
        Args:
            value: String to check
            field_name: Name of field for error message
        
        Returns:
            Result.ok(None) if valid, Result.fail() if empty
        """
        from core.errors import ValidationError
        
        if not value or not value.strip():
            return Result.fail(ValidationError(
                message=f"{field_name} cannot be empty",
                field=field_name,
                constraint="not_empty"
            ))
        return Result.ok(None)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__}>"


if __name__ == "__main__":
    # Self-test
    print("=" * 70)
    print("BASE SERVICE - SELF TEST")
    print("=" * 70)
    
    class TestService(BaseService):
        """Test service for demonstration"""
        
        def test_success(self) -> Result[str]:
            """Operation that succeeds"""
            return Result.ok("success")
        
        def test_failure(self) -> Result[str]:
            """Operation that fails"""
            from core.errors import ValidationError
            return Result.fail(ValidationError(
                message="Test validation error",
                field="test_field"
            ))
        
        @handle_exceptions("risky_operation")
        def test_exception(self) -> Result[str]:
            """Operation that raises exception"""
            raise ValueError("Test exception")
    
    # Test service creation
    print("\n1. Testing service creation...")
    service = TestService()
    print(f"   ✓ {service}")
    
    # Test successful operation
    print("\n2. Testing successful operation...")
    result = service.test_success()
    assert result.is_success
    assert result.value == "success"
    print(f"   ✓ Success: {result.value}")
    
    # Test failed operation
    print("\n3. Testing failed operation...")
    result = service.test_failure()
    assert result.is_failure
    assert result.error.code == "VALIDATION_ERROR"
    print(f"   ✓ Failure: {result.error}")
    
    # Test exception handling
    print("\n4. Testing exception handling...")
    result = service.test_exception()
    assert result.is_failure
    assert result.error.code == "INTERNAL_ERROR"
    print(f"   ✓ Exception caught: {result.error}")
    
    # Test email validation
    print("\n5. Testing email validation...")
    assert service.is_valid_email("user@example.com")
    assert not service.is_valid_email("invalid")
    assert not service.is_valid_email("@example.com")
    print(f"   ✓ Email validation works")
    
    # Test UUID validation
    print("\n6. Testing UUID validation...")
    from uuid import uuid4
    assert service.is_valid_uuid(str(uuid4()))
    assert not service.is_valid_uuid("not-a-uuid")
    print(f"   ✓ UUID validation works")
    
    # Test require_not_none
    print("\n7. Testing require_not_none...")
    result = service.require_not_none("value", "test_field")
    assert result.is_success
    result = service.require_not_none(None, "test_field")
    assert result.is_failure
    print(f"   ✓ require_not_none works")
    
    # Test require_not_empty
    print("\n8. Testing require_not_empty...")
    result = service.require_not_empty("value", "test_field")
    assert result.is_success
    result = service.require_not_empty("", "test_field")
    assert result.is_failure
    result = service.require_not_empty("   ", "test_field")
    assert result.is_failure
    print(f"   ✓ require_not_empty works")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)