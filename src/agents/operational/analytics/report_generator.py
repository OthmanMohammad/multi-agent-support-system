"""
Report Generator Agent - TASK-2018

Generates comprehensive weekly/monthly/quarterly executive reports.
Compiles data from multiple sources into structured narrative reports.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("report_generator", tier="operational", category="analytics")
class ReportGeneratorAgent(BaseAgent):
    """
    Report Generator Agent.

    Generates executive and operational reports:
    - Weekly operational reports
    - Monthly business reviews
    - Quarterly executive summaries
    - Custom period reports
    - Multi-metric compilation
    - Trend analysis and insights
    - Action items and recommendations
    """

    # Report templates
    REPORT_TEMPLATES = {
        "weekly": {
            "name": "Weekly Operations Report",
            "sections": ["executive_summary", "key_metrics", "highlights", "concerns", "action_items"],
            "metrics": ["customer_growth", "support_metrics", "product_usage"]
        },
        "monthly": {
            "name": "Monthly Business Review",
            "sections": ["executive_summary", "financial_metrics", "customer_metrics", "product_metrics", "team_performance", "strategic_initiatives"],
            "metrics": ["revenue", "customer_growth", "churn", "nps", "product_adoption"]
        },
        "quarterly": {
            "name": "Quarterly Executive Summary",
            "sections": ["executive_summary", "strategic_progress", "financial_performance", "market_position", "key_wins", "challenges", "roadmap"],
            "metrics": ["revenue", "growth_rate", "customer_acquisition", "market_share"]
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="report_generator",
            type=AgentType.GENERATOR,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=2000,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Generate comprehensive report.

        Args:
            state: Current agent state with report parameters

        Returns:
            Updated state with generated report
        """
        self.logger.info("report_generation_started")

        state = self.update_state(state)

        # Extract parameters
        report_type = state.get("entities", {}).get("report_type", "monthly")
        period_start = state.get("entities", {}).get("period_start", None)
        period_end = state.get("entities", {}).get("period_end", None)
        custom_sections = state.get("entities", {}).get("custom_sections", None)

        self.logger.debug(
            "report_generation_details",
            report_type=report_type,
            period_start=period_start,
            period_end=period_end
        )

        # Get report template
        template = self._get_report_template(report_type, custom_sections)

        # Collect data for all sections
        report_data = self._collect_report_data(template, period_start, period_end)

        # Generate each section
        sections = self._generate_report_sections(template, report_data)

        # Compile full report
        full_report = self._compile_full_report(
            template["name"],
            sections,
            period_start or "N/A",
            period_end or "N/A"
        )

        # Extract action items
        action_items = self._extract_action_items(sections)

        # Format response
        response = full_report

        state["agent_response"] = response
        state["full_report"] = full_report
        state["report_sections"] = sections
        state["action_items"] = action_items
        state["report_type"] = report_type
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "report_generation_completed",
            report_type=report_type,
            sections_generated=len(sections),
            action_items_count=len(action_items)
        )

        return state

    def _get_report_template(
        self,
        report_type: str,
        custom_sections: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Get report template."""
        if report_type in self.REPORT_TEMPLATES:
            template = self.REPORT_TEMPLATES[report_type].copy()
        else:
            template = self.REPORT_TEMPLATES["monthly"].copy()

        if custom_sections:
            template["sections"] = custom_sections

        return template

    def _collect_report_data(
        self,
        template: Dict[str, Any],
        period_start: Optional[str],
        period_end: Optional[str]
    ) -> Dict[str, Any]:
        """Collect data for report sections."""
        # Mock data collection - in production, query actual data sources
        return {
            "period": {
                "start": period_start or (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end": period_end or datetime.utcnow().strftime("%Y-%m-%d")
            },
            "financial_metrics": {
                "mrr": 542000,
                "mrr_growth": 8.5,
                "arr": 6504000,
                "churn_rate": 3.2,
                "expansion_revenue": 125000
            },
            "customer_metrics": {
                "total_customers": 15420,
                "new_customers": 342,
                "churned_customers": 87,
                "net_growth": 255,
                "nps": 52
            },
            "support_metrics": {
                "total_tickets": 1823,
                "avg_resolution_time": 18.5,
                "csat": 4.6,
                "backlog": 234
            },
            "product_metrics": {
                "active_users": 14230,
                "dau": 8450,
                "feature_adoption": 67.5,
                "api_calls": 1250000
            },
            "key_wins": [
                "Launched new analytics dashboard - 85% adoption",
                "Reduced support response time by 23%",
                "Closed largest enterprise deal ($150K ARR)"
            ],
            "concerns": [
                "Churn rate increased 0.8% from last period",
                "Support backlog growing - now at 234 tickets"
            ],
            "action_items": [
                "Launch churn reduction initiative",
                "Hire 2 additional support agents",
                "Complete Q3 feature roadmap review"
            ]
        }

    def _generate_report_sections(
        self,
        template: Dict[str, Any],
        report_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate content for each report section."""
        sections = {}

        for section_name in template["sections"]:
            sections[section_name] = self._generate_section_content(section_name, report_data)

        return sections

    def _generate_section_content(
        self,
        section_name: str,
        report_data: Dict[str, Any]
    ) -> str:
        """Generate content for a specific section."""
        if section_name == "executive_summary":
            financial = report_data.get("financial_metrics", {})
            customer = report_data.get("customer_metrics", {})

            return f"""The business delivered strong performance this period with MRR growing {financial.get('mrr_growth', 0)}% to ${financial.get('mrr', 0):,}. We acquired {customer.get('new_customers', 0)} new customers (net growth: {customer.get('net_growth', 0)}) while maintaining healthy retention metrics. Key achievements include our major product launches and improved customer satisfaction scores."""

        elif section_name == "key_metrics":
            financial = report_data.get("financial_metrics", {})
            customer = report_data.get("customer_metrics", {})
            support = report_data.get("support_metrics", {})

            return f"""**Financial:**
- MRR: ${financial.get('mrr', 0):,} ({financial.get('mrr_growth', 0):+.1f}%)
- ARR: ${financial.get('arr', 0):,}
- Churn Rate: {financial.get('churn_rate', 0)}%

**Customers:**
- Total: {customer.get('total_customers', 0):,}
- New: {customer.get('new_customers', 0)}
- Net Growth: {customer.get('net_growth', 0)}
- NPS: {customer.get('nps', 0)}

**Support:**
- Tickets: {support.get('total_tickets', 0):,}
- Avg Resolution: {support.get('avg_resolution_time', 0)}h
- CSAT: {support.get('csat', 0)}/5.0"""

        elif section_name == "highlights" or section_name == "key_wins":
            wins = report_data.get("key_wins", [])
            content = ""
            for win in wins:
                content += f"- {win}\n"
            return content.strip()

        elif section_name == "concerns" or section_name == "challenges":
            concerns = report_data.get("concerns", [])
            content = ""
            for concern in concerns:
                content += f"- {concern}\n"
            return content.strip()

        elif section_name == "action_items":
            items = report_data.get("action_items", [])
            content = ""
            for i, item in enumerate(items, 1):
                content += f"{i}. {item}\n"
            return content.strip()

        elif section_name == "financial_performance" or section_name == "financial_metrics":
            financial = report_data.get("financial_metrics", {})
            return f"""Revenue performance remained strong with MRR of ${financial.get('mrr', 0):,}, representing {financial.get('mrr_growth', 0):+.1f}% growth. ARR reached ${financial.get('arr', 0):,}. Expansion revenue contributed ${financial.get('expansion_revenue', 0):,} this period. Churn rate was {financial.get('churn_rate', 0)}%, slightly above target."""

        elif section_name == "customer_metrics":
            customer = report_data.get("customer_metrics", {})
            return f"""Customer base grew to {customer.get('total_customers', 0):,} total customers with {customer.get('new_customers', 0)} new acquisitions. We experienced {customer.get('churned_customers', 0)} churns, resulting in net growth of {customer.get('net_growth', 0)} customers. Customer satisfaction (NPS) stands at {customer.get('nps', 0)}."""

        elif section_name == "product_metrics":
            product = report_data.get("product_metrics", {})
            return f"""Product engagement remained healthy with {product.get('active_users', 0):,} active users and {product.get('dau', 0):,} daily active users. Feature adoption rate reached {product.get('feature_adoption', 0)}%. API usage totaled {product.get('api_calls', 0):,} calls."""

        else:
            return f"Section content for {section_name} would go here."

    def _compile_full_report(
        self,
        report_name: str,
        sections: Dict[str, str],
        period_start: str,
        period_end: str
    ) -> str:
        """Compile all sections into full report."""
        report = f"""# {report_name}

**Reporting Period:** {period_start} to {period_end}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

---

"""

        # Add each section
        section_titles = {
            "executive_summary": "Executive Summary",
            "key_metrics": "Key Metrics",
            "highlights": "Highlights & Achievements",
            "key_wins": "Key Wins",
            "concerns": "Areas of Concern",
            "challenges": "Challenges",
            "action_items": "Action Items",
            "financial_performance": "Financial Performance",
            "financial_metrics": "Financial Metrics",
            "customer_metrics": "Customer Metrics",
            "product_metrics": "Product Metrics",
            "support_metrics": "Support Metrics",
            "team_performance": "Team Performance",
            "strategic_initiatives": "Strategic Initiatives",
            "strategic_progress": "Strategic Progress",
            "market_position": "Market Position",
            "roadmap": "Roadmap & Priorities"
        }

        for section_name, content in sections.items():
            title = section_titles.get(section_name, section_name.replace("_", " ").title())
            report += f"## {title}\n\n{content}\n\n---\n\n"

        report += f"*End of Report*"

        return report

    def _extract_action_items(self, sections: Dict[str, str]) -> List[str]:
        """Extract action items from report."""
        action_items = []

        if "action_items" in sections:
            # Parse action items from section
            items_text = sections["action_items"]
            for line in items_text.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Remove numbering/bullets
                    clean_item = line.lstrip("0123456789.-) ").strip()
                    if clean_item:
                        action_items.append(clean_item)

        return action_items
