"""
API Models Package
Contains Pydantic models for API request/response validation
"""

from src.api.models.agent_models import (
    AgentInfo,
    AgentListResponse,
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentExecuteAsyncRequest,
    AgentJobResponse,
    AgentJobStatusResponse,
    AgentMetrics,
    AgentMetricsResponse,
)

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

from src.api.models.conversation_models import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageCreateRequest,
    MessageResponse,
)

from src.api.models.customer_models import (
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
)

from src.api.models.auth_models import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    APIKeyCreateRequest,
    APIKeyResponse,
)

__all__ = [
    # Agent models
    "AgentInfo",
    "AgentListResponse",
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    "AgentExecuteAsyncRequest",
    "AgentJobResponse",
    "AgentJobStatusResponse",
    "AgentMetrics",
    "AgentMetricsResponse",
    # Workflow models
    "SequentialWorkflowRequest",
    "SequentialWorkflowResponse",
    "ParallelWorkflowRequest",
    "ParallelWorkflowResponse",
    "DebateWorkflowRequest",
    "DebateWorkflowResponse",
    "DebateRound",
    "VerificationWorkflowRequest",
    "VerificationWorkflowResponse",
    "ExpertPanelWorkflowRequest",
    "ExpertPanelWorkflowResponse",
    "ExpertOpinion",
    "WorkflowJobResponse",
    # Conversation models
    "ConversationCreateRequest",
    "ConversationResponse",
    "MessageCreateRequest",
    "MessageResponse",
    # Customer models
    "CustomerCreateRequest",
    "CustomerResponse",
    "CustomerUpdateRequest",
    # Auth models
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "TokenResponse",
    "APIKeyCreateRequest",
    "APIKeyResponse",
]