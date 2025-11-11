"""
Analytics routes - HTTP endpoints for system metrics

Provides statistics and metrics for monitoring and dashboards.
"""

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_analytics_service
from api.error_handlers import map_error_to_http
from services.infrastructure.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/conversations")
async def get_conversation_statistics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get conversation statistics for period"""
    result = await service.get_conversation_statistics(days=days)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/agents/{agent_name}")
async def get_agent_performance(
    agent_name: str,
    days: int = Query(7, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get performance metrics for specific agent"""
    result = await service.get_agent_performance(
        agent_name=agent_name,
        days=days
    )
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/agents")
async def get_agent_comparison(
    days: int = Query(7, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Compare performance across all agents"""
    result = await service.get_agent_comparison(days=days)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/intents")
async def get_intent_distribution(
    days: int = Query(7, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get distribution of intents"""
    result = await service.get_intent_distribution(days=days)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/resolution-times")
async def get_resolution_time_trends(
    days: int = Query(7, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get resolution time trends"""
    result = await service.get_resolution_time_trends(days=days)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/escalation-rate")
async def get_escalation_rate(
    days: int = Query(7, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get escalation rate statistics"""
    result = await service.get_escalation_rate(days=days)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/kb-effectiveness")
async def get_kb_effectiveness(
    days: int = Query(7, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get knowledge base effectiveness metrics"""
    result = await service.get_kb_effectiveness(days=days)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value


@router.get("/satisfaction")
async def get_customer_satisfaction(
    days: int = Query(30, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get customer satisfaction metrics"""
    result = await service.get_customer_satisfaction_scores(days=days)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return result.value