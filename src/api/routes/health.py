"""
Health check routes - System health monitoring

"""
from fastapi import APIRouter, Depends
from datetime import datetime, UTC

from src.api.dependencies import get_analytics_service
from src.services.infrastructure.analytics_service import AnalyticsService
from src.utils.logging.setup import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    
    Returns system status and timestamp
    """
    logger.debug("health_check_endpoint_called")
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "multi-agent-support-system",
        "version": "3.0.0"
    }
    
    logger.debug(
        "health_check_success",
        status=health_status["status"]
    )
    
    return health_status


@router.get("/health/detailed")
async def detailed_health_check(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Detailed health check with component status
    
    Checks:
    - API status
    - Database connectivity
    - Recent activity metrics
    """
    logger.info("detailed_health_check_endpoint_called")
    
    # Get recent conversation stats to verify database connectivity
    stats_result = await service.get_conversation_statistics(days=1)
    
    database_healthy = stats_result.is_success
    
    health_status = {
        "status": "healthy" if database_healthy else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "multi-agent-support-system",
        "version": "3.0.0",
        "components": {
            "api": "healthy",
            "database": "healthy" if database_healthy else "unhealthy",
            "logging": "healthy",
            "middleware": "healthy"
        }
    }
    
    if database_healthy:
        health_status["recent_activity"] = {
            "conversations_24h": stats_result.value.get("total_conversations", 0)
        }
    
    logger.info(
        "detailed_health_check_completed",
        status=health_status["status"],
        database_healthy=database_healthy
    )
    
    return health_status