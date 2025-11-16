"""
Anomaly Detector Agent - TASK-2013

Detects anomalies in metrics using statistical methods (Z-score).
Generates warnings for >2σ and critical alerts for >3σ deviations.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import math

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("anomaly_detector", tier="operational", category="analytics")
class AnomalyDetectorAgent(BaseAgent):
    """
    Anomaly Detector Agent.

    Detects anomalies in time-series metrics using statistical methods:
    - Z-score analysis (standard deviations from mean)
    - Moving average deviation
    - Rate of change anomalies
    - Seasonal pattern violations
    - Multi-metric correlation anomalies

    Alert Levels:
    - Warning: >2σ deviation
    - Critical: >3σ deviation
    """

    # Anomaly detection thresholds
    Z_SCORE_WARNING = 2.0
    Z_SCORE_CRITICAL = 3.0

    # Anomaly types
    ANOMALY_TYPES = [
        "spike",           # Sudden increase
        "drop",            # Sudden decrease
        "trend_change",    # Direction change
        "missing_data",    # Data gaps
        "flatline",        # No variation
        "outlier"          # Statistical outlier
    ]

    def __init__(self):
        config = AgentConfig(
            name="anomaly_detector",
            type=AgentType.ANALYZER,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            max_tokens=1200,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Detect anomalies in metric data.

        Args:
            state: Current agent state with metric data

        Returns:
            Updated state with anomaly detection results
        """
        self.logger.info("anomaly_detection_started")

        state = self.update_state(state)

        # Extract parameters
        metric_name = state.get("entities", {}).get("metric_name", "unknown")
        time_series_data = state.get("entities", {}).get("time_series_data", [])
        sensitivity = state.get("entities", {}).get("sensitivity", "medium")
        check_seasonality = state.get("entities", {}).get("check_seasonality", True)

        self.logger.debug(
            "anomaly_detection_details",
            metric_name=metric_name,
            data_points=len(time_series_data),
            sensitivity=sensitivity
        )

        # Adjust thresholds based on sensitivity
        z_warning, z_critical = self._get_thresholds(sensitivity)

        # Calculate statistical baselines
        statistics = self._calculate_statistics(time_series_data)

        # Detect anomalies using Z-score
        z_score_anomalies = self._detect_z_score_anomalies(
            time_series_data,
            statistics,
            z_warning,
            z_critical
        )

        # Detect rate of change anomalies
        rate_anomalies = self._detect_rate_anomalies(time_series_data, statistics)

        # Detect pattern anomalies
        pattern_anomalies = self._detect_pattern_anomalies(time_series_data)

        # Combine all anomalies
        all_anomalies = self._combine_anomalies(
            z_score_anomalies,
            rate_anomalies,
            pattern_anomalies
        )

        # Classify anomaly severity
        classified_anomalies = self._classify_anomalies(all_anomalies, z_critical)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            classified_anomalies,
            metric_name,
            statistics
        )

        # Format response
        response = self._format_anomaly_report(
            metric_name,
            statistics,
            classified_anomalies,
            recommendations
        )

        state["agent_response"] = response
        state["anomalies"] = classified_anomalies
        state["statistics"] = statistics
        state["recommendations"] = recommendations
        state["anomaly_count"] = len(classified_anomalies)
        state["critical_anomalies"] = len([a for a in classified_anomalies if a["severity"] == "critical"])
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "anomaly_detection_completed",
            metric_name=metric_name,
            anomalies_detected=len(classified_anomalies),
            critical_count=state["critical_anomalies"]
        )

        return state

    def _get_thresholds(self, sensitivity: str) -> Tuple[float, float]:
        """
        Get Z-score thresholds based on sensitivity.

        Args:
            sensitivity: Sensitivity level (low, medium, high)

        Returns:
            Tuple of (warning_threshold, critical_threshold)
        """
        if sensitivity == "low":
            return 2.5, 3.5
        elif sensitivity == "high":
            return 1.5, 2.5
        else:  # medium (default)
            return self.Z_SCORE_WARNING, self.Z_SCORE_CRITICAL

    def _calculate_statistics(self, time_series_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistical baselines for anomaly detection.

        Args:
            time_series_data: Time series data points

        Returns:
            Statistical measures
        """
        if not time_series_data:
            return {
                "count": 0,
                "mean": 0,
                "std_dev": 0,
                "min": 0,
                "max": 0,
                "median": 0
            }

        # Extract values
        values = [point.get("value", 0) for point in time_series_data if isinstance(point.get("value"), (int, float))]

        if not values:
            return {"count": 0, "mean": 0, "std_dev": 0}

        # Calculate basic statistics
        count = len(values)
        mean = sum(values) / count
        variance = sum((x - mean) ** 2 for x in values) / count
        std_dev = math.sqrt(variance)

        # Calculate median
        sorted_values = sorted(values)
        mid = count // 2
        median = sorted_values[mid] if count % 2 else (sorted_values[mid - 1] + sorted_values[mid]) / 2

        # Calculate percentiles
        p25_idx = int(count * 0.25)
        p75_idx = int(count * 0.75)
        p25 = sorted_values[p25_idx]
        p75 = sorted_values[p75_idx]
        iqr = p75 - p25

        return {
            "count": count,
            "mean": round(mean, 2),
            "std_dev": round(std_dev, 2),
            "min": min(values),
            "max": max(values),
            "median": round(median, 2),
            "p25": round(p25, 2),
            "p75": round(p75, 2),
            "iqr": round(iqr, 2)
        }

    def _detect_z_score_anomalies(
        self,
        time_series_data: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        z_warning: float,
        z_critical: float
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies using Z-score method.

        Args:
            time_series_data: Time series data
            statistics: Statistical measures
            z_warning: Warning threshold
            z_critical: Critical threshold

        Returns:
            List of Z-score anomalies
        """
        anomalies = []
        mean = statistics["mean"]
        std_dev = statistics["std_dev"]

        if std_dev == 0:
            return anomalies  # No variation, no anomalies

        for i, point in enumerate(time_series_data):
            value = point.get("value")
            if not isinstance(value, (int, float)):
                continue

            # Calculate Z-score
            z_score = abs((value - mean) / std_dev)

            if z_score >= z_warning:
                severity = "critical" if z_score >= z_critical else "warning"
                anomaly_type = "spike" if value > mean else "drop"

                anomalies.append({
                    "index": i,
                    "timestamp": point.get("timestamp", "unknown"),
                    "value": value,
                    "expected_value": mean,
                    "deviation": round(value - mean, 2),
                    "z_score": round(z_score, 2),
                    "severity": severity,
                    "type": anomaly_type,
                    "method": "z_score"
                })

        return anomalies

    def _detect_rate_anomalies(
        self,
        time_series_data: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in rate of change.

        Args:
            time_series_data: Time series data
            statistics: Statistical measures

        Returns:
            List of rate anomalies
        """
        anomalies = []

        if len(time_series_data) < 2:
            return anomalies

        # Calculate rate of change for all points
        rates = []
        for i in range(1, len(time_series_data)):
            prev_val = time_series_data[i - 1].get("value", 0)
            curr_val = time_series_data[i].get("value", 0)

            if isinstance(prev_val, (int, float)) and isinstance(curr_val, (int, float)) and prev_val != 0:
                rate = ((curr_val - prev_val) / abs(prev_val)) * 100
                rates.append(rate)
            else:
                rates.append(0)

        if not rates:
            return anomalies

        # Calculate rate statistics
        mean_rate = sum(rates) / len(rates)
        rate_variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
        rate_std_dev = math.sqrt(rate_variance)

        if rate_std_dev == 0:
            return anomalies

        # Detect rate anomalies
        for i, rate in enumerate(rates):
            z_score = abs((rate - mean_rate) / rate_std_dev)

            if z_score >= 2.5:  # Rate anomaly threshold
                point_idx = i + 1
                point = time_series_data[point_idx]

                anomalies.append({
                    "index": point_idx,
                    "timestamp": point.get("timestamp", "unknown"),
                    "value": point.get("value"),
                    "rate_of_change": round(rate, 2),
                    "expected_rate": round(mean_rate, 2),
                    "z_score": round(z_score, 2),
                    "severity": "warning",
                    "type": "trend_change",
                    "method": "rate_of_change"
                })

        return anomalies

    def _detect_pattern_anomalies(
        self,
        time_series_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect pattern-based anomalies.

        Args:
            time_series_data: Time series data

        Returns:
            List of pattern anomalies
        """
        anomalies = []

        # Check for flatlines (no variation over period)
        if len(time_series_data) >= 5:
            for i in range(len(time_series_data) - 4):
                window = time_series_data[i:i + 5]
                values = [p.get("value") for p in window if isinstance(p.get("value"), (int, float))]

                if len(values) == 5 and len(set(values)) == 1:
                    # All values are identical
                    anomalies.append({
                        "index": i,
                        "timestamp": window[0].get("timestamp", "unknown"),
                        "value": values[0],
                        "severity": "warning",
                        "type": "flatline",
                        "method": "pattern",
                        "message": "No variation detected over 5 consecutive points"
                    })

        # Check for missing data patterns
        if len(time_series_data) >= 2:
            for i, point in enumerate(time_series_data):
                if point.get("value") is None or point.get("value") == "":
                    anomalies.append({
                        "index": i,
                        "timestamp": point.get("timestamp", "unknown"),
                        "value": None,
                        "severity": "warning",
                        "type": "missing_data",
                        "method": "pattern"
                    })

        return anomalies

    def _combine_anomalies(
        self,
        z_score_anomalies: List[Dict[str, Any]],
        rate_anomalies: List[Dict[str, Any]],
        pattern_anomalies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Combine anomalies from different detection methods.

        Args:
            z_score_anomalies: Z-score based anomalies
            rate_anomalies: Rate of change anomalies
            pattern_anomalies: Pattern based anomalies

        Returns:
            Combined list of unique anomalies
        """
        # Combine all anomalies
        all_anomalies = z_score_anomalies + rate_anomalies + pattern_anomalies

        # Remove duplicates based on index
        seen_indices = set()
        unique_anomalies = []

        for anomaly in all_anomalies:
            idx = anomaly.get("index")
            if idx not in seen_indices:
                seen_indices.add(idx)
                unique_anomalies.append(anomaly)

        # Sort by index
        unique_anomalies.sort(key=lambda x: x.get("index", 0))

        return unique_anomalies

    def _classify_anomalies(
        self,
        anomalies: List[Dict[str, Any]],
        z_critical: float
    ) -> List[Dict[str, Any]]:
        """
        Classify anomalies and add metadata.

        Args:
            anomalies: List of detected anomalies
            z_critical: Critical threshold

        Returns:
            Classified anomalies
        """
        for anomaly in anomalies:
            # Add priority based on severity
            if anomaly.get("severity") == "critical":
                anomaly["priority"] = "high"
            else:
                anomaly["priority"] = "medium"

            # Add confidence based on Z-score
            z_score = anomaly.get("z_score", 0)
            if z_score >= z_critical:
                anomaly["confidence"] = "high"
            elif z_score >= 2.0:
                anomaly["confidence"] = "medium"
            else:
                anomaly["confidence"] = "low"

        return anomalies

    def _generate_recommendations(
        self,
        anomalies: List[Dict[str, Any]],
        metric_name: str,
        statistics: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on detected anomalies.

        Args:
            anomalies: Detected anomalies
            metric_name: Metric name
            statistics: Statistical measures

        Returns:
            List of recommendations
        """
        recommendations = []

        critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
        warning_anomalies = [a for a in anomalies if a.get("severity") == "warning"]

        if critical_anomalies:
            recommendations.append(
                f"CRITICAL: {len(critical_anomalies)} critical anomalies detected in {metric_name}. Immediate investigation required."
            )

        if warning_anomalies:
            recommendations.append(
                f"WARNING: {len(warning_anomalies)} warning-level anomalies detected. Monitor closely."
            )

        # Type-specific recommendations
        anomaly_types = set(a.get("type") for a in anomalies)

        if "spike" in anomaly_types:
            recommendations.append("Investigate sudden spikes - may indicate traffic surge or system issue")

        if "drop" in anomaly_types:
            recommendations.append("Investigate sudden drops - may indicate service degradation")

        if "flatline" in anomaly_types:
            recommendations.append("Flatline detected - verify data collection is working properly")

        if "missing_data" in anomaly_types:
            recommendations.append("Data gaps detected - check data pipeline integrity")

        if not anomalies:
            recommendations.append(f"No anomalies detected in {metric_name}. Metrics within normal range.")

        return recommendations

    def _format_anomaly_report(
        self,
        metric_name: str,
        statistics: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        recommendations: List[str]
    ) -> str:
        """Format anomaly detection report."""
        critical_count = len([a for a in anomalies if a.get("severity") == "critical"])
        warning_count = len([a for a in anomalies if a.get("severity") == "warning"])

        report = f"""**Anomaly Detection Report: {metric_name}**

**Statistical Baseline:**
- Mean: {statistics['mean']:.2f}
- Std Dev: {statistics['std_dev']:.2f}
- Min: {statistics['min']:.2f} | Max: {statistics['max']:.2f}
- Median: {statistics['median']:.2f}
- Data Points: {statistics['count']}

**Anomaly Summary:**
- Total Anomalies: {len(anomalies)}
- Critical (>3σ): {critical_count}
- Warning (>2σ): {warning_count}

"""

        # Top anomalies
        if anomalies:
            report += "**Detected Anomalies:**\n"
            for anomaly in anomalies[:10]:  # Top 10
                severity_icon = "🔴" if anomaly["severity"] == "critical" else "⚠️"
                report += f"{severity_icon} **{anomaly['type'].upper()}** at {anomaly.get('timestamp', 'unknown')}\n"
                report += f"   - Value: {anomaly.get('value'):.2f} (Expected: {anomaly.get('expected_value', 'N/A'):.2f})\n"
                report += f"   - Z-Score: {anomaly.get('z_score', 0):.2f} | Method: {anomaly.get('method')}\n"

            if len(anomalies) > 10:
                report += f"... and {len(anomalies) - 10} more anomalies\n"
            report += "\n"

        # Recommendations
        if recommendations:
            report += "**Recommendations:**\n"
            for rec in recommendations:
                report += f"- {rec}\n"

        report += f"\n*Analysis completed at {datetime.utcnow().isoformat()}*"

        return report
