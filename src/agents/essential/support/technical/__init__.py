"""
Technical support agents - Specialists for technical issues.

This module contains 7 specialized technical support agents:
1. TechnicalAgent - General technical support (bug triager)
2. CrashInvestigator - Crash investigation and log analysis
3. SyncTroubleshooter - Data sync issue resolution
4. PerformanceOptimizer - Performance optimization
5. LoginSpecialist - Authentication and login issues
6. DataRecoverySpecialist - Data recovery from backups
7. BrowserCompatibilitySpecialist - Browser compatibility issues
"""

from src.agents.essential.support.technical.browser_compatibility_specialist import (
    BrowserCompatibilitySpecialist,
)
from src.agents.essential.support.technical.bug_triager import TechnicalAgent
from src.agents.essential.support.technical.crash_investigator import CrashInvestigator
from src.agents.essential.support.technical.data_recovery_specialist import DataRecoverySpecialist
from src.agents.essential.support.technical.login_specialist import LoginSpecialist
from src.agents.essential.support.technical.performance_optimizer import PerformanceOptimizer
from src.agents.essential.support.technical.sync_troubleshooter import SyncTroubleshooter

__all__ = [
    "BrowserCompatibilitySpecialist",
    "CrashInvestigator",
    "DataRecoverySpecialist",
    "LoginSpecialist",
    "PerformanceOptimizer",
    "SyncTroubleshooter",
    "TechnicalAgent",
]
