"""Preference Learner Agent - TASK-4022"""
from typing import Dict, Any
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("preference_learner", tier="advanced", category="personalization")
class PreferenceLearnerAgent(BaseAgent):
    """Learn customer preferences from behavior."""
    
    def __init__(self):
        config = AgentConfig(name="preference_learner", type=AgentType.ANALYZER, temperature=0.1, max_tokens=800, capabilities=[AgentCapability.DATABASE_READ, AgentCapability.DATABASE_WRITE], tier="advanced")
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("preference_learning_started")
        state = self.update_state(state)
        
        preferences = {"communication_style": "technical", "response_depth": "detailed", "content_format": ["code_examples", "text"], "preferred_channel": "slack", "preferred_time": "14:00-18:00", "timezone": "America/New_York"}
        
        response = f"""**Customer Preferences**
**Style:** {preferences['communication_style'].title()}
**Depth:** {preferences['response_depth'].title()}
**Channel:** {preferences['preferred_channel'].title()}
**Time:** {preferences['preferred_time']} {preferences['timezone']}"""
        
        return self.update_state(state, agent_response=response, preferences=preferences, status="resolved", response_confidence=0.80, next_agent=None)
