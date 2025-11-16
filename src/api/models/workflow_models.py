"""
Workflow Orchestration Pydantic Models

Request and response models for workflow orchestration endpoints.
"""

from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# =============================================================================
# WORKFLOW STEP CONFIGURATION
# =============================================================================

class WorkflowStepConfig(BaseModel):
    """Configuration for a workflow step"""

    agent_name: str = Field(..., description="Name of the agent to execute")
    required: bool = Field(default=True, description="Whether this step is required")
    timeout: int = Field(default=30, ge=1, le=300, description="Step timeout in seconds")
    retry_on_failure: bool = Field(default=True, description="Retry on failure")
    max_retries: int = Field(default=2, ge=0, le=5, description="Maximum retries")
    metadata: Dict[str, Any] = Field(default={}, description="Additional step metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "agent_name": "billing_inquiry_agent",
                "required": True,
                "timeout": 30,
                "retry_on_failure": True,
                "max_retries": 2,
                "metadata": {"priority": "high"}
            }]
        }
    }


# =============================================================================
# SEQUENTIAL WORKFLOW
# =============================================================================

class SequentialWorkflowRequest(BaseModel):
    """Request to execute a sequential workflow"""

    name: str = Field(..., description="Workflow name")
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    steps: List[WorkflowStepConfig] = Field(..., min_length=1, description="Workflow steps in order")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    rollback_on_failure: bool = Field(default=False, description="Rollback on failure")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "customer_onboarding",
                "query": "Onboard new customer: John Doe <john@example.com>",
                "steps": [
                    {"agent_name": "data_collector", "required": True},
                    {"agent_name": "account_setup", "required": True},
                    {"agent_name": "email_verification", "required": False}
                ],
                "rollback_on_failure": True
            }]
        }
    }


class SequentialWorkflowResponse(BaseModel):
    """Response from sequential workflow execution"""

    success: bool
    workflow_name: str
    steps_executed: List[str] = Field(..., description="Steps that were executed")
    steps_skipped: List[str] = Field(default=[], description="Steps that were skipped")
    final_result: str = Field(..., description="Final workflow result")
    execution_time: float = Field(..., description="Total execution time in seconds")
    step_results: Dict[str, Any] = Field(..., description="Results from each step")
    error: Optional[str] = Field(None, description="Error message if failed")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "success": True,
                "workflow_name": "customer_onboarding",
                "steps_executed": ["data_collector", "account_setup", "email_verification"],
                "steps_skipped": [],
                "final_result": "Customer onboarded successfully. Account ID: 12345",
                "execution_time": 8.5,
                "step_results": {
                    "data_collector": {"status": "success", "data": {"email": "john@example.com"}},
                    "account_setup": {"status": "success", "account_id": "12345"},
                    "email_verification": {"status": "success", "verified": True}
                }
            }]
        }
    }


# =============================================================================
# PARALLEL WORKFLOW
# =============================================================================

class ParallelWorkflowRequest(BaseModel):
    """Request to execute a parallel workflow"""

    name: str = Field(..., description="Workflow name")
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    agents: List[str] = Field(..., min_length=2, description="Agents to execute in parallel")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    timeout: int = Field(default=60, ge=1, le=300, description="Overall timeout in seconds")
    require_all_success: bool = Field(default=False, description="Require all agents to succeed")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "comprehensive_customer_analysis",
                "query": "Analyze customer account 12345",
                "agents": [
                    "billing_analysis_agent",
                    "usage_analysis_agent",
                    "churn_prediction_agent"
                ],
                "timeout": 60,
                "require_all_success": False
            }]
        }
    }


class ParallelWorkflowResponse(BaseModel):
    """Response from parallel workflow execution"""

    success: bool
    workflow_name: str
    agents_executed: List[str]
    agents_succeeded: List[str]
    agents_failed: List[str]
    aggregated_result: str = Field(..., description="Aggregated result from all agents")
    execution_time: float = Field(..., description="Total execution time in seconds")
    agent_results: Dict[str, Any] = Field(..., description="Individual agent results")
    error: Optional[str] = Field(None, description="Error message if failed")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "success": True,
                "workflow_name": "comprehensive_customer_analysis",
                "agents_executed": ["billing_analysis_agent", "usage_analysis_agent", "churn_prediction_agent"],
                "agents_succeeded": ["billing_analysis_agent", "usage_analysis_agent", "churn_prediction_agent"],
                "agents_failed": [],
                "aggregated_result": "Customer is healthy with low churn risk. Billing current, usage stable.",
                "execution_time": 4.2,
                "agent_results": {
                    "billing_analysis_agent": {"status": "paid", "balance": 0.0},
                    "usage_analysis_agent": {"trend": "stable", "avg_daily": 145},
                    "churn_prediction_agent": {"risk": "low", "score": 0.12}
                }
            }]
        }
    }


