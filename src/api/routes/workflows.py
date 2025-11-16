"""
Workflow Orchestration Routes - REST API endpoints for multi-agent workflows

Provides endpoints for:
- Sequential workflow execution
- Parallel workflow execution
- Debate workflow execution
- Verification workflow execution
- Expert panel workflow execution
- Async workflow execution with job tracking

Part of: Phase 2 - Agent & Workflow Endpoints
"""

import asyncio
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
import time

from src.api.models.workflow_models import (
    SequentialWorkflowRequest,
    SequentialWorkflowResponse,
    ParallelWorkflowRequest,
    ParallelWorkflowResponse,
    DebateWorkflowRequest,
    DebateWorkflowResponse,
    DebateRound,
    VerificationWorkflowRequest,
    VerificationWorkflowResponse,
    ExpertPanelWorkflowRequest,
    ExpertPanelWorkflowResponse,
    ExpertOpinion,
    WorkflowJobResponse,
)
from src.api.dependencies import get_current_user
from src.api.auth.permissions import PermissionScope, require_scopes
from src.database.models.user import User
from src.services.infrastructure.agent_registry import AgentRegistry
from src.workflow.patterns.sequential import SequentialWorkflow, SequentialStep
from src.workflow.patterns.parallel import ParallelWorkflow
from src.workflow.patterns.debate import DebateWorkflow
from src.workflow.patterns.verification import VerificationWorkflow
from src.workflow.patterns.expert_panel import ExpertPanelWorkflow
from src.workflow.state import AgentState
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/workflows")


# =============================================================================
# IN-MEMORY JOB STORE (temporary - will be replaced with Redis/DB)
# =============================================================================

class WorkflowJobStore:
    """In-memory job store for async workflow execution"""

    def __init__(self):
        self._jobs: Dict[UUID, Dict[str, Any]] = {}

    def create_job(self, workflow_type: str, workflow_name: str, request: Any) -> UUID:
        """Create a new workflow job"""
        job_id = uuid4()
        self._jobs[job_id] = {
            "job_id": job_id,
            "workflow_type": workflow_type,
            "workflow_name": workflow_name,
            "request": request,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "progress": 0.0,
            "result": None,
            "error": None,
        }
        return job_id

    def get_job(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        return self._jobs.get(job_id)

    def update_job(self, job_id: UUID, **kwargs):
        """Update job fields"""
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)


# Global job store instance
workflow_job_store = WorkflowJobStore()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_agents_exist(agent_names: list[str]) -> bool:
    """Check if all agents exist in registry"""
    for agent_name in agent_names:
        if not AgentRegistry.get_agent(agent_name):
            return False
    return True


def get_missing_agents(agent_names: list[str]) -> list[str]:
    """Get list of agents that don't exist"""
    missing = []
    for agent_name in agent_names:
        if not AgentRegistry.get_agent(agent_name):
            missing.append(agent_name)
    return missing


# =============================================================================
# SEQUENTIAL WORKFLOW
# =============================================================================

