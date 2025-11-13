"""
Request/Response Logging Middleware

Automatically logs:
- Request: method, path, query params, client IP, headers (filtered)
- Response: status code, duration, size
- Errors: exception details with full context

This gives complete visibility into API traffic with structured logging.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

from src.utils.logging.setup import get_logger
from src.utils.logging.context import get_correlation_id


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging
    
    Logs every request/response with:
    - Timing information
    - Status codes
    - Client information
    - Correlation IDs
    - Error details
    
    """
    
    def __init__(self, app, log_body: bool = False):
        """
        Initialize logging middleware
        
        Args:
            app: FastAPI application
            log_body: Whether to log request/response bodies (default: False for security)
        """
        super().__init__(app)
        self.logger = get_logger(__name__)
        self.log_body = log_body
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process request with logging
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Start timing
        start_time = time.time()
        
        # Log request start
        self.logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            correlation_id=get_correlation_id()
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            self.logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                correlation_id=get_correlation_id()
            )
            
            # Add correlation ID to response headers (redundant with CorrelationMiddleware, but safe)
            if corr_id := get_correlation_id():
                response.headers["X-Correlation-ID"] = corr_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=get_correlation_id(),
                exc_info=True
            )
            
            # Re-raise to let error handlers deal with it
            raise