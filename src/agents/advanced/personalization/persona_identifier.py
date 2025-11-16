"""Persona Identifier Agent - TASK-4021"""
from typing import Dict, Any
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("persona_identifier", tier="advanced", category="personalization")
class PersonaIdentifierAgent(BaseAgent):
    """Identify customer persona (executive, power_user, manager, casual_user, champion)."""
    
    PERSONAS = {"executive": "C-level, ROI-focused", "power_user": "Technical, API-heavy", "manager": "Team lead", "casual_user": "Occasional use", "champion": "Advocate"}
    
    def __init__(self):
        config = AgentConfig(name="persona_identifier", type=AgentType.ANALYZER, model="claude-3-haiku-20240307", temperature=0.1, max_tokens=800, capabilities=[AgentCapability.CONTEXT_AWARE], tier="advanced")
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("persona_identification_started")
        state = self.update_state(state)
        
        customer_id = state.get("entities", {}).get("customer_id") or state.get("customer_context", {}).get("customer_id")
        context = await self.get_enriched_context(customer_id) if customer_id else None
        
        persona = self._identify_persona(context)
        
        response = f"""**Persona Identification**
**Persona:** {persona['persona'].replace('_', ' ').title()}
**Confidence:** {persona['confidence']*100:.0f}%
**Communication Style:** {persona['communication_guidelines']}"""
        
        return self.update_state(state, agent_response=response, persona=persona, status="resolved", response_confidence=persona['confidence'], next_agent=None)
    
    def _identify_persona(self, context) -> Dict[str, Any]:
        if context and hasattr(context, 'customer'):
            customer = context.customer
            title = customer.get("title", "").lower()
            api_calls = customer.get("api_calls_30d", 0)
            team_size = customer.get("team_size", 1)
            
            if any(w in title for w in ["ceo", "cto", "vp", "director"]):
                return {"persona": "executive", "confidence": 0.9, "communication_guidelines": "High-level, ROI-focused"}
            elif api_calls > 1000:
                return {"persona": "power_user", "confidence": 0.85, "communication_guidelines": "Technical depth, code examples"}
            elif team_size > 5:
                return {"persona": "manager", "confidence": 0.8, "communication_guidelines": "Team-focused, collaboration"}
            else:
                return {"persona": "casual_user", "confidence": 0.6, "communication_guidelines": "Simple, step-by-step"}
        
        return {"persona": "casual_user", "confidence": 0.5, "communication_guidelines": "General, helpful"}
