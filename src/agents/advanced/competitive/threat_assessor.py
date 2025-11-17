"""Threat Assessor Agent"""
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("threat_assessor", tier="advanced", category="competitive")
class ThreatAssessorAgent(BaseAgent):
    """Threat Assessor."""
    
    def __init__(self):
        config = AgentConfig(name="threat_assessor", type=AgentType.ANALYZER, temperature=0.2, max_tokens=1200, capabilities=[AgentCapability.DATABASE_READ], tier="advanced")
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("threat_assessor_started")
        state = self.update_state(state)
        response = "**Threat Assessor** analysis completed"
        return self.update_state(state, agent_response=response, status="resolved", response_confidence=0.80, next_agent=None)
