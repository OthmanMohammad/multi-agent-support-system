"""
FastAPI Application - REST API for multi-agent support system

Configured with:
- Structured logging with structlog
- Sentry error monitoring
- Enhanced exception handling
- Request/response logging middleware
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from api.routes import conversations, customers, health, analytics
from api.error_handlers import setup_error_handlers

# Import middleware (Phase 5)
from api.middleware import CorrelationMiddleware, LoggingMiddleware

# Import initialization functions
from utils.logging.setup import setup_logging, get_logger
from utils.monitoring.sentry_config import init_sentry
from database.connection import init_db, close_db


# Initialize logger for this module
logger = get_logger(__name__)


# Create FastAPI application
app = FastAPI(
    title="Multi-Agent Support System",
    version="1.0.0",
    description="AI-powered customer support system with multi-agent orchestration",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


# Add correlation ID middleware (MUST be first to set context)
app.add_middleware(CorrelationMiddleware)

# Add logging middleware (MUST be after correlation middleware)
app.add_middleware(LoggingMiddleware, log_body=False)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    1. Logging - Must be first so other services can log
    2. Sentry - Captures errors during startup
    3. Database - Required for API operations
    """
    logger.info(
        "application_startup_initiated",
        version="3.0.0",
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
    
    logger.info(
        "application_startup_completed",
        status="ready",
        message="Multi-Agent Support System v3.0 ready to accept requests"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown
    """
    logger.info("application_shutdown_initiated")
    
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
        "version": "3.0.0",
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
        "message": "Multi-Agent Support System API v3.0",
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
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )