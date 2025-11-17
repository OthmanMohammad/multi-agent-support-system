"""
Security context provider.

Fetches security posture, compliance status, and incident information from database.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.infrastructure.context_enrichment.providers.base_provider import BaseContextProvider
from src.database.models import AuditLog
from src.database.unit_of_work import UnitOfWork
from src.database.connection import get_db_session


class SecurityContextProvider(BaseContextProvider):
    """
    Provides security and compliance context.

    Fetches:
    - Security posture and status
    - Compliance status and certifications
    - Security incidents
    - Access patterns and anomalies
    - MFA and SSO status

    Note: This provider is opt-in (disabled by default) due to
    sensitivity of security data.
    """

    async def fetch(
        self,
        customer_id: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch security context from database.

        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID (optional)
            **kwargs: Additional parameters

        Returns:
            Security context data
        """
        self.logger.debug("fetching_security_context", customer_id=customer_id)

        try:
            cust_uuid = UUID(customer_id)
        except (ValueError, AttributeError):
            self.logger.error("invalid_customer_id", customer_id=customer_id)
            return self._get_fallback_data()

        session = kwargs.get("session")
        if session:
            return await self._fetch_with_session(cust_uuid, session)
        else:
            async for session in get_db_session():
                return await self._fetch_with_session(cust_uuid, session)

    async def _fetch_with_session(
        self,
        customer_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Fetch security context using provided session"""
        try:
            uow = UnitOfWork(session)

            # Fetch audit logs to analyze security events
            cutoff = datetime.now(UTC) - timedelta(days=90)
            audit_logs = await uow.audit_logs.find_by(customer_id=customer_id)

            # Filter to last 90 days
            recent_logs = [
                log for log in audit_logs
                if hasattr(log, 'created_at') and
                   log.created_at.replace(tzinfo=None) > cutoff
            ]

            # Analyze security events
            security_events = [
                log for log in recent_logs
                if hasattr(log, 'event_type') and
                   log.event_type in ['login_failed', 'unauthorized_access', 'permission_denied']
            ]

            # Count failed login attempts (last 24 hours)
            daily_cutoff = datetime.now(UTC) - timedelta(days=1)
            failed_logins_24h = sum(
                1 for log in security_events
                if (hasattr(log, 'event_type') and log.event_type == 'login_failed' and
                    hasattr(log, 'created_at') and
                    log.created_at.replace(tzinfo=None) > daily_cutoff)
            )

            # Check for unusual activity
            unusual_activity = failed_logins_24h > 10

            # Get customer metadata for security settings
            customer = await uow.customers.get_by_id(customer_id)
            metadata = customer.extra_metadata if customer and hasattr(customer, 'extra_metadata') else {}

            # Extract security settings
            mfa_enabled = metadata.get('mfa_enabled', False)
            sso_configured = metadata.get('sso_configured', False)
            ip_whitelist_enabled = metadata.get('ip_whitelist_enabled', False)

            # Security posture score (0-100)
            score = 100
            if not mfa_enabled:
                score -= 30
            if not sso_configured:
                score -= 20
            if unusual_activity:
                score -= 20
            if failed_logins_24h > 5:
                score -= 10

            # Determine compliance status
            compliance_score = metadata.get('compliance_score', 85)
            certifications = metadata.get('certifications', [])

            # Build incidents list
            incidents: List[Dict[str, Any]] = []
            open_incidents = 0

            if unusual_activity:
                incidents.append({
                    "severity": "medium",
                    "type": "unusual_login_attempts",
                    "description": f"{failed_logins_24h} failed login attempts in last 24 hours",
                    "status": "investigating",
                })
                open_incidents += 1

            # Severity breakdown
            severity_breakdown = {
                "critical": 0,
                "high": 0,
                "medium": 1 if unusual_activity else 0,
                "low": 0,
            }

            # Last audit/assessment
            last_audit = metadata.get('last_security_audit')
            if last_audit:
                try:
                    last_audit = datetime.fromisoformat(last_audit)
                except:
                    last_audit = None

            return {
                "security_posture": {
                    "status": "healthy" if score >= 80 else "needs_attention",
                    "score": score,
                    "last_audit": last_audit,
                    "compliance_score": compliance_score,
                    "certifications": certifications or ["SOC2"],
                },
                "incidents": {
                    "open_incidents": open_incidents,
                    "resolved_90d": len(security_events) - open_incidents,
                    "severity_breakdown": severity_breakdown,
                    "recent_incidents": incidents,
                },
                "access_patterns": {
                    "unusual_activity_detected": unusual_activity,
                    "failed_login_attempts_24h": failed_logins_24h,
                    "mfa_enabled": mfa_enabled,
                    "sso_configured": sso_configured,
                    "ip_whitelist_enabled": ip_whitelist_enabled,
                },
            }

        except Exception as e:
            self.logger.error(
                "fetch_failed",
                customer_id=str(customer_id),
                error=str(e),
                error_type=type(e).__name__
            )
            return self._get_fallback_data()

    def _get_fallback_data(self) -> Dict[str, Any]:
        """Get fallback data when query fails"""
        return {
            "security_posture": {
                "status": "unknown",
                "score": 0,
                "last_audit": None,
                "compliance_score": 0,
                "certifications": [],
            },
            "incidents": {
                "open_incidents": 0,
                "resolved_90d": 0,
                "severity_breakdown": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                },
                "recent_incidents": [],
            },
            "access_patterns": {
                "unusual_activity_detected": False,
                "failed_login_attempts_24h": 0,
                "mfa_enabled": False,
                "sso_configured": False,
                "ip_whitelist_enabled": False,
            },
        }
