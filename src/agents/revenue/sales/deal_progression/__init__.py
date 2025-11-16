"""
Deal Progression Module - Sales Agents for Deal Advancement

This module contains specialized agents for moving deals through the sales pipeline,
from demo scheduling through closing and expansion.

Agents:
    - DemoScheduler: Schedules demos and prepares environment (TASK-1041)
    - TrialOptimizer: Monitors trials and optimizes conversions (TASK-1042)
    - ProposalGenerator: Creates customized proposals with pricing (TASK-1043)
    - ContractNegotiator: Handles contract negotiations and approvals (TASK-1044)
    - Closer: Drives deals to signature with urgency tactics (TASK-1045)
    - UpsellIdentifier: Identifies expansion opportunities (TASK-1046)
"""

from src.agents.revenue.sales.deal_progression.demo_scheduler import DemoScheduler
from src.agents.revenue.sales.deal_progression.trial_optimizer import TrialOptimizer
from src.agents.revenue.sales.deal_progression.proposal_generator import ProposalGenerator
from src.agents.revenue.sales.deal_progression.contract_negotiator import ContractNegotiator
from src.agents.revenue.sales.deal_progression.closer import Closer
from src.agents.revenue.sales.deal_progression.upsell_identifier import UpsellIdentifier

__all__ = [
    "DemoScheduler",
    "TrialOptimizer",
    "ProposalGenerator",
    "ContractNegotiator",
    "Closer",
    "UpsellIdentifier",
]
