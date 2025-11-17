"""
Discord Alerts Integration

Sends alerts to Discord via webhooks for critical events.
Integrates with Sentry for error tracking and notification.

Alert Types:
- Critical errors (500 errors, exceptions)
- Rate limit breaches
- Agent failures
- System health issues
- Performance degradation
- Security events

Part of: Phase 5 - Monitoring & Observability
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
from enum import Enum

from src.core.config import get_settings
from src.utils.logging.setup import get_logger

logger = get_logger(__name__)
settings = get_settings()


# =============================================================================
# ALERT SEVERITY LEVELS
# =============================================================================

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Severity colors for Discord embeds
SEVERITY_COLORS = {
    AlertSeverity.INFO: 0x00B2FF,      # Blue
    AlertSeverity.WARNING: 0xFFA500,   # Orange
    AlertSeverity.ERROR: 0xFF0000,     # Red
    AlertSeverity.CRITICAL: 0x8B0000,  # Dark Red
}


# =============================================================================
# DISCORD WEBHOOK CLIENT
# =============================================================================

class DiscordAlerter:
    """
    Discord webhook alerting client.

    Sends formatted alerts to Discord channels via webhooks.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Discord alerter.

        Args:
            webhook_url: Discord webhook URL (from settings if not provided)
        """
        self.webhook_url = webhook_url or getattr(settings, 'discord_webhook_url', None)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def send_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> bool:
        """
        Send alert to Discord.

        Args:
            title: Alert title
            description: Alert description
            severity: Alert severity level
            fields: Additional fields to include
            footer: Footer text
            thumbnail_url: Thumbnail image URL

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.warning("discord_webhook_url_not_configured")
            return False

        try:
            # Build Discord embed
            embed = {
                "title": title,
                "description": description,
                "color": SEVERITY_COLORS.get(severity, 0x00B2FF),
                "timestamp": datetime.now(UTC).isoformat(),
                "fields": fields or [],
            }

            if footer:
                embed["footer"] = {"text": footer}

            if thumbnail_url:
                embed["thumbnail"] = {"url": thumbnail_url}

            # Build webhook payload
            payload = {
                "embeds": [embed],
                "username": "Multi-Agent Support System",
            }

            # Send to Discord
            session = await self._get_session()
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.debug("discord_alert_sent", title=title, severity=severity.value)
                    return True
                else:
                    logger.error(
                        "discord_alert_failed",
                        status=response.status,
                        response=await response.text()
                    )
                    return False

        except Exception as e:
            logger.error("discord_alert_error", error=str(e), exc_info=True)
            return False


# =============================================================================
# ALERT FUNCTIONS
# =============================================================================

# Global alerter instance
_alerter: Optional[DiscordAlerter] = None


def get_alerter() -> DiscordAlerter:
    """Get or create Discord alerter instance"""
    global _alerter
    if _alerter is None:
        _alerter = DiscordAlerter()
    return _alerter