@router.post("/sequential", response_model=SequentialWorkflowResponse)
@require_scopes(PermissionScope.EXECUTE_WORKFLOWS)
async def execute_sequential_workflow(
    request: SequentialWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a sequential workflow.

    Executes agents in a defined sequence, where each agent's output
    becomes context for the next agent.

    Use cases:
    - Customer onboarding flows
    - Multi-step verification processes
    - Escalation chains
    - Step-by-step problem solving

    Requires: execute:workflows permission
    """
    logger.info(
        "sequential_workflow_request",
        workflow_name=request.name,
        user_id=str(current_user.id),
        steps_count=len(request.steps)
    )

    start_time = time.time()

    # Validate all agents exist
    agent_names = [step.agent_name for step in request.steps]
    missing = get_missing_agents(agent_names)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agents not found: {', '.join(missing)}"
        )

    # Build workflow steps
    workflow_steps = [
        SequentialStep(
            agent_name=step.agent_name,
            required=step.required,
            timeout=step.timeout,
            retry_on_failure=step.retry_on_failure,
            max_retries=step.max_retries,
            metadata=step.metadata,
        )
        for step in request.steps
    ]

    # Create workflow
    workflow = SequentialWorkflow(
        name=request.name,
        steps=workflow_steps,
        rollback_on_failure=request.rollback_on_failure,
    )

    # Create initial state
    initial_state = AgentState(
        current_query=request.query,
        conversation_history=[],
        context=request.context or {},
    )

    try:
        # Execute workflow
        result = await workflow.execute(initial_state)

        execution_time = time.time() - start_time

        response = SequentialWorkflowResponse(
            success=result.success,
            workflow_name=request.name,
            steps_executed=result.steps_executed,
            steps_skipped=result.steps_skipped,
            final_result=result.final_state.current_query if result.final_state else "",
            execution_time=round(execution_time, 2),
            step_results=result.step_results,
            error=result.error,
        )

        logger.info(
            "sequential_workflow_success",
            workflow_name=request.name,
            steps_executed=len(result.steps_executed),
            execution_time=execution_time
        )

        return response

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "sequential_workflow_error",
            workflow_name=request.name,
            error=str(e),
            execution_time=execution_time,
            exc_info=True
        )

        return SequentialWorkflowResponse(
            success=False,
            workflow_name=request.name,
            steps_executed=[],
            steps_skipped=[],
            final_result="",
            execution_time=round(execution_time, 2),
            step_results={},
            error=str(e),
        )


# =============================================================================
# PARALLEL WORKFLOW
# =============================================================================

@router.post("/parallel", response_model=ParallelWorkflowResponse)
@require_scopes(PermissionScope.EXECUTE_WORKFLOWS)
async def execute_parallel_workflow(
    request: ParallelWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a parallel workflow.

    Executes multiple agents concurrently and aggregates their results.

    Use cases:
    - Comprehensive customer analysis (billing + usage + churn)
    - Multi-source data gathering
    - Parallel processing pipelines
    - Independent task execution

    Requires: execute:workflows permission
    """
    logger.info(
        "parallel_workflow_request",
        workflow_name=request.name,
        user_id=str(current_user.id),
        agents_count=len(request.agents)
    )

    start_time = time.time()

    # Validate all agents exist
    missing = get_missing_agents(request.agents)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agents not found: {', '.join(missing)}"
        )

    # Create workflow
    workflow = ParallelWorkflow(
        name=request.name,
        agent_names=request.agents,
        timeout=request.timeout,
        require_all_success=request.require_all_success,
    )

    # Create initial state
    initial_state = AgentState(
        current_query=request.query,
        conversation_history=[],
        context=request.context or {},
    )

    try:
        # Execute workflow
        result = await workflow.execute(initial_state)

        execution_time = time.time() - start_time

        response = ParallelWorkflowResponse(
            success=result.success,
            workflow_name=request.name,
            agents_executed=result.agents_executed,
            agents_succeeded=result.agents_succeeded,
            agents_failed=result.agents_failed,
            aggregated_result=result.aggregated_result,
            execution_time=round(execution_time, 2),
            agent_results=result.agent_results,
            error=result.error,
        )

        logger.info(
            "parallel_workflow_success",
            workflow_name=request.name,
            agents_succeeded=len(result.agents_succeeded),
            agents_failed=len(result.agents_failed),
            execution_time=execution_time
        )

        return response

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "parallel_workflow_error",
            workflow_name=request.name,
            error=str(e),
            execution_time=execution_time,
            exc_info=True
        )

        return ParallelWorkflowResponse(
            success=False,
            workflow_name=request.name,
            agents_executed=[],
            agents_succeeded=[],
            agents_failed=request.agents,
            aggregated_result="",
            execution_time=round(execution_time, 2),
            agent_results={},
            error=str(e),
        )


# =============================================================================
# DEBATE WORKFLOW
# =============================================================================

