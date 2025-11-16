"""
Task Automation Agents - 5 Agents

Auto-creates tickets, schedules meetings, sends emails, reminders, and notifications.
"""

from src.agents.operational.automation.task_automation.ticket_creator import TicketCreatorAgent
from src.agents.operational.automation.task_automation.calendar_scheduler import CalendarSchedulerAgent
from src.agents.operational.automation.task_automation.email_sender import EmailSenderAgent
from src.agents.operational.automation.task_automation.reminder_sender import ReminderSenderAgent
from src.agents.operational.automation.task_automation.notification_sender import NotificationSenderAgent

__all__ = [
    "TicketCreatorAgent",
    "CalendarSchedulerAgent",
    "EmailSenderAgent",
    "ReminderSenderAgent",
    "NotificationSenderAgent",
]
