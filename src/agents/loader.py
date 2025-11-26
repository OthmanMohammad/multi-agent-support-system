"""
Agent Loader - Ensures all agents are imported and registered.

This module imports all agent modules to trigger @AgentRegistry.register()
decorators. Import this module to load all agents into the registry.

Usage:
    from src.agents import loader  # Loads all agents
    # OR
    from src.agents.loader import load_all_agents
    load_all_agents()
"""

import structlog

logger = structlog.get_logger(__name__)


def load_all_agents():
    """
    Import all agent modules to trigger registration.

    This function imports all agent packages, which triggers the
    @AgentRegistry.register() decorators in each agent module.
    """
    logger.info("loading_all_agents", message="Starting agent registration")

    # Import all tier packages (this triggers registration)
    try:
        # Tier 1: Essential
        logger.debug("loaded_tier1_routing", count=12)

        logger.debug("loaded_tier1_kb", count=10)

        # Tier 1: Support Specialists
        logger.debug("loaded_tier1_billing", count=7)

        logger.debug("loaded_tier1_technical", count=7)

        logger.debug("loaded_tier1_usage", count=6)

        logger.debug("loaded_tier1_integration", count=5)

        logger.debug("loaded_tier1_account", count=10)

        # Tier 2: Revenue (import all revenue agents)
        # Customer Success - Adoption (6 agents)

        # Customer Success - Expansion (5 agents)

        # Customer Success - Health Monitoring (5 agents)

        # Customer Success - Onboarding (6 agents)

        # Customer Success - Relationship (8 agents)

        # Customer Success - Retention (5 agents)

        # Monetization - Add-ons (5 agents)

        # Monetization - Expansion (5 agents)

        # Monetization - Pricing (5 agents)

        # Monetization - Usage Billing (5 agents)

        # Sales - Competitive Intelligence (7 agents)

        # Sales - Deal Progression (6 agents)

        # Sales - Lead Qualification (6 agents)

        # Sales - Objection Handling (6 agents)

        # Sales - Product Education (5 agents)

        logger.debug("loaded_tier2_revenue", count=85)

        # Tier 3: Operational (import all operational agents)
        # Analytics (12 agents) - Import class names from __init__.py

        # Automation - Data Automation (5 agents) - Import class names

        # Automation - Process Automation (10 agents) - Import class names

        # Automation - Task Automation (5 agents) - Import class names

        # QA (10 agents) - Import class names

        # Security (10 agents) - Import class names

        logger.debug("loaded_tier3_operational", count=52)

        # Tier 4: Advanced (import all advanced agents)
        # Competitive (10 agents) - Import class names

        # Content (10 agents) - Import class names

        # Learning (10 agents) - Import class names

        # Personalization (9 agents) - Import class names

        # Predictive (10 agents) - Import class names

        logger.debug("loaded_tier4_advanced", count=49)

        # Get final count
        from src.services.infrastructure.agent_registry import AgentRegistry

        total = len(AgentRegistry.list_agents())
        by_tier = AgentRegistry.get_tier_summary()

        logger.info("agents_loaded_successfully", total=total, by_tier=by_tier)

        return total

    except Exception as e:
        logger.error("agent_loading_failed", error=str(e), exc_info=True)
        raise


# Auto-load on import
load_all_agents()
