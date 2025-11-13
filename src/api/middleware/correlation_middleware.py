"""
Correlation ID Middleware

Handles correlation ID lifecycle:
1. Check if request has X-Correlation-ID header
2. If yes, use it; if no, generate new one
3. Store in context for entire request
4. Include in response headers

This enables end-to-end request tracing across all layers.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

from src.utils.logging.context import set_correlation_id, generate_correlation_id


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for correlation ID management
    
    Automatically handles correlation ID for every request:
    - Extracts from X-Correlation-ID or X-Request-ID headers
    - Generates new ID if none provided
    - Stores in async-safe context for entire request
    - Adds to response headers
    
    This enables tracing requests through all layers of the application.
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process request and inject correlation ID
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response with correlation ID header
        """
        # Extract or generate correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID") or
            request.headers.get("X-Request-ID") or
            generate_correlation_id()
        )
        
        # Set in async-safe context (available to entire request)
        set_correlation_id(correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Ensure correlation ID in response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response