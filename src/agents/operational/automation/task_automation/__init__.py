"""
Task Automation Agents - 5 Agents

Auto-creates tickets, schedules meetings, sends emails, reminders, and notifications.
"""

from src.agents.operational.automation.task_automation.calendar_scheduler import (
    CalendarSchedulerAgent,
)
from src.agents.operational.automation.task_automation.email_sender import EmailSenderAgent
from src.agents.operational.automation.task_automation.notification_sender import (
    NotificationSenderAgent,
)
from src.agents.operational.automation.task_automation.reminder_sender import ReminderSenderAgent
from src.agents.operational.automation.task_automation.ticket_creator import TicketCreatorAgent

__all__ = [
    "CalendarSchedulerAgent",
    "EmailSenderAgent",
    "NotificationSenderAgent",
    "ReminderSenderAgent",
    "TicketCreatorAgent",
]
