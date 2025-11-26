"""
Database models package
"""

# Base classes
# Agent collaboration
from src.database.models.agent_handoff import (
    AgentCollaboration,
    AgentHandoff,
    ConversationTag,
)
from src.database.models.agent_performance import AgentPerformance

# Analytics
from src.database.models.analytics import (
    ABTest,
    ConversationAnalytics,
    FeatureUsage,
)
from src.database.models.api_key import APIKey

# Security & compliance
from src.database.models.audit_log import AuditLog
from src.database.models.automation import (
    AutomatedTask,
    AutomationWorkflowExecution,
    SLACompliance,
)
from src.database.models.base import AuditMixin, Base, BaseModel, TimestampMixin
from src.database.models.conversation import Conversation

# Core models
from src.database.models.customer import Customer

# Customer health & segmentation
from src.database.models.customer_health import (
    CustomerContact,
    CustomerHealthEvent,
    CustomerIntegration,
    CustomerNote,
    CustomerSegment,
)

# Knowledge Base
from src.database.models.kb_article import (
    KBArticle,
    KBQualityReport,
    KBUsage,
)
from src.database.models.message import Message

# Tier 3: Operational Excellence models
from src.database.models.operational_analytics import (
    ABTestResult,
    AnomalyDetection,
    CohortAnalysis,
    CorrelationAnalysis,
    ExecutiveReport,
    FunnelAnalysis,
    FunnelStep,
    Insight,
    NLQuery,
    PredictionExplanation,
)
from src.database.models.qa_metrics import (
    CodeValidationResult,
    HallucinationDetection,
    KBArticleQuality,
    LinkCheckResult,
    PolicyRule,
    ResponseQualityCheck,
    SensitivityViolation,
)

# Sales & leads
from src.database.models.sales import (
    Deal,
    Employee,
    Lead,
    Quote,
    SalesActivity,
)
from src.database.models.security import (
    AccessControlLog,
    ComplianceAudit,
    ConsentRecord,
    DataRetentionPolicy,
    EncryptionValidation,
    PenetrationTest,
    PIIDetection,
    SecurityIncident,
    VulnerabilityScan,
)

# Subscription & billing
from src.database.models.subscription import (
    Credit,
    Invoice,
    Payment,
    Subscription,
    UsageEvent,
)

# Authentication & authorization
from src.database.models.user import OAuthProvider, User, UserRole, UserStatus

# Workflow automation
from src.database.models.workflow import (
    ScheduledTask,
    Workflow,
    WorkflowExecution,
)

__all__ = [
    "ABTest",
    "ABTestResult",
    "APIKey",
    "AccessControlLog",
    "AgentCollaboration",
    # Agent collaboration
    "AgentHandoff",
    "AgentPerformance",
    # Tier 3: Operational Analytics
    "AnomalyDetection",
    # Security & compliance
    "AuditLog",
    "AuditMixin",
    # Tier 3: Automation
    "AutomatedTask",
    "AutomationWorkflowExecution",
    # Base classes
    "Base",
    "BaseModel",
    "CodeValidationResult",
    "CohortAnalysis",
    "ComplianceAudit",
    "ConsentRecord",
    "Conversation",
    # Analytics
    "ConversationAnalytics",
    "ConversationTag",
    "CorrelationAnalysis",
    "Credit",
    # Core models
    "Customer",
    "CustomerContact",
    # Customer health & segmentation
    "CustomerHealthEvent",
    "CustomerIntegration",
    "CustomerNote",
    "CustomerSegment",
    "DataRetentionPolicy",
    "Deal",
    # Sales & leads
    "Employee",
    "EncryptionValidation",
    "ExecutiveReport",
    "FeatureUsage",
    "FunnelAnalysis",
    "FunnelStep",
    "HallucinationDetection",
    "Insight",
    "Invoice",
    # Knowledge Base
    "KBArticle",
    "KBArticleQuality",
    "KBQualityReport",
    "KBUsage",
    "Lead",
    "LinkCheckResult",
    "Message",
    "NLQuery",
    "OAuthProvider",
    # Tier 3: Security
    "PIIDetection",
    "Payment",
    "PenetrationTest",
    "PolicyRule",
    "PredictionExplanation",
    "Quote",
    # Tier 3: QA Metrics
    "ResponseQualityCheck",
    "SLACompliance",
    "SalesActivity",
    "ScheduledTask",
    "SecurityIncident",
    "SensitivityViolation",
    # Subscription & billing
    "Subscription",
    "TimestampMixin",
    "UsageEvent",
    # Authentication & authorization
    "User",
    "UserRole",
    "UserStatus",
    "VulnerabilityScan",
    # Workflow automation
    "Workflow",
    "WorkflowExecution",
]
