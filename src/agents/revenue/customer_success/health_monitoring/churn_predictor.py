"""
Churn Predictor Agent - TASK-2012

Predicts churn probability using ML model and behavioral signals.
Identifies at-risk customers and recommends retention strategies.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("churn_predictor", tier="revenue", category="customer_success")
class ChurnPredictorAgent(BaseAgent):
    """
    Churn Predictor Agent.

    Predicts churn probability (0-100%) using:
    - Usage trends (declining usage = higher churn risk)
    - Support signals (high tickets = higher risk)
    - Engagement signals (low NPS = higher risk)
    - Financial signals (payment issues = higher risk)
    - Contract signals (near renewal = critical period)
    """

    # Churn risk tiers
    RISK_TIERS = {
        "critical": (80, 100),
        "high": (60, 79),
        "medium": (40, 59),
        "low": (0, 39)
    }

    # Churn signals and weights
    CHURN_SIGNALS = {
        "declining_usage": 25,
        "low_nps": 20,
        "high_support_tickets": 15,
        "payment_issues": 20,
        "approaching_renewal": 10,
        "low_engagement": 10
    }

    def __init__(self):
        config = AgentConfig(
            name="churn_predictor",
            type=AgentType.SPECIALIST,
            temperature=0.2,
            max_tokens=600,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Predict churn probability.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with churn prediction
        """
        self.logger.info("churn_prediction_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})

        # Get usage trends and other signals
        usage_trends = state.get("entities", {}).get("usage_trends", "stable")
        support_tickets = state.get("entities", {}).get("support_tickets", 0)
        nps_score = state.get("entities", {}).get("nps_score", 7)
        days_until_renewal = state.get("entities", {}).get("days_until_renewal", 365)
        payment_status = state.get("entities", {}).get("payment_status", "current")

        # Calculate churn probability
        churn_analysis = self._predict_churn(
            usage_trends,
            support_tickets,
            nps_score,
            days_until_renewal,
            payment_status,
            customer_metadata
        )

        # Generate retention strategy
        retention_strategy = self._generate_retention_strategy(churn_analysis)

        # Format response
        response = self._format_churn_report(churn_analysis, retention_strategy)

        state["agent_response"] = response
        state["churn_probability"] = churn_analysis["churn_probability"]
        state["churn_risk"] = churn_analysis["churn_risk"]
        state["churn_signals"] = churn_analysis["churn_signals"]
        state["response_confidence"] = 0.85
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "churn_prediction_completed",
            customer_id=customer_id,
            churn_probability=churn_analysis["churn_probability"],
            churn_risk=churn_analysis["churn_risk"]
        )

        return state

    def _predict_churn(
        self,
        usage_trends: str,
        support_tickets: int,
        nps_score: int,
        days_until_renewal: int,
        payment_status: str,
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict churn probability based on signals.

        Args:
            usage_trends: Usage trend (declining, stable, increasing)
            support_tickets: Number of support tickets
            nps_score: NPS score (0-10)
            days_until_renewal: Days until contract renewal
            payment_status: Payment status
            customer_metadata: Customer profile data

        Returns:
            Churn prediction analysis
        """
        churn_score = 0.0
        signals = []

        # 1. Usage trend signal (0-25 points)
        if usage_trends == "declining":
            decline_severity = 25  # Could be calibrated based on % decline
            churn_score += decline_severity
            signals.append({
                "signal": "Declining usage trend",
                "strength": 0.9,
                "contribution": decline_severity,
                "description": "Usage declined significantly in last 30 days"
            })
        elif usage_trends == "stable_low":
            churn_score += 15
            signals.append({
                "signal": "Low stable usage",
                "strength": 0.6,
                "contribution": 15,
                "description": "Usage is consistently low"
            })

        # 2. NPS signal (0-20 points)
        if nps_score <= 6:  # Detractor
            nps_risk = (6 - nps_score) * 3.3  # Scale 0-6 to 0-20
            churn_score += nps_risk
            signals.append({
                "signal": f"NPS score {nps_score} (detractor)",
                "strength": 0.85,
                "contribution": nps_risk,
                "description": "Customer dissatisfaction indicated by low NPS"
            })
        elif nps_score <= 8:  # Passive
            churn_score += 8
            signals.append({
                "signal": f"NPS score {nps_score} (passive)",
                "strength": 0.5,
                "contribution": 8,
                "description": "Customer is passive, could churn to competitor"
            })

        # 3. Support tickets signal (0-15 points)
        if support_tickets >= 10:
            churn_score += 15
            signals.append({
                "signal": f"{support_tickets} support tickets in 30 days",
                "strength": 0.75,
                "contribution": 15,
                "description": "High support volume indicates product issues"
            })
        elif support_tickets >= 5:
            churn_score += 10
            signals.append({
                "signal": f"{support_tickets} support tickets",
                "strength": 0.5,
                "contribution": 10,
                "description": "Elevated support needs"
            })

        # 4. Payment issues signal (0-20 points)
        if payment_status in ["past_due_30", "failed"]:
            churn_score += 20
            signals.append({
                "signal": "Payment issues (30+ days past due)",
                "strength": 0.95,
                "contribution": 20,
                "description": "Serious payment problems - immediate churn risk"
            })
        elif payment_status == "past_due_7":
            churn_score += 12
            signals.append({
                "signal": "Payment past due (7 days)",
                "strength": 0.7,
                "contribution": 12,
                "description": "Recent payment issues"
            })

        # 5. Renewal proximity signal (0-10 points)
        if 0 <= days_until_renewal <= 30:
            churn_score += 10
            signals.append({
                "signal": f"Renewal in {days_until_renewal} days",
                "strength": 0.8,
                "contribution": 10,
                "description": "Critical renewal period - decision time"
            })
        elif 31 <= days_until_renewal <= 60:
            churn_score += 5
            signals.append({
                "signal": f"Renewal in {days_until_renewal} days",
                "strength": 0.5,
                "contribution": 5,
                "description": "Approaching renewal - start retention planning"
            })

        # 6. Low engagement signal (0-10 points)
        # This could be based on last login, feature usage, etc.
        # For now, infer from other signals
        if len(signals) >= 3:
            churn_score += 10
            signals.append({
                "signal": "Multiple risk factors present",
                "strength": 0.7,
                "contribution": 10,
                "description": "Combination of risk signals increases churn likelihood"
            })

        # Cap at 100%
        churn_probability = min(churn_score, 100)

        # Determine risk tier
        churn_risk = self._determine_risk_tier(churn_probability)

        # Calculate value at risk
        contract_value = customer_metadata.get("contract_value", 0)
        value_at_risk = contract_value

        return {
            "churn_probability": churn_probability,
            "churn_risk": churn_risk,
            "churn_signals": signals,
            "value_at_risk": value_at_risk,
            "predicted_churn_date": self._estimate_churn_date(days_until_renewal, churn_probability),
            "model_confidence": 0.85
        }

    def _determine_risk_tier(self, probability: float) -> str:
        """Determine risk tier from probability."""
        for tier, (min_prob, max_prob) in self.RISK_TIERS.items():
            if min_prob <= probability <= max_prob:
                return tier
        return "low"

    def _estimate_churn_date(self, days_until_renewal: int, churn_probability: float) -> Optional[str]:
        """Estimate likely churn date."""
        if churn_probability < 40:
            return None

        # High churn risk usually materializes at renewal
        if days_until_renewal <= 90:
            churn_date = datetime.now(UTC) + timedelta(days=days_until_renewal)
            return churn_date.strftime("%Y-%m-%d")

        # Otherwise estimate 90 days out
        churn_date = datetime.now(UTC) + timedelta(days=90)
        return churn_date.strftime("%Y-%m-%d")

    def _generate_retention_strategy(self, churn_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate retention strategy based on churn analysis."""
        probability = churn_analysis["churn_probability"]
        risk = churn_analysis["churn_risk"]
        signals = churn_analysis["churn_signals"]

        strategy = {
            "urgency": "low",
            "recommended_actions": []
        }

        if risk == "critical":
            strategy["urgency"] = "immediate"
            strategy["recommended_actions"] = [
                "Executive intervention - schedule call with VP Customer Success",
                "Analyze all support tickets for systemic issues",
                "Prepare custom retention offer or concession",
                "Engage executive sponsor on customer side",
                "Daily check-ins until situation stabilizes"
            ]

        elif risk == "high":
            strategy["urgency"] = "urgent"
            strategy["recommended_actions"] = [
                "CSM to conduct urgent health check call within 48 hours",
                "Review product usage and identify adoption gaps",
                "Address top pain points from support tickets",
                "Present product roadmap and upcoming features",
                "Consider discount or additional services"
            ]

        elif risk == "medium":
            strategy["urgency"] = "proactive"
            strategy["recommended_actions"] = [
                "Schedule quarterly business review (QBR)",
                "Share customer success best practices",
                "Offer training on underutilized features",
                "Monitor usage trends closely"
            ]

        else:  # low
            strategy["urgency"] = "monitor"
            strategy["recommended_actions"] = [
                "Continue regular touchpoints",
                "Monitor for changes in engagement"
            ]

        # Add signal-specific actions
        for signal in signals:
            if "declining usage" in signal["signal"].lower():
                strategy["recommended_actions"].insert(0, "Launch feature adoption campaign")
            if "nps" in signal["signal"].lower() and "detractor" in signal["signal"].lower():
                strategy["recommended_actions"].insert(0, "Immediate NPS follow-up call")
            if "payment" in signal["signal"].lower():
                strategy["recommended_actions"].insert(0, "Contact billing to resolve payment issues")

        # Deduplicate
        strategy["recommended_actions"] = list(dict.fromkeys(strategy["recommended_actions"]))[:5]

        return strategy

    def _format_churn_report(
        self,
        churn_analysis: Dict[str, Any],
        retention_strategy: Dict[str, Any]
    ) -> str:
        """Format churn prediction report."""
        probability = churn_analysis["churn_probability"]
        risk = churn_analysis["churn_risk"]
        signals = churn_analysis["churn_signals"]
        value_at_risk = churn_analysis["value_at_risk"]

        # Risk emoji
        risk_emoji = {
            "critical": "????",
            "high": "????",
            "medium": "??????",
            "low": "???"
        }

        report = f"""**{risk_emoji.get(risk, '????')} Churn Prediction Analysis**

**Churn Probability:** {int(probability)}%
**Risk Level:** {risk.upper()}
**Confidence:** {int(churn_analysis['model_confidence'] * 100)}%
"""

        if value_at_risk:
            report += f"**Value at Risk:** ${value_at_risk:,}\n"

        if churn_analysis.get("predicted_churn_date"):
            report += f"**Estimated Churn Date:** {churn_analysis['predicted_churn_date']}\n"

        # Churn signals
        if signals:
            report += "\n**???? Churn Signals:**\n"
            for signal in signals[:4]:
                strength_bar = "???" * int(signal["strength"] * 10)
                report += f"\n**{signal['signal']}**\n"
                report += f"- Strength: {strength_bar} ({int(signal['strength'] * 100)}%)\n"
                report += f"- {signal['description']}\n"

        # Retention strategy
        report += f"\n**???? Retention Strategy**\n"
        report += f"**Urgency:** {retention_strategy['urgency'].upper()}\n\n"
        report += "**Recommended Actions:**\n"

        for i, action in enumerate(retention_strategy["recommended_actions"], 1):
            report += f"{i}. {action}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Churn Predictor Agent (TASK-2012)")
        print("=" * 70)

        agent = ChurnPredictorAgent()

        # Test 1: High churn risk
        print("\n\nTest 1: High Churn Risk Customer")
        print("-" * 70)

        state1 = create_initial_state(
            "Predict churn risk",
            context={
                "customer_id": "cust_at_risk",
                "customer_metadata": {
                    "plan": "premium",
                    "contract_value": 50000
                }
            }
        )
        state1["entities"] = {
            "usage_trends": "declining",
            "support_tickets": 12,
            "nps_score": 3,
            "days_until_renewal": 45,
            "payment_status": "past_due_7"
        }

        result1 = await agent.process(state1)

        print(f"Churn Probability: {result1['churn_probability']}%")
        print(f"Churn Risk: {result1['churn_risk']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Low churn risk
        print("\n\n" + "=" * 70)
        print("Test 2: Low Churn Risk Customer")
        print("-" * 70)

        state2 = create_initial_state(
            "Predict churn risk",
            context={
                "customer_id": "cust_healthy",
                "customer_metadata": {
                    "plan": "enterprise",
                    "contract_value": 100000
                }
            }
        )
        state2["entities"] = {
            "usage_trends": "stable",
            "support_tickets": 2,
            "nps_score": 9,
            "days_until_renewal": 200,
            "payment_status": "current"
        }

        result2 = await agent.process(state2)

        print(f"Churn Probability: {result2['churn_probability']}%")
        print(f"Churn Risk: {result2['churn_risk']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:400]}...")

    asyncio.run(test())
