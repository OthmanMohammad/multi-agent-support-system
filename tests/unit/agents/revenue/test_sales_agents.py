"""
Comprehensive tests for all 30 Sales Agents (STORY #101).

Tests cover:
- Lead Qualification (6 agents)
- Product Education (5 agents)
- Objection Handling (6 agents)
- Deal Progression (6 agents)
- Competitive Intelligence (7 agents)
"""

import pytest
from uuid import uuid4
from datetime import datetime

from src.workflow.state import create_initial_state
from src.agents.revenue.sales import (
    # Lead Qualification
    InboundQualifier,
    BANTQualifier,
    LeadScorer,
    MQLtoSQLConverter,
    DisqualificationAgent,
    ReferralDetector,

    # Product Education
    FeatureExplainer,
    UseCaseMatcher,
    DemoPreparer,
    ROICalculator,
    ValueProposition,

    # Objection Handling
    PriceObjectionHandler,
    FeatureGapHandler,
    CompetitorComparisonHandler,
    SecurityObjectionHandler,
    IntegrationObjectionHandler,
    TimingObjectionHandler,

    # Deal Progression
    DemoScheduler,
    TrialOptimizer,
    ProposalGenerator,
    ContractNegotiator,
    Closer,
    UpsellIdentifier,

    # Competitive Intelligence
    CompetitorTracker,
    ReviewAnalyzer,
    SentimentTracker,
    FeatureComparator,
    PricingAnalyzer,
    PositioningAdvisor,
    MigrationSpecialist,
)


# ============================================
# LEAD QUALIFICATION TESTS (6 agents)
# ============================================

