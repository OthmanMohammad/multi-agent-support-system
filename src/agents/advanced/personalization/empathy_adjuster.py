"""Empathy Adjuster Agent - TASK-4029"""
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("empathy_adjuster", tier="advanced", category="personalization")
class EmpathyAdjusterAgent(BaseAgent):
    """Adjust empathy based on sentiment."""
    
    def __init__(self):
        config = AgentConfig(name="empathy_adjuster", type=AgentType.COORDINATOR, temperature=0.3, max_tokens=800, capabilities=[], tier="advanced")
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("empathy_adjustment_started")
        state = self.update_state(state)
        
        sentiment = state.get("sentiment", 0)
        original = state.get("entities", {}).get("response", "Your issue is resolved.")
        
        if sentiment < -0.5:
            adjusted = f"I'm truly sorry you're experiencing this. {original}"
        elif sentiment < 0:
            adjusted = f"I understand this is frustrating. {original}"
        else:
            adjusted = original
        
        return self.update_state(state, agent_response=adjusted, status="resolved", response_confidence=0.90, next_agent=None)
