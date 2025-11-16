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
from src.agents.revenue.monetization.usage_billing import (
    UsageTracker,
    BillingCalculator,
    OverageAlert,
    UsageOptimizer,
    DisputeResolver,
)

# Add-On Monetization (5 agents)
from src.agents.revenue.monetization.add_ons import (
    AddOnRecommender,
    PremiumSupportSeller,
    TrainingSeller,
    ProfServicesSeller,
    AdoptionTracker,
)

# Account Expansion (5 agents)
from src.agents.revenue.monetization.expansion import (
    SeatExpansion,
    PlanUpgrade,
    MultiYearDeal,
    LandAndExpand,
    WhiteSpaceAnalyzer,
)

# Pricing Optimization (5 agents)
from src.agents.revenue.monetization.pricing import (
    PricingAnalyzer,
    DiscountManager,
    ValueMetricOptimizer,
    PricingExperiment,
    RevenueForecaster,
)

__all__ = [
    # Usage-Based Billing (5)
    "UsageTracker",
    "BillingCalculator",
    "OverageAlert",
    "UsageOptimizer",
    "DisputeResolver",

    # Add-On Monetization (5)
    "AddOnRecommender",
    "PremiumSupportSeller",
    "TrainingSeller",
    "ProfServicesSeller",
    "AdoptionTracker",

    # Account Expansion (5)
    "SeatExpansion",
    "PlanUpgrade",
    "MultiYearDeal",
    "LandAndExpand",
    "WhiteSpaceAnalyzer",

    # Pricing Optimization (5)
    "PricingAnalyzer",
    "DiscountManager",
    "ValueMetricOptimizer",
    "PricingExperiment",
    "RevenueForecaster",
]
