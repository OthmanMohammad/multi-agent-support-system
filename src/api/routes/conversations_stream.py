"""
Conversation Streaming Routes - Server-Sent Events (SSE)

Real-time AI response streaming for chat conversations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from uuid import UUID
from typing import AsyncGenerator
import json
import asyncio

from src.api.dependencies import get_conversation_application_service
from src.api.error_handlers import map_error_to_http
from src.services.application.conversation_service import ConversationApplicationService
from src.utils.logging.setup import get_logger

router = APIRouter()
logger = get_logger(__name__)


class StreamMessageRequest(BaseModel):
    """Request model for streaming message"""
    message: str


async def stream_conversation_response(
    conversation_id: UUID,
    message: str,
    service: ConversationApplicationService
) -> AsyncGenerator[str, None]:
    """
    Stream conversation response as Server-Sent Events

    Yields SSE-formatted events:
    - content: AI response chunks
    - agent_switch: Agent handoff events
    - done: Completion event with metadata
    - error: Error events
    """
    try:
        logger.info(
            "stream_conversation_started",
            conversation_id=str(conversation_id),
            message_length=len(message)
        )

        # Validate conversation exists
        conversation = await service.uow.conversations.get_by_id(conversation_id)
        if not conversation:
            error_event = {
                "type": "error",
                "error": "Conversation not found"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            return

        if conversation.status != "active":
            error_event = {
                "type": "error",
                "error": f"Conversation is {conversation.status}, not active"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            return

        # Save user message
        await service.uow.messages.create_message(
            conversation_id=conversation.id,
            role="user",
            content=message,
            created_by=service.uow.current_user_id
        )

        # Execute workflow with streaming
        # Note: For now, we'll simulate streaming by chunking the response
        # TODO: Modify AgentWorkflowEngine to support true streaming

        agent_result = await service.workflow_engine.execute(
            message=message,
            context={
                "conversation_id": str(conversation.id),
                "customer_id": str(conversation.customer_id)
            }
        )

        # Extract response data
        response_text = agent_result.get("agent_response", "")
        intent = agent_result.get("primary_intent")
        confidence = agent_result.get("intent_confidence", 0.0)
        sentiment = agent_result.get("sentiment", 0.0)
        agent_path = agent_result.get("agent_history", [])
        agent_suggested_status = agent_result.get("status", "active")
        escalation_reason = agent_result.get("escalation_reason")
        should_escalate = agent_result.get("should_escalate", False)

        # Stream response in chunks (simulated streaming)
        words = response_text.split()
        accumulated = ""

        for i, word in enumerate(words):
            chunk = word + " "
            accumulated += chunk

            # Send content chunk
            content_event = {
                "type": "content",
                "chunk": chunk,
                "accumulated": accumulated.strip()
            }
            yield f"data: {json.dumps(content_event)}\n\n"

            # Small delay to simulate real-time streaming
            await asyncio.sleep(0.05)

        # Save agent response to database
        agent_name = agent_path[-1] if agent_path else "router"
        agent_message = await service.uow.messages.create_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            agent_name=agent_name,
            intent=intent,
            sentiment=sentiment,
            confidence=confidence,
            created_by=service.uow.current_user_id
        )

        # Apply business rules for status:
        # 1. Agents CANNOT auto-resolve - user must explicitly resolve
        # 2. Only escalate if truly needed (low confidence, negative sentiment, explicit flag)
        # 3. Default: keep conversation active
        final_status = "active"

        should_actually_escalate = (
            should_escalate or
            agent_suggested_status == "escalated" or
            (confidence < 0.4 and escalation_reason) or
            sentiment < -0.7
        )

        if should_actually_escalate:
            final_status = "escalated"
            await service.uow.conversations.mark_escalated(conversation.id)
            logger.warning(
                "stream_conversation_escalated",
                conversation_id=str(conversation_id),
                reason=escalation_reason or "Low confidence or negative sentiment",
                confidence=confidence,
                sentiment=sentiment
            )
        else:
            # Keep conversation active - user resolves when satisfied
            await service.uow.conversations.update(
                conversation.id,
                status="active",
                sentiment_avg=sentiment,
                updated_by=service.uow.current_user_id
            )

        # Commit all changes
        await service.uow.commit()

        # Send completion event
        done_event = {
            "type": "done",
            "messageId": str(agent_message.id),
            "timestamp": agent_message.created_at.isoformat(),
            "metadata": {
                "agent_name": agent_name,
                "confidence": confidence,
                "intent": intent,
                "sentiment": sentiment,
                "status": final_status,  # Use business-rule-determined status
                "agent_suggested_status": agent_suggested_status  # For debugging
            }
        }
        yield f"data: {json.dumps(done_event)}\n\n"

        logger.info(
            "stream_conversation_completed",
            conversation_id=str(conversation_id),
            message_id=str(agent_message.id),
            agent=agent_name
        )

    except Exception as e:
        logger.error(
            "stream_conversation_error",
            conversation_id=str(conversation_id),
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )

        error_event = {
            "type": "error",
            "error": str(e)
        }
        yield f"data: {json.dumps(error_event)}\n\n"


@router.post("/conversations/{conversation_id}/stream")
async def stream_message_response(
    conversation_id: UUID,
    request: StreamMessageRequest,
    service: ConversationApplicationService = Depends(get_conversation_application_service)
):
    """
    Stream AI response for a message in real-time

    Returns Server-Sent Events (SSE) stream with:
    - Real-time AI response chunks
    - Agent switch notifications
    - Completion metadata

    Example events:
    ```
    data: {"type": "content", "chunk": "I ", "accumulated": "I"}

    data: {"type": "content", "chunk": "can ", "accumulated": "I can"}

    data: {"type": "done", "messageId": "...", "metadata": {...}}
    ```
    """
    logger.info(
        "stream_message_endpoint_called",
        conversation_id=str(conversation_id),
        message_length=len(request.message)
    )

    return StreamingResponse(
        stream_conversation_response(
            conversation_id,
            request.message,
            service
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
