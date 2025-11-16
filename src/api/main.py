"""
FastAPI Application - REST API for multi-agent support system

Configured with:
- Structured logging with structlog
- Sentry error monitoring
- Enhanced exception handling
- Request/response logging middleware
- Centralized configuration management
- Environment-based settings validation
- JWT & API key authentication
- RBAC authorization
- Rate limiting with Redis
- Security headers
"""

from fastapi import FastAPI

# Import routes
from src.api.routes import conversations, customers, health, analytics, auth, agents, workflows, oauth
from src.api.error_handlers import setup_error_handlers

# Import middleware
from src.api.middleware import (
    CorrelationMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    CORSSecurityMiddleware
)

# Import initialization functions
from src.utils.logging.setup import setup_logging, get_logger
from src.utils.monitoring.sentry_config import init_sentry
from src.database.connection import init_db, close_db
from src.api.auth import get_redis_client, close_redis_client

# Import configuration
from src.core.config import get_settings
from src.core.config_validator import require_valid_configuration


# Initialize logger for this module
logger = get_logger(__name__)

# Load configuration
settings = get_settings()


# Create FastAPI application
app = FastAPI(
    title=settings.api.title,
    version=settings.api.version,
    description="AI-powered customer support system with multi-agent orchestration",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


# =============================================================================
# MIDDLEWARE STACK (ORDER MATTERS!)
# =============================================================================
# Middleware execution order (reverse of addition order):
# 1. CORS Security (first to handle preflight)
# 2. Security Headers
# 3. Rate Limiting
# 4. Logging
# 5. Correlation ID (innermost, sets context for all)

# Add correlation ID middleware (MUST be first to set context)
app.add_middleware(CorrelationMiddleware)

# Add logging middleware (MUST be after correlation middleware)
app.add_middleware(LoggingMiddleware, log_body=False)

# Add rate limiting middleware (Redis-based)
app.add_middleware(RateLimitMiddleware)

# Add security headers middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    hsts_enabled=True,
    hsts_max_age=31536000,
    hsts_include_subdomains=True,
    csp_enabled=True,
    csp_policy="default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
)

# Configure CORS security middleware
app.add_middleware(
    CORSSecurityMiddleware,
    allowed_origins=settings.api.cors_origins,
    allowed_methods=settings.api.cors_methods,
    allowed_headers=settings.api.cors_headers,
    allow_credentials=settings.api.cors_credentials,
    max_age=600,
)


# Setup error handlers
setup_error_handlers(app)


# =============================================================================
# API ROUTES
# =============================================================================

# Health check (no auth required)
app.include_router(health.router, prefix="/api", tags=["Health"])

# Authentication & user management
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(oauth.router, prefix="/api", tags=["OAuth"])

# Agent execution & workflow orchestration
app.include_router(agents.router, prefix="/api", tags=["Agents"])
app.include_router(workflows.router, prefix="/api", tags=["Workflows"])

# Core business endpoints
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(customers.router, prefix="/api", tags=["Customers"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])


@app.on_event("startup")
async def startup_event():
    """
    Initialize services on application startup

    Initialization order is critical:
    0. Configuration validation - Fail fast if config invalid
    1. Logging - Must be first so other services can log
    2. Sentry - Captures errors during startup
    3. Database - Required for API operations
    4. Redis - Required for rate limiting, caching, token blacklist
    """
    # CRITICAL: Validate configuration first (fail-fast)
    require_valid_configuration()

    logger.info(
        "application_startup_initiated",
        environment=settings.environment,
        version=settings.app_version,
        phase="startup"
    )

    # Initialize structured logging
    logger.info("logging_initialization_started")
    setup_logging()
    logger.info("logging_initialized")

    # Initialize Sentry error tracking
    logger.info("sentry_initialization_started")
    init_sentry()
    logger.info("sentry_initialized")

    # Initialize database
    logger.info("database_initialization_started")
    await init_db()
    logger.info("database_initialized")

    # Initialize Redis connection
    logger.info("redis_initialization_started")
    redis_client = await get_redis_client()
    logger.info(
        "redis_initialized",
        host=settings.redis.host,
        port=settings.redis.port,
        rate_limiting_enabled=settings.redis.rate_limit_enabled
    )

    # Log CORS configuration
    logger.info(
        "cors_configuration",
        allowed_origins=settings.api.cors_origins,
        origin_count=len(settings.api.cors_origins),
        allows_credentials=settings.api.cors_credentials
    )

    # Log authentication configuration
    logger.info(
        "authentication_configuration",
        jwt_algorithm=settings.jwt.algorithm,
        access_token_expire_minutes=settings.jwt.access_token_expire_minutes,
        refresh_token_expire_days=settings.jwt.refresh_token_expire_days
    )

    logger.info(
        "application_startup_completed",
        environment=settings.environment,
        status="ready",
        message=f"Multi-Agent Support System v{settings.app_version} ready to accept requests"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown
    """
    logger.info(
        "application_shutdown_initiated",
        environment=settings.environment
    )

    # Close Redis connection
    logger.info("redis_shutdown_started")
    await close_redis_client()
    logger.info("redis_connection_closed")

    # Close database connections
    logger.info("database_shutdown_started")
    await close_db()
    logger.info("database_connections_closed")

    logger.info(
        "application_shutdown_completed",
        message="Shutdown complete"
    )


@app.get("/")
async def root():
    """
    Root endpoint - API status
    
    Returns:
        API information and status
    """
    logger.debug("root_endpoint_accessed")
    
    return {
        "name": "Multi-Agent Support System",
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
        "docs": "/api/docs",
        "health": "/api/health"
    }


@app.get("/api")
async def api_root():
    """
    API root endpoint

    Returns:
        Available API endpoints
    """
    logger.debug("api_root_endpoint_accessed")

    return {
        "message": f"Multi-Agent Support System API v{settings.app_version}",
        "environment": settings.environment,
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/auth",
            "agents": "/api/agents",
            "workflows": "/api/workflows",
            "conversations": "/api/conversations",
            "customers": "/api/customers",
            "analytics": "/api/analytics",
            "docs": "/api/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=True,
        log_level="info"
    )