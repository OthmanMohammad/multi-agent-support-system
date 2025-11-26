"""
Base Service - Foundation for all service classes

Provides common functionality for service layer including:
- Result-based error handling
- Async/await support for database operations
- Transaction awareness via Unit of Work
- Logging
- Common helper methods

All service classes should inherit from BaseService.
"""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar
from uuid import UUID

from src.core.errors import InternalError
from src.core.result import Result
from src.utils.logging.setup import get_logger

__all__ = ["BaseService"]

T = TypeVar("T")


def handle_exceptions(operation_name: str = "operation"):
    """
    Decorator to handle exceptions in async methods and convert to Result

    Wraps async service methods to catch exceptions and return Result.fail()
    instead of raising. This enables Railway Oriented Programming.

    Args:
        operation_name: Name of operation for error messages

    Example:
        >>> class MyService(BaseService):
        ...     @handle_exceptions("create_user")
        ...     async def create_user(self, email: str) -> Result[User]:
        ...         user = await self.user_repo.create(email=email)
        ...         return Result.ok(user)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Result:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get logger from first arg (self)
                logger = getattr(args[0], "logger", get_logger(__name__))
                logger.error(
                    f"{operation_name}_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                return Result.fail(
                    InternalError(
                        message=f"Failed to {operation_name}",
                        operation=operation_name,
                        component=args[0].__class__.__name__,
                    )
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Result:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger = getattr(args[0], "logger", get_logger(__name__))
                logger.error(
                    f"{operation_name}_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                return Result.fail(
                    InternalError(
                        message=f"Failed to {operation_name}",
                        operation=operation_name,
                        component=args[0].__class__.__name__,
                    )
                )

        # Return appropriate wrapper based on whether function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class BaseService:
    """
    Base class for all service layer classes

    Services contain business logic and coordinate between repositories,
    domain models, and external services. They return Result objects
    instead of raising exceptions.

    Features:
    - Result-based error handling (no exceptions in business logic)
    - Async/await support for database operations
    - Structured logging with service context
    - Common helper methods
    - Transaction awareness (when used with UnitOfWork)

    Example:
        >>> from database.unit_of_work import UnitOfWork
        >>>
        >>> class CustomerService(BaseService):
        ...     def __init__(self, uow: UnitOfWork):
        ...         super().__init__()
        ...         self.uow = uow
        ...
        ...     async def create_customer(self, email: str) -> Result[Customer]:
        ...         # Validation
        ...         if not self.is_valid_email(email):
        ...             return Result.fail(ValidationError(
        ...                 message="Invalid email format",
        ...                 field="email",
        ...                 value=email
        ...             ))
        ...
        ...         # Business logic
        ...         customer = await self.uow.customers.create(email=email)
        ...         return Result.ok(customer)
    """

    def __init__(self):
        """Initialize base service with logger"""
        logger_name = self.__class__.__name__
        self.logger = get_logger(logger_name)
        # Store logger name for tests and debugging
        self.logger.name = logger_name
        self.logger.debug("service_initialized", service_class=logger_name)

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
        if not email or "@" not in email:
            return False

        parts = email.split("@")
        if len(parts) != 2:
            return False

        local, domain = parts
        if not local or not domain:
            return False

        return "." in domain

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

    def log_operation(self, operation: str, success: bool, **context) -> None:
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
        if success:
            self.logger.info(f"{operation}_succeeded", operation=operation, **context)
        else:
            self.logger.error(f"{operation}_failed", operation=operation, **context)

    async def execute_async(
        self, operation: Callable[[], Awaitable[T]], operation_name: str = "operation"
    ) -> Result[T]:
        """
        Execute async operation and wrap result

        Catches exceptions and converts them to Result.fail().
        Use this for async operations that might raise exceptions.

        Args:
            operation: Async callable that returns a value
            operation_name: Name for error messages

        Returns:
            Result wrapping the operation outcome

        Example:
            >>> async def do_something_risky():
            ...     # ... async code that might raise ...
            ...     return await db.query(...)
            >>>
            >>> result = await self.execute_async(do_something_risky, "db_query")
            >>> if result.is_success:
            ...     value = result.value
        """
        try:
            value = await operation()
            self.log_operation(operation_name, success=True)
            return Result.ok(value)
        except Exception as e:
            self.logger.error(
                f"{operation_name}_exception",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            self.log_operation(operation_name, success=False, error=str(e))
            return Result.fail(
                InternalError(
                    message=f"Failed to {operation_name}",
                    operation=operation_name,
                    component=self.__class__.__name__,
                )
            )

    def execute(self, operation: Callable[[], T], operation_name: str = "operation") -> Result[T]:
        """
        Execute synchronous operation and wrap result

        Catches exceptions and converts them to Result.fail().
        Use this for sync operations that might raise exceptions.

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
                f"{operation_name}_exception",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            self.log_operation(operation_name, success=False, error=str(e))
            return Result.fail(
                InternalError(
                    message=f"Failed to {operation_name}",
                    operation=operation_name,
                    component=self.__class__.__name__,
                )
            )

    # ===== Validation Helpers =====

    def require_not_none(self, value: Any, field_name: str) -> Result[None]:
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
        from src.core.errors import ValidationError

        if value is None:
            return Result.fail(
                ValidationError(
                    message=f"{field_name} is required", field=field_name, constraint="required"
                )
            )
        return Result.ok(None)

    def require_not_empty(self, value: str, field_name: str) -> Result[None]:
        """
        Validate that string is not empty

        Args:
            value: String to check
            field_name: Name of field for error message

        Returns:
            Result.ok(None) if valid, Result.fail() if empty
        """
        from src.core.errors import ValidationError

        if not value or not value.strip():
            return Result.fail(
                ValidationError(
                    message=f"{field_name} cannot be empty",
                    field=field_name,
                    constraint="not_empty",
                )
            )
        return Result.ok(None)

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__}>"


