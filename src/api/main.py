"""
FastAPI Application - REST API for multi-agent support system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from api.routes import conversations, customers, health, analytics
from api.error_handlers import setup_error_handlers

# Import initialization functions
from utils.logging.setup import setup_logging
from utils.monitoring.sentry_config import init_sentry
from database.connection import init_db, close_db


# Create FastAPI application
app = FastAPI(
    title="Multi-Agent Support System",
    version="1.0.0",
    description="AI-powered customer support system with multi-agent orchestration",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


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
    1. Logging (Phase 1) - Must be first so other services can log
    2. Sentry (Phase 2) - Captures errors during startup
    3. Database - Required for API operations
    """
    print("🚀 Starting Multi-Agent Support System v3.0...")
    
    # Phase 1: Initialize structured logging
    print("📝 Initializing structured logging...")
    setup_logging()
    print("✓ Logging initialized")
    
    # Phase 2: Initialize Sentry error tracking
    print("📊 Initializing Sentry monitoring...")
    init_sentry()
    print("✓ Sentry monitoring ready")
    
    # Initialize database
    print("💾 Initializing database connection...")
    await init_db()
    print("✓ Database connected")
    
    print("✅ API ready to accept requests!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown
    """
    print("👋 Shutting down Multi-Agent Support System...")
    
    # Close database connections
    print("💾 Closing database connections...")
    await close_db()
    print("✓ Database connections closed")
    
    print("✅ Shutdown complete")


@app.get("/")
async def root():
    """
    Root endpoint - API status
    
    Returns:
        API information and status
    """
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