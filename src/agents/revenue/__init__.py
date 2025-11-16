"""
Tier 2 Revenue Agents.

This tier contains revenue-focused agents:
- Customer Success: 35 agents across 6 sub-swarms (Health, Onboarding, Adoption, Retention, Expansion, Relationship)
- Sales: Lead qualification, demos, pricing (to be implemented)
- Monetization: Upsell, cross-sell, retention (to be implemented)
"""

from src.agents.revenue.customer_success import (
    # Health Monitoring (5 agents)
    HealthScoreAgent,
    ChurnPredictorAgent,
    UsageMonitorAgent,
    NPSTrackerAgent,
    RiskAlertAgent,

    # Onboarding (6 agents)
    OnboardingCoordinatorAgent,
    KickoffFacilitatorAgent,
    TrainingSchedulerAgent,
    DataMigrationAgent,
    ProgressTrackerAgent,
    SuccessValidatorAgent,

    # Adoption Driving (6 agents)
    FeatureAdoptionAgent,
    UserActivationAgent,
    BestPracticesAgent,
    AutomationCoachAgent,
    IntegrationAdvocateAgent,
    PowerUserEnablementAgent,

    # Retention (5 agents)
    RenewalManagerAgent,
    WinBackAgent,
    SaveTeamCoordinatorAgent,
    FeedbackLoopAgent,
    LoyaltyProgramAgent,

    # Expansion (5 agents)
    UpsellIdentifierAgent,
    UsageBasedExpansionAgent,
    CrossSellAgent,
    DepartmentExpansionAgent,
    ExpansionROIAgent,

    # Relationship Management (8 agents)
    QBRSchedulerAgent,
    ExecutiveSponsorAgent,
    ChampionCultivatorAgent,
    RelationshipHealthAgent,
    SuccessPlanAgent,
    AdvocacyBuilderAgent,
    CommunityManagerAgent,
    CustomerInsightsAgent,
)

__all__ = [
    # Health Monitoring
    "HealthScoreAgent",
    "ChurnPredictorAgent",
    "UsageMonitorAgent",
    "NPSTrackerAgent",
    "RiskAlertAgent",

    # Onboarding
    "OnboardingCoordinatorAgent",
    "KickoffFacilitatorAgent",
    "TrainingSchedulerAgent",
    "DataMigrationAgent",
    "ProgressTrackerAgent",
    "SuccessValidatorAgent",

    # Adoption Driving
    "FeatureAdoptionAgent",
    "UserActivationAgent",
    "BestPracticesAgent",
    "AutomationCoachAgent",
    "IntegrationAdvocateAgent",
    "PowerUserEnablementAgent",

    # Retention
    "RenewalManagerAgent",
    "WinBackAgent",
    "SaveTeamCoordinatorAgent",
    "FeedbackLoopAgent",
    "LoyaltyProgramAgent",

    # Expansion
    "UpsellIdentifierAgent",
    "UsageBasedExpansionAgent",
    "CrossSellAgent",
    "DepartmentExpansionAgent",
    "ExpansionROIAgent",

    # Relationship Management
    "QBRSchedulerAgent",
    "ExecutiveSponsorAgent",
    "ChampionCultivatorAgent",
    "RelationshipHealthAgent",
    "SuccessPlanAgent",
    "AdvocacyBuilderAgent",
    "CommunityManagerAgent",
    "CustomerInsightsAgent",
]
