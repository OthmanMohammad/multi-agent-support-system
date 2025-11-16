"""
Revenue Forecaster Agent - TASK-3045

Forecasts revenue based on pricing changes, expansion, and market trends.
Provides accurate revenue predictions to inform pricing and growth decisions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("revenue_forecaster", tier="revenue", category="monetization")
class RevenueForecaster(BaseAgent):
    """
    Revenue Forecaster Agent - Predicts future revenue.

    Handles:
    - Forecast revenue growth
    - Model pricing change impact
    - Project expansion revenue
    - Calculate churn impact
    - Analyze seasonality patterns
    - Provide scenario modeling
    - Track forecast accuracy
    - Generate revenue predictions
    """

    # Forecasting models
    FORECASTING_MODELS = {
        "linear_growth": {
            "description": "Linear trend extrapolation",
            "use_case": "Stable, predictable growth",
            "accuracy_range": 0.85
        },
        "exponential_growth": {
            "description": "Exponential growth curve",
            "use_case": "High-growth phase",
            "accuracy_range": 0.75
        },
        "cohort_based": {
            "description": "Cohort retention modeling",
            "use_case": "Subscription businesses",
            "accuracy_range": 0.90
        },
        "pipeline_based": {
            "description": "Sales pipeline conversion",
            "use_case": "New sales forecast",
            "accuracy_range": 0.80
        }
    }

    # Revenue components
    REVENUE_COMPONENTS = {
        "new_arr": {
            "description": "New customer annual recurring revenue",
            "typical_weight": 0.30
        },
        "expansion_arr": {
            "description": "Expansion from existing customers",
            "typical_weight": 0.25
        },
        "renewal_arr": {
            "description": "Renewed contracts",
            "typical_weight": 0.40
        },
        "churn_arr": {
            "description": "Lost revenue from churn",
            "typical_weight": -0.05
        }
    }

    # Seasonality patterns
    SEASONALITY_PATTERNS = {
        "Q1": {"multiplier": 0.95, "description": "Post-holiday slowdown"},
        "Q2": {"multiplier": 1.00, "description": "Normal activity"},
        "Q3": {"multiplier": 0.90, "description": "Summer slowdown"},
        "Q4": {"multiplier": 1.15, "description": "Year-end rush"}
    }

    # Confidence levels
    CONFIDENCE_LEVELS = {
        "high": (0.90, 1.10),      # +/- 10%
        "medium": (0.80, 1.20),    # +/- 20%
        "low": (0.70, 1.30)        # +/- 30%
    }

    def __init__(self):
        config = AgentConfig(
            name="revenue_forecaster",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20241022",  # Sonnet for complex forecasting
            temperature=0.2,  # Low for analytical accuracy
            max_tokens=800,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="monetization",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Generate revenue forecast.

        Args:
            state: Current agent state with historical revenue data

        Returns:
            Updated state with revenue forecast
        """
        self.logger.info("revenue_forecaster_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Analyze historical revenue
        historical_analysis = self._analyze_historical_revenue(customer_metadata)

        # Select forecasting model
        forecast_model = self._select_forecasting_model(
            historical_analysis,
            customer_metadata
        )

        # Generate base forecast
        base_forecast = self._generate_base_forecast(
            forecast_model,
            historical_analysis,
            customer_metadata
        )

        # Apply adjustments
        adjusted_forecast = self._apply_forecast_adjustments(
            base_forecast,
            customer_metadata
        )

        # Generate scenarios
        scenarios = self._generate_forecast_scenarios(
            adjusted_forecast,
            customer_metadata
        )

        # Calculate confidence intervals
        confidence_intervals = self._calculate_confidence_intervals(
            adjusted_forecast,
            historical_analysis
        )

        # Identify risks and opportunities
        risks_opportunities = self._identify_risks_opportunities(
            adjusted_forecast,
            scenarios,
            customer_metadata
        )

        # Generate revenue breakdown
        revenue_breakdown = self._generate_revenue_breakdown(
            adjusted_forecast,
            customer_metadata
        )

        # Search KB for forecasting resources
        kb_results = await self.search_knowledge_base(
            "revenue forecasting financial planning",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_forecast_response(
            message,
            historical_analysis,
            forecast_model,
            adjusted_forecast,
            scenarios,
            confidence_intervals,
            risks_opportunities,
            revenue_breakdown,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.87
        state["historical_analysis"] = historical_analysis
        state["forecast_model"] = forecast_model
        state["revenue_forecast"] = adjusted_forecast
        state["forecast_scenarios"] = scenarios
        state["confidence_intervals"] = confidence_intervals
        state["risks_opportunities"] = risks_opportunities
        state["revenue_breakdown"] = revenue_breakdown
        state["status"] = "resolved"

        self.logger.info(
            "revenue_forecaster_completed",
            forecast_arr=adjusted_forecast.get("annual_forecast", 0),
            confidence=confidence_intervals.get("confidence_level", "medium")
        )

        return state

    def _analyze_historical_revenue(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Analyze historical revenue trends"""
        historical_revenue = customer_metadata.get("historical_arr", [])

        if not historical_revenue or len(historical_revenue) < 2:
            return {
                "has_history": False,
                "current_arr": customer_metadata.get("current_arr", 0),
                "growth_rate": 0.15  # Default 15% growth assumption
            }

        # Calculate growth metrics
        current_arr = historical_revenue[-1]
        previous_arr = historical_revenue[-2] if len(historical_revenue) >= 2 else current_arr

        growth_rate = ((current_arr - previous_arr) / previous_arr) if previous_arr > 0 else 0

        # Calculate average growth
        if len(historical_revenue) >= 3:
            growth_rates = []
            for i in range(1, len(historical_revenue)):
                if historical_revenue[i-1] > 0:
                    gr = (historical_revenue[i] - historical_revenue[i-1]) / historical_revenue[i-1]
                    growth_rates.append(gr)
            avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        else:
            avg_growth = growth_rate

        # Calculate volatility
        if len(historical_revenue) >= 3:
            mean_revenue = sum(historical_revenue) / len(historical_revenue)
            variance = sum((x - mean_revenue) ** 2 for x in historical_revenue) / len(historical_revenue)
            volatility = (variance ** 0.5) / mean_revenue if mean_revenue > 0 else 0
        else:
            volatility = 0.10  # Default 10%

        return {
            "has_history": True,
            "current_arr": current_arr,
            "previous_arr": previous_arr,
            "growth_rate": round(growth_rate, 4),
            "avg_growth_rate": round(avg_growth, 4),
            "volatility": round(volatility, 4),
            "trend": "growing" if avg_growth > 0.05 else "stable" if avg_growth > -0.05 else "declining",
            "data_points": len(historical_revenue)
        }

    def _select_forecasting_model(
        self,
        historical: Dict,
        customer_metadata: Dict
    ) -> str:
        """Select appropriate forecasting model"""
        # For subscription businesses with good history
        if historical.get("data_points", 0) >= 6:
            return "cohort_based"

        # For high growth phase
        if historical.get("growth_rate", 0) > 0.30:
            return "exponential_growth"

        # For pipeline-heavy businesses
        if customer_metadata.get("pipeline_arr", 0) > customer_metadata.get("current_arr", 0) * 0.5:
            return "pipeline_based"

        # Default to linear
        return "linear_growth"

    def _generate_base_forecast(
        self,
        model: str,
        historical: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate base revenue forecast"""
        current_arr = historical["current_arr"]
        growth_rate = historical.get("avg_growth_rate", 0.15)

        # Forecast for next 12 months
        forecast_months = []
        monthly_arr = current_arr / 12

        for month in range(1, 13):
            if model == "linear_growth":
                # Linear growth
                forecasted_arr = current_arr * (1 + (growth_rate * month / 12))
            elif model == "exponential_growth":
                # Exponential growth (compounding)
                forecasted_arr = current_arr * ((1 + growth_rate) ** (month / 12))
            elif model == "cohort_based":
                # Cohort-based (with churn)
                churn_rate = customer_metadata.get("monthly_churn_rate", 0.02)
                expansion_rate = customer_metadata.get("expansion_rate", 0.10)
                new_arr_monthly = customer_metadata.get("new_arr_monthly", monthly_arr * 0.10)

                # Simplified cohort model
                retained_arr = current_arr * ((1 - churn_rate) ** month)
                expanded_arr = retained_arr * (expansion_rate * month / 12)
                new_customer_arr = new_arr_monthly * month

                forecasted_arr = retained_arr + expanded_arr + new_customer_arr
            else:  # pipeline_based
                pipeline_arr = customer_metadata.get("pipeline_arr", 0)
                win_rate = customer_metadata.get("win_rate", 0.25)
                forecasted_arr = current_arr + (pipeline_arr * win_rate * month / 12)

            forecast_months.append({
                "month": month,
                "arr": round(forecasted_arr, 2),
                "mrr": round(forecasted_arr / 12, 2)
            })

        # Annual forecast
        annual_forecast = forecast_months[-1]["arr"]

        return {
            "model": model,
            "current_arr": current_arr,
            "annual_forecast": annual_forecast,
            "forecast_growth_rate": round((annual_forecast - current_arr) / current_arr, 4) if current_arr > 0 else 0,
            "monthly_forecast": forecast_months,
            "quarterly_forecast": [
                {
                    "quarter": f"Q{i+1}",
                    "arr": forecast_months[i*3 + 2]["arr"]
                }
                for i in range(4)
            ]
        }

    def _apply_forecast_adjustments(
        self,
        base_forecast: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Apply adjustments to base forecast"""
        adjusted_forecast = base_forecast.copy()

        # Apply seasonality
        for i, month_forecast in enumerate(adjusted_forecast["monthly_forecast"]):
            month_num = (datetime.now().month + i) % 12 or 12
            quarter = f"Q{(month_num - 1) // 3 + 1}"
            seasonality_multiplier = self.SEASONALITY_PATTERNS[quarter]["multiplier"]

            month_forecast["arr_adjusted"] = round(
                month_forecast["arr"] * seasonality_multiplier,
                2
            )

        # Apply pricing change impact
        pricing_change = customer_metadata.get("planned_pricing_change", 0)
        if pricing_change != 0:
            impact_month = customer_metadata.get("pricing_change_month", 3)
            for month_forecast in adjusted_forecast["monthly_forecast"][impact_month:]:
                month_forecast["arr_adjusted"] = round(
                    month_forecast.get("arr_adjusted", month_forecast["arr"]) * (1 + pricing_change),
                    2
                )

        # Recalculate annual forecast
        adjusted_forecast["annual_forecast_adjusted"] = adjusted_forecast["monthly_forecast"][-1].get(
            "arr_adjusted",
            adjusted_forecast["monthly_forecast"][-1]["arr"]
        )

        return adjusted_forecast

    def _generate_forecast_scenarios(
        self,
        forecast: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Dict[str, Any]]:
        """Generate best/worst/expected case scenarios"""
        base_annual = forecast["annual_forecast_adjusted"]

        scenarios = {
            "pessimistic": {
                "annual_arr": round(base_annual * 0.80, 2),
                "assumptions": [
                    "20% lower growth than expected",
                    "Higher churn (5% vs 2%)",
                    "Slower sales cycles"
                ],
                "probability": 0.20
            },
            "expected": {
                "annual_arr": round(base_annual, 2),
                "assumptions": [
                    "Base forecast assumptions hold",
                    "Normal market conditions",
                    "Current trends continue"
                ],
                "probability": 0.60
            },
            "optimistic": {
                "annual_arr": round(base_annual * 1.25, 2),
                "assumptions": [
                    "25% higher growth than expected",
                    "Lower churn (1% vs 2%)",
                    "Faster deal velocity"
                ],
                "probability": 0.20
            }
        }

        return scenarios

    def _calculate_confidence_intervals(
        self,
        forecast: Dict,
        historical: Dict
    ) -> Dict[str, Any]:
        """Calculate forecast confidence intervals"""
        volatility = historical.get("volatility", 0.15)
        data_quality = "high" if historical.get("data_points", 0) >= 12 else "medium" if historical.get("data_points", 0) >= 6 else "low"

        # Determine confidence level based on data quality and volatility
        if data_quality == "high" and volatility < 0.10:
            confidence_level = "high"
        elif data_quality == "low" or volatility > 0.25:
            confidence_level = "low"
        else:
            confidence_level = "medium"

        lower_bound, upper_bound = self.CONFIDENCE_LEVELS[confidence_level]

        annual_forecast = forecast["annual_forecast_adjusted"]

        return {
            "confidence_level": confidence_level,
            "forecast": annual_forecast,
            "lower_bound": round(annual_forecast * lower_bound, 2),
            "upper_bound": round(annual_forecast * upper_bound, 2),
            "margin_of_error": round((upper_bound - 1) * 100, 0),
            "data_quality": data_quality
        }

    def _identify_risks_opportunities(
        self,
        forecast: Dict,
        scenarios: Dict,
        customer_metadata: Dict
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Identify risks and opportunities affecting forecast"""
        risks = []
        opportunities = []

        # Risks
        churn_rate = customer_metadata.get("monthly_churn_rate", 0.02)
        if churn_rate > 0.03:
            risks.append({
                "risk": "High churn rate",
                "impact": "Could reduce forecast by 10-15%",
                "mitigation": "Improve retention programs"
            })

        if customer_metadata.get("competitive_pressure", False):
            risks.append({
                "risk": "Increased competition",
                "impact": "Slower new customer acquisition",
                "mitigation": "Strengthen differentiation and value prop"
            })

        # Opportunities
        pipeline_arr = customer_metadata.get("pipeline_arr", 0)
        current_arr = forecast["current_arr"]
        if pipeline_arr > current_arr * 0.5:
            opportunities.append({
                "opportunity": "Strong pipeline",
                "impact": "Could exceed forecast by 10-20%",
                "action": "Focus on pipeline conversion"
            })

        expansion_opportunities = customer_metadata.get("expansion_opportunities_count", 0)
        if expansion_opportunities > 10:
            opportunities.append({
                "opportunity": "Multiple expansion opportunities",
                "impact": "Additional $50k-100k ARR potential",
                "action": "Prioritize land-and-expand motion"
            })

        return {
            "risks": risks,
            "opportunities": opportunities
        }

    def _generate_revenue_breakdown(
        self,
        forecast: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Break down forecasted revenue by component"""
        annual_forecast = forecast["annual_forecast_adjusted"]

        # Estimate component breakdown
        new_arr = annual_forecast * 0.30
        expansion_arr = annual_forecast * 0.25
        renewal_arr = annual_forecast * 0.45
        churn_impact = annual_forecast * -0.05

        return {
            "total_forecast": annual_forecast,
            "components": {
                "new_customer_arr": round(new_arr, 2),
                "expansion_arr": round(expansion_arr, 2),
                "renewal_arr": round(renewal_arr, 2),
                "churn_impact": round(churn_impact, 2)
            },
            "percentages": {
                "new_customer": "30%",
                "expansion": "25%",
                "renewal": "45%",
                "churn": "-5%"
            }
        }

    async def _generate_forecast_response(
        self,
        message: str,
        historical: Dict,
        model: str,
        forecast: Dict,
        scenarios: Dict,
        confidence: Dict,
        risks_opps: Dict,
        breakdown: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate revenue forecast response"""

        # Build historical context
        historical_context = f"""
Historical Analysis:
- Current ARR: ${historical['current_arr']:,.0f}
- Growth Rate: {historical.get('growth_rate', 0)*100:.1f}%
- Trend: {historical.get('trend', 'stable')}
- Data Points: {historical.get('data_points', 0)} months
"""

        # Build forecast context
        forecast_context = f"""
Revenue Forecast (12 Months):
- Model: {model}
- Forecast ARR: ${forecast['annual_forecast_adjusted']:,.0f}
- Projected Growth: {forecast.get('forecast_growth_rate', 0)*100:.1f}%
- Confidence: {confidence['confidence_level']} (+/- {confidence['margin_of_error']:.0f}%)
"""

        # Build scenarios context
        scenarios_context = "\n\nForecast Scenarios:\n"
        for scenario_name, scenario_data in scenarios.items():
            scenarios_context += f"- {scenario_name.title()}: ${scenario_data['annual_arr']:,.0f} ({scenario_data['probability']*100:.0f}% probability)\n"

        # Build breakdown context
        breakdown_context = f"""
Revenue Breakdown:
- New Customers: ${breakdown['components']['new_customer_arr']:,.0f} (30%)
- Expansion: ${breakdown['components']['expansion_arr']:,.0f} (25%)
- Renewals: ${breakdown['components']['renewal_arr']:,.0f} (45%)
"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nForecasting Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Revenue Forecaster providing financial projections.

{historical_context}
{forecast_context}

Your response should:
1. Present revenue forecast clearly
2. Explain forecasting methodology
3. Provide confidence intervals
4. Show scenario analysis
5. Break down revenue components
6. Identify risks and opportunities
7. Recommend actions to achieve forecast
8. Be data-driven and transparent
9. Help with financial planning

Tone: Analytical, professional, forward-looking"""

        user_prompt = f"""Customer message: {message}

{scenarios_context}

{breakdown_context}

Risks: {len(risks_opps['risks'])}
Opportunities: {len(risks_opps['opportunities'])}

{kb_context}

Generate a comprehensive revenue forecast."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
