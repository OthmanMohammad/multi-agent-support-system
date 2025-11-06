"""
FastAPI Application - REST API for multi-agent support system
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import time
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from api.models import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    HealthResponse,
    MetricsResponse
)
from api.dependencies import get_uow
from database.unit_of_work import UnitOfWork
from database.connection import init_db, close_db
from workflow.graph import SupportGraph

# Initialize
app = FastAPI(
    title="Multi-Agent Customer Support API",
    description="Production-ready multi-agent support system with LangGraph",
    version="2.0.0"
)

# CORS (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
graph: SupportGraph = None
start_time = time.time()


@app.on_event("startup")
async def startup_event():
    """Initialize graph and database on startup"""
    global graph
    print("🚀 Starting Multi-Agent API...")
    
    # Initialize database
    print("📊 Initializing database...")
    await init_db()
    print("✓ Database ready")
    
    # Initialize graph
    graph = SupportGraph()
    print("✓ API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down...")
    await close_db()
    print("✓ Database connections closed")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent Customer Support API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check Qdrant connection
        from vector_store import VectorStore
        vs = VectorStore()
        qdrant_connected = True
    except:
        qdrant_connected = False
    
    return HealthResponse(
        status="healthy" if graph is not None else "unhealthy",
        version="2.0.0",
        agents_loaded=["router", "billing", "technical", "usage", "api", "escalation"],
        qdrant_connected=qdrant_connected,
        timestamp=datetime.now().isoformat()
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Chat endpoint with database persistence using Unit of Work
    
    All database operations happen in a single transaction:
    - Get or create customer
    - Create or get conversation
    - Save user message
    - Run agent graph (no DB operations)
    - Save agent response
    - Update conversation metadata
    
    Args:
        request: ChatRequest with message and optional conversation_id
        uow: Unit of Work for transaction management
        
    Returns:
        ChatResponse with agent's response
        
    Raises:
        HTTPException: On validation or processing errors
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    try:
        # ===== TRANSACTION START =====
        # All operations below are in a single atomic transaction
        
        # 1. Get or create customer
        customer = await uow.customers.get_or_create_by_email(
            email=request.customer_id  # Using email as customer_id
        )
        
        # 2. Create or get conversation
        if request.conversation_id:
            try:
                conversation_uuid = UUID(request.conversation_id)
                conversation = await uow.conversations.get_by_id(conversation_uuid)
                if not conversation:
                    raise HTTPException(404, "Conversation not found")
            except ValueError:
                raise HTTPException(400, "Invalid conversation_id format")
        else:
            conversation = await uow.conversations.create_with_customer(
                customer_id=customer.id,
                status="active",
                created_by=uow.current_user_id  # Audit trail
            )
        
        # 3. Save user message to database
        user_message = await uow.messages.create_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
            created_by=uow.current_user_id  # Audit trail
        )
        
        # 4. Run through graph (NO database operations inside)
        result = graph.run(request.message, conversation_id=str(conversation.id))
        
        # Extract response data
        response_text = result.get("agent_response", "I'm not sure how to help with that.")
        agent_path = result.get("agent_history", [])
        intent = result.get("primary_intent")
        confidence = result.get("intent_confidence")
        sentiment = result.get("sentiment", 0.0)
        status = result.get("status", "active")
        
        # KB articles used
        kb_articles = [
            article["title"]
            for article in result.get("kb_results", [])
        ]
        
        # 5. Save agent response to database
        agent_name = agent_path[-1] if agent_path else "unknown"
        agent_message = await uow.messages.create_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            agent_name=agent_name,
            intent=intent,
            sentiment=sentiment,
            confidence=confidence,
            created_by=uow.current_user_id  # Audit trail
        )
        
        # 6. Update conversation metadata
        await uow.conversations.update(
            conversation.id,
            primary_intent=intent,
            agents_involved=agent_path,
            sentiment_avg=sentiment,
            kb_articles_used=kb_articles,
            updated_by=uow.current_user_id  # Audit trail
        )
        
        # 7. Mark as resolved or escalated if done
        if status == "resolved":
            resolution_time = int(
                (datetime.utcnow() - conversation.started_at).total_seconds()
            )
            await uow.conversations.mark_resolved(conversation.id, resolution_time)
        elif status == "escalated":
            await uow.conversations.mark_escalated(conversation.id)
        
        # ===== TRANSACTION COMMITS HERE (automatic via UoW context manager) =====
        
        return ChatResponse(
            conversation_id=str(conversation.id),
            message=response_text,
            intent=intent,
            confidence=confidence,
            agent_path=agent_path,
            kb_articles_used=kb_articles,
            status=status,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Any exception triggers automatic rollback via UoW
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Streaming chat endpoint - returns Server-Sent Events
    
    NOTE: This endpoint still uses UoW but handles transactions differently
    because of the streaming nature. Consider refactoring for proper
    transaction boundaries.
    
    Args:
        request: ChatRequest with stream=True
        uow: Unit of Work (limited use due to streaming)
        
    Returns:
        SSE stream with response chunks
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    async def generate_response() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        try:
            # NOTE: Using separate UoW context for streaming
            # This is not ideal but necessary for streaming responses
            
            # Get or create customer
            customer = await uow.customers.get_or_create_by_email(
                email=request.customer_id
            )
            
            # Create or get conversation
            if request.conversation_id:
                try:
                    conversation_uuid = UUID(request.conversation_id)
                    conversation = await uow.conversations.get_by_id(conversation_uuid)
                except:
                    conversation = await uow.conversations.create_with_customer(
                        customer_id=customer.id
                    )
            else:
                conversation = await uow.conversations.create_with_customer(
                    customer_id=customer.id
                )
            
            # Send conversation ID first
            yield {
                "event": "conversation_id",
                "data": str(conversation.id)
            }
            
            # Add user message
            await uow.messages.create_message(
                conversation_id=conversation.id,
                role="user",
                content=request.message
            )
            
            # Send thinking event
            yield {
                "event": "thinking",
                "data": "Processing your request..."
            }
            
            # Run through graph
            result = graph.run(request.message, conversation_id=str(conversation.id))
            
            # Send intent
            intent = result.get("primary_intent")
            if intent:
                yield {
                    "event": "intent",
                    "data": intent
                }
            
            # Send agent path
            agent_path = result.get("agent_history", [])
            if agent_path:
                yield {
                    "event": "agent_path",
                    "data": " → ".join(agent_path)
                }
            
            # Stream response (chunk by sentences)
            response_text = result.get("agent_response", "")
            sentences = response_text.split(". ")
            
            for sentence in sentences:
                if sentence.strip():
                    yield {
                        "event": "message",
                        "data": sentence + ". "
                    }
                    await asyncio.sleep(0.1)
            
            # Save to database
            agent_name = agent_path[-1] if agent_path else "unknown"
            await uow.messages.create_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                agent_name=agent_name,
                intent=intent,
                sentiment=result.get("sentiment", 0.0),
                confidence=result.get("intent_confidence")
            )
            
            # Update conversation
            await uow.conversations.update(
                conversation.id,
                primary_intent=intent,
                agents_involved=agent_path,
                sentiment_avg=result.get("sentiment", 0.0)
            )
            
            # Send done event
            yield {
                "event": "done",
                "data": "complete"
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "data": str(e)
            }
    
    return EventSourceResponse(generate_response())


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Get full conversation history from database
    
    Args:
        conversation_id: Conversation ID
        uow: Unit of Work
        
    Returns:
        Full conversation with messages
    """
    try:
        conversation_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id format")
    
    conversation = await uow.conversations.get_with_messages(conversation_uuid)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Format messages
    messages = [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat(),
            "agent_name": msg.agent_name
        }
        for msg in conversation.messages
    ]
    
    return ConversationResponse(
        conversation_id=str(conversation.id),
        customer_id=str(conversation.customer_id),
        messages=messages,
        agent_history=conversation.agents_involved or [],
        status=conversation.status,
        started_at=conversation.started_at.isoformat(),
        last_updated=conversation.ended_at.isoformat() if conversation.ended_at 
                     else conversation.started_at.isoformat()
    )


