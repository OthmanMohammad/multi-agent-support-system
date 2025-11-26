"""
Conversation Pydantic Models - Enhanced

Extended request/response models for conversation endpoints with
full CRUD operations, filtering, and pagination.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# CHAT REQUEST/RESPONSE (for POST endpoints)
# =============================================================================


class ChatRequest(BaseModel):
    """Request to send a message in a conversation"""

    message: str = Field(..., min_length=1, description="User message content")
    customer_email: str | None = Field(None, description="Customer email for new conversations")
    context: dict | None = Field(None, description="Additional context for the message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "I want to upgrade my plan",
                    "customer_email": "customer@example.com",
                    "context": {"source": "web_chat"},
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """Response after sending a message"""

    conversation_id: UUID
    message_id: UUID
    response: str
    agent_name: str | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                    "message_id": "987fcdeb-51a2-43d7-8c9f-123456789abc",
                    "response": "I can help you upgrade your plan...",
                    "agent_name": "billing_agent",
                    "confidence": 0.95,
                    "created_at": "2025-11-16T12:30:00Z",
                }
            ]
        },
    }


# =============================================================================
# MESSAGE MODELS
# =============================================================================


class MessageResponse(BaseModel):
    """Individual message in a conversation"""

    id: UUID
    conversation_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
    metadata: dict | None = None

    model_config = {"from_attributes": True}


# =============================================================================
# CONVERSATION LIST & DETAIL
# =============================================================================


class ConversationListItem(BaseModel):
    """Conversation summary for list view"""

    id: UUID
    customer_id: UUID
    customer_email: str | None = None
    status: str = Field(..., description="open, resolved, escalated")
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None
    assigned_agent: str | None = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "customer_id": "987fcdeb-51a2-43d7-8c9f-123456789abc",
                    "customer_email": "customer@example.com",
                    "status": "open",
                    "message_count": 5,
                    "created_at": "2025-11-16T12:00:00Z",
                    "updated_at": "2025-11-16T12:30:00Z",
                    "last_message_at": "2025-11-16T12:30:00Z",
                    "assigned_agent": "billing_inquiry_agent",
                }
            ]
        },
    }


class ConversationListResponse(BaseModel):
    """Paginated list of conversations"""

    conversations: list[ConversationListItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "conversations": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "customer_id": "987fcdeb-51a2-43d7-8c9f-123456789abc",
                            "customer_email": "customer@example.com",
                            "status": "open",
                            "message_count": 5,
                            "created_at": "2025-11-16T12:00:00Z",
                            "updated_at": "2025-11-16T12:30:00Z",
                            "last_message_at": "2025-11-16T12:30:00Z",
                        }
                    ],
                    "total": 150,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 8,
                }
            ]
        }
    }


class ConversationDetailResponse(BaseModel):
    """Detailed conversation with all messages"""

    id: UUID
    customer_id: UUID
    customer_email: str | None = None
    status: str
    messages: list[MessageResponse]
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    escalated_at: datetime | None = None
    assigned_agent: str | None = None
    metadata: dict | None = None

    model_config = {"from_attributes": True}


# =============================================================================
# CONVERSATION MUTATIONS
# =============================================================================


class EscalateRequest(BaseModel):
    """Request to escalate conversation to human"""

    reason: str = Field(..., min_length=1, description="Reason for escalation")

    model_config = {
        "json_schema_extra": {"examples": [{"reason": "Customer requested human agent"}]}
    }


class ConversationUpdateRequest(BaseModel):
    """Update conversation details"""

    status: Literal["open", "resolved", "escalated"] | None = None
    assigned_agent: str | None = None
    metadata: dict | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": "resolved", "metadata": {"resolution": "refund_processed"}}]
        }
    }


class ConversationTransferRequest(BaseModel):
    """Transfer conversation to different agent"""

    target_agent: str = Field(..., description="Name of agent to transfer to")
    reason: str | None = Field(None, description="Reason for transfer")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "target_agent": "technical_support_agent",
                    "reason": "Requires technical expertise",
                }
            ]
        }
    }


# =============================================================================
# CONVERSATION STATISTICS
# =============================================================================


class ConversationStats(BaseModel):
    """Conversation statistics"""

    total_conversations: int
    open_conversations: int
    resolved_conversations: int
    escalated_conversations: int
    average_messages_per_conversation: float
    average_resolution_time_minutes: float | None = None
    conversations_today: int
    conversations_this_week: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_conversations": 1542,
                    "open_conversations": 234,
                    "resolved_conversations": 1289,
                    "escalated_conversations": 19,
                    "average_messages_per_conversation": 4.2,
                    "average_resolution_time_minutes": 15.7,
                    "conversations_today": 87,
                    "conversations_this_week": 412,
                }
            ]
        }
    }


# =============================================================================
# BACKWARD COMPATIBILITY ALIASES
# =============================================================================

# Alias for backward compatibility with existing routes
ConversationResponse = ConversationDetailResponse
