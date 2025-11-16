"""
Data Automation Agents - 5 Agents

Auto-updates CRM, enriches contacts, deduplicates records, validates data, and generates reports.
"""

from src.agents.operational.automation.data_automation.crm_updater import CRMUpdaterAgent
from src.agents.operational.automation.data_automation.contact_enricher import ContactEnricherAgent
from src.agents.operational.automation.data_automation.deduplicator import DeduplicatorAgent
from src.agents.operational.automation.data_automation.data_validator import DataValidatorAgent
from src.agents.operational.automation.data_automation.report_automator import ReportAutomatorAgent

__all__ = [
    "CRMUpdaterAgent",
    "ContactEnricherAgent",
    "DeduplicatorAgent",
    "DataValidatorAgent",
    "ReportAutomatorAgent",
]
