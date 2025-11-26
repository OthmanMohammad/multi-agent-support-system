"""
Product Education Agents - Specialized agents for product education and value communication.

This module contains 5 specialized agents for product education:
1. Feature Explainer - Explains product features clearly, tailored to industry/role (TASK-1021)
2. Use Case Matcher - Matches prospect needs to use cases and customer stories (TASK-1022)
3. Demo Preparer - Creates personalized demo environments and scripts (TASK-1023)
4. ROI Calculator - Calculates time/cost savings ROI and payback periods (TASK-1024)
5. Value Proposition - Crafts tailored value props and competitive positioning (TASK-1025)
"""

from src.agents.revenue.sales.product_education.demo_preparer import DemoPreparer
from src.agents.revenue.sales.product_education.feature_explainer import FeatureExplainer
from src.agents.revenue.sales.product_education.roi_calculator import ROICalculator
from src.agents.revenue.sales.product_education.use_case_matcher import UseCaseMatcher
from src.agents.revenue.sales.product_education.value_proposition import ValueProposition

__all__ = [
    "DemoPreparer",
    "FeatureExplainer",
    "ROICalculator",
    "UseCaseMatcher",
    "ValueProposition",
]