@app.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    customer_id: str = None,
    limit: int = 50,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    List conversations from database
    
    Args:
        customer_id: Optional customer email filter
        limit: Max results (default 50)
        uow: Unit of Work
        
    Returns:
        List of conversations
    """
    if customer_id:
        # Get customer by email
        customer = await uow.customers.get_by_email(customer_id)
        if not customer:
            return []
        conversations = await uow.conversations.get_by_customer(customer.id, limit=limit)
    else:
        conversations = await uow.conversations.get_all(limit=limit)
    
    return [
        ConversationResponse(
            conversation_id=str(conv.id),
            customer_id=str(conv.customer_id),
            messages=[],  # Don't load messages for list view
            agent_history=conv.agents_involved or [],
            status=conv.status,
            started_at=conv.started_at.isoformat(),
            last_updated=conv.ended_at.isoformat() if conv.ended_at
                         else conv.started_at.isoformat()
        )
        for conv in conversations
    ]


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Get system metrics from database
    
    Returns:
        System statistics
    """
    # Get statistics from database
    stats = await uow.conversations.get_statistics(days=7)
    
    # Calculate uptime
    uptime = time.time() - start_time
    
    return MetricsResponse(
        total_conversations=stats["total_conversations"],
        total_messages=stats["total_conversations"] * 2,  # Approximate
        intent_distribution=stats.get("by_status", {}),
        agent_usage={},  # TODO: Aggregate from conversations
        avg_confidence=0.85,  # TODO: Calculate from messages
        uptime_seconds=uptime
    )


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Soft delete a conversation
    
    Args:
        conversation_id: Conversation ID to delete
        uow: Unit of Work
        
    Returns:
        Success message
    """
    try:
        conversation_uuid = UUID(conversation_id)
        # Use soft delete instead of hard delete
        deleted = await uow.conversations.soft_delete_by_id(conversation_uuid)
        if deleted:
            return {"message": "Conversation deleted (soft delete)"}
        raise HTTPException(status_code=404, detail="Conversation not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id format")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("Starting Multi-Agent Support API v2.0")
    print("=" * 70)
    print("NEW: Unit of Work transaction management")
    print("NEW: Audit trail support")
    print("NEW: Soft delete functionality")
    print("=" * 70)
    print("Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )