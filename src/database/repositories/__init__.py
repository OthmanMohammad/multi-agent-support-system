"""
Repository package - Data access layer
"""
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.api_key_repository import APIKeyRepository
from src.database.repositories.customer_repository import CustomerRepository
from src.database.repositories.conversation_repository import ConversationRepository
from src.database.repositories.message_repository import MessageRepository
from src.database.repositories.agent_performance_repository import AgentPerformanceRepository
from src.database.repositories.customer_health_repository import (
    CustomerHealthEventRepository,
    CustomerSegmentRepository,
    CustomerNoteRepository,
    CustomerContactRepository,
    CustomerIntegrationRepository,
)
from src.database.repositories.subscription_repository import (
    SubscriptionRepository,
    InvoiceRepository,
    PaymentRepository,
    UsageEventRepository,
    CreditRepository,
)
from src.database.repositories.sales_repository import (
    EmployeeRepository,
    LeadRepository,
    DealRepository,
    SalesActivityRepository,
    QuoteRepository,
)
from src.database.repositories.analytics_repository import (
    ConversationAnalyticsRepository,
    FeatureUsageRepository,
    ABTestRepository,
)
from src.database.repositories.workflow_repository import (
    WorkflowRepository,
    WorkflowExecutionRepository,
    ScheduledTaskRepository,
)
from src.database.repositories.agent_handoff_repository import (
    AgentHandoffRepository,
    AgentCollaborationRepository,
    ConversationTagRepository,
)
from src.database.repositories.audit_log_repository import AuditLogRepository

__all__ = [
    # Authentication
    "UserRepository",
    "APIKeyRepository",
    # Core
    "CustomerRepository",
    "ConversationRepository",
    "MessageRepository",
    "AgentPerformanceRepository",
    # Customer Health
    "CustomerHealthEventRepository",
    "CustomerSegmentRepository",
    "CustomerNoteRepository",
    "CustomerContactRepository",
    "CustomerIntegrationRepository",
    # Subscription & Billing
    "SubscriptionRepository",
    "InvoiceRepository",
    "PaymentRepository",
    "UsageEventRepository",
    "CreditRepository",
    # Sales
    "EmployeeRepository",
    "LeadRepository",
    "DealRepository",
    "SalesActivityRepository",
    "QuoteRepository",
    # Analytics
    "ConversationAnalyticsRepository",
    "FeatureUsageRepository",
    "ABTestRepository",
    # Workflow
    "WorkflowRepository",
    "WorkflowExecutionRepository",
    "ScheduledTaskRepository",
    # Agent Handoff
    "AgentHandoffRepository",
    "AgentCollaborationRepository",
    "ConversationTagRepository",
    # Audit
    "AuditLogRepository",
]