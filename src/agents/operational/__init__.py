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
    MetricsTrackerAgent,
    DashboardGeneratorAgent,
    AnomalyDetectorAgent,
    TrendAnalyzerAgent,
    CohortAnalyzerAgent,
    FunnelAnalyzerAgent,
    ABTestAnalyzerAgent,
    ReportGeneratorAgent,
    InsightSummarizerAgent,
    PredictionExplainerAgent,
    QueryBuilderAgent,
    CorrelationFinderAgent,
)

# Quality Assurance Swarm (10 agents)
from src.agents.operational.qa import (
    ResponseVerifierAgent,
    FactCheckerAgent,
    PolicyCheckerAgent,
    ToneCheckerAgent,
    CompletenessCheckerAgent,
    CodeValidatorAgent,
    LinkCheckerAgent,
    SensitivityCheckerAgent,
    HallucinationDetectorAgent,
    CitationValidatorAgent,
)

# Automation & Workflow Swarm (20 agents)
from src.agents.operational.automation import (
    # Task Automation (5)
    TicketCreatorAgent,
    CalendarSchedulerAgent,
    EmailSenderAgent,
    ReminderSenderAgent,
    NotificationSenderAgent,
    # Data Automation (5)
    CRMUpdaterAgent,
    ContactEnricherAgent,
    DeduplicatorAgent,
    DataValidatorAgent,
    ReportAutomatorAgent,
    # Process Automation (10)
    WorkflowExecutorAgent,
    ApprovalRouterAgent,
    SLAEnforcerAgent,
    HandoffAutomatorAgent,
    OnboardingAutomatorAgent,
    RenewalProcessorAgent,
    InvoiceSenderAgent,
    PaymentRetryAgent,
    DataBackupAgent,
    CleanupSchedulerAgent,
)

# Security & Compliance Swarm (10 agents)
from src.agents.operational.security import (
    PIIDetectorAgent,
    AccessControllerAgent,
    AuditLoggerAgent,
    ComplianceCheckerAgent,
    VulnerabilityScannerAgent,
    IncidentResponderAgent,
    DataRetentionEnforcerAgent,
    ConsentManagerAgent,
    EncryptionValidatorAgent,
    PenTestCoordinatorAgent,
)

__all__ = [
    # Analytics & Insights (12)
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
    # Quality Assurance (10)
    "ResponseVerifierAgent",
    "FactCheckerAgent",
    "PolicyCheckerAgent",
    "ToneCheckerAgent",
    "CompletenessCheckerAgent",
    "CodeValidatorAgent",
    "LinkCheckerAgent",
    "SensitivityCheckerAgent",
    "HallucinationDetectorAgent",
    "CitationValidatorAgent",
    # Automation & Workflow (20)
    "TicketCreatorAgent",
    "CalendarSchedulerAgent",
    "EmailSenderAgent",
    "ReminderSenderAgent",
    "NotificationSenderAgent",
    "CRMUpdaterAgent",
    "ContactEnricherAgent",
    "DeduplicatorAgent",
    "DataValidatorAgent",
    "ReportAutomatorAgent",
    "WorkflowExecutorAgent",
    "ApprovalRouterAgent",
    "SLAEnforcerAgent",
    "HandoffAutomatorAgent",
    "OnboardingAutomatorAgent",
    "RenewalProcessorAgent",
    "InvoiceSenderAgent",
    "PaymentRetryAgent",
    "DataBackupAgent",
    "CleanupSchedulerAgent",
    # Security & Compliance (10)
    "PIIDetectorAgent",
    "AccessControllerAgent",
    "AuditLoggerAgent",
    "ComplianceCheckerAgent",
    "VulnerabilityScannerAgent",
    "IncidentResponderAgent",
    "DataRetentionEnforcerAgent",
    "ConsentManagerAgent",
    "EncryptionValidatorAgent",
    "PenTestCoordinatorAgent",
]
