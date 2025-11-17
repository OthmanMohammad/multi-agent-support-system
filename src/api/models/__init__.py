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
    LoginRequest,
    LoginResponse,
    APIKeyCreateRequest,
    APIKeyResponse,
)

# Conversation models
from src.api.models.conversation_models import (
    ConversationDetailResponse,
    MessageResponse,
)

# Customer models
from src.api.models.customer_models import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
    CustomerResponse,
)

# Webhook models
from src.api.models.webhook_models import (
    WebhookCreateRequest,
    WebhookResponse,
)

# Workflow models
from src.api.models.workflow_models import (
    SequentialWorkflowRequest,
    ParallelWorkflowRequest,
)

__all__ = [
    # Agent models
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    # Analytics models
    "SystemOverviewResponse",
    "TimeSeriesResponse",
    # Auth models
    "LoginRequest",
    "LoginResponse",
    "APIKeyCreateRequest",
    "APIKeyResponse",
    # Conversation models
    "ConversationDetailResponse",
    "MessageResponse",
    # Customer models
    "CustomerCreateRequest",
    "CustomerUpdateRequest",
    "CustomerResponse",
    # Webhook models
    "WebhookCreateRequest",
    "WebhookResponse",
    # Workflow models
    "SequentialWorkflowRequest",
    "ParallelWorkflowRequest",
]
