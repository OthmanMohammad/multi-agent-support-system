"""
Dashboard Generator Agent - TASK-2012

Generates role-specific dashboards with JSON output for various stakeholders.
Provides customized data views for executives, managers, and individual contributors.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("dashboard_generator", tier="operational", category="analytics")
class DashboardGeneratorAgent(BaseAgent):
    """
    Dashboard Generator Agent.

    Generates role-specific dashboards for different stakeholders:
    - Executive dashboards (high-level KPIs, trends)
    - Manager dashboards (team performance, operational metrics)
    - CS dashboards (customer health, engagement, expansion)
    - Sales dashboards (pipeline, deals, forecasts)
    - Support dashboards (tickets, SLAs, customer satisfaction)
    - Engineering dashboards (system health, performance, errors)
    """

    # Dashboard templates by role
    DASHBOARD_TEMPLATES = {
        "executive": {
            "name": "Executive Dashboard",
            "widgets": [
                "revenue_overview",
                "customer_growth",
                "key_metrics",
                "health_indicators",
                "strategic_initiatives"
            ],
            "refresh_interval": "daily"
        },
        "cs_manager": {
            "name": "Customer Success Manager Dashboard",
            "widgets": [
                "account_health",
                "expansion_opportunities",
                "at_risk_accounts",
                "nps_score",
                "adoption_metrics",
                "upcoming_renewals"
            ],
            "refresh_interval": "hourly"
        },
        "sales_manager": {
            "name": "Sales Manager Dashboard",
            "widgets": [
                "pipeline_overview",
                "win_rate",
                "deal_stages",
                "quota_attainment",
                "top_opportunities",
                "sales_velocity"
            ],
            "refresh_interval": "hourly"
        },
        "support_manager": {
            "name": "Support Manager Dashboard",
            "widgets": [
                "ticket_volume",
                "sla_compliance",
                "csat_trends",
                "agent_performance",
                "backlog_status",
                "escalations"
            ],
            "refresh_interval": "realtime"
        },
        "product_manager": {
            "name": "Product Manager Dashboard",
            "widgets": [
                "feature_adoption",
                "user_engagement",
                "feature_requests",
                "bug_trends",
                "usage_analytics",
                "retention_cohorts"
            ],
            "refresh_interval": "daily"
        },
        "engineering": {
            "name": "Engineering Dashboard",
            "widgets": [
                "system_health",
                "api_performance",
                "error_rates",
                "deployment_frequency",
                "incident_status",
                "infrastructure_costs"
            ],
            "refresh_interval": "realtime"
        }
    }

    # Widget data sources
    WIDGET_CONFIGS = {
        "revenue_overview": {
            "type": "metric_card",
            "metrics": ["mrr", "arr", "growth_rate"],
            "visualization": "trend_line"
        },
        "customer_growth": {
            "type": "chart",
            "chart_type": "line",
            "metrics": ["new_customers", "churned_customers", "net_growth"]
        },
        "account_health": {
            "type": "distribution",
            "chart_type": "pie",
            "segments": ["healthy", "at_risk", "critical"]
        },
        "pipeline_overview": {
            "type": "funnel",
            "stages": ["qualified", "demo", "proposal", "negotiation", "closed_won"]
        },
        "ticket_volume": {
            "type": "chart",
            "chart_type": "bar",
            "metrics": ["new_tickets", "resolved_tickets", "open_tickets"]
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="dashboard_generator",
            type=AgentType.GENERATOR,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            max_tokens=2000,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Generate role-specific dashboard.

        Args:
            state: Current agent state with dashboard requirements

        Returns:
            Updated state with dashboard JSON
        """
        self.logger.info("dashboard_generation_started")

        state = self.update_state(state)

        # Extract parameters
        role = state.get("entities", {}).get("role", "executive")
        custom_widgets = state.get("entities", {}).get("custom_widgets", None)
        time_range = state.get("entities", {}).get("time_range", "7d")
        include_trends = state.get("entities", {}).get("include_trends", True)

        self.logger.debug(
            "dashboard_generation_details",
            role=role,
            time_range=time_range,
            custom_widgets=custom_widgets is not None
        )

        # Get dashboard template
        dashboard_template = self._get_dashboard_template(role, custom_widgets)

        # Fetch data for widgets
        dashboard_data = self._fetch_dashboard_data(
            dashboard_template,
            time_range,
            include_trends
        )

        # Build dashboard JSON
        dashboard_json = self._build_dashboard_json(
            dashboard_template,
            dashboard_data,
            role,
            time_range
        )

        # Generate insights for dashboard
        insights = self._generate_dashboard_insights(dashboard_data, role)

        # Format response
        response = self._format_dashboard_response(
            dashboard_json,
            insights,
            role
        )

        state["agent_response"] = response
        state["dashboard_json"] = dashboard_json
        state["dashboard_data"] = dashboard_data
        state["dashboard_insights"] = insights
        state["response_confidence"] = 0.92
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "dashboard_generation_completed",
            role=role,
            widgets_count=len(dashboard_template["widgets"]),
            insights_count=len(insights)
        )

        return state

    def _get_dashboard_template(
        self,
        role: str,
        custom_widgets: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Get dashboard template for role.

        Args:
            role: User role
            custom_widgets: Optional custom widget list

        Returns:
            Dashboard template
        """
        if role in self.DASHBOARD_TEMPLATES:
            template = self.DASHBOARD_TEMPLATES[role].copy()
        else:
            # Default to executive dashboard
            template = self.DASHBOARD_TEMPLATES["executive"].copy()

        # Override widgets if custom ones provided
        if custom_widgets:
            template["widgets"] = custom_widgets
            template["name"] = f"Custom {role.title()} Dashboard"

        return template

    def _fetch_dashboard_data(
        self,
        dashboard_template: Dict[str, Any],
        time_range: str,
        include_trends: bool
    ) -> Dict[str, Any]:
        """
        Fetch data for all dashboard widgets.

        Args:
            dashboard_template: Dashboard template
            time_range: Time range for data
            include_trends: Whether to include trend data

        Returns:
            Dashboard data
        """
        dashboard_data = {
            "time_range": time_range,
            "generated_at": datetime.utcnow().isoformat(),
            "widgets": {}
        }

        for widget_name in dashboard_template["widgets"]:
            widget_data = self._fetch_widget_data(widget_name, time_range, include_trends)
            dashboard_data["widgets"][widget_name] = widget_data

        return dashboard_data

    def _fetch_widget_data(
        self,
        widget_name: str,
        time_range: str,
        include_trends: bool
    ) -> Dict[str, Any]:
        """
        Fetch data for a specific widget.

        Args:
            widget_name: Widget identifier
            time_range: Time range
            include_trends: Include trend data

        Returns:
            Widget data
        """
        # Mock data - in production, query actual data sources
        widget_config = self.WIDGET_CONFIGS.get(widget_name, {"type": "metric_card"})

        # Generate mock data based on widget type
        if widget_name == "revenue_overview":
            return {
                "type": "metric_card",
                "data": {
                    "mrr": {"value": 542000, "change": "+8.5%", "trend": "up"},
                    "arr": {"value": 6504000, "change": "+12.3%", "trend": "up"},
                    "growth_rate": {"value": 12.3, "change": "+2.1%", "trend": "up"}
                }
            }
        elif widget_name == "customer_growth":
            return {
                "type": "chart",
                "chart_type": "line",
                "data": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "datasets": [
                        {"label": "New Customers", "values": [45, 52, 48, 61, 55, 38, 42]},
                        {"label": "Churned", "values": [12, 8, 15, 10, 13, 9, 11]},
                        {"label": "Net Growth", "values": [33, 44, 33, 51, 42, 29, 31]}
                    ]
                }
            }
        elif widget_name == "account_health":
            return {
                "type": "distribution",
                "chart_type": "pie",
                "data": {
                    "segments": [
                        {"label": "Healthy", "value": 1245, "percentage": 75.5},
                        {"label": "At Risk", "value": 312, "percentage": 19.0},
                        {"label": "Critical", "value": 91, "percentage": 5.5}
                    ]
                }
            }
        elif widget_name == "pipeline_overview":
            return {
                "type": "funnel",
                "data": {
                    "stages": [
                        {"name": "Qualified", "count": 450, "value": 15750000},
                        {"name": "Demo", "count": 285, "value": 9975000},
                        {"name": "Proposal", "count": 142, "value": 4970000},
                        {"name": "Negotiation", "count": 67, "value": 2345000},
                        {"name": "Closed Won", "count": 28, "value": 980000}
                    ]
                }
            }
        elif widget_name == "ticket_volume":
            return {
                "type": "chart",
                "chart_type": "bar",
                "data": {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    "datasets": [
                        {"label": "New Tickets", "values": [145, 162, 138, 171, 155, 89, 92]},
                        {"label": "Resolved", "values": [132, 148, 155, 149, 168, 95, 88]},
                        {"label": "Open", "values": [234, 248, 231, 253, 240, 234, 238]}
                    ]
                }
            }
        elif widget_name == "nps_score":
            return {
                "type": "metric_card",
                "data": {
                    "score": {"value": 52, "change": "+3", "trend": "up"},
                    "promoters": {"value": 68, "percentage": 68},
                    "detractors": {"value": 16, "percentage": 16}
                }
            }
        elif widget_name == "expansion_opportunities":
            return {
                "type": "list",
                "data": {
                    "total": 145,
                    "high_priority": 42,
                    "potential_value": 2450000,
                    "items": [
                        {"account": "Acme Corp", "value": 85000, "readiness": "high"},
                        {"account": "TechStart Inc", "value": 62000, "readiness": "high"},
                        {"account": "Global Solutions", "value": 48000, "readiness": "medium"}
                    ]
                }
            }
        elif widget_name == "at_risk_accounts":
            return {
                "type": "list",
                "data": {
                    "total": 23,
                    "critical": 5,
                    "at_risk_arr": 890000,
                    "items": [
                        {"account": "RetailCo", "arr": 125000, "health_score": 32, "risk": "critical"},
                        {"account": "FinServ LLC", "arr": 98000, "health_score": 38, "risk": "critical"},
                        {"account": "MedTech", "arr": 87000, "health_score": 45, "risk": "high"}
                    ]
                }
            }
        else:
            # Generic widget data
            return {
                "type": "metric_card",
                "data": {
                    "value": 0,
                    "status": "no_data"
                }
            }

    def _build_dashboard_json(
        self,
        dashboard_template: Dict[str, Any],
        dashboard_data: Dict[str, Any],
        role: str,
        time_range: str
    ) -> Dict[str, Any]:
        """
        Build complete dashboard JSON structure.

        Args:
            dashboard_template: Dashboard template
            dashboard_data: Fetched data
            role: User role
            time_range: Time range

        Returns:
            Complete dashboard JSON
        """
        dashboard_json = {
            "dashboard": {
                "id": f"dashboard_{role}_{datetime.utcnow().timestamp()}",
                "name": dashboard_template["name"],
                "role": role,
                "time_range": time_range,
                "refresh_interval": dashboard_template["refresh_interval"],
                "generated_at": dashboard_data["generated_at"],
                "widgets": []
            }
        }

        # Add widgets
        for widget_name in dashboard_template["widgets"]:
            if widget_name in dashboard_data["widgets"]:
                widget = {
                    "id": widget_name,
                    "name": widget_name.replace("_", " ").title(),
                    "config": self.WIDGET_CONFIGS.get(widget_name, {}),
                    "data": dashboard_data["widgets"][widget_name]
                }
                dashboard_json["dashboard"]["widgets"].append(widget)

        return dashboard_json

    def _generate_dashboard_insights(
        self,
        dashboard_data: Dict[str, Any],
        role: str
    ) -> List[Dict[str, Any]]:
        """
        Generate insights from dashboard data.

        Args:
            dashboard_data: Dashboard data
            role: User role

        Returns:
            List of insights
        """
        insights = []

        # Analyze widgets for insights
        for widget_name, widget_data in dashboard_data.get("widgets", {}).items():
            if widget_name == "revenue_overview":
                mrr_change = widget_data.get("data", {}).get("mrr", {}).get("change", "")
                if "+" in mrr_change:
                    insights.append({
                        "type": "positive",
                        "widget": widget_name,
                        "message": f"MRR growing at {mrr_change} - strong revenue momentum",
                        "priority": "high"
                    })

            elif widget_name == "at_risk_accounts":
                critical = widget_data.get("data", {}).get("critical", 0)
                if critical > 0:
                    insights.append({
                        "type": "alert",
                        "widget": widget_name,
                        "message": f"{critical} accounts at critical risk - immediate action needed",
                        "priority": "critical"
                    })

            elif widget_name == "pipeline_overview":
                stages = widget_data.get("data", {}).get("stages", [])
                if stages and len(stages) >= 2:
                    conversion_rate = (stages[-1]["count"] / stages[0]["count"]) * 100 if stages[0]["count"] > 0 else 0
                    insights.append({
                        "type": "info",
                        "widget": widget_name,
                        "message": f"Pipeline conversion rate: {conversion_rate:.1f}%",
                        "priority": "medium"
                    })

        # Add role-specific insights
        if role == "executive":
            insights.append({
                "type": "summary",
                "message": "Business metrics trending positively across key indicators",
                "priority": "high"
            })
        elif role == "cs_manager":
            insights.append({
                "type": "action",
                "message": "Focus on critical accounts to reduce churn risk",
                "priority": "high"
            })

        return insights

    def _format_dashboard_response(
        self,
        dashboard_json: Dict[str, Any],
        insights: List[Dict[str, Any]],
        role: str
    ) -> str:
        """Format dashboard generation response."""
        dashboard_info = dashboard_json.get("dashboard", {})

        response = f"""**{dashboard_info['name']}**

**Dashboard Configuration:**
- Role: {role.replace('_', ' ').title()}
- Time Range: {dashboard_info['time_range']}
- Refresh Interval: {dashboard_info['refresh_interval']}
- Widgets: {len(dashboard_info.get('widgets', []))}
- Generated: {dashboard_info['generated_at']}

"""

        # Key insights
        if insights:
            response += "**Key Insights:**\n"
            for insight in insights[:5]:
                icon = "🔴" if insight.get("type") == "alert" else "✅" if insight.get("type") == "positive" else "ℹ️"
                response += f"{icon} {insight['message']}\n"
            response += "\n"

        # Widget summary
        response += "**Dashboard Widgets:**\n"
        for widget in dashboard_info.get("widgets", [])[:10]:
            response += f"- {widget['name']} ({widget['config'].get('type', 'unknown')})\n"

        response += f"\n**Dashboard JSON:**\n```json\n{json.dumps(dashboard_json, indent=2)[:1000]}...\n```\n"
        response += "\n*Full dashboard JSON available in state.dashboard_json*"

        return response
