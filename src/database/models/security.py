"""
Security & Compliance models for Tier 3
Security Swarm database tables
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Date, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from src.database.models.base import BaseModel


class PIIDetection(BaseModel):
    """
    PII detections by TASK-2301
    Track personally identifiable information detections
    """

    __tablename__ = "pii_detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Context
    source = Column(String(100), nullable=False, index=True)
    source_id = Column(String(255), nullable=True, index=True)

    # PII details
    pii_types_detected = Column(JSONB, default=list, nullable=False)
    pii_count = Column(Integer, nullable=True)
    pii_locations = Column(JSONB, default=list, nullable=False)

    # Severity
    severity = Column(String(50), nullable=False, index=True)
    risk_level = Column(String(50), nullable=True)

    # Action taken
    action_taken = Column(String(100), nullable=True)
    redaction_applied = Column(Boolean, default=False, nullable=False)
    original_text_stored = Column(Boolean, default=False, nullable=False)

    # Alert
    alert_sent = Column(Boolean, default=False, nullable=False)
    alerted_to = Column(String(255), nullable=True)

    # Tracking
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<PIIDetection(source={self.source}, types={self.pii_types_detected}, severity={self.severity})>"


class AccessControlLog(BaseModel):
    """
    Access control logs by TASK-2302
    Track all access attempts and permissions
    """

    __tablename__ = "access_control_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    user_role = Column(String(100), nullable=True)

    # Access attempt
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)

    # Result
    access_granted = Column(Boolean, nullable=False, index=True)
    denial_reason = Column(String(255), nullable=True)
    required_permission = Column(String(255), nullable=True)

    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)

    # Tracking
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index('idx_resource', 'resource_type', 'resource_id'),
    )

    def __repr__(self) -> str:
        return f"<AccessControlLog(user={self.user_email}, resource={self.resource_type}, granted={self.access_granted})>"


class SecurityIncident(BaseModel):
    """
    Security incidents by TASK-2306
    Track and manage security events
    """

    __tablename__ = "security_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Incident details
    incident_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Detection
    detected_by = Column(String(100), nullable=True)
    detection_method = Column(String(100), nullable=True)

    # Impact
    affected_systems = Column(JSONB, default=list, nullable=False)
    affected_users_count = Column(Integer, nullable=True)
    affected_customers = Column(JSONB, default=list, nullable=False)
    data_compromised = Column(Boolean, default=False, nullable=False)
    data_types_compromised = Column(JSONB, default=list, nullable=False)

    # Response
    status = Column(String(50), default="open", nullable=False, index=True)
    incident_commander = Column(String(255), nullable=True)
    response_team = Column(JSONB, default=list, nullable=False)
    timeline = Column(JSONB, default=list, nullable=False)

    # Resolution
    root_cause = Column(Text, nullable=True)
    remediation_steps = Column(JSONB, default=list, nullable=False)
    preventive_measures = Column(JSONB, default=list, nullable=False)

    # Compliance
    breach_notification_required = Column(Boolean, default=False, nullable=False)
    regulators_notified = Column(Boolean, default=False, nullable=False)
    customers_notified = Column(Boolean, default=False, nullable=False)
    notification_date = Column(Date, nullable=True)

    # Tracking
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    contained_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<SecurityIncident(type={self.incident_type}, severity={self.severity}, status={self.status})>"


class ComplianceAudit(BaseModel):
    """
    Compliance audits by TASK-2304
    Track regulatory compliance checks
    """

    __tablename__ = "compliance_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Audit details
    audit_type = Column(String(100), nullable=False, index=True)
    audit_scope = Column(String(255), nullable=True)

    # Checklist
    total_controls = Column(Integer, nullable=True)
    compliant_controls = Column(Integer, nullable=True)
    non_compliant_controls = Column(Integer, nullable=True)
    not_applicable_controls = Column(Integer, nullable=True)
    compliance_percentage = Column(Float, nullable=True)

    # Findings
    findings = Column(JSONB, default=list, nullable=False)
    critical_findings = Column(Integer, nullable=True)
    high_findings = Column(Integer, nullable=True)
    medium_findings = Column(Integer, nullable=True)
    low_findings = Column(Integer, nullable=True)

    # Evidence
    evidence_collected = Column(JSONB, default=list, nullable=False)

    # Status
    status = Column(String(50), default="in_progress", nullable=False, index=True)
    overall_compliance = Column(String(50), nullable=True, index=True)

    # Remediation
    remediation_plan = Column(JSONB, default=list, nullable=False)
    remediation_deadline = Column(Date, nullable=True)

    # Tracking
    audit_date = Column(Date, nullable=False, index=True)
    auditor = Column(String(255), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ComplianceAudit(type={self.audit_type}, compliance={self.overall_compliance}, percentage={self.compliance_percentage})>"


class VulnerabilityScan(BaseModel):
    """
    Vulnerability scans by TASK-2305
    Track security vulnerability assessments
    """

    __tablename__ = "vulnerability_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Scan details
    scan_type = Column(String(100), nullable=False, index=True)
    scan_scope = Column(String(255), nullable=True)
    scanner = Column(String(100), nullable=True)

    # Results
    total_vulnerabilities = Column(Integer, nullable=True)
    critical_count = Column(Integer, nullable=True)
    high_count = Column(Integer, nullable=True)
    medium_count = Column(Integer, nullable=True)
    low_count = Column(Integer, nullable=True)
    info_count = Column(Integer, nullable=True)

    # Vulnerabilities
    vulnerabilities = Column(JSONB, default=list, nullable=False)

    # Remediation
    remediation_required = Column(Integer, nullable=True)
    remediation_status = Column(JSONB, default=dict, nullable=False)

    # Tracking
    scan_started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    scan_completed_at = Column(DateTime(timezone=True), nullable=True)
    scan_duration_minutes = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<VulnerabilityScan(type={self.scan_type}, total={self.total_vulnerabilities}, critical={self.critical_count})>"


class DataRetentionPolicy(BaseModel):
    """
    Data retention policies enforced by TASK-2307
    Define data lifecycle rules
    """

    __tablename__ = "data_retention_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Policy details
    policy_name = Column(String(255), nullable=False, index=True)
    data_type = Column(String(100), nullable=False, index=True)
    retention_period_days = Column(Integer, nullable=False)

    # Enforcement
    auto_delete_enabled = Column(Boolean, default=False, nullable=False)
    archive_before_delete = Column(Boolean, default=True, nullable=False)
    archive_location = Column(String(255), nullable=True)

    # Compliance
    regulatory_requirement = Column(String(255), nullable=True)
    applicable_regulations = Column(JSONB, default=list, nullable=False)

    # Status
    active = Column(Boolean, default=True, nullable=False, index=True)
    last_enforced_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<DataRetentionPolicy(name={self.policy_name}, type={self.data_type}, days={self.retention_period_days})>"


class ConsentRecord(BaseModel):
    """
    Consent records managed by TASK-2308
    Track GDPR/CCPA consent and data subject rights
    """

    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Customer
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Consent details
    consent_type = Column(String(100), nullable=False, index=True)
    consent_granted = Column(Boolean, nullable=False)
    consent_purpose = Column(String(255), nullable=True)
    consent_text = Column(Text, nullable=True)

    # Tracking
    granted_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    consent_method = Column(String(100), nullable=True)

    # Data subject rights
    data_access_requested = Column(Boolean, default=False, nullable=False)
    data_deletion_requested = Column(Boolean, default=False, nullable=False)
    data_portability_requested = Column(Boolean, default=False, nullable=False)
    request_fulfilled_at = Column(DateTime(timezone=True), nullable=True)

    # Compliance
    regulation = Column(String(50), nullable=True)  # 'GDPR', 'CCPA', 'HIPAA'

    # Relationships
    customer = relationship("Customer", back_populates="consent_records")

    def __repr__(self) -> str:
        return f"<ConsentRecord(customer_id={self.customer_id}, type={self.consent_type}, granted={self.consent_granted})>"


class EncryptionValidation(BaseModel):
    """
    Encryption validations by TASK-2309
    Verify encryption standards compliance
    """

    __tablename__ = "encryption_validations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Validation details
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True)
    encryption_context = Column(String(100), nullable=False)  # 'at_rest', 'in_transit'

    # Encryption details
    encryption_algorithm = Column(String(100), nullable=True)
    key_size = Column(Integer, nullable=True)
    tls_version = Column(String(50), nullable=True)

    # Validation result
    encryption_valid = Column(Boolean, nullable=False, index=True)
    issues_found = Column(JSONB, default=list, nullable=False)
    recommendations = Column(JSONB, default=list, nullable=False)

    # Standards compliance
    meets_aes_256 = Column(Boolean, nullable=True)
    meets_tls_13 = Column(Boolean, nullable=True)
    key_rotation_current = Column(Boolean, nullable=True)
    last_key_rotation = Column(DateTime(timezone=True), nullable=True)

    # Tracking
    validated_at = Column(DateTime(timezone=True), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<EncryptionValidation(resource={self.resource_type}, context={self.encryption_context}, valid={self.encryption_valid})>"


class PenetrationTest(BaseModel):
    """
    Penetration tests coordinated by TASK-2310
    Track pentest activities and findings
    """

    __tablename__ = "penetration_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Test details
    test_name = Column(String(255), nullable=False, index=True)
    test_type = Column(String(100), nullable=False)  # 'external', 'internal', 'application', 'social'
    test_scope = Column(Text, nullable=True)

    # Tester information
    tester_company = Column(String(255), nullable=True)
    lead_tester = Column(String(255), nullable=True)

    # Findings
    total_findings = Column(Integer, nullable=True)
    critical_findings = Column(Integer, nullable=True)
    high_findings = Column(Integer, nullable=True)
    medium_findings = Column(Integer, nullable=True)
    low_findings = Column(Integer, nullable=True)
    info_findings = Column(Integer, nullable=True)

    # Detailed findings
    findings = Column(JSONB, default=list, nullable=False)

    # Remediation
    remediation_plan = Column(JSONB, default=list, nullable=False)
    remediation_deadline = Column(Date, nullable=True)
    remediation_completed = Column(Boolean, default=False, nullable=False)

    # Reports
    executive_summary = Column(Text, nullable=True)
    technical_report_url = Column(String(500), nullable=True)

    # Tracking
    test_start_date = Column(Date, nullable=False, index=True)
    test_end_date = Column(Date, nullable=True)
    report_delivered_date = Column(Date, nullable=True)

    def __repr__(self) -> str:
        return f"<PenetrationTest(name={self.test_name}, type={self.test_type}, findings={self.total_findings})>"
