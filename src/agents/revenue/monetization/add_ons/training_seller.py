"""
Training Seller Agent - TASK-3023

Sells training packages by identifying low adoption and onboarding needs.
Converts teams with training needs into training package customers.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("training_seller", tier="revenue", category="monetization")
class TrainingSeller(BaseAgent):
    """
    Training Seller Agent - Identifies and sells training packages.

    Handles:
    - Identify teams with low feature adoption
    - Analyze onboarding success rates
    - Detect training needs from support tickets
    - Calculate productivity gains from training
    - Present training package options
    - Calculate ROI for training investment
    - Close training sales
    - Track training effectiveness
    """

    # Training package offerings
    TRAINING_PACKAGES = {
        "quick_start": {
            "name": "Quick Start Training",
            "price": 1000,
            "duration_hours": 2,
            "format": "Live virtual session",
            "includes": [
                "2-hour live training session",
                "Core features walkthrough",
                "Best practices guide",
                "30-day email support"
            ],
            "ideal_for": ["small_teams", "basic_needs"],
            "max_attendees": 10
        },
        "team_training": {
            "name": "Team Training Package",
            "price": 2500,
            "duration_hours": 8,
            "format": "Full-day workshop",
            "includes": [
                "8-hour comprehensive training",
                "Advanced features deep-dive",
                "Use case workshops",
                "Custom workflow setup",
                "Certification for attendees",
                "90-day follow-up support"
            ],
            "ideal_for": ["growing_teams", "standard"],
            "max_attendees": 25
        },
        "enterprise_training": {
            "name": "Enterprise Training Program",
            "price": 5000,
            "duration_hours": 16,
            "format": "Multi-session program",
            "includes": [
                "16 hours over 2 days",
                "Administrator training",
                "Power user certification",
                "Custom integration training",
                "Train-the-trainer program",
                "Quarterly refresher sessions",
                "6-month dedicated support"
            ],
            "ideal_for": ["enterprise", "complex_needs"],
            "max_attendees": 50
        }
    }

    # Training need signals
    TRAINING_SIGNALS = {
        "low_feature_adoption": {
            "metric": "feature_adoption_rate",
            "threshold": 0.40,
            "operator": "<=",
            "weight": 0.30,
            "indicator": "Teams using <40% of features need training"
        },
        "high_how_to_tickets": {
            "metric": "how_to_tickets_per_month",
            "threshold": 10,
            "operator": ">=",
            "weight": 0.25,
            "indicator": "Frequent 'how-to' questions indicate training gaps"
        },
        "new_team_members": {
            "metric": "new_users_last_30_days",
            "threshold": 5,
            "operator": ">=",
            "weight": 0.20,
            "indicator": "Growing teams need structured onboarding"
        },
        "low_engagement": {
            "metric": "avg_logins_per_user_per_week",
            "threshold": 2,
            "operator": "<=",
            "weight": 0.15,
            "indicator": "Low engagement suggests users don't know how to get value"
        },
        "support_escalations": {
            "metric": "user_confusion_escalations",
            "threshold": 3,
            "operator": ">=",
            "weight": 0.10,
            "indicator": "Escalations due to confusion need training"
        }
    }

    # Productivity impact metrics
    PRODUCTIVITY_METRICS = {
        "time_saved_per_user_per_week": 2,  # Hours saved with proper training
        "feature_adoption_increase": 0.45,  # Increase from 30% to 75%
        "support_ticket_reduction": 0.60,  # 60% reduction in how-to tickets
        "onboarding_time_reduction": 0.50   # 50% faster onboarding
    }

    def __init__(self):
        config = AgentConfig(
            name="training_seller",
            type=AgentType.SPECIALIST,
             # Haiku for efficient training sales
            temperature=0.3,
            max_tokens=500,
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
        Identify and sell training packages.

        Args:
            state: Current agent state with usage and adoption data

        Returns:
            Updated state with training recommendation
        """
        self.logger.info("training_seller_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify training needs
        training_needs = self._identify_training_needs(customer_metadata)

        # Recommend training package
        recommended_package = self._recommend_package(
            training_needs,
            customer_metadata
        )

        # Calculate productivity ROI
        roi_analysis = self._calculate_training_roi(
            recommended_package,
            customer_metadata
        )

        # Build training curriculum preview
        curriculum = self._build_curriculum_preview(
            recommended_package,
            customer_metadata
        )

        # Generate success metrics
        success_metrics = self._project_success_metrics(
            recommended_package,
            customer_metadata
        )

        # Search KB for training resources
        kb_results = await self.search_knowledge_base(
            "training onboarding feature adoption",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_training_sales_response(
            message,
            training_needs,
            recommended_package,
            roi_analysis,
            curriculum,
            success_metrics,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.83
        state["training_needs"] = training_needs
        state["recommended_package"] = recommended_package
        state["training_roi"] = roi_analysis
        state["curriculum"] = curriculum
        state["success_metrics"] = success_metrics
        state["status"] = "resolved"

        self.logger.info(
            "training_seller_completed",
            has_training_need=training_needs["has_need"],
            recommended_package=recommended_package,
            roi_percentage=roi_analysis.get("roi_percentage", 0)
        )

        return state

    def _identify_training_needs(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Identify customer training needs from signals"""
        needs = {
            "has_need": False,
            "need_score": 0.0,
            "signals_met": [],
            "specific_needs": []
        }

        total_weight = 0
        weighted_score = 0

        for signal_name, config in self.TRAINING_SIGNALS.items():
            metric = config["metric"]
            threshold = config["threshold"]
            operator = config["operator"]
            weight = config["weight"]
            total_weight += weight

            actual_value = customer_metadata.get(metric, 0)

            signal_met = False
            if operator == ">=":
                signal_met = actual_value >= threshold
            elif operator == "<=":
                signal_met = actual_value <= threshold

            if signal_met:
                weighted_score += weight
                needs["signals_met"].append({
                    "signal": signal_name,
                    "indicator": config["indicator"],
                    "actual_value": actual_value,
                    "threshold": threshold
                })

        needs["need_score"] = round(
            (weighted_score / total_weight) * 100 if total_weight > 0 else 0,
            2
        )
        needs["has_need"] = needs["need_score"] >= 40

        # Identify specific training needs
        if customer_metadata.get("feature_adoption_rate", 1.0) <= 0.40:
            needs["specific_needs"].append("Feature adoption and best practices")

        if customer_metadata.get("how_to_tickets_per_month", 0) >= 10:
            needs["specific_needs"].append("Self-service and advanced workflows")

        if customer_metadata.get("new_users_last_30_days", 0) >= 5:
            needs["specific_needs"].append("Onboarding and team enablement")

        if customer_metadata.get("admin_users", 0) >= 2:
            needs["specific_needs"].append("Administrator and power user training")

        return needs

    def _recommend_package(
        self,
        training_needs: Dict,
        customer_metadata: Dict
    ) -> str:
        """Recommend appropriate training package"""
        team_size = customer_metadata.get("team_size", 0)
        company_size = customer_metadata.get("company_size", 0)
        need_score = training_needs["need_score"]

        # Enterprise training for large teams or high need
        if team_size >= 30 or company_size >= 200 or need_score >= 70:
            return "enterprise_training"
        # Team training for medium teams
        elif team_size >= 10 or company_size >= 50 or need_score >= 50:
            return "team_training"
        # Quick start for smaller teams
        else:
            return "quick_start"

    def _calculate_training_roi(
        self,
        package: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate ROI from training investment"""
        package_info = self.TRAINING_PACKAGES[package]
        package_cost = package_info["price"]

        team_size = customer_metadata.get("team_size", 10)
        avg_hourly_cost = 50  # Average employee hourly cost

        # Calculate annual time savings
        weekly_hours_saved = team_size * self.PRODUCTIVITY_METRICS["time_saved_per_user_per_week"]
        annual_hours_saved = weekly_hours_saved * 52
        annual_time_value = annual_hours_saved * avg_hourly_cost

        # Calculate support cost reduction
        current_support_tickets = customer_metadata.get("how_to_tickets_per_month", 0)
        ticket_reduction = current_support_tickets * self.PRODUCTIVITY_METRICS["support_ticket_reduction"]
        annual_ticket_savings = ticket_reduction * 12 * 25  # $25 per ticket cost

        # Calculate onboarding efficiency
        new_users_per_year = customer_metadata.get("new_users_last_30_days", 0) * 12
        onboarding_hours_saved = new_users_per_year * 8 * self.PRODUCTIVITY_METRICS["onboarding_time_reduction"]
        onboarding_value = onboarding_hours_saved * avg_hourly_cost

        # Total annual value
        total_annual_value = annual_time_value + annual_ticket_savings + onboarding_value

        # Calculate ROI
        roi_percentage = ((total_annual_value - package_cost) / package_cost) * 100 if package_cost > 0 else 0
        payback_weeks = (package_cost / (total_annual_value / 52)) if total_annual_value > 0 else 0

        return {
            "package_cost": package_cost,
            "annual_hours_saved": round(annual_hours_saved, 0),
            "annual_time_value": round(annual_time_value, 2),
            "annual_ticket_savings": round(annual_ticket_savings, 2),
            "onboarding_value": round(onboarding_value, 2),
            "total_annual_value": round(total_annual_value, 2),
            "roi_percentage": round(roi_percentage, 2),
            "payback_weeks": round(payback_weeks, 1)
        }

    def _build_curriculum_preview(
        self,
        package: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Build preview of training curriculum"""
        package_info = self.TRAINING_PACKAGES[package]

        base_topics = [
            "Platform overview and navigation",
            "Core workflow setup",
            "Best practices and tips",
            "Q&A session"
        ]

        advanced_topics = [
            "Advanced automation setup",
            "Integration configuration",
            "Reporting and analytics",
            "Administrator controls",
            "Custom workflows"
        ]

        if package == "enterprise_training":
            topics = base_topics + advanced_topics + [
                "Train-the-trainer certification",
                "Change management strategies"
            ]
        elif package == "team_training":
            topics = base_topics + advanced_topics[:3]
        else:
            topics = base_topics

        return {
            "package_name": package_info["name"],
            "duration": package_info["duration_hours"],
            "format": package_info["format"],
            "topics_covered": topics,
            "deliverables": package_info["includes"]
        }

    def _project_success_metrics(
        self,
        package: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Project success metrics after training"""
        current_adoption = customer_metadata.get("feature_adoption_rate", 0.30)
        current_logins = customer_metadata.get("avg_logins_per_user_per_week", 1)

        return {
            "feature_adoption": {
                "before": f"{current_adoption * 100:.0f}%",
                "after": "75%",
                "improvement": f"+{(0.75 - current_adoption) * 100:.0f}%"
            },
            "user_engagement": {
                "before": f"{current_logins:.1f} logins/week",
                "after": "4.5 logins/week",
                "improvement": f"+{(4.5 - current_logins):.1f} logins"
            },
            "support_tickets": {
                "before": f"{customer_metadata.get('how_to_tickets_per_month', 0)} tickets/month",
                "after": f"{int(customer_metadata.get('how_to_tickets_per_month', 0) * 0.4)} tickets/month",
                "improvement": "-60%"
            },
            "time_to_productivity": {
                "before": "4 weeks",
                "after": "2 weeks",
                "improvement": "-50%"
            }
        }

    async def _generate_training_sales_response(
        self,
        message: str,
        training_needs: Dict,
        recommended_package: str,
        roi_analysis: Dict,
        curriculum: Dict,
        success_metrics: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate training sales response"""

        package_info = self.TRAINING_PACKAGES[recommended_package]

        # Build needs context
        needs_context = f"""
Training Need Score: {training_needs['need_score']}/100
Signals Met: {len(training_needs['signals_met'])}
Specific Needs: {', '.join(training_needs['specific_needs'])}
"""

        # Build ROI context
        roi_context = f"""
ROI Analysis:
- Investment: ${roi_analysis['package_cost']:,}
- Annual Value: ${roi_analysis['total_annual_value']:,.0f}
- ROI: {roi_analysis['roi_percentage']:.0f}%
- Payback: {roi_analysis['payback_weeks']:.0f} weeks
- Hours Saved: {roi_analysis['annual_hours_saved']:,.0f}/year
"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nTraining Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Training Seller helping teams maximize product value through training.

Customer: {customer_metadata.get('company', 'Customer')}
Team Size: {customer_metadata.get('team_size', 0)} users
Current Adoption: {customer_metadata.get('feature_adoption_rate', 0.30) * 100:.0f}%
{needs_context}
{roi_context}

Your response should:
1. Acknowledge their adoption and usage patterns
2. Identify specific training gaps
3. Recommend {package_info['name']}
4. Explain curriculum and what they'll learn
5. Quantify productivity gains and ROI
6. Show before/after metrics
7. Address time investment concerns
8. Make training feel valuable, not remedial
9. Create urgency around missed productivity
10. Provide next steps to schedule

Tone: Encouraging, value-focused, practical"""

        user_prompt = f"""Customer message: {message}

Recommended Training: {curriculum['package_name']}
Duration: {curriculum['duration']} hours ({curriculum['format']})

Success Metrics After Training:
- Feature Adoption: {success_metrics['feature_adoption']['before']} ??? {success_metrics['feature_adoption']['after']} ({success_metrics['feature_adoption']['improvement']})
- Support Tickets: {success_metrics['support_tickets']['improvement']} reduction

{kb_context}

Generate an encouraging training recommendation."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