# =============================================================================
# DEBATE WORKFLOW
# =============================================================================

class DebateWorkflowRequest(BaseModel):
    """Request to execute a debate workflow"""

    name: str = Field(..., description="Workflow name")
    query: str = Field(..., min_length=1, max_length=10000, description="Topic to debate")
    agents: List[str] = Field(..., min_length=2, max_length=10, description="Debating agents")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    rounds: int = Field(default=3, ge=1, le=10, description="Number of debate rounds")
    judge_agent: Optional[str] = Field(None, description="Optional judge agent for final decision")
    timeout: int = Field(default=120, ge=1, le=600, description="Overall timeout in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "pricing_strategy_debate",
                "query": "Should we offer a freemium tier for our SaaS product?",
                "agents": ["business_analyst_agent", "marketing_strategist_agent", "finance_advisor_agent"],
                "rounds": 3,
                "judge_agent": "ceo_decision_agent",
                "timeout": 120
            }]
        }
    }


class DebateRound(BaseModel):
    """Results from a single debate round"""

    round_number: int
    arguments: Dict[str, str] = Field(..., description="Arguments from each agent")
    execution_time: float

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "round_number": 1,
                "arguments": {
                    "business_analyst_agent": "Freemium increases user acquisition by 300%...",
                    "finance_advisor_agent": "Free users cost us money. We need to focus on paid conversions..."
                },
                "execution_time": 5.2
            }]
        }
    }


class DebateWorkflowResponse(BaseModel):
    """Response from debate workflow execution"""

    success: bool
    workflow_name: str
    topic: str
    participants: List[str]
    rounds_completed: int
    debate_rounds: List[DebateRound] = Field(..., description="Results from each round")
    final_decision: str = Field(..., description="Final decision or consensus")
    judge_reasoning: Optional[str] = Field(None, description="Judge's reasoning (if judge used)")
    execution_time: float
    error: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "success": True,
                "workflow_name": "pricing_strategy_debate",
                "topic": "Should we offer a freemium tier?",
                "participants": ["business_analyst_agent", "finance_advisor_agent"],
                "rounds_completed": 3,
                "debate_rounds": [
                    {
                        "round_number": 1,
                        "arguments": {"business_analyst_agent": "Increases acquisition..."},
                        "execution_time": 5.2
                    }
                ],
                "final_decision": "Implement limited freemium tier with clear upgrade path",
                "judge_reasoning": "Balance between acquisition and revenue generation",
                "execution_time": 18.5
            }]
        }
    }


# =============================================================================
# VERIFICATION WORKFLOW
# =============================================================================

class VerificationWorkflowRequest(BaseModel):
    """Request to execute a verification workflow"""

    name: str = Field(..., description="Workflow name")
    query: str = Field(..., min_length=1, max_length=10000, description="Content to verify")
    primary_agent: str = Field(..., description="Primary agent to generate response")
    verifier_agents: List[str] = Field(..., min_length=1, description="Agents to verify the response")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    consensus_threshold: float = Field(default=0.7, ge=0.5, le=1.0, description="Consensus threshold (0.5-1.0)")
    max_iterations: int = Field(default=3, ge=1, le=10, description="Max verification iterations")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "technical_answer_verification",
                "query": "How do I configure Redis clustering?",
                "primary_agent": "technical_support_agent",
                "verifier_agents": ["redis_expert_agent", "devops_specialist_agent"],
                "consensus_threshold": 0.8,
                "max_iterations": 3
            }]
        }
    }


