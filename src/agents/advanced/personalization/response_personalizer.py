"""Response Personalizer Agent - TASK-4023"""
from typing import Dict, Any
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("response_personalizer", tier="advanced", category="personalization")
class ResponsePersonalizerAgent(BaseAgent):
    """Personalize responses based on persona and preferences."""
    
    def __init__(self):
        config = AgentConfig(name="response_personalizer", type=AgentType.COORDINATOR, model="claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500, capabilities=[AgentCapability.CONTEXT_AWARE], tier="advanced")
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("response_personalization_started")
        state = self.update_state(state)
        
        generic_response = state.get("entities", {}).get("generic_response", "Your issue has been resolved.")
        customer_id = state.get("customer_context", {}).get("customer_id")
        
        personalized = await self._personalize(generic_response, customer_id)
        
        return self.update_state(state, agent_response=personalized, status="resolved", response_confidence=0.88, next_agent=None)
    
    async def _personalize(self, response: str, customer_id: str) -> str:
        if not customer_id:
            return response
        
        system_prompt = "Personalize this response for a technical power user. Add detail and code examples where relevant."
        user_message = f"Original: {response}\n\nPersonalize this response."
        
        try:
            return await self.call_llm(system_prompt, user_message)
        except:
            return response
