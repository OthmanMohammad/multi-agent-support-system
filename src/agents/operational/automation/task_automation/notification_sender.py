"""
Notification Sender Agent - TASK-2205

Auto-sends notifications via Slack, SMS, push notifications, and webhooks
for important events and alerts.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("notification_sender", tier="operational", category="automation")
class NotificationSenderAgent(BaseAgent):
    """
    Notification Sender Agent - Auto-sends multi-channel notifications.

    Handles:
    - Slack notifications (channels, DMs, mentions)
    - SMS notifications via Twilio
    - Push notifications (mobile, web)
    - Webhook notifications for integrations
    - Microsoft Teams notifications
    - Discord notifications
    - PagerDuty alerts for incidents
    - Multi-channel broadcast
    """

    # Supported notification channels
    NOTIFICATION_CHANNELS = {
        "slack": {
            "api_endpoint": "https://slack.com/api/chat.postMessage",
            "supports_attachments": True,
            "supports_markdown": True,
            "max_message_length": 40000
        },
        "sms": {
            "api_endpoint": "https://api.twilio.com/2010-04-01",
            "supports_attachments": False,
            "supports_markdown": False,
            "max_message_length": 1600
        },
        "push": {
            "api_endpoint": "https://fcm.googleapis.com/fcm/send",
            "supports_attachments": True,
            "supports_markdown": False,
            "max_message_length": 4096
        },
        "teams": {
            "api_endpoint": "https://outlook.office.com/webhook",
            "supports_attachments": True,
            "supports_markdown": True,
            "max_message_length": 28000
        },
        "webhook": {
            "supports_attachments": True,
            "supports_markdown": False,
            "max_message_length": None
        },
        "pagerduty": {
            "api_endpoint": "https://api.pagerduty.com/incidents",
            "supports_attachments": False,
            "supports_markdown": False,
            "max_message_length": 1024
        }
    }

    # Notification types and their priorities
    NOTIFICATION_TYPES = {
        "alert": {
            "priority": "high",
            "default_channels": ["slack", "sms", "pagerduty"],
            "requires_acknowledgment": True,
            "icon": "🚨"
        },
        "info": {
            "priority": "normal",
            "default_channels": ["slack"],
            "requires_acknowledgment": False,
            "icon": "ℹ️"
        },
        "success": {
            "priority": "low",
            "default_channels": ["slack"],
            "requires_acknowledgment": False,
            "icon": "✅"
        },
        "warning": {
            "priority": "medium",
            "default_channels": ["slack", "push"],
            "requires_acknowledgment": False,
            "icon": "⚠️"
        },
        "error": {
            "priority": "high",
            "default_channels": ["slack", "sms"],
            "requires_acknowledgment": True,
            "icon": "❌"
        },
        "update": {
            "priority": "normal",
            "default_channels": ["slack", "push"],
            "requires_acknowledgment": False,
            "icon": "📢"
        }
    }

    # Priority levels and retry policies
    PRIORITY_CONFIGS = {
        "critical": {
            "retry_attempts": 5,
            "retry_delay_seconds": 30,
            "timeout_seconds": 10
        },
        "high": {
            "retry_attempts": 3,
            "retry_delay_seconds": 60,
            "timeout_seconds": 30
        },
        "normal": {
            "retry_attempts": 2,
            "retry_delay_seconds": 120,
            "timeout_seconds": 60
        },
        "low": {
            "retry_attempts": 1,
            "retry_delay_seconds": 300,
            "timeout_seconds": 120
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="notification_sender",
            type=AgentType.AUTOMATOR,
            temperature=0.1,
            max_tokens=800,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Auto-send notifications via multiple channels.

        Args:
            state: Current agent state with notification request

        Returns:
            Updated state with sent notification details
        """
        self.logger.info("notification_sender_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Extract notification parameters
        notification_type = entities.get("notification_type", "info")
        channels = entities.get("channels", None)
        priority = entities.get("priority", "normal")

        self.logger.debug(
            "notification_sending_details",
            notification_type=notification_type,
            channels=channels,
            priority=priority
        )

        # Parse notification content
        notification_content = await self._parse_notification_content(
            message,
            notification_type,
            customer_metadata
        )

        # Determine target channels
        target_channels = self._determine_channels(
            notification_type,
            channels,
            customer_metadata
        )

        # Prepare channel-specific messages
        channel_messages = self._prepare_channel_messages(
            notification_content,
            target_channels,
            notification_type
        )

        # Validate messages for each channel
        validation_results = self._validate_messages(
            channel_messages,
            target_channels
        )

        # Send notifications to all channels
        sent_notifications = await self._send_notifications(
            channel_messages,
            target_channels,
            priority,
            validation_results
        )

        # Setup retry for failed notifications
        retry_config = self._setup_retry_policy(
            sent_notifications,
            priority
        )

        # Log automation action
        automation_log = self._log_automation_action(
            "notification_sent",
            sent_notifications,
            customer_metadata
        )

        # Generate response
        response = self._format_notification_response(
            sent_notifications,
            target_channels,
            retry_config
        )

        state["agent_response"] = response
        state["sent_notifications"] = sent_notifications
        state["notification_content"] = notification_content
        state["target_channels"] = target_channels
        state["retry_config"] = retry_config
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.95
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "notifications_sent_successfully",
            notification_count=len(sent_notifications),
            channels=target_channels,
            notification_type=notification_type
        )

        return state

    async def _parse_notification_content(
        self,
        message: str,
        notification_type: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Parse notification content from message.

        Args:
            message: Message content
            notification_type: Type of notification
            customer_metadata: Customer metadata

        Returns:
            Parsed notification content
        """
        system_prompt = f"""You are a notification content specialist. Extract structured information for a {notification_type} notification.

Extract:
1. Title/headline (concise, attention-grabbing)
2. Message body (clear, actionable)
3. Priority/urgency level
4. Any actionable links or buttons
5. Context or additional details

Keep it concise and clear."""

        user_prompt = f"""Parse this notification request:

Message: {message}

Notification Type: {notification_type}
Customer: {customer_metadata.get('customer_name', 'Unknown')}

Return JSON with title, body, priority, action_url, and additional_context."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[]  # Notification parsing uses message context
        )

        # Parse LLM response
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                content = json.loads(json_match.group())
            else:
                content = {
                    "title": f"{notification_type.title()} Notification",
                    "body": message,
                    "priority": "normal"
                }
        except:
            content = {
                "title": f"{notification_type.title()} Notification",
                "body": message,
                "priority": "normal"
            }

        return content

    def _determine_channels(
        self,
        notification_type: str,
        requested_channels: Optional[List[str]],
        customer_metadata: Dict
    ) -> List[str]:
        """
        Determine which channels to use for notification.

        Args:
            notification_type: Type of notification
            requested_channels: Explicitly requested channels
            customer_metadata: Customer metadata

        Returns:
            List of channels to use
        """
        if requested_channels:
            return requested_channels

        # Use default channels for notification type
        notification_config = self.NOTIFICATION_TYPES.get(
            notification_type,
            self.NOTIFICATION_TYPES["info"]
        )

        default_channels = notification_config["default_channels"]

        # Filter based on customer preferences
        customer_prefs = customer_metadata.get("notification_preferences", {})
        enabled_channels = customer_prefs.get("enabled_channels", default_channels)

        return [ch for ch in default_channels if ch in enabled_channels]

    def _prepare_channel_messages(
        self,
        notification_content: Dict,
        target_channels: List[str],
        notification_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Prepare channel-specific message formats.

        Args:
            notification_content: Base notification content
            target_channels: Channels to send to
            notification_type: Type of notification

        Returns:
            Dict mapping channel to formatted message
        """
        notification_config = self.NOTIFICATION_TYPES.get(
            notification_type,
            self.NOTIFICATION_TYPES["info"]
        )

        icon = notification_config["icon"]
        channel_messages = {}

        for channel in target_channels:
            channel_config = self.NOTIFICATION_CHANNELS.get(channel, {})

            if channel == "slack":
                channel_messages[channel] = {
                    "text": f"{icon} *{notification_content['title']}*",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"{icon} *{notification_content['title']}*\n{notification_content['body']}"
                            }
                        }
                    ],
                    "channel": "#general"
                }

                if notification_content.get("action_url"):
                    channel_messages[channel]["blocks"].append({
                        "type": "actions",
                        "elements": [{
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Details"},
                            "url": notification_content["action_url"]
                        }]
                    })

            elif channel == "sms":
                # SMS has length limits, keep it concise
                max_length = channel_config["max_message_length"]
                sms_text = f"{notification_content['title']}: {notification_content['body']}"
                channel_messages[channel] = {
                    "body": sms_text[:max_length],
                    "to": "+1234567890"  # Would come from customer metadata
                }

            elif channel == "push":
                channel_messages[channel] = {
                    "notification": {
                        "title": notification_content['title'],
                        "body": notification_content['body'][:200],  # Truncate for preview
                        "icon": icon
                    },
                    "data": {
                        "type": notification_type,
                        "action_url": notification_content.get("action_url")
                    }
                }

            elif channel == "teams":
                channel_messages[channel] = {
                    "@type": "MessageCard",
                    "@context": "https://schema.org/extensions",
                    "summary": notification_content['title'],
                    "themeColor": self._get_theme_color(notification_type),
                    "title": f"{icon} {notification_content['title']}",
                    "text": notification_content['body']
                }

            elif channel == "webhook":
                channel_messages[channel] = {
                    "event_type": notification_type,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "title": notification_content['title'],
                    "body": notification_content['body'],
                    "metadata": notification_content.get("additional_context", {})
                }

            elif channel == "pagerduty":
                channel_messages[channel] = {
                    "incident": {
                        "type": "incident",
                        "title": notification_content['title'],
                        "body": {
                            "type": "incident_body",
                            "details": notification_content['body']
                        },
                        "urgency": "high" if notification_type in ["alert", "error"] else "low"
                    }
                }

        return channel_messages

    def _get_theme_color(self, notification_type: str) -> str:
        """Get theme color for notification type."""
        colors = {
            "alert": "FF0000",
            "error": "FF0000",
            "warning": "FFA500",
            "success": "00FF00",
            "info": "0078D4",
            "update": "0078D4"
        }
        return colors.get(notification_type, "0078D4")

    def _validate_messages(
        self,
        channel_messages: Dict[str, Dict],
        target_channels: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate messages for each channel.

        Args:
            channel_messages: Messages prepared for each channel
            target_channels: Target channels

        Returns:
            Validation results per channel
        """
        validation_results = {}

        for channel in target_channels:
            message = channel_messages.get(channel, {})
            channel_config = self.NOTIFICATION_CHANNELS.get(channel, {})

            validation = {
                "is_valid": True,
                "warnings": [],
                "errors": []
            }

            # Check message length
            max_length = channel_config.get("max_message_length")
            if max_length:
                message_str = json.dumps(message)
                if len(message_str) > max_length:
                    validation["warnings"].append(f"Message exceeds max length ({max_length})")

            # Check required fields
            if channel == "slack" and not message.get("text"):
                validation["errors"].append("Missing required 'text' field")
                validation["is_valid"] = False

            validation_results[channel] = validation

        return validation_results

    async def _send_notifications(
        self,
        channel_messages: Dict[str, Dict],
        target_channels: List[str],
        priority: str,
        validation_results: Dict
    ) -> List[Dict[str, Any]]:
        """
        Send notifications to all channels (mocked).

        Args:
            channel_messages: Messages for each channel
            target_channels: Target channels
            priority: Priority level
            validation_results: Validation results

        Returns:
            List of sent notification records
        """
        sent_notifications = []

        for channel in target_channels:
            if not validation_results.get(channel, {}).get("is_valid", False):
                self.logger.warning(
                    "skipping_invalid_notification",
                    channel=channel,
                    errors=validation_results[channel].get("errors")
                )
                continue

            message = channel_messages.get(channel, {})

            # In production, make actual API calls to each service
            # For now, return mock sent notification

            import hashlib
            notification_id = hashlib.md5(
                f"{channel}{datetime.now(UTC)}".encode()
            ).hexdigest()[:12]

            notification_record = {
                "id": notification_id,
                "channel": channel,
                "message": message,
                "priority": priority,
                "status": "sent",
                "sent_at": datetime.now(UTC).isoformat(),
                "delivery_status": "delivered",
                "retry_count": 0
            }

            sent_notifications.append(notification_record)

            self.logger.info(
                "notification_sent_to_channel",
                notification_id=notification_id,
                channel=channel,
                priority=priority
            )

        return sent_notifications

    def _setup_retry_policy(
        self,
        sent_notifications: List[Dict],
        priority: str
    ) -> Dict[str, Any]:
        """
        Setup retry policy for failed notifications.

        Args:
            sent_notifications: Sent notification records
            priority: Priority level

        Returns:
            Retry configuration
        """
        priority_config = self.PRIORITY_CONFIGS.get(
            priority,
            self.PRIORITY_CONFIGS["normal"]
        )

        failed_notifications = [
            n for n in sent_notifications
            if n.get("status") != "sent"
        ]

        return {
            "enabled": len(failed_notifications) > 0,
            "failed_count": len(failed_notifications),
            "max_retry_attempts": priority_config["retry_attempts"],
            "retry_delay_seconds": priority_config["retry_delay_seconds"],
            "timeout_seconds": priority_config["timeout_seconds"],
            "failed_channels": [n["channel"] for n in failed_notifications]
        }

    def _log_automation_action(
        self,
        action_type: str,
        sent_notifications: List[Dict],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Log automated action for audit trail."""
        return {
            "action_type": action_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "notification_count": len(sent_notifications),
            "customer_id": customer_metadata.get("customer_id"),
            "success": all(n.get("status") == "sent" for n in sent_notifications),
            "details": {
                "channels": [n["channel"] for n in sent_notifications],
                "statuses": {n["channel"]: n["status"] for n in sent_notifications}
            }
        }

    def _format_notification_response(
        self,
        sent_notifications: List[Dict],
        target_channels: List[str],
        retry_config: Dict
    ) -> str:
        """Format notification sending response."""
        response = f"""**Notifications Sent Successfully**

Total Notifications: {len(sent_notifications)}
Channels: {', '.join(target_channels)}

**Delivery Status:**
"""

        for notification in sent_notifications:
            status_icon = "✓" if notification["status"] == "sent" else "✗"
            response += f"{status_icon} {notification['channel'].title()}: {notification['delivery_status'].title()}\n"
            response += f"   Notification ID: {notification['id']}\n"
            response += f"   Sent At: {notification['sent_at']}\n\n"

        if retry_config.get("enabled"):
            response += f"""**Retry Policy:**
- Failed notifications: {retry_config['failed_count']}
- Max retry attempts: {retry_config['max_retry_attempts']}
- Retry delay: {retry_config['retry_delay_seconds']} seconds
- Failed channels: {', '.join(retry_config['failed_channels'])}
"""

        return response
