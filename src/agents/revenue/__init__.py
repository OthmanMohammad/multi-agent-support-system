"""
Tier 2 Revenue Agents.

This tier contains revenue-focused agents:
- Customer Success: 35 agents across 6 sub-swarms (Health, Onboarding, Adoption, Retention, Expansion, Relationship)
- Sales: Lead qualification, demos, pricing (to be implemented)
- Monetization: Upsell, cross-sell, retention (to be implemented)
"""

from src.agents.revenue.customer_success import (
    AdvocacyBuilderAgent,
    AutomationCoachAgent,
    BestPracticesAgent,
    ChampionCultivatorAgent,
    ChurnPredictorAgent,
    CommunityManagerAgent,
    CrossSellAgent,
    CustomerInsightsAgent,
    DataMigrationAgent,
    DepartmentExpansionAgent,
    ExecutiveSponsorAgent,
    ExpansionROIAgent,
    # Adoption Driving (6 agents)
    FeatureAdoptionAgent,
    FeedbackLoopAgent,
    # Health Monitoring (5 agents)
    HealthScoreAgent,
    IntegrationAdvocateAgent,
    KickoffFacilitatorAgent,
    LoyaltyProgramAgent,
    NPSTrackerAgent,
    # Onboarding (6 agents)
    OnboardingCoordinatorAgent,
    PowerUserEnablementAgent,
    ProgressTrackerAgent,
    # Relationship Management (8 agents)
    QBRSchedulerAgent,
    RelationshipHealthAgent,
    # Retention (5 agents)
    RenewalManagerAgent,
    RiskAlertAgent,
    SaveTeamCoordinatorAgent,
    SuccessPlanAgent,
    SuccessValidatorAgent,
    TrainingSchedulerAgent,
    # Expansion (5 agents)
    UpsellIdentifierAgent,
    UsageBasedExpansionAgent,
    UsageMonitorAgent,
    UserActivationAgent,
    WinBackAgent,
)

__all__ = [
    "AdvocacyBuilderAgent",
    "AutomationCoachAgent",
    "BestPracticesAgent",
    "ChampionCultivatorAgent",
    "ChurnPredictorAgent",
    "CommunityManagerAgent",
    "CrossSellAgent",
    "CustomerInsightsAgent",
    "DataMigrationAgent",
    "DepartmentExpansionAgent",
    "ExecutiveSponsorAgent",
    "ExpansionROIAgent",
    # Adoption Driving
    "FeatureAdoptionAgent",
    "FeedbackLoopAgent",
    # Health Monitoring
    "HealthScoreAgent",
    "IntegrationAdvocateAgent",
    "KickoffFacilitatorAgent",
    "LoyaltyProgramAgent",
    "NPSTrackerAgent",
    # Onboarding
    "OnboardingCoordinatorAgent",
    "PowerUserEnablementAgent",
    "ProgressTrackerAgent",
    # Relationship Management
    "QBRSchedulerAgent",
    "RelationshipHealthAgent",
    # Retention
    "RenewalManagerAgent",
    "RiskAlertAgent",
    "SaveTeamCoordinatorAgent",
    "SuccessPlanAgent",
    "SuccessValidatorAgent",
    "TrainingSchedulerAgent",
    # Expansion
    "UpsellIdentifierAgent",
    "UsageBasedExpansionAgent",
    "UsageMonitorAgent",
    "UserActivationAgent",
    "WinBackAgent",
]
