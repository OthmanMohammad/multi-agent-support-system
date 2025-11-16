"""
Expansion ROI Agent - TASK-2055

Calculates and presents ROI for expansion opportunities, generates compelling
business cases, and quantifies value realization for customer decision-makers.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("expansion_roi", tier="revenue", category="customer_success")
class ExpansionROIAgent(BaseAgent):
    """
    Expansion ROI Agent.

    Calculates expansion ROI by:
    - Quantifying cost savings and efficiency gains
    - Calculating revenue impact and growth potential
    - Measuring productivity improvements
    - Assessing risk reduction value
    - Generating TCO analysis
    - Creating executive-ready business cases
    - Benchmarking against industry standards
    """

    # Value categories and typical impact ranges
    VALUE_CATEGORIES = {
        "cost_savings": {
            "weight": 30,
            "typical_range": (0.10, 0.40),  # 10-40% cost reduction
            "metrics": ["reduced_manual_work", "lower_error_rates", "decreased_support_costs"]
        },
        "productivity_gains": {
            "weight": 25,
            "typical_range": (0.15, 0.50),  # 15-50% productivity increase
            "metrics": ["time_saved", "faster_processes", "automation_value"]
        },
        "revenue_impact": {
            "weight": 25,
            "typical_range": (0.05, 0.25),  # 5-25% revenue increase
            "metrics": ["faster_sales_cycles", "increased_conversion", "upsell_opportunities"]
        },
        "risk_reduction": {
            "weight": 12,
            "typical_range": (0.08, 0.30),  # 8-30% risk mitigation
            "metrics": ["compliance_value", "security_improvements", "reduced_downtime"]
        },
        "strategic_value": {
            "weight": 8,
            "typical_range": (0.05, 0.20),  # 5-20% strategic value
            "metrics": ["competitive_advantage", "innovation_enablement", "scalability"]
        }
    }

    # Industry benchmarks (typical payback periods in months)
    INDUSTRY_BENCHMARKS = {
        "technology": {"payback_months": 6, "typical_roi": 250},
        "finance": {"payback_months": 9, "typical_roi": 180},
        "healthcare": {"payback_months": 12, "typical_roi": 150},
        "retail": {"payback_months": 8, "typical_roi": 200},
        "manufacturing": {"payback_months": 10, "typical_roi": 170},
        "professional_services": {"payback_months": 7, "typical_roi": 220}
    }

    # Expansion types and typical impact
    EXPANSION_TYPES = {
        "tier_upgrade": {"complexity": "medium", "time_to_value": 60},
        "seat_expansion": {"complexity": "low", "time_to_value": 30},
        "department_expansion": {"complexity": "medium", "time_to_value": 90},
        "product_cross_sell": {"complexity": "high", "time_to_value": 120},
        "usage_increase": {"complexity": "low", "time_to_value": 30}
    }

    def __init__(self):
        config = AgentConfig(
            name="expansion_roi",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",
            temperature=0.3,
            max_tokens=800,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="customer_success",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Calculate ROI for expansion opportunities.

        Args:
            state: Current agent state with expansion opportunity data

        Returns:
            Updated state with ROI analysis and business case
        """
        self.logger.info("expansion_roi_calculation_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        expansion_opportunity = state.get("entities", {}).get("expansion_opportunity", {})
        contract_data = state.get("entities", {}).get("contract_data", {})
        customer_metadata = state.get("customer_metadata", {})
        usage_data = state.get("entities", {}).get("usage_data", {})

        self.logger.debug(
            "expansion_roi_calculation_details",
            customer_id=customer_id,
            expansion_type=expansion_opportunity.get("type", "unknown"),
            expansion_cost=expansion_opportunity.get("cost", 0)
        )

        # Calculate financial ROI
        financial_roi = self._calculate_financial_roi(
            expansion_opportunity,
            contract_data,
            customer_metadata
        )

        # Quantify value drivers
        value_analysis = self._quantify_value_drivers(
            expansion_opportunity,
            usage_data,
            customer_metadata
        )

        # Calculate TCO (Total Cost of Ownership)
        tco_analysis = self._calculate_tco(
            expansion_opportunity,
            contract_data,
            value_analysis
        )

        # Benchmark against industry
        benchmark_analysis = self._benchmark_against_industry(
            financial_roi,
            tco_analysis,
            customer_metadata
        )

        # Generate business case
        business_case = self._generate_business_case(
            expansion_opportunity,
            financial_roi,
            value_analysis,
            tco_analysis,
            benchmark_analysis
        )

        # Create executive summary
        executive_summary = self._create_executive_summary(
            expansion_opportunity,
            financial_roi,
            value_analysis,
            business_case
        )

        # Format response
        response = self._format_roi_report(
            expansion_opportunity,
            financial_roi,
            value_analysis,
            tco_analysis,
            benchmark_analysis,
            business_case,
            executive_summary
        )

        state["agent_response"] = response
        state["expansion_roi_percentage"] = financial_roi["roi_percentage"]
        state["payback_months"] = financial_roi["payback_months"]
        state["net_value"] = financial_roi["net_value_3yr"]
        state["recommendation"] = business_case["recommendation"]
        state["roi_analysis"] = financial_roi
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "expansion_roi_calculation_completed",
            customer_id=customer_id,
            roi_percentage=financial_roi["roi_percentage"],
            payback_months=financial_roi["payback_months"],
            recommendation=business_case["recommendation"]
        )

        return state

    def _calculate_financial_roi(
        self,
        expansion_opportunity: Dict[str, Any],
        contract_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate financial ROI metrics.

        Args:
            expansion_opportunity: Expansion details
            contract_data: Current contract information
            customer_metadata: Customer profile

        Returns:
            Financial ROI analysis
        """
        # Extract expansion costs
        expansion_cost = expansion_opportunity.get("cost", 0)
        expansion_type = expansion_opportunity.get("type", "tier_upgrade")
        annual_value = expansion_opportunity.get("annual_value", expansion_cost)

        # Calculate implementation costs
        implementation_cost = self._estimate_implementation_cost(
            expansion_type,
            expansion_cost,
            customer_metadata
        )

        # Total investment
        total_investment = expansion_cost + implementation_cost

        # Calculate benefits over 3 years
        year1_benefit = annual_value * 0.7  # Ramp-up in year 1
        year2_benefit = annual_value * 1.0
        year3_benefit = annual_value * 1.15  # Growth in year 3

        total_benefit_3yr = year1_benefit + year2_benefit + year3_benefit

        # Net value
        net_value_3yr = total_benefit_3yr - (total_investment + (expansion_cost * 2))  # 3 years of costs

        # ROI percentage
        if total_investment > 0:
            roi_percentage = (net_value_3yr / total_investment) * 100
        else:
            roi_percentage = 0

        # Payback period
        cumulative = -total_investment
        payback_months = 0
        monthly_benefit = annual_value / 12

        for month in range(1, 61):  # Check up to 5 years
            if month <= 12:
                cumulative += monthly_benefit * 0.7
            else:
                cumulative += monthly_benefit

            if cumulative >= 0 and payback_months == 0:
                payback_months = month
                break

        if payback_months == 0:
            payback_months = 60  # Cap at 5 years

        # NPV calculation (simplified, 10% discount rate)
        discount_rate = 0.10
        npv = -total_investment
        for year in range(1, 4):
            benefit = [year1_benefit, year2_benefit, year3_benefit][year - 1]
            cost = expansion_cost
            npv += (benefit - cost) / ((1 + discount_rate) ** year)

        return {
            "expansion_cost": expansion_cost,
            "implementation_cost": implementation_cost,
            "total_investment": total_investment,
            "annual_value": annual_value,
            "year1_benefit": int(year1_benefit),
            "year2_benefit": int(year2_benefit),
            "year3_benefit": int(year3_benefit),
            "total_benefit_3yr": int(total_benefit_3yr),
            "net_value_3yr": int(net_value_3yr),
            "roi_percentage": round(roi_percentage, 1),
            "payback_months": payback_months,
            "npv": int(npv)
        }

    def _estimate_implementation_cost(
        self,
        expansion_type: str,
        expansion_cost: int,
        customer_metadata: Dict[str, Any]
    ) -> int:
        """Estimate one-time implementation costs."""
        type_config = self.EXPANSION_TYPES.get(expansion_type, {})
        complexity = type_config.get("complexity", "medium")

        # Implementation as % of expansion cost
        complexity_multipliers = {
            "low": 0.05,      # 5% for simple expansions
            "medium": 0.15,   # 15% for moderate complexity
            "high": 0.30      # 30% for complex expansions
        }

        multiplier = complexity_multipliers.get(complexity, 0.15)
        base_implementation = int(expansion_cost * multiplier)

        # Adjust for company size (larger companies need more change management)
        company_size = customer_metadata.get("company_size", "medium")
        size_multipliers = {"small": 0.8, "medium": 1.0, "large": 1.3, "enterprise": 1.5}

        implementation_cost = int(base_implementation * size_multipliers.get(company_size, 1.0))

        return implementation_cost

    def _quantify_value_drivers(
        self,
        expansion_opportunity: Dict[str, Any],
        usage_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Quantify value across different categories.

        Args:
            expansion_opportunity: Expansion details
            usage_data: Usage patterns
            customer_metadata: Customer profile

        Returns:
            Quantified value drivers
        """
        total_employees = customer_metadata.get("total_employees", 100)
        avg_salary = customer_metadata.get("avg_employee_salary", 75000)
        annual_revenue = customer_metadata.get("annual_revenue", 10000000)

        value_drivers = {}

        # Cost savings
        cost_savings = self._calculate_cost_savings(
            expansion_opportunity,
            total_employees,
            avg_salary
        )
        value_drivers["cost_savings"] = cost_savings

        # Productivity gains
        productivity_gains = self._calculate_productivity_gains(
            expansion_opportunity,
            total_employees,
            avg_salary,
            usage_data
        )
        value_drivers["productivity_gains"] = productivity_gains

        # Revenue impact
        revenue_impact = self._calculate_revenue_impact(
            expansion_opportunity,
            annual_revenue,
            usage_data
        )
        value_drivers["revenue_impact"] = revenue_impact

        # Risk reduction
        risk_reduction = self._calculate_risk_reduction(
            expansion_opportunity,
            annual_revenue
        )
        value_drivers["risk_reduction"] = risk_reduction

        # Strategic value
        strategic_value = self._calculate_strategic_value(
            expansion_opportunity,
            customer_metadata
        )
        value_drivers["strategic_value"] = strategic_value

        # Calculate total value
        total_annual_value = sum(
            driver["annual_value"]
            for driver in value_drivers.values()
        )

        return {
            "value_drivers": value_drivers,
            "total_annual_value": int(total_annual_value),
            "value_breakdown": {
                category: driver["annual_value"]
                for category, driver in value_drivers.items()
            }
        }

    def _calculate_cost_savings(
        self,
        expansion_opportunity: Dict[str, Any],
        total_employees: int,
        avg_salary: int
    ) -> Dict[str, Any]:
        """Calculate cost savings value."""
        # Estimate time saved per employee per week
        hours_saved_per_week = expansion_opportunity.get("estimated_hours_saved", 2)
        affected_employees = expansion_opportunity.get("affected_employees", int(total_employees * 0.3))

        # Calculate hourly rate
        hourly_rate = avg_salary / 2080  # 52 weeks * 40 hours

        # Annual savings
        annual_hours_saved = hours_saved_per_week * 52 * affected_employees
        annual_value = int(annual_hours_saved * hourly_rate)

        return {
            "annual_value": annual_value,
            "hours_saved_annually": int(annual_hours_saved),
            "affected_employees": affected_employees,
            "metrics": [
                f"{hours_saved_per_week} hours saved per employee per week",
                f"{affected_employees} employees impacted",
                f"${annual_value:,} in labor cost savings"
            ]
        }

    def _calculate_productivity_gains(
        self,
        expansion_opportunity: Dict[str, Any],
        total_employees: int,
        avg_salary: int,
        usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate productivity improvement value."""
        # Productivity increase percentage
        productivity_increase_pct = expansion_opportunity.get("productivity_increase_pct", 15)
        affected_employees = expansion_opportunity.get("affected_employees", int(total_employees * 0.4))

        # Value of productivity increase
        employee_value = avg_salary * 1.4  # Include benefits
        annual_value = int(affected_employees * employee_value * (productivity_increase_pct / 100))

        return {
            "annual_value": annual_value,
            "productivity_increase_pct": productivity_increase_pct,
            "affected_employees": affected_employees,
            "metrics": [
                f"{productivity_increase_pct}% productivity increase",
                f"{affected_employees} employees more efficient",
                f"${annual_value:,} in productivity gains"
            ]
        }

    def _calculate_revenue_impact(
        self,
        expansion_opportunity: Dict[str, Any],
        annual_revenue: int,
        usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate revenue impact value."""
        # Revenue increase percentage
        revenue_increase_pct = expansion_opportunity.get("revenue_increase_pct", 5)

        # Be conservative - cap at actual expansion capabilities
        max_impact_pct = min(revenue_increase_pct, 15)

        annual_value = int(annual_revenue * (max_impact_pct / 100))

        return {
            "annual_value": annual_value,
            "revenue_increase_pct": max_impact_pct,
            "metrics": [
                f"{max_impact_pct}% revenue growth enabled",
                f"${annual_value:,} in incremental revenue",
                "Faster sales cycles and higher conversion"
            ]
        }

    def _calculate_risk_reduction(
        self,
        expansion_opportunity: Dict[str, Any],
        annual_revenue: int
    ) -> Dict[str, Any]:
        """Calculate risk reduction value."""
        # Risk categories
        compliance_value = expansion_opportunity.get("compliance_value", 0)
        security_value = expansion_opportunity.get("security_value", 0)
        downtime_reduction = expansion_opportunity.get("downtime_reduction_hours", 0)

        # Downtime cost (estimated)
        hourly_downtime_cost = annual_revenue / 8760  # Revenue per hour
        downtime_value = int(downtime_reduction * hourly_downtime_cost)

        annual_value = compliance_value + security_value + downtime_value

        metrics = []
        if compliance_value > 0:
            metrics.append(f"${compliance_value:,} in compliance risk mitigation")
        if security_value > 0:
            metrics.append(f"${security_value:,} in security improvements")
        if downtime_value > 0:
            metrics.append(f"{downtime_reduction} hours downtime prevented (${downtime_value:,})")

        return {
            "annual_value": annual_value,
            "compliance_value": compliance_value,
            "security_value": security_value,
            "downtime_value": downtime_value,
            "metrics": metrics if metrics else ["Risk mitigation value"]
        }

    def _calculate_strategic_value(
        self,
        expansion_opportunity: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate strategic value (harder to quantify)."""
        # Strategic value is often estimated as % of total investment
        expansion_cost = expansion_opportunity.get("cost", 0)

        # Conservative estimate: 10-20% of expansion cost annually
        strategic_multiplier = 0.15
        annual_value = int(expansion_cost * strategic_multiplier)

        return {
            "annual_value": annual_value,
            "metrics": [
                "Competitive advantage in market",
                "Future innovation enablement",
                "Scalability for growth"
            ]
        }

    def _calculate_tco(
        self,
        expansion_opportunity: Dict[str, Any],
        contract_data: Dict[str, Any],
        value_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate Total Cost of Ownership."""
        expansion_cost = expansion_opportunity.get("cost", 0)

        # 3-year TCO
        year1_cost = expansion_cost + expansion_opportunity.get("implementation_cost", 0)
        year2_cost = expansion_cost
        year3_cost = expansion_cost

        total_cost_3yr = year1_cost + year2_cost + year3_cost

        # Benefits
        total_benefit_3yr = value_analysis["total_annual_value"] * 2.85  # Year 1 ramp + years 2-3

        # TCO ratio (benefit / cost)
        if total_cost_3yr > 0:
            tco_ratio = total_benefit_3yr / total_cost_3yr
        else:
            tco_ratio = 0

        return {
            "year1_cost": year1_cost,
            "year2_cost": year2_cost,
            "year3_cost": year3_cost,
            "total_cost_3yr": total_cost_3yr,
            "total_benefit_3yr": int(total_benefit_3yr),
            "tco_ratio": round(tco_ratio, 2),
            "net_benefit_3yr": int(total_benefit_3yr - total_cost_3yr)
        }

    def _benchmark_against_industry(
        self,
        financial_roi: Dict[str, Any],
        tco_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Benchmark ROI against industry standards."""
        industry = customer_metadata.get("industry", "technology")
        benchmark = self.INDUSTRY_BENCHMARKS.get(
            industry,
            self.INDUSTRY_BENCHMARKS["technology"]
        )

        # Compare metrics
        payback_comparison = "faster" if financial_roi["payback_months"] < benchmark["payback_months"] else "slower"
        roi_comparison = "higher" if financial_roi["roi_percentage"] > benchmark["typical_roi"] else "lower"

        return {
            "industry": industry,
            "benchmark_payback_months": benchmark["payback_months"],
            "benchmark_roi": benchmark["typical_roi"],
            "actual_payback_months": financial_roi["payback_months"],
            "actual_roi": financial_roi["roi_percentage"],
            "payback_comparison": payback_comparison,
            "roi_comparison": roi_comparison,
            "payback_vs_benchmark": financial_roi["payback_months"] - benchmark["payback_months"],
            "roi_vs_benchmark": round(financial_roi["roi_percentage"] - benchmark["typical_roi"], 1)
        }

    def _generate_business_case(
        self,
        expansion_opportunity: Dict[str, Any],
        financial_roi: Dict[str, Any],
        value_analysis: Dict[str, Any],
        tco_analysis: Dict[str, Any],
        benchmark_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive business case."""
        # Determine recommendation strength
        if financial_roi["roi_percentage"] > 200 and financial_roi["payback_months"] <= 12:
            recommendation = "strongly_recommended"
            confidence = "high"
        elif financial_roi["roi_percentage"] > 100 and financial_roi["payback_months"] <= 18:
            recommendation = "recommended"
            confidence = "medium-high"
        elif financial_roi["roi_percentage"] > 50:
            recommendation = "favorable"
            confidence = "medium"
        else:
            recommendation = "needs_analysis"
            confidence = "low"

        # Key selling points
        selling_points = []

        if financial_roi["payback_months"] <= 12:
            selling_points.append(f"Fast payback: {financial_roi['payback_months']} months")

        if financial_roi["roi_percentage"] > 150:
            selling_points.append(f"Exceptional ROI: {financial_roi['roi_percentage']:.0f}%")

        if tco_analysis["tco_ratio"] > 3:
            selling_points.append(f"Strong value ratio: {tco_analysis['tco_ratio']:.1f}x return on investment")

        if benchmark_analysis["payback_comparison"] == "faster":
            selling_points.append(f"Faster payback than industry average")

        # Risk factors
        risk_factors = []

        if financial_roi["payback_months"] > 24:
            risk_factors.append("Long payback period - requires long-term commitment")

        if financial_roi["implementation_cost"] > financial_roi["expansion_cost"] * 0.3:
            risk_factors.append("Significant implementation costs")

        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "selling_points": selling_points,
            "risk_factors": risk_factors if risk_factors else ["Low risk - strong business case"],
            "decision_criteria": [
                f"ROI: {financial_roi['roi_percentage']:.0f}% over 3 years",
                f"Payback: {financial_roi['payback_months']} months",
                f"Net Value: ${financial_roi['net_value_3yr']:,} over 3 years"
            ]
        }

    def _create_executive_summary(
        self,
        expansion_opportunity: Dict[str, Any],
        financial_roi: Dict[str, Any],
        value_analysis: Dict[str, Any],
        business_case: Dict[str, Any]
    ) -> str:
        """Create executive summary for business case."""
        expansion_type = expansion_opportunity.get("type", "expansion").replace("_", " ").title()

        summary = f"""
**Investment:** ${financial_roi['total_investment']:,}
**3-Year Return:** ${financial_roi['total_benefit_3yr']:,}
**Net Value:** ${financial_roi['net_value_3yr']:,}
**ROI:** {financial_roi['roi_percentage']:.0f}%
**Payback:** {financial_roi['payback_months']} months

**Recommendation:** {business_case['recommendation'].replace('_', ' ').title()}

**Key Value Drivers:**
- Cost Savings: ${value_analysis['value_breakdown']['cost_savings']:,}/year
- Productivity Gains: ${value_analysis['value_breakdown']['productivity_gains']:,}/year
- Revenue Impact: ${value_analysis['value_breakdown']['revenue_impact']:,}/year
        """.strip()

        return summary

    def _format_roi_report(
        self,
        expansion_opportunity: Dict[str, Any],
        financial_roi: Dict[str, Any],
        value_analysis: Dict[str, Any],
        tco_analysis: Dict[str, Any],
        benchmark_analysis: Dict[str, Any],
        business_case: Dict[str, Any],
        executive_summary: str
    ) -> str:
        """Format comprehensive ROI report."""
        expansion_type = expansion_opportunity.get("type", "expansion").replace("_", " ").title()

        recommendation_emoji = {
            "strongly_recommended": "????",
            "recommended": "????",
            "favorable": "????",
            "needs_analysis": "????"
        }

        report = f"""**???? Expansion ROI Analysis: {expansion_type}**

**???? Executive Summary:**
{executive_summary}

**???? Financial Analysis:**
- Investment Required: ${financial_roi['total_investment']:,}
  - Expansion Cost: ${financial_roi['expansion_cost']:,}
  - Implementation: ${financial_roi['implementation_cost']:,}

**3-Year Projection:**
- Year 1 Benefit: ${financial_roi['year1_benefit']:,}
- Year 2 Benefit: ${financial_roi['year2_benefit']:,}
- Year 3 Benefit: ${financial_roi['year3_benefit']:,}
- Total Benefit: ${financial_roi['total_benefit_3yr']:,}
- Net Value: ${financial_roi['net_value_3yr']:,}

**Key Metrics:**
- ROI: {financial_roi['roi_percentage']:.1f}%
- Payback Period: {financial_roi['payback_months']} months
- NPV: ${financial_roi['npv']:,}

**???? Value Drivers (Annual):**
"""

        for category, driver in value_analysis["value_drivers"].items():
            report += f"\n**{category.replace('_', ' ').title()}:** ${driver['annual_value']:,}/year\n"
            for metric in driver["metrics"][:3]:
                report += f"  - {metric}\n"

        report += f"\n**Total Annual Value:** ${value_analysis['total_annual_value']:,}\n"

        # TCO Analysis
        report += f"\n**???? TCO Analysis (3 Years):**\n"
        report += f"- Total Cost: ${tco_analysis['total_cost_3yr']:,}\n"
        report += f"- Total Benefit: ${tco_analysis['total_benefit_3yr']:,}\n"
        report += f"- Benefit/Cost Ratio: {tco_analysis['tco_ratio']:.2f}x\n"
        report += f"- Net Benefit: ${tco_analysis['net_benefit_3yr']:,}\n"

        # Industry benchmark
        report += f"\n**???? Industry Benchmark ({benchmark_analysis['industry'].title()}):**\n"
        report += f"- Industry Avg Payback: {benchmark_analysis['benchmark_payback_months']} months\n"
        report += f"- Your Payback: {benchmark_analysis['actual_payback_months']} months ({benchmark_analysis['payback_comparison'].title()})\n"
        report += f"- Industry Avg ROI: {benchmark_analysis['benchmark_roi']}%\n"
        report += f"- Your ROI: {benchmark_analysis['actual_roi']:.0f}% ({benchmark_analysis['roi_comparison'].title()})\n"

        # Business case recommendation
        rec_emoji = recommendation_emoji.get(business_case['recommendation'], '???')
        report += f"\n**??? Business Case Recommendation** {rec_emoji}\n"
        report += f"**Decision:** {business_case['recommendation'].replace('_', ' ').title()}\n"
        report += f"**Confidence:** {business_case['confidence'].title()}\n\n"

        if business_case["selling_points"]:
            report += "**Key Selling Points:**\n"
            for point in business_case["selling_points"]:
                report += f"- {point}\n"

        if business_case["risk_factors"]:
            report += "\n**Risk Factors:**\n"
            for risk in business_case["risk_factors"]:
                report += f"- {risk}\n"

        report += "\n**Decision Criteria:**\n"
        for criterion in business_case["decision_criteria"]:
            report += f"- {criterion}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Expansion ROI Agent (TASK-2055)")
        print("=" * 70)

        agent = ExpansionROIAgent()

        # Test 1: Strong ROI scenario
        print("\n\nTest 1: Strong ROI Expansion")
        print("-" * 70)

        state1 = create_initial_state(
            "Calculate expansion ROI",
            context={
                "customer_id": "cust_strong_roi",
                "customer_metadata": {
                    "industry": "technology",
                    "total_employees": 200,
                    "avg_employee_salary": 85000,
                    "annual_revenue": 25000000,
                    "company_size": "medium"
                }
            }
        )
        state1["entities"] = {
            "expansion_opportunity": {
                "type": "tier_upgrade",
                "cost": 50000,
                "annual_value": 180000,
                "estimated_hours_saved": 5,
                "affected_employees": 80,
                "productivity_increase_pct": 20,
                "revenue_increase_pct": 8,
                "compliance_value": 15000,
                "downtime_reduction_hours": 100
            },
            "contract_data": {
                "contract_value": 100000
            },
            "usage_data": {}
        }

        result1 = await agent.process(state1)

        print(f"ROI: {result1['expansion_roi_percentage']:.1f}%")
        print(f"Payback: {result1['payback_months']} months")
        print(f"Net Value (3yr): ${result1['net_value']:,}")
        print(f"Recommendation: {result1['recommendation']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Moderate ROI scenario
        print("\n\n" + "=" * 70)
        print("Test 2: Moderate ROI Expansion")
        print("-" * 70)

        state2 = create_initial_state(
            "Analyze expansion ROI",
            context={
                "customer_id": "cust_moderate_roi",
                "customer_metadata": {
                    "industry": "healthcare",
                    "total_employees": 500,
                    "avg_employee_salary": 70000,
                    "annual_revenue": 50000000,
                    "company_size": "large"
                }
            }
        )
        state2["entities"] = {
            "expansion_opportunity": {
                "type": "department_expansion",
                "cost": 75000,
                "annual_value": 125000,
                "estimated_hours_saved": 3,
                "affected_employees": 100,
                "productivity_increase_pct": 12,
                "revenue_increase_pct": 4
            },
            "contract_data": {
                "contract_value": 150000
            },
            "usage_data": {}
        }

        result2 = await agent.process(state2)

        print(f"ROI: {result2['expansion_roi_percentage']:.1f}%")
        print(f"Payback: {result2['payback_months']} months")
        print(f"Recommendation: {result2['recommendation']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:700]}...")

    asyncio.run(test())
