"""
Router Agent - Classifies intent and routes to specialist agents
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field
import json

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from state import AgentState, IntentCategory, AgentType
from agents.base import BaseAgent


class IntentClassification(BaseModel):
    """Structured output for intent classification"""
    primary_intent: IntentCategory = Field(
        description="Primary intent category"
    )
    confidence: float = Field(
        description="Confidence score 0-1",
        ge=0,
        le=1
    )
    sentiment: float = Field(
        description="Sentiment score -1 (negative) to 1 (positive)",
        ge=-1,
        le=1
    )
    reasoning: str = Field(
        description="Brief explanation of classification"
    )
    should_answer_directly: bool = Field(
        description="Can router answer this directly without specialist?"
    )


class RouterAgent(BaseAgent):
    """
    Router Agent - Entry point for all conversations.
    
    Responsibilities:
    1. Classify intent (billing, technical, usage, etc.)
    2. Extract entities (plan type, feature, etc.)
    3. Route to appropriate specialist OR answer directly
    """
    
    def __init__(self):
        super().__init__(
            agent_type="router",
            model="claude-3-haiku-20240307",  # Fast and cheap
            temperature=0.1  # Low temp for consistent classification
        )
    
    def process(self, state: AgentState) -> AgentState:
        """
        Process message: classify intent and route
        
        Args:
            state: Current state
            
        Returns:
            Updated state with classification and routing decision
        """
        print(f"\n{'='*60}")
        print(f"🧭 ROUTER AGENT PROCESSING")
        print(f"{'='*60}")
        
        # Add to history
        state = self.add_to_history(state)
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        # Get current message
        current_message = state["current_message"]
        print(f"Message: {current_message[:100]}...")
        
        # Classify intent
        classification = self.classify_intent(current_message)
        
        # Update state with classification
        state["primary_intent"] = classification.primary_intent
        state["intent_confidence"] = classification.confidence
        state["sentiment"] = classification.sentiment
        
        print(f"\nIntent: {classification.primary_intent}")
        print(f"Confidence: {classification.confidence:.2%}")
        print(f"Sentiment: {classification.sentiment:+.2f}")
        print(f"Reasoning: {classification.reasoning}")
        
        # Decide routing
        if classification.should_answer_directly and classification.confidence > 0.8:
            # Answer directly with KB search
            print("\n→ Decision: Answer directly (simple FAQ)")
            response = self.answer_directly(current_message, state)
            state["agent_response"] = response
            state["next_agent"] = None  # End conversation
            state["status"] = "resolved"
        
        elif classification.confidence < 0.5:
            # Low confidence - escalate
            print("\n→ Decision: Escalate (low confidence)")
            state["should_escalate"] = True
            state["escalation_reason"] = "Low intent confidence"
            state["next_agent"] = "escalation"
        
        else:
            # Route to specialist
            next_agent = self.route_to_specialist(classification.primary_intent)
            print(f"\n→ Decision: Route to {next_agent.upper()} agent")
            state["next_agent"] = next_agent
        
        state["response_confidence"] = classification.confidence
        
        return state
    
    def classify_intent(self, message: str) -> IntentClassification:
        """
        Classify user intent using Claude with structured output
        
        Args:
            message: User's message
            
        Returns:
            IntentClassification with primary_intent, confidence, etc.
        """
        system_prompt = """You are an intent classifier for a customer support system.

Analyze the user's message and classify their primary intent into ONE of these categories:

BILLING:
- billing_upgrade: Wants to upgrade plan
- billing_downgrade: Wants to downgrade plan  
- billing_refund: Requesting refund
- billing_invoice: Needs invoice or payment info

TECHNICAL:
- technical_bug: Reporting a bug or error
- technical_sync: Sync or data update issues
- technical_performance: Performance/speed problems

FEATURES (Usage):
- feature_create: How to create something (project, task, etc.)
- feature_edit: How to edit/modify something
- feature_invite: How to invite/add team members
- feature_export: How to export data

