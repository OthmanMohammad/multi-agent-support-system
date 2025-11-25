"""
Conversation routes - HTTP endpoints for conversations

All endpoints require authentication via JWT token or API key.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional, List

from src.api.models import ChatRequest, ChatResponse, EscalateRequest
from src.database.schemas.conversation import ConversationWithMessages, ConversationInDB
from src.database.models.user import User, UserRole
from src.api.dependencies import get_conversation_application_service
from src.api.dependencies.auth_dependencies import get_current_user_or_api_key
from src.api.error_handlers import map_error_to_http
from src.services.application.conversation_service import ConversationApplicationService
from src.utils.logging.setup import get_logger

router = APIRouter()
logger = get_logger(__name__)


async def verify_conversation_access(
    conversation_id: UUID,
    current_user: User,
    service: ConversationApplicationService
) -> None:
    """
    Verify that the current user has access to the specified conversation.

    Access control:
    - Admin/Super Admin: Can access any conversation
    - Regular users: Can only access their own conversations

    Raises:
        HTTPException(403): If user doesn't have permission to access the conversation
        HTTPException(404): If conversation not found
    """
    is_admin = current_user.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN)

    if is_admin:
        return  # Admins can access all conversations

    # Get conversation with customer relationship
    conversation = await service.uow.conversations.get_by_id(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.customer:
        customer_email = conversation.customer.email
        if customer_email != current_user.email:
            logger.warning(
                "conversation_access_denied",
                conversation_id=str(conversation_id),
                user_email=current_user.email,
                customer_email=customer_email
            )
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this conversation"
            )


@router.post("/conversations", response_model=ChatResponse, status_code=201)
async def create_conversation(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Create new conversation with initial message

    Requires authentication via JWT token or API key.
    """
    # Use customer_email if provided, otherwise use authenticated user's email
    customer_email = getattr(request, 'customer_email', None) or current_user.email

    logger.info(
        "create_conversation_endpoint_called",
        customer_email=customer_email,
        user_id=str(current_user.id),
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
            user_id=str(current_user.id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "create_conversation_success",
        conversation_id=result.value.get("conversation_id"),
        customer_email=customer_email,
        user_id=str(current_user.id),
        status=result.value.get("status")
    )

    return ChatResponse(**result.value)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationWithMessages,
    summary="Get conversation details",
    description="Retrieve a conversation with all its messages and metadata. Requires authentication."
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
) -> ConversationWithMessages:
    """Get conversation details with messages

    Requires authentication via JWT token or API key.

    Access control:
    - Admin/Super Admin: Can access any conversation
    - Regular users: Can only access their own conversations

    Returns conversation with full message history. FastAPI automatically
    converts UUID and datetime objects to JSON-serializable strings.
    """
    logger.debug(
        "get_conversation_endpoint_called",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id)
    )

    # Authorization check
    await verify_conversation_access(conversation_id, current_user, service)

    result = await service.get_conversation(conversation_id)

    if result.is_failure:
        logger.warning(
            "get_conversation_failed",
            conversation_id=str(conversation_id),
            user_id=str(current_user.id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.debug(
        "get_conversation_success",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id),
        message_count=len(result.value.messages)
    )

    # Service returns ConversationWithMessages schema object
    # FastAPI handles JSON serialization automatically
    return result.value


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def add_message(
    conversation_id: UUID,
    request: ChatRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Add message to existing conversation

    Requires authentication via JWT token or API key.
    """
    logger.info(
        "add_message_endpoint_called",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id),
        message_length=len(request.message)
    )

    # Authorization check
    await verify_conversation_access(conversation_id, current_user, service)

    result = await service.add_message(
        conversation_id=conversation_id,
        message=request.message
    )

    if result.is_failure:
        logger.warning(
            "add_message_failed",
            conversation_id=str(conversation_id),
            user_id=str(current_user.id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "add_message_success",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id),
        status=result.value.get("status")
    )

    return ChatResponse(**result.value)


@router.post("/conversations/{conversation_id}/resolve", status_code=200)
async def resolve_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Mark conversation as resolved

    Requires authentication via JWT token or API key.
    """
    logger.info(
        "resolve_conversation_endpoint_called",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id)
    )

    # Authorization check
    await verify_conversation_access(conversation_id, current_user, service)

    result = await service.resolve_conversation(conversation_id)

    if result.is_failure:
        logger.warning(
            "resolve_conversation_failed",
            conversation_id=str(conversation_id),
            user_id=str(current_user.id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "resolve_conversation_success",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id)
    )

    return {"status": "resolved", "conversation_id": str(conversation_id)}


@router.post("/conversations/{conversation_id}/reopen", status_code=200)
async def reopen_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Reopen a resolved or escalated conversation

    Requires authentication via JWT token or API key.
    """
    logger.info(
        "reopen_conversation_endpoint_called",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id)
    )

    # Authorization check
    await verify_conversation_access(conversation_id, current_user, service)

    result = await service.reopen_conversation(conversation_id)

    if result.is_failure:
        logger.warning(
            "reopen_conversation_failed",
            conversation_id=str(conversation_id),
            user_id=str(current_user.id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "reopen_conversation_success",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id)
    )

    return {"status": "active", "conversation_id": str(conversation_id)}


@router.post("/conversations/{conversation_id}/escalate", status_code=200)
async def escalate_conversation(
    conversation_id: UUID,
    request: EscalateRequest,
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Escalate conversation to human

    Requires authentication via JWT token or API key.
    """
    logger.warning(
        "escalate_conversation_endpoint_called",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id),
        reason=request.reason
    )

    # Authorization check
    await verify_conversation_access(conversation_id, current_user, service)

    result = await service.escalate_conversation(conversation_id, request.reason)

    if result.is_failure:
        logger.error(
            "escalate_conversation_failed",
            conversation_id=str(conversation_id),
            user_id=str(current_user.id),
            reason=request.reason,
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.warning(
        "escalate_conversation_success",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id),
        reason=request.reason
    )

    return {"status": "escalated", "conversation_id": str(conversation_id)}


