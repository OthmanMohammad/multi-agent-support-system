"""
Operational analytics models for Tier 3
Analytics & Insights Swarm database tables
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Date, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from decimal import Decimal
import uuid

from src.database.models.base import BaseModel


class AnomalyDetection(BaseModel):
    """
    Anomaly detections by TASK-2013
    Track unusual patterns in metrics
    """

    __tablename__ = "anomaly_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Anomaly details
    metric_name = Column(String(255), nullable=False, index=True)
    metric_category = Column(String(100), nullable=True, index=True)
    current_value = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=True)
    historical_avg = Column(Float, nullable=True)
    historical_std = Column(Float, nullable=True)

    # Statistical analysis
    z_score = Column(Float, nullable=True)
    severity = Column(String(50), nullable=False, index=True)  # 'critical', 'warning', 'info'
    anomaly_type = Column(String(50), nullable=True)  # 'spike', 'drop', 'unusual_pattern'

    # Diagnosis
    diagnosis = Column(Text, nullable=True)
    possible_causes = Column(JSONB, default=list, nullable=False)
    recommended_actions = Column(JSONB, default=list, nullable=False)

    # Context
    time_window = Column(String(100), nullable=True)
    comparison_period = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)

    # Status
    status = Column(String(50), default="open", nullable=False, index=True)
    alert_sent = Column(Boolean, default=False, nullable=False)
    alerted_channels = Column(JSONB, default=list, nullable=False)
    assigned_to = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Tracking
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<AnomalyDetection(metric={self.metric_name}, severity={self.severity}, z_score={self.z_score})>"


class CohortAnalysis(BaseModel):
    """
    Cohort analysis results by TASK-2015
    Track retention and metrics by customer cohorts
    """

    __tablename__ = "cohort_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Cohort definition
    cohort_name = Column(String(255), nullable=False, index=True)
    cohort_type = Column(String(100), nullable=False, index=True)  # 'signup_month', 'plan_tier', etc.
    cohort_value = Column(String(255), nullable=False)
    cohort_start_date = Column(Date, nullable=True)

    # Cohort size
    cohort_size = Column(Integer, nullable=False)
    active_customers = Column(Integer, nullable=True)
    churned_customers = Column(Integer, nullable=True)

    # Retention metrics (by month from cohort start)
    month_0_retention = Column(Float, nullable=True)  # Always 1.00
    month_1_retention = Column(Float, nullable=True)
    month_3_retention = Column(Float, nullable=True)
    month_6_retention = Column(Float, nullable=True)
    month_12_retention = Column(Float, nullable=True)

    # Revenue metrics
    avg_ltv = Column(Float, nullable=True)
    avg_arr = Column(Float, nullable=True)
    avg_months_retained = Column(Float, nullable=True)

    # Engagement metrics
    avg_dau_mau_ratio = Column(Float, nullable=True)
    avg_feature_adoption_rate = Column(Float, nullable=True)
    avg_nps = Column(Integer, nullable=True)

    # Comparison
    vs_overall_retention = Column(Float, nullable=True)
    vs_overall_ltv = Column(Float, nullable=True)

    # Tracking
    analysis_date = Column(Date, nullable=False, index=True)
    calculated_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<CohortAnalysis(cohort={self.cohort_name}, size={self.cohort_size}, retention={self.month_12_retention})>"


class ABTestResult(BaseModel):
    """
    A/B test results by TASK-2017
    Statistical analysis of experiments
    """

    __tablename__ = "ab_test_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Test details
    test_name = Column(String(255), nullable=False, index=True)
    test_type = Column(String(100), nullable=True)  # 'pricing', 'prompt', 'ui', 'email'
    hypothesis = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True, index=True)
    end_date = Column(Date, nullable=True)

    # Variants
    control_variant = Column(JSONB, default=dict, nullable=False)
    test_variants = Column(JSONB, default=list, nullable=False)

    # Results
    primary_metric = Column(String(100), nullable=True)
    control_metric_value = Column(Float, nullable=True)
    test_variant_results = Column(JSONB, default=list, nullable=False)

    # Statistical analysis
    statistical_significance = Column(Boolean, default=False, nullable=False)
    p_value = Column(Float, nullable=True)
    confidence_level = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=True)
    winner = Column(String(100), nullable=True, index=True)

    # Decision
    decision = Column(String(100), nullable=True)
    decision_rationale = Column(Text, nullable=True)
    implemented = Column(Boolean, default=False, nullable=False)
    implementation_date = Column(Date, nullable=True)

    # Tracking
    analyzed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    analyzed_by = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ABTestResult(test={self.test_name}, winner={self.winner}, significance={self.statistical_significance})>"


class FunnelStep(BaseModel):
    """
    Funnel step definitions by TASK-2016
    Define steps in conversion funnels
    """

    __tablename__ = "funnel_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Funnel definition
    funnel_name = Column(String(255), nullable=False, index=True)
    funnel_type = Column(String(100), nullable=True)  # 'sales', 'onboarding', 'support'
    step_order = Column(Integer, nullable=False)
    step_name = Column(String(255), nullable=False)

    # Step criteria
    entry_criteria = Column(JSONB, default=dict, nullable=False)
    exit_criteria = Column(JSONB, default=dict, nullable=False)

    __table_args__ = (
        Index('idx_funnel_step', 'funnel_name', 'step_order', unique=True),
    )

    def __repr__(self) -> str:
        return f"<FunnelStep(funnel={self.funnel_name}, step={self.step_order}:{self.step_name})>"


class FunnelAnalysis(BaseModel):
    """
    Funnel analysis results by TASK-2016
    Track conversion rates and bottlenecks
    """

    __tablename__ = "funnel_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Analysis period
    funnel_name = Column(String(255), nullable=False, index=True)
    analysis_date = Column(Date, nullable=False, index=True)
    time_period = Column(String(100), nullable=True)

    # Funnel steps with metrics
    steps = Column(JSONB, default=list, nullable=False)

    # Overall metrics
    total_entered = Column(Integer, nullable=True)
    total_completed = Column(Integer, nullable=True)
    overall_conversion_rate = Column(Float, nullable=True)
    avg_time_to_completion_days = Column(Float, nullable=True)

    # Bottlenecks
    biggest_dropoff_step = Column(String(255), nullable=True)
    biggest_dropoff_rate = Column(Float, nullable=True)
    slowest_step = Column(String(255), nullable=True)
    slowest_step_avg_days = Column(Float, nullable=True)

    # Recommendations
    optimization_opportunities = Column(JSONB, default=list, nullable=False)

    # Comparison
    vs_previous_period = Column(JSONB, default=dict, nullable=False)

    # Tracking
    calculated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index('idx_funnel_period', 'funnel_name', 'analysis_date', 'time_period', unique=True),
    )

    def __repr__(self) -> str:
        return f"<FunnelAnalysis(funnel={self.funnel_name}, conversion={self.overall_conversion_rate})>"


class CorrelationAnalysis(BaseModel):
    """
    Correlation analysis results by TASK-2022
    Find relationships between metrics
    """

    __tablename__ = "correlation_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Variables
    variable_1 = Column(String(255), nullable=False, index=True)
    variable_2 = Column(String(255), nullable=False, index=True)
    correlation_type = Column(String(100), default="pearson", nullable=False)

    # Results
    correlation_coefficient = Column(Float, nullable=True)
    strength = Column(String(50), nullable=True)  # 'strong', 'moderate', 'weak'
    direction = Column(String(50), nullable=True)  # 'positive', 'negative', 'none'
    p_value = Column(Float, nullable=True)
    statistically_significant = Column(Boolean, default=False, nullable=False)

    # Analysis details
    sample_size = Column(Integer, nullable=True)
    time_period = Column(String(100), nullable=True)
    data_source = Column(String(255), nullable=True)

    # Interpretation
    hypothesis = Column(Text, nullable=True)
    causation_likelihood = Column(String(50), nullable=True)
    confounding_factors = Column(JSONB, default=list, nullable=False)
    recommended_tests = Column(JSONB, default=list, nullable=False)

    # Tracking
    analyzed_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('idx_variables', 'variable_1', 'variable_2'),
    )

    def __repr__(self) -> str:
        return f"<CorrelationAnalysis(v1={self.variable_1}, v2={self.variable_2}, r={self.correlation_coefficient})>"


class NLQuery(BaseModel):
    """
    Natural language queries by TASK-2021
    Track user queries and generated SQL
    """

    __tablename__ = "nl_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Query
    user_email = Column(String(255), nullable=True, index=True)
    user_role = Column(String(100), nullable=True)
    natural_language_query = Column(Text, nullable=False)

    # Parsed intent
    parsed_intent = Column(JSONB, default=dict, nullable=False)

    # Generated SQL
    generated_sql = Column(Text, nullable=True)
    sql_safe = Column(Boolean, default=False, nullable=False)
    sql_complexity = Column(String(50), nullable=True)

    # Execution
    executed = Column(Boolean, default=False, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    rows_returned = Column(Integer, nullable=True)
    success = Column(Boolean, default=False, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    # Results
    results = Column(JSONB, default=list, nullable=False)
    visualization_type = Column(String(100), nullable=True)
    visualization_config = Column(JSONB, default=dict, nullable=False)

    # Feedback
    user_satisfied = Column(Boolean, nullable=True)
    user_feedback = Column(Text, nullable=True)

    # Tracking
    queried_at = Column(DateTime(timezone=True), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<NLQuery(user={self.user_email}, query={self.natural_language_query[:50]})>"


class ExecutiveReport(BaseModel):
    """
    Executive reports by TASK-2018
    Automated weekly/monthly/quarterly reports
    """

    __tablename__ = "executive_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Report details
    report_type = Column(String(100), nullable=False, index=True)  # 'weekly', 'monthly', 'quarterly'
    report_period_start = Column(Date, nullable=False)
    report_period_end = Column(Date, nullable=False)

    # Content sections
    executive_summary = Column(Text, nullable=True)
    key_metrics = Column(JSONB, default=dict, nullable=False)
    notable_changes = Column(JSONB, default=list, nullable=False)
    top_issues = Column(JSONB, default=list, nullable=False)
    achievements = Column(JSONB, default=list, nullable=False)
    action_items = Column(JSONB, default=list, nullable=False)

    # Visualizations
    charts = Column(JSONB, default=list, nullable=False)

    # Document
    pdf_url = Column(String(500), nullable=True)
    markdown_content = Column(Text, nullable=True)

    # Distribution
    recipients = Column(JSONB, default=list, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivery_status = Column(String(50), default="pending", nullable=False)

    # Tracking
    generated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    generated_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_report_period', 'report_period_start', 'report_period_end'),
    )

    def __repr__(self) -> str:
        return f"<ExecutiveReport(type={self.report_type}, period={self.report_period_start} to {self.report_period_end})>"


class Insight(BaseModel):
    """
    Insights by TASK-2019
    AI-generated insights from data analysis
    """

    __tablename__ = "insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Insight details
    insight_category = Column(String(100), nullable=False, index=True)
    priority = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Context
    related_metrics = Column(JSONB, default=list, nullable=False)
    metric_values = Column(JSONB, default=dict, nullable=False)
    time_period = Column(String(100), nullable=True)

    # Recommendations
    recommended_actions = Column(JSONB, default=list, nullable=False)
    estimated_impact = Column(String(255), nullable=True)

    # Confidence
    confidence = Column(String(50), nullable=True)
    supporting_data = Column(JSONB, default=dict, nullable=False)

    # Status
    status = Column(String(50), default="new", nullable=False, index=True)
    assigned_to = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Tracking
    discovered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Insight(category={self.insight_category}, priority={self.priority}, title={self.title})>"


class PredictionExplanation(BaseModel):
    """
    ML prediction explanations by TASK-2020
    SHAP values and interpretability
    """

    __tablename__ = "prediction_explanations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Prediction context
    model_name = Column(String(255), nullable=False, index=True)
    model_version = Column(String(50), nullable=True)
    entity_type = Column(String(100), nullable=False)  # 'customer', 'lead', 'opportunity'
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Prediction
    prediction_value = Column(Float, nullable=False)
    prediction_category = Column(String(100), nullable=True)

    # SHAP explanations
    shap_values = Column(JSONB, default=list, nullable=False)
    top_features = Column(JSONB, default=list, nullable=False)
    feature_directions = Column(JSONB, default=dict, nullable=False)

    # Human-readable explanation
    explanation_text = Column(Text, nullable=True)
    key_reasons = Column(JSONB, default=list, nullable=False)
    recommended_actions = Column(JSONB, default=list, nullable=False)

    # Feedback
    explanation_helpful = Column(Boolean, nullable=True)
    user_feedback = Column(Text, nullable=True)

    # Tracking
    explained_at = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('idx_entity', 'entity_type', 'entity_id'),
    )

    def __repr__(self) -> str:
        return f"<PredictionExplanation(model={self.model_name}, entity={self.entity_type}:{self.entity_id})>"
