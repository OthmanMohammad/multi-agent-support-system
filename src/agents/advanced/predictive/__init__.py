"""
Predictive Intelligence Swarm - EPIC-004 STORY-401

10 predictive agents that forecast future events 30-90 days in advance,
enabling proactive interventions for churn prevention, upsell capture,
and operational optimization.

Agents:
- Churn Predictor: Predict customer churn risk (TASK-4011)
- Upsell Predictor: Identify upsell opportunities (TASK-4012)
- Support Volume Predictor: Forecast support ticket volume (TASK-4013)
- Renewal Predictor: Predict contract renewal probability (TASK-4014)
- Bug Predictor: Predict bug-prone code modules (TASK-4015)
- Capacity Predictor: Forecast infrastructure needs (TASK-4016)
- LTV Predictor: Predict customer lifetime value (TASK-4017)
- Conversion Predictor: Predict trial conversion likelihood (TASK-4018)
- Sentiment Predictor: Predict sentiment trajectory (TASK-4019)
- Feature Demand Predictor: Predict feature demand trends (TASK-4020)
"""

from src.agents.advanced.predictive.churn_predictor import ChurnPredictorAgent
from src.agents.advanced.predictive.upsell_predictor import UpsellPredictorAgent
from src.agents.advanced.predictive.support_volume_predictor import SupportVolumePredictorAgent
from src.agents.advanced.predictive.renewal_predictor import RenewalPredictorAgent
from src.agents.advanced.predictive.bug_predictor import BugPredictorAgent
from src.agents.advanced.predictive.capacity_predictor import CapacityPredictorAgent
from src.agents.advanced.predictive.ltv_predictor import LTVPredictorAgent
from src.agents.advanced.predictive.conversion_predictor import ConversionPredictorAgent
from src.agents.advanced.predictive.sentiment_predictor import SentimentPredictorAgent
from src.agents.advanced.predictive.feature_demand_predictor import FeatureDemandPredictorAgent

__all__ = [
    "ChurnPredictorAgent",
    "UpsellPredictorAgent",
    "SupportVolumePredictorAgent",
    "RenewalPredictorAgent",
    "BugPredictorAgent",
    "CapacityPredictorAgent",
    "LTVPredictorAgent",
    "ConversionPredictorAgent",
    "SentimentPredictorAgent",
    "FeatureDemandPredictorAgent",
]
