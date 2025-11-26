"""
Plan Upgrade Agent - TASK-3032

Identifies customers ready to upgrade to higher-tier plans based on usage and needs.
Converts plan upgrade opportunities into expansion revenue.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("plan_upgrade", tier="revenue", category="monetization")
class PlanUpgrade(BaseAgent):
    """
    Plan Upgrade Agent - Drives plan tier upgrades.

    Handles:
    - Identify customers outgrowing current plan
    - Analyze feature usage vs plan limits
    - Detect enterprise-ready signals
    - Calculate upgrade ROI and value
    - Present upgrade value proposition
    - Compare plan tiers effectively
    - Close plan upgrade deals
    - Track upgrade conversion rates
    """

    # Plan tiers and features
    PLAN_TIERS = {
        "basic": {
            "name": "Basic Plan",
            "price_monthly": 49,
            "price_annual": 490,
            "features": [
                "10 seats included",
                "Basic support",
                "Core features",
                "Email support only",
            ],
            "limits": {"seats": 10, "api_calls": 10000, "storage_gb": 50},
        },
        "professional": {
            "name": "Professional Plan",
            "price_monthly": 199,
            "price_annual": 1990,
            "features": [
                "25 seats included",
                "Priority support",
                "Advanced features",
                "API access",
                "Integrations",
                "Custom workflows",
            ],
            "limits": {"seats": 25, "api_calls": 100000, "storage_gb": 250},
        },
        "enterprise": {
            "name": "Enterprise Plan",
            "price_monthly": 499,
            "price_annual": 4990,
            "features": [
                "Unlimited seats",
                "24/7 premium support",
                "All features",
                "Advanced API",
                "SSO & SAML",
                "Custom SLAs",
                "Dedicated account manager",
                "Advanced security",
            ],
            "limits": {"seats": float("inf"), "api_calls": float("inf"), "storage_gb": 1000},
        },
    }

    # Upgrade signals by target tier
    UPGRADE_SIGNALS = {
        "basic_to_professional": [
            {"metric": "seat_count", "threshold": 8, "weight": 0.30},
            {"metric": "api_calls", "threshold": 8000, "weight": 0.25},
            {"metric": "integration_requests", "threshold": 2, "weight": 0.20},
            {"metric": "advanced_feature_requests", "threshold": 3, "weight": 0.15},
            {"metric": "support_tickets_per_month", "threshold": 10, "weight": 0.10},
        ],
        "professional_to_enterprise": [
            {"metric": "seat_count", "threshold": 20, "weight": 0.25},
            {"metric": "company_size", "threshold": 200, "weight": 0.25},
            {"metric": "sso_requests", "threshold": 1, "weight": 0.20},
            {"metric": "security_audit_requests", "threshold": 1, "weight": 0.15},
            {"metric": "current_mrr", "threshold": 2000, "weight": 0.15},
        ],
    }

    # Upgrade value factors
    VALUE_FACTORS = {
        "productivity_per_advanced_feature": 5000,
        "security_compliance_value": 25000,
        "support_upgrade_value": 10000,
        "integration_value_per_integration": 8000,
    }

    def __init__(self):
        config = AgentConfig(
            name="plan_upgrade",
            type=AgentType.SPECIALIST,
            # Sonnet for upgrade sales
            temperature=0.3,
            max_tokens=600,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="monetization",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Identify and drive plan upgrade opportunities.

        Args:
            state: Current agent state with plan and usage data

        Returns:
            Updated state with upgrade recommendation
        """
        self.logger.info("plan_upgrade_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Get current plan
        current_plan = customer_metadata.get("plan_tier", "basic")

        # Identify upgrade signals
        upgrade_signals = self._identify_upgrade_signals(current_plan, customer_metadata)

        # Determine target plan
        target_plan = self._determine_target_plan(current_plan, upgrade_signals)

        # Calculate upgrade value
        upgrade_value = self._calculate_upgrade_value(current_plan, target_plan, customer_metadata)

        # Build plan comparison
        comparison = self._build_plan_comparison(current_plan, target_plan)

        # Generate feature gap analysis
        feature_gaps = self._analyze_feature_gaps(current_plan, target_plan, customer_metadata)

        # Build upgrade proposal
        proposal = self._build_upgrade_proposal(
            current_plan, target_plan, upgrade_value, feature_gaps, customer_metadata
        )

        # Search KB for upgrade resources
        kb_results = await self.search_knowledge_base(
            f"plan upgrade {target_plan} features benefits", category="monetization", limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_upgrade_response(
            message,
            current_plan,
            target_plan,
            upgrade_signals,
            upgrade_value,
            comparison,
            feature_gaps,
            kb_results,
            customer_metadata,
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.89
        state["upgrade_signals"] = upgrade_signals
        state["target_plan"] = target_plan
        state["upgrade_value"] = upgrade_value
        state["plan_comparison"] = comparison
        state["feature_gaps"] = feature_gaps
        state["upgrade_proposal"] = proposal
        state["status"] = "resolved"

        self.logger.info(
            "plan_upgrade_completed",
            current_plan=current_plan,
            target_plan=target_plan,
            has_opportunity=upgrade_signals["should_upgrade"],
            annual_expansion=upgrade_value.get("annual_expansion_revenue", 0),
        )

        return state

    def _identify_upgrade_signals(
        self, current_plan: str, customer_metadata: dict
    ) -> dict[str, Any]:
        """Identify signals indicating readiness to upgrade"""
        signals = {
            "should_upgrade": False,
            "upgrade_score": 0.0,
            "signals_detected": [],
            "urgency": "low",
        }

        # Determine upgrade path
        if current_plan == "basic":
            signal_key = "basic_to_professional"
        elif current_plan == "professional":
            signal_key = "professional_to_enterprise"
        else:
            return signals  # Already on highest tier

        signal_configs = self.UPGRADE_SIGNALS.get(signal_key, [])

        total_weight = 0
        weighted_score = 0

        for config in signal_configs:
            metric = config["metric"]
            threshold = config["threshold"]
            weight = config["weight"]
            total_weight += weight

            actual_value = customer_metadata.get(metric, 0)

            if actual_value >= threshold:
                weighted_score += weight
                signals["signals_detected"].append(
                    {
                        "metric": metric,
                        "threshold": threshold,
                        "actual_value": actual_value,
                        "indicator": f"{metric} exceeds threshold",
                    }
                )

        signals["upgrade_score"] = round(
            (weighted_score / total_weight) * 100 if total_weight > 0 else 0, 2
        )
        signals["should_upgrade"] = signals["upgrade_score"] >= 50

        # Determine urgency
        if signals["upgrade_score"] >= 75:
            signals["urgency"] = "high"
        elif signals["upgrade_score"] >= 60:
            signals["urgency"] = "medium"
        else:
            signals["urgency"] = "low"

        return signals

    def _determine_target_plan(self, current_plan: str, signals: dict) -> str:
        """Determine recommended target plan"""
        if not signals["should_upgrade"]:
            return current_plan

        if current_plan == "basic":
            return "professional"
        elif current_plan == "professional":
            return "enterprise"
        else:
            return current_plan

    def _calculate_upgrade_value(
        self, current_plan: str, target_plan: str, customer_metadata: dict
    ) -> dict[str, Any]:
        """Calculate value delivered by plan upgrade"""
        if current_plan == target_plan:
            return {}

        current_pricing = self.PLAN_TIERS[current_plan]
        target_pricing = self.PLAN_TIERS[target_plan]

        # Calculate pricing difference
        monthly_increase = target_pricing["price_monthly"] - current_pricing["price_monthly"]
        annual_increase = target_pricing["price_annual"] - current_pricing["price_annual"]

        # Calculate value delivered
        advanced_features_count = len(target_pricing["features"]) - len(current_pricing["features"])
        feature_value = (
            advanced_features_count * self.VALUE_FACTORS["productivity_per_advanced_feature"]
        )

        # Additional value factors
        additional_value = 0
        if target_plan == "enterprise":
            additional_value += self.VALUE_FACTORS["security_compliance_value"]
            additional_value += self.VALUE_FACTORS["support_upgrade_value"]

        total_annual_value = feature_value + additional_value

        # Calculate ROI
        roi_percentage = (
            ((total_annual_value - annual_increase) / annual_increase) * 100
            if annual_increase > 0
            else 0
        )

        return {
            "monthly_expansion_revenue": monthly_increase,
            "annual_expansion_revenue": annual_increase,
            "total_annual_value_delivered": total_annual_value,
            "roi_percentage": round(roi_percentage, 2),
            "payback_months": round(annual_increase / (total_annual_value / 12), 1)
            if total_annual_value > 0
            else 0,
            "value_per_dollar": round(total_annual_value / annual_increase, 2)
            if annual_increase > 0
            else 0,
        }

    def _build_plan_comparison(self, current_plan: str, target_plan: str) -> dict[str, Any]:
        """Build detailed comparison between plans"""
        current = self.PLAN_TIERS[current_plan]
        target = self.PLAN_TIERS[target_plan]

        return {
            "current_plan": {
                "name": current["name"],
                "price_monthly": current["price_monthly"],
                "price_annual": current["price_annual"],
                "features": current["features"],
                "limits": current["limits"],
            },
            "target_plan": {
                "name": target["name"],
                "price_monthly": target["price_monthly"],
                "price_annual": target["price_annual"],
                "features": target["features"],
                "limits": target["limits"],
            },
            "new_features": [f for f in target["features"] if f not in current["features"]],
            "increased_limits": {
                k: target["limits"][k]
                for k in target["limits"]
                if target["limits"][k] != current["limits"][k]
            },
        }

    def _analyze_feature_gaps(
        self, current_plan: str, target_plan: str, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Analyze features customer needs but doesn't have"""
        gaps = []

        # Check for requested features not in current plan
        if customer_metadata.get("sso_requests", 0) > 0 and current_plan != "enterprise":
            gaps.append(
                {
                    "feature": "SSO & SAML",
                    "requested_times": customer_metadata.get("sso_requests", 0),
                    "available_in": "enterprise",
                    "business_value": "Enhanced security and easier user management",
                }
            )

        if customer_metadata.get("integration_requests", 0) > 0 and current_plan == "basic":
            gaps.append(
                {
                    "feature": "Advanced Integrations",
                    "requested_times": customer_metadata.get("integration_requests", 0),
                    "available_in": "professional",
                    "business_value": "Automate workflows and connect systems",
                }
            )

        if customer_metadata.get("api_calls", 0) > 5000 and current_plan == "basic":
            gaps.append(
                {
                    "feature": "Advanced API Access",
                    "current_usage": customer_metadata.get("api_calls", 0),
                    "available_in": "professional",
                    "business_value": "Build custom integrations and automations",
                }
            )

        return gaps

    def _build_upgrade_proposal(
        self,
        current_plan: str,
        target_plan: str,
        upgrade_value: dict,
        feature_gaps: list[dict],
        customer_metadata: dict,
    ) -> dict[str, Any]:
        """Build plan upgrade proposal"""
        target_info = self.PLAN_TIERS[target_plan]

        return {
            "customer": customer_metadata.get("company", "Customer"),
            "current_plan": self.PLAN_TIERS[current_plan]["name"],
            "recommended_plan": target_info["name"],
            "pricing": {
                "monthly": target_info["price_monthly"],
                "annual": target_info["price_annual"],
                "monthly_increase": upgrade_value.get("monthly_expansion_revenue", 0),
                "annual_increase": upgrade_value.get("annual_expansion_revenue", 0),
            },
            "value_delivered": upgrade_value.get("total_annual_value_delivered", 0),
            "roi": upgrade_value.get("roi_percentage", 0),
            "feature_gaps_addressed": len(feature_gaps),
            "implementation": "Immediate - seamless upgrade with no downtime",
        }

    async def _generate_upgrade_response(
        self,
        message: str,
        current_plan: str,
        target_plan: str,
        signals: dict,
        upgrade_value: dict,
        comparison: dict,
        feature_gaps: list[dict],
        kb_results: list[dict],
        customer_metadata: dict,
    ) -> str:
        """Generate plan upgrade response"""

        # Build signals context
        signals_context = f"""
Upgrade Readiness Score: {signals["upgrade_score"]}/100
Upgrade Signals: {len(signals["signals_detected"])}
Urgency: {signals["urgency"]}
"""

        # Build upgrade context
        upgrade_context = ""
        if upgrade_value:
            upgrade_context = f"""
Upgrade Investment:
- Monthly: ${upgrade_value.get("monthly_expansion_revenue", 0):,.2f} increase
- Annual: ${upgrade_value.get("annual_expansion_revenue", 0):,.2f} increase
- Annual Value: ${upgrade_value.get("total_annual_value_delivered", 0):,.2f}
- ROI: {upgrade_value.get("roi_percentage", 0):.0f}%
"""

        # Build feature gaps context
        gaps_context = ""
        if feature_gaps:
            gaps_context = "\n\nFeatures You Need (Not in Current Plan):\n"
            for gap in feature_gaps[:3]:
                gaps_context += f"- {gap['feature']}: {gap['business_value']}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nPlan Upgrade Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Plan Upgrade specialist helping customers grow into the right plan tier.

Customer: {customer_metadata.get("company", "Customer")}
Current Plan: {self.PLAN_TIERS[current_plan]["name"]}
Recommended Plan: {self.PLAN_TIERS[target_plan]["name"]}
{signals_context}
{upgrade_context}

Your response should:
1. Acknowledge their growth and success
2. Show how they've outgrown current plan
3. Present specific upgrade signals and needs
4. Recommend {self.PLAN_TIERS[target_plan]["name"]}
5. Highlight new features and capabilities
6. Explain increased limits and flexibility
7. Quantify ROI and business value
8. Address investment with value delivered
9. Make upgrade seamless and easy
10. Provide clear next steps

Tone: Congratulatory, growth-focused, value-driven"""

        user_prompt = f"""Customer message: {message}

New Features in {self.PLAN_TIERS[target_plan]["name"]}:
{chr(10).join(f"- {feature}" for feature in comparison["new_features"][:5])}

{gaps_context}

{kb_context}

Generate an exciting plan upgrade recommendation."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[],  # Upgrade context built from plan usage data
        )
        return response
