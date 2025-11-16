"""
Upsell Identifier Agent - TASK-1046

Identifies upsell opportunities, analyzes usage patterns, recommends additional features,
and calculates expansion revenue potential from existing customers.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("upsell_identifier", tier="revenue", category="sales")
class UpsellIdentifier(BaseAgent):
    """
    Upsell Identifier Agent - Specialist in identifying expansion opportunities.

    Handles:
    - Upsell opportunity identification
    - Usage pattern analysis
    - Additional feature recommendations
    - Expansion revenue calculation
    - Upgrade path mapping
    """

    # Upsell trigger signals
    UPSELL_SIGNALS = {
        "usage_based": {
            "approaching_limits": {
                "trigger": "usage_at_80_percent",
                "opportunity": "upgrade_tier",
                "urgency": "high",
                "timing": "proactive"
            },
            "exceeded_limits": {
                "trigger": "usage_over_100_percent",
                "opportunity": "immediate_upgrade",
                "urgency": "critical",
                "timing": "immediate"
            },
            "power_user_behavior": {
                "trigger": "using_advanced_features",
                "opportunity": "premium_tier",
                "urgency": "medium",
                "timing": "next_renewal"
            },
            "frequent_usage": {
                "trigger": "daily_active_usage",
                "opportunity": "additional_seats",
                "urgency": "medium",
                "timing": "quarterly"
            }
        },
        "growth_based": {
            "team_expansion": {
                "trigger": "new_users_added",
                "opportunity": "volume_discount_tier",
                "urgency": "medium",
                "timing": "ongoing"
            },
            "department_spread": {
                "trigger": "multiple_departments",
                "opportunity": "enterprise_license",
                "urgency": "high",
                "timing": "strategic"
            },
            "increased_data": {
                "trigger": "data_volume_growth",
                "opportunity": "storage_upgrade",
                "urgency": "medium",
                "timing": "as_needed"
            }
        },
        "feature_based": {
            "feature_requests": {
                "trigger": "requesting_premium_features",
                "opportunity": "tier_upgrade",
                "urgency": "high",
                "timing": "immediate"
            },
            "integration_needs": {
                "trigger": "asking_about_integrations",
                "opportunity": "professional_tier",
                "urgency": "medium",
                "timing": "project_based"
            },
            "api_usage": {
                "trigger": "heavy_api_usage",
                "opportunity": "developer_tier",
                "urgency": "medium",
                "timing": "ongoing"
            }
        },
        "success_based": {
            "achieving_goals": {
                "trigger": "meeting_success_metrics",
                "opportunity": "expand_use_cases",
                "urgency": "low",
                "timing": "strategic"
            },
            "positive_feedback": {
                "trigger": "high_satisfaction_scores",
                "opportunity": "additional_products",
                "urgency": "low",
                "timing": "renewal"
            },
            "champion_identified": {
                "trigger": "internal_champion_active",
                "opportunity": "cross_sell",
                "urgency": "medium",
                "timing": "quarterly"
            }
        }
    }

    # Upsell opportunities by customer tier
    UPSELL_PATHS = {
        "starter_to_professional": {
            "from_tier": "starter",
            "to_tier": "professional",
            "typical_triggers": ["approaching_limits", "feature_requests", "team_expansion"],
            "avg_revenue_increase": 2.0,  # 2x increase
            "conversion_rate": 0.35
        },
        "professional_to_enterprise": {
            "from_tier": "professional",
            "to_tier": "enterprise",
            "typical_triggers": ["department_spread", "integration_needs", "exceeded_limits"],
            "avg_revenue_increase": 2.5,  # 2.5x increase
            "conversion_rate": 0.25
        },
        "seat_expansion": {
            "from_tier": "any",
            "to_tier": "same",
            "typical_triggers": ["team_expansion", "department_spread"],
            "avg_revenue_increase": 1.5,  # 1.5x increase
            "conversion_rate": 0.60
        },
        "add_on_services": {
            "from_tier": "any",
            "to_tier": "same_plus_services",
            "typical_triggers": ["integration_needs", "feature_requests"],
            "avg_revenue_increase": 1.3,  # 1.3x increase
            "conversion_rate": 0.45
        }
    }

    # Feature upsell recommendations
    FEATURE_RECOMMENDATIONS = {
        "advanced_analytics": {
            "recommended_for": ["data_volume_growth", "power_user_behavior"],
            "value_proposition": "Deeper insights and custom reporting",
            "typical_price_increase": 500,
            "adoption_rate": 0.40
        },
        "api_access": {
            "recommended_for": ["integration_needs", "api_usage"],
            "value_proposition": "Automate workflows and integrate systems",
            "typical_price_increase": 1000,
            "adoption_rate": 0.35
        },
        "premium_support": {
            "recommended_for": ["critical_usage", "enterprise_customer"],
            "value_proposition": "24/7 support with dedicated CSM",
            "typical_price_increase": 2000,
            "adoption_rate": 0.30
        },
        "advanced_security": {
            "recommended_for": ["compliance_requirements", "enterprise_customer"],
            "value_proposition": "Enhanced security and compliance features",
            "typical_price_increase": 1500,
            "adoption_rate": 0.25
        },
        "custom_integrations": {
            "recommended_for": ["integration_needs", "complex_workflows"],
            "value_proposition": "Tailored integrations for your tech stack",
            "typical_price_increase": 5000,
            "adoption_rate": 0.20
        },
        "training_program": {
            "recommended_for": ["team_expansion", "low_adoption"],
            "value_proposition": "Accelerate team productivity",
            "typical_price_increase": 3000,
            "adoption_rate": 0.50
        }
    }

    # Usage scoring matrix
    USAGE_SCORING = {
        "seat_utilization": {
            "weight": 0.25,
            "thresholds": {
                "excellent": 0.90,  # 90%+ seats active
                "good": 0.70,
                "fair": 0.50,
                "poor": 0.30
            }
        },
        "feature_adoption": {
            "weight": 0.20,
            "thresholds": {
                "excellent": 0.80,  # Using 80%+ features
                "good": 0.60,
                "fair": 0.40,
                "poor": 0.20
            }
        },
        "login_frequency": {
            "weight": 0.15,
            "thresholds": {
                "excellent": 5.0,  # 5+ days per week
                "good": 3.0,
                "fair": 1.0,
                "poor": 0.5
            }
        },
        "data_volume": {
            "weight": 0.15,
            "thresholds": {
                "excellent": 0.80,  # 80%+ of quota
                "good": 0.60,
                "fair": 0.40,
                "poor": 0.20
            }
        },
        "integration_usage": {
            "weight": 0.15,
            "thresholds": {
                "excellent": 3.0,  # 3+ integrations
                "good": 2.0,
                "fair": 1.0,
                "poor": 0.0
            }
        },
        "support_engagement": {
            "weight": 0.10,
            "thresholds": {
                "excellent": 0.10,  # Minimal support needed
                "good": 0.05,
                "fair": 0.02,
                "poor": 0.0
            }
        }
    }

    # Expansion revenue potential
    REVENUE_MULTIPLIERS = {
        "high_potential": {
            "multiplier_range": (2.0, 5.0),
            "criteria": ["fast_growth", "multiple_triggers", "executive_engagement"],
            "probability": 0.60
        },
        "medium_potential": {
            "multiplier_range": (1.5, 2.0),
            "criteria": ["steady_usage", "some_triggers", "champion_identified"],
            "probability": 0.40
        },
        "low_potential": {
            "multiplier_range": (1.0, 1.5),
            "criteria": ["stable_usage", "satisfied", "renewal_likely"],
            "probability": 0.25
        },
        "minimal_potential": {
            "multiplier_range": (1.0, 1.2),
            "criteria": ["basic_usage", "no_triggers", "price_sensitive"],
            "probability": 0.10
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="upsell_identifier",
            type=AgentType.ANALYZER,
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,
            max_tokens=1500,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process upsell identification request.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with upsell opportunities
        """
        self.logger.info("upsell_identifier_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        usage_data = state.get("usage_data", {})
        account_details = state.get("account_details", {})

        self.logger.debug(
            "upsell_identification_details",
            current_tier=account_details.get("current_tier", "unknown"),
            current_mrr=account_details.get("monthly_recurring_revenue", 0)
        )

        # Analyze usage patterns
        usage_analysis = self._analyze_usage_patterns(usage_data, account_details)

        # Calculate usage score
        usage_score = self._calculate_usage_score(usage_data)

        # Identify upsell signals
        upsell_signals = self._identify_upsell_signals(
            usage_data,
            usage_score,
            account_details
        )

        # Determine upsell opportunities
        opportunities = self._determine_opportunities(
            upsell_signals,
            account_details,
            usage_analysis
        )

        # Recommend features
        feature_recommendations = self._recommend_features(
            upsell_signals,
            usage_data,
            account_details
        )

        # Calculate expansion revenue potential
        expansion_potential = self._calculate_expansion_revenue(
            opportunities,
            feature_recommendations,
            account_details
        )

        # Prioritize opportunities
        prioritized_opportunities = self._prioritize_opportunities(
            opportunities,
            expansion_potential,
            usage_score
        )

        # Generate upsell strategy
        upsell_strategy = self._generate_upsell_strategy(
            prioritized_opportunities,
            usage_analysis,
            customer_metadata
        )

        # Search KB for upsell best practices
        kb_results = await self.search_knowledge_base(
            f"upsell strategies {account_details.get('current_tier', '')}",
            category="sales",
            limit=3
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_upsell_response(
            message,
            prioritized_opportunities,
            feature_recommendations,
            expansion_potential,
            upsell_strategy,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.86
        state["usage_analysis"] = usage_analysis
        state["usage_score"] = usage_score
        state["upsell_signals"] = upsell_signals
        state["opportunities"] = opportunities
        state["feature_recommendations"] = feature_recommendations
        state["expansion_potential"] = expansion_potential
        state["prioritized_opportunities"] = prioritized_opportunities
        state["upsell_strategy"] = upsell_strategy
        state["deal_stage"] = "expansion"
        state["status"] = "resolved"

        self.logger.info(
            "upsell_identifier_completed",
            opportunities_found=len(opportunities),
            expansion_potential=expansion_potential["total_potential_arr"],
            usage_score=usage_score["overall_score"]
        )

        return state

    def _analyze_usage_patterns(
        self,
        usage_data: Dict,
        account_details: Dict
    ) -> Dict[str, Any]:
        """Analyze customer usage patterns"""
        total_seats = account_details.get("total_seats", 10)
        active_seats = usage_data.get("active_users", 7)

        return {
            "seat_utilization": active_seats / total_seats if total_seats > 0 else 0,
            "active_users": active_seats,
            "total_seats": total_seats,
            "features_used": usage_data.get("features_used", []),
            "feature_adoption_rate": len(usage_data.get("features_used", [])) / 10,  # Assume 10 total features
            "avg_logins_per_week": usage_data.get("logins_per_week", 3),
            "data_usage_percentage": usage_data.get("data_usage_gb", 50) / usage_data.get("data_quota_gb", 100),
            "integrations_active": len(usage_data.get("integrations", [])),
            "api_calls_per_month": usage_data.get("api_calls", 0),
            "growth_trend": usage_data.get("user_growth_trend", "stable")
        }

    def _calculate_usage_score(self, usage_data: Dict) -> Dict[str, Any]:
        """Calculate comprehensive usage score"""
        scores = {}
        total_score = 0

        for metric, config in self.USAGE_SCORING.items():
            weight = config["weight"]

            # Get metric value
            if metric == "seat_utilization":
                value = usage_data.get("seat_utilization_percentage", 0.70)
            elif metric == "feature_adoption":
                value = len(usage_data.get("features_used", [])) / 10
            elif metric == "login_frequency":
                value = usage_data.get("logins_per_week", 3)
            elif metric == "data_volume":
                value = usage_data.get("data_usage_percentage", 0.50)
            elif metric == "integration_usage":
                value = len(usage_data.get("integrations", []))
            else:
                value = 0.05

            # Score based on thresholds
            thresholds = config["thresholds"]
            if value >= thresholds["excellent"]:
                metric_score = 1.0
                rating = "excellent"
            elif value >= thresholds["good"]:
                metric_score = 0.75
                rating = "good"
            elif value >= thresholds["fair"]:
                metric_score = 0.50
                rating = "fair"
            else:
                metric_score = 0.25
                rating = "poor"

            scores[metric] = {
                "value": value,
                "score": metric_score,
                "rating": rating,
                "weight": weight
            }

            total_score += metric_score * weight

        return {
            "overall_score": total_score,
            "scores": scores,
            "rating": "excellent" if total_score >= 0.80 else "good" if total_score >= 0.60 else "fair" if total_score >= 0.40 else "poor"
        }

    def _identify_upsell_signals(
        self,
        usage_data: Dict,
        usage_score: Dict,
        account_details: Dict
    ) -> List[Dict[str, Any]]:
        """Identify upsell signals from usage patterns"""
        signals = []

        # Check usage-based signals
        seat_utilization = usage_data.get("seat_utilization_percentage", 0.70)
        if seat_utilization >= 0.80:
            signals.append({
                "category": "usage_based",
                "signal": "approaching_limits",
                "details": self.UPSELL_SIGNALS["usage_based"]["approaching_limits"],
                "strength": "high"
            })

        # Check growth-based signals
        if usage_data.get("user_growth_trend", "stable") == "increasing":
            signals.append({
                "category": "growth_based",
                "signal": "team_expansion",
                "details": self.UPSELL_SIGNALS["growth_based"]["team_expansion"],
                "strength": "medium"
            })

        # Check feature-based signals
        if usage_data.get("feature_requests", 0) > 0:
            signals.append({
                "category": "feature_based",
                "signal": "feature_requests",
                "details": self.UPSELL_SIGNALS["feature_based"]["feature_requests"],
                "strength": "high"
            })

        # Check success-based signals
        if usage_score["overall_score"] >= 0.75:
            signals.append({
                "category": "success_based",
                "signal": "achieving_goals",
                "details": self.UPSELL_SIGNALS["success_based"]["achieving_goals"],
                "strength": "medium"
            })

        return signals

    def _determine_opportunities(
        self,
        signals: List[Dict],
        account_details: Dict,
        usage_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """Determine specific upsell opportunities"""
        opportunities = []
        current_tier = account_details.get("current_tier", "starter")

        # Tier upgrade opportunity
        if current_tier == "starter" and usage_analysis["seat_utilization"] > 0.75:
            path = self.UPSELL_PATHS["starter_to_professional"]
            opportunities.append({
                "type": "tier_upgrade",
                "path": "starter_to_professional",
                "description": f"Upgrade from {path['from_tier']} to {path['to_tier']}",
                "revenue_multiplier": path["avg_revenue_increase"],
                "conversion_probability": path["conversion_rate"],
                "triggers": [s["signal"] for s in signals if s["signal"] in path["typical_triggers"]]
            })
        elif current_tier == "professional" and usage_analysis["integrations_active"] >= 2:
            path = self.UPSELL_PATHS["professional_to_enterprise"]
            opportunities.append({
                "type": "tier_upgrade",
                "path": "professional_to_enterprise",
                "description": f"Upgrade from {path['from_tier']} to {path['to_tier']}",
                "revenue_multiplier": path["avg_revenue_increase"],
                "conversion_probability": path["conversion_rate"],
                "triggers": [s["signal"] for s in signals]
            })

        # Seat expansion opportunity
        if usage_analysis["seat_utilization"] > 0.80:
            path = self.UPSELL_PATHS["seat_expansion"]
            opportunities.append({
                "type": "seat_expansion",
                "path": "seat_expansion",
                "description": f"Add {int(account_details.get('total_seats', 10) * 0.5)} additional seats",
                "revenue_multiplier": path["avg_revenue_increase"],
                "conversion_probability": path["conversion_rate"],
                "triggers": ["approaching_limits"]
            })

        # Add-on services opportunity
        if any(s["signal"] == "integration_needs" for s in signals):
            path = self.UPSELL_PATHS["add_on_services"]
            opportunities.append({
                "type": "add_on_services",
                "path": "add_on_services",
                "description": "Add premium services and integrations",
                "revenue_multiplier": path["avg_revenue_increase"],
                "conversion_probability": path["conversion_rate"],
                "triggers": ["integration_needs"]
            })

        return opportunities

    def _recommend_features(
        self,
        signals: List[Dict],
        usage_data: Dict,
        account_details: Dict
    ) -> List[Dict[str, Any]]:
        """Recommend specific features for upsell"""
        recommendations = []

        # Check each feature recommendation
        for feature_name, feature_info in self.FEATURE_RECOMMENDATIONS.items():
            # Check if any signal matches recommendation criteria
            matching_signals = [
                s for s in signals
                if s["signal"] in feature_info["recommended_for"]
            ]

            if matching_signals:
                recommendations.append({
                    "feature": feature_name,
                    "value_proposition": feature_info["value_proposition"],
                    "price_increase": feature_info["typical_price_increase"],
                    "adoption_probability": feature_info["adoption_rate"],
                    "matching_signals": [s["signal"] for s in matching_signals]
                })

        # Sort by adoption probability
        recommendations.sort(key=lambda x: x["adoption_probability"], reverse=True)

        return recommendations[:3]  # Top 3 recommendations

    def _calculate_expansion_revenue(
        self,
        opportunities: List[Dict],
        feature_recommendations: List[Dict],
        account_details: Dict
    ) -> Dict[str, Any]:
        """Calculate potential expansion revenue"""
        current_mrr = account_details.get("monthly_recurring_revenue", 5000)
        current_arr = current_mrr * 12

        # Calculate from opportunities
        opportunity_revenue = 0
        for opp in opportunities:
            potential_increase = current_arr * (opp["revenue_multiplier"] - 1)
            weighted_increase = potential_increase * opp["conversion_probability"]
            opportunity_revenue += weighted_increase

        # Calculate from feature add-ons
        feature_revenue = 0
        for feature in feature_recommendations:
            annual_increase = feature["price_increase"] * 12
            weighted_increase = annual_increase * feature["adoption_probability"]
            feature_revenue += weighted_increase

        total_potential_arr = opportunity_revenue + feature_revenue
        expansion_rate = (total_potential_arr / current_arr) if current_arr > 0 else 0

        # Determine potential category
        if expansion_rate >= 2.0:
            potential_category = "high_potential"
        elif expansion_rate >= 1.5:
            potential_category = "medium_potential"
        elif expansion_rate >= 1.0:
            potential_category = "low_potential"
        else:
            potential_category = "minimal_potential"

        return {
            "current_arr": current_arr,
            "current_mrr": current_mrr,
            "opportunity_revenue": opportunity_revenue,
            "feature_revenue": feature_revenue,
            "total_potential_arr": total_potential_arr,
            "expansion_rate": expansion_rate,
            "potential_category": potential_category,
            "confidence": self.REVENUE_MULTIPLIERS[potential_category]["probability"]
        }

    def _prioritize_opportunities(
        self,
        opportunities: List[Dict],
        expansion_potential: Dict,
        usage_score: Dict
    ) -> List[Dict[str, Any]]:
        """Prioritize upsell opportunities"""
        prioritized = []

        for opp in opportunities:
            # Calculate priority score
            revenue_score = opp["revenue_multiplier"] * 0.4
            probability_score = opp["conversion_probability"] * 0.4
            urgency_score = 0.2  # Base urgency

            # Boost urgency based on triggers
            if "approaching_limits" in opp.get("triggers", []):
                urgency_score = 0.9
            elif "feature_requests" in opp.get("triggers", []):
                urgency_score = 0.7

            priority_score = revenue_score + probability_score + urgency_score

            prioritized.append({
                **opp,
                "priority_score": priority_score,
                "priority": "high" if priority_score >= 1.5 else "medium" if priority_score >= 1.0 else "low"
            })

        # Sort by priority score
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

        return prioritized

    def _generate_upsell_strategy(
        self,
        opportunities: List[Dict],
        usage_analysis: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive upsell strategy"""
        if not opportunities:
            return {
                "approach": "nurture",
                "timing": "monitor_usage",
                "message": "Continue delivering value, monitor for signals"
            }

        top_opportunity = opportunities[0]

        return {
            "approach": "proactive_outreach",
            "primary_opportunity": top_opportunity["type"],
            "timing": "immediate" if top_opportunity["priority"] == "high" else "next_30_days",
            "message_framework": [
                "Acknowledge their success and usage",
                "Highlight the value they're getting",
                "Introduce the expansion opportunity",
                "Show ROI of additional investment",
                "Make it easy to upgrade"
            ],
            "supporting_materials": [
                "Usage analytics dashboard",
                "ROI calculator for expansion",
                "Customer success stories",
                "Upgrade comparison chart"
            ]
        }

    async def _generate_upsell_response(
        self,
        message: str,
        opportunities: List[Dict],
        feature_recommendations: List[Dict],
        expansion_potential: Dict,
        strategy: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate upsell identification response"""

        # Build opportunities context
        opportunities_text = ""
        if opportunities:
            opportunities_text = "\n\nIdentified Opportunities:\n"
            for opp in opportunities[:3]:
                opportunities_text += f"- {opp['description']} (Priority: {opp.get('priority', 'medium').upper()})\n"
                opportunities_text += f"  Revenue Impact: {opp['revenue_multiplier']}x, Probability: {opp['conversion_probability']:.0%}\n"

        # Build feature recommendations
        features_text = ""
        if feature_recommendations:
            features_text = "\n\nRecommended Features:\n"
            for feature in feature_recommendations:
                features_text += f"- {feature['feature'].replace('_', ' ').title()}: {feature['value_proposition']}\n"
                features_text += f"  Additional ARR: ${feature['price_increase'] * 12:,.0f}\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nUpsell Best Practices:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are an Upsell Identifier specialist finding expansion opportunities.

Expansion Analysis:
- Current ARR: ${expansion_potential['current_arr']:,.0f}
- Expansion Potential: ${expansion_potential['total_potential_arr']:,.0f}
- Expansion Rate: {expansion_potential['expansion_rate']:.1f}x
- Potential Category: {expansion_potential['potential_category'].replace('_', ' ').title()}
- Confidence: {expansion_potential['confidence']:.0%}

Strategy: {strategy['approach']}
Timing: {strategy['timing']}

Company: {customer_metadata.get('company', 'Customer')}

Your response should:
1. Acknowledge their current usage and success
2. Present expansion opportunities as value-adds
3. Focus on benefits and ROI, not just features
4. Make recommendations specific to their usage
5. Be consultative, not pushy
6. Emphasize how expansion solves their needs
7. Make next steps clear and easy
8. Use customer success language"""

        user_prompt = f"""Customer message: {message}

{opportunities_text}

{features_text}

Strategy Framework:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(strategy.get('message_framework', [])))}

{kb_context}

Generate a consultative upsell response focused on value."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing UpsellIdentifier Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: High usage customer ready for upgrade
        state1 = create_initial_state(
            "We're really loving the platform and getting great value",
            context={
                "customer_metadata": {
                    "company": "GrowthCo",
                    "title": "VP Product",
                    "company_size": 100,
                    "industry": "technology"
                },
                "account_details": {
                    "current_tier": "starter",
                    "total_seats": 20,
                    "monthly_recurring_revenue": 1000
                },
                "usage_data": {
                    "active_users": 18,
                    "seat_utilization_percentage": 0.90,
                    "features_used": ["dashboard", "reports", "api", "analytics", "workflows", "integrations", "automation"],
                    "logins_per_week": 5,
                    "data_usage_gb": 80,
                    "data_quota_gb": 100,
                    "data_usage_percentage": 0.80,
                    "integrations": ["slack", "salesforce"],
                    "api_calls": 50000,
                    "user_growth_trend": "increasing",
                    "feature_requests": 3
                }
            }
        )

        agent = UpsellIdentifier()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - High Usage Ready for Upgrade")
        print(f"Usage Score: {result1['usage_score']['overall_score']:.2f} ({result1['usage_score']['rating']})")
        print(f"Upsell Signals: {len(result1['upsell_signals'])}")
        print(f"Opportunities: {len(result1['opportunities'])}")
        print(f"Expansion Potential: ${result1['expansion_potential']['total_potential_arr']:,.0f}")
        print(f"Expansion Rate: {result1['expansion_potential']['expansion_rate']:.1f}x")
        print(f"Top Priority: {result1['prioritized_opportunities'][0]['priority'] if result1['prioritized_opportunities'] else 'None'}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Enterprise customer with add-on potential
        state2 = create_initial_state(
            "We're interested in exploring additional capabilities",
            context={
                "customer_metadata": {
                    "company": "BigCorp Inc",
                    "title": "Director",
                    "company_size": 500,
                    "industry": "finance"
                },
                "account_details": {
                    "current_tier": "professional",
                    "total_seats": 100,
                    "monthly_recurring_revenue": 10000
                },
                "usage_data": {
                    "active_users": 85,
                    "seat_utilization_percentage": 0.85,
                    "features_used": ["dashboard", "reports", "analytics", "workflows", "integrations"],
                    "logins_per_week": 4,
                    "data_usage_gb": 200,
                    "data_quota_gb": 500,
                    "data_usage_percentage": 0.40,
                    "integrations": ["slack", "salesforce", "jira"],
                    "api_calls": 100000,
                    "user_growth_trend": "stable",
                    "feature_requests": 5
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Enterprise Add-on Potential")
        print(f"Usage Score: {result2['usage_score']['overall_score']:.2f}")
        print(f"Opportunities: {len(result2['opportunities'])}")
        print(f"Feature Recommendations: {len(result2['feature_recommendations'])}")
        print(f"Current ARR: ${result2['expansion_potential']['current_arr']:,.0f}")
        print(f"Potential ARR: ${result2['expansion_potential']['total_potential_arr']:,.0f}")
        print(f"Strategy: {result2['upsell_strategy']['approach']}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Stable customer with minimal signals
        state3 = create_initial_state(
            "Everything is working well for us",
            context={
                "customer_metadata": {
                    "company": "StableCo",
                    "title": "Manager",
                    "company_size": 50,
                    "industry": "retail"
                },
                "account_details": {
                    "current_tier": "professional",
                    "total_seats": 25,
                    "monthly_recurring_revenue": 2500
                },
                "usage_data": {
                    "active_users": 15,
                    "seat_utilization_percentage": 0.60,
                    "features_used": ["dashboard", "reports", "analytics"],
                    "logins_per_week": 2,
                    "data_usage_gb": 30,
                    "data_quota_gb": 100,
                    "data_usage_percentage": 0.30,
                    "integrations": ["slack"],
                    "api_calls": 1000,
                    "user_growth_trend": "stable",
                    "feature_requests": 0
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Stable Customer Minimal Signals")
        print(f"Usage Score: {result3['usage_score']['overall_score']:.2f}")
        print(f"Upsell Signals: {len(result3['upsell_signals'])}")
        print(f"Opportunities: {len(result3['opportunities'])}")
        print(f"Strategy Approach: {result3['upsell_strategy']['approach']}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