INTEGRATIONS:
- integration_api: API questions
- integration_webhook: Webhook questions

ACCOUNT:
- account_login: Login or authentication issues

GENERAL:
- general_inquiry: General questions, greetings, unclear intent

Return your classification with confidence (0-1) and reasoning."""

        user_prompt = f"""Classify this message:

"{message}"

Return JSON with:
{{
  "primary_intent": "category_name",
  "confidence": 0.0-1.0,
  "sentiment": -1.0 to 1.0,
  "reasoning": "brief explanation",
  "should_answer_directly": true/false (true if simple FAQ, false if needs specialist)
}}"""

        # Call Claude
        response_text = self.call_llm(system_prompt, user_prompt, max_tokens=500)
        
        # Parse JSON response
        try:
            # Extract JSON from response (Claude might add text around it)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            data = json.loads(json_str)
            
            # Validate and create classification
            classification = IntentClassification(**data)
            return classification
            
        except Exception as e:
            print(f"⚠ Classification parsing failed: {e}")
            # Default fallback
            return IntentClassification(
                primary_intent="general_inquiry",
                confidence=0.3,
                sentiment=0.0,
                reasoning="Failed to parse classification",
                should_answer_directly=False
            )
    
    def route_to_specialist(self, intent: IntentCategory) -> AgentType:
        """
        Map intent to specialist agent
        
        Args:
            intent: Classified intent
            
        Returns:
            Agent type to route to
        """
        # Intent → Agent mapping
        routing_map = {
            "billing_upgrade": "billing",
            "billing_downgrade": "billing",
            "billing_refund": "billing",
            "billing_invoice": "billing",
            
            "technical_bug": "technical",
            "technical_sync": "technical",
            "technical_performance": "technical",
            
            "feature_create": "usage",
            "feature_edit": "usage",
            "feature_invite": "usage",
            "feature_export": "usage",
            
            "integration_api": "api",
            "integration_webhook": "api",
            
            "account_login": "technical",  # Login issues are technical
            
            "general_inquiry": "escalation"  # Unclear → human
        }
        
        return routing_map.get(intent, "escalation")
    
    def answer_directly(self, message: str, state: AgentState) -> str:
        """
        Answer simple FAQs directly using KB search
        
        Args:
            message: User's message
            state: Current state
            
        Returns:
            Direct answer
        """
        # Import KB search
        from knowledge_base import search_articles
        
        # Search KB
        kb_results = search_articles(message, limit=2)
        state["kb_results"] = kb_results
        
        if not kb_results:
            return "I'm not sure about that. Let me connect you with a specialist who can help."
        
        # Build context
        kb_context = "\n\n".join([
            f"Article: {r['title']}\n{r['content']}"
            for r in kb_results
        ])
        
        # Generate answer
        system_prompt = """You are a helpful customer support agent.

Answer the user's question using ONLY the knowledge base articles provided.
Be concise and friendly. Cite the article title."""

        user_prompt = f"""Question: {message}

Knowledge Base:
{kb_context}

Provide a helpful answer."""

        response = self.call_llm(system_prompt, user_prompt, max_tokens=300)
        
        return response


if __name__ == "__main__":
    # Test router agent
    print("=" * 60)
    print("TESTING ROUTER AGENT")
    print("=" * 60)
    
    from state import create_initial_state
    
    # Test cases
    test_messages = [
        "I want to upgrade to premium",
        "My project is not syncing",
        "How do I invite team members?",
        "What are your prices?",
    ]
    
    router = RouterAgent()
    
    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"TEST: {msg}")
        print(f"{'='*60}")
        
        state = create_initial_state(msg)
        result = router.process(state)
        
        print(f"\nRESULT:")
        print(f"  Intent: {result['primary_intent']}")
        print(f"  Confidence: {result['intent_confidence']:.2%}")
        print(f"  Next Agent: {result.get('next_agent', 'END')}")
        
        if result.get("agent_response"):
            print(f"\n  Response: {result['agent_response'][:100]}...")