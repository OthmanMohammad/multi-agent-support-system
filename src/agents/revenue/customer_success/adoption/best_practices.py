"""
Best Practices Agent - TASK-2033

Shares best practices, provides templates and workflows, offers optimization tips,
and benchmarks customer performance against industry standards.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("best_practices", tier="revenue", category="customer_success")
class BestPracticesAgent(BaseAgent):
    """
    Best Practices Agent.

    Provides guidance and optimization by:
    - Sharing industry best practices
    - Recommending proven templates and workflows
    - Identifying optimization opportunities
    - Benchmarking against similar customers
    - Providing actionable improvement tips
    - Tracking implementation of recommendations
    """

    # Best practice categories
    PRACTICE_CATEGORIES = {
        "workflow_optimization": {
            "priority": "high",
            "impact": "efficiency gains",
            "difficulty": "medium"
        },
        "feature_utilization": {
            "priority": "high",
            "impact": "value realization",
            "difficulty": "low"
        },
        "collaboration": {
            "priority": "medium",
            "impact": "team productivity",
            "difficulty": "low"
        },
        "automation": {
            "priority": "high",
            "impact": "time savings",
            "difficulty": "medium"
        },
        "reporting": {
            "priority": "medium",
            "impact": "data insights",
            "difficulty": "low"
        },
        "integration": {
            "priority": "medium",
            "impact": "ecosystem value",
            "difficulty": "high"
        }
    }

    # Performance benchmarks by tier
    BENCHMARKS = {
        "top_quartile": {"percentile": 75, "rating": "excellent"},
        "above_average": {"percentile": 50, "rating": "good"},
        "average": {"percentile": 25, "rating": "acceptable"},
        "below_average": {"percentile": 10, "rating": "needs_improvement"}
    }

    def __init__(self):
        config = AgentConfig(
            name="best_practices",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",
            temperature=0.4,
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
        Analyze customer practices and provide recommendations.

        Args:
            state: Current agent state with customer usage data

        Returns:
            Updated state with best practices and benchmarks
        """
        self.logger.info("best_practices_analysis_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        usage_data = state.get("entities", {}).get("usage_data", {})
        customer_metadata = state.get("customer_metadata", {})
        current_practices = state.get("entities", {}).get("current_practices", {})

        self.logger.debug(
            "best_practices_details",
            customer_id=customer_id,
            industry=customer_metadata.get("industry", "unknown"),
            plan=customer_metadata.get("plan", "unknown")
        )

        # Analyze current practices
        practices_analysis = self._analyze_current_practices(
            usage_data,
            current_practices,
            customer_metadata
        )

        # Generate best practice recommendations
        recommendations = self._generate_best_practices(
            practices_analysis,
            customer_metadata
        )

        # Benchmark against cohort
        benchmarks = self._benchmark_performance(
            usage_data,
            customer_metadata
        )

        # Create optimization roadmap
        roadmap = self._create_optimization_roadmap(
            recommendations,
            benchmarks
        )

        # Provide templates and resources
        resources = self._recommend_resources(
            recommendations,
            customer_metadata
        )

        # Format response
        response = self._format_best_practices_report(
            practices_analysis,
            recommendations,
            benchmarks,
            roadmap,
            resources
        )

        state["agent_response"] = response
        state["practice_score"] = practices_analysis["overall_score"]
        state["benchmark_rating"] = benchmarks["overall_rating"]
        state["optimization_opportunities"] = len(recommendations)
        state["practices_analysis"] = practices_analysis
        state["response_confidence"] = 0.86
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "best_practices_analysis_completed",
            customer_id=customer_id,
            practice_score=practices_analysis["overall_score"],
            benchmark_rating=benchmarks["overall_rating"],
            recommendations=len(recommendations)
        )

        return state

    def _analyze_current_practices(
        self,
        usage_data: Dict[str, Any],
        current_practices: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze customer's current practices.

        Args:
            usage_data: Customer usage metrics
            current_practices: Current workflows and practices
            customer_metadata: Customer profile data

        Returns:
            Analysis of current practices
        """
        # Evaluate practices by category
        category_scores = {}

        for category, criteria in self.PRACTICE_CATEGORIES.items():
            score = self._score_practice_category(
                category,
                usage_data,
                current_practices
            )
            category_scores[category] = {
                "score": score,
                "priority": criteria["priority"],
                "impact": criteria["impact"]
            }

        # Calculate overall practice score
        total_score = sum(cat["score"] for cat in category_scores.values())
        overall_score = int(total_score / len(category_scores))

        # Identify strengths and gaps
        strengths = [
            cat for cat, data in category_scores.items()
            if data["score"] >= 70
        ]

        gaps = [
            cat for cat, data in category_scores.items()
            if data["score"] < 50
        ]

        # Determine maturity level
        maturity_level = self._determine_maturity_level(overall_score)

        return {
            "overall_score": overall_score,
            "maturity_level": maturity_level,
            "category_scores": category_scores,
            "strengths": strengths,
            "gaps": gaps,
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _score_practice_category(
        self,
        category: str,
        usage_data: Dict[str, Any],
        current_practices: Dict[str, Any]
    ) -> int:
        """Score a specific practice category (0-100)."""
        score = 50  # Default baseline

        # Workflow optimization
        if category == "workflow_optimization":
            workflows_count = current_practices.get("workflows_created", 0)
            if workflows_count >= 10:
                score = 90
            elif workflows_count >= 5:
                score = 70
            elif workflows_count >= 1:
                score = 50
            else:
                score = 20

        # Feature utilization
        elif category == "feature_utilization":
            features_used = len(usage_data.get("features_used", []))
            if features_used >= 15:
                score = 90
            elif features_used >= 10:
                score = 70
            elif features_used >= 5:
                score = 50
            else:
                score = 30

        # Collaboration
        elif category == "collaboration":
            collaboration_features = current_practices.get("collaboration_features_used", 0)
            if collaboration_features >= 5:
                score = 85
            elif collaboration_features >= 3:
                score = 65
            elif collaboration_features >= 1:
                score = 45
            else:
                score = 25

        # Automation
        elif category == "automation":
            automation_rules = current_practices.get("automation_rules", 0)
            if automation_rules >= 20:
                score = 95
            elif automation_rules >= 10:
                score = 75
            elif automation_rules >= 3:
                score = 55
            else:
                score = 30

        # Reporting
        elif category == "reporting":
            custom_reports = current_practices.get("custom_reports", 0)
            if custom_reports >= 10:
                score = 88
            elif custom_reports >= 5:
                score = 68
            elif custom_reports >= 1:
                score = 48
            else:
                score = 28

        # Integration
        elif category == "integration":
            active_integrations = current_practices.get("active_integrations", 0)
            if active_integrations >= 5:
                score = 92
            elif active_integrations >= 3:
                score = 72
            elif active_integrations >= 1:
                score = 52
            else:
                score = 25

        return score

    def _determine_maturity_level(self, overall_score: int) -> str:
        """Determine practice maturity level."""
        if overall_score >= 80:
            return "optimized"
        elif overall_score >= 60:
            return "advanced"
        elif overall_score >= 40:
            return "developing"
        else:
            return "initial"

    def _generate_best_practices(
        self,
        practices_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized best practice recommendations."""
        recommendations = []
        gaps = practices_analysis.get("gaps", [])
        category_scores = practices_analysis.get("category_scores", {})
        industry = customer_metadata.get("industry", "general")

        # Prioritize gaps
        for category in gaps:
            practice_info = self.PRACTICE_CATEGORIES.get(category, {})
            category_data = category_scores.get(category, {})

            recommendation = {
                "category": category,
                "priority": practice_info.get("priority", "medium"),
                "current_score": category_data.get("score", 0),
                "target_score": 75,
                "impact": practice_info.get("impact", "value realization"),
                "difficulty": practice_info.get("difficulty", "medium"),
                "practices": self._get_category_practices(category, industry),
                "expected_benefit": self._estimate_benefit(category)
            }

            recommendations.append(recommendation)

        # Add improvement recommendations for medium-scoring categories
        for category, data in category_scores.items():
            if 50 <= data["score"] < 70 and category not in gaps:
                practice_info = self.PRACTICE_CATEGORIES.get(category, {})

                recommendations.append({
                    "category": category,
                    "priority": "low",
                    "current_score": data["score"],
                    "target_score": 85,
                    "impact": practice_info.get("impact", "optimization"),
                    "difficulty": "low",
                    "practices": self._get_category_practices(category, industry)[:2],
                    "expected_benefit": "Incremental improvement"
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 2))

        return recommendations[:8]

    def _get_category_practices(self, category: str, industry: str) -> List[str]:
        """Get specific best practices for a category."""
        practices_db = {
            "workflow_optimization": [
                "Create standardized workflow templates for common processes",
                "Implement approval workflows to reduce bottlenecks",
                "Use conditional logic to automate decision paths",
                "Document and share team workflows across departments"
            ],
            "feature_utilization": [
                "Enable advanced search and filtering for faster data access",
                "Use bulk actions to process multiple items simultaneously",
                "Set up custom views for different team roles",
                "Leverage keyboard shortcuts for frequent actions"
            ],
            "collaboration": [
                "Use @mentions to notify specific team members",
                "Share project boards for cross-functional visibility",
                "Enable commenting and activity feeds for async communication",
                "Create team workspaces for departmental organization"
            ],
            "automation": [
                "Automate status updates based on trigger conditions",
                "Set up recurring task creation for routine processes",
                "Use automation to assign tasks based on round-robin or workload",
                "Implement notification rules to reduce manual follow-ups"
            ],
            "reporting": [
                "Build executive dashboards for high-level KPI tracking",
                "Schedule automated report delivery to stakeholders",
                "Create role-specific reports for different team needs",
                "Use data visualization for trend analysis"
            ],
            "integration": [
                f"Connect with popular {industry} tools for seamless data flow",
                "Use two-way sync to keep data updated across platforms",
                "Automate workflows across integrated applications",
                "Leverage webhooks for real-time event notifications"
            ]
        }

        return practices_db.get(category, ["Optimize usage patterns", "Follow industry standards"])

    def _estimate_benefit(self, category: str) -> str:
        """Estimate benefit of implementing best practices."""
        benefits = {
            "workflow_optimization": "20-30% reduction in process completion time",
            "feature_utilization": "40-50% improvement in user productivity",
            "collaboration": "25-35% faster team communication",
            "automation": "50-70% time savings on repetitive tasks",
            "reporting": "80% reduction in manual reporting time",
            "integration": "30-40% efficiency gain from unified data"
        }

        return benefits.get(category, "Measurable productivity improvement")

    def _benchmark_performance(
        self,
        usage_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Benchmark customer performance against cohort."""
        # Simplified benchmarking - in production, would use real cohort data
        industry = customer_metadata.get("industry", "general")
        plan = customer_metadata.get("plan", "standard")

        # Calculate key metrics
        feature_adoption = len(usage_data.get("features_used", [])) / 20 * 100  # Assume 20 total features
        dau_mau_ratio = usage_data.get("dau", 0) / max(usage_data.get("mau", 1), 1) * 100
        automation_usage = usage_data.get("automation_count", 0)

        # Compare to benchmarks
        benchmarks = {
            "feature_adoption": self._get_benchmark_tier(feature_adoption, [75, 50, 25]),
            "engagement": self._get_benchmark_tier(dau_mau_ratio, [60, 40, 20]),
            "automation": self._get_benchmark_tier(automation_usage, [15, 8, 3])
        }

        # Calculate overall rating
        tier_scores = {"top_quartile": 4, "above_average": 3, "average": 2, "below_average": 1}
        avg_score = sum(tier_scores.get(b, 2) for b in benchmarks.values()) / len(benchmarks)

        if avg_score >= 3.5:
            overall_rating = "top_quartile"
        elif avg_score >= 2.5:
            overall_rating = "above_average"
        elif avg_score >= 1.5:
            overall_rating = "average"
        else:
            overall_rating = "below_average"

        return {
            "overall_rating": overall_rating,
            "industry": industry,
            "plan": plan,
            "metrics": {
                "feature_adoption": {"value": round(feature_adoption, 1), "tier": benchmarks["feature_adoption"]},
                "engagement": {"value": round(dau_mau_ratio, 1), "tier": benchmarks["engagement"]},
                "automation": {"value": automation_usage, "tier": benchmarks["automation"]}
            }
        }

    def _get_benchmark_tier(self, value: float, thresholds: List[int]) -> str:
        """Determine benchmark tier based on value and thresholds."""
        if value >= thresholds[0]:
            return "top_quartile"
        elif value >= thresholds[1]:
            return "above_average"
        elif value >= thresholds[2]:
            return "average"
        else:
            return "below_average"

    def _create_optimization_roadmap(
        self,
        recommendations: List[Dict[str, Any]],
        benchmarks: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Create 30-60-90 day optimization roadmap."""
        roadmap = {
            "30_days": [],
            "60_days": [],
            "90_days": []
        }

        # 30 days: High priority, low difficulty
        for rec in recommendations:
            if rec["priority"] == "high" and rec["difficulty"] in ["low", "medium"]:
                roadmap["30_days"].append(
                    f"Implement {rec['category'].replace('_', ' ')} best practices"
                )

        # 60 days: Medium priority and medium difficulty
        for rec in recommendations:
            if rec["priority"] == "medium" or rec["difficulty"] == "medium":
                roadmap["60_days"].append(
                    f"Optimize {rec['category'].replace('_', ' ')}"
                )

        # 90 days: All remaining and high difficulty
        for rec in recommendations:
            if rec["difficulty"] == "high" or rec["priority"] == "low":
                roadmap["90_days"].append(
                    f"Advanced {rec['category'].replace('_', ' ')} implementation"
                )

        # Limit to top 3-4 per timeframe
        roadmap["30_days"] = roadmap["30_days"][:4]
        roadmap["60_days"] = roadmap["60_days"][:4]
        roadmap["90_days"] = roadmap["90_days"][:3]

        return roadmap

    def _recommend_resources(
        self,
        recommendations: List[Dict[str, Any]],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Recommend templates, guides, and resources."""
        resources = []

        for rec in recommendations[:5]:
            category = rec["category"]

            resource = {
                "category": category,
                "type": "template" if category in ["workflow_optimization", "reporting"] else "guide",
                "title": f"{category.replace('_', ' ').title()} Best Practices Guide",
                "description": f"Step-by-step guide to implement {rec['impact']}"
            }

            resources.append(resource)

        return resources

    def _format_best_practices_report(
        self,
        practices_analysis: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        benchmarks: Dict[str, Any],
        roadmap: Dict[str, List[str]],
        resources: List[Dict[str, str]]
    ) -> str:
        """Format best practices report."""
        maturity = practices_analysis["maturity_level"]
        overall_score = practices_analysis["overall_score"]

        maturity_emoji = {
            "optimized": "????",
            "advanced": "???",
            "developing": "????",
            "initial": "????"
        }

        report = f"""**{maturity_emoji.get(maturity, '????')} Best Practices Analysis**

**Maturity Level:** {maturity.upper()}
**Overall Score:** {overall_score}/100

**Practice Category Scores:**
"""

        for category, data in practices_analysis["category_scores"].items():
            score_icon = "????" if data["score"] >= 70 else "????" if data["score"] >= 50 else "????"
            report += f"- {score_icon} {category.replace('_', ' ').title()}: {data['score']}/100 ({data['priority']} priority)\n"

        # Strengths
        if practices_analysis["strengths"]:
            report += "\n**???? Strengths:**\n"
            for strength in practices_analysis["strengths"][:3]:
                report += f"- {strength.replace('_', ' ').title()}\n"

        # Benchmarks
        rating = benchmarks["overall_rating"]
        rating_emoji = "????" if rating == "top_quartile" else "???" if rating == "above_average" else "????"

        report += f"\n**{rating_emoji} Performance Benchmarks**\n"
        report += f"**Overall Rating:** {rating.replace('_', ' ').title()}\n\n"

        for metric, data in benchmarks["metrics"].items():
            report += f"- {metric.replace('_', ' ').title()}: {data['value']}% ({data['tier'].replace('_', ' ').title()})\n"

        # Top recommendations
        if recommendations:
            report += "\n**???? Top Optimization Opportunities:**\n"
            for i, rec in enumerate(recommendations[:4], 1):
                priority_icon = "????" if rec["priority"] == "high" else "????" if rec["priority"] == "medium" else "????"
                report += f"\n{i}. **{rec['category'].replace('_', ' ').title()}** {priority_icon}\n"
                report += f"   - Current: {rec['current_score']}/100 ??? Target: {rec['target_score']}/100\n"
                report += f"   - Impact: {rec['impact']}\n"
                report += f"   - Benefit: {rec['expected_benefit']}\n"
                report += f"   - Key practices:\n"
                for practice in rec["practices"][:2]:
                    report += f"     ??? {practice}\n"

        # Roadmap
        report += "\n**??????? Optimization Roadmap:**\n"
        for timeframe, items in roadmap.items():
            if items:
                report += f"\n**{timeframe.replace('_', '-')} Days:**\n"
                for item in items:
                    report += f"- {item}\n"

        # Resources
        if resources:
            report += "\n**???? Recommended Resources:**\n"
            for resource in resources[:3]:
                report += f"- [{resource['title']}] - {resource['description']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Best Practices Agent (TASK-2033)")
        print("=" * 70)

        agent = BestPracticesAgent()

        # Test 1: Developing maturity
        print("\n\nTest 1: Developing Maturity Customer")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze best practices",
            context={
                "customer_id": "cust_developing",
                "customer_metadata": {
                    "plan": "premium",
                    "industry": "healthcare"
                }
            }
        )
        state1["entities"] = {
            "usage_data": {
                "features_used": ["feature1", "feature2", "feature3", "feature4"],
                "dau": 12,
                "mau": 25,
                "automation_count": 2
            },
            "current_practices": {
                "workflows_created": 1,
                "collaboration_features_used": 1,
                "automation_rules": 2,
                "custom_reports": 0,
                "active_integrations": 0
            }
        }

        result1 = await agent.process(state1)

        print(f"Practice Score: {result1['practice_score']}/100")
        print(f"Benchmark Rating: {result1['benchmark_rating']}")
        print(f"Optimization Opportunities: {result1['optimization_opportunities']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Advanced maturity
        print("\n\n" + "=" * 70)
        print("Test 2: Advanced Maturity Customer")
        print("-" * 70)

        state2 = create_initial_state(
            "Check best practices",
            context={
                "customer_id": "cust_advanced",
                "customer_metadata": {
                    "plan": "enterprise",
                    "industry": "technology"
                }
            }
        )
        state2["entities"] = {
            "usage_data": {
                "features_used": [f"feature{i}" for i in range(1, 18)],
                "dau": 45,
                "mau": 60,
                "automation_count": 25
            },
            "current_practices": {
                "workflows_created": 15,
                "collaboration_features_used": 6,
                "automation_rules": 25,
                "custom_reports": 12,
                "active_integrations": 7
            }
        }

        result2 = await agent.process(state2)

        print(f"Practice Score: {result2['practice_score']}/100")
        print(f"Benchmark Rating: {result2['benchmark_rating']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