if __name__ == "__main__":
    import asyncio

    # Self-test
    print("=" * 70)
    print("BASE SERVICE - SELF TEST")
    print("=" * 70)

    class TestService(BaseService):
        """Test service for demonstration"""

        def test_success(self) -> Result[str]:
            """Sync operation that succeeds"""
            return Result.ok("success")

        async def test_async_success(self) -> Result[str]:
            """Async operation that succeeds"""
            await asyncio.sleep(0.01)  # Simulate async work
            return Result.ok("async_success")

        def test_failure(self) -> Result[str]:
            """Operation that fails"""
            from src.core.errors import ValidationError

            return Result.fail(ValidationError(message="Test validation error", field="test_field"))

        @handle_exceptions("risky_operation")
        def test_exception(self) -> Result[str]:
            """Sync operation that raises exception"""
            raise ValueError("Test exception")

        @handle_exceptions("risky_async_operation")
        async def test_async_exception(self) -> Result[str]:
            """Async operation that raises exception"""
            await asyncio.sleep(0.01)
            raise ValueError("Test async exception")

    async def run_tests():
        # Test service creation
        print("\n1. Testing service creation...")
        service = TestService()
        print(f"   ✓ {service}")

        # Test successful operation
        print("\n2. Testing successful sync operation...")
        result = service.test_success()
        assert result.is_success
        assert result.value == "success"
        print(f"   ✓ Success: {result.value}")

        # Test successful async operation
        print("\n3. Testing successful async operation...")
        result = await service.test_async_success()
        assert result.is_success
        assert result.value == "async_success"
        print(f"   ✓ Async Success: {result.value}")

        # Test failed operation
        print("\n4. Testing failed operation...")
        result = service.test_failure()
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        print(f"   ✓ Failure: {result.error}")

        # Test sync exception handling
        print("\n5. Testing sync exception handling...")
        result = service.test_exception()
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"
        print(f"   ✓ Exception caught: {result.error}")

        # Test async exception handling
        print("\n6. Testing async exception handling...")
        result = await service.test_async_exception()
        assert result.is_failure
        assert result.error.code == "INTERNAL_ERROR"
        print(f"   ✓ Async exception caught: {result.error}")

        # Test email validation
        print("\n7. Testing email validation...")
        assert service.is_valid_email("user@example.com")
        assert not service.is_valid_email("invalid")
        assert not service.is_valid_email("@example.com")
        print("   ✓ Email validation works")

        # Test UUID validation
        print("\n8. Testing UUID validation...")
        from uuid import uuid4

        assert service.is_valid_uuid(str(uuid4()))
        assert not service.is_valid_uuid("not-a-uuid")
        print("   ✓ UUID validation works")

        # Test require_not_none
        print("\n9. Testing require_not_none...")
        result = service.require_not_none("value", "test_field")
        assert result.is_success
        result = service.require_not_none(None, "test_field")
        assert result.is_failure
        print("   ✓ require_not_none works")

        # Test require_not_empty
        print("\n10. Testing require_not_empty...")
        result = service.require_not_empty("value", "test_field")
        assert result.is_success
        result = service.require_not_empty("", "test_field")
        assert result.is_failure
        result = service.require_not_empty("   ", "test_field")
        assert result.is_failure
        print("   ✓ require_not_empty works")

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)

    asyncio.run(run_tests())
