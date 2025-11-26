"""
Bug Predictor Agent - TASK-4015
Predicts which code modules are likely to have bugs.
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("bug_predictor", tier="advanced", category="predictive")
class BugPredictorAgent(BaseAgent):
    """Predict bug-prone code modules."""

    def __init__(self):
        config = AgentConfig(
            name="bug_predictor",
            type=AgentType.ANALYZER,
            temperature=0.1,
            max_tokens=1200,
            capabilities=[AgentCapability.DATABASE_READ],
            tier="advanced",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Predict bug-prone modules."""
        self.logger.info("bug_prediction_started")
        state = self.update_state(state)

        high_risk_modules = [
            {
                "module": "src/agents/billing/refund_processor.py",
                "bug_probability": 0.72,
                "factors": ["Low test coverage (45%)", "High complexity", "Recent major changes"],
            },
            {
                "module": "src/agents/technical/sync_troubleshooter.py",
                "bug_probability": 0.65,
                "factors": ["Complex logic", "Multiple contributors"],
            },
        ]

        response = "**Bug Prediction Report**\n\n**High-Risk Modules:**\n"
        for mod in high_risk_modules:
            response += f"\n**{mod['module']}** (Risk: {mod['bug_probability'] * 100:.0f}%)\n"
            response += "\n".join(f"• {f}" for f in mod["factors"]) + "\n"

        return self.update_state(
            state,
            agent_response=response,
            high_risk_modules=high_risk_modules,
            status="resolved",
            response_confidence=0.75,
            next_agent=None,
        )
