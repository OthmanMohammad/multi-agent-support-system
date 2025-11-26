"""
API Models Package

Centralized exports for all API request/response models.
"""

# Agent execution models
from src.api.models.agent_models import (
    AgentExecuteRequest,
    AgentExecuteResponse,
)

# Analytics models
from src.api.models.analytics_models import (
    SystemOverviewResponse,
    TimeSeriesResponse,
)

# Authentication models
from src.api.models.auth_models import (
    APIKeyCreateRequest,
    APIKeyResponse,
    LoginRequest,
    LoginResponse,
)

# Conversation models
from src.api.models.conversation_models import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationResponse,
    EscalateRequest,
    MessageResponse,
)

# Customer models
from src.api.models.customer_models import (
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
)

# Webhook models
from src.api.models.webhook_models import (
    WebhookCreateRequest,
    WebhookResponse,
)

# Workflow models
from src.api.models.workflow_models import (
    ParallelWorkflowRequest,
    SequentialWorkflowRequest,
)

__all__ = [
    "APIKeyCreateRequest",
    "APIKeyResponse",
    # Agent models
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    # Conversation models
    "ChatRequest",
    "ChatResponse",
    "ConversationDetailResponse",
    "ConversationResponse",
    # Customer models
    "CustomerCreateRequest",
    "CustomerResponse",
    "CustomerUpdateRequest",
    "EscalateRequest",
    # Auth models
    "LoginRequest",
    "LoginResponse",
    "MessageResponse",
    "ParallelWorkflowRequest",
    # Workflow models
    "SequentialWorkflowRequest",
    # Analytics models
    "SystemOverviewResponse",
    "TimeSeriesResponse",
    # Webhook models
    "WebhookCreateRequest",
    "WebhookResponse",
]
