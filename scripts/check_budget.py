#!/usr/bin/env python3
"""
Budget Monitoring Script

Checks LLM cost budget and sends alerts if thresholds are exceeded.

Alert levels:
- 75% = Caution (warning log)
- 90% = Warning (error log + optional notification)
- 100% = Critical (error log + optional notification)

Should be run periodically via cron job (e.g., every 6 hours):
    0 */6 * * * cd ~/multi-agent-system && python scripts/check_budget.py

Vast.ai GPU Orchestration
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.cost_tracking import cost_tracker
from src.utils.logging.setup import setup_logging, get_logger
from src.core.config import get_settings

# Initialize logging
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def send_alert(alert_level: str, message: str, details: dict):
    """
    Send budget alert notification.

    Can be extended to send Slack/email notifications.

    Args:
        alert_level: Alert level (caution, warning, critical)
        message: Alert message
        details: Budget details dictionary
    """
    # Log alert
    if alert_level == "critical":
        logger.error(
            "budget_alert_critical",
            alert_level=alert_level,
            message=message,
            **details,
        )
    elif alert_level == "warning":
        logger.error(
            "budget_alert_warning",
            alert_level=alert_level,
            message=message,
            **details,
        )
    else:
        logger.warning(
            "budget_alert_caution",
            alert_level=alert_level,
            message=message,
            **details,
        )

    # TODO: Add Slack webhook notification
    # if settings.notification.slack_enabled and settings.notification.slack_webhook_url:
    #     send_slack_notification(alert_level, message, details)

    # TODO: Add email notification
    # if settings.notification.email_enabled:
    #     send_email_notification(alert_level, message, details)


def main():
    """
    Check budget status and send alerts if needed.
    """
    logger.info(
        "budget_check_started",
        timestamp=datetime.utcnow().isoformat(),
        script="check_budget.py",
    )

    try:
        # Get budget status
        status = cost_tracker.get_budget_status()
        breakdown = cost_tracker.get_breakdown()

        logger.info(
            "budget_check_status",
            alert_level=status["alert_level"],
            total_spent=status["total_spent"],
            budget_limit=status["budget_limit"],
            percent_used=status["percent_used"],
            remaining=status["remaining"],
        )

        # Check alert level and send notifications
        if status["alert_level"] == "critical":
            send_alert(
                "critical",
                f"⚠️  CRITICAL: Budget exceeded! ${status['total_spent']:.2f} / ${status['budget_limit']:.2f}",
                {
                    "total_spent": status["total_spent"],
                    "budget_limit": status["budget_limit"],
                    "percent_used": status["percent_used"],
                    "anthropic_cost": breakdown["anthropic"],
                    "vllm_cost": breakdown["vllm"],
                },
            )

            # Exit with error code to trigger alerts
            sys.exit(1)

        elif status["alert_level"] == "warning":
            send_alert(
                "warning",
                f"⚠️  WARNING: Budget at {status['percent_used']:.1f}% - ${status['total_spent']:.2f} / ${status['budget_limit']:.2f}",
                {
                    "total_spent": status["total_spent"],
                    "budget_limit": status["budget_limit"],
                    "percent_used": status["percent_used"],
                    "remaining": status["remaining"],
                    "anthropic_cost": breakdown["anthropic"],
                    "vllm_cost": breakdown["vllm"],
                },
            )

            # Exit with warning code
            sys.exit(1)

        elif status["alert_level"] == "caution":
            send_alert(
                "caution",
                f"⚠️  CAUTION: Budget at {status['percent_used']:.1f}% - ${status['total_spent']:.2f} / ${status['budget_limit']:.2f}",
                {
                    "total_spent": status["total_spent"],
                    "budget_limit": status["budget_limit"],
                    "percent_used": status["percent_used"],
                    "remaining": status["remaining"],
                },
            )

            # Exit successfully (just a warning)
            sys.exit(0)

        else:
            # Budget OK
            logger.info(
                "budget_check_ok",
                message=f"✅ Budget OK: ${status['total_spent']:.2f} / ${status['budget_limit']:.2f} ({status['percent_used']:.1f}%)",
                total_spent=status["total_spent"],
                budget_limit=status["budget_limit"],
                percent_used=status["percent_used"],
                remaining=status["remaining"],
            )

            # Exit successfully
            sys.exit(0)

    except Exception as e:
        logger.error(
            "budget_check_failed",
            error=str(e),
            exc_info=True,
            timestamp=datetime.utcnow().isoformat(),
        )

        # Exit with error code
        sys.exit(1)


if __name__ == "__main__":
    main()
