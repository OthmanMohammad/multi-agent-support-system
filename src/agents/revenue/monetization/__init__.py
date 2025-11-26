"""
Monetization Agents Module - STORY #103: Monetization Swarm (20 Agents)

Complete monetization agent swarm for revenue optimization, including:
- Usage-Based Billing (5 agents)
- Add-On Monetization (5 agents)
- Account Expansion (5 agents)
- Pricing Optimization (5 agents)

Total: 20 specialized monetization agents for maximizing revenue per customer.
"""

# Usage-Based Billing (5 agents)
# Add-On Monetization (5 agents)
from src.agents.revenue.monetization.add_ons import (
    AddOnRecommender,
    AdoptionTracker,
    PremiumSupportSeller,
    ProfServicesSeller,
    TrainingSeller,
)

# Account Expansion (5 agents)
from src.agents.revenue.monetization.expansion import (
    LandAndExpand,
    MultiYearDeal,
    PlanUpgrade,
    SeatExpansion,
    WhiteSpaceAnalyzer,
)

# Pricing Optimization (5 agents)
from src.agents.revenue.monetization.pricing import (
    DiscountManager,
    PricingAnalyzer,
    PricingExperiment,
    RevenueForecaster,
    ValueMetricOptimizer,
)
from src.agents.revenue.monetization.usage_billing import (
    BillingCalculator,
    DisputeResolver,
    OverageAlert,
    UsageOptimizer,
    UsageTracker,
)

__all__ = [
    # Add-On Monetization (5)
    "AddOnRecommender",
    "AdoptionTracker",
    "BillingCalculator",
    "DiscountManager",
    "DisputeResolver",
    "LandAndExpand",
    "MultiYearDeal",
    "OverageAlert",
    "PlanUpgrade",
    "PremiumSupportSeller",
    # Pricing Optimization (5)
    "PricingAnalyzer",
    "PricingExperiment",
    "ProfServicesSeller",
    "RevenueForecaster",
    # Account Expansion (5)
    "SeatExpansion",
    "TrainingSeller",
    "UsageOptimizer",
    # Usage-Based Billing (5)
    "UsageTracker",
    "ValueMetricOptimizer",
    "WhiteSpaceAnalyzer",
]
