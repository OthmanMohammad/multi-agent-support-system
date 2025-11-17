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
        from src.agents.essential.routing import (
            meta_router,
            intent_classifier,
            entity_extractor,
            sentiment_analyzer,
            support_domain_router,
            sales_domain_router,
            cs_domain_router,
            complexity_assessor,
            coordinator,
            handoff_manager,
            escalation_decider,
            context_injector,
        )
        logger.debug("loaded_tier1_routing", count=12)

        from src.agents.essential.knowledge_base import (
            searcher,
            ranker,
            synthesizer,
            feedback_tracker,
            quality_checker,
            updater,
            gap_detector,
            suggester,
            faq_generator,
            embedder,
        )
        logger.debug("loaded_tier1_kb", count=10)

        # Tier 1: Support Specialists
        from src.agents.essential.support.billing import (
            upgrade_specialist,
            downgrade_specialist,
            refund_processor,
            invoice_generator,
            payment_troubleshooter,
            pricing_explainer,
            discount_negotiator,
        )
        logger.debug("loaded_tier1_billing", count=7)

        from src.agents.essential.support.technical import (
            bug_triager,
            crash_investigator,
            sync_troubleshooter,
            performance_optimizer,
            login_specialist,
            data_recovery_specialist,
            browser_compatibility_specialist,
        )
        logger.debug("loaded_tier1_technical", count=7)

        from src.agents.essential.support.usage import (
            feature_teacher,
            workflow_optimizer,
            export_specialist,
            import_specialist,
            collaboration_expert,
            onboarding_guide,
        )
        logger.debug("loaded_tier1_usage", count=6)

        from src.agents.essential.support.integration import (
            api_debugger,
            oauth_specialist,
            rate_limit_advisor,
            sdk_expert,
            webhook_troubleshooter,
        )
        logger.debug("loaded_tier1_integration", count=5)

        from src.agents.essential.support.account import (
            ProfileManager,
            TeamManager,
            SecurityAdvisor,
            SSOSpecialist,
            PermissionManager,
            DataExportSpecialist,
            AccountDeletionSpecialist,
            ComplianceSpecialist,
            AuditLogSpecialist,
            NotificationConfigurator,
        )
        logger.debug("loaded_tier1_account", count=10)

        # Tier 2: Revenue (import all revenue agents)
        # Note: Add all revenue agent imports here
        logger.debug("loaded_tier2_revenue", note="Add imports")

        # Tier 3: Operational (import all operational agents)
        # Note: Add all operational agent imports here
        logger.debug("loaded_tier3_operational", note="Add imports")

        # Tier 4: Advanced (import all advanced agents)
        # Note: Add all advanced agent imports here
        logger.debug("loaded_tier4_advanced", note="Add imports")

        # Get final count
        from src.services.infrastructure.agent_registry import AgentRegistry
        total = len(AgentRegistry.list_agents())
        by_tier = AgentRegistry.get_tier_summary()

        logger.info(
            "agents_loaded_successfully",
            total=total,
            by_tier=by_tier
        )

        return total

    except Exception as e:
        logger.error(
            "agent_loading_failed",
            error=str(e),
            exc_info=True
        )
        raise


# Auto-load on import
load_all_agents()