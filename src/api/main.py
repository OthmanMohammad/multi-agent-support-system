"""
FastAPI Application - REST API for multi-agent support system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api.routes import api_router
from api.error_handlers import register_error_handlers
from database.connection import init_db, close_db
from utils.logging import setup_logging, get_logger  # NEW

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Customer Support API",
    description="Production-ready multi-agent support system with clean architecture",
    version="3.0.0"
)

# CORS (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # NEW: Initialize structured logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("application_starting", version="3.0.0")
    logger.info("initializing_database")
    
    await init_db()
    
    logger.info("application_ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger = get_logger(__name__)
    logger.info("application_shutting_down")
    
    await close_db()
    
    logger.info("application_shutdown_complete")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Multi-Agent Customer Support API",
        "version": "3.0.0",
        "architecture": "Clean Architecture with Application Services",
        "docs": "/docs",
        "health": "/health"
    }


# Register all routes
app.include_router(api_router)

# Register error handlers
register_error_handlers(app)


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("Multi-Agent Support API v3.0")
    print("=" * 70)
    print("NEW: Clean Architecture + Structured Logging")
    print("  ✓ Application Services (orchestration)")
    print("  ✓ Domain Services (business logic)")
    print("  ✓ Infrastructure Services (data access)")
    print("  ✓ Structured logging with correlation IDs")
    print("  ✓ PII masking for compliance")
    print("=" * 70)
    print("Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )