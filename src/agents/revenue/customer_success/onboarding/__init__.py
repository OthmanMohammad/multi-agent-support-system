"""Onboarding Sub-Swarm - 6 Agents"""

from src.agents.revenue.customer_success.onboarding.data_migration import DataMigrationAgent
from src.agents.revenue.customer_success.onboarding.kickoff_facilitator import (
    KickoffFacilitatorAgent,
)
from src.agents.revenue.customer_success.onboarding.onboarding_coordinator import (
    OnboardingCoordinatorAgent,
)
from src.agents.revenue.customer_success.onboarding.progress_tracker import ProgressTrackerAgent
from src.agents.revenue.customer_success.onboarding.success_validator import SuccessValidatorAgent
from src.agents.revenue.customer_success.onboarding.training_scheduler import TrainingSchedulerAgent

__all__ = [
    "DataMigrationAgent",
    "KickoffFacilitatorAgent",
    "OnboardingCoordinatorAgent",
    "ProgressTrackerAgent",
    "SuccessValidatorAgent",
    "TrainingSchedulerAgent",
]
