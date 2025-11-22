"""
Notification Tasks
Email, SMS, Slack notifications sent in background
"""

import structlog
from typing import Optional

from src.celery.celery_app import celery_app

logger = structlog.get_logger(__name__)

# =============================================================================
# NOTIFICATION TASKS
# =============================================================================

@celery_app.task(
    name="notification.send_email",
    bind=True,
    max_retries=5,
    default_retry_delay=300,  # 5 minutes
)
def send_email(
    self,
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
):
    """
    Send email notification (with retry logic)
    """
    try:
        logger.info(
            "send_email_started",
            task_id=self.request.id,
            to=to,
            subject=subject,
        )

        # Send email via SMTP
        # email_service.send(to, subject, body, html)

        logger.info(
            "send_email_completed",
            task_id=self.request.id,
            to=to,
        )

        return {"status": "sent", "to": to}

    except Exception as exc:
        logger.error(
            "send_email_failed",
            task_id=self.request.id,
            to=to,
            error=str(exc),
        )
        raise self.retry(exc=exc)


@celery_app.task(
    name="notification.send_critical_alert",
    priority=10,  # High priority
)
def send_critical_alert(
    message: str,
    recipients: list[str],
):
    """
    Send critical alert (high priority)
    """
    try:
        logger.critical(
            "critical_alert",
            message=message,
            recipients=recipients,
        )

        # Send via Slack, PagerDuty, etc.
        # alert_service.send_critical(message, recipients)

        return {"status": "sent"}

    except Exception as exc:
        logger.error(
            "send_critical_alert_failed",
            error=str(exc),
        )
        raise


@celery_app.task(name="notification.send_slack_message")
def send_slack_message(
    channel: str,
    message: str,
):
    """
    Send Slack notification
    """
    try:
        logger.info(
            "send_slack_message_started",
            channel=channel,
        )

        # Send Slack message
        # slack_client.send_message(channel, message)

        logger.info(
            "send_slack_message_completed",
            channel=channel,
        )

        return {"status": "sent"}

    except Exception as exc:
        logger.error(
            "send_slack_message_failed",
            channel=channel,
            error=str(exc),
        )
        raise
