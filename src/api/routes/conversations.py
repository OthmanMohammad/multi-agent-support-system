"""
Conversation routes - HTTP endpoints for conversations

"""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from src.api.models import ChatRequest, ChatResponse, ConversationResponse
from src.api.dependencies import get_conversation_application_service
from src.api.error_handlers import map_error_to_http
from src.services.application.conversation_service import ConversationApplicationService
from src.utils.logging.setup import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/conversations", response_model=ChatResponse, status_code=201)
async def create_conversation(
    request: ChatRequest,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Create new conversation with initial message"""
    # Use customer_email if provided, otherwise use default
    customer_email = getattr(request, 'customer_email', None) or getattr(request, 'customer_id', 'default@example.com')

    logger.info(
        "create_conversation_endpoint_called",
        customer_email=customer_email,
        message_length=len(request.message)
    )

    result = await service.create_conversation(
        customer_email=customer_email,
        message=request.message
    )

    if result.is_failure:
        logger.warning(
            "create_conversation_failed",
            customer_email=customer_email,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "create_conversation_success",
        conversation_id=result.value.get("conversation_id"),
        customer_email=customer_email,
        status=result.value.get("status")
    )
    
    return ChatResponse(**result.value)


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Get conversation details with messages"""
    logger.debug(
        "get_conversation_endpoint_called",
        conversation_id=str(conversation_id)
    )

    result = await service.get_conversation(conversation_id)

    if result.is_failure:
        logger.warning(
            "get_conversation_failed",
            conversation_id=str(conversation_id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.debug(
        "get_conversation_success",
        conversation_id=str(conversation_id),
        message_count=len(result.value.get("messages", []))
    )

    return result.value


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def add_message(
    conversation_id: UUID,
    request: ChatRequest,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Add message to existing conversation"""
    logger.info(
        "add_message_endpoint_called",
        conversation_id=str(conversation_id),
        message_length=len(request.message)
    )
    
    result = await service.add_message(
        conversation_id=conversation_id,
        message=request.message
    )
    
    if result.is_failure:
        logger.warning(
            "add_message_failed",
            conversation_id=str(conversation_id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "add_message_success",
        conversation_id=str(conversation_id),
        status=result.value.get("status")
    )
    
    return ChatResponse(**result.value)


@router.post("/conversations/{conversation_id}/resolve", status_code=200)
async def resolve_conversation(
    conversation_id: UUID,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Mark conversation as resolved"""
    logger.info(
        "resolve_conversation_endpoint_called",
        conversation_id=str(conversation_id)
    )
    
    result = await service.resolve_conversation(conversation_id)
    
    if result.is_failure:
        logger.warning(
            "resolve_conversation_failed",
            conversation_id=str(conversation_id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "resolve_conversation_success",
        conversation_id=str(conversation_id)
    )
    
    return {"status": "resolved", "conversation_id": str(conversation_id)}


@router.post("/conversations/{conversation_id}/escalate", status_code=200)
async def escalate_conversation(
    conversation_id: UUID,
    reason: str = Query(..., description="Reason for escalation"),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Escalate conversation to human"""
    logger.warning(
        "escalate_conversation_endpoint_called",
        conversation_id=str(conversation_id),
        reason=reason
    )
    
    result = await service.escalate_conversation(conversation_id, reason)
    
    if result.is_failure:
        logger.error(
            "escalate_conversation_failed",
            conversation_id=str(conversation_id),
            reason=reason,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.warning(
        "escalate_conversation_success",
        conversation_id=str(conversation_id),
        reason=reason
    )
    
    return {"status": "escalated", "conversation_id": str(conversation_id)}


@router.get("/conversations")
async def list_conversations(
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """List conversations with optional filters"""
    logger.debug(
        "list_conversations_endpoint_called",
        customer_email=customer_email,
        status=status,
        limit=limit
    )
    
    result = await service.list_conversations(
        customer_email=customer_email,
        status=status,
        limit=limit
    )
    
    if result.is_failure:
        logger.warning(
            "list_conversations_failed",
            customer_email=customer_email,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)
    
    logger.info(
        "list_conversations_success",
        count=len(result.value),
        customer_email=customer_email,
        status=status
    )
    
    # Return the list directly (it's already formatted as dicts)
    return result.value