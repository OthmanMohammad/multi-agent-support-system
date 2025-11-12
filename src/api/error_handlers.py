"""
Global Error Handlers for FastAPI

This module provides centralized error handling for the API:
- Maps domain errors to HTTP exceptions
- Captures internal errors in Sentry (Phase 2)
- Handles validation errors
- Catches unexpected exceptions
- Provides consistent error response format

All errors return JSON in this format:
{
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}  // Optional additional context
}
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

import sentry_sdk

from core.result import Error
from core.errors import ErrorCodes
from utils.logging.setup import get_logger


# Get logger for this module
logger = get_logger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """
    Register global error handlers with FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        Handle standard HTTP exceptions
        
        These are typically raised by FastAPI itself (404, 405, etc.)
        """
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {}
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors
        
        These occur when request body/query params don't match expected schema
        """
        logger.warning(
            "validation_error",
            errors=exc.errors(),
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": exc.errors()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for unexpected exceptions
        
        This captures any exception not handled by other handlers.
        All unexpected exceptions are sent to Sentry for tracking.
        """
        # Log the error
        logger.error(
            "unexpected_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            method=request.method,
            exc_info=True
        )
        
        # Capture in Sentry (Phase 2)
        sentry_sdk.capture_exception(exc)
        
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )


def map_error_to_http(error: Error) -> HTTPException:
    """
    Map domain Error to HTTP exception
    
    This function converts our domain Error objects (from Result pattern)
    into FastAPI HTTPException objects with appropriate status codes.
    
    Internal errors are automatically captured in Sentry for tracking.
    
    Args:
        error: Domain Error object from Result.fail()
    
    Returns:
        HTTPException with appropriate status code
    
    Raises:
        HTTPException: Always raises to trigger FastAPI error handling
    
    Example:
        result = customer_service.create_customer(email)
        if result.is_failure:
            raise map_error_to_http(result.error)
    """
    # Capture internal errors in Sentry (Phase 2)
    if error.code == ErrorCodes.INTERNAL_ERROR:
        # Log the internal error
        logger.error(
            "internal_error_captured",
            error_code=error.code,
            error_message=error.message,
            error_details=error.details
        )
        
        # Capture in Sentry with full context
        sentry_sdk.capture_exception(
            Exception(error.message),
            extras={
                "error_code": error.code,
                "error_message": error.message,
                "error_details": error.details,
                "stacktrace": error.stacktrace,
            }
        )
    
    # Map error codes to HTTP status codes
    status_codes = {
        ErrorCodes.VALIDATION_ERROR: 400,
        ErrorCodes.BUSINESS_RULE_VIOLATION: 400,
        ErrorCodes.NOT_FOUND: 404,
        ErrorCodes.CONFLICT: 409,
        ErrorCodes.AUTHORIZATION_ERROR: 403,
        ErrorCodes.RATE_LIMIT_EXCEEDED: 429,
        ErrorCodes.INTERNAL_ERROR: 500,
        ErrorCodes.EXTERNAL_SERVICE_ERROR: 503,
    }
    
    status_code = status_codes.get(error.code, 500)
    
    # Log the error mapping
    logger.debug(
        "error_mapped_to_http",
        error_code=error.code,
        status_code=status_code,
        message=error.message
    )
    
    # Create and raise HTTP exception
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "details": error.details or {}
        }
    )


# Convenience function for routes
def handle_result(result):
    """
    Handle a Result object in route handlers
    
    If Result is success, returns the value.
    If Result is failure, raises mapped HTTP exception.
    
    Args:
        result: Result object from service call
    
    Returns:
        result.value if successful
    
    Raises:
        HTTPException: If result is failure
    
    Example:
        @router.post("/customers")
        async def create_customer(data: CustomerCreate):
            result = await customer_service.create(data.email)
            return handle_result(result)
    """
    if result.is_failure:
        raise map_error_to_http(result.error)
    return result.value