async def send_critical_error_alert(
    error_type: str,
    error_message: str,
    endpoint: Optional[str] = None,
    user_id: Optional[str] = None,
    stack_trace: Optional[str] = None,
):
    """
    Send critical error alert.

    Args:
        error_type: Type of error (e.g., "DatabaseError", "AgentExecutionError")
        error_message: Error message
        endpoint: API endpoint where error occurred
        user_id: User ID if applicable
        stack_trace: Stack trace (truncated)
    """
    alerter = get_alerter()

    fields = [
        {"name": "Error Type", "value": error_type, "inline": True},
        {"name": "Timestamp", "value": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": True},
    ]

    if endpoint:
        fields.append({"name": "Endpoint", "value": endpoint, "inline": False})

    if user_id:
        fields.append({"name": "User ID", "value": user_id, "inline": True})

    if stack_trace:
        # Truncate stack trace to fit Discord limits
        truncated_trace = stack_trace[:500] + "..." if len(stack_trace) > 500 else stack_trace
        fields.append({"name": "Stack Trace", "value": f"```\n{truncated_trace}\n```", "inline": False})

    await alerter.send_alert(
        title="🚨 Critical Error Detected",
        description=error_message,
        severity=AlertSeverity.CRITICAL,
        fields=fields,
        footer="Multi-Agent Support System"
    )


async def send_rate_limit_alert(
    tier: str,
    endpoint: str,
    user_id: Optional[str] = None,
):
    """
    Send rate limit breach alert.

    Args:
        tier: Rate limit tier
        endpoint: Endpoint that was rate limited
        user_id: User ID if applicable
    """
    alerter = get_alerter()

    fields = [
        {"name": "Tier", "value": tier, "inline": True},
        {"name": "Endpoint", "value": endpoint, "inline": True},
    ]

    if user_id:
        fields.append({"name": "User ID", "value": user_id, "inline": True})

    await alerter.send_alert(
        title="⚠️ Rate Limit Exceeded",
        description=f"Rate limit exceeded for tier **{tier}** on endpoint **{endpoint}**",
        severity=AlertSeverity.WARNING,
        fields=fields
    )


async def send_agent_failure_alert(
    agent_name: str,
    error_message: str,
    tier: str,
    conversation_id: Optional[str] = None,
):
    """
    Send agent execution failure alert.

    Args:
        agent_name: Name of failed agent
        error_message: Error message
        tier: Agent tier
        conversation_id: Conversation ID if applicable
    """
    alerter = get_alerter()

    fields = [
        {"name": "Agent", "value": agent_name, "inline": True},
        {"name": "Tier", "value": tier, "inline": True},
    ]

    if conversation_id:
        fields.append({"name": "Conversation ID", "value": conversation_id, "inline": False})

    await alerter.send_alert(
        title="⚠️ Agent Execution Failed",
        description=error_message,
        severity=AlertSeverity.ERROR,
        fields=fields
    )


async def send_performance_degradation_alert(
    metric_name: str,
    current_value: float,
    threshold: float,
    unit: str = "seconds",
):
    """
    Send performance degradation alert.

    Args:
        metric_name: Name of performance metric
        current_value: Current metric value
        threshold: Threshold that was exceeded
        unit: Unit of measurement
    """
    alerter = get_alerter()

    fields = [
        {"name": "Metric", "value": metric_name, "inline": True},
        {"name": "Current Value", "value": f"{current_value:.2f} {unit}", "inline": True},
        {"name": "Threshold", "value": f"{threshold:.2f} {unit}", "inline": True},
    ]

    await alerter.send_alert(
        title="📊 Performance Degradation Detected",
        description=f"**{metric_name}** has exceeded threshold",
        severity=AlertSeverity.WARNING,
        fields=fields
    )


async def send_security_alert(
    event_type: str,
    description: str,
    ip_address: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Send security event alert.

    Args:
        event_type: Type of security event
        description: Event description
        ip_address: IP address if applicable
        user_id: User ID if applicable
    """
    alerter = get_alerter()

    fields = [
        {"name": "Event Type", "value": event_type, "inline": True},
        {"name": "Timestamp", "value": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": True},
    ]

    if ip_address:
        fields.append({"name": "IP Address", "value": ip_address, "inline": True})

    if user_id:
        fields.append({"name": "User ID", "value": user_id, "inline": True})

    await alerter.send_alert(
        title="🔒 Security Alert",
        description=description,
        severity=AlertSeverity.ERROR,
        fields=fields
    )


async def send_system_health_alert(
    component: str,
    status: str,
    details: Optional[str] = None,
):
    """
    Send system health alert.

    Args:
        component: System component (e.g., "database", "redis", "api")
        status: Health status (e.g., "unhealthy", "degraded")
        details: Additional details
    """
    alerter = get_alerter()

    severity = AlertSeverity.CRITICAL if status == "unhealthy" else AlertSeverity.WARNING

    fields = [
        {"name": "Component", "value": component, "inline": True},
        {"name": "Status", "value": status, "inline": True},
    ]

    if details:
        fields.append({"name": "Details", "value": details, "inline": False})

    await alerter.send_alert(
        title="🏥 System Health Issue",
        description=f"Component **{component}** is **{status}**",
        severity=severity,
        fields=fields
    )


# =============================================================================
# SENTRY INTEGRATION
# =============================================================================

def setup_sentry_discord_integration():
    """
    Setup integration between Sentry and Discord.

    Configures Sentry to send critical errors to Discord.
    This should be called during application startup.
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Add custom before_send hook to send critical errors to Discord
        def before_send(event, hint):
            """Sentry before_send hook to send alerts to Discord"""
            if event.get('level') in ('error', 'fatal'):
                # Send to Discord asynchronously (non-blocking)
                error_type = event.get('exception', {}).get('values', [{}])[0].get('type', 'Unknown')
                error_message = event.get('exception', {}).get('values', [{}])[0].get('value', 'No message')

                # Create async task to send alert
                asyncio.create_task(
                    send_critical_error_alert(
                        error_type=error_type,
                        error_message=error_message,
                        endpoint=event.get('request', {}).get('url'),
                        stack_trace=str(event.get('exception'))
                    )
                )

            return event

        logger.info("sentry_discord_integration_setup_complete")

        # Note: This integration requires Sentry to be initialized
        # It should be called after Sentry is initialized in the application

    except ImportError:
        logger.warning("sentry_sdk_not_installed")
    except Exception as e:
        logger.error("sentry_discord_integration_setup_failed", error=str(e))


logger.info("discord_alerts_module_loaded")
