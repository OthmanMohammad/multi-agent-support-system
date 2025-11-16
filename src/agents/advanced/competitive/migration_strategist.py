"""Migration Strategist Agent"""
from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("migration_strategist", tier="advanced", category="competitive")
class MigrationStrategistAgent(BaseAgent):
    """Migration Strategist."""
    
    def __init__(self):
        config = AgentConfig(name="migration_strategist", type=AgentType.ANALYZER, model="claude-3-haiku-20240307", temperature=0.2, max_tokens=1200, capabilities=[AgentCapability.DATABASE_READ], tier="advanced")
        super().__init__(config)
        self.logger = get_logger(__name__)
    
    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("migration_strategist_started")
        state = self.update_state(state)
        response = "**Migration Strategist** analysis completed"
        return self.update_state(state, agent_response=response, status="resolved", response_confidence=0.80, next_agent=None)
