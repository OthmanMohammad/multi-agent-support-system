"""
Health routes - System health and status endpoints

Provides health checks for monitoring and load balancers.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import time

from api.dependencies import get_uow
from database.unit_of_work import UnitOfWork

router = APIRouter()

# Track startup time for uptime calculation
_startup_time = time.time()


@router.get("/health")
async def health_check():
    """
    Basic health check
    
    Returns 200 if service is running.
    Use this for load balancer health checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed")
async def detailed_health_check(
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Detailed health check with component status
    
    Checks:
    - Database connectivity
    - Service availability
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - _startup_time),
        "components": {}
    }
    
    # Check database
    try:
        # Try a simple query
        await uow.customers.get_all(limit=1)
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check vector store (optional)
    try:
        from vector_store import VectorStore
        vs = VectorStore()
        health_status["components"]["vector_store"] = "healthy"
    except Exception:
        health_status["components"]["vector_store"] = "unavailable"
    
    return health_status


@router.get("/metrics")
async def get_metrics(
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Basic system metrics
    
    For Prometheus integration, use a proper metrics library.
    """
    # Get basic stats
    try:
        stats = await uow.conversations.get_statistics(days=1)
        
        return {
            "uptime_seconds": int(time.time() - _startup_time),
            "conversations_today": stats.get("total_conversations", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }