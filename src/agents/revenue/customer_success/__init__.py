"""
Customer Success Swarm - 35 Agents

This module contains all Customer Success agents organized into 6 sub-swarms:
- Health Monitoring (5 agents): Track customer health, predict churn, monitor usage
- Onboarding (6 agents): Ensure successful onboarding and rapid time-to-value
- Adoption Driving (6 agents): Drive feature adoption and user activation
- Retention (5 agents): Prevent churn and retain customers at renewal
- Expansion (5 agents): Identify and close expansion opportunities
- Relationship Management (8 agents): Build strong relationships and drive engagement
"""

# Health Monitoring Agents (TASK-2011 to TASK-2015)
from src.agents.revenue.customer_success.health_monitoring.health_score import HealthScoreAgent
from src.agents.revenue.customer_success.health_monitoring.churn_predictor import ChurnPredictorAgent
from src.agents.revenue.customer_success.health_monitoring.usage_monitor import UsageMonitorAgent
from src.agents.revenue.customer_success.health_monitoring.nps_tracker import NPSTrackerAgent
from src.agents.revenue.customer_success.health_monitoring.risk_alert import RiskAlertAgent

# Onboarding Agents (TASK-2021 to TASK-2026)
from src.agents.revenue.customer_success.onboarding.onboarding_coordinator import OnboardingCoordinatorAgent
from src.agents.revenue.customer_success.onboarding.kickoff_facilitator import KickoffFacilitatorAgent
from src.agents.revenue.customer_success.onboarding.training_scheduler import TrainingSchedulerAgent
from src.agents.revenue.customer_success.onboarding.data_migration import DataMigrationAgent
from src.agents.revenue.customer_success.onboarding.progress_tracker import ProgressTrackerAgent
from src.agents.revenue.customer_success.onboarding.success_validator import SuccessValidatorAgent

# Adoption Driving Agents (TASK-2031 to TASK-2036)
from src.agents.revenue.customer_success.adoption.feature_adoption import FeatureAdoptionAgent
from src.agents.revenue.customer_success.adoption.user_activation import UserActivationAgent
from src.agents.revenue.customer_success.adoption.best_practices import BestPracticesAgent
from src.agents.revenue.customer_success.adoption.automation_coach import AutomationCoachAgent
from src.agents.revenue.customer_success.adoption.integration_advocate import IntegrationAdvocateAgent
from src.agents.revenue.customer_success.adoption.power_user_enablement import PowerUserEnablementAgent

# Retention Agents (TASK-2041 to TASK-2045)
from src.agents.revenue.customer_success.retention.renewal_manager import RenewalManagerAgent
from src.agents.revenue.customer_success.retention.win_back import WinBackAgent
from src.agents.revenue.customer_success.retention.save_team_coordinator import SaveTeamCoordinatorAgent
from src.agents.revenue.customer_success.retention.feedback_loop import FeedbackLoopAgent
from src.agents.revenue.customer_success.retention.loyalty_program import LoyaltyProgramAgent

# Expansion Agents (TASK-2051 to TASK-2055)
from src.agents.revenue.customer_success.expansion.upsell_identifier import UpsellIdentifierAgent
from src.agents.revenue.customer_success.expansion.usage_based_expansion import UsageBasedExpansionAgent
from src.agents.revenue.customer_success.expansion.cross_sell import CrossSellAgent
from src.agents.revenue.customer_success.expansion.department_expansion import DepartmentExpansionAgent
from src.agents.revenue.customer_success.expansion.expansion_roi import ExpansionROIAgent

# Relationship Management Agents (TASK-2061 to TASK-2068)
from src.agents.revenue.customer_success.relationship.qbr_scheduler import QBRSchedulerAgent
from src.agents.revenue.customer_success.relationship.executive_sponsor import ExecutiveSponsorAgent
from src.agents.revenue.customer_success.relationship.champion_cultivator import ChampionCultivatorAgent
from src.agents.revenue.customer_success.relationship.relationship_health import RelationshipHealthAgent
from src.agents.revenue.customer_success.relationship.success_plan import SuccessPlanAgent
from src.agents.revenue.customer_success.relationship.advocacy_builder import AdvocacyBuilderAgent
from src.agents.revenue.customer_success.relationship.community_manager import CommunityManagerAgent
from src.agents.revenue.customer_success.relationship.customer_insights import CustomerInsightsAgent

__all__ = [
    # Health Monitoring (5 agents)
    "HealthScoreAgent",
    "ChurnPredictorAgent",
    "UsageMonitorAgent",
    "NPSTrackerAgent",
    "RiskAlertAgent",

    # Onboarding (6 agents)
    "OnboardingCoordinatorAgent",
    "KickoffFacilitatorAgent",
    "TrainingSchedulerAgent",
    "DataMigrationAgent",
    "ProgressTrackerAgent",
    "SuccessValidatorAgent",

    # Adoption Driving (6 agents)
    "FeatureAdoptionAgent",
    "UserActivationAgent",
    "BestPracticesAgent",
    "AutomationCoachAgent",
    "IntegrationAdvocateAgent",
    "PowerUserEnablementAgent",

    # Retention (5 agents)
    "RenewalManagerAgent",
    "WinBackAgent",
    "SaveTeamCoordinatorAgent",
    "FeedbackLoopAgent",
    "LoyaltyProgramAgent",

    # Expansion (5 agents)
    "UpsellIdentifierAgent",
    "UsageBasedExpansionAgent",
    "CrossSellAgent",
    "DepartmentExpansionAgent",
    "ExpansionROIAgent",

    # Relationship Management (8 agents)
    "QBRSchedulerAgent",
    "ExecutiveSponsorAgent",
    "ChampionCultivatorAgent",
    "RelationshipHealthAgent",
    "SuccessPlanAgent",
    "AdvocacyBuilderAgent",
    "CommunityManagerAgent",
    "CustomerInsightsAgent",
]
