"""Onboarding Sub-Swarm - 6 Agents"""

from src.agents.revenue.customer_success.onboarding.onboarding_coordinator import OnboardingCoordinatorAgent
from src.agents.revenue.customer_success.onboarding.kickoff_facilitator import KickoffFacilitatorAgent
from src.agents.revenue.customer_success.onboarding.training_scheduler import TrainingSchedulerAgent
from src.agents.revenue.customer_success.onboarding.data_migration import DataMigrationAgent
from src.agents.revenue.customer_success.onboarding.progress_tracker import ProgressTrackerAgent
from src.agents.revenue.customer_success.onboarding.success_validator import SuccessValidatorAgent

__all__ = [
    "OnboardingCoordinatorAgent",
    "KickoffFacilitatorAgent",
    "TrainingSchedulerAgent",
    "DataMigrationAgent",
    "ProgressTrackerAgent",
    "SuccessValidatorAgent",
]