class TestInboundQualifier:
    """Tests for Inbound Qualifier Agent"""

    @pytest.fixture
    def agent(self):
        return InboundQualifier()

    def test_initialization(self, agent):
        """Test agent initializes with correct config"""
        assert agent.config.name == "inbound_qualifier"
        assert agent.config.tier == "revenue"

    @pytest.mark.asyncio
    async def test_high_quality_lead(self, agent):
        """Test qualification of high-quality lead (enterprise CTO)"""
        state = create_initial_state(
            "I'd like to request a demo for our 500-person team",
            context={
                "customer_metadata": {
                    "company": "Acme Corp",
                    "title": "CTO",
                    "company_size": 500,
                    "lead_source": "website_form"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert result["lead_score"] >= 70  # Should be SQL
        assert result["qualification_status"] == "SQL"
        assert result["next_action"] == "assign_to_sales"

    @pytest.mark.asyncio
    async def test_low_quality_lead(self, agent):
        """Test qualification of low-quality lead"""
        state = create_initial_state(
            "Just browsing",
            context={
                "customer_metadata": {
                    "company": "Unknown",
                    "title": "Student",
                    "company_size": 1,
                    "lead_source": "content_download"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert result["lead_score"] < 70
        assert result["qualification_status"] in ["MQL", "Unqualified"]


class TestBANTQualifier:
    """Tests for BANT Qualifier Agent"""

    @pytest.fixture
    def agent(self):
        return BANTQualifier()

    def test_initialization(self, agent):
        assert agent.config.name == "bant_qualifier"

    @pytest.mark.asyncio
    async def test_strong_bant(self, agent):
        """Test strong BANT assessment"""
        state = create_initial_state(
            "We have budget approved and need to decide this quarter",
            context={
                "customer_metadata": {
                    "title": "VP Engineering",
                    "company_size": 300
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "bant_assessment" in result
        assert result["overall_bant_score"] >= 50


class TestLeadScorer:
    """Tests for Lead Scorer Agent"""

    @pytest.fixture
    def agent(self):
        return LeadScorer()

    def test_initialization(self, agent):
        assert agent.config.name == "lead_scorer"

    @pytest.mark.asyncio
    async def test_scoring(self, agent):
        """Test lead scoring calculation"""
        state = create_initial_state(
            "Interested in demo",
            context={
                "customer_metadata": {
                    "company_size": 250,
                    "industry": "technology",
                    "demo_requested": True,
                    "email_opens": 5
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "lead_score" in result
        assert "lead_tier" in result
        assert result["lead_tier"] in ["A", "B", "C", "D"]


class TestMQLtoSQLConverter:
    """Tests for MQL to SQL Converter Agent"""

    @pytest.fixture
    def agent(self):
        return MQLtoSQLConverter()

    def test_initialization(self, agent):
        assert agent.config.name == "mql_to_sql_converter"

    @pytest.mark.asyncio
    async def test_conversion_eligible(self, agent):
        """Test MQL to SQL conversion for eligible lead"""
        state = create_initial_state(
            "Ready to see a demo",
            context={
                "customer_metadata": {
                    "lead_score": 75,
                    "bant_score": 72,
                    "company_size": 200,
                    "industry": "technology"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestDisqualificationAgent:
    """Tests for Disqualification Agent"""

    @pytest.fixture
    def agent(self):
        return DisqualificationAgent()

    def test_initialization(self, agent):
        assert agent.config.name == "disqualification_agent"

    @pytest.mark.asyncio
    async def test_student_disqualification(self, agent):
        """Test student lead disqualification"""
        state = create_initial_state(
            "I'm a student looking for free plan",
            context={
                "customer_metadata": {
                    "email": "student@university.edu",
                    "title": "Student"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestReferralDetector:
    """Tests for Referral Detector Agent"""

    @pytest.fixture
    def agent(self):
        return ReferralDetector()

    def test_initialization(self, agent):
        assert agent.config.name == "referral_detector"

    @pytest.mark.asyncio
    async def test_referral_detection(self, agent):
        """Test referral detection"""
        state = create_initial_state(
            "My colleague John recommended your product",
            context={
                "customer_metadata": {
                    "lead_source": "referral"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "referral_detected" in result


# ============================================
# PRODUCT EDUCATION TESTS (5 agents)
# ============================================

class TestFeatureExplainer:
    """Tests for Feature Explainer Agent"""

    @pytest.fixture
    def agent(self):
        return FeatureExplainer()

    def test_initialization(self, agent):
        assert agent.config.name == "feature_explainer"

    @pytest.mark.asyncio
    async def test_feature_explanation(self, agent):
        """Test feature explanation"""
        state = create_initial_state(
            "What's your automation feature?",
            context={
                "customer_metadata": {
                    "industry": "marketing",
                    "role": "Marketing Manager"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "agent_response" in result


class TestUseCaseMatcher:
    """Tests for Use Case Matcher Agent"""

    @pytest.fixture
    def agent(self):
        return UseCaseMatcher()

    def test_initialization(self, agent):
        assert agent.config.name == "use_case_matcher"


class TestDemoPreparer:
    """Tests for Demo Preparer Agent"""

    @pytest.fixture
    def agent(self):
        return DemoPreparer()

    def test_initialization(self, agent):
        assert agent.config.name == "demo_preparer"


class TestROICalculator:
    """Tests for ROI Calculator Agent"""

    @pytest.fixture
    def agent(self):
        return ROICalculator()

    def test_initialization(self, agent):
        assert agent.config.name == "roi_calculator"


class TestValueProposition:
    """Tests for Value Proposition Agent"""

    @pytest.fixture
    def agent(self):
        return ValueProposition()

    def test_initialization(self, agent):
        assert agent.config.name == "value_proposition"


# ============================================
# OBJECTION HANDLING TESTS (6 agents)
# ============================================

class TestPriceObjectionHandler:
    """Tests for Price Objection Handler Agent"""

    @pytest.fixture
    def agent(self):
        return PriceObjectionHandler()

    def test_initialization(self, agent):
        assert agent.config.name == "price_objection_handler"

    @pytest.mark.asyncio
    async def test_price_objection(self, agent):
        """Test price objection handling"""
        state = create_initial_state(
            "This seems expensive for our budget",
            context={
                "customer_metadata": {
                    "company_size": 50,
                    "industry": "technology"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestFeatureGapHandler:
    """Tests for Feature Gap Handler Agent"""

    @pytest.fixture
    def agent(self):
        return FeatureGapHandler()

    def test_initialization(self, agent):
        assert agent.config.name == "feature_gap_handler"


class TestCompetitorComparisonHandler:
    """Tests for Competitor Comparison Handler Agent"""

    @pytest.fixture
    def agent(self):
        return CompetitorComparisonHandler()

    def test_initialization(self, agent):
        assert agent.config.name == "competitor_comparison_handler"


class TestSecurityObjectionHandler:
    """Tests for Security Objection Handler Agent"""

    @pytest.fixture
    def agent(self):
        return SecurityObjectionHandler()

    def test_initialization(self, agent):
        assert agent.config.name == "security_objection_handler"


class TestIntegrationObjectionHandler:
    """Tests for Integration Objection Handler Agent"""

    @pytest.fixture
    def agent(self):
        return IntegrationObjectionHandler()

    def test_initialization(self, agent):
        assert agent.config.name == "integration_objection_handler"


class TestTimingObjectionHandler:
    """Tests for Timing Objection Handler Agent"""

    @pytest.fixture
    def agent(self):
        return TimingObjectionHandler()

    def test_initialization(self, agent):
        assert agent.config.name == "timing_objection_handler"


# ============================================
# DEAL PROGRESSION TESTS (6 agents)
# ============================================

class TestDemoScheduler:
    """Tests for Demo Scheduler Agent"""

    @pytest.fixture
    def agent(self):
        return DemoScheduler()

    def test_initialization(self, agent):
        assert agent.config.name == "demo_scheduler"


class TestTrialOptimizer:
    """Tests for Trial Optimizer Agent"""

    @pytest.fixture
    def agent(self):
        return TrialOptimizer()

    def test_initialization(self, agent):
        assert agent.config.name == "trial_optimizer"


class TestProposalGenerator:
    """Tests for Proposal Generator Agent"""

    @pytest.fixture
    def agent(self):
        return ProposalGenerator()

    def test_initialization(self, agent):
        assert agent.config.name == "proposal_generator"


class TestContractNegotiator:
    """Tests for Contract Negotiator Agent"""

    @pytest.fixture
    def agent(self):
        return ContractNegotiator()

    def test_initialization(self, agent):
        assert agent.config.name == "contract_negotiator"


class TestCloser:
    """Tests for Closer Agent"""

    @pytest.fixture
    def agent(self):
        return Closer()

    def test_initialization(self, agent):
        assert agent.config.name == "closer"


class TestUpsellIdentifier:
    """Tests for Upsell Identifier Agent"""

    @pytest.fixture
    def agent(self):
        return UpsellIdentifier()

    def test_initialization(self, agent):
        assert agent.config.name == "upsell_identifier"


# ============================================
# COMPETITIVE INTELLIGENCE TESTS (7 agents)
# ============================================

class TestCompetitorTracker:
    """Tests for Competitor Tracker Agent"""

    @pytest.fixture
    def agent(self):
        return CompetitorTracker()

    def test_initialization(self, agent):
        assert agent.config.name == "competitor_tracker"


class TestReviewAnalyzer:
    """Tests for Review Analyzer Agent"""

    @pytest.fixture
    def agent(self):
        return ReviewAnalyzer()

    def test_initialization(self, agent):
        assert agent.config.name == "review_analyzer"


class TestSentimentTracker:
    """Tests for Sentiment Tracker Agent"""

    @pytest.fixture
    def agent(self):
        return SentimentTracker()

    def test_initialization(self, agent):
        assert agent.config.name == "sentiment_tracker"


class TestFeatureComparator:
    """Tests for Feature Comparator Agent"""

    @pytest.fixture
    def agent(self):
        return FeatureComparator()

    def test_initialization(self, agent):
        assert agent.config.name == "feature_comparator"


class TestPricingAnalyzer:
    """Tests for Pricing Analyzer Agent"""

    @pytest.fixture
    def agent(self):
        return PricingAnalyzer()

    def test_initialization(self, agent):
        assert agent.config.name == "pricing_analyzer"


class TestPositioningAdvisor:
    """Tests for Positioning Advisor Agent"""

    @pytest.fixture
    def agent(self):
        return PositioningAdvisor()

    def test_initialization(self, agent):
        assert agent.config.name == "positioning_advisor"


class TestMigrationSpecialist:
    """Tests for Migration Specialist Agent"""

    @pytest.fixture
    def agent(self):
        return MigrationSpecialist()

    def test_initialization(self, agent):
        assert agent.config.name == "migration_specialist"


# ============================================
# INTEGRATION TESTS
# ============================================

class TestAgentRegistry:
    """Test that all agents are properly registered"""

    def test_all_agents_registered(self):
        """Verify all 30 agents are registered in AgentRegistry"""
        from src.services.infrastructure.agent_registry import AgentRegistry

        sales_agents = AgentRegistry.get_agents_by_category("sales")

        # Should have 30 sales agents registered
        assert len(sales_agents) >= 30, f"Expected 30+ sales agents, found {len(sales_agents)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
