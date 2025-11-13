"""
API Middleware - Request/Response processing middleware

This package contains FastAPI middleware for:
- Correlation ID generation and propagation
- Request/Response logging with structured logging
- Performance timing
"""

from src.api.middleware.correlation_middleware import CorrelationMiddleware
from src.api.middleware.logging_middleware import LoggingMiddleware

__all__ = [
    "CorrelationMiddleware",
    "LoggingMiddleware",
]