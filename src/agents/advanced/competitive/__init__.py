"""
Competitive Intelligence Swarm - EPIC-004 STORY-403

10 competitive intelligence agents that track competitors, analyze market positioning,
and inform product strategy.

Agents: Competitor Tracker, Review Analyzer, Sentiment Tracker, Feature Comparator,
Pricing Analyzer, Positioning Advisor, Win/Loss Analyzer, Migration Strategist,
Battlecard Updater, Threat Assessor (TASK-4030 to TASK-4039)
"""

from src.agents.advanced.competitive.competitor_tracker import CompetitorTrackerAgent
from src.agents.advanced.competitive.review_analyzer import ReviewAnalyzerAgent
from src.agents.advanced.competitive.sentiment_tracker import SentimentTrackerAgent
from src.agents.advanced.competitive.feature_comparator import FeatureComparatorAgent
from src.agents.advanced.competitive.pricing_analyzer import PricingAnalyzerAgent
from src.agents.advanced.competitive.positioning_advisor import PositioningAdvisorAgent
from src.agents.advanced.competitive.win_loss_analyzer import WinLossAnalyzerAgent
from src.agents.advanced.competitive.migration_strategist import MigrationStrategistAgent
from src.agents.advanced.competitive.battlecard_updater import BattlecardUpdaterAgent
from src.agents.advanced.competitive.threat_assessor import ThreatAssessorAgent

__all__ = ["CompetitorTrackerAgent", "ReviewAnalyzerAgent", "SentimentTrackerAgent", "FeatureComparatorAgent", "PricingAnalyzerAgent", "PositioningAdvisorAgent", "WinLossAnalyzerAgent", "MigrationStrategistAgent", "BattlecardUpdaterAgent", "ThreatAssessorAgent"]
