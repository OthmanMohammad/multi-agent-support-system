"""
Reminder Sender Agent - TASK-2204

Auto-sends reminders for upcoming deadlines, renewals, meetings,
and action items via email or notifications.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("reminder_sender", tier="operational", category="automation")
class ReminderSenderAgent(BaseAgent):
    """
    Reminder Sender Agent - Auto-sends deadline and event reminders.

    Handles:
    - Deadline reminder scheduling
    - Recurring reminder setup
    - Multi-channel delivery (email, SMS, Slack, push notification)
    - Smart reminder timing based on urgency
    - Reminder escalation for overdue items
    - Snooze and reschedule functionality
    - Batch reminder processing
    - Reminder deduplication
    """

    # Reminder types and default schedules
    REMINDER_TYPES = {
        "renewal": {
            "advance_days": [30, 14, 7, 1],
            "channels": ["email", "slack"],
            "escalate_if_overdue": True
        },
        "meeting": {
            "advance_hours": [24, 1, 0.25],  # 24h, 1h, 15min
            "channels": ["email", "notification"],
            "escalate_if_overdue": False
        },
        "deadline": {
            "advance_days": [7, 3, 1],
            "channels": ["email", "slack", "notification"],
            "escalate_if_overdue": True
        },
        "followup": {
            "advance_hours": [0],  # Send immediately
            "channels": ["email"],
            "escalate_if_overdue": False
        },
        "payment": {
            "advance_days": [7, 3, 0],  # 7d, 3d, day-of
            "channels": ["email", "sms"],
            "escalate_if_overdue": True
        },
        "action_item": {
            "advance_hours": [24, 4],
            "channels": ["notification", "slack"],
            "escalate_if_overdue": True
        }
    }

    # Reminder urgency levels
    URGENCY_LEVELS = {
        "critical": {
            "max_reminders": 5,
            "escalate_after": 1,  # days
            "repeat_interval": 4  # hours
        },
        "high": {
            "max_reminders": 3,
            "escalate_after": 3,
            "repeat_interval": 24
        },
        "medium": {
            "max_reminders": 2,
            "escalate_after": 7,
            "repeat_interval": 72
        },
        "low": {
            "max_reminders": 1,
            "escalate_after": 14,
            "repeat_interval": 168
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="reminder_sender",
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
        Auto-send reminders for deadlines and events.

        Args:
            state: Current agent state with reminder request

        Returns:
            Updated state with sent reminder details
        """
        self.logger.info("reminder_sender_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Extract reminder parameters
        reminder_type = entities.get("reminder_type", "deadline")
        urgency = entities.get("urgency", "medium")
        deadline = entities.get("deadline", None)

        self.logger.debug(
            "reminder_sending_details",
            reminder_type=reminder_type,
            urgency=urgency,
            deadline=deadline
        )

        # Parse reminder details
        reminder_details = await self._parse_reminder_request(
            message,
            reminder_type,
            customer_metadata
        )

        # Calculate reminder schedule
        reminder_schedule = self._calculate_reminder_schedule(
            reminder_type,
            reminder_details,
            urgency
        )

        # Check for duplicate reminders
        duplicate_check = self._check_duplicate_reminders(
            reminder_details,
            customer_metadata.get("active_reminders", [])
        )

        # Prepare reminder messages
        reminder_messages = self._prepare_reminder_messages(
            reminder_type,
            reminder_details,
            reminder_schedule,
            customer_metadata
        )

        # Send or schedule reminders
        sent_reminders = await self._send_reminders(
            reminder_messages,
            reminder_schedule,
            duplicate_check
        )

        # Setup escalation if needed
        escalation_config = self._setup_escalation(
            reminder_type,
            reminder_details,
            urgency
        )

        # Log automation action
        automation_log = self._log_automation_action(
            "reminder_sent",
            sent_reminders,
            customer_metadata
        )

        # Generate response
        response = self._format_reminder_response(
            sent_reminders,
            reminder_schedule,
            escalation_config
        )

        state["agent_response"] = response
        state["sent_reminders"] = sent_reminders
        state["reminder_schedule"] = reminder_schedule
        state["reminder_details"] = reminder_details
        state["escalation_config"] = escalation_config
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.94
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "reminders_sent_successfully",
            reminder_count=len(sent_reminders),
            reminder_type=reminder_type,
            urgency=urgency
        )

        return state

    async def _parse_reminder_request(
        self,
        message: str,
        reminder_type: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Parse reminder request from message.

        Args:
            message: Customer message or trigger
            reminder_type: Type of reminder
            customer_metadata: Customer metadata

        Returns:
            Parsed reminder details
        """
        system_prompt = f"""You are a reminder scheduling specialist. Extract details for a {reminder_type} reminder.

Extract:
1. What the reminder is for (subject/topic)
2. Deadline/due date (if mentioned)
3. Urgency indicators
4. Any specific timing preferences
5. Additional context

Be precise with dates and times."""

        user_prompt = f"""Parse this reminder request:

Message: {message}

Reminder Type: {reminder_type}
Customer: {customer_metadata.get('customer_name', 'Unknown')}

Return JSON with subject, deadline, urgency_level, preferred_channels, and additional_context."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[]  # Reminder parsing uses message context
        )

        # Parse LLM response
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                details = json.loads(json_match.group())
            else:
                details = {
                    "subject": message[:100],
                    "deadline": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
                    "urgency_level": "medium"
                }
        except:
            details = {
                "subject": message[:100],
                "deadline": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
                "urgency_level": "medium"
            }

        return details

    def _calculate_reminder_schedule(
        self,
        reminder_type: str,
        reminder_details: Dict,
        urgency: str
    ) -> List[Dict[str, Any]]:
        """
        Calculate when reminders should be sent.

        Args:
            reminder_type: Type of reminder
            reminder_details: Reminder details
            urgency: Urgency level

        Returns:
            List of scheduled reminder times
        """
        reminder_config = self.REMINDER_TYPES.get(
            reminder_type,
            self.REMINDER_TYPES["deadline"]
        )

        deadline_str = reminder_details.get("deadline")
        if deadline_str:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00').split('+')[0])
        else:
            deadline = datetime.now(UTC) + timedelta(days=7)

        schedule = []

        # Calculate reminder times based on advance days/hours
        if "advance_days" in reminder_config:
            for days in reminder_config["advance_days"]:
                send_time = deadline - timedelta(days=days)
                if send_time > datetime.now(UTC):
                    schedule.append({
                        "send_at": send_time.isoformat(),
                        "advance_days": days,
                        "channels": reminder_config["channels"],
                        "type": "scheduled"
                    })

        if "advance_hours" in reminder_config:
            for hours in reminder_config["advance_hours"]:
                send_time = deadline - timedelta(hours=hours)
                if send_time > datetime.now(UTC):
                    schedule.append({
                        "send_at": send_time.isoformat(),
                        "advance_hours": hours,
                        "channels": reminder_config["channels"],
                        "type": "scheduled"
                    })

        # Sort by send time
        schedule.sort(key=lambda x: x["send_at"])

        return schedule

    def _check_duplicate_reminders(
        self,
        reminder_details: Dict,
        active_reminders: List[Dict]
    ) -> Dict[str, Any]:
        """
        Check for duplicate active reminders.

        Args:
            reminder_details: New reminder details
            active_reminders: List of active reminders

        Returns:
            Duplicate check results
        """
        subject = reminder_details.get("subject", "").lower()
        deadline = reminder_details.get("deadline")

        duplicates = []

        for active in active_reminders:
            active_subject = active.get("subject", "").lower()
            active_deadline = active.get("deadline")

            # Check for same subject and deadline
            if subject == active_subject and deadline == active_deadline:
                duplicates.append({
                    "reminder_id": active.get("id"),
                    "subject": active.get("subject"),
                    "status": active.get("status")
                })

        return {
            "has_duplicates": len(duplicates) > 0,
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
            "should_proceed": len(duplicates) == 0
        }

    def _prepare_reminder_messages(
        self,
        reminder_type: str,
        reminder_details: Dict,
        reminder_schedule: List[Dict],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """
        Prepare reminder messages for each scheduled time.

        Args:
            reminder_type: Type of reminder
            reminder_details: Reminder details
            reminder_schedule: When to send reminders
            customer_metadata: Customer metadata

        Returns:
            List of prepared reminder messages
        """
        messages = []

        subject = reminder_details.get("subject", "Reminder")
        deadline = reminder_details.get("deadline")

        for idx, schedule_item in enumerate(reminder_schedule):
            # Determine message urgency based on how close to deadline
            advance = schedule_item.get("advance_days", schedule_item.get("advance_hours", 0))

            if advance <= 1:
                urgency_prefix = "URGENT: "
            elif advance <= 3:
                urgency_prefix = "Important: "
            else:
                urgency_prefix = ""

            message = {
                "id": f"reminder_{idx}_{reminder_type}",
                "subject": f"{urgency_prefix}Reminder: {subject}",
                "body": self._generate_reminder_body(
                    reminder_type,
                    subject,
                    deadline,
                    advance,
                    customer_metadata
                ),
                "send_at": schedule_item["send_at"],
                "channels": schedule_item["channels"],
                "type": reminder_type,
                "urgency": "high" if advance <= 1 else "normal"
            }

            messages.append(message)

        return messages

    def _generate_reminder_body(
        self,
        reminder_type: str,
        subject: str,
        deadline: str,
        advance: float,
        customer_metadata: Dict
    ) -> str:
        """Generate reminder message body."""
        customer_name = customer_metadata.get("customer_name", "there")

        if reminder_type == "renewal":
            body = f"""Hi {customer_name},

This is a reminder that your subscription renewal is coming up.

What: {subject}
When: {deadline}
Days Remaining: {int(advance)}

No action needed - your subscription will automatically renew unless you make changes.

Questions? Contact us anytime.

Best regards,
The Team"""

        elif reminder_type == "meeting":
            hours = advance if advance < 1 else advance * 24
            body = f"""Hi {customer_name},

Reminder: You have an upcoming meeting.

Meeting: {subject}
When: {deadline}
Time Until Meeting: {int(hours)} hours

Meeting details and join link were sent in your calendar invite.

See you soon!"""

        elif reminder_type == "deadline":
            body = f"""Hi {customer_name},

Reminder about an upcoming deadline.

Task: {subject}
Due: {deadline}
Days Remaining: {int(advance)}

Please ensure this is completed on time.

Need help? Let us know.

Best regards,
The Team"""

        else:
            body = f"""Hi {customer_name},

Reminder: {subject}

Due: {deadline}
Time Remaining: {int(advance)} days

Please take appropriate action.

Best regards,
The Team"""

        return body

    async def _send_reminders(
        self,
        reminder_messages: List[Dict],
        reminder_schedule: List[Dict],
        duplicate_check: Dict
    ) -> List[Dict[str, Any]]:
        """
        Send or schedule reminders (mocked).

        Args:
            reminder_messages: Prepared reminder messages
            reminder_schedule: Schedule information
            duplicate_check: Duplicate check results

        Returns:
            List of sent/scheduled reminders
        """
        sent_reminders = []

        for message in reminder_messages:
            send_time = datetime.fromisoformat(message["send_at"])
            is_immediate = send_time <= datetime.now(UTC)

            reminder_record = {
                "id": message["id"],
                "subject": message["subject"],
                "body": message["body"],
                "channels": message["channels"],
                "send_at": message["send_at"],
                "status": "sent" if is_immediate else "scheduled",
                "type": message["type"],
                "urgency": message["urgency"],
                "created_at": datetime.now(UTC).isoformat()
            }

            sent_reminders.append(reminder_record)

            self.logger.info(
                "reminder_processed",
                reminder_id=message["id"],
                status=reminder_record["status"],
                channels=message["channels"]
            )

        return sent_reminders

    def _setup_escalation(
        self,
        reminder_type: str,
        reminder_details: Dict,
        urgency: str
    ) -> Dict[str, Any]:
        """
        Setup escalation policy for overdue items.

        Args:
            reminder_type: Type of reminder
            reminder_details: Reminder details
            urgency: Urgency level

        Returns:
            Escalation configuration
        """
        reminder_config = self.REMINDER_TYPES.get(reminder_type, {})
        urgency_config = self.URGENCY_LEVELS.get(urgency, self.URGENCY_LEVELS["medium"])

        if not reminder_config.get("escalate_if_overdue", False):
            return {"enabled": False}

        return {
            "enabled": True,
            "escalate_after_days": urgency_config["escalate_after"],
            "max_reminders": urgency_config["max_reminders"],
            "repeat_interval_hours": urgency_config["repeat_interval"],
            "escalation_channels": ["email", "slack", "sms"],
            "escalation_recipients": ["manager@acme-corp.com"]
        }

    def _log_automation_action(
        self,
        action_type: str,
        sent_reminders: List[Dict],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Log automated action for audit trail."""
        return {
            "action_type": action_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "reminder_count": len(sent_reminders),
            "customer_id": customer_metadata.get("customer_id"),
            "success": True,
            "details": {
                "reminders": [
                    {
                        "id": r["id"],
                        "status": r["status"],
                        "send_at": r["send_at"]
                    }
                    for r in sent_reminders
                ]
            }
        }

    def _format_reminder_response(
        self,
        sent_reminders: List[Dict],
        reminder_schedule: List[Dict],
        escalation_config: Dict
    ) -> str:
        """Format reminder sending response."""
        response = f"""**Reminders Configured Successfully**

Total Reminders: {len(sent_reminders)}

**Reminder Schedule:**
"""

        for reminder in sent_reminders:
            status_icon = "✓" if reminder["status"] == "sent" else "⏰"
            response += f"{status_icon} {reminder['subject']}\n"
            response += f"   Send At: {reminder['send_at']}\n"
            response += f"   Channels: {', '.join(reminder['channels'])}\n"
            response += f"   Status: {reminder['status'].title()}\n\n"

        if escalation_config.get("enabled"):
            response += f"""**Escalation Policy:**
- Escalate if overdue after: {escalation_config['escalate_after_days']} days
- Max reminder attempts: {escalation_config['max_reminders']}
- Repeat interval: {escalation_config['repeat_interval_hours']} hours
"""

        return response
