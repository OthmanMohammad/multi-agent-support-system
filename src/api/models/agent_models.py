"""
Agent Execution Pydantic Models

Request and response models for agent execution endpoints.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# AGENT LISTING
# =============================================================================


class AgentInfo(BaseModel):
    """Information about a registered agent"""

    name: str = Field(..., description="Agent unique identifier")
    tier: str = Field(..., description="Agent tier (essential, revenue, operational, advanced)")
    category: str | None = Field(None, description="Agent category (routing, billing, etc.)")
    type: str = Field(..., description="Agent type (router, specialist, coordinator)")
    description: str = Field(..., description="Agent description")
    capabilities: list[str] = Field(default=[], description="Agent capabilities")
    required_scopes: list[str] = Field(
        default=[], description="Required permission scopes to execute"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "meta_router",
                    "tier": "essential",
                    "category": "routing",
                    "type": "router",
                    "description": "Intelligent routing agent for customer queries",
                    "capabilities": ["routing", "classification", "escalation"],
                    "required_scopes": ["execute:agents:tier1"],
                }
            ]
        }
    }


class AgentListResponse(BaseModel):
    """List of available agents"""

    agents: list[AgentInfo]
    total: int
    by_tier: dict[str, int] = Field(..., description="Count of agents per tier")
    by_category: dict[str, int] = Field(..., description="Count of agents per category")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agents": [
                        {
                            "name": "meta_router",
                            "tier": "essential",
                            "category": "routing",
                            "type": "router",
                            "description": "Routes customer queries",
                            "capabilities": ["routing"],
                            "required_scopes": ["execute:agents:tier1"],
                        }
                    ],
                    "total": 237,
                    "by_tier": {"essential": 75, "revenue": 81, "operational": 44, "advanced": 37},
                    "by_category": {"routing": 1, "billing": 15, "technical": 20},
                }
            ]
        }
    }


# =============================================================================
# AGENT EXECUTION
# =============================================================================


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent"""

    agent_name: str = Field(..., description="Name of the agent to execute")
    query: str = Field(..., min_length=1, max_length=10000, description="User query or input")
    context: dict[str, Any] | None = Field(None, description="Additional context for execution")
    conversation_id: UUID | None = Field(None, description="Associated conversation ID")
    customer_id: UUID | None = Field(None, description="Associated customer ID")

    # Execution options
    timeout: int = Field(default=30, ge=1, le=300, description="Execution timeout in seconds")
    temperature: float | None = Field(None, ge=0.0, le=1.0, description="LLM temperature override")
    max_tokens: int | None = Field(None, ge=100, le=4096, description="Max tokens override")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agent_name": "billing_inquiry_agent",
                    "query": "I was charged twice for my subscription this month",
                    "context": {"customer_tier": "premium", "account_balance": -50.00},
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                    "timeout": 30,
                    "temperature": 0.3,
                }
            ]
        }
    }


class AgentExecuteResponse(BaseModel):
    """Response from agent execution"""

    # Execution result
    success: bool
    agent_name: str
    result: str = Field(..., description="Agent's response/output")

    # Metadata
    execution_time: float = Field(..., description="Execution time in seconds")
    tokens_used: int = Field(..., description="LLM tokens used")
    model_used: str = Field(..., description="LLM model used")

    # Optional context
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Agent confidence score")
    suggested_actions: list[str] = Field(default=[], description="Suggested follow-up actions")
    escalation_needed: bool = Field(default=False, description="Whether escalation is needed")
    knowledge_base_hits: int = Field(default=0, description="Number of KB documents used")

    # Error handling
    error: str | None = Field(None, description="Error message if execution failed")
    error_type: str | None = Field(None, description="Error type/category")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "agent_name": "billing_inquiry_agent",
                    "result": "I see you were charged twice on Nov 15th. I've initiated a refund for $49.99. You should see it in 3-5 business days. Is there anything else I can help with?",
                    "execution_time": 2.45,
                    "tokens_used": 342,
                    "model_used": "claude-3-haiku-20240307",
                    "confidence": 0.92,
                    "suggested_actions": ["send_refund_confirmation_email", "add_account_credit"],
                    "escalation_needed": False,
                    "knowledge_base_hits": 2,
                }
            ]
        }
    }


# =============================================================================
# ASYNC AGENT EXECUTION
# =============================================================================


class AgentExecuteAsyncRequest(AgentExecuteRequest):
    """Request for async agent execution"""

    callback_url: str | None = Field(None, description="Webhook URL for completion notification")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agent_name": "case_study_creator",
                    "query": "Create a case study for customer XYZ's successful implementation",
                    "timeout": 120,
                    "callback_url": "https://api.example.com/webhooks/agent-completion",
                }
            ]
        }
    }


class AgentJobResponse(BaseModel):
    """Response for async agent job"""

    job_id: UUID
    agent_name: str
    status: str = Field(..., description="Job status (pending, running, completed, failed)")
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")

    # Result (only available when completed)
    result: AgentExecuteResponse | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "agent_name": "case_study_creator",
                    "status": "running",
                    "created_at": "2025-11-16T12:00:00Z",
                    "started_at": "2025-11-16T12:00:05Z",
                    "estimated_completion": "2025-11-16T12:02:00Z",
                }
            ]
        }
    }


class AgentJobStatusResponse(BaseModel):
    """Status of an async agent job"""

    job_id: UUID
    status: str
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    message: str | None = Field(None, description="Status message")
    result: AgentExecuteResponse | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "running",
                    "progress": 65.0,
                    "message": "Generating content sections...",
                }
            ]
        }
    }


# =============================================================================
# AGENT METRICS
# =============================================================================


class AgentMetrics(BaseModel):
    """Metrics for a single agent"""

    agent_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float = Field(..., description="Average execution time in seconds")
    average_tokens_used: float
    total_tokens_used: int
    average_confidence: float | None = Field(None, description="Average confidence score")
    escalation_rate: float = Field(..., ge=0.0, le=100.0, description="Escalation rate percentage")
    last_executed_at: datetime | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "agent_name": "billing_inquiry_agent",
                    "total_executions": 1542,
                    "successful_executions": 1489,
                    "failed_executions": 53,
                    "average_execution_time": 2.3,
                    "average_tokens_used": 287.5,
                    "total_tokens_used": 443205,
                    "average_confidence": 0.87,
                    "escalation_rate": 12.5,
                    "last_executed_at": "2025-11-16T12:30:00Z",
                }
            ]
        }
    }


class AgentMetricsResponse(BaseModel):
    """Agent metrics response"""

    metrics: list[AgentMetrics]
    time_period: str = Field(..., description="Time period for metrics (24h, 7d, 30d)")
    total_executions: int
    total_tokens_used: int
    average_success_rate: float = Field(..., ge=0.0, le=100.0, description="Overall success rate %")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "metrics": [
                        {
                            "agent_name": "billing_inquiry_agent",
                            "total_executions": 1542,
                            "successful_executions": 1489,
                            "failed_executions": 53,
                            "average_execution_time": 2.3,
                            "average_tokens_used": 287.5,
                            "total_tokens_used": 443205,
                            "average_confidence": 0.87,
                            "escalation_rate": 12.5,
                            "last_executed_at": "2025-11-16T12:30:00Z",
                        }
                    ],
                    "time_period": "24h",
                    "total_executions": 15847,
                    "total_tokens_used": 4532198,
                    "average_success_rate": 96.8,
                }
            ]
        }
    }
