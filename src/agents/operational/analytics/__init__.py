"""
Analytics & Insights Swarm - Tier 3: Operational Excellence

This module contains 12 specialized analytics agents for comprehensive
data analysis, reporting, and business intelligence.

Agents:
- MetricsTrackerAgent (TASK-2011): Track all key metrics across domains
- DashboardGeneratorAgent (TASK-2012): Generate role-specific dashboards (JSON output)
- AnomalyDetectorAgent (TASK-2013): Detect anomalies using Z-score (>2σ warning, >3σ critical)
- TrendAnalyzerAgent (TASK-2014): Analyze WoW, MoM, YoY trends and seasonality
- CohortAnalyzerAgent (TASK-2015): Analyze customer cohorts, retention curves, LTV
- FunnelAnalyzerAgent (TASK-2016): Analyze conversion funnels and identify bottlenecks
- ABTestAnalyzerAgent (TASK-2017): Statistical A/B test analysis (Chi-square, p<0.05)
- ReportGeneratorAgent (TASK-2018): Generate weekly/monthly/quarterly executive reports
- InsightSummarizerAgent (TASK-2019): Generate narrative insights using Claude
- PredictionExplainerAgent (TASK-2020): Explain ML predictions using SHAP values
- QueryBuilderAgent (TASK-2021): Build SQL from natural language queries
- CorrelationFinderAgent (TASK-2022): Find correlations between metrics (Pearson r>0.7)
"""

from src.agents.operational.analytics.metrics_tracker import MetricsTrackerAgent
from src.agents.operational.analytics.dashboard_generator import DashboardGeneratorAgent
from src.agents.operational.analytics.anomaly_detector import AnomalyDetectorAgent
from src.agents.operational.analytics.trend_analyzer import TrendAnalyzerAgent
from src.agents.operational.analytics.cohort_analyzer import CohortAnalyzerAgent
from src.agents.operational.analytics.funnel_analyzer import FunnelAnalyzerAgent
from src.agents.operational.analytics.ab_test_analyzer import ABTestAnalyzerAgent
from src.agents.operational.analytics.report_generator import ReportGeneratorAgent
from src.agents.operational.analytics.insight_summarizer import InsightSummarizerAgent
from src.agents.operational.analytics.prediction_explainer import PredictionExplainerAgent
from src.agents.operational.analytics.query_builder import QueryBuilderAgent
from src.agents.operational.analytics.correlation_finder import CorrelationFinderAgent


__all__ = [
    "MetricsTrackerAgent",
    "DashboardGeneratorAgent",
    "AnomalyDetectorAgent",
    "TrendAnalyzerAgent",
    "CohortAnalyzerAgent",
    "FunnelAnalyzerAgent",
    "ABTestAnalyzerAgent",
    "ReportGeneratorAgent",
    "InsightSummarizerAgent",
    "PredictionExplainerAgent",
    "QueryBuilderAgent",
    "CorrelationFinderAgent",
]
