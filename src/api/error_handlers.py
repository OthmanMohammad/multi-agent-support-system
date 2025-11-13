"""
Global Error Handlers for FastAPI

This module provides centralized error handling for the API:
- Maps domain errors to HTTP exceptions
- Captures internal errors in Sentry (Phase 2)
- Enriches exceptions with context (Phase 4)
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

from src.core.result import Error
from src.core.errors import ErrorCodes
from src.utils.logging.setup import get_logger
from src.utils.logging.context import get_correlation_id
from src.utils.exceptions import enrich_exception, get_exception_context


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
        
        Phase 4 Enhancement: Added correlation ID logging and response header
        """
        correlation_id = get_correlation_id()
        
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
            correlation_id=correlation_id,
        )
        
        # Create response
        response = JSONResponse(
            status_code=exc.status_code,
            content={
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {}
            }
        )
        
        # Add correlation ID to response headers
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """
        Handle Pydantic validation errors
        
        These occur when request body/query params don't match expected schema
        
        Phase 4 Enhancement: Added correlation ID and context enrichment
        """
        correlation_id = get_correlation_id()
        
        # Enrich the exception
        enrich_exception(exc)
        
        logger.warning(
            "validation_error",
            errors=exc.errors(),
            path=request.url.path,
            method=request.method,
            correlation_id=correlation_id,
        )
        
        # Create response
        response = JSONResponse(
            status_code=400,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": exc.errors()
                }
            }
        )
        
        # Add correlation ID to response headers
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """
        Catch-all handler for unexpected exceptions
        
        This captures any exception not handled by other handlers.
        All unexpected exceptions are sent to Sentry for tracking.
        
        Phase 4 Enhancement: Added automatic enrichment and context extraction
        """
        # Enrich exception with context
        enrich_exception(exc)
        
        # Get enriched context
        context = get_exception_context(exc)
        
        # Log the error with full context
        logger.error(
            "unexpected_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            method=request.method,
            **context,
            exc_info=True
        )
        
        # Capture in Sentry with enriched context
        sentry_sdk.capture_exception(exc)
        
        # Create response
        response = JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )
        
        # Add correlation ID to response headers
        correlation_id = context.get("correlation_id")
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        
        return response


def map_error_to_http(error: Error) -> HTTPException:
    """
    Map domain Error to HTTP exception
    
    This function converts our domain Error objects (from Result pattern)
    into FastAPI HTTPException objects with appropriate status codes.
    
    Internal errors are automatically captured in Sentry for tracking.
    
    Phase 4 Enhancement: Added enrichment and better context logging
    
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
    correlation_id = get_correlation_id()
    
    # Log error with correlation ID and context
    logger.error(
        "error_mapped_to_http",
        error_code=error.code,
        error_message=error.message,
        error_details=error.details,
        correlation_id=correlation_id,
    )
    
    # Capture internal errors in Sentry with full context
    if error.code == ErrorCodes.INTERNAL_ERROR:
        # Create an exception from the Error for Sentry
        # This gives Sentry a proper exception to track
        internal_exc = Exception(error.message)
        
        # Enrich it with context
        enrich_exception(internal_exc)
        
        # Capture in Sentry with extra context
        sentry_sdk.capture_exception(
            internal_exc,
            extras={
                "error_code": error.code,
                "error_message": error.message,
                "error_details": error.details,
                "stacktrace": error.stacktrace,
                "correlation_id": correlation_id,
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
    
    # Create HTTP exception
    http_exc = HTTPException(
        status_code=status_code,
        detail={
            "code": error.code,
            "message": error.message,
            "details": error.details or {}
        }
    )
    
    # Enrich the HTTP exception too
    enrich_exception(http_exc)
    
    logger.debug(
        "error_mapped_to_http",
        error_code=error.code,
        status_code=status_code,
        message=error.message
    )
    
    raise http_exc


# Convenience function for routes
def handle_result(result):
    """
    Handle a Result object in route handlers
    
    If Result is success, returns the value.
    If Result is failure, raises mapped HTTP exception.
    
    Phase 4 Enhancement: Added enrichment to raised exceptions
    
    Args:
        result: Result object from service call
    
    Returns:
        result.value if successful
    
    Raises:
        HTTPException: If result is failure (with enrichment)
    
    Example:
        @router.post("/customers")
        async def create_customer(data: CustomerCreate):
            result = await customer_service.create(data.email)
            return handle_result(result)
    """
    if result.is_failure:
        raise map_error_to_http(result.error)
    return result.value