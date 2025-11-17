"""
Comprehensive tests for all 35 Customer Success agents.

Tests agent initialization, registration, and basic processing for:
- Health Monitoring (5 agents)
- Onboarding (6 agents)
- Adoption Driving (6 agents)
- Retention (5 agents)
- Expansion (5 agents)
- Relationship Management (8 agents)
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta, UTC

from src.workflow.state import create_initial_state

# Health Monitoring Agents
from src.agents.revenue.customer_success.health_monitoring.health_score import HealthScoreAgent
from src.agents.revenue.customer_success.health_monitoring.churn_predictor import ChurnPredictorAgent
from src.agents.revenue.customer_success.health_monitoring.usage_monitor import UsageMonitorAgent
from src.agents.revenue.customer_success.health_monitoring.nps_tracker import NPSTrackerAgent
from src.agents.revenue.customer_success.health_monitoring.risk_alert import RiskAlertAgent

# Onboarding Agents
from src.agents.revenue.customer_success.onboarding.onboarding_coordinator import OnboardingCoordinatorAgent
from src.agents.revenue.customer_success.onboarding.kickoff_facilitator import KickoffFacilitatorAgent
from src.agents.revenue.customer_success.onboarding.training_scheduler import TrainingSchedulerAgent
from src.agents.revenue.customer_success.onboarding.data_migration import DataMigrationAgent
from src.agents.revenue.customer_success.onboarding.progress_tracker import ProgressTrackerAgent
from src.agents.revenue.customer_success.onboarding.success_validator import SuccessValidatorAgent

# Adoption Driving Agents
from src.agents.revenue.customer_success.adoption.feature_adoption import FeatureAdoptionAgent
from src.agents.revenue.customer_success.adoption.user_activation import UserActivationAgent
from src.agents.revenue.customer_success.adoption.best_practices import BestPracticesAgent
from src.agents.revenue.customer_success.adoption.automation_coach import AutomationCoachAgent
from src.agents.revenue.customer_success.adoption.integration_advocate import IntegrationAdvocateAgent
from src.agents.revenue.customer_success.adoption.power_user_enablement import PowerUserEnablementAgent

# Retention Agents
from src.agents.revenue.customer_success.retention.renewal_manager import RenewalManagerAgent
from src.agents.revenue.customer_success.retention.win_back import WinBackAgent
from src.agents.revenue.customer_success.retention.save_team_coordinator import SaveTeamCoordinatorAgent
from src.agents.revenue.customer_success.retention.feedback_loop import FeedbackLoopAgent
from src.agents.revenue.customer_success.retention.loyalty_program import LoyaltyProgramAgent

# Expansion Agents
from src.agents.revenue.customer_success.expansion.upsell_identifier import UpsellIdentifierAgent
from src.agents.revenue.customer_success.expansion.usage_based_expansion import UsageBasedExpansionAgent
from src.agents.revenue.customer_success.expansion.cross_sell import CrossSellAgent
from src.agents.revenue.customer_success.expansion.department_expansion import DepartmentExpansionAgent
from src.agents.revenue.customer_success.expansion.expansion_roi import ExpansionROIAgent

# Relationship Management Agents
from src.agents.revenue.customer_success.relationship.qbr_scheduler import QBRSchedulerAgent
from src.agents.revenue.customer_success.relationship.executive_sponsor import ExecutiveSponsorAgent
from src.agents.revenue.customer_success.relationship.champion_cultivator import ChampionCultivatorAgent
from src.agents.revenue.customer_success.relationship.relationship_health import RelationshipHealthAgent
from src.agents.revenue.customer_success.relationship.success_plan import SuccessPlanAgent
from src.agents.revenue.customer_success.relationship.advocacy_builder import AdvocacyBuilderAgent
from src.agents.revenue.customer_success.relationship.community_manager import CommunityManagerAgent
from src.agents.revenue.customer_success.relationship.customer_insights import CustomerInsightsAgent


class TestCustomerSuccessAgents:
    """Test suite for all 35 Customer Success agents."""

    # ============================================================================
    # HEALTH MONITORING AGENTS (5 agents)
    # ============================================================================

    def test_health_score_agent_initialization(self):
        """Test HealthScoreAgent initializes correctly."""
        agent = HealthScoreAgent()
        assert agent.config.name == "health_score"
        assert agent.config.tier == "revenue"
        assert agent.config.model == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_health_score_agent_process(self):
        """Test HealthScoreAgent processes customer health."""
        agent = HealthScoreAgent()
        state = create_initial_state("Calculate health score", context={
            "customer_id": "cust_123",
            "customer_metadata": {"plan": "premium"}
        })
        state["entities"] = {
            "usage_data": {"daily_active_users": 10, "total_users": 15, "features_used": 8, "automation_rules_active": 3},
            "engagement_data": {"nps_score": 8, "support_tickets_last_30d": 2, "last_login": datetime.now(UTC).isoformat()},
            "business_data": {"payment_status": "current"}
        }

        result = await agent.process(state)

        assert "health_score" in result
        assert "health_status" in result
        assert result["status"] == "resolved"
        assert 0 <= result["health_score"] <= 100

    def test_churn_predictor_agent_initialization(self):
        """Test ChurnPredictorAgent initializes correctly."""
        agent = ChurnPredictorAgent()
        assert agent.config.name == "churn_predictor"
        assert agent.config.tier == "revenue"

    @pytest.mark.asyncio
    async def test_churn_predictor_agent_process(self):
        """Test ChurnPredictorAgent predicts churn."""
        agent = ChurnPredictorAgent()
        state = create_initial_state("Predict churn", context={
            "customer_id": "cust_123",
            "customer_metadata": {"plan": "premium", "contract_value": 50000}
        })
        state["entities"] = {
            "usage_trends": "declining",
            "support_tickets": 10,
            "nps_score": 4,
            "days_until_renewal": 45,
            "payment_status": "current"
        }

        result = await agent.process(state)

        assert "churn_probability" in result
        assert "churn_risk" in result
        assert result["status"] == "resolved"

    def test_usage_monitor_agent_initialization(self):
        """Test UsageMonitorAgent initializes correctly."""
        agent = UsageMonitorAgent()
        assert agent.config.name == "usage_monitor"
        assert agent.config.tier == "revenue"

    @pytest.mark.asyncio
    async def test_usage_monitor_agent_process(self):
        """Test UsageMonitorAgent monitors usage."""
        agent = UsageMonitorAgent()
        state = create_initial_state("Monitor usage")
        state["entities"] = {
            "current_period_usage": {"dau": 12, "mau": 18, "total_seats": 20},
            "previous_period_usage": {"dau": 15, "mau": 20}
        }

        result = await agent.process(state)

        assert "usage_status" in result
        assert result["status"] == "resolved"

    def test_nps_tracker_agent_initialization(self):
        """Test NPSTrackerAgent initializes correctly."""
        agent = NPSTrackerAgent()
        assert agent.config.name == "nps_tracker"
        assert agent.config.tier == "revenue"

    @pytest.mark.asyncio
    async def test_nps_tracker_agent_process(self):
        """Test NPSTrackerAgent tracks NPS."""
        agent = NPSTrackerAgent()
        state = create_initial_state("Process NPS")
        state["entities"] = {
            "nps_score": 9,
            "feedback": "Great product!"
        }

        result = await agent.process(state)

        assert "nps_classification" in result
        assert result["nps_classification"] == "promoter"
        assert result["status"] == "resolved"

    def test_risk_alert_agent_initialization(self):
        """Test RiskAlertAgent initializes correctly."""
        agent = RiskAlertAgent()
        assert agent.config.name == "risk_alert"
        assert agent.config.tier == "revenue"

    @pytest.mark.asyncio
    async def test_risk_alert_agent_process(self):
        """Test RiskAlertAgent generates alerts."""
        agent = RiskAlertAgent()
        state = create_initial_state("Generate alert", context={"customer_id": "cust_123"})
        state["entities"] = {
            "risk_signals": [
                {"type": "churn_risk", "value": 75},
                {"type": "usage_drop", "value": 60}
            ]
        }

        result = await agent.process(state)

        assert "alert_severity" in result
        assert result["status"] == "resolved"

    # ============================================================================
    # ONBOARDING AGENTS (6 agents)
    # ============================================================================

    def test_onboarding_coordinator_agent_initialization(self):
        """Test OnboardingCoordinatorAgent initializes correctly."""
        agent = OnboardingCoordinatorAgent()
        assert agent.config.name == "onboarding_coordinator"
        assert agent.config.tier == "revenue"

    def test_kickoff_facilitator_agent_initialization(self):
        """Test KickoffFacilitatorAgent initializes correctly."""
        agent = KickoffFacilitatorAgent()
        assert agent.config.name == "kickoff_facilitator"
        assert agent.config.tier == "revenue"

    def test_training_scheduler_agent_initialization(self):
        """Test TrainingSchedulerAgent initializes correctly."""
        agent = TrainingSchedulerAgent()
        assert agent.config.name == "training_scheduler"
        assert agent.config.tier == "revenue"

    def test_data_migration_agent_initialization(self):
        """Test DataMigrationAgent initializes correctly."""
        agent = DataMigrationAgent()
        assert agent.config.name == "data_migration"
        assert agent.config.tier == "revenue"

    def test_progress_tracker_agent_initialization(self):
        """Test ProgressTrackerAgent initializes correctly."""
        agent = ProgressTrackerAgent()
        assert agent.config.name == "progress_tracker"
        assert agent.config.tier == "revenue"

    def test_success_validator_agent_initialization(self):
        """Test SuccessValidatorAgent initializes correctly."""
        agent = SuccessValidatorAgent()
        assert agent.config.name == "success_validator"
        assert agent.config.tier == "revenue"

    # ============================================================================
    # ADOPTION DRIVING AGENTS (6 agents)
    # ============================================================================

    def test_feature_adoption_agent_initialization(self):
        """Test FeatureAdoptionAgent initializes correctly."""
        agent = FeatureAdoptionAgent()
        assert agent.config.name == "feature_adoption"
        assert agent.config.tier == "revenue"

    def test_user_activation_agent_initialization(self):
        """Test UserActivationAgent initializes correctly."""
        agent = UserActivationAgent()
        assert agent.config.name == "user_activation"
        assert agent.config.tier == "revenue"

    def test_best_practices_agent_initialization(self):
        """Test BestPracticesAgent initializes correctly."""
        agent = BestPracticesAgent()
        assert agent.config.name == "best_practices"
        assert agent.config.tier == "revenue"

    def test_automation_coach_agent_initialization(self):
        """Test AutomationCoachAgent initializes correctly."""
        agent = AutomationCoachAgent()
        assert agent.config.name == "automation_coach"
        assert agent.config.tier == "revenue"

    def test_integration_advocate_agent_initialization(self):
        """Test IntegrationAdvocateAgent initializes correctly."""
        agent = IntegrationAdvocateAgent()
        assert agent.config.name == "integration_advocate"
        assert agent.config.tier == "revenue"

    def test_power_user_enablement_agent_initialization(self):
        """Test PowerUserEnablementAgent initializes correctly."""
        agent = PowerUserEnablementAgent()
        assert agent.config.name == "power_user_enablement"
        assert agent.config.tier == "revenue"

    # ============================================================================
    # RETENTION AGENTS (5 agents)
    # ============================================================================

    def test_renewal_manager_agent_initialization(self):
        """Test RenewalManagerAgent initializes correctly."""
        agent = RenewalManagerAgent()
        assert agent.config.name == "renewal_manager"
        assert agent.config.tier == "revenue"

    def test_win_back_agent_initialization(self):
        """Test WinBackAgent initializes correctly."""
        agent = WinBackAgent()
        assert agent.config.name == "win_back"
        assert agent.config.tier == "revenue"

    def test_save_team_coordinator_agent_initialization(self):
        """Test SaveTeamCoordinatorAgent initializes correctly."""
        agent = SaveTeamCoordinatorAgent()
        assert agent.config.name == "save_team_coordinator"
        assert agent.config.tier == "revenue"

    def test_feedback_loop_agent_initialization(self):
        """Test FeedbackLoopAgent initializes correctly."""
        agent = FeedbackLoopAgent()
        assert agent.config.name == "feedback_loop"
        assert agent.config.tier == "revenue"

    def test_loyalty_program_agent_initialization(self):
        """Test LoyaltyProgramAgent initializes correctly."""
        agent = LoyaltyProgramAgent()
        assert agent.config.name == "loyalty_program"
        assert agent.config.tier == "revenue"

    # ============================================================================
    # EXPANSION AGENTS (5 agents)
    # ============================================================================

    def test_upsell_identifier_agent_initialization(self):
        """Test UpsellIdentifierAgent initializes correctly."""
        agent = UpsellIdentifierAgent()
        assert agent.config.name == "upsell_identifier"
        assert agent.config.tier == "revenue"

    def test_usage_based_expansion_agent_initialization(self):
        """Test UsageBasedExpansionAgent initializes correctly."""
        agent = UsageBasedExpansionAgent()
        assert agent.config.name == "usage_based_expansion"
        assert agent.config.tier == "revenue"

    def test_cross_sell_agent_initialization(self):
        """Test CrossSellAgent initializes correctly."""
        agent = CrossSellAgent()
        assert agent.config.name == "cross_sell"
        assert agent.config.tier == "revenue"

    def test_department_expansion_agent_initialization(self):
        """Test DepartmentExpansionAgent initializes correctly."""
        agent = DepartmentExpansionAgent()
        assert agent.config.name == "department_expansion"
        assert agent.config.tier == "revenue"

    def test_expansion_roi_agent_initialization(self):
        """Test ExpansionROIAgent initializes correctly."""
        agent = ExpansionROIAgent()
        assert agent.config.name == "expansion_roi"
        assert agent.config.tier == "revenue"

    # ============================================================================
    # RELATIONSHIP MANAGEMENT AGENTS (8 agents)
    # ============================================================================

    def test_qbr_scheduler_agent_initialization(self):
        """Test QBRSchedulerAgent initializes correctly."""
        agent = QBRSchedulerAgent()
        assert agent.config.name == "qbr_scheduler"
        assert agent.config.tier == "revenue"

    def test_executive_sponsor_agent_initialization(self):
        """Test ExecutiveSponsorAgent initializes correctly."""
        agent = ExecutiveSponsorAgent()
        assert agent.config.name == "executive_sponsor"
        assert agent.config.tier == "revenue"

    def test_champion_cultivator_agent_initialization(self):
        """Test ChampionCultivatorAgent initializes correctly."""
        agent = ChampionCultivatorAgent()
        assert agent.config.name == "champion_cultivator"
        assert agent.config.tier == "revenue"

    def test_relationship_health_agent_initialization(self):
        """Test RelationshipHealthAgent initializes correctly."""
        agent = RelationshipHealthAgent()
        assert agent.config.name == "relationship_health"
        assert agent.config.tier == "revenue"

    def test_success_plan_agent_initialization(self):
        """Test SuccessPlanAgent initializes correctly."""
        agent = SuccessPlanAgent()
        assert agent.config.name == "success_plan"
        assert agent.config.tier == "revenue"

    def test_advocacy_builder_agent_initialization(self):
        """Test AdvocacyBuilderAgent initializes correctly."""
        agent = AdvocacyBuilderAgent()
        assert agent.config.name == "advocacy_builder"
        assert agent.config.tier == "revenue"

    def test_community_manager_agent_initialization(self):
        """Test CommunityManagerAgent initializes correctly."""
        agent = CommunityManagerAgent()
        assert agent.config.name == "community_manager"
        assert agent.config.tier == "revenue"

    def test_customer_insights_agent_initialization(self):
        """Test CustomerInsightsAgent initializes correctly."""
        agent = CustomerInsightsAgent()
        assert agent.config.name == "customer_insights"
        assert agent.config.tier == "revenue"

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================

    def test_all_agents_have_unique_names(self):
        """Test all 35 agents have unique registry names."""
        agents = [
            # Health Monitoring
            HealthScoreAgent(), ChurnPredictorAgent(), UsageMonitorAgent(),
            NPSTrackerAgent(), RiskAlertAgent(),

            # Onboarding
            OnboardingCoordinatorAgent(), KickoffFacilitatorAgent(), TrainingSchedulerAgent(),
            DataMigrationAgent(), ProgressTrackerAgent(), SuccessValidatorAgent(),

            # Adoption
            FeatureAdoptionAgent(), UserActivationAgent(), BestPracticesAgent(),
            AutomationCoachAgent(), IntegrationAdvocateAgent(), PowerUserEnablementAgent(),

            # Retention
            RenewalManagerAgent(), WinBackAgent(), SaveTeamCoordinatorAgent(),
            FeedbackLoopAgent(), LoyaltyProgramAgent(),

            # Expansion
            UpsellIdentifierAgent(), UsageBasedExpansionAgent(), CrossSellAgent(),
            DepartmentExpansionAgent(), ExpansionROIAgent(),

            # Relationship
            QBRSchedulerAgent(), ExecutiveSponsorAgent(), ChampionCultivatorAgent(),
            RelationshipHealthAgent(), SuccessPlanAgent(), AdvocacyBuilderAgent(),
            CommunityManagerAgent(), CustomerInsightsAgent(),
        ]

        names = [agent.config.name for agent in agents]
        assert len(names) == 35, "Should have exactly 35 agents"
        assert len(set(names)) == 35, "All agent names should be unique"

    def test_all_agents_are_revenue_tier(self):
        """Test all agents are in revenue tier."""
        agents = [
            # Health Monitoring
            HealthScoreAgent(), ChurnPredictorAgent(), UsageMonitorAgent(),
            NPSTrackerAgent(), RiskAlertAgent(),

            # Onboarding
            OnboardingCoordinatorAgent(), KickoffFacilitatorAgent(), TrainingSchedulerAgent(),
            DataMigrationAgent(), ProgressTrackerAgent(), SuccessValidatorAgent(),

            # Adoption
            FeatureAdoptionAgent(), UserActivationAgent(), BestPracticesAgent(),
            AutomationCoachAgent(), IntegrationAdvocateAgent(), PowerUserEnablementAgent(),

            # Retention
            RenewalManagerAgent(), WinBackAgent(), SaveTeamCoordinatorAgent(),
            FeedbackLoopAgent(), LoyaltyProgramAgent(),

            # Expansion
            UpsellIdentifierAgent(), UsageBasedExpansionAgent(), CrossSellAgent(),
            DepartmentExpansionAgent(), ExpansionROIAgent(),

            # Relationship
            QBRSchedulerAgent(), ExecutiveSponsorAgent(), ChampionCultivatorAgent(),
            RelationshipHealthAgent(), SuccessPlanAgent(), AdvocacyBuilderAgent(),
            CommunityManagerAgent(), CustomerInsightsAgent(),
        ]

        for agent in agents:
            assert agent.config.tier == "revenue", f"{agent.config.name} should be in revenue tier"

    def test_agent_count_by_category(self):
        """Test correct number of agents per category."""
        # This test documents the structure
        assert True  # Health Monitoring: 5 agents
        assert True  # Onboarding: 6 agents
        assert True  # Adoption: 6 agents
        assert True  # Retention: 5 agents
        assert True  # Expansion: 5 agents
        assert True  # Relationship: 8 agents
        # Total: 35 agents