class VerificationWorkflowResponse(BaseModel):
    """Response from verification workflow execution"""

    success: bool
    workflow_name: str
    verified_result: str = Field(..., description="Final verified result")
    iterations: int = Field(..., description="Number of iterations performed")
    consensus_achieved: bool
    consensus_score: float = Field(..., ge=0.0, le=1.0, description="Final consensus score")
    verifier_feedback: Dict[str, Any] = Field(..., description="Feedback from verifiers")
    execution_time: float
    error: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "success": True,
                "workflow_name": "technical_answer_verification",
                "verified_result": "To configure Redis clustering: 1) Enable cluster mode...",
                "iterations": 2,
                "consensus_achieved": True,
                "consensus_score": 0.92,
                "verifier_feedback": {
                    "redis_expert_agent": {"approved": True, "confidence": 0.95},
                    "devops_specialist_agent": {"approved": True, "confidence": 0.89}
                },
                "execution_time": 12.3
            }]
        }
    }


# =============================================================================
# EXPERT PANEL WORKFLOW
# =============================================================================

class ExpertPanelWorkflowRequest(BaseModel):
    """Request to execute an expert panel workflow"""

    name: str = Field(..., description="Workflow name")
    query: str = Field(..., min_length=1, max_length=10000, description="Question for expert panel")
    experts: List[str] = Field(..., min_length=2, description="Expert agents")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    moderator_agent: Optional[str] = Field(None, description="Optional moderator agent")
    voting_method: Literal["majority", "weighted", "consensus"] = Field(
        default="majority",
        description="Voting method for final decision"
    )
    timeout: int = Field(default=120, ge=1, le=600, description="Overall timeout in seconds")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "product_feature_evaluation",
                "query": "Should we build native mobile apps or stick with responsive web?",
                "experts": [
                    "mobile_expert_agent",
                    "web_expert_agent",
                    "ux_designer_agent",
                    "cost_analyst_agent"
                ],
                "moderator_agent": "product_manager_agent",
                "voting_method": "weighted",
                "timeout": 120
            }]
        }
    }


class ExpertOpinion(BaseModel):
    """Opinion from a single expert"""

    expert_name: str
    opinion: str
    reasoning: str
    vote: Literal["approve", "reject", "abstain"]
    confidence: float = Field(..., ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "expert_name": "mobile_expert_agent",
                "opinion": "Native apps provide better performance and user experience",
                "reasoning": "Benchmarks show 40% faster load times, better offline support",
                "vote": "approve",
                "confidence": 0.85
            }]
        }
    }


class ExpertPanelWorkflowResponse(BaseModel):
    """Response from expert panel workflow execution"""

    success: bool
    workflow_name: str
    question: str
    expert_opinions: List[ExpertOpinion]
    final_recommendation: str = Field(..., description="Final panel recommendation")
    vote_summary: Dict[str, int] = Field(..., description="Vote counts (approve/reject/abstain)")
    consensus_level: float = Field(..., ge=0.0, le=1.0, description="Level of consensus")
    moderator_summary: Optional[str] = Field(None, description="Moderator's summary (if used)")
    execution_time: float
    error: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "success": True,
                "workflow_name": "product_feature_evaluation",
                "question": "Should we build native mobile apps?",
                "expert_opinions": [
                    {
                        "expert_name": "mobile_expert_agent",
                        "opinion": "Native apps provide better UX",
                        "reasoning": "40% faster load times",
                        "vote": "approve",
                        "confidence": 0.85
                    }
                ],
                "final_recommendation": "Build native apps with phased rollout",
                "vote_summary": {"approve": 3, "reject": 1, "abstain": 0},
                "consensus_level": 0.75,
                "moderator_summary": "Panel recommends native apps with cost controls",
                "execution_time": 25.7
            }]
        }
    }


# =============================================================================
# ASYNC WORKFLOW EXECUTION
# =============================================================================

class WorkflowJobResponse(BaseModel):
    """Response for async workflow job"""

    job_id: UUID
    workflow_type: str = Field(..., description="Workflow type (sequential, parallel, debate, etc.)")
    workflow_name: str
    status: str = Field(..., description="Job status (pending, running, completed, failed)")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")

    # Result (available when completed)
    result: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "workflow_type": "debate",
                "workflow_name": "pricing_strategy_debate",
                "status": "running",
                "created_at": "2025-11-16T12:00:00Z",
                "started_at": "2025-11-16T12:00:05Z",
                "progress": 33.3
            }]
        }
    }
