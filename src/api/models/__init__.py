"""
API Models Package

Centralized exports for all API request/response models.
"""

# Agent execution models
from src.api.models.agent_models import (
    AgentExecuteRequest,
    AgentExecuteResponse,
    BatchAgentRequest,
    BatchAgentResponse,
)

# Analytics models
from src.api.models.analytics_models import (
    AnalyticsQuery,
    AnalyticsResponse,
    MetricDefinition,
    TimeSeriesData,
)

# Authentication models
from src.api.models.auth_models import (
    Token,
    TokenData,
    UserLogin,
    UserCreate,
    UserResponse,
    APIKeyCreate,
    APIKeyResponse,
)

# Conversation models
from src.api.models.conversation_models import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)

# Customer models
from src.api.models.customer_models import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)

# Webhook models
from src.api.models.webhook_models import (
    WebhookEvent,
    WebhookPayload,
    WebhookConfig,
)

# Workflow models
from src.api.models.workflow_models import (
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    WorkflowStatus,
    StepResult,
)

__all__ = [
    # Agent models
    "AgentExecuteRequest",
    "AgentExecuteResponse",
    "BatchAgentRequest",
    "BatchAgentResponse",
    # Analytics models
    "AnalyticsQuery",
    "AnalyticsResponse",
    "MetricDefinition",
    "TimeSeriesData",
    # Auth models
    "Token",
    "TokenData",
    "UserLogin",
    "UserCreate",
    "UserResponse",
    "APIKeyCreate",
    "APIKeyResponse",
    # Conversation models
    "ConversationCreate",
    "ConversationResponse",
    "MessageCreate",
    "MessageResponse",
    # Customer models
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    # Webhook models
    "WebhookEvent",
    "WebhookPayload",
    "WebhookConfig",
    # Workflow models
    "WorkflowExecuteRequest",
    "WorkflowExecuteResponse",
    "WorkflowStatus",
    "StepResult",
]
