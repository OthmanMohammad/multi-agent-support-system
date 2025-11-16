"""
Usage Optimizer Agent - TASK-3014

Advises customers on optimizing their usage to reduce costs and stay within plan limits.
Provides actionable recommendations based on usage patterns.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("usage_optimizer", tier="revenue", category="monetization")
class UsageOptimizer(BaseAgent):
    """
    Usage Optimizer Agent - Helps customers optimize usage and reduce costs.

    Handles:
    - Analyze usage patterns for inefficiencies
    - Identify cost-saving opportunities
    - Recommend usage optimizations
    - Calculate potential savings
    - Provide best practices by metric
    - Monitor optimization implementation
    - Track savings realized
    - Improve customer value perception
    """

    # Optimization strategies by metric
    OPTIMIZATION_STRATEGIES = {
        "api_calls": {
            "high_usage_tips": [
                "Implement caching layer (potential 40% reduction)",
                "Use batch API endpoints instead of single calls",
                "Reduce polling frequency from real-time to 5-minute intervals",
                "Eliminate redundant API calls in application logic"
            ],
            "medium_usage_tips": [
                "Cache frequently accessed data",
                "Implement request deduplication",
                "Optimize query patterns"
            ],
            "low_usage_tips": [
                "Monitor for unexpected spikes",
                "Review API call patterns periodically"
            ]
        },
        "storage_gb": {
            "high_usage_tips": [
                "Archive data older than 90 days (potential 60% reduction)",
                "Compress large files before upload",
                "Delete duplicate and unused files",
                "Implement data lifecycle policies"
            ],
            "medium_usage_tips": [
                "Enable automatic compression",
                "Archive old attachments",
                "Review storage usage monthly"
            ],
            "low_usage_tips": [
                "Set up automatic cleanup policies",
                "Monitor storage growth trends"
            ]
        },
        "seats_active": {
            "high_usage_tips": [
                "Remove inactive users (last login >90 days)",
                "Consolidate roles and permissions",
                "Review contractor and temp access",
                "Implement just-in-time provisioning"
            ],
            "medium_usage_tips": [
                "Audit user list monthly",
                "Remove offboarded employees promptly",
                "Share accounts where appropriate"
            ],
            "low_usage_tips": [
                "Monitor seat utilization regularly",
                "Plan for growth efficiently"
            ]
        },
        "tickets_created": {
            "high_usage_tips": [
                "Implement self-service knowledge base",
                "Train users on common workflows",
                "Consolidate related tickets",
                "Automate routine requests"
            ],
            "medium_usage_tips": [
                "Use templates for common requests",
                "Batch similar tickets",
                "Improve documentation"
            ],
            "low_usage_tips": [
                "Monitor ticket trends",
                "Identify training opportunities"
            ]
        }
    }

    # Inefficiency patterns to detect
    INEFFICIENCY_PATTERNS = {
        "redundant_calls": {
            "description": "Multiple API calls for same data",
            "solution": "Implement caching",
            "potential_savings": 0.30
        },
        "high_frequency_polling": {
            "description": "Excessive polling frequency",
            "solution": "Use webhooks or increase polling interval",
            "potential_savings": 0.50
        },
        "unused_storage": {
            "description": "Old data not archived",
            "solution": "Implement data lifecycle policies",
            "potential_savings": 0.40
        },
        "inactive_users": {
            "description": "Users not logged in >90 days",
            "solution": "Remove inactive accounts",
            "potential_savings": 0.20
        },
        "duplicate_tickets": {
            "description": "Similar tickets created repeatedly",
            "solution": "Improve documentation or training",
            "potential_savings": 0.25
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="usage_optimizer",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20241022",  # Sonnet for detailed analysis
            temperature=0.3,
            max_tokens=600,
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
        Analyze usage and provide optimization recommendations.

        Args:
            state: Current agent state with usage data

        Returns:
            Updated state with optimization recommendations
        """
        self.logger.info("usage_optimizer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        usage_data = state.get("current_usage", customer_metadata.get("usage_data", {}))

        # Analyze usage patterns
        usage_analysis = self._analyze_usage_patterns(
            usage_data,
            customer_metadata
        )

        # Identify inefficiencies
        inefficiencies = self._identify_inefficiencies(
            usage_data,
            usage_analysis,
            customer_metadata
        )

        # Generate optimization recommendations
        recommendations = self._generate_recommendations(
            usage_data,
            inefficiencies,
            customer_metadata
        )

        # Calculate potential savings
        potential_savings = self._calculate_potential_savings(
            recommendations,
            usage_data,
            customer_metadata
        )

        # Prioritize recommendations
        prioritized_recommendations = self._prioritize_recommendations(
            recommendations,
            potential_savings
        )

        # Get best practices
        best_practices = self._get_best_practices(usage_data)

        # Search KB for optimization guides
        kb_results = await self.search_knowledge_base(
            "usage optimization cost reduction",
            category="monetization",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_optimization_response(
            message,
            usage_analysis,
            inefficiencies,
            prioritized_recommendations,
            potential_savings,
            best_practices,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["usage_analysis"] = usage_analysis
        state["inefficiencies"] = inefficiencies
        state["optimization_recommendations"] = prioritized_recommendations
        state["potential_savings"] = potential_savings
        state["best_practices"] = best_practices
        state["status"] = "resolved"

        self.logger.info(
            "usage_optimizer_completed",
            recommendations_count=len(prioritized_recommendations),
            total_potential_savings=potential_savings.get("total_monthly_savings", 0)
        )

        return state

    def _analyze_usage_patterns(
        self,
        usage_data: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Analyze usage patterns to identify trends"""
        analysis = {
            "usage_levels": {},
            "trends": {},
            "efficiency_score": 0
        }

        plan_limits = customer_metadata.get("plan_limits", {})
        historical_usage = customer_metadata.get("historical_usage", [])

        for metric, current_value in usage_data.items():
            limit = plan_limits.get(f"{metric}_limit", float('inf'))

            # Determine usage level
            if limit != float('inf'):
                usage_percentage = (current_value / limit) * 100
                if usage_percentage >= 80:
                    level = "high"
                elif usage_percentage >= 50:
                    level = "medium"
                else:
                    level = "low"
            else:
                level = "unlimited"

            analysis["usage_levels"][metric] = level

            # Analyze trend
            if historical_usage and len(historical_usage) >= 2:
                prev_value = historical_usage[-1].get(metric, 0)
                if prev_value > 0:
                    growth_rate = ((current_value - prev_value) / prev_value) * 100
                    if growth_rate > 20:
                        trend = "increasing_fast"
                    elif growth_rate > 5:
                        trend = "increasing"
                    elif growth_rate < -20:
                        trend = "decreasing_fast"
                    elif growth_rate < -5:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "new"

                analysis["trends"][metric] = {
                    "direction": trend,
                    "growth_rate": round(growth_rate, 2)
                }

        # Calculate overall efficiency score (0-100)
        high_count = sum(1 for level in analysis["usage_levels"].values() if level == "high")
        total_count = len(analysis["usage_levels"])
        analysis["efficiency_score"] = max(0, 100 - (high_count / total_count * 30)) if total_count > 0 else 100

        return analysis

    def _identify_inefficiencies(
        self,
        usage_data: Dict,
        usage_analysis: Dict,
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Identify usage inefficiencies"""
        inefficiencies = []

        # Check for high usage patterns
        for metric, level in usage_analysis["usage_levels"].items():
            if level == "high":
                # Look for specific inefficiency patterns
                if metric == "api_calls":
                    inefficiencies.append({
                        "metric": metric,
                        "pattern": "high_frequency_polling",
                        "severity": "high",
                        **self.INEFFICIENCY_PATTERNS["high_frequency_polling"]
                    })
                elif metric == "storage_gb":
                    inefficiencies.append({
                        "metric": metric,
                        "pattern": "unused_storage",
                        "severity": "medium",
                        **self.INEFFICIENCY_PATTERNS["unused_storage"]
                    })
                elif metric == "seats_active":
                    inefficiencies.append({
                        "metric": metric,
                        "pattern": "inactive_users",
                        "severity": "medium",
                        **self.INEFFICIENCY_PATTERNS["inactive_users"]
                    })

        # Check for rapid growth
        for metric, trend_info in usage_analysis.get("trends", {}).items():
            if trend_info["direction"] in ["increasing_fast"]:
                inefficiencies.append({
                    "metric": metric,
                    "pattern": "rapid_growth",
                    "description": f"Usage growing at {trend_info['growth_rate']:.1f}% per period",
                    "solution": "Review growth drivers and optimize",
                    "severity": "medium",
                    "potential_savings": 0.15
                })

        return inefficiencies

    def _generate_recommendations(
        self,
        usage_data: Dict,
        inefficiencies: List[Dict],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Generate actionable optimization recommendations"""
        recommendations = []

        # Recommendations based on inefficiencies
        for inefficiency in inefficiencies:
            metric = inefficiency["metric"]
            recommendations.append({
                "metric": metric,
                "issue": inefficiency["description"],
                "recommendation": inefficiency["solution"],
                "potential_savings_percentage": inefficiency["potential_savings"],
                "priority": "high" if inefficiency["severity"] == "high" else "medium",
                "effort": "medium",
                "timeframe": "1-2 weeks"
            })

        # General recommendations based on usage levels
        plan_limits = customer_metadata.get("plan_limits", {})
        for metric, usage_value in usage_data.items():
            limit = plan_limits.get(f"{metric}_limit", float('inf'))

            if limit != float('inf'):
                usage_percentage = (usage_value / limit) * 100

                if usage_percentage >= 80:
                    level = "high"
                elif usage_percentage >= 50:
                    level = "medium"
                else:
                    level = "low"

                # Get appropriate tips
                tips_key = f"{level}_usage_tips"
                if metric in self.OPTIMIZATION_STRATEGIES:
                    tips = self.OPTIMIZATION_STRATEGIES[metric].get(tips_key, [])

                    for tip in tips[:2]:  # Top 2 tips per metric
                        recommendations.append({
                            "metric": metric,
                            "issue": f"{metric} at {usage_percentage:.1f}% of limit",
                            "recommendation": tip,
                            "potential_savings_percentage": 0.20 if level == "high" else 0.10,
                            "priority": "high" if level == "high" else "low",
                            "effort": "low",
                            "timeframe": "immediate"
                        })

        return recommendations

    def _calculate_potential_savings(
        self,
        recommendations: List[Dict],
        usage_data: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate potential cost savings from recommendations"""
        savings = {
            "by_metric": {},
            "total_monthly_savings": 0.0,
            "total_annual_savings": 0.0
        }

        overage_pricing = customer_metadata.get("overage_pricing", {})
        base_plan_cost = customer_metadata.get("base_plan_cost", 0)

        for rec in recommendations:
            metric = rec["metric"]
            usage_value = usage_data.get(metric, 0)
            savings_percentage = rec["potential_savings_percentage"]

            # Calculate savings in usage units
            usage_savings = usage_value * savings_percentage

            # Calculate cost savings
            rate = overage_pricing.get(metric, {}).get("rate", 0)
            monthly_savings = usage_savings * rate

            if metric not in savings["by_metric"]:
                savings["by_metric"][metric] = {
                    "monthly_savings": 0.0,
                    "annual_savings": 0.0
                }

            savings["by_metric"][metric]["monthly_savings"] += monthly_savings
            savings["by_metric"][metric]["annual_savings"] = monthly_savings * 12

            savings["total_monthly_savings"] += monthly_savings

        savings["total_annual_savings"] = savings["total_monthly_savings"] * 12
        savings["total_monthly_savings"] = round(savings["total_monthly_savings"], 2)
        savings["total_annual_savings"] = round(savings["total_annual_savings"], 2)

        return savings

    def _prioritize_recommendations(
        self,
        recommendations: List[Dict],
        potential_savings: Dict
    ) -> List[Dict[str, Any]]:
        """Prioritize recommendations by impact and effort"""

        # Score each recommendation
        for rec in recommendations:
            impact_score = rec["potential_savings_percentage"] * 10  # 0-10 scale
            effort_score = {"low": 3, "medium": 2, "high": 1}.get(rec["effort"], 2)
            priority_score = {"high": 3, "medium": 2, "low": 1}.get(rec["priority"], 2)

            rec["score"] = impact_score * effort_score * priority_score

        # Sort by score descending
        return sorted(recommendations, key=lambda x: x["score"], reverse=True)

    def _get_best_practices(self, usage_data: Dict) -> List[str]:
        """Get general best practices for usage optimization"""
        practices = [
            "Monitor usage trends weekly to catch issues early",
            "Set up automated alerts at 80% of plan limits",
            "Review and remove inactive users monthly",
            "Implement caching for frequently accessed data",
            "Use batch operations instead of individual calls",
            "Archive old data based on retention policies"
        ]

        return practices[:4]  # Top 4 practices

    async def _generate_optimization_response(
        self,
        message: str,
        usage_analysis: Dict,
        inefficiencies: List[Dict],
        recommendations: List[Dict],
        potential_savings: Dict,
        best_practices: List[str],
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate usage optimization response"""

        # Build analysis context
        analysis_context = f"""
Usage Efficiency Score: {usage_analysis['efficiency_score']}/100

Inefficiencies Detected: {len(inefficiencies)}
Optimization Opportunities: {len(recommendations)}
Potential Monthly Savings: ${potential_savings['total_monthly_savings']:.2f}
Potential Annual Savings: ${potential_savings['total_annual_savings']:.2f}
"""

        # Build top recommendations
        rec_context = ""
        if recommendations:
            rec_context = "\n\nTop Optimization Recommendations:\n"
            for rec in recommendations[:3]:  # Top 3
                rec_context += f"- {rec['recommendation']} (Potential {rec['potential_savings_percentage']*100:.0f}% reduction)\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nOptimization Guides:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Usage Optimizer specialist helping customers reduce costs and optimize usage.

Customer: {customer_metadata.get('company', 'Customer')}
Plan: {customer_metadata.get('plan_name', 'Unknown')}
{analysis_context}
{rec_context}

Your response should:
1. Acknowledge their usage patterns
2. Highlight optimization opportunities
3. Provide specific, actionable recommendations
4. Quantify potential savings
5. Prioritize quick wins (high impact, low effort)
6. Explain how to implement each recommendation
7. Be encouraging and helpful
8. Show value of staying on current plan vs upgrading"""

        user_prompt = f"""Customer message: {message}

Best Practices:
{chr(10).join(f'- {practice}' for practice in best_practices)}

{kb_context}

Generate helpful usage optimization advice."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