@router.post("/debate", response_model=DebateWorkflowResponse)
@require_scopes(PermissionScope.EXECUTE_WORKFLOWS)
async def execute_debate_workflow(
    request: DebateWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a debate workflow.

    Multiple agents debate a topic over several rounds, optionally with
    a judge agent making the final decision.

    Use cases:
    - Strategic decision making
    - Product feature evaluation
    - Pros/cons analysis
    - Multi-perspective problem solving

    Requires: execute:workflows permission
    """
    logger.info(
        "debate_workflow_request",
        workflow_name=request.name,
        user_id=str(current_user.id),
        agents_count=len(request.agents),
        rounds=request.rounds
    )

    start_time = time.time()

    # Validate agents
    all_agents = request.agents + ([request.judge_agent] if request.judge_agent else [])
    missing = get_missing_agents(all_agents)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agents not found: {', '.join(missing)}"
        )

    # Create workflow
    workflow = DebateWorkflow(
        name=request.name,
        debater_names=request.agents,
        rounds=request.rounds,
        judge_name=request.judge_agent,
        timeout=request.timeout,
    )

    # Create initial state
    initial_state = AgentState(
        current_query=request.query,
        conversation_history=[],
        context=request.context or {},
    )

    try:
        # Execute workflow
        result = await workflow.execute(initial_state)

        execution_time = time.time() - start_time

        # Build debate rounds
        debate_rounds = [
            DebateRound(
                round_number=i + 1,
                arguments=round_data.get("arguments", {}),
                execution_time=round_data.get("execution_time", 0.0),
            )
            for i, round_data in enumerate(result.rounds)
        ]

        response = DebateWorkflowResponse(
            success=result.success,
            workflow_name=request.name,
            topic=request.query,
            participants=request.agents,
            rounds_completed=result.rounds_completed,
            debate_rounds=debate_rounds,
            final_decision=result.final_decision,
            judge_reasoning=result.judge_reasoning,
            execution_time=round(execution_time, 2),
            error=result.error,
        )

        logger.info(
            "debate_workflow_success",
            workflow_name=request.name,
            rounds_completed=result.rounds_completed,
            execution_time=execution_time
        )

        return response

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "debate_workflow_error",
            workflow_name=request.name,
            error=str(e),
            execution_time=execution_time,
            exc_info=True
        )

        return DebateWorkflowResponse(
            success=False,
            workflow_name=request.name,
            topic=request.query,
            participants=request.agents,
            rounds_completed=0,
            debate_rounds=[],
            final_decision="",
            execution_time=round(execution_time, 2),
            error=str(e),
        )


# =============================================================================
# VERIFICATION WORKFLOW
# =============================================================================

@router.post("/verification", response_model=VerificationWorkflowResponse)
@require_scopes(PermissionScope.EXECUTE_WORKFLOWS)
async def execute_verification_workflow(
    request: VerificationWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a verification workflow.

    A primary agent generates a response, then multiple verifier agents
    review and validate it until consensus is reached.

    Use cases:
    - Technical answer verification
    - Fact-checking
    - Multi-expert review
    - Quality assurance

    Requires: execute:workflows permission
    """
    logger.info(
        "verification_workflow_request",
        workflow_name=request.name,
        user_id=str(current_user.id),
        verifiers_count=len(request.verifier_agents)
    )

    start_time = time.time()

    # Validate agents
    all_agents = [request.primary_agent] + request.verifier_agents
    missing = get_missing_agents(all_agents)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agents not found: {', '.join(missing)}"
        )

    # Create workflow
    workflow = VerificationWorkflow(
        name=request.name,
        primary_agent_name=request.primary_agent,
        verifier_names=request.verifier_agents,
        consensus_threshold=request.consensus_threshold,
        max_iterations=request.max_iterations,
    )

    # Create initial state
    initial_state = AgentState(
        current_query=request.query,
        conversation_history=[],
        context=request.context or {},
    )

    try:
        # Execute workflow
        result = await workflow.execute(initial_state)

        execution_time = time.time() - start_time

        response = VerificationWorkflowResponse(
            success=result.success,
            workflow_name=request.name,
            verified_result=result.verified_response,
            iterations=result.iterations,
            consensus_achieved=result.consensus_achieved,
            consensus_score=result.consensus_score,
            verifier_feedback=result.verifier_feedback,
            execution_time=round(execution_time, 2),
            error=result.error,
        )

        logger.info(
            "verification_workflow_success",
            workflow_name=request.name,
            iterations=result.iterations,
            consensus=result.consensus_achieved,
            execution_time=execution_time
        )

        return response

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "verification_workflow_error",
            workflow_name=request.name,
            error=str(e),
            execution_time=execution_time,
            exc_info=True
        )

        return VerificationWorkflowResponse(
            success=False,
            workflow_name=request.name,
            verified_result="",
            iterations=0,
            consensus_achieved=False,
            consensus_score=0.0,
            verifier_feedback={},
            execution_time=round(execution_time, 2),
            error=str(e),
        )


# =============================================================================
# EXPERT PANEL WORKFLOW
# =============================================================================

