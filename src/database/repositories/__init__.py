"""
Repository package - Data access layer
"""

from src.database.repositories.agent_handoff_repository import (
    AgentCollaborationRepository,
    AgentHandoffRepository,
    ConversationTagRepository,
)
from src.database.repositories.agent_performance_repository import AgentPerformanceRepository
from src.database.repositories.analytics_repository import (
    ABTestRepository,
    ConversationAnalyticsRepository,
    FeatureUsageRepository,
)
from src.database.repositories.api_key_repository import APIKeyRepository
from src.database.repositories.audit_log_repository import AuditLogRepository
from src.database.repositories.conversation_repository import ConversationRepository
from src.database.repositories.customer_health_repository import (
    CustomerContactRepository,
    CustomerHealthEventRepository,
    CustomerIntegrationRepository,
    CustomerNoteRepository,
    CustomerSegmentRepository,
)
from src.database.repositories.customer_repository import CustomerRepository
from src.database.repositories.message_repository import MessageRepository
from src.database.repositories.sales_repository import (
    DealRepository,
    EmployeeRepository,
    LeadRepository,
    QuoteRepository,
    SalesActivityRepository,
)
from src.database.repositories.subscription_repository import (
    CreditRepository,
    InvoiceRepository,
    PaymentRepository,
    SubscriptionRepository,
    UsageEventRepository,
)
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.workflow_repository import (
    ScheduledTaskRepository,
    WorkflowExecutionRepository,
    WorkflowRepository,
)

__all__ = [
    "ABTestRepository",
    "APIKeyRepository",
    "AgentCollaborationRepository",
    # Agent Handoff
    "AgentHandoffRepository",
    "AgentPerformanceRepository",
    # Audit
    "AuditLogRepository",
    # Analytics
    "ConversationAnalyticsRepository",
    "ConversationRepository",
    "ConversationTagRepository",
    "CreditRepository",
    "CustomerContactRepository",
    # Customer Health
    "CustomerHealthEventRepository",
    "CustomerIntegrationRepository",
    "CustomerNoteRepository",
    # Core
    "CustomerRepository",
    "CustomerSegmentRepository",
    "DealRepository",
    # Sales
    "EmployeeRepository",
    "FeatureUsageRepository",
    "InvoiceRepository",
    "LeadRepository",
    "MessageRepository",
    "PaymentRepository",
    "QuoteRepository",
    "SalesActivityRepository",
    "ScheduledTaskRepository",
    # Subscription & Billing
    "SubscriptionRepository",
    "UsageEventRepository",
    # Authentication
    "UserRepository",
    "WorkflowExecutionRepository",
    # Workflow
    "WorkflowRepository",
]