@router.get(
    "/conversations",
    response_model=List[ConversationInDB],
    summary="List conversations",
    description="Retrieve a list of conversations with optional filtering. Requires authentication."
)
async def list_conversations(
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
) -> List[ConversationInDB]:
    """List conversations with optional filters

    Requires authentication via JWT token or API key.

    Access control:
    - Admin/Super Admin: Can see all conversations, optionally filtered by customer_email
    - Regular users: Can only see their own conversations (customer_email = user email)

    Returns list of conversations without messages. Use GET /conversations/{id}
    for full conversation with messages. FastAPI automatically converts UUID
    and datetime objects to JSON-serializable strings.
    """
    # Determine the effective customer_email filter based on user role
    # Admins can see all or filter; regular users can only see their own
    from src.database.models.user import UserRole

    is_admin = current_user.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN)

    if is_admin:
        # Admins can filter by any customer_email or see all
        effective_customer_email = customer_email
    else:
        # Regular users can ONLY see their own conversations
        # Override any provided customer_email filter for security
        effective_customer_email = current_user.email

    logger.debug(
        "list_conversations_endpoint_called",
        customer_email=effective_customer_email,
        original_filter=customer_email,
        status=status,
        limit=limit,
        user_id=str(current_user.id),
        user_role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        is_admin=is_admin
    )

    result = await service.list_conversations(
        customer_email=effective_customer_email,
        status=status,
        limit=limit
    )

    if result.is_failure:
        logger.warning(
            "list_conversations_failed",
            customer_email=customer_email,
            user_id=str(current_user.id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "list_conversations_success",
        count=len(result.value),
        customer_email=customer_email,
        status=status,
        user_id=str(current_user.id)
    )

    # Service returns list of ConversationInDB schema objects
    # FastAPI handles JSON serialization automatically
    return result.value


@router.delete("/conversations/{conversation_id}", status_code=200)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user_or_api_key),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Delete a conversation and all its messages

    Requires authentication via JWT token or API key.
    """
    logger.warning(
        "delete_conversation_endpoint_called",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id)
    )

    # Authorization check
    await verify_conversation_access(conversation_id, current_user, service)

    result = await service.delete_conversation(conversation_id)

    if result.is_failure:
        logger.error(
            "delete_conversation_failed",
            conversation_id=str(conversation_id),
            user_id=str(current_user.id),
            error_type=type(result.error).__name__
        )
        raise map_error_to_http(result.error)

    logger.info(
        "delete_conversation_success",
        conversation_id=str(conversation_id),
        user_id=str(current_user.id)
    )

    return {"status": "deleted", "conversation_id": str(conversation_id)}