@router.post("/expert-panel", response_model=ExpertPanelWorkflowResponse)
@require_scopes(PermissionScope.EXECUTE_WORKFLOWS)
async def execute_expert_panel_workflow(
    request: ExpertPanelWorkflowRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute an expert panel workflow.

    Multiple expert agents provide opinions and vote on a decision,
    optionally moderated by a moderator agent.

    Use cases:
    - Product feature decisions
    - Strategic planning
    - Investment decisions
    - Complex problem evaluation

    Requires: execute:workflows permission
    """
    logger.info(
        "expert_panel_workflow_request",
        workflow_name=request.name,
        user_id=str(current_user.id),
        experts_count=len(request.experts)
    )

    start_time = time.time()

    # Validate agents
    all_agents = request.experts + ([request.moderator_agent] if request.moderator_agent else [])
    missing = get_missing_agents(all_agents)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agents not found: {', '.join(missing)}"
        )

    # Create workflow
    workflow = ExpertPanelWorkflow(
        name=request.name,
        expert_names=request.experts,
        moderator_name=request.moderator_agent,
        voting_method=request.voting_method,
        timeout=request.timeout,
    )

    # Create initial state
    initial_state = AgentState(
        current_query=request.query,
        conversation_history=[],
        context=request.context or {},
    )

    try:
        # Execute workflow
        result = await workflow.execute(initial_state)

        execution_time = time.time() - start_time

        # Build expert opinions
        expert_opinions = [
            ExpertOpinion(
                expert_name=opinion.get("expert_name", ""),
                opinion=opinion.get("opinion", ""),
                reasoning=opinion.get("reasoning", ""),
                vote=opinion.get("vote", "abstain"),
                confidence=opinion.get("confidence", 0.5),
            )
            for opinion in result.expert_opinions
        ]

        response = ExpertPanelWorkflowResponse(
            success=result.success,
            workflow_name=request.name,
            question=request.query,
            expert_opinions=expert_opinions,
            final_recommendation=result.final_recommendation,
            vote_summary=result.vote_summary,
            consensus_level=result.consensus_level,
            moderator_summary=result.moderator_summary,
            execution_time=round(execution_time, 2),
            error=result.error,
        )

        logger.info(
            "expert_panel_workflow_success",
            workflow_name=request.name,
            experts_count=len(expert_opinions),
            consensus=result.consensus_level,
            execution_time=execution_time
        )

        return response

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "expert_panel_workflow_error",
            workflow_name=request.name,
            error=str(e),
            execution_time=execution_time,
            exc_info=True
        )

        return ExpertPanelWorkflowResponse(
            success=False,
            workflow_name=request.name,
            question=request.query,
            expert_opinions=[],
            final_recommendation="",
            vote_summary={"approve": 0, "reject": 0, "abstain": 0},
            consensus_level=0.0,
            execution_time=round(execution_time, 2),
            error=str(e),
        )


# =============================================================================
# ASYNC WORKFLOW EXECUTION
# =============================================================================

@router.post("/{workflow_type}/execute-async", response_model=WorkflowJobResponse)
@require_scopes(PermissionScope.EXECUTE_WORKFLOWS)
async def execute_workflow_async(
    workflow_type: str,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Execute a workflow asynchronously.

    Creates a background job for workflow execution. Returns a job ID
    that can be used to check status and retrieve results.

    Workflow types: sequential, parallel, debate, verification, expert-panel

    Requires: execute:workflows permission
    """
    valid_types = ["sequential", "parallel", "debate", "verification", "expert-panel"]
    if workflow_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow type. Must be one of: {', '.join(valid_types)}"
        )

    logger.info(
        "workflow_async_request",
        workflow_type=workflow_type,
        user_id=str(current_user.id)
    )

    # Create job
    workflow_name = request.get("name", f"{workflow_type}_workflow")
    job_id = workflow_job_store.create_job(workflow_type, workflow_name, request)

    # TODO: Start background task for workflow execution
    # For now, just create the job

    return WorkflowJobResponse(
        job_id=job_id,
        workflow_type=workflow_type,
        workflow_name=workflow_name,
        status="pending",
        created_at=datetime.utcnow(),
        progress=0.0,
    )


@router.get("/jobs/{job_id}", response_model=WorkflowJobResponse)
async def get_workflow_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of an async workflow job.

    Returns current status, progress, and results (if completed).

    Requires: Authentication (own jobs only)
    """
    logger.debug("get_workflow_job_status", job_id=str(job_id), user_id=str(current_user.id))

    job = workflow_job_store.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow job {job_id} not found"
        )

    return WorkflowJobResponse(
        job_id=job_id,
        workflow_type=job["workflow_type"],
        workflow_name=job["workflow_name"],
        status=job["status"],
        created_at=job["created_at"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        progress=job.get("progress", 0.0),
        result=job.get("result"),
    )
