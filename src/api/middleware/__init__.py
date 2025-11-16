"""
API Middleware - Request/Response processing middleware

This package contains FastAPI middleware for:
- Correlation ID generation and propagation
- Request/Response logging with structured logging
- Performance timing
- Rate limiting (per user/IP/API key)
- Security headers (XSS, clickjacking, etc.)
- CORS security
"""

from src.api.middleware.correlation_middleware import CorrelationMiddleware
from src.api.middleware.logging_middleware import LoggingMiddleware
from src.api.middleware.rate_limit_middleware import RateLimitMiddleware
from src.api.middleware.security_middleware import (
    SecurityHeadersMiddleware,
    CORSSecurityMiddleware
)

__all__ = [
    "CorrelationMiddleware",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "CORSSecurityMiddleware",
]