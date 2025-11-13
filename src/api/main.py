"""
FastAPI Application - REST API for multi-agent support system

Configured with:
- Structured logging with structlog
- Sentry error monitoring
- Enhanced exception handling
- Request/response logging middleware
- Centralized configuration management
- Environment-based settings validation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from src.api.routes import conversations, customers, health, analytics
from src.api.error_handlers import setup_error_handlers

# Import middleware
from src.api.middleware import CorrelationMiddleware, LoggingMiddleware

# Import initialization functions
from src.utils.logging.setup import setup_logging, get_logger
from src.utils.monitoring.sentry_config import init_sentry
from src.database.connection import init_db, close_db

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


# Add correlation ID middleware (MUST be first to set context)
app.add_middleware(CorrelationMiddleware)

# Add logging middleware (MUST be after correlation middleware)
app.add_middleware(LoggingMiddleware, log_body=False)

# Configure CORS with validated origins from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=settings.api.cors_credentials,
    allow_methods=settings.api.cors_methods,
    allow_headers=settings.api.cors_headers,
)


# Setup error handlers
setup_error_handlers(app)


# Include API routes
app.include_router(health.router, prefix="/api", tags=["Health"])
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
    
    # Log CORS configuration
    logger.info(
        "cors_configuration",
        allowed_origins=settings.api.cors_origins,
        origin_count=len(settings.api.cors_origins),
        allows_credentials=settings.api.cors_credentials
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