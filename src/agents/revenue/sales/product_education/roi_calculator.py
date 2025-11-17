"""
ROI Calculator Agent - TASK-1024

Calculates time savings ROI, cost savings ROI, and generates business case documents.
Performs payback period analysis with financial projections.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("roi_calculator", tier="revenue", category="sales")
class ROICalculator(BaseAgent):
    """
    ROI Calculator Agent - Specialist in ROI and business case analysis.

    Handles:
    - Time savings ROI calculations
    - Cost savings ROI calculations
    - Business case document generation
    - Payback period analysis
    - Financial projections (3-year)
    """

    # Average hourly costs by role
    HOURLY_COSTS = {
        "executive": 150,
        "manager": 85,
        "professional": 55,
        "support_staff": 35,
        "entry_level": 25
    }

    # Time savings multipliers by company size
    TIME_SAVINGS_MULTIPLIERS = {
        "small": 1.0,      # < 50 employees
        "medium": 1.5,     # 50-500 employees
        "large": 2.0,      # 500-1000 employees
        "enterprise": 3.0  # > 1000 employees
    }

    # Cost reduction categories
    COST_REDUCTION_AREAS = {
        "automation": {
            "avg_reduction": 0.60,  # 60% reduction in manual tasks
            "description": "Automated workflows reduce manual processing time"
        },
        "integration": {
            "avg_reduction": 0.45,  # 45% reduction in data entry
            "description": "Integrated systems eliminate duplicate data entry"
        },
        "analytics": {
            "avg_reduction": 0.70,  # 70% faster reporting
            "description": "Automated analytics reduce report generation time"
        },
        "collaboration": {
            "avg_reduction": 0.35,  # 35% reduction in coordination time
            "description": "Streamlined collaboration reduces meeting overhead"
        },
        "compliance": {
            "avg_reduction": 0.55,  # 55% faster compliance processes
            "description": "Automated compliance reduces audit preparation time"
        }
    }

    # Pricing tiers (annual per user)
    PRICING_TIERS = {
        "starter": 600,     # $50/month per user
        "professional": 1200,  # $100/month per user
        "enterprise": 2400     # $200/month per user
    }

    # ROI benchmarks
    EXCELLENT_ROI = 300  # 300% ROI or higher
    GOOD_ROI = 200       # 200-299% ROI
    ACCEPTABLE_ROI = 100 # 100-199% ROI

    def __init__(self):
        config = AgentConfig(
            name="roi_calculator",
            type=AgentType.ANALYZER,
            model="claude-3-5-sonnet-20240620",
            temperature=0.2,  # Low temperature for accuracy
            max_tokens=1500,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.MULTI_TURN
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process ROI calculation request"""
        self.logger.info("roi_calculator_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Extract ROI input parameters
        roi_params = self._extract_roi_parameters(customer_metadata, message)

        # Calculate time savings
        time_savings = self._calculate_time_savings(roi_params)

        # Calculate cost savings
        cost_savings = self._calculate_cost_savings(roi_params, time_savings)

        # Calculate investment (cost of solution)
        investment = self._calculate_investment(roi_params)

        # Calculate ROI metrics
        roi_metrics = self._calculate_roi_metrics(cost_savings, investment)

        # Generate payback period analysis
        payback_analysis = self._calculate_payback_period(cost_savings, investment)

        # Generate 3-year projection
        three_year_projection = self._generate_three_year_projection(
            cost_savings,
            investment
        )

        # Generate business case summary
        business_case = self._generate_business_case(
            roi_params,
            time_savings,
            cost_savings,
            roi_metrics,
            payback_analysis,
            three_year_projection
        )

        # Search KB for ROI case studies
        kb_results = await self.search_knowledge_base(
            f"roi case study {customer_metadata.get('industry', '')}",
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_roi_response(
            message,
            roi_metrics,
            payback_analysis,
            three_year_projection,
            business_case,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.92  # High confidence for numerical calculations
        state["roi_params"] = roi_params
        state["time_savings"] = time_savings
        state["cost_savings"] = cost_savings
        state["investment"] = investment
        state["roi_metrics"] = roi_metrics
        state["payback_analysis"] = payback_analysis
        state["three_year_projection"] = three_year_projection
        state["business_case"] = business_case
        state["status"] = "resolved"

        self.logger.info(
            "roi_calculator_completed",
            roi_percentage=roi_metrics["roi_percentage"],
            payback_months=payback_analysis["payback_months"]
        )

        return state

    def _extract_roi_parameters(
        self,
        customer_metadata: Dict,
        message: str
    ) -> Dict[str, Any]:
        """Extract parameters needed for ROI calculation"""
        company_size = customer_metadata.get("company_size", 100)

        # Determine company size category
        if company_size < 50:
            size_category = "small"
            affected_users = min(company_size, 20)
        elif company_size < 500:
            size_category = "medium"
            affected_users = min(company_size // 2, 100)
        elif company_size < 1000:
            size_category = "large"
            affected_users = min(company_size // 3, 300)
        else:
            size_category = "enterprise"
            affected_users = min(company_size // 4, 500)

        # Estimate hours saved per user per week
        hours_saved_per_week = 5  # Conservative default

        # Detect if specific hours mentioned in message
        message_lower = message.lower()
        if "hour" in message_lower:
            # Try to extract number
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                hours_saved_per_week = min(int(numbers[0]), 20)  # Cap at 20 hours/week

        return {
            "company_size": company_size,
            "size_category": size_category,
            "affected_users": affected_users,
            "hours_saved_per_week": hours_saved_per_week,
            "average_hourly_cost": self.HOURLY_COSTS["professional"],  # Default
            "industry": customer_metadata.get("industry", "technology")
        }

    def _calculate_time_savings(self, params: Dict) -> Dict[str, Any]:
        """Calculate time savings metrics"""
        hours_per_week = params["hours_saved_per_week"]
        affected_users = params["affected_users"]
        size_multiplier = self.TIME_SAVINGS_MULTIPLIERS[params["size_category"]]

        # Apply size multiplier for collaboration/network effects
        adjusted_hours_per_week = hours_per_week * size_multiplier

        # Calculate various timeframes
        hours_per_month = adjusted_hours_per_week * 4
        hours_per_year = adjusted_hours_per_week * 52

        total_hours_per_month = hours_per_month * affected_users
        total_hours_per_year = hours_per_year * affected_users

        return {
            "hours_per_user_per_week": adjusted_hours_per_week,
            "hours_per_user_per_month": hours_per_month,
            "hours_per_user_per_year": hours_per_year,
            "total_hours_per_month": total_hours_per_month,
            "total_hours_per_year": total_hours_per_year,
            "affected_users": affected_users
        }

    def _calculate_cost_savings(
        self,
        params: Dict,
        time_savings: Dict
    ) -> Dict[str, Any]:
        """Calculate cost savings from time savings"""
        hourly_cost = params["average_hourly_cost"]

        monthly_savings = time_savings["total_hours_per_month"] * hourly_cost
        annual_savings = time_savings["total_hours_per_year"] * hourly_cost

        # Additional cost reductions
        additional_savings = self._calculate_additional_savings(params)

        total_monthly_savings = monthly_savings + additional_savings["monthly"]
        total_annual_savings = annual_savings + additional_savings["annual"]

        return {
            "time_based_monthly": monthly_savings,
            "time_based_annual": annual_savings,
            "additional_monthly": additional_savings["monthly"],
            "additional_annual": additional_savings["annual"],
            "total_monthly": total_monthly_savings,
            "total_annual": total_annual_savings,
            "breakdown": additional_savings["breakdown"]
        }

    def _calculate_additional_savings(self, params: Dict) -> Dict[str, Any]:
        """Calculate additional cost savings beyond time"""
        # Estimate additional savings (reduced errors, better compliance, etc.)
        base_monthly = params["affected_users"] * 100  # $100 per user/month in soft savings

        breakdown = {
            "reduced_errors": base_monthly * 0.3,
            "improved_compliance": base_monthly * 0.2,
            "better_decision_making": base_monthly * 0.3,
            "reduced_turnover": base_monthly * 0.2
        }

        return {
            "monthly": base_monthly,
            "annual": base_monthly * 12,
            "breakdown": breakdown
        }

    def _calculate_investment(self, params: Dict) -> Dict[str, Any]:
        """Calculate total investment cost"""
        affected_users = params["affected_users"]
        company_size = params["company_size"]

        # Determine pricing tier
        if company_size > 500:
            tier = "enterprise"
        elif company_size > 100:
            tier = "professional"
        else:
            tier = "starter"

        annual_per_user = self.PRICING_TIERS[tier]
        annual_subscription = annual_per_user * affected_users

        # One-time costs
        implementation_cost = annual_subscription * 0.25  # 25% of annual for implementation
        training_cost = affected_users * 100  # $100 per user for training

        one_time_costs = implementation_cost + training_cost
        total_year_one = annual_subscription + one_time_costs

        return {
            "pricing_tier": tier,
            "annual_per_user": annual_per_user,
            "annual_subscription": annual_subscription,
            "implementation_cost": implementation_cost,
            "training_cost": training_cost,
            "one_time_costs": one_time_costs,
            "total_year_one": total_year_one,
            "annual_recurring": annual_subscription
        }

    def _calculate_roi_metrics(
        self,
        cost_savings: Dict,
        investment: Dict
    ) -> Dict[str, Any]:
        """Calculate ROI metrics"""
        annual_savings = cost_savings["total_annual"]
        year_one_cost = investment["total_year_one"]
        annual_recurring = investment["annual_recurring"]

        # Year 1 ROI (including one-time costs)
        year_one_net = annual_savings - year_one_cost
        year_one_roi = (year_one_net / year_one_cost) * 100 if year_one_cost > 0 else 0

        # Ongoing annual ROI (years 2+)
        annual_net = annual_savings - annual_recurring
        annual_roi = (annual_net / annual_recurring) * 100 if annual_recurring > 0 else 0

        # Determine ROI rating
        if annual_roi >= self.EXCELLENT_ROI:
            rating = "Excellent"
        elif annual_roi >= self.GOOD_ROI:
            rating = "Good"
        elif annual_roi >= self.ACCEPTABLE_ROI:
            rating = "Acceptable"
        else:
            rating = "Marginal"

        return {
            "year_one_roi_percentage": round(year_one_roi, 1),
            "annual_roi_percentage": round(annual_roi, 1),
            "roi_percentage": round(annual_roi, 1),  # Use annual for summary
            "rating": rating,
            "annual_net_benefit": annual_net,
            "year_one_net_benefit": year_one_net
        }

    def _calculate_payback_period(
        self,
        cost_savings: Dict,
        investment: Dict
    ) -> Dict[str, Any]:
        """Calculate payback period"""
        monthly_savings = cost_savings["total_monthly"]
        total_investment = investment["total_year_one"]

        if monthly_savings > 0:
            payback_months = total_investment / monthly_savings
        else:
            payback_months = 999  # Effectively never

        payback_months = round(payback_months, 1)

        # Determine if acceptable
        if payback_months <= 6:
            assessment = "Excellent - Very fast payback"
        elif payback_months <= 12:
            assessment = "Good - Payback within one year"
        elif payback_months <= 24:
            assessment = "Acceptable - Payback within two years"
        else:
            assessment = "Long - Payback exceeds two years"

        return {
            "payback_months": payback_months,
            "payback_years": round(payback_months / 12, 1),
            "monthly_savings": monthly_savings,
            "total_investment": total_investment,
            "assessment": assessment
        }

    def _generate_three_year_projection(
        self,
        cost_savings: Dict,
        investment: Dict
    ) -> Dict[str, Any]:
        """Generate 3-year financial projection"""
        annual_savings = cost_savings["total_annual"]
        annual_cost = investment["annual_recurring"]
        year_one_cost = investment["total_year_one"]

        # Year by year
        year_1 = {
            "savings": annual_savings,
            "costs": year_one_cost,
            "net_benefit": annual_savings - year_one_cost,
            "cumulative_benefit": annual_savings - year_one_cost
        }

        year_2 = {
            "savings": annual_savings * 1.1,  # 10% improvement as users get more efficient
            "costs": annual_cost,
            "net_benefit": (annual_savings * 1.1) - annual_cost,
            "cumulative_benefit": year_1["cumulative_benefit"] + ((annual_savings * 1.1) - annual_cost)
        }

        year_3 = {
            "savings": annual_savings * 1.2,  # 20% improvement by year 3
            "costs": annual_cost,
            "net_benefit": (annual_savings * 1.2) - annual_cost,
            "cumulative_benefit": year_2["cumulative_benefit"] + ((annual_savings * 1.2) - annual_cost)
        }

        total_3year_benefit = year_3["cumulative_benefit"]
        total_3year_investment = year_one_cost + (annual_cost * 2)

        return {
            "year_1": year_1,
            "year_2": year_2,
            "year_3": year_3,
            "total_3year_benefit": total_3year_benefit,
            "total_3year_investment": total_3year_investment,
            "total_3year_roi": round((total_3year_benefit / total_3year_investment) * 100, 1)
        }

    def _generate_business_case(
        self,
        params: Dict,
        time_savings: Dict,
        cost_savings: Dict,
        roi_metrics: Dict,
        payback_analysis: Dict,
        projection: Dict
    ) -> Dict[str, Any]:
        """Generate executive business case summary"""
        return {
            "executive_summary": {
                "roi": f"{roi_metrics['roi_percentage']}%",
                "payback_period": f"{payback_analysis['payback_months']} months",
                "annual_savings": f"${cost_savings['total_annual']:,.0f}",
                "3_year_benefit": f"${projection['total_3year_benefit']:,.0f}"
            },
            "investment_summary": {
                "year_one_cost": f"${payback_analysis['total_investment']:,.0f}",
                "annual_recurring": f"${cost_savings['total_annual']:,.0f}",
                "affected_users": params["affected_users"]
            },
            "value_drivers": [
                f"{time_savings['total_hours_per_year']:,.0f} hours saved annually",
                f"${cost_savings['total_annual']:,.0f} in annual cost savings",
                f"{roi_metrics['roi_percentage']}% ROI",
                f"Payback in {payback_analysis['payback_months']} months"
            ]
        }

    async def _generate_roi_response(
        self,
        message: str,
        roi_metrics: Dict,
        payback_analysis: Dict,
        projection: Dict,
        business_case: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate ROI analysis response"""

        # Build projection context
        projection_context = f"\n\n3-Year Financial Projection:\n"
        projection_context += f"Year 1: ${projection['year_1']['net_benefit']:,.0f} net benefit\n"
        projection_context += f"Year 2: ${projection['year_2']['net_benefit']:,.0f} net benefit\n"
        projection_context += f"Year 3: ${projection['year_3']['net_benefit']:,.0f} net benefit\n"
        projection_context += f"Cumulative 3-Year: ${projection['total_3year_benefit']:,.0f}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nSimilar customer ROI examples:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Case Study')}\n"

        system_prompt = f"""You are an ROI Calculator specialist helping prospects understand the financial value.

Financial Analysis Results:
- ROI: {roi_metrics['roi_percentage']}% ({roi_metrics['rating']})
- Payback Period: {payback_analysis['payback_months']} months
- Annual Savings: ${payback_analysis['monthly_savings'] * 12:,.0f}
- Total Investment: ${payback_analysis['total_investment']:,.0f}
- 3-Year Cumulative Benefit: ${projection['total_3year_benefit']:,.0f}

Company Profile:
- Industry: {customer_metadata.get('industry', 'Unknown')}
- Size: {customer_metadata.get('company_size', 'Unknown')} employees

Your response should:
1. Present ROI metrics clearly and confidently
2. Explain the payback period and what it means
3. Highlight the 3-year projection
4. Use specific numbers from the analysis
5. Make the business case compelling but realistic
6. Offer to provide detailed business case document
7. Use financial language appropriate for decision-makers"""

        user_prompt = f"""Customer message: {message}

{projection_context}
{kb_context}

Generate a compelling ROI analysis response with specific numbers."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    """Test harness for ROICalculator"""
    import asyncio
    from src.workflow.state import AgentState

    async def test_roi_calculator():
        agent = ROICalculator()

        # Test case 1: Medium company
        state1 = AgentState(
            current_message="What kind of ROI can we expect? We have about 10 hours per week of manual work.",
            customer_metadata={
                "company_size": 250,
                "industry": "technology",
                "title": "CFO"
            },
            messages=[],
            status="pending"
        )

        result1 = await agent.process(state1)
        print("Test 1 - Medium Company ROI:")
        print(f"ROI: {result1['roi_metrics']['roi_percentage']}%")
        print(f"Payback: {result1['payback_analysis']['payback_months']} months")
        print(f"3-Year Benefit: ${result1['three_year_projection']['total_3year_benefit']:,.0f}")
        print()

        # Test case 2: Enterprise
        state2 = AgentState(
            current_message="Can you calculate the ROI for our organization?",
            customer_metadata={
                "company_size": 2000,
                "industry": "finance",
                "title": "VP Operations"
            },
            messages=[],
            status="pending"
        )

        result2 = await agent.process(state2)
        print("Test 2 - Enterprise ROI:")
        print(f"Affected Users: {result2['roi_params']['affected_users']}")
        print(f"Annual Savings: ${result2['cost_savings']['total_annual']:,.0f}")
        print(f"Rating: {result2['roi_metrics']['rating']}")
        print()

    asyncio.run(test_roi_calculator())
