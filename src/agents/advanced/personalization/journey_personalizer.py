"""Journey Personalizer Agent - TASK-4025"""
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("journey_personalizer", tier="advanced", category="personalization")
class JourneyPersonalizerAgent(BaseAgent):
    """Customize onboarding journey."""
    
    def __init__(self):
        config = AgentConfig(name="journey_personalizer", type=AgentType.COORDINATOR, model="claude-3-haiku-20240307", temperature=0.2, max_tokens=1000, capabilities=[AgentCapability.DATABASE_READ], tier="advanced")
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("journey_personalization_started")
        state = self.update_state(state)
        
        journey = ["Generate API key", "Make first API call", "Set up webhook", "Connect integration", "Automate workflow"]
        
        response = "**Personalized Onboarding Journey:**\n" + "\n".join(f"{i+1}. {step}" for i, step in enumerate(journey))
        
        return self.update_state(state, agent_response=response, journey=journey, status="resolved", response_confidence=0.83, next_agent=None)
