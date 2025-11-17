"""
Prediction Explainer Agent - TASK-2020

Explains ML prediction results using SHAP values and feature importance.
Makes black-box models interpretable for business stakeholders.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("prediction_explainer", tier="operational", category="analytics")
class PredictionExplainerAgent(BaseAgent):
    """
    Prediction Explainer Agent.

    Explains ML predictions using interpretability techniques:
    - SHAP value analysis
    - Feature importance ranking
    - Prediction contribution breakdown
    - What-if scenario analysis
    - Confidence explanation
    - Business-friendly interpretation
    """

    def __init__(self):
        config = AgentConfig(
            name="prediction_explainer",
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=1500,
            capabilities=[],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Explain ML prediction.

        Args:
            state: Current agent state with prediction data

        Returns:
            Updated state with explanation
        """
        self.logger.info("prediction_explanation_started")

        state = self.update_state(state)

        # Extract prediction data
        prediction_value = state.get("entities", {}).get("prediction_value", None)
        model_type = state.get("entities", {}).get("model_type", "classification")
        feature_values = state.get("entities", {}).get("feature_values", {})
        shap_values = state.get("entities", {}).get("shap_values", None)

        self.logger.debug(
            "prediction_explanation_details",
            model_type=model_type,
            prediction_value=prediction_value,
            features_count=len(feature_values)
        )

        # Calculate or retrieve SHAP values
        if shap_values is None:
            shap_values = self._calculate_mock_shap_values(feature_values, prediction_value)

        # Analyze feature importance
        feature_importance = self._analyze_feature_importance(shap_values, feature_values)

        # Generate contribution breakdown
        contribution_breakdown = self._generate_contribution_breakdown(
            shap_values,
            feature_values,
            prediction_value
        )

        # Create what-if scenarios
        what_if_scenarios = self._generate_what_if_scenarios(
            feature_values,
            feature_importance
        )

        # Explain confidence
        confidence_explanation = self._explain_confidence(
            prediction_value,
            feature_importance,
            model_type
        )

        # Generate business interpretation
        business_interpretation = self._generate_business_interpretation(
            prediction_value,
            feature_importance,
            model_type
        )

        # Format response
        response = self._format_explanation_report(
            prediction_value,
            model_type,
            feature_importance,
            contribution_breakdown,
            what_if_scenarios,
            confidence_explanation,
            business_interpretation
        )

        state["agent_response"] = response
        state["feature_importance"] = feature_importance
        state["contribution_breakdown"] = contribution_breakdown
        state["what_if_scenarios"] = what_if_scenarios
        state["confidence_explanation"] = confidence_explanation
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "prediction_explanation_completed",
            model_type=model_type,
            top_features=len(feature_importance[:5])
        )

        return state

    def _calculate_mock_shap_values(
        self,
        feature_values: Dict[str, Any],
        prediction_value: Any
    ) -> Dict[str, float]:
        """Calculate mock SHAP values for demonstration."""
        # In production, use actual SHAP library
        import random

        shap_values = {}
        for feature in feature_values.keys():
            # Generate random SHAP value
            shap_values[feature] = random.uniform(-0.5, 0.5)

        return shap_values

    def _analyze_feature_importance(
        self,
        shap_values: Dict[str, float],
        feature_values: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze feature importance from SHAP values.

        Args:
            shap_values: SHAP values for each feature
            feature_values: Actual feature values

        Returns:
            Sorted list of feature importance
        """
        importance_list = []

        for feature, shap_value in shap_values.items():
            feature_value = feature_values.get(feature, "N/A")

            importance_list.append({
                "feature": feature,
                "shap_value": round(shap_value, 4),
                "abs_importance": round(abs(shap_value), 4),
                "feature_value": feature_value,
                "impact": "positive" if shap_value > 0 else "negative" if shap_value < 0 else "neutral",
                "impact_magnitude": "high" if abs(shap_value) > 0.3 else "medium" if abs(shap_value) > 0.1 else "low"
            })

        # Sort by absolute importance
        importance_list.sort(key=lambda x: x["abs_importance"], reverse=True)

        return importance_list

    def _generate_contribution_breakdown(
        self,
        shap_values: Dict[str, float],
        feature_values: Dict[str, Any],
        prediction_value: Any
    ) -> Dict[str, Any]:
        """Generate prediction contribution breakdown."""
        total_positive = sum(v for v in shap_values.values() if v > 0)
        total_negative = sum(v for v in shap_values.values() if v < 0)

        return {
            "prediction_value": prediction_value,
            "base_value": 0.5,  # Mock base value
            "total_positive_contribution": round(total_positive, 4),
            "total_negative_contribution": round(total_negative, 4),
            "net_contribution": round(total_positive + total_negative, 4)
        }

    def _generate_what_if_scenarios(
        self,
        feature_values: Dict[str, Any],
        feature_importance: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate what-if scenarios."""
        scenarios = []

        # Get top 3 important features
        top_features = feature_importance[:3]

        for feat in top_features:
            feature_name = feat["feature"]
            current_value = feat["feature_value"]
            impact = feat["impact"]

            # Generate scenario based on impact
            if impact == "positive":
                scenario_action = "Decrease"
                expected_effect = "Lower prediction score"
            else:
                scenario_action = "Increase"
                expected_effect = "Higher prediction score"

            scenarios.append({
                "feature": feature_name,
                "current_value": current_value,
                "scenario_action": f"{scenario_action} {feature_name}",
                "expected_effect": expected_effect,
                "impact_magnitude": feat["impact_magnitude"]
            })

        return scenarios

    def _explain_confidence(
        self,
        prediction_value: Any,
        feature_importance: List[Dict[str, Any]],
        model_type: str
    ) -> Dict[str, Any]:
        """Explain prediction confidence."""
        # Mock confidence calculation
        # In production, use actual model confidence scores

        high_impact_features = len([f for f in feature_importance if f["impact_magnitude"] == "high"])

        if high_impact_features >= 3:
            confidence = "high"
            explanation = f"{high_impact_features} strong features drive this prediction with clear signals"
        elif high_impact_features >= 1:
            confidence = "medium"
            explanation = f"Moderate confidence - {high_impact_features} strong features identified"
        else:
            confidence = "low"
            explanation = "Lower confidence - features show weak signals"

        return {
            "confidence_level": confidence,
            "explanation": explanation,
            "contributing_factors": high_impact_features
        }

    def _generate_business_interpretation(
        self,
        prediction_value: Any,
        feature_importance: List[Dict[str, Any]],
        model_type: str
    ) -> str:
        """Generate business-friendly interpretation."""
        top_features = feature_importance[:3]

        interpretation = f"This prediction is primarily driven by:\n\n"

        for i, feat in enumerate(top_features, 1):
            impact_desc = "increasing" if feat["impact"] == "positive" else "decreasing"
            interpretation += f"{i}. **{feat['feature'].replace('_', ' ').title()}** ({feat['feature_value']}) - {impact_desc} the score by {abs(feat['shap_value']):.3f}\n"

        interpretation += f"\nThe model's decision is most sensitive to changes in {top_features[0]['feature'].replace('_', ' ')}."

        return interpretation

    def _format_explanation_report(
        self,
        prediction_value: Any,
        model_type: str,
        feature_importance: List[Dict[str, Any]],
        contribution_breakdown: Dict[str, Any],
        what_if_scenarios: List[Dict[str, Any]],
        confidence_explanation: Dict[str, Any],
        business_interpretation: str
    ) -> str:
        """Format prediction explanation report."""
        report = f"""**ML Prediction Explanation**

**Prediction:** {prediction_value}
**Model Type:** {model_type.title()}
**Confidence:** {confidence_explanation['confidence_level'].upper()}

**Explanation:**
{confidence_explanation['explanation']}

**Feature Importance (Top Features):**
"""

        for feat in feature_importance[:10]:
            impact_icon = "📈" if feat["impact"] == "positive" else "📉" if feat["impact"] == "negative" else "➡️"
            report += f"{impact_icon} **{feat['feature'].replace('_', ' ').title()}**\n"
            report += f"   - Value: {feat['feature_value']}\n"
            report += f"   - SHAP Impact: {feat['shap_value']:+.4f}\n"
            report += f"   - Magnitude: {feat['impact_magnitude'].title()}\n\n"

        # Contribution breakdown
        report += "**Contribution Breakdown:**\n"
        report += f"- Base Value: {contribution_breakdown['base_value']:.4f}\n"
        report += f"- Positive Contributions: +{contribution_breakdown['total_positive_contribution']:.4f}\n"
        report += f"- Negative Contributions: {contribution_breakdown['total_negative_contribution']:.4f}\n"
        report += f"- Net Effect: {contribution_breakdown['net_contribution']:+.4f}\n"

        # What-if scenarios
        if what_if_scenarios:
            report += "\n**What-If Scenarios:**\n"
            for scenario in what_if_scenarios:
                report += f"- {scenario['scenario_action']}: {scenario['expected_effect']} ({scenario['impact_magnitude']} impact)\n"

        # Business interpretation
        report += f"\n**Business Interpretation:**\n{business_interpretation}\n"

        report += f"\n*Explanation generated at {datetime.now(UTC).isoformat()}*"

        return report
