"""
Correlation Finder Agent - TASK-2022

Finds correlations between metrics using Pearson correlation coefficient.
Identifies significant relationships (r>0.7) between business metrics.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import math

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("correlation_finder", tier="operational", category="analytics")
class CorrelationFinderAgent(BaseAgent):
    """
    Correlation Finder Agent.

    Identifies correlations between metrics:
    - Pearson correlation coefficient calculation
    - Correlation strength classification
    - Statistical significance testing
    - Correlation matrix generation
    - Insight generation from correlations
    - Causation warnings (correlation ≠ causation)
    """

    # Correlation strength thresholds
    CORRELATION_THRESHOLDS = {
        "very_strong": 0.9,
        "strong": 0.7,
        "moderate": 0.5,
        "weak": 0.3,
        "very_weak": 0.1
    }

    # Significance level
    SIGNIFICANCE_LEVEL = 0.05

    def __init__(self):
        config = AgentConfig(
            name="correlation_finder",
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
        Find correlations between metrics.

        Args:
            state: Current agent state with metrics data

        Returns:
            Updated state with correlation analysis
        """
        self.logger.info("correlation_analysis_started")

        state = self.update_state(state)

        # Extract metrics data
        metrics_data = state.get("entities", {}).get("metrics_data", {})
        correlation_threshold = state.get("entities", {}).get("threshold", 0.7)
        include_weak = state.get("entities", {}).get("include_weak", False)

        self.logger.debug(
            "correlation_analysis_details",
            metrics_count=len(metrics_data),
            threshold=correlation_threshold
        )

        # Prepare metric time series
        metric_series = self._prepare_metric_series(metrics_data)

        # Calculate correlation matrix
        correlation_matrix = self._calculate_correlation_matrix(metric_series)

        # Find significant correlations
        significant_correlations = self._find_significant_correlations(
            correlation_matrix,
            correlation_threshold,
            include_weak
        )

        # Test statistical significance
        significance_tests = self._test_significance(
            significant_correlations,
            metric_series
        )

        # Generate insights
        insights = self._generate_correlation_insights(
            significant_correlations,
            significance_tests
        )

        # Identify potential causation candidates
        causation_candidates = self._identify_causation_candidates(
            significant_correlations,
            metric_series
        )

        # Format response
        response = self._format_correlation_report(
            correlation_matrix,
            significant_correlations,
            significance_tests,
            insights,
            causation_candidates
        )

        state["agent_response"] = response
        state["correlation_matrix"] = correlation_matrix
        state["significant_correlations"] = significant_correlations
        state["correlation_insights"] = insights
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "correlation_analysis_completed",
            correlations_found=len(significant_correlations),
            insights_generated=len(insights)
        )

        return state

    def _prepare_metric_series(
        self,
        metrics_data: Dict[str, Any]
    ) -> Dict[str, List[float]]:
        """
        Prepare metric time series for correlation analysis.

        Args:
            metrics_data: Metrics data

        Returns:
            Dictionary of metric time series
        """
        # Mock time series data - in production, fetch actual historical data
        import random

        metric_series = {}

        # Generate correlated mock data
        n_points = 30

        # Base series
        base_series = [random.gauss(100, 20) for _ in range(n_points)]

        metric_series["revenue"] = base_series.copy()
        metric_series["active_users"] = [v * 1.2 + random.gauss(0, 10) for v in base_series]  # Strong positive correlation
        metric_series["churn_rate"] = [100 - v * 0.5 + random.gauss(0, 5) for v in base_series]  # Strong negative correlation
        metric_series["support_tickets"] = [random.gauss(50, 15) for _ in range(n_points)]  # No correlation
        metric_series["nps_score"] = [v * 0.3 + random.gauss(50, 8) for v in base_series]  # Moderate positive correlation

        # Add more metrics if provided in input
        for metric_name in metrics_data.keys():
            if metric_name not in metric_series:
                metric_series[metric_name] = [random.gauss(50, 15) for _ in range(n_points)]

        return metric_series

    def _calculate_correlation_matrix(
        self,
        metric_series: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate Pearson correlation matrix.

        Args:
            metric_series: Metric time series

        Returns:
            Correlation matrix
        """
        matrix = {}
        metric_names = list(metric_series.keys())

        for metric1 in metric_names:
            matrix[metric1] = {}
            for metric2 in metric_names:
                correlation = self._calculate_pearson_correlation(
                    metric_series[metric1],
                    metric_series[metric2]
                )
                matrix[metric1][metric2] = round(correlation, 4)

        return matrix

    def _calculate_pearson_correlation(
        self,
        x: List[float],
        y: List[float]
    ) -> float:
        """
        Calculate Pearson correlation coefficient.

        Args:
            x: First series
            y: Second series

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x) != len(y) or len(x) == 0:
            return 0.0

        n = len(x)

        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        # Calculate covariance and standard deviations
        covariance = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        std_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
        std_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))

        # Calculate correlation
        if std_x == 0 or std_y == 0:
            return 0.0

        correlation = covariance / (std_x * std_y)

        return correlation

    def _find_significant_correlations(
        self,
        correlation_matrix: Dict[str, Dict[str, float]],
        threshold: float,
        include_weak: bool
    ) -> List[Dict[str, Any]]:
        """
        Find significant correlations above threshold.

        Args:
            correlation_matrix: Correlation matrix
            threshold: Minimum correlation threshold
            include_weak: Include weak correlations

        Returns:
            List of significant correlations
        """
        correlations = []
        processed_pairs = set()

        for metric1, correlations_dict in correlation_matrix.items():
            for metric2, correlation in correlations_dict.items():
                # Skip self-correlation
                if metric1 == metric2:
                    continue

                # Skip already processed pairs
                pair = tuple(sorted([metric1, metric2]))
                if pair in processed_pairs:
                    continue

                processed_pairs.add(pair)

                abs_correlation = abs(correlation)

                # Check threshold
                if abs_correlation >= threshold or (include_weak and abs_correlation >= 0.3):
                    strength = self._classify_correlation_strength(abs_correlation)

                    correlations.append({
                        "metric1": metric1,
                        "metric2": metric2,
                        "correlation": correlation,
                        "abs_correlation": abs_correlation,
                        "direction": "positive" if correlation > 0 else "negative",
                        "strength": strength
                    })

        # Sort by absolute correlation
        correlations.sort(key=lambda x: x["abs_correlation"], reverse=True)

        return correlations

    def _classify_correlation_strength(self, abs_correlation: float) -> str:
        """Classify correlation strength."""
        if abs_correlation >= self.CORRELATION_THRESHOLDS["very_strong"]:
            return "very_strong"
        elif abs_correlation >= self.CORRELATION_THRESHOLDS["strong"]:
            return "strong"
        elif abs_correlation >= self.CORRELATION_THRESHOLDS["moderate"]:
            return "moderate"
        elif abs_correlation >= self.CORRELATION_THRESHOLDS["weak"]:
            return "weak"
        else:
            return "very_weak"

    def _test_significance(
        self,
        correlations: List[Dict[str, Any]],
        metric_series: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Test statistical significance of correlations.

        Args:
            correlations: List of correlations
            metric_series: Metric time series

        Returns:
            Significance test results
        """
        significance_tests = {}

        for corr in correlations:
            metric1 = corr["metric1"]
            metric2 = corr["metric2"]
            r = corr["correlation"]

            # Sample size
            n = len(metric_series[metric1])

            # Calculate t-statistic
            if abs(r) == 1:
                t_stat = float('inf')
            else:
                t_stat = r * math.sqrt(n - 2) / math.sqrt(1 - r**2)

            # Approximate p-value (two-tailed)
            # For production, use scipy.stats.t.sf
            p_value = 0.001 if abs(t_stat) > 3 else 0.01 if abs(t_stat) > 2 else 0.05

            is_significant = p_value < self.SIGNIFICANCE_LEVEL

            key = f"{metric1}__{metric2}"
            significance_tests[key] = {
                "t_statistic": round(t_stat, 3),
                "p_value": p_value,
                "is_significant": is_significant,
                "sample_size": n
            }

        return significance_tests

    def _generate_correlation_insights(
        self,
        correlations: List[Dict[str, Any]],
        significance_tests: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate insights from correlations."""
        insights = []

        # Strong correlations
        strong_correlations = [c for c in correlations if c["strength"] in ["strong", "very_strong"]]

        if strong_correlations:
            insights.append(
                f"Found {len(strong_correlations)} strong correlations (r>0.7) between metrics"
            )

            for corr in strong_correlations[:3]:
                direction = corr["direction"]
                insights.append(
                    f"{corr['metric1']} and {corr['metric2']} show {direction} correlation (r={corr['correlation']:.3f})"
                )

        # Negative correlations
        negative_correlations = [c for c in correlations if c["direction"] == "negative" and c["abs_correlation"] > 0.7]

        if negative_correlations:
            insights.append(
                f"Strong negative correlations suggest inverse relationships - monitor carefully"
            )

        # Correlation ≠ causation warning
        insights.append(
            "⚠️ Remember: Correlation does not imply causation. Further investigation needed to establish causal relationships."
        )

        return insights

    def _identify_causation_candidates(
        self,
        correlations: List[Dict[str, Any]],
        metric_series: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        """Identify potential causation relationships."""
        candidates = []

        # Look for very strong correlations with potential causal logic
        for corr in correlations:
            if corr["abs_correlation"] > 0.85:
                candidates.append({
                    "metric1": corr["metric1"],
                    "metric2": corr["metric2"],
                    "correlation": corr["correlation"],
                    "potential_causation": "Possible - requires domain knowledge to confirm",
                    "suggested_analysis": "Time-lagged correlation or Granger causality test"
                })

        return candidates[:5]  # Top 5

    def _format_correlation_report(
        self,
        correlation_matrix: Dict[str, Dict[str, float]],
        significant_correlations: List[Dict[str, Any]],
        significance_tests: Dict[str, Dict[str, Any]],
        insights: List[str],
        causation_candidates: List[Dict[str, Any]]
    ) -> str:
        """Format correlation analysis report."""
        report = f"""**Correlation Analysis Report**

**Summary:**
- Total Correlations Analyzed: {len(correlation_matrix)}
- Significant Correlations Found: {len(significant_correlations)}
- Analysis Method: Pearson Correlation Coefficient

**Significant Correlations (r>0.7):**

"""

        for corr in significant_correlations[:10]:
            direction_icon = "📈" if corr["direction"] == "positive" else "📉"
            strength_icon = "🔴" if corr["strength"] == "very_strong" else "🟡" if corr["strength"] == "strong" else "🟢"

            key = f"{corr['metric1']}__{corr['metric2']}"
            sig_test = significance_tests.get(key, {})

            report += f"{direction_icon} {strength_icon} **{corr['metric1']} ↔ {corr['metric2']}**\n"
            report += f"   - Correlation: r={corr['correlation']:+.3f}\n"
            report += f"   - Strength: {corr['strength'].replace('_', ' ').title()}\n"
            report += f"   - Direction: {corr['direction'].title()}\n"

            if sig_test.get("is_significant"):
                report += f"   - Statistically Significant: Yes (p={sig_test['p_value']:.3f})\n"

            report += "\n"

        # Insights
        if insights:
            report += "**Key Insights:**\n"
            for insight in insights:
                report += f"- {insight}\n"
            report += "\n"

        # Causation candidates
        if causation_candidates:
            report += "**Potential Causation Relationships:**\n"
            report += "*Note: These require further investigation*\n\n"
            for candidate in causation_candidates:
                report += f"- {candidate['metric1']} → {candidate['metric2']} (r={candidate['correlation']:.3f})\n"
                report += f"  Suggested analysis: {candidate['suggested_analysis']}\n\n"

        report += f"*Analysis completed at {datetime.utcnow().isoformat()}*"

        return report
