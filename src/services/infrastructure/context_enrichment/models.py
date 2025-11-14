"""
Data models for context enrichment.

This module defines the data structures used throughout the context enrichment system,
including customer intelligence, engagement metrics, support history, and enriched context.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ChurnRiskLevel(Enum):
    """Churn risk classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealthScoreLevel(Enum):
    """Health score classification"""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class CustomerIntelligence:
    """
    Customer profile and key business metrics.

    This represents the core customer data including plan, revenue,
    health indicators, and tenure information.
    """
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[int] = None
    plan: str = "free"
    mrr: float = 0.0
    ltv: float = 0.0
    health_score: int = 50
    churn_risk: float = 0.5
    nps_score: Optional[int] = None
    customer_since: Optional[datetime] = None

    def get_churn_risk_level(self) -> ChurnRiskLevel:
        """Get churn risk classification"""
        if self.churn_risk < 0.3:
            return ChurnRiskLevel.LOW
        elif self.churn_risk < 0.6:
            return ChurnRiskLevel.MEDIUM
        elif self.churn_risk < 0.8:
            return ChurnRiskLevel.HIGH
        else:
            return ChurnRiskLevel.CRITICAL

    def get_health_score_level(self) -> HealthScoreLevel:
        """Get health score classification"""
        if self.health_score >= 80:
            return HealthScoreLevel.EXCELLENT
        elif self.health_score >= 60:
            return HealthScoreLevel.GOOD
        elif self.health_score >= 40:
            return HealthScoreLevel.FAIR
        else:
            return HealthScoreLevel.POOR


@dataclass
class EngagementMetrics:
    """
    Customer engagement and product usage metrics.

    Tracks how actively the customer is using the product,
    which features they use, and their engagement patterns.
    """
    last_login: Optional[datetime] = None
    login_count_30d: int = 0
    avg_session_duration_minutes: float = 0.0
    feature_adoption_score: float = 0.0
    most_used_features: List[str] = field(default_factory=list)
    unused_features: List[str] = field(default_factory=list)
    days_since_last_login: Optional[int] = None


@dataclass
class SupportHistory:
    """
    Support interaction history and satisfaction metrics.

    Provides context on past support interactions, resolution times,
    and customer satisfaction.
    """
    total_conversations: int = 0
    avg_resolution_time_minutes: float = 0.0
    most_common_issues: List[str] = field(default_factory=list)
    last_conversation: Optional[datetime] = None
    last_csat: Optional[int] = None
    avg_csat: Optional[float] = None
    escalation_count: int = 0
    open_tickets: int = 0


@dataclass
class SubscriptionDetails:
    """
    Current subscription and billing information.

    Details about the customer's subscription status, seats,
    billing cycle, and upcoming renewals.
    """
    seats_total: int = 1
    seats_used: int = 1
    billing_cycle: str = "monthly"
    current_period_end: Optional[datetime] = None
    days_to_renewal: Optional[int] = None
    cancel_at_period_end: bool = False
    trial_status: Optional[str] = None
    payment_method_valid: bool = True


@dataclass
class AccountHealth:
    """
    Account health indicators and flags.

    Identifies positive opportunities (green flags) and
    potential issues (red/yellow flags) for the account.
    """
    red_flags: List[str] = field(default_factory=list)
    yellow_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    recent_health_changes: List[Dict[str, Any]] = field(default_factory=list)

    def has_critical_issues(self) -> bool:
        """Check if account has critical issues"""
        return len(self.red_flags) > 0

    def has_opportunities(self) -> bool:
        """Check if account has expansion opportunities"""
        return len(self.green_flags) > 0


@dataclass
class CompanyEnrichment:
    """
    External company data (from third-party APIs).

    Optional enrichment from services like Clearbit, Crunchbase, etc.
    This is only populated if external API integrations are enabled.
    """
    company_size: Optional[int] = None
    industry: Optional[str] = None
    estimated_revenue: Optional[float] = None
    tech_stack: List[str] = field(default_factory=list)
    funding_stage: Optional[str] = None
    total_funding: Optional[float] = None


@dataclass
class ProductStatus:
    """
    Real-time product status information.

    Current system status, incidents, and recent deployments
    that might affect customer experience.
    """
    status: str = "operational"
    active_incidents: List[Dict[str, Any]] = field(default_factory=list)
    recent_deployments: List[Dict[str, Any]] = field(default_factory=list)

    def has_incidents(self) -> bool:
        """Check if there are active incidents"""
        return len(self.active_incidents) > 0


