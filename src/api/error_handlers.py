"""
Error handlers - Map Result objects to HTTP responses

Converts domain errors (from Result.fail()) into appropriate
HTTP exceptions with proper status codes and error formatting.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR
)

from core.result import Error


def map_error_to_http(error: Error) -> HTTPException:
    """
    Map domain Error to HTTP exception
    
    This is the bridge between domain layer (Result/Error) and
    HTTP layer (status codes, JSON responses).
    
    Args:
        error: Domain error from Result.fail()
        
    Returns:
        HTTPException with appropriate status code
        
    Example:
        result = await service.create_customer(email)
        if result.is_failure:
            raise map_error_to_http(result.error)
    """
    # Error code → HTTP status mapping
    status_codes = {
        "VALIDATION_ERROR": HTTP_400_BAD_REQUEST,
        "NOT_FOUND": HTTP_404_NOT_FOUND,
        "BUSINESS_RULE_VIOLATION": HTTP_400_BAD_REQUEST,
        "AUTHORIZATION_ERROR": HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": HTTP_403_FORBIDDEN,
        "CONFLICT": HTTP_409_CONFLICT,
        "RATE_LIMIT_EXCEEDED": HTTP_429_TOO_MANY_REQUESTS,
        "INTERNAL_ERROR": HTTP_500_INTERNAL_SERVER_ERROR,
        "EXTERNAL_SERVICE_ERROR": HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    # Get status code (default to 500 for unknown errors)
    status_code = status_codes.get(error.code, HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Format error response
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": error.code,
            "message": error.message,
            "details": error.details or {}
        }
    )


def register_error_handlers(app):
    """
    Register all error handlers with FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Catch-all for unexpected exceptions
        
        This ensures no uncaught exceptions leak to the user.
        All errors are formatted consistently.
        """
        # Log the full error server-side
        import traceback
        print(f"Unhandled exception: {exc}")
        traceback.print_exc()
        
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handle FastAPI HTTPExceptions
        
        Ensures consistent error format even for HTTP exceptions.
        """
        # If detail is already a dict (from map_error_to_http), use it
        if isinstance(exc.detail, dict):
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.detail
            )
        
        # Otherwise, wrap in standard format
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": "HTTP_ERROR",
                "message": str(exc.detail),
                "details": {}
            }
        )