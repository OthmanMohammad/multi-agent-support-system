"""
Trial Optimizer Agent - TASK-1042

Monitors trial usage, identifies low engagement, sends intervention messages,
and tracks conversion signals to maximize trial-to-paid conversion rates.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("trial_optimizer", tier="revenue", category="sales")
class TrialOptimizer(BaseAgent):
    """
    Trial Optimizer Agent - Specialist in optimizing trial experiences and conversions.

    Handles:
    - Trial usage monitoring and analytics
    - Low engagement identification
    - Intervention message triggers
    - Conversion signal tracking
    - Trial extension recommendations
    """

    # Engagement levels and thresholds
    ENGAGEMENT_THRESHOLDS = {
        "high": {
            "logins_per_week": 5,
            "features_used": 8,
            "data_uploaded": True,
            "team_invited": True,
            "conversion_probability": 0.75
        },
        "medium": {
            "logins_per_week": 3,
            "features_used": 4,
            "data_uploaded": True,
            "team_invited": False,
            "conversion_probability": 0.45
        },
        "low": {
            "logins_per_week": 1,
            "features_used": 2,
            "data_uploaded": False,
            "team_invited": False,
            "conversion_probability": 0.15
        },
        "at_risk": {
            "logins_per_week": 0,
            "features_used": 0,
            "data_uploaded": False,
            "team_invited": False,
            "conversion_probability": 0.05
        }
    }

    # Conversion signals (positive indicators)
    CONVERSION_SIGNALS = {
        "strong": [
            "invited_team_members",
            "integrated_production_data",
            "configured_custom_settings",
            "contacted_sales",
            "viewed_pricing_page",
            "asked_about_enterprise_features"
        ],
        "moderate": [
            "multiple_daily_logins",
            "explored_advanced_features",
            "created_custom_workflows",
            "downloaded_reports",
            "completed_onboarding"
        ],
        "weak": [
            "regular_logins",
            "basic_feature_usage",
            "viewed_documentation",
            "opened_support_tickets"
        ]
    }

    # At-risk indicators (negative signals)
    AT_RISK_INDICATORS = {
        "critical": [
            "no_login_7_days",
            "abandoned_onboarding",
            "unsubscribed_emails",
            "negative_support_feedback",
            "comparing_competitors"
        ],
        "warning": [
            "decreasing_usage_trend",
            "no_login_3_days",
            "stuck_on_feature",
            "incomplete_setup",
            "only_basic_features"
        ]
    }

    # Intervention strategies
    INTERVENTION_STRATEGIES = {
        "at_risk_rescue": {
            "trigger": "at_risk",
            "timing": "immediate",
            "channel": ["email", "phone"],
            "message_type": "personalized_help",
            "actions": [
                "Offer 1-on-1 onboarding session",
                "Provide setup assistance",
                "Identify blocking issues",
                "Extend trial if needed"
            ]
        },
        "low_engagement_boost": {
            "trigger": "low",
            "timing": "within_24_hours",
            "channel": ["email", "in_app"],
            "message_type": "feature_education",
            "actions": [
                "Send targeted feature tutorials",
                "Highlight unused capabilities",
                "Share relevant use cases",
                "Invite to webinar"
            ]
        },
        "medium_engagement_nurture": {
            "trigger": "medium",
            "timing": "every_3_days",
            "channel": ["email", "in_app"],
            "message_type": "value_reinforcement",
            "actions": [
                "Share success stories",
                "Suggest advanced features",
                "Provide optimization tips",
                "Check if questions exist"
            ]
        },
        "high_engagement_convert": {
            "trigger": "high",
            "timing": "strategic",
            "channel": ["email", "phone"],
            "message_type": "conversion_focused",
            "actions": [
                "Schedule pricing discussion",
                "Offer limited-time discount",
                "Discuss implementation plan",
                "Introduce account executive"
            ]
        }
    }

    # Trial milestones
    TRIAL_MILESTONES = {
        "day_1": {
            "goals": ["Complete profile", "Explore dashboard", "Try core feature"],
            "success_metric": "first_value_moment"
        },
        "day_3": {
            "goals": ["Upload data", "Create first workflow", "Invite team member"],
            "success_metric": "activation"
        },
        "day_7": {
            "goals": ["Use 5+ features", "Configure settings", "Generate first report"],
            "success_metric": "product_qualified_lead"
        },
        "day_14": {
            "goals": ["Daily active usage", "Advanced features", "Integration setup"],
            "success_metric": "conversion_ready"
        }
    }

    # Usage patterns by company size
    USAGE_BENCHMARKS = {
        "small": {
            "expected_logins_per_week": 4,
            "expected_features_used": 5,
            "typical_trial_length": 14
        },
        "medium": {
            "expected_logins_per_week": 6,
            "expected_features_used": 8,
            "typical_trial_length": 30
        },
        "large": {
            "expected_logins_per_week": 8,
            "expected_features_used": 12,
            "typical_trial_length": 45
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="trial_optimizer",
            type=AgentType.ANALYZER,
            model="claude-3-5-sonnet-20240620",
            temperature=0.3,
            max_tokens=1200,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process trial optimization request.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with trial optimization insights
        """
        self.logger.info("trial_optimizer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        trial_data = state.get("trial_data", {})

        self.logger.debug(
            "trial_optimization_details",
            trial_day=trial_data.get("days_in_trial", 0),
            engagement=trial_data.get("engagement_level", "unknown")
        )

        # Analyze trial usage
        usage_analysis = self._analyze_trial_usage(trial_data, customer_metadata)

        # Detect engagement level
        engagement_level = self._detect_engagement_level(trial_data)

        # Identify conversion signals
        conversion_signals = self._identify_conversion_signals(trial_data)

        # Detect at-risk indicators
        at_risk_indicators = self._detect_at_risk_indicators(trial_data)

        # Calculate conversion probability
        conversion_probability = self._calculate_conversion_probability(
            engagement_level,
            conversion_signals,
            at_risk_indicators,
            trial_data
        )

        # Determine intervention strategy
        intervention = self._determine_intervention(
            engagement_level,
            conversion_probability,
            trial_data
        )

        # Check milestone progress
        milestone_progress = self._check_milestone_progress(trial_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            engagement_level,
            conversion_probability,
            intervention,
            trial_data,
            customer_metadata
        )

        # Search KB for trial optimization best practices
        kb_results = await self.search_knowledge_base(
            f"trial optimization {engagement_level} engagement",
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_optimization_response(
            message,
            usage_analysis,
            engagement_level,
            conversion_probability,
            intervention,
            recommendations,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["engagement_level"] = engagement_level
        state["usage_analysis"] = usage_analysis
        state["conversion_signals"] = conversion_signals
        state["at_risk_indicators"] = at_risk_indicators
        state["conversion_probability"] = conversion_probability
        state["intervention_strategy"] = intervention
        state["milestone_progress"] = milestone_progress
        state["recommendations"] = recommendations
        state["deal_stage"] = "trial_active"
        state["status"] = "resolved"

        self.logger.info(
            "trial_optimizer_completed",
            engagement=engagement_level,
            conversion_probability=conversion_probability,
            intervention=intervention["trigger"]
        )

        return state

    def _analyze_trial_usage(
        self,
        trial_data: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Analyze trial usage patterns"""
        days_in_trial = trial_data.get("days_in_trial", 0)
        total_logins = trial_data.get("total_logins", 0)
        features_used = trial_data.get("features_used", [])

        # Calculate usage metrics
        logins_per_day = total_logins / max(days_in_trial, 1)
        logins_per_week = logins_per_day * 7
        features_used_count = len(features_used)

        # Get benchmark for company size
        company_size = customer_metadata.get("company_size", 50)
        if company_size < 50:
            benchmark = self.USAGE_BENCHMARKS["small"]
        elif company_size < 500:
            benchmark = self.USAGE_BENCHMARKS["medium"]
        else:
            benchmark = self.USAGE_BENCHMARKS["large"]

        # Compare to benchmarks
        login_performance = logins_per_week / benchmark["expected_logins_per_week"]
        feature_performance = features_used_count / benchmark["expected_features_used"]

        return {
            "days_in_trial": days_in_trial,
            "total_logins": total_logins,
            "logins_per_week": round(logins_per_week, 1),
            "features_used_count": features_used_count,
            "login_performance_vs_benchmark": round(login_performance, 2),
            "feature_performance_vs_benchmark": round(feature_performance, 2),
            "benchmark_category": "small" if company_size < 50 else "medium" if company_size < 500 else "large"
        }

    def _detect_engagement_level(self, trial_data: Dict) -> str:
        """Detect current engagement level"""
        logins_per_week = trial_data.get("logins_per_week", 0)
        features_used = len(trial_data.get("features_used", []))
        data_uploaded = trial_data.get("data_uploaded", False)
        team_invited = trial_data.get("team_invited", False)

        # Check thresholds in order
        if (logins_per_week >= self.ENGAGEMENT_THRESHOLDS["high"]["logins_per_week"] and
            features_used >= self.ENGAGEMENT_THRESHOLDS["high"]["features_used"]):
            return "high"
        elif (logins_per_week >= self.ENGAGEMENT_THRESHOLDS["medium"]["logins_per_week"] and
              features_used >= self.ENGAGEMENT_THRESHOLDS["medium"]["features_used"]):
            return "medium"
        elif (logins_per_week >= self.ENGAGEMENT_THRESHOLDS["low"]["logins_per_week"] or
              features_used >= self.ENGAGEMENT_THRESHOLDS["low"]["features_used"]):
            return "low"
        else:
            return "at_risk"

    def _identify_conversion_signals(self, trial_data: Dict) -> Dict[str, List[str]]:
        """Identify positive conversion signals"""
        signals = {
            "strong": [],
            "moderate": [],
            "weak": []
        }

        # Check for strong signals
        if trial_data.get("team_invited", False):
            signals["strong"].append("invited_team_members")
        if trial_data.get("data_uploaded", False):
            signals["strong"].append("integrated_production_data")
        if trial_data.get("viewed_pricing", False):
            signals["strong"].append("viewed_pricing_page")
        if trial_data.get("contacted_sales", False):
            signals["strong"].append("contacted_sales")

        # Check for moderate signals
        if trial_data.get("logins_per_week", 0) >= 5:
            signals["moderate"].append("multiple_daily_logins")
        if trial_data.get("onboarding_completed", False):
            signals["moderate"].append("completed_onboarding")
        if trial_data.get("custom_workflows", 0) > 0:
            signals["moderate"].append("created_custom_workflows")

        # Check for weak signals
        if trial_data.get("total_logins", 0) > 3:
            signals["weak"].append("regular_logins")
        if trial_data.get("viewed_docs", False):
            signals["weak"].append("viewed_documentation")

        return signals

    def _detect_at_risk_indicators(self, trial_data: Dict) -> Dict[str, List[str]]:
        """Detect at-risk indicators"""
        indicators = {
            "critical": [],
            "warning": []
        }

        days_since_last_login = trial_data.get("days_since_last_login", 0)

        # Critical indicators
        if days_since_last_login >= 7:
            indicators["critical"].append("no_login_7_days")
        if not trial_data.get("onboarding_completed", True):
            indicators["critical"].append("abandoned_onboarding")

        # Warning indicators
        if days_since_last_login >= 3:
            indicators["warning"].append("no_login_3_days")
        if trial_data.get("usage_trend", "stable") == "decreasing":
            indicators["warning"].append("decreasing_usage_trend")
        if len(trial_data.get("features_used", [])) <= 2:
            indicators["warning"].append("only_basic_features")

        return indicators

    def _calculate_conversion_probability(
        self,
        engagement_level: str,
        conversion_signals: Dict,
        at_risk_indicators: Dict,
        trial_data: Dict
    ) -> float:
        """Calculate probability of trial conversion"""
        # Start with base probability from engagement
        base_prob = self.ENGAGEMENT_THRESHOLDS[engagement_level]["conversion_probability"]

        # Adjust for conversion signals
        strong_signals = len(conversion_signals["strong"])
        moderate_signals = len(conversion_signals["moderate"])

        signal_boost = (strong_signals * 0.10) + (moderate_signals * 0.05)

        # Adjust for at-risk indicators
        critical_indicators = len(at_risk_indicators["critical"])
        warning_indicators = len(at_risk_indicators["warning"])

        risk_penalty = (critical_indicators * 0.15) + (warning_indicators * 0.05)

        # Calculate final probability
        final_prob = base_prob + signal_boost - risk_penalty

        return max(0.0, min(1.0, final_prob))  # Clamp between 0 and 1

    def _determine_intervention(
        self,
        engagement_level: str,
        conversion_probability: float,
        trial_data: Dict
    ) -> Dict[str, Any]:
        """Determine appropriate intervention strategy"""
        strategy_key = f"{engagement_level}_engagement"

        # Map engagement levels to intervention strategies
        strategy_mapping = {
            "at_risk": "at_risk_rescue",
            "low": "low_engagement_boost",
            "medium": "medium_engagement_nurture",
            "high": "high_engagement_convert"
        }

        strategy_name = strategy_mapping.get(engagement_level, "low_engagement_boost")
        strategy = self.INTERVENTION_STRATEGIES[strategy_name].copy()

        # Add urgency based on trial progress
        days_in_trial = trial_data.get("days_in_trial", 0)
        trial_length = trial_data.get("trial_length_days", 14)
        days_remaining = trial_length - days_in_trial

        if days_remaining <= 3:
            strategy["urgency"] = "high"
        elif days_remaining <= 7:
            strategy["urgency"] = "medium"
        else:
            strategy["urgency"] = "low"

        return strategy

    def _check_milestone_progress(self, trial_data: Dict) -> Dict[str, Any]:
        """Check progress against trial milestones"""
        days_in_trial = trial_data.get("days_in_trial", 0)

        progress = {}
        for milestone, details in self.TRIAL_MILESTONES.items():
            day_number = int(milestone.split("_")[1])

            if days_in_trial >= day_number:
                # Check if goals are met
                goals_met = 0
                total_goals = len(details["goals"])

                # Simple heuristic based on trial data
                if trial_data.get("profile_completed", False):
                    goals_met += 1
                if trial_data.get("data_uploaded", False):
                    goals_met += 1
                if trial_data.get("team_invited", False):
                    goals_met += 1

                progress[milestone] = {
                    "goals": details["goals"],
                    "goals_met": min(goals_met, total_goals),
                    "total_goals": total_goals,
                    "completion_rate": min(goals_met / total_goals, 1.0) if total_goals > 0 else 0.0,
                    "status": "complete" if goals_met >= total_goals else "incomplete"
                }

        return progress

    def _generate_recommendations(
        self,
        engagement_level: str,
        conversion_probability: float,
        intervention: Dict,
        trial_data: Dict,
        customer_metadata: Dict
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Based on engagement level
        if engagement_level == "at_risk":
            recommendations.extend([
                "URGENT: Call prospect within 24 hours",
                "Offer personalized onboarding session",
                "Identify and resolve blocking issues",
                "Consider trial extension"
            ])
        elif engagement_level == "low":
            recommendations.extend([
                "Send targeted feature tutorials",
                "Schedule check-in call",
                "Share relevant use case examples"
            ])
        elif engagement_level == "high":
            recommendations.extend([
                "Schedule pricing discussion",
                "Prepare custom proposal",
                "Introduce account executive",
                "Offer early adopter discount"
            ])

        # Based on conversion probability
        if conversion_probability > 0.7:
            recommendations.append("HIGH PRIORITY: Strong conversion candidate - fast-track to close")
        elif conversion_probability < 0.3:
            recommendations.append("Consider re-qualification or trial extension")

        # Based on trial progress
        days_remaining = trial_data.get("trial_length_days", 14) - trial_data.get("days_in_trial", 0)
        if days_remaining <= 3:
            recommendations.append(f"URGENT: Only {days_remaining} days remaining in trial")

        return recommendations

    async def _generate_optimization_response(
        self,
        message: str,
        usage_analysis: Dict,
        engagement_level: str,
        conversion_probability: float,
        intervention: Dict,
        recommendations: List[str],
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate trial optimization response"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nBest Practices:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Trial Optimizer specialist helping maximize trial conversions.

Trial Analysis:
- Engagement Level: {engagement_level.upper()}
- Conversion Probability: {conversion_probability:.0%}
- Days in Trial: {usage_analysis['days_in_trial']}
- Logins per Week: {usage_analysis['logins_per_week']}
- Features Used: {usage_analysis['features_used_count']}
- Performance vs Benchmark: {usage_analysis['login_performance_vs_benchmark']}x

Intervention Strategy: {intervention['message_type']}
Urgency: {intervention.get('urgency', 'medium')}

Company Profile:
- Company: {customer_metadata.get('company', 'Unknown')}
- Industry: {customer_metadata.get('industry', 'Unknown')}

Your response should:
1. Acknowledge their trial progress
2. Highlight value they've already received
3. Address engagement level appropriately
4. Suggest specific next steps
5. Create urgency if needed
6. Be helpful and supportive
7. Guide toward conversion if ready"""

        user_prompt = f"""Customer message: {message}

Usage Analysis:
- Login Performance: {usage_analysis['login_performance_vs_benchmark']}x benchmark
- Feature Performance: {usage_analysis['feature_performance_vs_benchmark']}x benchmark

Recommended Actions:
{chr(10).join(f"- {rec}" for rec in recommendations[:3])}

{kb_context}

Generate a helpful trial optimization response."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing TrialOptimizer Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: High engagement trial
        state1 = create_initial_state(
            "We've been using the trial for a week and the team loves it!",
            context={
                "customer_metadata": {
                    "company": "GrowthCo",
                    "title": "VP Product",
                    "company_size": 100,
                    "industry": "technology"
                },
                "trial_data": {
                    "days_in_trial": 7,
                    "trial_length_days": 14,
                    "total_logins": 35,
                    "logins_per_week": 6,
                    "features_used": ["dashboard", "reports", "api", "integrations", "analytics", "workflows", "automation", "alerts"],
                    "data_uploaded": True,
                    "team_invited": True,
                    "viewed_pricing": True,
                    "contacted_sales": True,
                    "onboarding_completed": True,
                    "days_since_last_login": 0,
                    "usage_trend": "increasing"
                }
            }
        )

        agent = TrialOptimizer()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - High Engagement Trial")
        print(f"Engagement Level: {result1['engagement_level']}")
        print(f"Conversion Probability: {result1['conversion_probability']:.0%}")
        print(f"Intervention: {result1['intervention_strategy']['message_type']}")
        print(f"Urgency: {result1['intervention_strategy'].get('urgency')}")
        print(f"Recommendations: {len(result1['recommendations'])}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: At-risk trial
        state2 = create_initial_state(
            "Just checking on trial status",
            context={
                "customer_metadata": {
                    "company": "StartupLabs",
                    "title": "Founder",
                    "company_size": 15,
                    "industry": "technology"
                },
                "trial_data": {
                    "days_in_trial": 10,
                    "trial_length_days": 14,
                    "total_logins": 2,
                    "logins_per_week": 0.7,
                    "features_used": ["dashboard"],
                    "data_uploaded": False,
                    "team_invited": False,
                    "viewed_pricing": False,
                    "contacted_sales": False,
                    "onboarding_completed": False,
                    "days_since_last_login": 8,
                    "usage_trend": "decreasing"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - At-Risk Trial")
        print(f"Engagement Level: {result2['engagement_level']}")
        print(f"Conversion Probability: {result2['conversion_probability']:.0%}")
        print(f"Intervention: {result2['intervention_strategy']['message_type']}")
        print(f"Urgency: {result2['intervention_strategy'].get('urgency')}")
        print(f"At-Risk Indicators: {sum(len(v) for v in result2['at_risk_indicators'].values())}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Medium engagement
        state3 = create_initial_state(
            "We're exploring the features and seeing some good value",
            context={
                "customer_metadata": {
                    "company": "MidMarket Inc",
                    "title": "Director of Operations",
                    "company_size": 200,
                    "industry": "retail"
                },
                "trial_data": {
                    "days_in_trial": 5,
                    "trial_length_days": 14,
                    "total_logins": 12,
                    "logins_per_week": 4,
                    "features_used": ["dashboard", "reports", "integrations", "analytics"],
                    "data_uploaded": True,
                    "team_invited": False,
                    "viewed_pricing": False,
                    "contacted_sales": False,
                    "onboarding_completed": True,
                    "days_since_last_login": 1,
                    "usage_trend": "stable"
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Medium Engagement")
        print(f"Engagement Level: {result3['engagement_level']}")
        print(f"Conversion Probability: {result3['conversion_probability']:.0%}")
        print(f"Strong Signals: {len(result3['conversion_signals']['strong'])}")
        print(f"Moderate Signals: {len(result3['conversion_signals']['moderate'])}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
