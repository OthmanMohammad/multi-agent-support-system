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

import importlib

import structlog

logger = structlog.get_logger(__name__)

# Track if agents have been loaded (prevent double loading)
_agents_loaded = False


def load_all_agents():
    """
    Import all agent modules to trigger registration.

    This function imports all agent packages, which triggers the
    @AgentRegistry.register() decorators in each agent module.
    """
    global _agents_loaded

    if _agents_loaded:
        logger.debug("agents_already_loaded", message="Skipping duplicate load")
        return 0

    logger.info("loading_all_agents", message="Starting agent registration")

    loaded_count = 0

    try:
        # =====================================================================
        # TIER 1: ESSENTIAL - Routing Agents
        # =====================================================================
        routing_modules = [
            "src.agents.essential.routing.meta_router",
            "src.agents.essential.routing.support_domain_router",
            "src.agents.essential.routing.sales_domain_router",
            "src.agents.essential.routing.cs_domain_router",
            "src.agents.essential.routing.intent_classifier",
            "src.agents.essential.routing.entity_extractor",
            "src.agents.essential.routing.sentiment_analyzer",
            "src.agents.essential.routing.escalation_decider",
            "src.agents.essential.routing.complexity_assessor",
            "src.agents.essential.routing.context_injector",
            "src.agents.essential.routing.coordinator",
            "src.agents.essential.routing.handoff_manager",
        ]
        for module_name in routing_modules:
            try:
                importlib.import_module(module_name)
                loaded_count += 1
            except ImportError as e:
                logger.debug("module_import_skipped", module=module_name, reason=str(e))

        logger.debug("loaded_tier1_routing", count=loaded_count)

        # =====================================================================
        # TIER 1: ESSENTIAL - Support Specialists
        # =====================================================================
        support_modules = [
            # Billing
            "src.agents.essential.support.billing.upgrade_specialist",
            "src.agents.essential.support.billing.refund_processor",
            "src.agents.essential.support.billing.payment_troubleshooter",
            "src.agents.essential.support.billing.invoice_generator",
            "src.agents.essential.support.billing.pricing_explainer",
            "src.agents.essential.support.billing.discount_negotiator",
            "src.agents.essential.support.billing.downgrade_specialist",
            # Technical
            "src.agents.essential.support.technical.bug_triager",
            "src.agents.essential.support.technical.crash_investigator",
            "src.agents.essential.support.technical.sync_troubleshooter",
            "src.agents.essential.support.technical.performance_optimizer",
            "src.agents.essential.support.technical.login_specialist",
            "src.agents.essential.support.technical.data_recovery_specialist",
            "src.agents.essential.support.technical.browser_compatibility_specialist",
            # Usage
            "src.agents.essential.support.usage.feature_teacher",
            "src.agents.essential.support.usage.onboarding_guide",
            "src.agents.essential.support.usage.workflow_optimizer",
            "src.agents.essential.support.usage.collaboration_expert",
            "src.agents.essential.support.usage.export_specialist",
            "src.agents.essential.support.usage.import_specialist",
            # Integration
            "src.agents.essential.support.integration.api_debugger",
            "src.agents.essential.support.integration.webhook_troubleshooter",
            "src.agents.essential.support.integration.oauth_specialist",
            "src.agents.essential.support.integration.sdk_expert",
            "src.agents.essential.support.integration.rate_limit_advisor",
            # Account
            "src.agents.essential.support.account.account_deletion_specialist",
            "src.agents.essential.support.account.profile_manager",
            "src.agents.essential.support.account.team_manager",
            "src.agents.essential.support.account.permission_manager",
            "src.agents.essential.support.account.security_advisor",
            "src.agents.essential.support.account.sso_specialist",
            "src.agents.essential.support.account.data_export_specialist",
            "src.agents.essential.support.account.notification_configurator",
            "src.agents.essential.support.account.audit_log_specialist",
            "src.agents.essential.support.account.compliance_specialist",
        ]
        support_count = 0
        for module_name in support_modules:
            try:
                importlib.import_module(module_name)
                loaded_count += 1
                support_count += 1
            except ImportError as e:
                logger.debug("module_import_skipped", module=module_name, reason=str(e))

        logger.debug("loaded_tier1_support", count=support_count)

        # =====================================================================
        # TIER 2: REVENUE - Sales Agents
        # =====================================================================
        sales_modules = [
            # Lead Qualification
            "src.agents.revenue.sales.lead_qualification.inbound_qualifier",
            "src.agents.revenue.sales.lead_qualification.bant_qualifier",
            "src.agents.revenue.sales.lead_qualification.lead_scorer",
            "src.agents.revenue.sales.lead_qualification.mql_to_sql_converter",
            "src.agents.revenue.sales.lead_qualification.referral_detector",
            "src.agents.revenue.sales.lead_qualification.disqualification_agent",
            # Product Education
            "src.agents.revenue.sales.product_education.feature_explainer",
            "src.agents.revenue.sales.product_education.demo_preparer",
            "src.agents.revenue.sales.product_education.use_case_matcher",
            "src.agents.revenue.sales.product_education.roi_calculator",
            "src.agents.revenue.sales.product_education.value_proposition",
            # Objection Handling
            "src.agents.revenue.sales.objection_handling.price_objection_handler",
            "src.agents.revenue.sales.objection_handling.competitor_comparison_handler",
            "src.agents.revenue.sales.objection_handling.integration_objection_handler",
            "src.agents.revenue.sales.objection_handling.security_objection_handler",
            "src.agents.revenue.sales.objection_handling.timing_objection_handler",
            "src.agents.revenue.sales.objection_handling.feature_gap_handler",
            # Deal Progression
            "src.agents.revenue.sales.deal_progression.closer",
            "src.agents.revenue.sales.deal_progression.trial_optimizer",
            "src.agents.revenue.sales.deal_progression.proposal_generator",
            "src.agents.revenue.sales.deal_progression.contract_negotiator",
            "src.agents.revenue.sales.deal_progression.demo_scheduler",
            "src.agents.revenue.sales.deal_progression.upsell_identifier",
            # Competitive Intelligence
            "src.agents.revenue.sales.competitive_intelligence.competitor_tracker",
            "src.agents.revenue.sales.competitive_intelligence.feature_comparator",
            "src.agents.revenue.sales.competitive_intelligence.pricing_analyzer",
            "src.agents.revenue.sales.competitive_intelligence.migration_specialist",
            "src.agents.revenue.sales.competitive_intelligence.positioning_advisor",
            "src.agents.revenue.sales.competitive_intelligence.review_analyzer",
            "src.agents.revenue.sales.competitive_intelligence.sentiment_tracker",
        ]
        sales_count = 0
        for module_name in sales_modules:
            try:
                importlib.import_module(module_name)
                loaded_count += 1
                sales_count += 1
            except ImportError as e:
                logger.debug("module_import_skipped", module=module_name, reason=str(e))

        logger.debug("loaded_tier2_sales", count=sales_count)

        # =====================================================================
        # TIER 2: REVENUE - Customer Success Agents
        # =====================================================================
        cs_modules = [
            # Health Monitoring
            "src.agents.revenue.customer_success.health_monitoring.health_score",
            "src.agents.revenue.customer_success.health_monitoring.engagement_tracker",
            "src.agents.revenue.customer_success.health_monitoring.usage_analyzer",
            "src.agents.revenue.customer_success.health_monitoring.risk_detector",
            "src.agents.revenue.customer_success.health_monitoring.trend_analyzer",
            # Onboarding
            "src.agents.revenue.customer_success.onboarding.onboarding_coordinator",
            "src.agents.revenue.customer_success.onboarding.setup_guide",
            "src.agents.revenue.customer_success.onboarding.milestone_tracker",
            "src.agents.revenue.customer_success.onboarding.integration_helper",
            "src.agents.revenue.customer_success.onboarding.training_scheduler",
            "src.agents.revenue.customer_success.onboarding.success_criteria_definer",
            # Adoption
            "src.agents.revenue.customer_success.adoption.feature_adoption",
            "src.agents.revenue.customer_success.adoption.usage_optimizer",
            "src.agents.revenue.customer_success.adoption.best_practice_advisor",
            "src.agents.revenue.customer_success.adoption.workflow_consultant",
            "src.agents.revenue.customer_success.adoption.power_user_identifier",
            "src.agents.revenue.customer_success.adoption.adoption_gap_finder",
            # Retention
            "src.agents.revenue.customer_success.retention.renewal_manager",
            "src.agents.revenue.customer_success.retention.churn_preventer",
            "src.agents.revenue.customer_success.retention.win_back_specialist",
            "src.agents.revenue.customer_success.retention.satisfaction_surveyor",
            "src.agents.revenue.customer_success.retention.escalation_handler",
            # Expansion
            "src.agents.revenue.customer_success.expansion.upsell_identifier",
            "src.agents.revenue.customer_success.expansion.cross_sell_advisor",
            "src.agents.revenue.customer_success.expansion.growth_planner",
            "src.agents.revenue.customer_success.expansion.roi_demonstrator",
            "src.agents.revenue.customer_success.expansion.expansion_timing_advisor",
            # Relationship
            "src.agents.revenue.customer_success.relationship.account_manager",
            "src.agents.revenue.customer_success.relationship.executive_sponsor",
            "src.agents.revenue.customer_success.relationship.qbr_preparer",
            "src.agents.revenue.customer_success.relationship.stakeholder_mapper",
            "src.agents.revenue.customer_success.relationship.feedback_collector",
            "src.agents.revenue.customer_success.relationship.advocate_developer",
            "src.agents.revenue.customer_success.relationship.reference_builder",
            "src.agents.revenue.customer_success.relationship.case_study_creator",
        ]
        cs_count = 0
        for module_name in cs_modules:
            try:
                importlib.import_module(module_name)
                loaded_count += 1
                cs_count += 1
            except ImportError as e:
                logger.debug("module_import_skipped", module=module_name, reason=str(e))

        logger.debug("loaded_tier2_customer_success", count=cs_count)

        # Get final count from registry
        from src.services.infrastructure.agent_registry import AgentRegistry

        total = len(AgentRegistry.list_agents())
        by_tier = AgentRegistry.get_tier_summary()

        logger.info("agents_loaded_successfully", total=total, by_tier=by_tier, modules_loaded=loaded_count)

        _agents_loaded = True
        return total

    except Exception as e:
        logger.error("agent_loading_failed", error=str(e), exc_info=True)
        raise


# Auto-load on import
load_all_agents()
