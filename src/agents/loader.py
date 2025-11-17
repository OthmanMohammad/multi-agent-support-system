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
        # Customer Success - Adoption (6 agents)
        from src.agents.revenue.customer_success.adoption import (
            automation_coach,
            best_practices,
            feature_adoption,
            integration_advocate,
            power_user_enablement,
            user_activation,
        )

        # Customer Success - Expansion (5 agents)
        from src.agents.revenue.customer_success.expansion import (
            cross_sell,
            department_expansion,
            expansion_roi,
            upsell_identifier as cs_upsell_identifier,  # Alias to avoid conflict
            usage_based_expansion,
        )

        # Customer Success - Health Monitoring (5 agents)
        from src.agents.revenue.customer_success.health_monitoring import (
            churn_predictor as cs_churn_predictor,  # Alias to avoid conflict
            health_score,
            nps_tracker,
            risk_alert,
            usage_monitor,
        )

        # Customer Success - Onboarding (6 agents)
        from src.agents.revenue.customer_success.onboarding import (
            data_migration,
            kickoff_facilitator,
            onboarding_coordinator,
            progress_tracker,
            success_validator,
            training_scheduler,
        )

        # Customer Success - Relationship (8 agents)
        from src.agents.revenue.customer_success.relationship import (
            advocacy_builder,
            champion_cultivator,
            community_manager,
            customer_insights,
            executive_sponsor,
            qbr_scheduler,
            relationship_health,
            success_plan,
        )

        # Customer Success - Retention (5 agents)
        from src.agents.revenue.customer_success.retention import (
            feedback_loop,
            loyalty_program,
            renewal_manager,
            save_team_coordinator,
            win_back,
        )

        # Monetization - Add-ons (5 agents)
        from src.agents.revenue.monetization.add_ons import (
            add_on_recommender,
            adoption_tracker,
            premium_support_seller,
            prof_services_seller,
            training_seller,
        )

        # Monetization - Expansion (5 agents)
        from src.agents.revenue.monetization.expansion import (
            land_and_expand,
            multi_year_deal,
            plan_upgrade,
            seat_expansion,
            white_space_analyzer,
        )

        # Monetization - Pricing (5 agents)
        from src.agents.revenue.monetization.pricing import (
            discount_manager,
            pricing_analyzer as mon_pricing_analyzer,  # Alias to avoid conflict
            pricing_experiment,
            revenue_forecaster,
            value_metric_optimizer,
        )

        # Monetization - Usage Billing (5 agents)
        from src.agents.revenue.monetization.usage_billing import (
            billing_calculator,
            dispute_resolver,
            overage_alert,
            usage_optimizer,
            usage_tracker,
        )

        # Sales - Competitive Intelligence (7 agents)
        from src.agents.revenue.sales.competitive_intelligence import (
            competitor_tracker as sales_competitor_tracker,  # Alias to avoid conflict
            feature_comparator as sales_feature_comparator,  # Alias to avoid conflict
            migration_specialist,
            positioning_advisor as sales_positioning_advisor,  # Alias to avoid conflict
            pricing_analyzer as sales_pricing_analyzer,  # Alias to avoid conflict
            review_analyzer as sales_review_analyzer,  # Alias to avoid conflict
            sentiment_tracker as sales_sentiment_tracker,  # Alias to avoid conflict
        )

        # Sales - Deal Progression (6 agents)
        from src.agents.revenue.sales.deal_progression import (
            closer,
            contract_negotiator,
            demo_scheduler,
            proposal_generator,
            trial_optimizer,
            upsell_identifier as sales_upsell_identifier,  # Alias to avoid conflict
        )

        # Sales - Lead Qualification (6 agents)
        from src.agents.revenue.sales.lead_qualification import (
            bant_qualifier,
            disqualification_agent,
            inbound_qualifier,
            lead_scorer,
            mql_to_sql_converter,
            referral_detector,
        )

        # Sales - Objection Handling (6 agents)
        from src.agents.revenue.sales.objection_handling import (
            competitor_comparison_handler,
            feature_gap_handler,
            integration_objection_handler,
            price_objection_handler,
            security_objection_handler,
            timing_objection_handler,
        )

        # Sales - Product Education (5 agents)
        from src.agents.revenue.sales.product_education import (
            demo_preparer,
            feature_explainer,
            roi_calculator,
            use_case_matcher,
            value_proposition,
        )

        logger.debug("loaded_tier2_revenue", count=85)

        # Tier 3: Operational (import all operational agents)
        # Analytics (12 agents) - Import class names from __init__.py
        from src.agents.operational.analytics import (
            ABTestAnalyzerAgent,
            AnomalyDetectorAgent,
            CohortAnalyzerAgent,
            CorrelationFinderAgent,
            DashboardGeneratorAgent,
            FunnelAnalyzerAgent,
            InsightSummarizerAgent,
            MetricsTrackerAgent,
            PredictionExplainerAgent,
            QueryBuilderAgent,
            ReportGeneratorAgent,
            TrendAnalyzerAgent,
        )

        # Automation - Data Automation (5 agents) - Import class names
        from src.agents.operational.automation.data_automation import (
            ContactEnricherAgent,
            CRMUpdaterAgent,
            DataValidatorAgent,
            DeduplicatorAgent,
            ReportAutomatorAgent,
        )

        # Automation - Process Automation (10 agents) - Import class names
        from src.agents.operational.automation.process_automation import (
            ApprovalRouterAgent,
            CleanupSchedulerAgent,
            DataBackupAgent,
            HandoffAutomatorAgent,
            InvoiceSenderAgent,
            OnboardingAutomatorAgent,
            PaymentRetryAgent,
            RenewalProcessorAgent,
            SLAEnforcerAgent,
            WorkflowExecutorAgent,
        )

        # Automation - Task Automation (5 agents) - Import class names
        from src.agents.operational.automation.task_automation import (
            CalendarSchedulerAgent,
            EmailSenderAgent,
            NotificationSenderAgent,
            ReminderSenderAgent,
            TicketCreatorAgent,
        )

        # QA (10 agents) - Import class names
        from src.agents.operational.qa import (
            CitationValidatorAgent,
            CodeValidatorAgent,
            CompletenessCheckerAgent,
            FactCheckerAgent,
            HallucinationDetectorAgent,
            LinkCheckerAgent,
            PolicyCheckerAgent,
            ResponseVerifierAgent,
            SensitivityCheckerAgent,
            ToneCheckerAgent,
        )

        # Security (10 agents) - Import class names
        from src.agents.operational.security import (
            AccessControllerAgent,
            AuditLoggerAgent,
            ComplianceCheckerAgent,
            ConsentManagerAgent,
            DataRetentionEnforcerAgent,
            EncryptionValidatorAgent,
            IncidentResponderAgent,
            PenTestCoordinatorAgent,
            PIIDetectorAgent,
            VulnerabilityScannerAgent,
        )

        logger.debug("loaded_tier3_operational", count=52)

        # Tier 4: Advanced (import all advanced agents)
        # Competitive (10 agents) - Import class names
        from src.agents.advanced.competitive import (
            BattlecardUpdaterAgent,
            CompetitorTrackerAgent,
            FeatureComparatorAgent,
            MigrationStrategistAgent,
            PositioningAdvisorAgent,
            PricingAnalyzerAgent as AdvPricingAnalyzerAgent,  # Alias to avoid conflict
            ReviewAnalyzerAgent as AdvReviewAnalyzerAgent,  # Alias to avoid conflict
            SentimentTrackerAgent as AdvSentimentTrackerAgent,  # Alias to avoid conflict
            ThreatAssessorAgent,
            WinLossAnalyzerAgent,
        )

        # Content (10 agents) - Import class names
        from src.agents.advanced.content import (
            BlogPostWriterAgent,
            CaseStudyCreatorAgent,
            ChangelogWriterAgent,
            DocumentationWriterAgent,
            EmailTemplateCreatorAgent,
            FAQGeneratorAgent,
            KBArticleWriterAgent,
            SalesCollateralCreatorAgent,
            SocialMediaWriterAgent,
            TutorialCreatorAgent,
        )

        # Learning (10 agents) - Import class names
        from src.agents.advanced.learning import (
            ABTestDesignerAgent,
            ConversationAnalyzerAgent,
            FeedbackProcessorAgent,
            ImprovementSuggesterAgent,
            KnowledgeGapIdentifierAgent,
            MistakeDetectorAgent,
            ModelFineTunerAgent,
            PerformanceTrackerAgent,
            PromptOptimizerAgent,
            RoutingOptimizerAgent,
        )

        # Personalization (9 agents) - Import class names
        from src.agents.advanced.personalization import (
            ChannelOptimizerAgent,
            ContentRecommenderAgent,
            EmpathyAdjusterAgent,
            JourneyPersonalizerAgent,
            LanguageAdapterAgent,
            PersonaIdentifierAgent,
            PreferenceLearnerAgent,
            ResponsePersonalizerAgent,
            TimingOptimizerAgent,
        )

        # Predictive (10 agents) - Import class names
        from src.agents.advanced.predictive import (
            BugPredictorAgent,
            CapacityPredictorAgent,
            ChurnPredictorAgent as AdvChurnPredictorAgent,  # Alias to avoid conflict
            ConversionPredictorAgent,
            FeatureDemandPredictorAgent,
            LTVPredictorAgent,
            RenewalPredictorAgent,
            SentimentPredictorAgent,
            SupportVolumePredictorAgent,
            UpsellPredictorAgent,
        )

        logger.debug("loaded_tier4_advanced", count=49)

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