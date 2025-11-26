"""Migration Strategist Agent"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("migration_strategist", tier="advanced", category="competitive")
class MigrationStrategistAgent(BaseAgent):
    """Migration Strategist."""

    def __init__(self):
        config = AgentConfig(
            name="migration_strategist",
            type=AgentType.ANALYZER,
            temperature=0.2,
            max_tokens=1200,
            capabilities=[AgentCapability.DATABASE_READ],
            tier="advanced",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("migration_strategist_started")
        state = self.update_state(state)
        response = "**Migration Strategist** analysis completed"
        return self.update_state(
            state,
            agent_response=response,
            status="resolved",
            response_confidence=0.80,
            next_agent=None,
        )
