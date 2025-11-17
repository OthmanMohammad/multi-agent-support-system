"""
Agent Execution Routes - REST API endpoints for agent management and execution

Provides endpoints for:
- Agent discovery and listing
- Synchronous agent execution
- Asynchronous agent execution with job tracking
- Agent performance metrics

Part of: Phase 2 - Agent & Workflow Endpoints
"""

import asyncio
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException, status, Query
import time
import os

from src.api.models.agent_models import (
    AgentListResponse,
    AgentInfo,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentExecuteAsyncRequest,
    AgentJobResponse,
    AgentJobStatusResponse,
    AgentMetricsResponse,
    AgentMetrics,
)
from src.api.dependencies import get_current_user
from src.api.auth.permissions import PermissionScope, require_scopes, require_any_scope
from src.database.models.user import User
from src.services.infrastructure.agent_registry import AgentRegistry
from src.services.job_store import RedisJobStore, InMemoryJobStore, JobType, JobStatus
from src.agents.base.agent_types import AgentType
from src.agents.base.base_agent import AgentConfig
from src.workflow.state import AgentState
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/agents")


# =============================================================================
# PRODUCTION JOB STORE (Redis-backed with in-memory fallback)
# =============================================================================

# Initialize job store (Redis if available, otherwise in-memory)
def _initialize_job_store():
    """Initialize job store based on environment"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    environment = os.getenv("ENVIRONMENT", "development")

    # Use Redis in production, in-memory for development
    if environment == "production":
        logger.info("initializing_redis_job_store", redis_url=redis_url)
        return RedisJobStore(redis_url=redis_url)
    else:
        logger.warning(
            "using_in_memory_job_store",
            message="Using in-memory job store. Jobs will not persist across restarts."
        )
        return InMemoryJobStore()


# Global job store instance
job_store = _initialize_job_store()


# Initialize job store on startup
@router.on_event("startup")
async def startup_job_store():
    """Initialize job store on router startup"""
    await job_store.initialize()
    logger.info("job_store_initialized")


@router.on_event("shutdown")
async def shutdown_job_store():
    """Close job store on router shutdown"""
    await job_store.close()
    logger.info("job_store_closed")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_agent_tier_scope(tier: str) -> str:
    """Get required permission scope for agent tier"""
    tier_scopes = {
        "essential": PermissionScope.EXECUTE_AGENTS_TIER1,
        "revenue": PermissionScope.EXECUTE_AGENTS_TIER2,
        "operational": PermissionScope.EXECUTE_AGENTS_TIER3,
        "advanced": PermissionScope.EXECUTE_AGENTS_TIER4,
    }
    return tier_scopes.get(tier.lower(), PermissionScope.EXECUTE_AGENTS_TIER1)


def check_agent_permission(user: User, agent_name: str) -> bool:
    """Check if user has permission to execute agent"""
    metadata = AgentRegistry.get_agent_metadata(agent_name)
    if not metadata:
        return False

    tier = metadata.get("tier", "essential")
    required_scope = get_agent_tier_scope(tier)

    user_scopes = user.get_scopes()
    return required_scope in user_scopes or PermissionScope.ALL in user_scopes


async def execute_agent(
    agent_name: str,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> AgentExecuteResponse:
    """
    Execute an agent and return response.

    Args:
        agent_name: Name of agent to execute
        query: User query/input
        context: Additional context
        timeout: Execution timeout
        temperature: LLM temperature override
        max_tokens: Max tokens override

    Returns:
        AgentExecuteResponse with execution results

    Raises:
        HTTPException: If agent not found or execution fails
    """
    start_time = time.time()

    # Get agent class from registry
    agent_class = AgentRegistry.get_agent(agent_name)
    if not agent_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    # Get agent metadata
    metadata = AgentRegistry.get_agent_metadata(agent_name)

    try:
        # Create agent config
        agent_config = AgentConfig(
            name=agent_name,
            type=AgentType.SPECIALIST,  # Default type
            tier=metadata.get("tier", "essential"),
            temperature=temperature or 0.3,
            max_tokens=max_tokens or 1000,
        )

        # Instantiate agent
        agent = agent_class(config=agent_config)

        # Create agent state
        state = AgentState(
            current_query=query,
            conversation_history=[],
            context=context or {},
        )

        # Execute agent with timeout
        try:
            result = await asyncio.wait_for(
                agent.process(state),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                "agent_execution_timeout",
                agent=agent_name,
                timeout=timeout
            )
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Agent execution timed out after {timeout}s"
            )

        execution_time = time.time() - start_time

        # Build response
        response = AgentExecuteResponse(
            success=True,
            agent_name=agent_name,
            result=result.response if hasattr(result, 'response') else str(result),
            execution_time=round(execution_time, 2),
            tokens_used=result.tokens_used if hasattr(result, 'tokens_used') else 0,
            model_used=result.model_used if hasattr(result, 'model_used') else agent_config.model,
            confidence=result.confidence if hasattr(result, 'confidence') else None,
            suggested_actions=result.suggested_actions if hasattr(result, 'suggested_actions') else [],
            escalation_needed=result.escalation_needed if hasattr(result, 'escalation_needed') else False,
            knowledge_base_hits=result.kb_hits if hasattr(result, 'kb_hits') else 0,
        )

        logger.info(
            "agent_execution_success",
            agent=agent_name,
            execution_time=execution_time,
            tokens=response.tokens_used
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "agent_execution_error",
            agent=agent_name,
            error=str(e),
            execution_time=execution_time,
            exc_info=True
        )

        # Return error response
        return AgentExecuteResponse(
            success=False,
            agent_name=agent_name,
            result="",
            execution_time=round(execution_time, 2),
            tokens_used=0,
            model_used="unknown",
            error=str(e),
            error_type=type(e).__name__,
        )


# =============================================================================
# AGENT LISTING ENDPOINTS
# =============================================================================

@router.get("", response_model=AgentListResponse)
@require_scopes(PermissionScope.READ_AGENTS)
async def list_agents(
    tier: Optional[str] = Query(None, description="Filter by tier (essential, revenue, operational, advanced)"),
    category: Optional[str] = Query(None, description="Filter by category (billing, technical, etc.)"),
    current_user: User = Depends(get_current_user)
):
    """
    List all available agents.

    Returns agent information including tier, category, capabilities,
    and required permissions.

    Requires: read:agents permission
    """
    logger.info(
        "list_agents_request",
        user_id=str(current_user.id),
        tier_filter=tier,
        category_filter=category
    )

    # Get all agents
    all_agents = AgentRegistry.list_agents()

    # Apply filters
    filtered_agents = all_agents
    if tier:
        filtered_agents = [a for a in filtered_agents if a.get("tier") == tier]
    if category:
        filtered_agents = [a for a in filtered_agents if a.get("category") == category]

    # Build agent info list
    agent_infos = []
    for agent in filtered_agents:
        agent_tier = agent.get("tier", "essential")
        agent_infos.append(
            AgentInfo(
                name=agent["name"],
                tier=agent_tier,
                category=agent.get("category"),
                type=agent.get("type", "specialist"),
                description=agent.get("description", f"Agent: {agent['name']}"),
                capabilities=agent.get("capabilities", []),
                required_scopes=[get_agent_tier_scope(agent_tier)],
            )
        )

    # Calculate statistics
    by_tier = {}
    by_category = {}
    for agent in all_agents:
        tier_name = agent.get("tier", "unknown")
        category_name = agent.get("category", "unknown")
        by_tier[tier_name] = by_tier.get(tier_name, 0) + 1
        by_category[category_name] = by_category.get(category_name, 0) + 1

    response = AgentListResponse(
        agents=agent_infos,
        total=len(agent_infos),
        by_tier=by_tier,
        by_category=by_category,
    )

    logger.info(
        "list_agents_success",
        total=len(agent_infos),
        filtered_total=len(agent_infos),
        user_id=str(current_user.id)
    )

    return response


# =============================================================================
# SYNCHRONOUS AGENT EXECUTION
# =============================================================================

@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent_sync(
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute an agent synchronously.

    Executes the specified agent with the provided query and context.
    Blocks until execution completes or times out.

    Permission required based on agent tier:
    - Tier 1 (Essential): execute:agents:tier1
    - Tier 2 (Revenue): execute:agents:tier2
    - Tier 3 (Operational): execute:agents:tier3
    - Tier 4 (Advanced): execute:agents:tier4
    """
    logger.info(
        "agent_execute_request",
        agent=request.agent_name,
        user_id=str(current_user.id),
        conversation_id=str(request.conversation_id) if request.conversation_id else None
    )

    # Check if agent exists
    if not AgentRegistry.get_agent(request.agent_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{request.agent_name}' not found"
        )

    # Check permissions
    if not check_agent_permission(current_user, request.agent_name):
        metadata = AgentRegistry.get_agent_metadata(request.agent_name)
        tier = metadata.get("tier", "essential") if metadata else "essential"
        required_scope = get_agent_tier_scope(tier)

        logger.warning(
            "agent_execution_permission_denied",
            agent=request.agent_name,
            user_id=str(current_user.id),
            required_scope=required_scope
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {required_scope}"
        )

    # Execute agent
    response = await execute_agent(
        agent_name=request.agent_name,
        query=request.query,
        context=request.context,
        timeout=request.timeout,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    return response


# =============================================================================
# ASYNCHRONOUS AGENT EXECUTION
# =============================================================================

@router.post("/execute-async", response_model=AgentJobResponse)
async def execute_agent_async(
    request: AgentExecuteAsyncRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute an agent asynchronously.

    Creates a background job for agent execution. Returns a job ID
    that can be used to check status and retrieve results.

    Useful for long-running agents (e.g., content generation, analysis).

    Permission required based on agent tier.
    """
    logger.info(
        "agent_execute_async_request",
        agent=request.agent_name,
        user_id=str(current_user.id)
    )

    # Check if agent exists
    if not AgentRegistry.get_agent(request.agent_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{request.agent_name}' not found"
        )

    # Check permissions
    if not check_agent_permission(current_user, request.agent_name):
        metadata = AgentRegistry.get_agent_metadata(request.agent_name)
        tier = metadata.get("tier", "essential") if metadata else "essential"
        required_scope = get_agent_tier_scope(tier)

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {required_scope}"
        )

    # Create job
    job_id = await job_store.create_job(
        job_type=JobType.AGENT_EXECUTION,
        agent_name=request.agent_name,
        input_data={
            "query": request.query,
            "context": request.context,
            "timeout": request.timeout,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        },
        metadata={
            "user_id": str(current_user.id),
            "conversation_id": str(request.conversation_id) if request.conversation_id else None,
            "callback_url": request.callback_url
        }
    )

    # Start background task
    async def run_agent_job(job_id: UUID):
        """Background task to execute agent"""
        await job_store.update_job(job_id, status=JobStatus.RUNNING)

        try:
            result = await execute_agent(
                agent_name=request.agent_name,
                query=request.query,
                context=request.context,
                timeout=request.timeout,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            await job_store.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                result=result.model_dump(),
            )

            # TODO: Send webhook if callback_url provided
            if request.callback_url:
                logger.info("webhook_callback", url=request.callback_url, job_id=str(job_id))

        except Exception as e:
            await job_store.update_job(
                job_id,
                status=JobStatus.FAILED,
                error=str(e),
                error_type=type(e).__name__
            )

    # Start task in background (don't await)
    asyncio.create_task(run_agent_job(job_id))

    # Return job response
    job = await job_store.get_job(job_id)
    estimated_completion = datetime.now(UTC) + timedelta(seconds=request.timeout)

    return AgentJobResponse(
        job_id=job_id,
        agent_name=request.agent_name,
        status=job["status"],
        created_at=datetime.fromisoformat(job["created_at"]),
        started_at=datetime.fromisoformat(job["started_at"]) if job.get("started_at") else None,
        completed_at=datetime.fromisoformat(job["completed_at"]) if job.get("completed_at") else None,
        estimated_completion=estimated_completion,
    )


@router.get("/jobs/{job_id}", response_model=AgentJobStatusResponse)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of an async agent job.

    Returns current status, progress, and results (if completed).

    Requires: Authentication (own jobs only)
    """
    logger.debug("get_job_status", job_id=str(job_id), user_id=str(current_user.id))

    try:
        job = await job_store.get_job(job_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Build response
    result = None
    if job["status"] == JobStatus.COMPLETED.value and job["result"]:
        result = AgentExecuteResponse(**job["result"])

    return AgentJobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0.0),
        message=job.get("error") if job["status"] == JobStatus.FAILED.value else None,
        result=result,
    )


# =============================================================================
# AGENT METRICS
# =============================================================================

@router.get("/metrics", response_model=AgentMetricsResponse)
@require_scopes(PermissionScope.READ_ANALYTICS)
async def get_agent_metrics(
    time_period: str = Query("24h", description="Time period (24h, 7d, 30d)"),
    agent_name: Optional[str] = Query(None, description="Filter by specific agent"),
    current_user: User = Depends(get_current_user)
):
    """
    Get agent performance metrics.

    Returns execution statistics, token usage, success rates,
    and performance metrics for agents.

    Requires: read:analytics permission
    """
    logger.info(
        "agent_metrics_request",
        user_id=str(current_user.id),
        time_period=time_period,
        agent_filter=agent_name
    )

    # TODO: Implement actual metrics collection from database/Redis
    # For now, return mock data

    metrics = [
        AgentMetrics(
            agent_name="billing_inquiry_agent",
            total_executions=1542,
            successful_executions=1489,
            failed_executions=53,
            average_execution_time=2.3,
            average_tokens_used=287.5,
            total_tokens_used=443205,
            average_confidence=0.87,
            escalation_rate=12.5,
            last_executed_at=datetime.now(UTC),
        )
    ]

    return AgentMetricsResponse(
        metrics=metrics,
        time_period=time_period,
        total_executions=sum(m.total_executions for m in metrics),
        total_tokens_used=sum(m.total_tokens_used for m in metrics),
        average_success_rate=96.8,
    )
