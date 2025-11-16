"""
Automation & Workflow Swarm - Tier 3: Operational Excellence

This module contains 20 specialized automation agents organized into 3 categories:
- Task Automation (5 agents): Tickets, scheduling, emails, reminders, notifications
- Data Automation (5 agents): CRM updates, enrichment, deduplication, validation, reports
- Process Automation (10 agents): Workflows, approvals, SLAs, handoffs, renewals, billing, backups

Total: 20 automation agents for comprehensive workflow and process automation.

Agents:
**Task Automation:**
- TicketCreatorAgent (TASK-2201): Auto-create tickets in Jira/Linear/GitHub
- CalendarSchedulerAgent (TASK-2202): Auto-schedule demos, QBRs, calls
- EmailSenderAgent (TASK-2203): Auto-send templated emails
- ReminderSenderAgent (TASK-2204): Auto-send reminders for deadlines
- NotificationSenderAgent (TASK-2205): Auto-send Slack/SMS notifications

**Data Automation:**
- CRMUpdaterAgent (TASK-2206): Auto-update CRM from conversations
- ContactEnricherAgent (TASK-2207): Auto-enrich contacts with external data
- DeduplicatorAgent (TASK-2208): Auto-detect and merge duplicates
- DataValidatorAgent (TASK-2209): Auto-validate data quality
- ReportAutomatorAgent (TASK-2210): Auto-generate recurring reports

**Process Automation:**
- WorkflowExecutorAgent (TASK-2211): Execute multi-step workflows
- ApprovalRouterAgent (TASK-2212): Route approvals automatically
- SLAEnforcerAgent (TASK-2213): Monitor and enforce SLAs
- HandoffAutomatorAgent (TASK-2214): Automate agent-to-agent handoffs
- OnboardingAutomatorAgent (TASK-2215): Automate customer onboarding
- RenewalProcessorAgent (TASK-2216): Automate renewal workflows
- InvoiceSenderAgent (TASK-2217): Auto-send invoices
- PaymentRetryAgent (TASK-2218): Auto-retry failed payments
- DataBackupAgent (TASK-2219): Auto-backup critical data
- CleanupSchedulerAgent (TASK-2220): Auto-cleanup old data
"""

# Task Automation (5 agents)
from src.agents.operational.automation.task_automation import (
    TicketCreatorAgent,
    CalendarSchedulerAgent,
    EmailSenderAgent,
    ReminderSenderAgent,
    NotificationSenderAgent,
)

# Data Automation (5 agents)
from src.agents.operational.automation.data_automation import (
    CRMUpdaterAgent,
    ContactEnricherAgent,
    DeduplicatorAgent,
    DataValidatorAgent,
    ReportAutomatorAgent,
)

# Process Automation (10 agents)
from src.agents.operational.automation.process_automation import (
    WorkflowExecutorAgent,
    ApprovalRouterAgent,
    SLAEnforcerAgent,
    HandoffAutomatorAgent,
    OnboardingAutomatorAgent,
    RenewalProcessorAgent,
    InvoiceSenderAgent,
    PaymentRetryAgent,
    DataBackupAgent,
    CleanupSchedulerAgent,
)

__all__ = [
    # Task Automation (5)
    "TicketCreatorAgent",
    "CalendarSchedulerAgent",
    "EmailSenderAgent",
    "ReminderSenderAgent",
    "NotificationSenderAgent",

    # Data Automation (5)
    "CRMUpdaterAgent",
    "ContactEnricherAgent",
    "DeduplicatorAgent",
    "DataValidatorAgent",
    "ReportAutomatorAgent",

    # Process Automation (10)
    "WorkflowExecutorAgent",
    "ApprovalRouterAgent",
    "SLAEnforcerAgent",
    "HandoffAutomatorAgent",
    "OnboardingAutomatorAgent",
    "RenewalProcessorAgent",
    "InvoiceSenderAgent",
    "PaymentRetryAgent",
    "DataBackupAgent",
    "CleanupSchedulerAgent",
]
