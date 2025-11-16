"""
Tier 3: Operational Excellence Agents

This package contains 52 specialized agents for operational excellence across
analytics, quality assurance, automation, and security domains.

Swarms:
- Analytics & Insights (12 agents): Data-driven decision making
- Quality Assurance (10 agents): Ensure 95%+ response accuracy
- Automation & Workflow (20 agents): Eliminate 50-70% of manual work
- Security & Compliance (10 agents): Zero security incidents, 100% compliance

Total: 52 agents
"""

# Analytics & Insights Swarm (12 agents)
from src.agents.operational.analytics import (
    MetricsTracker,
    DashboardGenerator,
    AnomalyDetector,
    TrendAnalyzer,
    CohortAnalyzer,
    FunnelAnalyzer,
    ABTestAnalyzer,
    ReportGenerator,
    InsightSummarizer,
    PredictionExplainer,
    QueryBuilder,
    CorrelationFinder,
)

# Quality Assurance Swarm (10 agents)
from src.agents.operational.qa import (
    ResponseVerifier,
    FactChecker,
    PolicyChecker,
    ToneChecker,
    CompletenessChecker,
    CodeValidator,
    LinkChecker,
    SensitivityChecker,
    HallucinationDetector,
    CitationValidator,
)

# Automation & Workflow Swarm (20 agents)
from src.agents.operational.automation import (
    # Task Automation (5)
    TicketCreator,
    CalendarScheduler,
    EmailSender,
    ReminderSender,
    NotificationSender,
    # Data Automation (5)
    CRMUpdater,
    ContactEnricher,
    Deduplicator,
    DataValidator,
    ReportAutomator,
    # Process Automation (10)
    WorkflowExecutor,
    ApprovalRouter,
    SLAEnforcer,
    HandoffAutomator,
    OnboardingAutomator,
    RenewalProcessor,
    InvoiceSender,
    PaymentRetry,
    DataBackup,
    CleanupScheduler,
)

# Security & Compliance Swarm (10 agents)
from src.agents.operational.security import (
    PIIDetector,
    AccessController,
    AuditLogger,
    ComplianceChecker,
    VulnerabilityScanner,
    IncidentResponder,
    DataRetentionEnforcer,
    ConsentManager,
    EncryptionValidator,
    PenTestCoordinator,
)

__all__ = [
    # Analytics & Insights (12)
    "MetricsTracker",
    "DashboardGenerator",
    "AnomalyDetector",
    "TrendAnalyzer",
    "CohortAnalyzer",
    "FunnelAnalyzer",
    "ABTestAnalyzer",
    "ReportGenerator",
    "InsightSummarizer",
    "PredictionExplainer",
    "QueryBuilder",
    "CorrelationFinder",
    # Quality Assurance (10)
    "ResponseVerifier",
    "FactChecker",
    "PolicyChecker",
    "ToneChecker",
    "CompletenessChecker",
    "CodeValidator",
    "LinkChecker",
    "SensitivityChecker",
    "HallucinationDetector",
    "CitationValidator",
    # Automation & Workflow (20)
    "TicketCreator",
    "CalendarScheduler",
    "EmailSender",
    "ReminderSender",
    "NotificationSender",
    "CRMUpdater",
    "ContactEnricher",
    "Deduplicator",
    "DataValidator",
    "ReportAutomator",
    "WorkflowExecutor",
    "ApprovalRouter",
    "SLAEnforcer",
    "HandoffAutomator",
    "OnboardingAutomator",
    "RenewalProcessor",
    "InvoiceSender",
    "PaymentRetry",
    "DataBackup",
    "CleanupScheduler",
    # Security & Compliance (10)
    "PIIDetector",
    "AccessController",
    "AuditLogger",
    "ComplianceChecker",
    "VulnerabilityScanner",
    "IncidentResponder",
    "DataRetentionEnforcer",
    "ConsentManager",
    "EncryptionValidator",
    "PenTestCoordinator",
]
