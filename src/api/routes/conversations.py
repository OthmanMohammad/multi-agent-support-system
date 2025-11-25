"""
Conversation routes - HTTP endpoints for conversations

"""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional, List

from src.api.models import ChatRequest, ChatResponse, EscalateRequest
from src.database.schemas.conversation import ConversationWithMessages, ConversationInDB
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


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationWithMessages,
    summary="Get conversation details",
    description="Retrieve a conversation with all its messages and metadata"
)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
) -> ConversationWithMessages:
    """Get conversation details with messages

    Returns conversation with full message history. FastAPI automatically
    converts UUID and datetime objects to JSON-serializable strings.
    """
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
        message_count=len(result.value.messages)
    )

    # Service returns ConversationWithMessages schema object
    # FastAPI handles JSON serialization automatically
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


@router.post("/conversations/{conversation_id}/reopen", status_code=200)
async def reopen_conversation(
    conversation_id: UUID,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Reopen a resolved or escalated conversation"""
    logger.info(
        "reopen_conversation_endpoint_called",
        conversation_id=str(conversation_id)
    )

    result = await service.reopen_conversation(conversation_id)

    if result.is_failure:
        logger.warning(
            "reopen_conversation_failed",
            conversation_id=str(conversation_id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "reopen_conversation_success",
        conversation_id=str(conversation_id)
    )

    return {"status": "active", "conversation_id": str(conversation_id)}


@router.post("/conversations/{conversation_id}/escalate", status_code=200)
async def escalate_conversation(
    conversation_id: UUID,
    request: EscalateRequest,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Escalate conversation to human"""
    logger.warning(
        "escalate_conversation_endpoint_called",
        conversation_id=str(conversation_id),
        reason=request.reason
    )

    result = await service.escalate_conversation(conversation_id, request.reason)

    if result.is_failure:
        logger.error(
            "escalate_conversation_failed",
            conversation_id=str(conversation_id),
            reason=request.reason,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.warning(
        "escalate_conversation_success",
        conversation_id=str(conversation_id),
        reason=request.reason
    )

    return {"status": "escalated", "conversation_id": str(conversation_id)}


@router.get(
    "/conversations",
    response_model=List[ConversationInDB],
    summary="List conversations",
    description="Retrieve a list of conversations with optional filtering"
)
async def list_conversations(
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
) -> List[ConversationInDB]:
    """List conversations with optional filters

    Returns list of conversations without messages. Use GET /conversations/{id}
    for full conversation with messages. FastAPI automatically converts UUID
    and datetime objects to JSON-serializable strings.
    """
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

    # Service returns list of ConversationInDB schema objects
    # FastAPI handles JSON serialization automatically
    return result.value


@router.delete("/conversations/{conversation_id}", status_code=200)
async def delete_conversation(
    conversation_id: UUID,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Delete a conversation and all its messages"""
    logger.warning(
        "delete_conversation_endpoint_called",
        conversation_id=str(conversation_id)
    )

    result = await service.delete_conversation(conversation_id)

    if result.is_failure:
        logger.error(
            "delete_conversation_failed",
            conversation_id=str(conversation_id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "delete_conversation_success",
        conversation_id=str(conversation_id)
    )

    return {"status": "deleted", "conversation_id": str(conversation_id)}