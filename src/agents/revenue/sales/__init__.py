"""
Sales Agents Module - STORY #101: Sales Swarm (30 Agents)

Complete sales agent swarm for revenue generation, including:
- Lead Qualification (6 agents)
- Product Education (5 agents)
- Objection Handling (6 agents)
- Deal Progression (6 agents)
- Competitive Intelligence (7 agents)

Total: 30 specialized sales agents for accelerating lead-to-customer conversion.
"""

# Lead Qualification (6 agents)
# Competitive Intelligence (7 agents)
from src.agents.revenue.sales.competitive_intelligence.competitor_tracker import CompetitorTracker
from src.agents.revenue.sales.competitive_intelligence.feature_comparator import FeatureComparator
from src.agents.revenue.sales.competitive_intelligence.migration_specialist import (
    MigrationSpecialist,
)
from src.agents.revenue.sales.competitive_intelligence.positioning_advisor import PositioningAdvisor
from src.agents.revenue.sales.competitive_intelligence.pricing_analyzer import PricingAnalyzer
from src.agents.revenue.sales.competitive_intelligence.review_analyzer import ReviewAnalyzer
from src.agents.revenue.sales.competitive_intelligence.sentiment_tracker import SentimentTracker
from src.agents.revenue.sales.deal_progression.closer import Closer
from src.agents.revenue.sales.deal_progression.contract_negotiator import ContractNegotiator

# Deal Progression (6 agents)
from src.agents.revenue.sales.deal_progression.demo_scheduler import DemoScheduler
from src.agents.revenue.sales.deal_progression.proposal_generator import ProposalGenerator
from src.agents.revenue.sales.deal_progression.trial_optimizer import TrialOptimizer
from src.agents.revenue.sales.deal_progression.upsell_identifier import UpsellIdentifier
from src.agents.revenue.sales.lead_qualification.bant_qualifier import BANTQualifier
from src.agents.revenue.sales.lead_qualification.disqualification_agent import DisqualificationAgent
from src.agents.revenue.sales.lead_qualification.inbound_qualifier import InboundQualifier
from src.agents.revenue.sales.lead_qualification.lead_scorer import LeadScorer
from src.agents.revenue.sales.lead_qualification.mql_to_sql_converter import MQLtoSQLConverter
from src.agents.revenue.sales.lead_qualification.referral_detector import ReferralDetector
from src.agents.revenue.sales.objection_handling.competitor_comparison_handler import (
    CompetitorComparisonHandler,
)
from src.agents.revenue.sales.objection_handling.feature_gap_handler import FeatureGapHandler
from src.agents.revenue.sales.objection_handling.integration_objection_handler import (
    IntegrationObjectionHandler,
)

# Objection Handling (6 agents)
from src.agents.revenue.sales.objection_handling.price_objection_handler import (
    PriceObjectionHandler,
)
from src.agents.revenue.sales.objection_handling.security_objection_handler import (
    SecurityObjectionHandler,
)
from src.agents.revenue.sales.objection_handling.timing_objection_handler import (
    TimingObjectionHandler,
)
from src.agents.revenue.sales.product_education.demo_preparer import DemoPreparer

# Product Education (5 agents)
from src.agents.revenue.sales.product_education.feature_explainer import FeatureExplainer
from src.agents.revenue.sales.product_education.roi_calculator import ROICalculator
from src.agents.revenue.sales.product_education.use_case_matcher import UseCaseMatcher
from src.agents.revenue.sales.product_education.value_proposition import ValueProposition

__all__ = [
    "BANTQualifier",
    "Closer",
    "CompetitorComparisonHandler",
    # Competitive Intelligence (7)
    "CompetitorTracker",
    "ContractNegotiator",
    "DemoPreparer",
    # Deal Progression (6)
    "DemoScheduler",
    "DisqualificationAgent",
    "FeatureComparator",
    # Product Education (5)
    "FeatureExplainer",
    "FeatureGapHandler",
    # Lead Qualification (6)
    "InboundQualifier",
    "IntegrationObjectionHandler",
    "LeadScorer",
    "MQLtoSQLConverter",
    "MigrationSpecialist",
    "PositioningAdvisor",
    # Objection Handling (6)
    "PriceObjectionHandler",
    "PricingAnalyzer",
    "ProposalGenerator",
    "ROICalculator",
    "ReferralDetector",
    "ReviewAnalyzer",
    "SecurityObjectionHandler",
    "SentimentTracker",
    "TimingObjectionHandler",
    "TrialOptimizer",
    "UpsellIdentifier",
    "UseCaseMatcher",
    "ValueProposition",
]
