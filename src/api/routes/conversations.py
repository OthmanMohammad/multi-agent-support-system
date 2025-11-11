"""
Conversation routes - HTTP endpoints for conversations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
from typing import Optional

from api.models import ChatRequest, ChatResponse, ConversationResponse
from api.dependencies import get_conversation_application_service
from api.error_handlers import map_error_to_http
from services.application.conversation_service import ConversationApplicationService

router = APIRouter()


@router.post("", response_model=ChatResponse, status_code=201)
async def create_conversation(
    request: ChatRequest,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Create new conversation with initial message"""
    result = await service.create_conversation(
        customer_email=request.customer_id,
        message=request.message
    )
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return ChatResponse(**result.value)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Get conversation details with messages"""
    result = await service.get_conversation(conversation_id)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return ConversationResponse(**result.value)


@router.post("/{conversation_id}/messages", response_model=ChatResponse)
async def add_message(
    conversation_id: UUID,
    request: ChatRequest,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Add message to existing conversation"""
    result = await service.add_message(
        conversation_id=conversation_id,
        message=request.message
    )
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return ChatResponse(**result.value)


@router.post("/{conversation_id}/resolve", status_code=200)
async def resolve_conversation(
    conversation_id: UUID,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Mark conversation as resolved"""
    result = await service.resolve_conversation(conversation_id)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return {"status": "resolved", "conversation_id": str(conversation_id)}


@router.post("/{conversation_id}/escalate", status_code=200)
async def escalate_conversation(
    conversation_id: UUID,
    reason: str = Query(..., description="Reason for escalation"),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """Escalate conversation to human"""
    result = await service.escalate_conversation(conversation_id, reason)
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    return {"status": "escalated", "conversation_id": str(conversation_id)}


# FIXED: Return dict directly instead of ConversationResponse
@router.get("")
async def list_conversations(
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """List conversations with optional filters"""
    result = await service.list_conversations(
        customer_email=customer_email,
        status=status,
        limit=limit
    )
    
    if result.is_failure:
        raise map_error_to_http(result.error)
    
    # Return the list directly (it's already formatted as dicts)
    return result.value