@dataclass
class EnrichedContext:
    """
    Complete enriched context combining all data sources.

    This is the main data structure returned by the context enrichment service.
    It combines internal customer data, engagement metrics, support history,
    and optional external enrichment.
    """
    # Internal context (always populated)
    customer_intelligence: CustomerIntelligence
    engagement_metrics: EngagementMetrics
    support_history: SupportHistory
    subscription_details: SubscriptionDetails
    account_health: AccountHealth

    # External context (optional)
    company_enrichment: Optional[CompanyEnrichment] = None

    # Real-time context
    product_status: ProductStatus = field(default_factory=ProductStatus)

    # Metadata
    enriched_at: datetime = field(default_factory=datetime.utcnow)
    cache_hit: bool = False
    enrichment_latency_ms: float = 0.0
    providers_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    def to_prompt_context(self) -> str:
        """
        Convert to formatted string for LLM prompt injection.

        This creates a human-readable context summary that can be
        injected into agent system prompts.
        """
        ci = self.customer_intelligence
        em = self.engagement_metrics
        sh = self.support_history
        sd = self.subscription_details
        ah = self.account_health

        # Churn risk label
        churn_risk_level = ci.get_churn_risk_level()
        churn_label = churn_risk_level.value.title()

        # Health score label
        health_level = ci.get_health_score_level()
        health_label = health_level.value.title()

        # Build context string
        context = f"""
<customer_context>
Company: {ci.company_name}
Industry: {ci.industry or 'Unknown'}
Plan: {ci.plan.upper()}
MRR: ${ci.mrr:,.2f}
Health Score: {ci.health_score}/100 ({health_label})
Churn Risk: {churn_label} ({ci.churn_risk:.0%})
"""

        # Add customer tenure if available
        if ci.customer_since:
            days_as_customer = (datetime.utcnow() - ci.customer_since).days
            context += f"Customer Since: {ci.customer_since.strftime('%Y-%m-%d')} ({days_as_customer} days)\n"

        # Engagement section
        context += f"""
Recent Activity:
- Last login: {em.last_login.strftime('%Y-%m-%d %H:%M') if em.last_login else 'Never'}
- Login frequency: {em.login_count_30d} times (last 30 days)
"""
        if em.most_used_features:
            context += f"- Most used features: {', '.join(em.most_used_features[:3])}\n"
        if em.days_since_last_login is not None:
            context += f"- Days since last login: {em.days_since_last_login}\n"

        # Support history section
        context += f"""
Support History:
- Total conversations: {sh.total_conversations}
"""
        if sh.avg_resolution_time_minutes > 0:
            context += f"- Average resolution time: {sh.avg_resolution_time_minutes:.1f} minutes\n"
        if sh.last_csat:
            context += f"- Last CSAT: {sh.last_csat}/5\n"
        if sh.avg_csat:
            context += f"- Average CSAT: {sh.avg_csat:.1f}/5\n"
        if sh.open_tickets > 0:
            context += f"- Open tickets: {sh.open_tickets}\n"

        # Subscription section
        context += f"""
Subscription:
- Plan: {ci.plan.upper()}
- Seats: {sd.seats_used}/{sd.seats_total}
"""
        if sd.days_to_renewal is not None:
            context += f"- Renewal: {sd.days_to_renewal} days\n"
        if sd.cancel_at_period_end:
            context += f"- ⚠️ Scheduled for cancellation at period end\n"
        if not sd.payment_method_valid:
            context += f"- ⚠️ Payment method invalid\n"

        # Add red flags if any
        if ah.red_flags:
            context += f"\n🚨 RED FLAGS:\n"
            for flag in ah.red_flags:
                context += f"- {flag}\n"

        # Add yellow flags if any
        if ah.yellow_flags:
            context += f"\n⚠️ YELLOW FLAGS:\n"
            for flag in ah.yellow_flags:
                context += f"- {flag}\n"

        # Add green flags (opportunities) if any
        if ah.green_flags:
            context += f"\n✅ OPPORTUNITIES:\n"
            for flag in ah.green_flags:
                context += f"- {flag}\n"

        # Add product status if there are incidents
        if self.product_status.has_incidents():
            context += f"\n⚠️ ACTIVE INCIDENTS:\n"
            for incident in self.product_status.active_incidents:
                context += f"- {incident.get('title', 'Unknown incident')}\n"

        context += "</customer_context>"
        return context

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of key metrics"""
        return {
            "company_name": self.customer_intelligence.company_name,
            "plan": self.customer_intelligence.plan,
            "health_score": self.customer_intelligence.health_score,
            "churn_risk": self.customer_intelligence.churn_risk,
            "churn_risk_level": self.customer_intelligence.get_churn_risk_level().value,
            "login_count_30d": self.engagement_metrics.login_count_30d,
            "open_tickets": self.support_history.open_tickets,
            "days_to_renewal": self.subscription_details.days_to_renewal,
            "has_critical_issues": self.account_health.has_critical_issues(),
            "has_opportunities": self.account_health.has_opportunities(),
            "enrichment_latency_ms": self.enrichment_latency_ms,
            "cache_hit": self.cache_hit
        }
