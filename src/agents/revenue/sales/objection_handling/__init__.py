"""
Objection Handling Agents - Specialized agents for handling sales objections.

This module contains 6 specialized agents for objection handling:
1. Price Objection Handler - Handles pricing concerns with ROI, discounts, payment terms (TASK-1031)
2. Feature Gap Handler - Handles missing feature objections with roadmap, workarounds (TASK-1032)
3. Competitor Comparison Handler - Handles competitive objections with differentiation (TASK-1033)
4. Security Objection Handler - Handles security/compliance concerns with certifications (TASK-1034)
5. Integration Objection Handler - Handles integration concerns with API docs, examples (TASK-1035)
6. Timing Objection Handler - Handles timing objections with pilots, phased rollouts (TASK-1036)
"""

from src.agents.revenue.sales.objection_handling.competitor_comparison_handler import (
    CompetitorComparisonHandler,
)
from src.agents.revenue.sales.objection_handling.feature_gap_handler import FeatureGapHandler
from src.agents.revenue.sales.objection_handling.integration_objection_handler import (
    IntegrationObjectionHandler,
)
from src.agents.revenue.sales.objection_handling.price_objection_handler import (
    PriceObjectionHandler,
)
from src.agents.revenue.sales.objection_handling.security_objection_handler import (
    SecurityObjectionHandler,
)
from src.agents.revenue.sales.objection_handling.timing_objection_handler import (
    TimingObjectionHandler,
)

__all__ = [
    "CompetitorComparisonHandler",
    "FeatureGapHandler",
    "IntegrationObjectionHandler",
    "PriceObjectionHandler",
    "SecurityObjectionHandler",
    "TimingObjectionHandler",
]
