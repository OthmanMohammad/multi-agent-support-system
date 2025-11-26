"""
Agent type definitions and enums.

This module defines the type system for agents, including:
- Agent types and roles
- Agent capabilities
- Domain and intent classifications
"""

from enum import Enum


class AgentType(Enum):
    """Agent type classification"""

    ROUTER = "router"
    SPECIALIST = "specialist"
    COORDINATOR = "coordinator"
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    UTILITY = "utility"
    AUTOMATOR = "automator"
    SECURITY = "security"


class AgentCapability(Enum):
    """Agent capabilities for enabling specific features"""

    KB_SEARCH = "kb_search"
    CONTEXT_AWARE = "context_aware"
    MULTI_TURN = "multi_turn"
    COLLABORATION = "collaboration"
    EXTERNAL_API = "external_api"
    DATABASE_WRITE = "database_write"
    DATABASE_READ = "database_read"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ENTITY_EXTRACTION = "entity_extraction"


class Domain(Enum):
    """Top-level business domains"""

    SUPPORT = "support"
    SALES = "sales"
    CUSTOMER_SUCCESS = "customer_success"
    OPERATIONS = "operations"


class SupportIntent(Enum):
    """Support domain intents"""

    # Billing
    BILLING_UPGRADE = "billing_upgrade"
    BILLING_DOWNGRADE = "billing_downgrade"
    BILLING_REFUND = "billing_refund"
    BILLING_INVOICE = "billing_invoice"
    BILLING_PAYMENT = "billing_payment"
    BILLING_PRICING = "billing_pricing"

    # Technical
    TECHNICAL_BUG = "technical_bug"
    TECHNICAL_CRASH = "technical_crash"
    TECHNICAL_SYNC = "technical_sync"
    TECHNICAL_PERFORMANCE = "technical_performance"
    TECHNICAL_LOGIN = "technical_login"
    TECHNICAL_DATA_RECOVERY = "technical_data_recovery"
    TECHNICAL_COMPATIBILITY = "technical_compatibility"

    # Usage/Features
    FEATURE_CREATE = "feature_create"
    FEATURE_EDIT = "feature_edit"
    FEATURE_INVITE = "feature_invite"
    FEATURE_EXPORT = "feature_export"
    FEATURE_IMPORT = "feature_import"
    FEATURE_COLLABORATION = "feature_collaboration"

    # Integrations
    INTEGRATION_API = "integration_api"
    INTEGRATION_WEBHOOK = "integration_webhook"
    INTEGRATION_OAUTH = "integration_oauth"
    INTEGRATION_SDK = "integration_sdk"

    # Account Management
    ACCOUNT_LOGIN = "account_login"
    ACCOUNT_PROFILE = "account_profile"
    ACCOUNT_TEAM = "account_team"
    ACCOUNT_SECURITY = "account_security"
    ACCOUNT_SSO = "account_sso"
    ACCOUNT_PERMISSIONS = "account_permissions"
    ACCOUNT_DELETION = "account_deletion"
    ACCOUNT_COMPLIANCE = "account_compliance"

    # General
    GENERAL_INQUIRY = "general_inquiry"


class SalesIntent(Enum):
    """Sales domain intents"""

    QUALIFICATION = "qualification"
    DEMO_REQUEST = "demo_request"
    PRICING_INQUIRY = "pricing_inquiry"
    COMPETITOR_COMPARISON = "competitor_comparison"
    OBJECTION_HANDLING = "objection_handling"
    TRIAL_EXTENSION = "trial_extension"
    CONTRACT_NEGOTIATION = "contract_negotiation"


class CSIntent(Enum):
    """Customer success intents"""

    ONBOARDING = "onboarding"
    HEALTH_CHECK = "health_check"
    ADOPTION_GUIDANCE = "adoption_guidance"
    EXPANSION_OPPORTUNITY = "expansion_opportunity"
    RETENTION = "retention"
    FEEDBACK_COLLECTION = "feedback_collection"
    FEATURE_REQUEST = "feature_request"


class AgentRole(Enum):
    """Agent roles in the system"""

    META_ROUTER = "meta_router"
    DOMAIN_ROUTER = "domain_router"
    INTENT_CLASSIFIER = "intent_classifier"
    ENTITY_EXTRACTOR = "entity_extractor"
    SENTIMENT_ANALYZER = "sentiment_analyzer"
    COMPLEXITY_ASSESSOR = "complexity_assessor"
    SPECIALIST = "specialist"
    COORDINATOR = "coordinator"
    HANDOFF_MANAGER = "handoff_manager"
    ESCALATION_DECIDER = "escalation_decider"
    CONTEXT_INJECTOR = "context_injector"


class Tier(Enum):
    """Agent tier classification"""

    ESSENTIAL = "essential"
    REVENUE = "revenue"
    OPERATIONAL = "operational"
    ADVANCED = "advanced"


class ResponseType(Enum):
    """Types of responses agents can provide"""

    DIRECT_ANSWER = "direct_answer"
    ROUTING_DECISION = "routing_decision"
    ESCALATION = "escalation"
    COLLABORATION_REQUEST = "collaboration_request"
    CLARIFICATION_REQUEST = "clarification_request"
