"""
Result Pattern - Railway Oriented Programming
"""

import traceback as tb
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

__all__ = ["Error", "Result"]

T = TypeVar("T")
U = TypeVar("U")

# Sentinel value to distinguish "not set" from "None"
_UNSET = object()


@dataclass(frozen=True)
class Error:
    """Structured error with code, message, and optional details"""

    code: str
    message: str
    details: dict | None = None
    stacktrace: str | None = field(default=None, repr=False)

    @property
    def user_message(self) -> str:
        return self.message

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details or {}}

    def with_details(self, **kwargs) -> "Error":
        merged_details = {**(self.details or {}), **kwargs}
        return Error(
            code=self.code, message=self.message, details=merged_details, stacktrace=self.stacktrace
        )

    @staticmethod
    def from_exception(exc: Exception, code: str = "INTERNAL_ERROR") -> "Error":
        return Error(
            code=code,
            message=str(exc),
            details={"exception_type": type(exc).__name__},
            stacktrace=tb.format_exc(),
        )

    def __str__(self) -> str:
        details_str = f", details={self.details}" if self.details else ""
        return f"{self.code}: {self.message}{details_str}"


@dataclass(frozen=True)
class Result(Generic[T]):
    """Result of an operation - either success with value or failure with error"""

    _value: object = _UNSET
    _error: object = _UNSET

    def __post_init__(self):
        """Validate that exactly one of value or error is set"""
        has_value = self._value is not _UNSET
        has_error = self._error is not _UNSET

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
        return self._error is _UNSET

    @property
    def is_failure(self) -> bool:
        return self._error is not _UNSET

    @property
    def value(self) -> T:
        if self.is_failure:
            raise ValueError(f"Cannot get value from failed result. Error: {self._error}")
        return self._value

    @property
    def error(self) -> Error:
        if self.is_success:
            raise ValueError(f"Cannot get error from successful result. Value: {self._value}")
        return self._error

    @staticmethod
    def ok(value: T) -> "Result[T]":
        """Create a successful result"""
        return Result(_value=value)

    @staticmethod
    def fail(error: Error) -> "Result[T]":
        """Create a failed result"""
        return Result(_error=error)

    def map(self, func: Callable[[T], U]) -> "Result[U]":
        if self.is_failure:
            return Result.fail(self._error)
        try:
            new_value = func(self._value)
            return Result.ok(new_value)
        except Exception as e:
            return Result.fail(Error.from_exception(e, code="TRANSFORMATION_ERROR"))

    def bind(self, func: Callable[[T], "Result[U]"]) -> "Result[U]":
        if self.is_failure:
            return Result.fail(self._error)
        try:
            return func(self._value)
        except Exception as e:
            return Result.fail(Error.from_exception(e, code="OPERATION_ERROR"))

    def map_error(self, func: Callable[[Error], Error]) -> "Result[T]":
        if self.is_success:
            return Result.ok(self._value)
        try:
            new_error = func(self._error)
            return Result.fail(new_error)
        except Exception:
            return Result.fail(self._error)

    def or_else(self, default: T) -> T:
        return self._value if self.is_success else default

    def or_else_get(self, func: Callable[[Error], T]) -> T:
        return self._value if self.is_success else func(self._error)

    def unwrap(self) -> T:
        if self.is_failure:
            raise RuntimeError(f"Result unwrap failed: {self._error}")
        return self._value

    def expect(self, message: str) -> T:
        if self.is_failure:
            raise RuntimeError(f"{message}: {self._error}")
        return self._value

    def __bool__(self) -> bool:
        return self.is_success

    def __repr__(self) -> str:
        if self.is_success:
            return f"Result.ok({self._value!r})"
        return f"Result.fail({self._error!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Result):
            return False
        return self._value == other._value and self._error == other._error
