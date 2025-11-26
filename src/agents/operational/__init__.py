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
    ABTestAnalyzerAgent,
    AnomalyDetectorAgent,
    CohortAnalyzerAgent,
    CorrelationFinderAgent,
    DashboardGeneratorAgent,
    FunnelAnalyzerAgent,
    InsightSummarizerAgent,
    MetricsTrackerAgent,
    PredictionExplainerAgent,
    QueryBuilderAgent,
    ReportGeneratorAgent,
    TrendAnalyzerAgent,
)

# Automation & Workflow Swarm (20 agents)
from src.agents.operational.automation import (
    ApprovalRouterAgent,
    CalendarSchedulerAgent,
    CleanupSchedulerAgent,
    ContactEnricherAgent,
    # Data Automation (5)
    CRMUpdaterAgent,
    DataBackupAgent,
    DataValidatorAgent,
    DeduplicatorAgent,
    EmailSenderAgent,
    HandoffAutomatorAgent,
    InvoiceSenderAgent,
    NotificationSenderAgent,
    OnboardingAutomatorAgent,
    PaymentRetryAgent,
    ReminderSenderAgent,
    RenewalProcessorAgent,
    ReportAutomatorAgent,
    SLAEnforcerAgent,
    # Task Automation (5)
    TicketCreatorAgent,
    # Process Automation (10)
    WorkflowExecutorAgent,
)

# Quality Assurance Swarm (10 agents)
from src.agents.operational.qa import (
    CitationValidatorAgent,
    CodeValidatorAgent,
    CompletenessCheckerAgent,
    FactCheckerAgent,
    HallucinationDetectorAgent,
    LinkCheckerAgent,
    PolicyCheckerAgent,
    ResponseVerifierAgent,
    SensitivityCheckerAgent,
    ToneCheckerAgent,
)

# Security & Compliance Swarm (10 agents)
from src.agents.operational.security import (
    AccessControllerAgent,
    AuditLoggerAgent,
    ComplianceCheckerAgent,
    ConsentManagerAgent,
    DataRetentionEnforcerAgent,
    EncryptionValidatorAgent,
    IncidentResponderAgent,
    PenTestCoordinatorAgent,
    PIIDetectorAgent,
    VulnerabilityScannerAgent,
)

__all__ = [
    "ABTestAnalyzerAgent",
    "AccessControllerAgent",
    "AnomalyDetectorAgent",
    "ApprovalRouterAgent",
    "AuditLoggerAgent",
    "CRMUpdaterAgent",
    "CalendarSchedulerAgent",
    "CitationValidatorAgent",
    "CleanupSchedulerAgent",
    "CodeValidatorAgent",
    "CohortAnalyzerAgent",
    "CompletenessCheckerAgent",
    "ComplianceCheckerAgent",
    "ConsentManagerAgent",
    "ContactEnricherAgent",
    "CorrelationFinderAgent",
    "DashboardGeneratorAgent",
    "DataBackupAgent",
    "DataRetentionEnforcerAgent",
    "DataValidatorAgent",
    "DeduplicatorAgent",
    "EmailSenderAgent",
    "EncryptionValidatorAgent",
    "FactCheckerAgent",
    "FunnelAnalyzerAgent",
    "HallucinationDetectorAgent",
    "HandoffAutomatorAgent",
    "IncidentResponderAgent",
    "InsightSummarizerAgent",
    "InvoiceSenderAgent",
    "LinkCheckerAgent",
    # Analytics & Insights (12)
    "MetricsTrackerAgent",
    "NotificationSenderAgent",
    "OnboardingAutomatorAgent",
    # Security & Compliance (10)
    "PIIDetectorAgent",
    "PaymentRetryAgent",
    "PenTestCoordinatorAgent",
    "PolicyCheckerAgent",
    "PredictionExplainerAgent",
    "QueryBuilderAgent",
    "ReminderSenderAgent",
    "RenewalProcessorAgent",
    "ReportAutomatorAgent",
    "ReportGeneratorAgent",
    # Quality Assurance (10)
    "ResponseVerifierAgent",
    "SLAEnforcerAgent",
    "SensitivityCheckerAgent",
    # Automation & Workflow (20)
    "TicketCreatorAgent",
    "ToneCheckerAgent",
    "TrendAnalyzerAgent",
    "VulnerabilityScannerAgent",
    "WorkflowExecutorAgent",
]
