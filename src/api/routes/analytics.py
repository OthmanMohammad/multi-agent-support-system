"""
Analytics routes - HTTP endpoints for analytics and metrics

"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from src.api.dependencies import get_analytics_service
from src.api.error_handlers import map_error_to_http
from src.services.infrastructure.analytics_service import AnalyticsService
from src.utils.logging.setup import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/analytics/conversations")
async def get_conversation_statistics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get conversation statistics for period"""
    logger.info(
        "get_conversation_statistics_endpoint_called",
        days=days
    )
    
    result = await service.get_conversation_statistics(days=days)
    
    if result.is_failure:
        logger.error(
            "get_conversation_statistics_failed",
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_conversation_statistics_success",
        days=days,
        total_conversations=result.value.get("total_conversations", 0)
    )
    
    return result.value


@router.get("/analytics/agents/{agent_name}")
async def get_agent_performance(
    agent_name: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get performance metrics for specific agent"""
    logger.info(
        "get_agent_performance_endpoint_called",
        agent_name=agent_name,
        days=days
    )
    
    result = await service.get_agent_performance(
        agent_name=agent_name,
        days=days
    )
    
    if result.is_failure:
        logger.error(
            "get_agent_performance_failed",
            agent_name=agent_name,
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_agent_performance_success",
        agent_name=agent_name,
        days=days,
        total_interactions=result.value.get("total_interactions", 0)
    )
    
    return result.value


@router.get("/analytics/agents")
async def get_all_agents_comparison(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Compare performance across all agents"""
    logger.info(
        "get_all_agents_comparison_endpoint_called",
        days=days
    )
    
    result = await service.get_agent_comparison(days=days)
    
    if result.is_failure:
        logger.error(
            "get_all_agents_comparison_failed",
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_all_agents_comparison_success",
        days=days,
        agent_count=len(result.value)
    )
    
    return result.value


@router.get("/analytics/csat")
async def get_customer_satisfaction(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get customer satisfaction metrics based on sentiment"""
    logger.info(
        "get_customer_satisfaction_endpoint_called",
        days=days
    )
    
    result = await service.get_customer_satisfaction_scores(days=days)
    
    if result.is_failure:
        logger.error(
            "get_customer_satisfaction_failed",
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_customer_satisfaction_success",
        days=days,
        avg_sentiment=result.value.get("avg_sentiment", 0)
    )
    
    return result.value


@router.get("/analytics/intents")
async def get_intent_distribution(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get distribution of intents"""
    logger.info(
        "get_intent_distribution_endpoint_called",
        days=days
    )
    
    result = await service.get_intent_distribution(days=days)
    
    if result.is_failure:
        logger.error(
            "get_intent_distribution_failed",
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_intent_distribution_success",
        days=days,
        unique_intents=len(result.value)
    )
    
    return result.value


@router.get("/analytics/resolution-time")
async def get_resolution_time_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get resolution time trends"""
    logger.info(
        "get_resolution_time_trends_endpoint_called",
        days=days
    )
    
    result = await service.get_resolution_time_trends(days=days)
    
    if result.is_failure:
        logger.error(
            "get_resolution_time_trends_failed",
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_resolution_time_trends_success",
        days=days,
        avg_seconds=result.value.get("avg_resolution_seconds", 0)
    )
    
    return result.value


@router.get("/analytics/escalation-rate")
async def get_escalation_rate(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get escalation rate"""
    logger.info(
        "get_escalation_rate_endpoint_called",
        days=days
    )
    
    result = await service.get_escalation_rate(days=days)
    
    if result.is_failure:
        logger.error(
            "get_escalation_rate_failed",
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_escalation_rate_success",
        days=days,
        escalation_rate=result.value.get("escalation_rate", 0)
    )
    
    return result.value


@router.get("/analytics/kb-effectiveness")
async def get_kb_effectiveness(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """Get knowledge base effectiveness metrics"""
    logger.info(
        "get_kb_effectiveness_endpoint_called",
        days=days
    )
    
    result = await service.get_kb_effectiveness(days=days)
    
    if result.is_failure:
        logger.error(
            "get_kb_effectiveness_failed",
            days=days,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "get_kb_effectiveness_success",
        days=days,
        kb_usage_rate=result.value.get("kb_usage_rate", 0)
    )
    
    return result.value