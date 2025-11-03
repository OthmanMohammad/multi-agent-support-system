"""
FastAPI Application - REST API for multi-agent support system
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import time
from datetime import datetime
from typing import AsyncGenerator

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
from api.storage import get_store
from graph import SupportGraph

# Initialize
app = FastAPI(
    title="Multi-Agent Customer Support API",
    description="Production-ready multi-agent support system with LangGraph",
    version="1.0.0"
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
store = get_store()
start_time = time.time()


@app.on_event("startup")
async def startup_event():
    """Initialize graph on startup"""
    global graph
    print("🚀 Starting Multi-Agent API...")
    graph = SupportGraph()
    print("✓ API ready!")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent Customer Support API",
        "version": "1.0.0",
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
        version="1.0.0",
        agents_loaded=["router", "billing", "technical", "usage", "escalation"],
        qdrant_connected=qdrant_connected,
        timestamp=datetime.now().isoformat()
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - send message and get response
    
    Args:
        request: ChatRequest with message and optional conversation_id
        
    Returns:
        ChatResponse with agent's response
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    try:
        # Create or get conversation
        if request.conversation_id:
            conv_id = request.conversation_id
        else:
            conv_id = store.create_conversation(customer_id=request.customer_id)
        
        # Add user message to storage
        store.add_message(conv_id, "user", request.message)
        
        # Run through graph
        result = graph.run(request.message, conversation_id=conv_id)
        
        # Extract response data
        response_text = result.get("agent_response", "I'm not sure how to help with that.")
        agent_path = result.get("agent_history", [])
        intent = result.get("primary_intent")
        confidence = result.get("intent_confidence")
        status = result.get("status", "active")
        
        # KB articles used
        kb_articles = [
            article["title"]
            for article in result.get("kb_results", [])
        ]
        
        # Add assistant message to storage
        agent_name = agent_path[-1] if agent_path else "unknown"
        store.add_message(conv_id, "assistant", response_text, agent_name=agent_name)
        
        # Update storage metadata
        store.update_agent_history(conv_id, agent_path)
        store.update_status(conv_id, status)
        
        return ChatResponse(
            conversation_id=conv_id,
            message=response_text,
            intent=intent,
            confidence=confidence,
            agent_path=agent_path,
            kb_articles_used=kb_articles,
            status=status,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint - returns Server-Sent Events
    
    Args:
        request: ChatRequest with stream=True
        
    Returns:
        SSE stream with response chunks
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    async def generate_response() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        try:
            # Create conversation
            if request.conversation_id:
                conv_id = request.conversation_id
            else:
                conv_id = store.create_conversation(customer_id=request.customer_id)
            
            # Send conversation ID first
            yield {
                "event": "conversation_id",
                "data": conv_id
            }
            
            # Add user message
            store.add_message(conv_id, "user", request.message)
            
            # Send thinking event
            yield {
                "event": "thinking",
                "data": "Processing your request..."
            }
            
            # Simulate streaming (in real impl, we'd stream from Claude)
            # For now, get full response and chunk it
            result = graph.run(request.message, conversation_id=conv_id)
            
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
                    await asyncio.sleep(0.1)  # Simulate streaming delay
            
            # Add to storage
            agent_name = agent_path[-1] if agent_path else "unknown"
            store.add_message(conv_id, "assistant", response_text, agent_name=agent_name)
            store.update_agent_history(conv_id, agent_path)
            store.update_status(conv_id, result.get("status", "active"))
            
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
async def get_conversation(conversation_id: str):
    """
    Get full conversation history
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Full conversation with messages
    """
    conversation = store.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationResponse(**conversation)


@app.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    customer_id: str = None,
    limit: int = 50
):
    """
    List conversations
    
    Args:
        customer_id: Optional customer filter
        limit: Max results (default 50)
        
    Returns:
        List of conversations
    """
    conversations = store.list_conversations(customer_id=customer_id, limit=limit)
    return [ConversationResponse(**c) for c in conversations]


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get system metrics
    
    Returns:
        System statistics
    """
    stats = store.get_stats()
    
    # Calculate uptime
    uptime = time.time() - start_time
    
    return MetricsResponse(
        total_conversations=stats["total_conversations"],
        total_messages=stats["total_messages"],
        intent_distribution={},  # TODO: Track intents
        agent_usage=stats["agent_usage"],
        avg_confidence=0.85,  # TODO: Track actual confidence
        uptime_seconds=uptime
    )


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation (for testing)"""
    if conversation_id in store.conversations:
        del store.conversations[conversation_id]
        return {"message": "Conversation deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 Starting Multi-Agent Support API")
    print("=" * 70)
    print("Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )