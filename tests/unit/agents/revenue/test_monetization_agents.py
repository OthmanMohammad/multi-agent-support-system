"""
Comprehensive tests for all 20 Monetization Agents (STORY #103).

Tests cover:
- Usage-Based Billing (5 agents)
- Add-On Monetization (5 agents)
- Account Expansion (5 agents)
- Pricing Optimization (5 agents)
"""

import pytest
from uuid import uuid4
from datetime import datetime

from src.workflow.state import create_initial_state
from src.agents.revenue.monetization import (
    # Usage-Based Billing
    UsageTracker,
    BillingCalculator,
    OverageAlert,
    UsageOptimizer,
    DisputeResolver,

    # Add-On Monetization
    AddOnRecommender,
    PremiumSupportSeller,
    TrainingSeller,
    ProfServicesSeller,
    AdoptionTracker,

    # Account Expansion
    SeatExpansion,
    PlanUpgrade,
    MultiYearDeal,
    LandAndExpand,
    WhiteSpaceAnalyzer,

    # Pricing Optimization
    PricingAnalyzer,
    DiscountManager,
    ValueMetricOptimizer,
    PricingExperiment,
    RevenueForecaster,
)


# ============================================
# USAGE-BASED BILLING TESTS (5 agents)
# ============================================

class TestUsageTracker:
    """Tests for Usage Tracker Agent"""

    @pytest.fixture
    def agent(self):
        return UsageTracker()

    def test_initialization(self, agent):
        """Test agent initializes with correct config"""
        assert agent.config.name == "usage_tracker"
        assert agent.config.tier == "revenue"
        assert agent.config.model == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_high_usage_tracking(self, agent):
        """Test tracking high usage approaching limits"""
        state = create_initial_state(
            "What is my current usage?",
            context={
                "customer_metadata": {
                    "plan_name": "Professional",
                    "usage_data": {
                        "api_calls": 450000,
                        "storage_gb": 800,
                        "seats_active": 45
                    },
                    "plan_limits": {
                        "api_calls_limit": 500000,
                        "storage_gb_limit": 1000,
                        "seats_active_limit": 50
                    }
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "usage_analysis" in result
        assert result["usage_analysis"]["overage_risk"] in ["medium", "high"]


class TestBillingCalculator:
    """Tests for Billing Calculator Agent"""

    @pytest.fixture
    def agent(self):
        return BillingCalculator()

    def test_initialization(self, agent):
        assert agent.config.name == "billing_calculator"

    @pytest.mark.asyncio
    async def test_calculate_bill_with_overages(self, agent):
        """Test bill calculation with overage charges"""
        state = create_initial_state(
            "Calculate my bill",
            context={
                "customer_metadata": {
                    "base_plan_cost": 499,
                    "usage_data": {
                        "api_calls": 600000,
                        "storage_gb": 150
                    },
                    "plan_limits": {
                        "api_calls_limit": 500000,
                        "storage_gb_limit": 100
                    },
                    "overage_pricing": {
                        "api_calls": {"rate": 0.01},
                        "storage_gb": {"rate": 10}
                    },
                    "tax_region": "US"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "invoice" in result
        assert result["invoice"]["total"] > result["base_plan_cost"]


class TestOverageAlert:
    """Tests for Overage Alert Agent"""

    @pytest.fixture
    def agent(self):
        return OverageAlert()

    def test_initialization(self, agent):
        assert agent.config.name == "overage_alert"

    @pytest.mark.asyncio
    async def test_critical_overage_alert(self, agent):
        """Test critical overage alert at 100%+ usage"""
        state = create_initial_state(
            "Am I approaching any limits?",
            context={
                "customer_metadata": {
                    "usage_data": {
                        "api_calls": 550000
                    },
                    "plan_limits": {
                        "api_calls_limit": 500000
                    }
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert len(result["alerts_needed"]) > 0
        assert result["alert_priority"] in ["high", "critical"]


class TestUsageOptimizer:
    """Tests for Usage Optimizer Agent"""

    @pytest.fixture
    def agent(self):
        return UsageOptimizer()

    def test_initialization(self, agent):
        assert agent.config.name == "usage_optimizer"

    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, agent):
        """Test usage optimization recommendations"""
        state = create_initial_state(
            "How can I reduce my usage costs?",
            context={
                "customer_metadata": {
                    "usage_data": {
                        "api_calls": 900000,
                        "storage_gb": 1200
                    },
                    "plan_limits": {
                        "api_calls_limit": 1000000,
                        "storage_gb_limit": 1000
                    }
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert len(result["optimization_recommendations"]) > 0
        assert "potential_savings" in result


class TestDisputeResolver:
    """Tests for Dispute Resolver Agent"""

    @pytest.fixture
    def agent(self):
        return DisputeResolver()

    def test_initialization(self, agent):
        assert agent.config.name == "dispute_resolver"

    @pytest.mark.asyncio
    async def test_valid_dispute_resolution(self, agent):
        """Test resolving valid billing dispute"""
        state = create_initial_state(
            "I was charged twice for the same invoice",
            context={
                "customer_metadata": {
                    "disputed_amount": 500,
                    "payment_count": 2,
                    "dispute_history": []
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert result["is_valid_dispute"] == True
        assert result["resolution"]["type"] == "full_refund"


# ============================================
# ADD-ON MONETIZATION TESTS (5 agents)
# ============================================

class TestAddOnRecommender:
    """Tests for Add-On Recommender Agent"""

    @pytest.fixture
    def agent(self):
        return AddOnRecommender()

    def test_initialization(self, agent):
        assert agent.config.name == "add_on_recommender"

    @pytest.mark.asyncio
    async def test_premium_support_recommendation(self, agent):
        """Test recommending premium support for high-ticket customers"""
        state = create_initial_state(
            "What add-ons would help us?",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "company_size": 500,
                    "support_tickets_per_month": 25,
                    "avg_response_time_hours": 6
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert len(result["add_on_recommendations"]) > 0


class TestPremiumSupportSeller:
    """Tests for Premium Support Seller Agent"""

    @pytest.fixture
    def agent(self):
        return PremiumSupportSeller()

    def test_initialization(self, agent):
        assert agent.config.name == "premium_support_seller"

    @pytest.mark.asyncio
    async def test_sell_premium_support(self, agent):
        """Test selling premium support"""
        state = create_initial_state(
            "Tell me about premium support",
            context={
                "customer_metadata": {
                    "support_tickets_per_month": 30
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestTrainingSeller:
    """Tests for Training Seller Agent"""

    @pytest.fixture
    def agent(self):
        return TrainingSeller()

    def test_initialization(self, agent):
        assert agent.config.name == "training_seller"

    @pytest.mark.asyncio
    async def test_recommend_training(self, agent):
        """Test training package recommendation"""
        state = create_initial_state(
            "We need help onboarding our team",
            context={
                "customer_metadata": {
                    "team_size": 50,
                    "feature_adoption_rate": 0.25
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestProfServicesSeller:
    """Tests for Professional Services Seller Agent"""

    @pytest.fixture
    def agent(self):
        return ProfServicesSeller()

    def test_initialization(self, agent):
        assert agent.config.name == "prof_services_seller"

    @pytest.mark.asyncio
    async def test_scope_custom_project(self, agent):
        """Test scoping custom integration project"""
        state = create_initial_state(
            "We need a custom integration with Salesforce",
            context={
                "customer_metadata": {
                    "custom_integration_requests": 5
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestAdoptionTracker:
    """Tests for Adoption Tracker Agent"""

    @pytest.fixture
    def agent(self):
        return AdoptionTracker()

    def test_initialization(self, agent):
        assert agent.config.name == "adoption_tracker"

    @pytest.mark.asyncio
    async def test_track_add_on_usage(self, agent):
        """Test tracking add-on adoption and usage"""
        state = create_initial_state(
            "How is our team using premium support?",
            context={
                "customer_metadata": {
                    "add_ons": ["premium_support"],
                    "premium_support_hours_used": 15,
                    "premium_support_hours_limit": 20
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


# ============================================
# ACCOUNT EXPANSION TESTS (5 agents)
# ============================================

class TestSeatExpansion:
    """Tests for Seat Expansion Agent"""

    @pytest.fixture
    def agent(self):
        return SeatExpansion()

    def test_initialization(self, agent):
        assert agent.config.name == "seat_expansion"

    @pytest.mark.asyncio
    async def test_identify_seat_expansion(self, agent):
        """Test identifying seat expansion opportunity"""
        state = create_initial_state(
            "We're growing our team",
            context={
                "customer_metadata": {
                    "seats_active": 48,
                    "seats_limit": 50,
                    "team_growth_rate": 0.15
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestPlanUpgrade:
    """Tests for Plan Upgrade Agent"""

    @pytest.fixture
    def agent(self):
        return PlanUpgrade()

    def test_initialization(self, agent):
        assert agent.config.name == "plan_upgrade"

    @pytest.mark.asyncio
    async def test_recommend_plan_upgrade(self, agent):
        """Test recommending plan upgrade"""
        state = create_initial_state(
            "What plan should we be on?",
            context={
                "customer_metadata": {
                    "current_plan": "Professional",
                    "usage_percentage": 95,
                    "company_size": 250
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestMultiYearDeal:
    """Tests for Multi-Year Deal Agent"""

    @pytest.fixture
    def agent(self):
        return MultiYearDeal()

    def test_initialization(self, agent):
        assert agent.config.name == "multi_year_deal"

    @pytest.mark.asyncio
    async def test_propose_multi_year(self, agent):
        """Test proposing multi-year contract"""
        state = create_initial_state(
            "What's the benefit of a multi-year contract?",
            context={
                "customer_metadata": {
                    "contract_type": "annual",
                    "renewal_coming_up": True,
                    "current_mrr": 5000
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestLandAndExpand:
    """Tests for Land and Expand Agent"""

    @pytest.fixture
    def agent(self):
        return LandAndExpand()

    def test_initialization(self, agent):
        assert agent.config.name == "land_and_expand"

    @pytest.mark.asyncio
    async def test_expansion_strategy(self, agent):
        """Test land and expand strategy"""
        state = create_initial_state(
            "We started with one department, now want company-wide",
            context={
                "customer_metadata": {
                    "initial_seats": 10,
                    "current_seats": 45,
                    "departments_using": 2,
                    "total_departments": 8
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestWhiteSpaceAnalyzer:
    """Tests for White Space Analyzer Agent"""

    @pytest.fixture
    def agent(self):
        return WhiteSpaceAnalyzer()

    def test_initialization(self, agent):
        assert agent.config.name == "white_space_analyzer"

    @pytest.mark.asyncio
    async def test_identify_white_space(self, agent):
        """Test identifying untapped revenue potential"""
        state = create_initial_state(
            "Where else could we use the platform?",
            context={
                "customer_metadata": {
                    "features_used": ["ticketing", "automation"],
                    "features_available": ["ticketing", "automation", "analytics", "reporting", "integrations"],
                    "company_size": 300,
                    "seats_active": 50
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


# ============================================
# PRICING OPTIMIZATION TESTS (5 agents)
# ============================================

class TestPricingAnalyzer:
    """Tests for Pricing Analyzer Agent"""

    @pytest.fixture
    def agent(self):
        return PricingAnalyzer()

    def test_initialization(self, agent):
        assert agent.config.name == "pricing_analyzer"

    @pytest.mark.asyncio
    async def test_analyze_pricing_performance(self, agent):
        """Test analyzing pricing performance"""
        state = create_initial_state(
            "Analyze our pricing effectiveness",
            context={
                "customer_metadata": {
                    "pricing_data": {
                        "conversion_rate": 0.25,
                        "avg_deal_size": 50000,
                        "discount_rate": 0.15
                    }
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestDiscountManager:
    """Tests for Discount Manager Agent"""

    @pytest.fixture
    def agent(self):
        return DiscountManager()

    def test_initialization(self, agent):
        assert agent.config.name == "discount_manager"

    @pytest.mark.asyncio
    async def test_approve_discount(self, agent):
        """Test discount approval workflow"""
        state = create_initial_state(
            "Can we get a 20% discount?",
            context={
                "customer_metadata": {
                    "deal_value": 100000,
                    "requested_discount": 0.20,
                    "company_size": 500
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestValueMetricOptimizer:
    """Tests for Value Metric Optimizer Agent"""

    @pytest.fixture
    def agent(self):
        return ValueMetricOptimizer()

    def test_initialization(self, agent):
        assert agent.config.name == "value_metric_optimizer"

    @pytest.mark.asyncio
    async def test_optimize_value_metrics(self, agent):
        """Test optimizing pricing value metrics"""
        state = create_initial_state(
            "What's the best pricing model for us?",
            context={
                "customer_metadata": {
                    "current_pricing_model": "per_seat",
                    "usage_patterns": "high_api_usage"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestPricingExperiment:
    """Tests for Pricing Experiment Agent"""

    @pytest.fixture
    def agent(self):
        return PricingExperiment()

    def test_initialization(self, agent):
        assert agent.config.name == "pricing_experiment"

    @pytest.mark.asyncio
    async def test_design_pricing_test(self, agent):
        """Test designing A/B pricing experiment"""
        state = create_initial_state(
            "Should we test $49 vs $59 pricing?",
            context={
                "customer_metadata": {
                    "current_price": 49,
                    "segment": "smb"
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestRevenueForecaster:
    """Tests for Revenue Forecaster Agent"""

    @pytest.fixture
    def agent(self):
        return RevenueForecaster()

    def test_initialization(self, agent):
        assert agent.config.name == "revenue_forecaster"

    @pytest.mark.asyncio
    async def test_forecast_revenue(self, agent):
        """Test forecasting monthly revenue"""
        state = create_initial_state(
            "Forecast next quarter revenue",
            context={
                "customer_metadata": {
                    "historical_revenue": [
                        {"month": "2024-01", "mrr": 100000},
                        {"month": "2024-02", "mrr": 110000},
                        {"month": "2024-03", "mrr": 121000}
                    ],
                    "pipeline_value": 500000
                }
            }
        )

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "revenue_forecast" in result
