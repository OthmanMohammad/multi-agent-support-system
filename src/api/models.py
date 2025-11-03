"""
API Models - Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class ChatRequest(BaseModel):
    """Request to chat endpoint"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    customer_id: Optional[str] = Field("default_customer", description="Customer identifier")
    stream: bool = Field(False, description="Enable streaming responses")


class MessageDetail(BaseModel):
    """Single message in conversation"""
    role: str
    content: str
    timestamp: str
    agent_name: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    conversation_id: str
    message: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    agent_path: List[str]
    kb_articles_used: List[str] = []
    status: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Full conversation history"""
    conversation_id: str
    customer_id: str
    messages: List[MessageDetail]
    agent_history: List[str]
    status: str
    started_at: str
    last_updated: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    agents_loaded: List[str]
    qdrant_connected: bool
    timestamp: str


class MetricsResponse(BaseModel):
    """System metrics"""
    total_conversations: int
    total_messages: int
    intent_distribution: Dict[str, int]
    agent_usage: Dict[str, int]
    avg_confidence: float
    uptime_seconds: float