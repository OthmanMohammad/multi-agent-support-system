"""
Unit tests for Metrics Tracker Agent.

Tests metric tracking, aggregation, threshold checking, and reporting.
Part of: TASK-2011 Analytics Swarm
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.agents.operational.analytics.metrics_tracker import MetricsTrackerAgent
from src.workflow.state import AgentState, create_initial_state


@pytest.fixture
def agent():
    """Create MetricsTrackerAgent instance for testing."""
    return MetricsTrackerAgent()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Show me all metrics",
        context={"customer_metadata": {"plan": "premium"}}
    )


class TestMetricsTrackerInitialization:
    """Test Metrics Tracker initialization and configuration."""

    def test_agent_initialization(self, agent):
        """Test that agent initializes with correct configuration."""
        assert agent.config.name == "metrics_tracker"
        assert agent.config.type.value == "analyzer"
        assert agent.config.model == "claude-3-haiku-20240307"
        assert agent.config.temperature == 0.2
        assert agent.config.tier == "operational"

    def test_metric_categories_defined(self, agent):
        """Test that metric categories are properly defined."""
        assert "customer" in agent.METRIC_CATEGORIES
        assert "support" in agent.METRIC_CATEGORIES
        assert "sales" in agent.METRIC_CATEGORIES
        assert "customer_success" in agent.METRIC_CATEGORIES
        assert "operational" in agent.METRIC_CATEGORIES

    def test_thresholds_defined(self, agent):
        """Test that thresholds are properly defined."""
        assert "csat_score" in agent.THRESHOLDS
        assert "nps" in agent.THRESHOLDS
        assert agent.THRESHOLDS["csat_score"]["warning"] > agent.THRESHOLDS["csat_score"]["critical"]


class TestMetricsProcessing:
    """Test metrics processing and tracking."""

    @pytest.mark.asyncio
    async def test_successful_metrics_tracking_all_categories(self, agent, sample_state):
        """Test successful tracking of all metric categories."""
        sample_state["entities"] = {"metric_category": "all", "time_period": "today"}

        result = await agent.process(sample_state)

        assert result["status"] == "resolved"
        assert "metrics_data" in result
        assert "aggregations" in result
        assert result["response_confidence"] == 0.95
        assert result["next_agent"] is None

    @pytest.mark.asyncio
    async def test_metrics_tracking_single_category(self, agent):
        """Test tracking metrics for a single category."""
        state = create_initial_state(
            message="Show customer metrics",
            context={}
        )
        state["entities"] = {"metric_category": "customer", "time_period": "today"}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        assert "customer" in result["metrics_data"]["categories"]
        assert len(result["metrics_data"]["categories"]) == 1

    @pytest.mark.asyncio
    async def test_metrics_with_comparisons(self, agent):
        """Test metrics tracking with period comparisons."""
        state = create_initial_state(
            message="Show metrics with comparisons",
            context={}
        )
        state["entities"] = {
            "metric_category": "support",
            "include_comparisons": True
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"
        # Comparisons are calculated in the process
        assert "metrics_data" in result

    @pytest.mark.asyncio
    async def test_metrics_without_comparisons(self, agent):
        """Test metrics tracking without comparisons."""
        state = create_initial_state(
            message="Show metrics",
            context={}
        )
        state["entities"] = {
            "metric_category": "sales",
            "include_comparisons": False
        }

        result = await agent.process(state)

        assert result["status"] == "resolved"


class TestAggregations:
    """Test metric aggregations."""

    def test_calculate_aggregations(self, agent):
        """Test aggregation calculations."""
        metrics_data = {
            "categories": {
                "customer": {
                    "metrics": {
                        "total_customers": 1000,
                        "active_customers": 850,
                        "mrr": 50000
                    }
                }
            }
        }

        aggregations = agent._calculate_aggregations(metrics_data, "customer")

        assert aggregations["total_metrics_tracked"] == 3
        assert aggregations["categories_analyzed"] == 1
        assert "customer" in aggregations["by_category"]
        assert aggregations["by_category"]["customer"]["metric_count"] == 3

    def test_aggregations_multiple_categories(self, agent):
        """Test aggregations across multiple categories."""
        metrics_data = {
            "categories": {
                "customer": {"metrics": {"total_customers": 1000}},
                "support": {"metrics": {"total_tickets": 500}}
            }
        }

        aggregations = agent._calculate_aggregations(metrics_data, "all")

        assert aggregations["categories_analyzed"] == 2
        assert aggregations["total_metrics_tracked"] == 2


class TestThresholdChecking:
    """Test threshold checking and alerting."""

    def test_check_thresholds_no_alerts(self, agent):
        """Test threshold checking with healthy metrics."""
        metrics_data = {
            "categories": {
                "support": {
                    "metrics": {
                        "csat_score": 4.7,
                        "nps": 55
                    }
                }
            }
        }

        alerts = agent._check_thresholds(metrics_data)

        assert len(alerts) == 0

    def test_check_thresholds_critical_alert(self, agent):
        """Test threshold checking with critical metrics."""
        metrics_data = {
            "categories": {
                "support": {
                    "metrics": {
                        "csat_score": 3.0,  # Below critical threshold
                    }
                }
            }
        }

        alerts = agent._check_thresholds(metrics_data)

        assert len(alerts) > 0
        assert any(alert["severity"] == "critical" for alert in alerts)
        assert any("csat_score" in alert["metric"] for alert in alerts)

    def test_check_thresholds_warning_alert(self, agent):
        """Test threshold checking with warning-level metrics."""
        metrics_data = {
            "categories": {
                "support": {
                    "metrics": {
                        "csat_score": 3.8,  # Below warning, above critical
                    }
                }
            }
        }

        alerts = agent._check_thresholds(metrics_data)

        assert len(alerts) > 0
        assert any(alert["severity"] == "warning" for alert in alerts)

    def test_check_thresholds_inverted_metric(self, agent):
        """Test threshold checking for inverted metrics (lower is better)."""
        metrics_data = {
            "categories": {
                "support": {
                    "metrics": {
                        "avg_resolution_time_hours": 50,  # Above critical threshold
                    }
                }
            }
        }

        alerts = agent._check_thresholds(metrics_data)

        assert len(alerts) > 0
        assert any("resolution_time" in alert["metric"] for alert in alerts)


class TestMetricsFetching:
    """Test metrics data fetching."""

    def test_fetch_metrics_all_categories(self, agent):
        """Test fetching metrics for all categories."""
        metrics_data = agent._fetch_metrics_data("all", "today", "daily")

        assert "categories" in metrics_data
        assert len(metrics_data["categories"]) == 5
        assert all(cat in metrics_data["categories"] for cat in
                  ["customer", "support", "sales", "customer_success", "operational"])

    def test_fetch_metrics_single_category(self, agent):
        """Test fetching metrics for a single category."""
        metrics_data = agent._fetch_metrics_data("customer", "today", "daily")

        assert "categories" in metrics_data
        assert "customer" in metrics_data["categories"]
        assert len(metrics_data["categories"]) == 1

    def test_fetch_metrics_invalid_category_defaults(self, agent):
        """Test fetching metrics with invalid category defaults to customer."""
        metrics_data = agent._fetch_metrics_data("invalid_category", "today", "daily")

        assert "categories" in metrics_data
        assert "customer" in metrics_data["categories"]


class TestComparisons:
    """Test period-over-period comparisons."""

    def test_calculate_comparisons(self, agent):
        """Test comparison calculations."""
        metrics_data = {
            "categories": {
                "customer": {
                    "metrics": {
                        "total_customers": 1000,
                        "mrr": 50000
                    }
                }
            }
        }

        comparisons = agent._calculate_comparisons(metrics_data, "today")

        assert "comparison_period" in comparisons
        assert "changes" in comparisons
        assert "customer" in comparisons["changes"]
        assert "total_customers" in comparisons["changes"]["customer"]
        assert "trend" in comparisons["changes"]["customer"]["total_customers"]


class TestSummaryGeneration:
    """Test summary statistics generation."""

    def test_generate_summary_healthy(self, agent):
        """Test summary generation with healthy metrics."""
        metrics_data = {"categories": {"customer": {"metrics": {}}}}
        aggregations = {"total_metrics_tracked": 10, "categories_analyzed": 2}
        alerts = []

        summary = agent._generate_summary(metrics_data, aggregations, alerts)

        assert summary["total_metrics"] == 10
        assert summary["categories_tracked"] == 2
        assert summary["alerts_count"] == 0
        assert summary["health_status"] == "healthy"

    def test_generate_summary_with_warnings(self, agent):
        """Test summary generation with warnings."""
        metrics_data = {"categories": {}}
        aggregations = {"total_metrics_tracked": 10, "categories_analyzed": 2}
        alerts = [{"severity": "warning", "message": "Test warning"}]

        summary = agent._generate_summary(metrics_data, aggregations, alerts)

        assert summary["warning_alerts"] == 1
        assert summary["health_status"] == "warning"

    def test_generate_summary_with_critical_alerts(self, agent):
        """Test summary generation with critical alerts."""
        metrics_data = {"categories": {}}
        aggregations = {"total_metrics_tracked": 10, "categories_analyzed": 2}
        alerts = [{"severity": "critical", "message": "Test critical"}]

        summary = agent._generate_summary(metrics_data, aggregations, alerts)

        assert summary["critical_alerts"] == 1
        assert summary["health_status"] == "critical"


class TestReportFormatting:
    """Test report formatting."""

    def test_format_metrics_report(self, agent):
        """Test metrics report formatting."""
        metrics_data = {
            "time_period": "today",
            "granularity": "daily",
            "categories": {
                "customer": {
                    "metrics": {"total_customers": 1000}
                }
            }
        }
        aggregations = {
            "total_metrics_tracked": 1,
            "by_category": {
                "customer": {"metric_count": 1}
            }
        }
        alerts = []
        comparisons = None
        summary = {
            "total_metrics": 1,
            "categories_tracked": 1,
            "health_status": "healthy",
            "alerts_count": 0,
            "critical_alerts": 0,
            "warning_alerts": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        report = agent._format_metrics_report(
            metrics_data, aggregations, alerts, comparisons, summary, "customer"
        )

        assert "Metrics Tracking Report" in report
        assert "Total Metrics Tracked" in report
        assert "healthy" in report.lower()

    def test_format_report_with_alerts(self, agent):
        """Test report formatting with alerts."""
        metrics_data = {"time_period": "today", "granularity": "daily", "categories": {}}
        aggregations = {"total_metrics_tracked": 0, "by_category": {}}
        alerts = [
            {"severity": "critical", "message": "Critical issue", "category": "support"}
        ]
        comparisons = None
        summary = {
            "total_metrics": 0,
            "categories_tracked": 0,
            "health_status": "critical",
            "alerts_count": 1,
            "critical_alerts": 1,
            "warning_alerts": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

        report = agent._format_metrics_report(
            metrics_data, aggregations, alerts, comparisons, summary, "all"
        )

        assert "Critical issue" in report


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_handles_empty_entities(self, agent):
        """Test handling of missing entities."""
        state = create_initial_state(message="Show metrics", context={})
        state["entities"] = {}

        result = await agent.process(state)

        assert result["status"] == "resolved"
        # Should use defaults
        assert "metrics_data" in result

    @pytest.mark.asyncio
    async def test_handles_missing_time_period(self, agent):
        """Test handling of missing time period."""
        state = create_initial_state(message="Show metrics", context={})
        state["entities"] = {"metric_category": "customer"}

        result = await agent.process(state)

        assert result["status"] == "resolved"

    def test_empty_metrics_data(self, agent):
        """Test handling of empty metrics data."""
        metrics_data = {"categories": {}}
        aggregations = agent._calculate_aggregations(metrics_data, "all")

        assert aggregations["total_metrics_tracked"] == 0
        assert aggregations["categories_analyzed"] == 0
