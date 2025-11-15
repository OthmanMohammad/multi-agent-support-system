"""
Database models package
"""
# Base classes
from src.database.models.base import Base, BaseModel, TimestampMixin, AuditMixin

# Core models
from src.database.models.customer import Customer
from src.database.models.conversation import Conversation
from src.database.models.message import Message
from src.database.models.agent_performance import AgentPerformance

# Customer health & segmentation
from src.database.models.customer_health import (
    CustomerHealthEvent,
    CustomerSegment,
    CustomerNote,
    CustomerContact,
    CustomerIntegration,
)

# Agent collaboration
from src.database.models.agent_handoff import (
    AgentHandoff,
    AgentCollaboration,
    ConversationTag,
)

# Subscription & billing
from src.database.models.subscription import (
    Subscription,
    Invoice,
    Payment,
    UsageEvent,
    Credit,
)

# Sales & leads
from src.database.models.sales import (
    Employee,
    Lead,
    Deal,
    SalesActivity,
    Quote,
)

# Analytics
from src.database.models.analytics import (
    ConversationAnalytics,
    FeatureUsage,
    ABTest,
)

# Workflow automation
from src.database.models.workflow import (
    Workflow,
    WorkflowExecution,
    ScheduledTask,
)

# Security & compliance
from src.database.models.audit_log import AuditLog

# Knowledge Base
from src.database.models.kb_article import (
    KBArticle,
    KBUsage,
    KBQualityReport,
)

__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "TimestampMixin",
    "AuditMixin",
    # Core models
    "Customer",
    "Conversation",
    "Message",
    "AgentPerformance",
    # Customer health & segmentation
    "CustomerHealthEvent",
    "CustomerSegment",
    "CustomerNote",
    "CustomerContact",
    "CustomerIntegration",
    # Agent collaboration
    "AgentHandoff",
    "AgentCollaboration",
    "ConversationTag",
    # Subscription & billing
    "Subscription",
    "Invoice",
    "Payment",
    "UsageEvent",
    "Credit",
    # Sales & leads
    "Employee",
    "Lead",
    "Deal",
    "SalesActivity",
    "Quote",
    # Analytics
    "ConversationAnalytics",
    "FeatureUsage",
    "ABTest",
    # Workflow automation
    "Workflow",
    "WorkflowExecution",
    "ScheduledTask",
    # Security & compliance
    "AuditLog",
    # Knowledge Base
    "KBArticle",
    "KBUsage",
    "KBQualityReport",
]