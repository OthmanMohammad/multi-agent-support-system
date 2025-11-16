"""
Quality Assurance metrics models for Tier 3
QA Swarm database tables
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from src.database.models.base import BaseModel


class ResponseQualityCheck(BaseModel):
    """
    Response quality checks by TASK-2101 to TASK-2110
    Verification results before sending responses
    """

    __tablename__ = "response_quality_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id = Column(UUID(as_uuid=True), nullable=True)

    # Check types performed
    checks_performed = Column(JSONB, default=list, nullable=False)

    # Individual check results
    fact_check_passed = Column(Boolean, nullable=True)
    fact_check_details = Column(JSONB, default=dict, nullable=False)

    policy_check_passed = Column(Boolean, nullable=True)
    policy_violations = Column(JSONB, default=list, nullable=False)

    tone_check_passed = Column(Boolean, nullable=True)
    tone_appropriateness = Column(Float, nullable=True)
    tone_issues = Column(JSONB, default=list, nullable=False)

    completeness_check_passed = Column(Boolean, nullable=True)
    completeness_score = Column(Float, nullable=True)
    missing_elements = Column(JSONB, default=list, nullable=False)

    code_validation_passed = Column(Boolean, nullable=True)
    code_issues = Column(JSONB, default=list, nullable=False)

    link_check_passed = Column(Boolean, nullable=True)
    broken_links = Column(JSONB, default=list, nullable=False)

    sensitivity_check_passed = Column(Boolean, nullable=True)
    sensitivity_issues = Column(JSONB, default=list, nullable=False)

    hallucination_detected = Column(Boolean, nullable=True)
    hallucination_details = Column(JSONB, default=dict, nullable=False)

    citation_check_passed = Column(Boolean, nullable=True)
    citation_issues = Column(JSONB, default=list, nullable=False)

    # Overall result
    all_checks_passed = Column(Boolean, nullable=False, index=True)
    overall_quality_score = Column(Float, nullable=True)
    response_approved = Column(Boolean, nullable=False)
    blocked_reason = Column(Text, nullable=True)

    # Tracking
    checked_at = Column(DateTime(timezone=True), nullable=False, index=True)
    check_duration_ms = Column(Integer, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="quality_checks")

    def __repr__(self) -> str:
        return f"<ResponseQualityCheck(conversation_id={self.conversation_id}, approved={self.response_approved}, score={self.overall_quality_score})>"


class KBArticleQuality(BaseModel):
    """
    Knowledge base article quality by TASK-2102, TASK-2110
    Track KB article health and issues
    """

    __tablename__ = "kb_article_quality"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True),
        ForeignKey("kb_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Quality checks
    fact_accuracy_score = Column(Float, nullable=True)
    citation_completeness = Column(Float, nullable=True)
    link_validity_score = Column(Float, nullable=True)
    content_freshness_days = Column(Integer, nullable=True)

    # Issues
    broken_links = Column(JSONB, default=list, nullable=False)
    outdated_information = Column(JSONB, default=list, nullable=False)
    missing_citations = Column(JSONB, default=list, nullable=False)

    # Usage quality
    helpfulness_score = Column(Float, nullable=True)
    search_ranking = Column(Float, nullable=True)

    # Recommendations
    needs_update = Column(Boolean, default=False, nullable=False, index=True)
    recommended_actions = Column(JSONB, default=list, nullable=False)

    # Tracking
    checked_at = Column(DateTime(timezone=True), nullable=False, index=True)

    # Relationships
    article = relationship("KBArticle", back_populates="quality_checks")

    def __repr__(self) -> str:
        return f"<KBArticleQuality(article_id={self.article_id}, needs_update={self.needs_update})>"


class PolicyRule(BaseModel):
    """
    Policy rules enforced by TASK-2103
    Define company policies for enforcement
    """

    __tablename__ = "policy_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Policy details
    policy_name = Column(String(255), nullable=False, index=True)
    policy_category = Column(String(100), nullable=False, index=True)
    policy_description = Column(Text, nullable=True)

    # Rule definition
    rule_type = Column(String(100), nullable=False)
    rule_config = Column(JSONB, default=dict, nullable=False)

    # Enforcement
    enforcement_level = Column(String(50), default="strict", nullable=False)
    violation_action = Column(String(100), nullable=False)

    # Examples
    compliant_examples = Column(JSONB, default=list, nullable=False)
    violation_examples = Column(JSONB, default=list, nullable=False)

    # Status
    active = Column(Boolean, default=True, nullable=False, index=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<PolicyRule(name={self.policy_name}, category={self.policy_category}, active={self.active})>"


class CodeValidationResult(BaseModel):
    """
    Code validation results by TASK-2106
    Verify code examples in responses
    """

    __tablename__ = "code_validation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Context
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id = Column(UUID(as_uuid=True), nullable=True)
    code_block_index = Column(Integer, nullable=True)

    # Code details
    programming_language = Column(String(50), nullable=False, index=True)
    code_content = Column(Text, nullable=False)
    code_length = Column(Integer, nullable=True)

    # Validation checks
    syntax_valid = Column(Boolean, nullable=True)
    syntax_errors = Column(JSONB, default=list, nullable=False)

    imports_valid = Column(Boolean, nullable=True)
    invalid_imports = Column(JSONB, default=list, nullable=False)

    api_endpoints_valid = Column(Boolean, nullable=True)
    invalid_endpoints = Column(JSONB, default=list, nullable=False)

    # Sandbox execution (if applicable)
    executed_in_sandbox = Column(Boolean, default=False, nullable=False)
    execution_success = Column(Boolean, nullable=True)
    execution_output = Column(Text, nullable=True)
    execution_errors = Column(Text, nullable=True)

    # Overall result
    validation_passed = Column(Boolean, nullable=False, index=True)
    validation_score = Column(Float, nullable=True)
    issues_found = Column(Integer, nullable=True)
    critical_issues = Column(Integer, nullable=True)

    # Recommendations
    suggested_fixes = Column(JSONB, default=list, nullable=False)

    # Tracking
    validated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    validation_time_ms = Column(Integer, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="code_validations")

    def __repr__(self) -> str:
        return f"<CodeValidationResult(conversation_id={self.conversation_id}, language={self.programming_language}, passed={self.validation_passed})>"


class LinkCheckResult(BaseModel):
    """
    Link check results by TASK-2107
    Verify URLs in responses and KB articles
    """

    __tablename__ = "link_check_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link details
    url = Column(String(2000), nullable=False, index=True)
    url_domain = Column(String(255), nullable=True, index=True)
    url_context = Column(String(100), nullable=True)

    # Source
    source_type = Column(String(100), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Check result
    check_type = Column(String(50), default="real_time", nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Status
    link_working = Column(Boolean, nullable=False, index=True)
    error_type = Column(String(100), nullable=True)
    redirect_url = Column(String(2000), nullable=True)

    # Action taken
    action = Column(String(100), default="none", nullable=False)
    replacement_url = Column(String(2000), nullable=True)

    # Tracking
    checked_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_working_at = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index('idx_source', 'source_type', 'source_id'),
    )

    def __repr__(self) -> str:
        return f"<LinkCheckResult(url={self.url[:50]}, working={self.link_working}, status={self.status_code})>"


class SensitivityViolation(BaseModel):
    """
    Sensitivity violations by TASK-2108
    Track inappropriate content detections
    """

    __tablename__ = "sensitivity_violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Context
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id = Column(UUID(as_uuid=True), nullable=True)
    text_content = Column(Text, nullable=True)

    # Violation details
    violation_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)

    # Detected issues
    detected_issues = Column(JSONB, default=list, nullable=False)
    offensive_terms = Column(JSONB, default=list, nullable=False)
    bias_indicators = Column(JSONB, default=list, nullable=False)
    pii_detected = Column(JSONB, default=list, nullable=False)

    # Action taken
    response_blocked = Column(Boolean, default=False, nullable=False)
    auto_remediation_attempted = Column(Boolean, default=False, nullable=False)
    remediation_suggestions = Column(JSONB, default=list, nullable=False)

    # Review
    false_positive = Column(Boolean, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)

    # Tracking
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="sensitivity_violations")

    def __repr__(self) -> str:
        return f"<SensitivityViolation(type={self.violation_type}, severity={self.severity}, blocked={self.response_blocked})>"


class HallucinationDetection(BaseModel):
    """
    Hallucination detections by TASK-2109
    Track AI-generated false information
    """

    __tablename__ = "hallucination_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Context
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_id = Column(UUID(as_uuid=True), nullable=True)
    agent_id = Column(String(100), nullable=True, index=True)

    # Hallucinated content
    hallucination_type = Column(String(100), nullable=False, index=True)
    hallucinated_claim = Column(Text, nullable=True)
    hallucinated_elements = Column(JSONB, default=list, nullable=False)

    # Verification
    verification_method = Column(String(100), nullable=True)
    verification_sources = Column(JSONB, default=list, nullable=False)
    confidence = Column(Float, nullable=True)

    # Impact
    severity = Column(String(50), nullable=False, index=True)
    potential_customer_impact = Column(String(255), nullable=True)

    # Correction
    correct_information = Column(Text, nullable=True)
    corrected_response = Column(Text, nullable=True)
    response_blocked = Column(Boolean, default=False, nullable=False)

    # Tracking
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    detected_by = Column(String(100), default="TASK-2109", nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="hallucination_detections")

    def __repr__(self) -> str:
        return f"<HallucinationDetection(type={self.hallucination_type}, severity={self.severity}, blocked={self.response_blocked})>"
