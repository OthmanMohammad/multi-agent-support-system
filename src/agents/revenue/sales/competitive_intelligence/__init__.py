"""
Competitive Intelligence Agents - Specialized agents for competitive analysis and positioning.

This module contains 7 specialized agents for competitive intelligence:
1. Competitor Tracker - Tracks competitor mentions, wins/losses, competitive threats (TASK-1051)
2. Review Analyzer - Analyzes competitor reviews from G2, Capterra, TrustRadius (TASK-1052)
3. Sentiment Tracker - Tracks competitor sentiment on social media and forums (TASK-1053)
4. Feature Comparator - Maintains feature comparison matrices and battle cards (TASK-1054)
5. Pricing Analyzer - Tracks competitor pricing, analyzes TCO, monitors discounts (TASK-1055)
6. Positioning Advisor - Advises on positioning, generates talking points, win strategies (TASK-1056)
7. Migration Specialist - Helps prospects migrate from competitors with guides and support (TASK-1057)
"""

from src.agents.revenue.sales.competitive_intelligence.competitor_tracker import CompetitorTracker
from src.agents.revenue.sales.competitive_intelligence.review_analyzer import ReviewAnalyzer
from src.agents.revenue.sales.competitive_intelligence.sentiment_tracker import SentimentTracker
from src.agents.revenue.sales.competitive_intelligence.feature_comparator import FeatureComparator
from src.agents.revenue.sales.competitive_intelligence.pricing_analyzer import PricingAnalyzer
from src.agents.revenue.sales.competitive_intelligence.positioning_advisor import PositioningAdvisor
from src.agents.revenue.sales.competitive_intelligence.migration_specialist import MigrationSpecialist


__all__ = [
    "CompetitorTracker",
    "ReviewAnalyzer",
    "SentimentTracker",
    "FeatureComparator",
    "PricingAnalyzer",
    "PositioningAdvisor",
    "MigrationSpecialist",
]
