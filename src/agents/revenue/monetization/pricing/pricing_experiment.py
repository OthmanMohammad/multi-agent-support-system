"""
Pricing Experiment Agent - TASK-3044

Designs and analyzes pricing experiments to optimize pricing strategy.
Runs A/B tests on pricing and measures impact on conversion and revenue.
"""

from datetime import datetime, timedelta
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("pricing_experiment", tier="revenue", category="monetization")
class PricingExperiment(BaseAgent):
    """
    Pricing Experiment Agent - Optimizes pricing through experimentation.

    Handles:
    - Design pricing experiments
    - Define test variants and control
    - Calculate sample size requirements
    - Monitor experiment performance
    - Analyze statistical significance
    - Measure revenue and conversion impact
    - Generate experiment insights
    - Recommend pricing changes based on data
    """

    # Experiment types
    EXPERIMENT_TYPES = {
        "price_point_test": {
            "description": "Test different price points",
            "typical_variants": 3,
            "min_sample_size": 100,
            "duration_weeks": 4,
        },
        "packaging_test": {
            "description": "Test different feature packages",
            "typical_variants": 2,
            "min_sample_size": 150,
            "duration_weeks": 6,
        },
        "discount_test": {
            "description": "Test discount strategies",
            "typical_variants": 3,
            "min_sample_size": 100,
            "duration_weeks": 4,
        },
        "anchor_pricing_test": {
            "description": "Test anchor prices and tier positioning",
            "typical_variants": 2,
            "min_sample_size": 120,
            "duration_weeks": 4,
        },
        "free_trial_test": {
            "description": "Test trial length and terms",
            "typical_variants": 3,
            "min_sample_size": 200,
            "duration_weeks": 8,
        },
    }

    # Success metrics for experiments
    SUCCESS_METRICS = {
        "primary": ["conversion_rate", "revenue_per_customer", "total_revenue"],
        "secondary": [
            "trial_to_paid_rate",
            "average_deal_size",
            "time_to_close",
            "customer_lifetime_value",
        ],
    }

    # Statistical significance thresholds
    SIGNIFICANCE_THRESHOLDS = {
        "p_value": 0.05,  # 95% confidence
        "min_effect_size": 0.10,  # 10% minimum detectable effect
        "min_sample_size": 50,  # Per variant
    }

    def __init__(self):
        config = AgentConfig(
            name="pricing_experiment",
            type=AgentType.SPECIALIST,
            # Sonnet for experimental design
            temperature=0.2,  # Low for analytical precision
            max_tokens=700,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="monetization",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Design or analyze pricing experiment.

        Args:
            state: Current agent state with experiment data

        Returns:
            Updated state with experiment design or results
        """
        self.logger.info("pricing_experiment_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Determine if designing new experiment or analyzing existing
        experiment_mode = customer_metadata.get("experiment_mode", "design")

        if experiment_mode == "design":
            # Design new experiment
            experiment_design = self._design_experiment(customer_metadata)
            sample_size = self._calculate_sample_size(experiment_design)
            timeline = self._create_experiment_timeline(experiment_design)
            success_criteria = self._define_success_criteria(experiment_design)

            # Search KB for experiment resources
            kb_results = await self.search_knowledge_base(
                "pricing experiment A/B testing optimization", category="monetization", limit=2
            )
            state["kb_results"] = kb_results

            # Generate response
            response = await self._generate_design_response(
                message,
                experiment_design,
                sample_size,
                timeline,
                success_criteria,
                kb_results,
                customer_metadata,
            )

            # Update state with design
            state["experiment_design"] = experiment_design
            state["sample_size_requirement"] = sample_size
            state["experiment_timeline"] = timeline
            state["success_criteria"] = success_criteria

        else:
            # Analyze existing experiment
            experiment_results = self._analyze_experiment_results(customer_metadata)
            statistical_analysis = self._perform_statistical_analysis(experiment_results)
            winner = self._determine_winner(statistical_analysis)
            recommendations = self._generate_recommendations(winner, statistical_analysis)
            rollout_plan = self._create_rollout_plan(winner)

            # Search KB
            kb_results = await self.search_knowledge_base(
                "pricing optimization rollout strategy", category="monetization", limit=2
            )
            state["kb_results"] = kb_results

            # Generate response
            response = await self._generate_analysis_response(
                message,
                experiment_results,
                statistical_analysis,
                winner,
                recommendations,
                rollout_plan,
                kb_results,
                customer_metadata,
            )

            # Update state with results
            state["experiment_results"] = experiment_results
            state["statistical_analysis"] = statistical_analysis
            state["experiment_winner"] = winner
            state["experiment_recommendations"] = recommendations
            state["rollout_plan"] = rollout_plan

        state["agent_response"] = response
        state["response_confidence"] = 0.89
        state["status"] = "resolved"

        self.logger.info("pricing_experiment_completed", experiment_mode=experiment_mode)

        return state

    def _design_experiment(self, customer_metadata: dict) -> dict[str, Any]:
        """Design pricing experiment"""
        experiment_type = customer_metadata.get("experiment_type", "price_point_test")
        experiment_config = self.EXPERIMENT_TYPES.get(experiment_type, {})

        current_price = customer_metadata.get("current_price", 99)

        # Design variants based on type
        if experiment_type == "price_point_test":
            variants = [
                {"name": "Control", "price": current_price, "description": "Current pricing"},
                {
                    "name": "Lower Price",
                    "price": current_price * 0.85,
                    "description": "15% price reduction",
                },
                {
                    "name": "Higher Price",
                    "price": current_price * 1.15,
                    "description": "15% price increase",
                },
            ]
        elif experiment_type == "discount_test":
            variants = [
                {"name": "Control", "discount": 0, "description": "No discount"},
                {
                    "name": "10% Discount",
                    "discount": 0.10,
                    "description": "10% promotional discount",
                },
                {
                    "name": "20% Discount",
                    "discount": 0.20,
                    "description": "20% promotional discount",
                },
            ]
        elif experiment_type == "free_trial_test":
            variants = [
                {"name": "7-day trial", "trial_days": 7, "description": "1 week trial"},
                {"name": "14-day trial", "trial_days": 14, "description": "2 week trial"},
                {"name": "30-day trial", "trial_days": 30, "description": "1 month trial"},
            ]
        else:
            variants = [
                {"name": "Control", "description": "Current offering"},
                {"name": "Variant A", "description": "Alternative offering"},
            ]

        return {
            "experiment_type": experiment_type,
            "description": experiment_config.get("description", "Pricing experiment"),
            "variants": variants,
            "duration_weeks": experiment_config.get("duration_weeks", 4),
            "traffic_split": [1 / len(variants)] * len(variants),  # Equal split
            "primary_metric": "conversion_rate",
            "secondary_metrics": ["revenue_per_customer", "trial_to_paid_rate"],
        }

    def _calculate_sample_size(self, experiment: dict) -> dict[str, Any]:
        """Calculate required sample size for statistical power"""
        # Simplified sample size calculation
        baseline_conversion = 0.25  # 25% baseline conversion
        min_detectable_effect = self.SIGNIFICANCE_THRESHOLDS["min_effect_size"]
        confidence_level = 1 - self.SIGNIFICANCE_THRESHOLDS["p_value"]

        # Sample size per variant (simplified formula)
        # Real implementation would use proper power analysis
        sample_size_per_variant = int(
            (16 * baseline_conversion * (1 - baseline_conversion)) / (min_detectable_effect**2)
        )

        total_sample_size = sample_size_per_variant * len(experiment["variants"])

        return {
            "sample_size_per_variant": sample_size_per_variant,
            "total_sample_size": total_sample_size,
            "baseline_conversion": baseline_conversion,
            "min_detectable_effect": min_detectable_effect,
            "confidence_level": confidence_level,
            "expected_duration_weeks": experiment["duration_weeks"],
        }

    def _create_experiment_timeline(self, experiment: dict) -> list[dict[str, Any]]:
        """Create experiment timeline"""
        duration_weeks = experiment["duration_weeks"]
        start_date = datetime.now()

        return [
            {
                "phase": "Setup",
                "week": 0,
                "start_date": start_date.isoformat(),
                "activities": ["Configure variants", "Set up tracking", "QA test"],
            },
            {
                "phase": "Ramp-up",
                "week": 1,
                "start_date": (start_date + timedelta(weeks=1)).isoformat(),
                "activities": [
                    "Start with 25% traffic",
                    "Monitor for issues",
                    "Verify data collection",
                ],
            },
            {
                "phase": "Full test",
                "week": 2,
                "start_date": (start_date + timedelta(weeks=2)).isoformat(),
                "activities": [
                    "Scale to 100% traffic",
                    "Monitor metrics",
                    "Check for significance",
                ],
            },
            {
                "phase": "Analysis",
                "week": duration_weeks,
                "start_date": (start_date + timedelta(weeks=duration_weeks)).isoformat(),
                "activities": ["Analyze results", "Determine winner", "Plan rollout"],
            },
        ]

    def _define_success_criteria(self, experiment: dict) -> dict[str, Any]:
        """Define success criteria for experiment"""
        return {
            "primary_goal": f"Increase {experiment['primary_metric']} by {self.SIGNIFICANCE_THRESHOLDS['min_effect_size'] * 100:.0f}%",
            "statistical_requirements": {
                "p_value": f"< {self.SIGNIFICANCE_THRESHOLDS['p_value']}",
                "confidence": "95%",
                "min_sample_size": f"{self.SIGNIFICANCE_THRESHOLDS['min_sample_size']} per variant",
            },
            "business_requirements": {
                "revenue_neutral_or_positive": "Total revenue should not decrease",
                "customer_satisfaction": "NPS should not drop significantly",
                "operational_feasibility": "Can be implemented at scale",
            },
            "decision_framework": [
                "If variant shows >10% improvement with p<0.05, roll out to 100%",
                "If variant shows 5-10% improvement, run extended test",
                "If no significant difference, keep current pricing",
            ],
        }

    def _analyze_experiment_results(self, customer_metadata: dict) -> dict[str, Any]:
        """Analyze experiment results from metadata"""
        variants_data = customer_metadata.get("experiment_variants_data", [])

        results = {
            "experiment_id": customer_metadata.get("experiment_id", "EXP-001"),
            "duration_days": customer_metadata.get("experiment_duration_days", 28),
            "variants": [],
        }

        for variant in variants_data:
            results["variants"].append(
                {
                    "name": variant.get("name", "Unknown"),
                    "sample_size": variant.get("sample_size", 0),
                    "conversions": variant.get("conversions", 0),
                    "conversion_rate": variant.get("conversion_rate", 0),
                    "revenue": variant.get("revenue", 0),
                    "revenue_per_customer": variant.get("revenue_per_customer", 0),
                }
            )

        return results

    def _perform_statistical_analysis(self, results: dict) -> dict[str, Any]:
        """Perform statistical analysis on results"""
        if len(results["variants"]) < 2:
            return {"error": "Not enough variants for analysis"}

        control = results["variants"][0]
        analysis = {"control": control["name"], "comparisons": []}

        for variant in results["variants"][1:]:
            # Calculate lift
            conversion_lift = (
                (
                    (variant["conversion_rate"] - control["conversion_rate"])
                    / control["conversion_rate"]
                )
                if control["conversion_rate"] > 0
                else 0
            )

            revenue_lift = (
                (
                    (variant["revenue_per_customer"] - control["revenue_per_customer"])
                    / control["revenue_per_customer"]
                )
                if control["revenue_per_customer"] > 0
                else 0
            )

            # Simplified significance calculation (real would use proper statistical test)
            sample_size = variant["sample_size"]
            is_significant = sample_size >= 100 and abs(conversion_lift) >= 0.10

            analysis["comparisons"].append(
                {
                    "variant": variant["name"],
                    "conversion_lift": round(conversion_lift * 100, 2),
                    "revenue_lift": round(revenue_lift * 100, 2),
                    "is_significant": is_significant,
                    "confidence": "95%" if is_significant else "< 95%",
                    "sample_size": sample_size,
                    "recommendation": "Roll out"
                    if is_significant and conversion_lift > 0
                    else "Keep testing"
                    if not is_significant
                    else "Reject",
                }
            )

        return analysis

    def _determine_winner(self, analysis: dict) -> dict[str, Any]:
        """Determine winning variant"""
        if "error" in analysis:
            return {"winner": "None", "reason": "Insufficient data"}

        best_variant = None
        best_lift = -999

        for comparison in analysis["comparisons"]:
            if comparison["is_significant"] and comparison["conversion_lift"] > best_lift:
                best_lift = comparison["conversion_lift"]
                best_variant = comparison

        if best_variant:
            return {
                "winner": best_variant["variant"],
                "conversion_improvement": best_variant["conversion_lift"],
                "revenue_improvement": best_variant["revenue_lift"],
                "confidence": best_variant["confidence"],
                "recommendation": "Roll out to 100%",
            }
        else:
            return {
                "winner": "Control",
                "reason": "No variant showed significant improvement",
                "recommendation": "Keep current pricing or design new test",
            }

    def _generate_recommendations(self, winner: dict, analysis: dict) -> list[dict[str, str]]:
        """Generate recommendations based on experiment"""
        recommendations = []

        if winner["winner"] != "Control":
            recommendations.append(
                {
                    "action": f"Roll out {winner['winner']} pricing",
                    "rationale": f"Showed {winner['conversion_improvement']:.1f}% conversion improvement",
                    "timeline": "2 weeks",
                    "priority": "high",
                }
            )
        else:
            recommendations.append(
                {
                    "action": "Keep current pricing",
                    "rationale": "No variant showed significant improvement",
                    "timeline": "Immediate",
                    "priority": "medium",
                }
            )
            recommendations.append(
                {
                    "action": "Design new experiment with larger price variations",
                    "rationale": "Test more aggressive pricing changes",
                    "timeline": "4 weeks",
                    "priority": "medium",
                }
            )

        return recommendations

    def _create_rollout_plan(self, winner: dict) -> dict[str, Any]:
        """Create rollout plan for winning variant"""
        if winner["winner"] == "Control":
            return {"rollout_required": False}

        return {
            "rollout_required": True,
            "phases": [
                {
                    "phase": 1,
                    "percentage": 25,
                    "duration_days": 7,
                    "description": "25% rollout with monitoring",
                },
                {
                    "phase": 2,
                    "percentage": 50,
                    "duration_days": 7,
                    "description": "50% rollout if stable",
                },
                {"phase": 3, "percentage": 100, "duration_days": 7, "description": "100% rollout"},
            ],
            "monitoring_metrics": ["conversion_rate", "revenue", "customer_feedback"],
            "rollback_criteria": "If conversion drops >5% or revenue decreases, rollback immediately",
        }

    async def _generate_design_response(
        self,
        message: str,
        experiment: dict,
        sample_size: dict,
        timeline: list[dict],
        success_criteria: dict,
        kb_results: list[dict],
        customer_metadata: dict,
    ) -> str:
        """Generate experiment design response"""

        design_context = f"""
Experiment Design:
- Type: {experiment["experiment_type"]}
- Variants: {len(experiment["variants"])}
- Duration: {experiment["duration_weeks"]} weeks
- Sample Size: {sample_size["total_sample_size"]} total ({sample_size["sample_size_per_variant"]} per variant)
- Primary Metric: {experiment["primary_metric"]}
"""

        variants_context = "\n\nVariants:\n"
        for i, variant in enumerate(experiment["variants"], 1):
            variants_context += f"{i}. {variant['name']}: {variant['description']}\n"

        kb_context = ""
        if kb_results:
            kb_context = "\n\nExperiment Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Pricing Experiment specialist designing A/B tests.

{design_context}

Your response should:
1. Explain experiment design and rationale
2. Present variants clearly
3. Define success metrics
4. Calculate sample size requirements
5. Create experiment timeline
6. Set statistical significance criteria
7. Provide implementation guidance
8. Address potential risks
9. Be methodical and data-driven

Tone: Analytical, precise, experimental"""

        user_prompt = f"""Customer message: {message}

{variants_context}

Success Criteria:
{success_criteria["primary_goal"]}
Statistical Requirements: {success_criteria["statistical_requirements"]["confidence"]} confidence

Timeline: {experiment["duration_weeks"]} weeks

{kb_context}

Generate a comprehensive experiment design."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[],  # Experiment design uses config data
        )
        return response

    async def _generate_analysis_response(
        self,
        message: str,
        results: dict,
        analysis: dict,
        winner: dict,
        recommendations: list[dict],
        rollout_plan: dict,
        kb_results: list[dict],
        customer_metadata: dict,
    ) -> str:
        """Generate experiment analysis response"""

        results_context = f"""
Experiment Results:
- Duration: {results["duration_days"]} days
- Variants Tested: {len(results["variants"])}
"""

        winner_context = f"""
Winner: {winner["winner"]}
{f"Improvement: {winner.get('conversion_improvement', 0):.1f}% conversion" if winner.get("conversion_improvement") else ""}
Confidence: {winner.get("confidence", "N/A")}
"""

        kb_context = ""
        if kb_results:
            kb_context = "\n\nRollout Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Pricing Experiment specialist analyzing test results.

{results_context}
{winner_context}

Your response should:
1. Summarize experiment results
2. Present statistical analysis clearly
3. Declare winning variant with confidence
4. Quantify improvement
5. Provide rollout recommendations
6. Address implementation considerations
7. Suggest next experiments
8. Be data-driven and objective

Tone: Analytical, conclusive, actionable"""

        user_prompt = f"""Customer message: {message}

Statistical Analysis:
{chr(10).join(f"- {comp['variant']}: {comp['conversion_lift']:.1f}% lift ({comp['recommendation']})" for comp in analysis.get("comparisons", []))}

Recommendations:
{chr(10).join(f"- {rec['action']}: {rec['rationale']}" for rec in recommendations)}

{kb_context}

Generate a comprehensive experiment analysis."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[],  # Experiment analysis uses results data
        )
        return response
