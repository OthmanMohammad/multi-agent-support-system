"""
Account health provider.

Analyzes aggregated data from other providers to identify health indicators and flags.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider


class AccountHealthProvider(BaseContextProvider):
    """
    Provides account health analysis and flags.

    Analyzes data from other providers to identify:
    - Red flags (critical issues)
    - Yellow flags (warnings)
    - Green flags (opportunities)
    - Recent health changes

    This provider is special - it aggregates data from other providers
    instead of querying the database directly.
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze account health and return flags.

        This provider receives enriched context from other providers
        via kwargs and performs analysis.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            **kwargs: Should contain data from other providers:
                - customer_intelligence
                - engagement_metrics
                - support_history
                - subscription_details

        Returns:
            Account health flags and indicators
        """
        self.logger.debug("analyzing_account_health", customer_id=customer_id)

        # Extract data from other providers
        customer_intel = kwargs.get('customer_intelligence', {})
        engagement = kwargs.get('engagement_metrics', {})
        support = kwargs.get('support_history', {})
        subscription = kwargs.get('subscription_details', {})

        red_flags: List[str] = []
        yellow_flags: List[str] = []
        green_flags: List[str] = []
        recent_changes: List[Dict[str, Any]] = []

        # Analyze for RED FLAGS (critical issues)

        # Engagement red flags
        days_since_login = engagement.get('days_since_last_login')
        if days_since_login and days_since_login > 30:
            red_flags.append(f"No login activity in {days_since_login} days")

        # Subscription red flags
        sub_data = subscription.get('subscription', {})
        if sub_data.get('cancel_at_period_end'):
            red_flags.append("Scheduled for cancellation at period end")

        payment_health = subscription.get('payment_health', {})
        if not payment_health.get('payment_method_valid'):
            red_flags.append("Payment method declined or invalid")

        if payment_health.get('failed_payments_90d', 0) >= 3:
            red_flags.append(f"{payment_health['failed_payments_90d']} failed payments in last 90 days")

        if payment_health.get('overdue_invoices', 0) > 0:
            red_flags.append(f"{payment_health['overdue_invoices']} overdue invoices")

        # Support red flags
        if support.get('open_tickets', 0) >= 3:
            red_flags.append(f"{support['open_tickets']} open support tickets")

        avg_csat = support.get('avg_csat')
        if avg_csat and avg_csat < 3.0:
            red_flags.append(f"Low CSAT score: {avg_csat:.1f}/5.0")

        # Churn risk
        churn_risk = customer_intel.get('churn_risk', 0)
        if churn_risk > 0.7:
            red_flags.append(f"High churn risk: {churn_risk:.0%}")

        # Analyze for YELLOW FLAGS (warnings)

        # Engagement warnings
        login_count = engagement.get('login_count_30d', 0)
        if 0 < login_count < 5:
            yellow_flags.append(f"Low login frequency: {login_count} logins in 30 days")

        feature_adoption = engagement.get('feature_adoption_score', 0)
        if feature_adoption < 0.3:
            yellow_flags.append(f"Low feature adoption: {feature_adoption:.0%}")

        # Subscription warnings
        if sub_data.get('status') == 'trialing':
            trial_status = subscription.get('billing', {}).get('trial_status')
            if trial_status == 'active':
                yellow_flags.append("In trial period - requires conversion")

        days_to_renewal = subscription.get('days_to_renewal')
        if days_to_renewal and days_to_renewal <= 30:
            yellow_flags.append(f"Renewal approaching: {days_to_renewal} days")

        seat_utilization = sub_data.get('seat_utilization', 0)
        if seat_utilization >= 90:
            yellow_flags.append(f"High seat utilization: {seat_utilization:.0f}%")

        # Support warnings
        escalation_count = support.get('escalation_count', 0)
        if escalation_count >= 2:
            yellow_flags.append(f"{escalation_count} escalations in conversation history")

        if avg_csat and 3.0 <= avg_csat < 3.5:
            yellow_flags.append(f"Moderate CSAT score: {avg_csat:.1f}/5.0")

        # Health score warnings
        health_score = customer_intel.get('health_score', 50)
        if 30 <= health_score < 60:
            yellow_flags.append(f"Declining health score: {health_score}/100")

        if 0.5 <= churn_risk <= 0.7:
            yellow_flags.append(f"Moderate churn risk: {churn_risk:.0%}")

        # Analyze for GREEN FLAGS (opportunities)

        # Engagement opportunities
        if login_count > 20:
            green_flags.append(f"Highly engaged: {login_count} logins in 30 days")

        if feature_adoption > 0.7:
            green_flags.append(f"Strong feature adoption: {feature_adoption:.0%}")

        # Revenue opportunities
        mrr = customer_intel.get('mrr', 0)
        if seat_utilization >= 80 and mrr > 0:
            green_flags.append("High seat usage - expansion opportunity")

        unused_features = engagement.get('unused_features', [])
        if mrr > 0 and unused_features:
            green_flags.append(f"Not using {len(unused_features)} premium features - upsell potential")

        # Support opportunities
        if avg_csat and avg_csat >= 4.5:
            green_flags.append(f"Excellent CSAT: {avg_csat:.1f}/5.0 - request referral")

        # Health opportunities
        if health_score >= 80:
            green_flags.append(f"Excellent health score: {health_score}/100")

        health_trend = customer_intel.get('health_trend', 'stable')
        if health_trend == 'improving':
            green_flags.append("Health score improving")

        if churn_risk < 0.3:
            green_flags.append(f"Low churn risk: {churn_risk:.0%}")

        # Recent health changes (based on trends)
        if health_trend == 'declining':
            recent_changes.append({
                "timestamp": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
                "change": "Health score decreased",
                "reason": red_flags[0] if red_flags else yellow_flags[0] if yellow_flags else "Unknown"
            })
        elif health_trend == 'improving':
            recent_changes.append({
                "timestamp": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
                "change": "Health score increased",
                "reason": green_flags[0] if green_flags else "Improved engagement"
            })

        return {
            "red_flags": red_flags,
            "yellow_flags": yellow_flags,
            "green_flags": green_flags,
            "recent_health_changes": recent_changes,
        }
