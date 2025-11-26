"""
Webhook Pydantic Models

Request/response models for webhook management and delivery.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

# =============================================================================
# WEBHOOK MANAGEMENT
# =============================================================================


class WebhookCreateRequest(BaseModel):
    """Create new webhook"""

    url: HttpUrl = Field(..., description="Webhook delivery URL")
    events: list[str] = Field(..., min_length=1, description="Event types to subscribe to")
    description: str | None = Field(None, max_length=500)
    secret: str | None = Field(None, description="Webhook signing secret")
    active: bool = Field(default=True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://api.example.com/webhooks/support",
                    "events": ["conversation.created", "conversation.resolved", "message.created"],
                    "description": "Production webhook for conversation events",
                    "active": True,
                }
            ]
        }
    }


class WebhookResponse(BaseModel):
    """Webhook details"""

    id: UUID
    url: str
    events: list[str]
    description: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    # Statistics
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_delivery_at: datetime | None = None
    last_delivery_status: int | None = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "url": "https://api.example.com/webhooks/support",
                    "events": ["conversation.created", "conversation.resolved"],
                    "description": "Production webhook",
                    "active": True,
                    "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-11-16T12:00:00Z",
                    "total_deliveries": 1542,
                    "successful_deliveries": 1489,
                    "failed_deliveries": 53,
                    "last_delivery_at": "2025-11-16T12:30:00Z",
                    "last_delivery_status": 200,
                }
            ]
        },
    }


class WebhookListResponse(BaseModel):
    """List of webhooks"""

    webhooks: list[WebhookResponse]
    total: int


class WebhookUpdateRequest(BaseModel):
    """Update webhook"""

    url: HttpUrl | None = None
    events: list[str] | None = None
    description: str | None = None
    active: bool | None = None


# =============================================================================
# WEBHOOK DELIVERY
# =============================================================================


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery attempt"""

    id: UUID
    webhook_id: UUID
    event_type: str
    status: Literal["pending", "delivered", "failed", "retrying"]
    http_status: int | None = None
    attempt_count: int = 0
    max_attempts: int = 3
    created_at: datetime
    delivered_at: datetime | None = None
    next_retry_at: datetime | None = None
    error_message: str | None = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "webhook_id": "987fcdeb-51a2-43d7-8c9f-123456789abc",
                    "event_type": "conversation.created",
                    "status": "delivered",
                    "http_status": 200,
                    "attempt_count": 1,
                    "max_attempts": 3,
                    "created_at": "2025-11-16T12:00:00Z",
                    "delivered_at": "2025-11-16T12:00:01Z",
                }
            ]
        },
    }


class WebhookDeliveryListResponse(BaseModel):
    """List of webhook deliveries"""

    deliveries: list[WebhookDeliveryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# WEBHOOK EVENTS
# =============================================================================


class WebhookEventList(BaseModel):
    """Available webhook event types"""

    events: list[str]
    categories: dict = Field(..., description="Events grouped by category")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "events": [
                        "conversation.created",
                        "conversation.updated",
                        "conversation.resolved",
                        "message.created",
                        "customer.created",
                        "customer.updated",
                    ],
                    "categories": {
                        "conversation": ["created", "updated", "resolved"],
                        "message": ["created"],
                        "customer": ["created", "updated", "deleted"],
                    },
                }
            ]
        }
    }
