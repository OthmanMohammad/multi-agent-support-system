"""
Metrics Tracker Agent - TASK-2011

Tracks all key metrics across customer, support, sales, and CS domains.
Provides comprehensive metric monitoring and aggregation capabilities.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("metrics_tracker", tier="operational", category="analytics")
class MetricsTrackerAgent(BaseAgent):
    """
    Metrics Tracker Agent.

    Tracks and aggregates key metrics across all business domains:
    - Customer metrics (acquisition, activation, retention, revenue)
    - Support metrics (tickets, resolution time, CSAT, backlog)
    - Sales metrics (pipeline, conversion rates, deal velocity)
    - CS metrics (health scores, NPS, churn risk, expansion)
    - Operational metrics (system performance, agent utilization)
    """

    # Metric categories and their key indicators
    METRIC_CATEGORIES = {
        "customer": [
            "total_customers",
            "active_customers",
            "new_customers",
            "churned_customers",
            "mrr",
            "arr",
            "ltv",
            "cac"
        ],
        "support": [
            "total_tickets",
            "open_tickets",
            "resolved_tickets",
            "avg_resolution_time_hours",
            "first_response_time_minutes",
            "csat_score",
            "ticket_backlog"
        ],
        "sales": [
            "pipeline_value",
            "closed_won",
            "closed_lost",
            "win_rate",
            "avg_deal_size",
            "sales_cycle_days",
            "quota_attainment"
        ],
        "customer_success": [
            "avg_health_score",
            "nps",
            "accounts_at_risk",
            "expansion_opportunities",
            "qbr_completion_rate",
            "adoption_rate"
        ],
        "operational": [
            "api_requests",
            "avg_response_time_ms",
            "error_rate",
            "uptime_pct",
            "agent_utilization",
            "cache_hit_rate"
        ]
    }

    # Metric thresholds for alerting
    THRESHOLDS = {
        "csat_score": {"warning": 4.0, "critical": 3.5},
        "nps": {"warning": 30, "critical": 20},
        "churn_rate": {"warning": 5.0, "critical": 8.0},
        "error_rate": {"warning": 1.0, "critical": 3.0},
        "avg_resolution_time_hours": {"warning": 24, "critical": 48},
        "uptime_pct": {"warning": 99.0, "critical": 98.0}
    }

    def __init__(self):
        config = AgentConfig(
            name="metrics_tracker",
            type=AgentType.ANALYZER,
            temperature=0.2,
            max_tokens=1000,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Track and aggregate metrics across all domains.

        Args:
            state: Current agent state with metric query parameters

        Returns:
            Updated state with tracked metrics and aggregations
        """
        self.logger.info("metrics_tracking_started")

        state = self.update_state(state)

        # Extract parameters
        metric_category = state.get("entities", {}).get("metric_category", "all")
        time_period = state.get("entities", {}).get("time_period", "today")
        granularity = state.get("entities", {}).get("granularity", "daily")
        include_comparisons = state.get("entities", {}).get("include_comparisons", True)

        self.logger.debug(
            "metrics_tracking_details",
            category=metric_category,
            time_period=time_period,
            granularity=granularity
        )

        # Get metric data
        metrics_data = self._fetch_metrics_data(metric_category, time_period, granularity)

        # Calculate aggregations
        aggregations = self._calculate_aggregations(metrics_data, metric_category)

        # Check thresholds and generate alerts
        alerts = self._check_thresholds(metrics_data)

        # Calculate comparisons if requested
        comparisons = None
        if include_comparisons:
            comparisons = self._calculate_comparisons(metrics_data, time_period)

        # Generate summary statistics
        summary = self._generate_summary(metrics_data, aggregations, alerts)

        # Format response
        response = self._format_metrics_report(
            metrics_data,
            aggregations,
            alerts,
            comparisons,
            summary,
            metric_category
        )

        state["agent_response"] = response
        state["metrics_data"] = metrics_data
        state["aggregations"] = aggregations
        state["alerts"] = alerts
        state["metrics_summary"] = summary
        state["response_confidence"] = 0.95
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "metrics_tracking_completed",
            category=metric_category,
            metrics_count=len(metrics_data),
            alerts_count=len(alerts)
        )

        return state

    def _fetch_metrics_data(
        self,
        category: str,
        time_period: str,
        granularity: str
    ) -> Dict[str, Any]:
        """
        Fetch metrics data from data sources.

        Args:
            category: Metric category to fetch
            time_period: Time period for metrics
            granularity: Data granularity (hourly, daily, weekly, monthly)

        Returns:
            Dictionary of metrics data
        """
        # In production, this would query actual data sources
        # For now, return mock data structure

        current_time = datetime.now(UTC)

        # Determine categories to fetch
        if category == "all":
            categories = list(self.METRIC_CATEGORIES.keys())
        elif category in self.METRIC_CATEGORIES:
            categories = [category]
        else:
            categories = ["customer"]  # Default fallback

        metrics_data = {
            "timestamp": current_time.isoformat(),
            "time_period": time_period,
            "granularity": granularity,
            "categories": {}
        }

        for cat in categories:
            metrics_data["categories"][cat] = self._generate_category_metrics(cat)

        return metrics_data

    def _generate_category_metrics(self, category: str) -> Dict[str, Any]:
        """Generate metrics for a specific category."""
        metric_names = self.METRIC_CATEGORIES.get(category, [])

        # Mock data - in production, query actual metrics
        metrics = {}

        if category == "customer":
            metrics = {
                "total_customers": 15420,
                "active_customers": 14230,
                "new_customers": 342,
                "churned_customers": 87,
                "mrr": 542000,
                "arr": 6504000,
                "ltv": 45600,
                "cac": 3200
            }
        elif category == "support":
            metrics = {
                "total_tickets": 1823,
                "open_tickets": 234,
                "resolved_tickets": 1589,
                "avg_resolution_time_hours": 18.5,
                "first_response_time_minutes": 12.3,
                "csat_score": 4.6,
                "ticket_backlog": 234
            }
        elif category == "sales":
            metrics = {
                "pipeline_value": 2450000,
                "closed_won": 890000,
                "closed_lost": 320000,
                "win_rate": 73.5,
                "avg_deal_size": 35000,
                "sales_cycle_days": 42,
                "quota_attainment": 87.3
            }
        elif category == "customer_success":
            metrics = {
                "avg_health_score": 78.5,
                "nps": 52,
                "accounts_at_risk": 23,
                "expansion_opportunities": 145,
                "qbr_completion_rate": 82.0,
                "adoption_rate": 67.5
            }
        elif category == "operational":
            metrics = {
                "api_requests": 1250000,
                "avg_response_time_ms": 145,
                "error_rate": 0.35,
                "uptime_pct": 99.97,
                "agent_utilization": 76.5,
                "cache_hit_rate": 89.2
            }

        return {
            "metrics": metrics,
            "metric_count": len(metrics),
            "last_updated": datetime.now(UTC).isoformat()
        }

    def _calculate_aggregations(
        self,
        metrics_data: Dict[str, Any],
        category: str
    ) -> Dict[str, Any]:
        """
        Calculate metric aggregations.

        Args:
            metrics_data: Raw metrics data
            category: Metric category

        Returns:
            Aggregated metrics
        """
        aggregations = {
            "total_metrics_tracked": 0,
            "categories_analyzed": len(metrics_data.get("categories", {})),
            "by_category": {}
        }

        for cat, cat_data in metrics_data.get("categories", {}).items():
            cat_metrics = cat_data.get("metrics", {})

            # Calculate basic stats
            values = [v for v in cat_metrics.values() if isinstance(v, (int, float))]

            if values:
                aggregations["by_category"][cat] = {
                    "metric_count": len(cat_metrics),
                    "avg_value": sum(values) / len(values),
                    "max_value": max(values),
                    "min_value": min(values)
                }
                aggregations["total_metrics_tracked"] += len(cat_metrics)

        return aggregations

    def _check_thresholds(self, metrics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check metrics against thresholds and generate alerts.

        Args:
            metrics_data: Metrics data

        Returns:
            List of alerts
        """
        alerts = []

        for cat, cat_data in metrics_data.get("categories", {}).items():
            cat_metrics = cat_data.get("metrics", {})

            for metric_name, value in cat_metrics.items():
                if metric_name in self.THRESHOLDS:
                    thresholds = self.THRESHOLDS[metric_name]

                    # Check if metric is inverted (lower is better)
                    inverted_metrics = ["avg_resolution_time_hours", "error_rate", "churn_rate"]

                    if metric_name in inverted_metrics:
                        if value >= thresholds["critical"]:
                            alerts.append({
                                "severity": "critical",
                                "metric": metric_name,
                                "category": cat,
                                "value": value,
                                "threshold": thresholds["critical"],
                                "message": f"{metric_name} is critically high: {value}"
                            })
                        elif value >= thresholds["warning"]:
                            alerts.append({
                                "severity": "warning",
                                "metric": metric_name,
                                "category": cat,
                                "value": value,
                                "threshold": thresholds["warning"],
                                "message": f"{metric_name} is above warning threshold: {value}"
                            })
                    else:
                        if value <= thresholds["critical"]:
                            alerts.append({
                                "severity": "critical",
                                "metric": metric_name,
                                "category": cat,
                                "value": value,
                                "threshold": thresholds["critical"],
                                "message": f"{metric_name} is critically low: {value}"
                            })
                        elif value <= thresholds["warning"]:
                            alerts.append({
                                "severity": "warning",
                                "metric": metric_name,
                                "category": cat,
                                "value": value,
                                "threshold": thresholds["warning"],
                                "message": f"{metric_name} is below warning threshold: {value}"
                            })

        return alerts

    def _calculate_comparisons(
        self,
        metrics_data: Dict[str, Any],
        time_period: str
    ) -> Dict[str, Any]:
        """
        Calculate period-over-period comparisons.

        Args:
            metrics_data: Current metrics data
            time_period: Time period

        Returns:
            Comparison data
        """
        # Mock comparison data - in production, query historical data
        comparisons = {
            "comparison_period": "previous_period",
            "changes": {}
        }

        for cat, cat_data in metrics_data.get("categories", {}).items():
            cat_metrics = cat_data.get("metrics", {})
            comparisons["changes"][cat] = {}

            for metric_name, current_value in cat_metrics.items():
                if isinstance(current_value, (int, float)):
                    # Mock: simulate 5-15% change
                    import random
                    change_pct = random.uniform(-15, 15)
                    previous_value = current_value / (1 + change_pct / 100)

                    comparisons["changes"][cat][metric_name] = {
                        "current": current_value,
                        "previous": round(previous_value, 2),
                        "change": round(current_value - previous_value, 2),
                        "change_pct": round(change_pct, 2),
                        "trend": "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
                    }

        return comparisons

    def _generate_summary(
        self,
        metrics_data: Dict[str, Any],
        aggregations: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary statistics."""
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        warning_alerts = [a for a in alerts if a["severity"] == "warning"]

        return {
            "total_metrics": aggregations["total_metrics_tracked"],
            "categories_tracked": aggregations["categories_analyzed"],
            "alerts_count": len(alerts),
            "critical_alerts": len(critical_alerts),
            "warning_alerts": len(warning_alerts),
            "health_status": "critical" if critical_alerts else "warning" if warning_alerts else "healthy",
            "timestamp": datetime.now(UTC).isoformat()
        }

    def _format_metrics_report(
        self,
        metrics_data: Dict[str, Any],
        aggregations: Dict[str, Any],
        alerts: List[Dict[str, Any]],
        comparisons: Optional[Dict[str, Any]],
        summary: Dict[str, Any],
        category: str
    ) -> str:
        """Format metrics tracking report."""
        report = f"""**Metrics Tracking Report**

**Summary:**
- Total Metrics Tracked: {summary['total_metrics']}
- Categories Analyzed: {summary['categories_tracked']}
- Health Status: {summary['health_status'].upper()}
- Alerts: {summary['alerts_count']} ({summary['critical_alerts']} critical, {summary['warning_alerts']} warnings)
- Time Period: {metrics_data['time_period']}
- Granularity: {metrics_data['granularity']}

"""

        # Alerts section
        if alerts:
            report += "**Alerts:**\n"
            for alert in alerts[:5]:  # Top 5 alerts
                icon = "🔴" if alert["severity"] == "critical" else "⚠️"
                report += f"{icon} {alert['message']} (Category: {alert['category']})\n"
            if len(alerts) > 5:
                report += f"... and {len(alerts) - 5} more alerts\n"
            report += "\n"

        # Metrics by category
        for cat, cat_data in metrics_data.get("categories", {}).items():
            report += f"**{cat.replace('_', ' ').title()} Metrics:**\n"
            cat_metrics = cat_data.get("metrics", {})

            for metric_name, value in list(cat_metrics.items())[:8]:  # Top 8 metrics per category
                formatted_value = f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"

                # Add comparison if available
                comparison_str = ""
                if comparisons and cat in comparisons.get("changes", {}):
                    if metric_name in comparisons["changes"][cat]:
                        comp = comparisons["changes"][cat][metric_name]
                        trend_icon = "📈" if comp["trend"] == "up" else "📉" if comp["trend"] == "down" else "➡️"
                        comparison_str = f" {trend_icon} {comp['change_pct']:+.1f}%"

                report += f"- {metric_name.replace('_', ' ').title()}: {formatted_value}{comparison_str}\n"

            report += "\n"

        # Aggregations
        report += "**Aggregations:**\n"
        for cat, agg_data in aggregations.get("by_category", {}).items():
            report += f"- {cat.replace('_', ' ').title()}: {agg_data['metric_count']} metrics tracked\n"

        report += f"\n*Report generated at {summary['timestamp']}*"

        return report
