"""
Agent State - Shared state passed between agents in LangGraph
"""
from typing import TypedDict, List, Dict, Optional, Literal
from datetime import datetime


# Agent types
AgentType = Literal[
    "router",
    "billing", 
    "technical",
    "usage",
    "api",
    "escalation"
]

# Intent categories (13 total from spec)
IntentCategory = Literal[
    "billing_upgrade",
    "billing_downgrade", 
    "billing_refund",
    "billing_invoice",
    "technical_bug",
    "technical_sync",
    "technical_performance",
    "feature_create",
    "feature_edit",
    "feature_invite",
    "feature_export",
    "integration_api",
    "integration_webhook",
    "account_login",
    "general_inquiry"  # Catch-all
]


class Message(TypedDict):
    """Single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    agent_name: Optional[str]  # Which agent sent this


class AgentState(TypedDict, total=False):
    """
    State passed between agents in LangGraph.
    
    Total=False means all fields are optional (safer for gradual updates)
    """
    
    # ===== CONVERSATION =====
    conversation_id: str
    customer_id: str
    messages: List[Message]  # Full conversation history
    current_message: str  # User's latest message
    
    # ===== ROUTING =====
    current_agent: AgentType  # Which agent is handling this now
    agent_history: List[AgentType]  # Which agents have been involved
    next_agent: Optional[AgentType]  # Where to route next (None = END)
    
    # ===== CLASSIFICATION =====
    primary_intent: Optional[IntentCategory]  # What user wants
    intent_confidence: float  # 0-1 confidence score
    entities: Dict[str, any]  # Extracted entities (plan_type, feature, etc.)
    sentiment: float  # -1 (negative) to 1 (positive)
    
    # ===== CONTEXT =====
    customer_metadata: Dict[str, any]  # plan, account_age, tier, etc.
    kb_results: List[Dict]  # Knowledge base search results
    
    # ===== RESPONSE =====
    agent_response: Optional[str]  # Agent's response to user
    tools_used: List[str]  # Which tools were called
    response_confidence: float  # How confident agent is in response
    
    # ===== CONTROL FLOW =====
    should_escalate: bool  # Should we escalate to human?
    escalation_reason: Optional[str]  # Why escalate?
    status: str  # "active", "resolved", "escalated"
    max_turns: int  # Safety: max agent hops
    turn_count: int  # Current turn number


def create_initial_state(
    message: str,
    conversation_id: str = None,
    customer_id: str = "default_customer"
) -> AgentState:
    """
    Create initial state for a new conversation
    
    Args:
        message: User's first message
        conversation_id: Optional conversation ID
        customer_id: Customer identifier
        
    Returns:
        Initial AgentState
    """
    from uuid import uuid4
    
    if conversation_id is None:
        conversation_id = str(uuid4())
    
    return AgentState(
        # Conversation
        conversation_id=conversation_id,
        customer_id=customer_id,
        messages=[
            Message(
                role="user",
                content=message,
                timestamp=datetime.now().isoformat(),
                agent_name=None
            )
        ],
        current_message=message,
        
        # Routing
        current_agent="router",  # Always start with router
        agent_history=[],
        next_agent=None,
        
        # Classification (will be filled by router)
        primary_intent=None,
        intent_confidence=0.0,
        entities={},
        sentiment=0.0,
        
        # Context
        customer_metadata={
            "plan": "free",  # Default
            "account_age_days": 0
        },
        kb_results=[],
        
        # Response
        agent_response=None,
        tools_used=[],
        response_confidence=0.0,
        
        # Control
        should_escalate=False,
        escalation_reason=None,
        status="active",
        max_turns=5,  # Safety: prevent infinite loops
        turn_count=0
    )


if __name__ == "__main__":
    # Test state creation
    print("Testing AgentState creation...")
    print("=" * 60)
    
    state = create_initial_state(
        message="I want to upgrade my plan",
        customer_id="test_user_123"
    )
    
    print(f"Conversation ID: {state['conversation_id']}")
    print(f"Current Message: {state['current_message']}")
    print(f"Current Agent: {state['current_agent']}")
    print(f"Status: {state['status']}")
    print(f"Messages: {len(state['messages'])}")
    
    print("\n✓ AgentState working correctly!")