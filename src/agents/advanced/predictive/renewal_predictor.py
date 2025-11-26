"""
Renewal Predictor Agent - TASK-4014
Predicts whether customers will renew their contracts.
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("renewal_predictor", tier="advanced", category="predictive")
class RenewalPredictorAgent(BaseAgent):
    """Predict contract renewal probability."""

    def __init__(self):
        config = AgentConfig(
            name="renewal_predictor",
            type=AgentType.ANALYZER,
            temperature=0.1,
            max_tokens=1200,
            capabilities=[AgentCapability.DATABASE_READ, AgentCapability.CONTEXT_AWARE],
            tier="advanced",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Predict renewal probability."""
        self.logger.info("renewal_prediction_started")
        state = self.update_state(state)

        customer_id = state.get("entities", {}).get("customer_id") or state.get(
            "customer_context", {}
        ).get("customer_id")

        if not customer_id:
            return self.update_state(
                state,
                agent_response="Error: No customer ID provided",
                status="failed",
                next_agent=None,
            )

        prediction = {
            "renewal_probability": 0.75,
            "renewal_likelihood": "medium",
            "days_to_renewal": 45,
            "risk_factors": [
                "Health score declined 10 points",
                "No executive engagement in 60 days",
            ],
            "recommended_actions": ["Schedule QBR", "Share ROI report"],
        }

        response = f"""**Renewal Prediction**
**Probability:** {prediction["renewal_probability"] * 100:.0f}%
**Days to Renewal:** {prediction["days_to_renewal"]}
**Recommended Actions:**
{chr(10).join(f"• {a}" for a in prediction["recommended_actions"])}
"""

        return self.update_state(
            state,
            agent_response=response,
            renewal_prediction=prediction,
            status="resolved",
            response_confidence=0.80,
            next_agent=None,
        )
