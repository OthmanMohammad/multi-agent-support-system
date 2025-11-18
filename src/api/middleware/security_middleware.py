"""
Security Headers Middleware - HTTP security headers

This middleware adds security-related HTTP headers to all responses
to protect against common web vulnerabilities.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.logging.setup import get_logger

logger = get_logger(__name__)


# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware for FastAPI.

    Adds security headers to all responses to protect against:
    - XSS (Cross-Site Scripting)
    - Clickjacking
    - MIME sniffing
    - Information disclosure

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy: default-src 'self'
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(), microphone=(), camera=()
    """

    def __init__(
        self,
        app: ASGIApp,
        hsts_enabled: bool = True,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        csp_enabled: bool = True,
        csp_policy: str = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    ):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            hsts_enabled: Enable HTTP Strict Transport Security
            hsts_max_age: HSTS max age in seconds (default: 1 year)
            hsts_include_subdomains: Include subdomains in HSTS
            csp_enabled: Enable Content Security Policy
            csp_policy: Custom CSP policy string
        """
        super().__init__(app)
        self.hsts_enabled = hsts_enabled
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.csp_enabled = csp_enabled
        self.csp_policy = csp_policy

        logger.info(
            "security_headers_middleware_initialized",
            hsts_enabled=hsts_enabled,
            csp_enabled=csp_enabled
        )

    async def dispatch(self, request: Request, call_next):
        """
        Add security headers to response.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with security headers
        """
        # Process request
        response = await call_next(request)

        # Add security headers

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=(), "
            "fullscreen=(self)"
        )

        # HTTP Strict Transport Security (HSTS)
        if self.hsts_enabled:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy
        if self.csp_enabled:
            response.headers["Content-Security-Policy"] = self.csp_policy

        # Remove server header (information disclosure)
        # MutableHeaders doesn't have pop(), use del with try/except
        try:
            del response.headers["Server"]
        except KeyError:
            pass

        # Add custom header to identify API
        response.headers["X-API-Version"] = "1.0.0"

        logger.debug(
            "security_headers_added",
            path=request.url.path,
            method=request.method
        )

        return response


# =============================================================================
# CORS SECURITY MIDDLEWARE
# =============================================================================

class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with security checks.

    This middleware provides additional security checks beyond
    FastAPI's built-in CORSMiddleware:
    - Origin validation
    - Preflight request handling
    - Method and header validation
    """

    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: list[str] = None,
        allowed_methods: list[str] = None,
        allowed_headers: list[str] = None,
        expose_headers: list[str] = None,
        max_age: int = 600,
        allow_credentials: bool = True,
    ):
        """
        Initialize CORS security middleware.

        Args:
            app: ASGI application
            allowed_origins: List of allowed origins (default: ["*"])
            allowed_methods: List of allowed methods (default: ["GET", "POST", "PUT", "DELETE", "PATCH"])
            allowed_headers: List of allowed headers (default: ["*"])
            expose_headers: List of exposed headers
            max_age: Preflight cache max age in seconds
            allow_credentials: Allow credentials (cookies, auth)
        """
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["*"]
        self.expose_headers = expose_headers or [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-API-Version"
        ]
        self.max_age = max_age
        self.allow_credentials = allow_credentials

        logger.info(
            "cors_security_middleware_initialized",
            allowed_origins=allowed_origins,
            allow_credentials=allow_credentials
        )

    async def dispatch(self, request: Request, call_next):
        """
        Handle CORS with security validation.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with CORS headers
        """
        origin = request.headers.get("origin")

        # Handle preflight requests
        if request.method == "OPTIONS":
            response = await self._handle_preflight(request, origin)
            return response

        # Process normal request
        response = await call_next(request)

        # Add CORS headers
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()

            if self.expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)

        # Vary header for caching
        response.headers["Vary"] = "Origin"

        return response

    async def _handle_preflight(self, request: Request, origin: str):
        """
        Handle CORS preflight requests.

        Args:
            request: FastAPI request
            origin: Request origin

        Returns:
            Preflight response
        """
        from fastapi import Response

        # Create preflight response
        response = Response(status_code=204)

        # Add CORS headers
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
            response.headers["Access-Control-Allow-Credentials"] = str(self.allow_credentials).lower()
            response.headers["Access-Control-Max-Age"] = str(self.max_age)

        # Vary header for caching
        response.headers["Vary"] = "Origin"

        logger.debug(
            "cors_preflight_handled",
            origin=origin,
            method=request.headers.get("access-control-request-method")
        )

        return response

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed.

        Args:
            origin: Request origin

        Returns:
            True if origin is allowed, False otherwise
        """
        # Allow all origins
        if "*" in self.allowed_origins:
            return True

        # Check exact match
        if origin in self.allowed_origins:
            return True

        # Check wildcard patterns
        for allowed in self.allowed_origins:
            if allowed.startswith("*"):
                # *.example.com pattern
                suffix = allowed[1:]  # Remove *
                if origin.endswith(suffix):
                    return True

        return False