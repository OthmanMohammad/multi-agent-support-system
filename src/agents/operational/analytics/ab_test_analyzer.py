"""
A/B Test Analyzer Agent - TASK-2017

Performs statistical analysis of A/B tests using Chi-square test and other methods.
Determines statistical significance (p<0.05) and provides actionable insights.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import math

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("ab_test_analyzer", tier="operational", category="analytics")
class ABTestAnalyzerAgent(BaseAgent):
    """
    A/B Test Analyzer Agent.

    Performs rigorous statistical analysis of A/B tests:
    - Chi-square test for categorical outcomes
    - T-test for continuous outcomes
    - Sample size and power analysis
    - Confidence interval calculation
    - Statistical significance determination (p<0.05)
    - Effect size measurement
    - Recommendations on test validity and next steps
    """

    # Statistical constants
    SIGNIFICANCE_LEVEL = 0.05  # α = 0.05 (95% confidence)
    MINIMUM_SAMPLE_SIZE = 100
    MINIMUM_CONVERSION_EVENTS = 10

    # Effect size thresholds (Cohen's h for proportions)
    EFFECT_SIZE_THRESHOLDS = {
        "small": 0.2,
        "medium": 0.5,
        "large": 0.8
    }

    def __init__(self):
        config = AgentConfig(
            name="ab_test_analyzer",
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            max_tokens=1500,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze A/B test results.

        Args:
            state: Current agent state with test data

        Returns:
            Updated state with statistical analysis
        """
        self.logger.info("ab_test_analysis_started")

        state = self.update_state(state)

        # Extract test data
        test_name = state.get("entities", {}).get("test_name", "Unknown Test")
        variant_a = state.get("entities", {}).get("variant_a", {})
        variant_b = state.get("entities", {}).get("variant_b", {})
        metric_type = state.get("entities", {}).get("metric_type", "conversion")  # conversion or continuous

        self.logger.debug(
            "ab_test_analysis_details",
            test_name=test_name,
            metric_type=metric_type,
            variant_a_size=variant_a.get("sample_size", 0)
        )

        # Validate test data
        validation_result = self._validate_test_data(variant_a, variant_b, metric_type)

        if not validation_result["valid"]:
            response = self._format_validation_error(test_name, validation_result)
            state["agent_response"] = response
            state["status"] = "resolved"
            state["response_confidence"] = 0.95
            return state

        # Perform statistical test
        if metric_type == "conversion":
            test_results = self._perform_chi_square_test(variant_a, variant_b)
        else:  # continuous metric
            test_results = self._perform_t_test(variant_a, variant_b)

        # Calculate effect size
        effect_size = self._calculate_effect_size(variant_a, variant_b, metric_type)

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(variant_a, variant_b, metric_type)

        # Determine winner and recommendations
        conclusion = self._determine_conclusion(test_results, effect_size)
        recommendations = self._generate_recommendations(
            test_results,
            effect_size,
            variant_a,
            variant_b
        )

        # Format response
        response = self._format_ab_test_report(
            test_name,
            variant_a,
            variant_b,
            test_results,
            effect_size,
            confidence_intervals,
            conclusion,
            recommendations,
            metric_type
        )

        state["agent_response"] = response
        state["test_results"] = test_results
        state["effect_size"] = effect_size
        state["conclusion"] = conclusion
        state["recommendations"] = recommendations
        state["is_significant"] = test_results["is_significant"]
        state["response_confidence"] = 0.93
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "ab_test_analysis_completed",
            test_name=test_name,
            is_significant=test_results["is_significant"],
            winner=conclusion.get("winner", "none")
        )

        return state

    def _validate_test_data(
        self,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        metric_type: str
    ) -> Dict[str, Any]:
        """
        Validate A/B test data.

        Args:
            variant_a: Variant A data
            variant_b: Variant B data
            metric_type: Type of metric

        Returns:
            Validation result
        """
        issues = []

        # Check sample sizes
        sample_a = variant_a.get("sample_size", 0)
        sample_b = variant_b.get("sample_size", 0)

        if sample_a < self.MINIMUM_SAMPLE_SIZE:
            issues.append(f"Variant A sample size ({sample_a}) below minimum ({self.MINIMUM_SAMPLE_SIZE})")

        if sample_b < self.MINIMUM_SAMPLE_SIZE:
            issues.append(f"Variant B sample size ({sample_b}) below minimum ({self.MINIMUM_SAMPLE_SIZE})")

        # Check conversion events for conversion tests
        if metric_type == "conversion":
            conversions_a = variant_a.get("conversions", 0)
            conversions_b = variant_b.get("conversions", 0)

            if conversions_a < self.MINIMUM_CONVERSION_EVENTS:
                issues.append(f"Variant A has insufficient conversions ({conversions_a})")

            if conversions_b < self.MINIMUM_CONVERSION_EVENTS:
                issues.append(f"Variant B has insufficient conversions ({conversions_b})")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def _perform_chi_square_test(
        self,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform Chi-square test for conversion rates.

        Args:
            variant_a: Variant A data
            variant_b: Variant B data

        Returns:
            Chi-square test results
        """
        # Extract data
        n_a = variant_a.get("sample_size", 0)
        conversions_a = variant_a.get("conversions", 0)
        n_b = variant_b.get("sample_size", 0)
        conversions_b = variant_b.get("conversions", 0)

        # Calculate conversion rates
        rate_a = (conversions_a / n_a) if n_a > 0 else 0
        rate_b = (conversions_b / n_b) if n_b > 0 else 0

        # Calculate pooled probability
        total_conversions = conversions_a + conversions_b
        total_sample = n_a + n_b
        pooled_probability = total_conversions / total_sample if total_sample > 0 else 0

        # Calculate standard error
        se = math.sqrt(pooled_probability * (1 - pooled_probability) * (1/n_a + 1/n_b))

        # Calculate z-score
        z_score = (rate_b - rate_a) / se if se > 0 else 0

        # Calculate p-value (two-tailed)
        # Using normal approximation
        p_value = self._calculate_p_value_from_z(abs(z_score))

        # Determine significance
        is_significant = p_value < self.SIGNIFICANCE_LEVEL

        return {
            "test_type": "chi_square",
            "variant_a_rate": round(rate_a * 100, 2),
            "variant_b_rate": round(rate_b * 100, 2),
            "absolute_difference": round((rate_b - rate_a) * 100, 2),
            "relative_lift": round(((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0, 2),
            "z_score": round(z_score, 3),
            "p_value": round(p_value, 4),
            "is_significant": is_significant,
            "confidence_level": 95
        }

    def _perform_t_test(
        self,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform t-test for continuous metrics.

        Args:
            variant_a: Variant A data
            variant_b: Variant B data

        Returns:
            T-test results
        """
        # Extract data
        mean_a = variant_a.get("mean", 0)
        std_a = variant_a.get("std_dev", 1)
        n_a = variant_a.get("sample_size", 0)

        mean_b = variant_b.get("mean", 0)
        std_b = variant_b.get("std_dev", 1)
        n_b = variant_b.get("sample_size", 0)

        # Calculate pooled standard deviation
        pooled_var = ((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2)
        pooled_std = math.sqrt(pooled_var)

        # Calculate standard error
        se = pooled_std * math.sqrt(1/n_a + 1/n_b)

        # Calculate t-statistic
        t_stat = (mean_b - mean_a) / se if se > 0 else 0

        # Degrees of freedom
        df = n_a + n_b - 2

        # Calculate p-value (approximate using normal distribution for large samples)
        p_value = self._calculate_p_value_from_z(abs(t_stat))

        # Determine significance
        is_significant = p_value < self.SIGNIFICANCE_LEVEL

        return {
            "test_type": "t_test",
            "variant_a_mean": round(mean_a, 2),
            "variant_b_mean": round(mean_b, 2),
            "absolute_difference": round(mean_b - mean_a, 2),
            "relative_lift": round(((mean_b - mean_a) / mean_a * 100) if mean_a > 0 else 0, 2),
            "t_statistic": round(t_stat, 3),
            "degrees_of_freedom": df,
            "p_value": round(p_value, 4),
            "is_significant": is_significant,
            "confidence_level": 95
        }

    def _calculate_p_value_from_z(self, z: float) -> float:
        """
        Calculate two-tailed p-value from z-score using normal approximation.

        Args:
            z: Z-score (absolute value)

        Returns:
            P-value
        """
        # Simple approximation using error function
        # For production, use scipy.stats.norm.sf(z) * 2
        if z > 6:
            return 0.0001

        # Approximate cumulative distribution
        t = 1 / (1 + 0.2316419 * z)
        d = 0.3989423 * math.exp(-z * z / 2)
        prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))

        return 2 * prob  # Two-tailed

    def _calculate_effect_size(
        self,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        metric_type: str
    ) -> Dict[str, Any]:
        """
        Calculate effect size.

        Args:
            variant_a: Variant A data
            variant_b: Variant B data
            metric_type: Metric type

        Returns:
            Effect size analysis
        """
        if metric_type == "conversion":
            # Cohen's h for proportions
            n_a = variant_a.get("sample_size", 0)
            conversions_a = variant_a.get("conversions", 0)
            n_b = variant_b.get("sample_size", 0)
            conversions_b = variant_b.get("conversions", 0)

            p_a = conversions_a / n_a if n_a > 0 else 0
            p_b = conversions_b / n_b if n_b > 0 else 0

            # Cohen's h
            h = 2 * (math.asin(math.sqrt(p_b)) - math.asin(math.sqrt(p_a)))

            effect_size_value = abs(h)

        else:
            # Cohen's d for continuous metrics
            mean_a = variant_a.get("mean", 0)
            std_a = variant_a.get("std_dev", 1)
            n_a = variant_a.get("sample_size", 0)

            mean_b = variant_b.get("mean", 0)
            std_b = variant_b.get("std_dev", 1)
            n_b = variant_b.get("sample_size", 0)

            # Pooled standard deviation
            pooled_std = math.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))

            # Cohen's d
            d = (mean_b - mean_a) / pooled_std if pooled_std > 0 else 0

            effect_size_value = abs(d)

        # Classify effect size
        if effect_size_value >= self.EFFECT_SIZE_THRESHOLDS["large"]:
            magnitude = "large"
        elif effect_size_value >= self.EFFECT_SIZE_THRESHOLDS["medium"]:
            magnitude = "medium"
        elif effect_size_value >= self.EFFECT_SIZE_THRESHOLDS["small"]:
            magnitude = "small"
        else:
            magnitude = "negligible"

        return {
            "value": round(effect_size_value, 3),
            "magnitude": magnitude,
            "interpretation": f"{magnitude.title()} practical significance"
        }

    def _calculate_confidence_intervals(
        self,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        metric_type: str
    ) -> Dict[str, Any]:
        """
        Calculate confidence intervals for the difference.

        Args:
            variant_a: Variant A data
            variant_b: Variant B data
            metric_type: Metric type

        Returns:
            Confidence intervals
        """
        z_95 = 1.96  # 95% confidence

        if metric_type == "conversion":
            n_a = variant_a.get("sample_size", 0)
            conversions_a = variant_a.get("conversions", 0)
            n_b = variant_b.get("sample_size", 0)
            conversions_b = variant_b.get("conversions", 0)

            p_a = conversions_a / n_a if n_a > 0 else 0
            p_b = conversions_b / n_b if n_b > 0 else 0

            # Standard error of difference
            se = math.sqrt((p_a * (1 - p_a) / n_a) + (p_b * (1 - p_b) / n_b))

            diff = p_b - p_a
            margin = z_95 * se

            return {
                "difference": round(diff * 100, 2),
                "lower_bound": round((diff - margin) * 100, 2),
                "upper_bound": round((diff + margin) * 100, 2),
                "confidence_level": 95
            }

        else:
            mean_a = variant_a.get("mean", 0)
            std_a = variant_a.get("std_dev", 1)
            n_a = variant_a.get("sample_size", 0)

            mean_b = variant_b.get("mean", 0)
            std_b = variant_b.get("std_dev", 1)
            n_b = variant_b.get("sample_size", 0)

            # Standard error of difference
            se = math.sqrt((std_a**2 / n_a) + (std_b**2 / n_b))

            diff = mean_b - mean_a
            margin = z_95 * se

            return {
                "difference": round(diff, 2),
                "lower_bound": round(diff - margin, 2),
                "upper_bound": round(diff + margin, 2),
                "confidence_level": 95
            }

    def _determine_conclusion(
        self,
        test_results: Dict[str, Any],
        effect_size: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine test conclusion and winner.

        Args:
            test_results: Statistical test results
            effect_size: Effect size analysis

        Returns:
            Conclusion
        """
        is_significant = test_results.get("is_significant", False)
        relative_lift = test_results.get("relative_lift", 0)

        if not is_significant:
            return {
                "winner": "none",
                "decision": "No significant difference detected",
                "action": "Continue testing or conclude no difference"
            }

        # Determine winner
        if relative_lift > 0:
            winner = "variant_b"
            decision = f"Variant B wins with {abs(relative_lift):.2f}% lift"
        else:
            winner = "variant_a"
            decision = f"Variant A wins with {abs(relative_lift):.2f}% lift"

        # Consider effect size
        if effect_size["magnitude"] == "negligible":
            action = "Statistically significant but practically negligible - consider business impact"
        elif effect_size["magnitude"] == "small":
            action = "Small but significant effect - evaluate against implementation cost"
        else:
            action = f"Implement winning variant - {effect_size['magnitude']} practical impact"

        return {
            "winner": winner,
            "decision": decision,
            "action": action,
            "effect_magnitude": effect_size["magnitude"]
        }

    def _generate_recommendations(
        self,
        test_results: Dict[str, Any],
        effect_size: Dict[str, Any],
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if test_results["is_significant"]:
            recommendations.append(
                f"Test is statistically significant (p={test_results['p_value']:.4f} < 0.05)"
            )
            recommendations.append(
                f"Effect size is {effect_size['magnitude']} ({effect_size['interpretation']})"
            )

            if test_results["relative_lift"] > 0:
                recommendations.append(
                    f"Implement Variant B for {abs(test_results['relative_lift']):.1f}% improvement"
                )
            else:
                recommendations.append(
                    f"Keep Variant A (control) - it performs {abs(test_results['relative_lift']):.1f}% better"
                )
        else:
            recommendations.append(
                f"No significant difference found (p={test_results['p_value']:.4f} >= 0.05)"
            )
            recommendations.append(
                "Options: (1) Continue testing with more samples, (2) Conclude variants are equivalent"
            )

        return recommendations

    def _format_validation_error(
        self,
        test_name: str,
        validation_result: Dict[str, Any]
    ) -> str:
        """Format validation error message."""
        report = f"""**A/B Test Analysis: {test_name}**

**VALIDATION FAILED**

The test data does not meet minimum requirements for statistical analysis:

"""
        for issue in validation_result["issues"]:
            report += f"- {issue}\n"

        report += f"\n**Recommendations:**\n"
        report += f"- Continue collecting data until minimum sample sizes are met\n"
        report += f"- Ensure sufficient conversion events for reliable analysis\n"

        return report

    def _format_ab_test_report(
        self,
        test_name: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        test_results: Dict[str, Any],
        effect_size: Dict[str, Any],
        confidence_intervals: Dict[str, Any],
        conclusion: Dict[str, Any],
        recommendations: List[str],
        metric_type: str
    ) -> str:
        """Format A/B test analysis report."""
        report = f"""**A/B Test Analysis: {test_name}**

**Test Configuration:**
- Metric Type: {metric_type.title()}
- Significance Level: α = {self.SIGNIFICANCE_LEVEL}
- Confidence Level: 95%

**Sample Sizes:**
- Variant A (Control): {variant_a.get('sample_size', 0):,}
- Variant B (Treatment): {variant_b.get('sample_size', 0):,}

**Results:**
"""

        # Variant performance
        if metric_type == "conversion":
            report += f"- Variant A Conversion: {test_results['variant_a_rate']}%\n"
            report += f"- Variant B Conversion: {test_results['variant_b_rate']}%\n"
        else:
            report += f"- Variant A Mean: {test_results['variant_a_mean']}\n"
            report += f"- Variant B Mean: {test_results['variant_b_mean']}\n"

        report += f"- Absolute Difference: {test_results['absolute_difference']}\n"
        report += f"- Relative Lift: {test_results['relative_lift']:+.2f}%\n"

        # Statistical significance
        significance_icon = "✅" if test_results["is_significant"] else "❌"
        report += f"\n**Statistical Significance:** {significance_icon}\n"
        report += f"- P-value: {test_results['p_value']:.4f}\n"
        report += f"- Significant: {'Yes' if test_results['is_significant'] else 'No'} (p {'<' if test_results['is_significant'] else '>='} 0.05)\n"

        # Effect size
        report += f"\n**Effect Size:**\n"
        report += f"- Magnitude: {effect_size['magnitude'].title()}\n"
        report += f"- Value: {effect_size['value']:.3f}\n"
        report += f"- Interpretation: {effect_size['interpretation']}\n"

        # Confidence interval
        report += f"\n**95% Confidence Interval:**\n"
        report += f"- Difference: {confidence_intervals['difference']}\n"
        report += f"- CI: [{confidence_intervals['lower_bound']}, {confidence_intervals['upper_bound']}]\n"

        # Conclusion
        winner_icon = "🏆" if conclusion["winner"] != "none" else "🤝"
        report += f"\n**Conclusion:** {winner_icon}\n"
        report += f"- Winner: {conclusion['winner'].replace('_', ' ').title()}\n"
        report += f"- Decision: {conclusion['decision']}\n"
        report += f"- Recommended Action: {conclusion['action']}\n"

        # Recommendations
        report += f"\n**Recommendations:**\n"
        for rec in recommendations:
            report += f"- {rec}\n"

        report += f"\n*Analysis completed at {datetime.utcnow().isoformat()}*"

        return report
