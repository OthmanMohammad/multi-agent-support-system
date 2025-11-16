"""
Analytics Pydantic Models - Enhanced

Comprehensive analytics and metrics models for system-wide reporting.
"""

from typing import List, Optional, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field


# =============================================================================
# SYSTEM OVERVIEW
# =============================================================================

class SystemOverviewResponse(BaseModel):
    """High-level system metrics"""

    # Conversations
    total_conversations: int
    active_conversations: int
    conversations_today: int
    avg_response_time_seconds: float

    # Customers
    total_customers: int
    active_customers: int
    new_customers_today: int

    # Agents
    total_agent_executions_today: int
    avg_agent_execution_time: float
    agent_success_rate: float = Field(..., ge=0.0, le=100.0)

    # System health
    api_uptime_percentage: float = Field(..., ge=0.0, le=100.0)
    error_rate: float = Field(..., ge=0.0, le=100.0)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "total_conversations": 15847,
                "active_conversations": 234,
                "conversations_today": 412,
                "avg_response_time_seconds": 2.3,
                "total_customers": 1542,
                "active_customers": 1489,
                "new_customers_today": 12,
                "total_agent_executions_today": 1847,
                "avg_agent_execution_time": 2.1,
                "agent_success_rate": 96.8,
                "api_uptime_percentage": 99.9,
                "error_rate": 0.3
            }]
        }
    }


# =============================================================================
# TIME SERIES DATA
# =============================================================================

class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series"""

    timestamp: datetime
    value: float
    label: Optional[str] = None


class TimeSeriesResponse(BaseModel):
    """Time series analytics data"""

    metric_name: str
    metric_unit: str = Field(..., description="count, seconds, percentage, etc.")
    time_period: str = Field(..., description="1h, 24h, 7d, 30d")
    data_points: List[TimeSeriesDataPoint]
    total: Optional[float] = None
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "metric_name": "conversation_volume",
                "metric_unit": "count",
                "time_period": "24h",
                "data_points": [
                    {"timestamp": "2025-11-16T00:00:00Z", "value": 42},
                    {"timestamp": "2025-11-16T01:00:00Z", "value": 38},
                    {"timestamp": "2025-11-16T02:00:00Z", "value": 31}
                ],
                "total": 412,
                "average": 17.2,
                "min_value": 8,
                "max_value": 45
            }]
        }
    }


# =============================================================================
# BREAKDOWN ANALYTICS
# =============================================================================

class BreakdownItem(BaseModel):
    """Single item in a breakdown"""

    category: str
    count: int
    percentage: float = Field(..., ge=0.0, le=100.0)


class BreakdownResponse(BaseModel):
    """Categorical breakdown analytics"""

    metric_name: str
    breakdown_by: str = Field(..., description="status, plan, agent, etc.")
    items: List[BreakdownItem]
    total: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "metric_name": "conversations",
                "breakdown_by": "status",
                "items": [
                    {"category": "open", "count": 234, "percentage": 15.2},
                    {"category": "resolved", "count": 1289, "percentage": 83.5},
                    {"category": "escalated", "count": 19, "percentage": 1.2}
                ],
                "total": 1542
            }]
        }
    }


# =============================================================================
# PERFORMANCE METRICS
# =============================================================================

class PerformanceMetrics(BaseModel):
    """System performance metrics"""

    # Response times (in seconds)
    avg_api_response_time: float
    p50_api_response_time: float
    p95_api_response_time: float
    p99_api_response_time: float

    # Agent performance
    avg_agent_execution_time: float
    p95_agent_execution_time: float
    total_agent_executions: int
    successful_agent_executions: int

    # Database
    avg_db_query_time: float
    total_db_queries: int

    # Errors
    total_errors: int
    error_rate: float

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "avg_api_response_time": 0.15,
                "p50_api_response_time": 0.12,
                "p95_api_response_time": 0.35,
                "p99_api_response_time": 0.58,
                "avg_agent_execution_time": 2.1,
                "p95_agent_execution_time": 4.5,
                "total_agent_executions": 1847,
                "successful_agent_executions": 1789,
                "avg_db_query_time": 0.015,
                "total_db_queries": 15234,
                "total_errors": 23,
                "error_rate": 0.3
            }]
        }
    }


# =============================================================================
# USAGE ANALYTICS
# =============================================================================

class UsageMetrics(BaseModel):
    """Usage and consumption metrics"""

    # API calls
    total_api_calls: int
    api_calls_by_endpoint: Dict[str, int]

    # Token usage (LLM)
    total_tokens_used: int
    tokens_by_model: Dict[str, int]
    estimated_cost_usd: float

    # Storage
    total_conversations: int
    total_messages: int
    total_customers: int
    database_size_mb: float

    # Active usage
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "total_api_calls": 45234,
                "api_calls_by_endpoint": {
                    "/api/conversations": 12456,
                    "/api/agents/execute": 8934,
                    "/api/customers": 3421
                },
                "total_tokens_used": 4532198,
                "tokens_by_model": {
                    "claude-3-haiku-20240307": 3842156,
                    "claude-3-sonnet-20240229": 690042
                },
                "estimated_cost_usd": 123.45,
                "total_conversations": 15847,
                "total_messages": 67542,
                "total_customers": 1542,
                "database_size_mb": 245.8,
                "daily_active_users": 342,
                "weekly_active_users": 1245,
                "monthly_active_users": 4231
            }]
        }
    }


# =============================================================================
# EXPORT MODELS
# =============================================================================

class AnalyticsExportRequest(BaseModel):
    """Request to export analytics data"""

    metrics: List[str] = Field(..., description="Metrics to export")
    start_date: date
    end_date: date
    format: str = Field(default="csv", description="csv, json, excel")
    email: Optional[str] = Field(None, description="Email to send export to")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "metrics": ["conversations", "agent_performance", "customer_growth"],
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
                "format": "csv",
                "email": "admin@example.com"
            }]
        }
    }


class AnalyticsExportResponse(BaseModel):
    """Analytics export response"""

    export_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    download_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "export_id": "exp_abc123",
                "status": "completed",
                "download_url": "https://api.example.com/exports/exp_abc123.csv",
                "created_at": "2025-11-16T12:00:00Z",
                "completed_at": "2025-11-16T12:00:15Z",
                "file_size_bytes": 524288
            }]
        }
    }
