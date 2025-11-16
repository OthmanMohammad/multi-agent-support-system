"""
Upsell Identifier Agent - TASK-2051

Identifies upsell opportunities based on usage patterns, calculates expansion potential,
and recommends strategic upsell approaches to grow account value.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("upsell_identifier", tier="revenue", category="customer_success")
class UpsellIdentifierAgent(BaseAgent):
    """
    Upsell Identifier Agent.

    Identifies and recommends upsell opportunities by:
    - Analyzing usage patterns and growth trends
    - Identifying feature adoption signals for premium tiers
    - Calculating expansion revenue potential
    - Scoring upsell readiness based on customer health
    - Recommending optimal upsell timing and approach
    - Generating business cases for tier upgrades
    """

    # Tier upgrade paths and value
    TIER_UPGRADES = {
        "basic": {
            "next_tier": "professional",
            "avg_uplift_pct": 150,
            "key_features": ["advanced_analytics", "automation", "api_access"]
        },
        "professional": {
            "next_tier": "enterprise",
            "avg_uplift_pct": 200,
            "key_features": ["custom_integrations", "dedicated_support", "sla", "sso"]
        },
        "enterprise": {
            "next_tier": "enterprise_plus",
            "avg_uplift_pct": 125,
            "key_features": ["white_label", "priority_support", "custom_contracts"]
        }
    }

    # Upsell readiness thresholds
    READINESS_THRESHOLDS = {
        "high": {"score_min": 75, "conversion_rate": 45},
        "medium": {"score_min": 50, "conversion_rate": 25},
        "low": {"score_min": 25, "conversion_rate": 10},
        "not_ready": {"score_min": 0, "conversion_rate": 2}
    }

    # Usage-based signals
    USAGE_SIGNALS = {
        "power_user": {"threshold": 90, "weight": 30},
        "feature_ceiling": {"threshold": 85, "weight": 25},
        "team_growth": {"threshold": 20, "weight": 20},
        "high_engagement": {"threshold": 75, "weight": 15},
        "support_requests": {"threshold": 5, "weight": 10}
    }

    def __init__(self):
        config = AgentConfig(
            name="upsell_identifier",
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
        Identify and analyze upsell opportunities.

        Args:
            state: Current agent state with customer usage and contract data

        Returns:
            Updated state with upsell analysis and recommendations
        """
        self.logger.info("upsell_identification_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        usage_data = state.get("entities", {}).get("usage_data", {})
        contract_data = state.get("entities", {}).get("contract_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "upsell_identification_details",
            customer_id=customer_id,
            current_tier=contract_data.get("tier", "unknown"),
            current_value=contract_data.get("contract_value", 0)
        )

        # Analyze usage patterns for upsell signals
        usage_analysis = self._analyze_usage_patterns(
            usage_data,
            contract_data,
            customer_metadata
        )

        # Calculate upsell readiness score
        readiness_score = self._calculate_upsell_readiness(
            usage_analysis,
            contract_data,
            customer_metadata
        )

        # Identify specific upsell opportunities
        upsell_opportunities = self._identify_upsell_opportunities(
            usage_analysis,
            readiness_score,
            contract_data,
            customer_metadata
        )

        # Calculate revenue potential
        revenue_potential = self._calculate_revenue_potential(
            upsell_opportunities,
            contract_data
        )

        # Generate upsell strategy
        upsell_strategy = self._generate_upsell_strategy(
            upsell_opportunities,
            readiness_score,
            customer_metadata
        )

        # Format response
        response = self._format_upsell_report(
            usage_analysis,
            readiness_score,
            upsell_opportunities,
            revenue_potential,
            upsell_strategy
        )

        state["agent_response"] = response
        state["upsell_readiness"] = readiness_score["readiness_level"]
        state["upsell_score"] = readiness_score["overall_score"]
        state["upsell_opportunities_count"] = len(upsell_opportunities)
        state["expansion_revenue_potential"] = revenue_potential["total_potential"]
        state["upsell_analysis"] = usage_analysis
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "upsell_identification_completed",
            customer_id=customer_id,
            readiness_level=readiness_score["readiness_level"],
            opportunities_found=len(upsell_opportunities),
            revenue_potential=revenue_potential["total_potential"]
        )

        return state

    def _analyze_usage_patterns(
        self,
        usage_data: Dict[str, Any],
        contract_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze usage patterns for upsell indicators.

        Args:
            usage_data: Customer usage metrics
            contract_data: Contract and tier information
            customer_metadata: Customer profile data

        Returns:
            Usage pattern analysis with upsell signals
        """
        # Extract usage metrics
        usage_rate = usage_data.get("usage_rate", 50)
        feature_usage = usage_data.get("feature_usage_frequency", {})
        active_users = usage_data.get("active_users", 5)
        previous_users = usage_data.get("previous_month_users", active_users)

        # Calculate user growth
        if previous_users > 0:
            user_growth_pct = ((active_users - previous_users) / previous_users) * 100
        else:
            user_growth_pct = 0

        # Identify power users
        power_user_threshold = usage_data.get("power_user_threshold", 100)
        power_users = sum(1 for freq in feature_usage.values() if freq >= power_user_threshold)
        power_user_pct = (power_users / max(active_users, 1)) * 100

        # Check for feature ceiling (using premium features heavily)
        premium_features = usage_data.get("premium_features_used", [])
        total_features = len(usage_data.get("features_used", []))
        feature_ceiling_reached = len(premium_features) >= total_features * 0.7 if total_features > 0 else False

        # Calculate engagement score
        login_frequency = usage_data.get("login_frequency_score", 50)
        session_duration = usage_data.get("avg_session_duration_minutes", 30)
        engagement_score = min(int((login_frequency + (session_duration / 60 * 100)) / 2), 100)

        # Identify usage-based signals
        signals_detected = []
        signal_scores = {}

        if power_user_pct >= self.USAGE_SIGNALS["power_user"]["threshold"]:
            signals_detected.append("power_user_behavior")
            signal_scores["power_user"] = self.USAGE_SIGNALS["power_user"]["weight"]

        if feature_ceiling_reached or usage_rate >= self.USAGE_SIGNALS["feature_ceiling"]["threshold"]:
            signals_detected.append("feature_ceiling_reached")
            signal_scores["feature_ceiling"] = self.USAGE_SIGNALS["feature_ceiling"]["weight"]

        if user_growth_pct >= self.USAGE_SIGNALS["team_growth"]["threshold"]:
            signals_detected.append("rapid_team_growth")
            signal_scores["team_growth"] = self.USAGE_SIGNALS["team_growth"]["weight"]

        if engagement_score >= self.USAGE_SIGNALS["high_engagement"]["threshold"]:
            signals_detected.append("high_engagement")
            signal_scores["high_engagement"] = self.USAGE_SIGNALS["high_engagement"]["weight"]

        # Check support requests for advanced features
        advanced_support_tickets = usage_data.get("advanced_feature_support_tickets", 0)
        if advanced_support_tickets >= self.USAGE_SIGNALS["support_requests"]["threshold"]:
            signals_detected.append("requesting_advanced_features")
            signal_scores["support_requests"] = self.USAGE_SIGNALS["support_requests"]["weight"]

        return {
            "usage_rate": usage_rate,
            "active_users": active_users,
            "user_growth_pct": round(user_growth_pct, 1),
            "power_user_pct": round(power_user_pct, 1),
            "power_users_count": power_users,
            "feature_ceiling_reached": feature_ceiling_reached,
            "engagement_score": engagement_score,
            "signals_detected": signals_detected,
            "signal_scores": signal_scores,
            "total_signal_score": sum(signal_scores.values()),
            "premium_features_used": len(premium_features),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_upsell_readiness(
        self,
        usage_analysis: Dict[str, Any],
        contract_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate customer's readiness for upsell.

        Args:
            usage_analysis: Usage pattern analysis
            contract_data: Contract information
            customer_metadata: Customer profile

        Returns:
            Upsell readiness assessment
        """
        score = 0

        # Usage signals (0-40 points)
        score += min(usage_analysis["total_signal_score"], 40)

        # Customer health (0-25 points)
        health_score = customer_metadata.get("health_score", 50)
        score += (health_score / 100) * 25

        # Contract tenure (0-15 points)
        months_as_customer = contract_data.get("months_as_customer", 6)
        if months_as_customer >= 12:
            score += 15
        elif months_as_customer >= 6:
            score += 10
        elif months_as_customer >= 3:
            score += 5

        # Payment history (0-10 points)
        payment_status = contract_data.get("payment_status", "current")
        if payment_status == "current":
            score += 10
        elif payment_status == "past_due_7":
            score += 5

        # NPS/satisfaction (0-10 points)
        nps_score = customer_metadata.get("nps_score", 5)
        if nps_score >= 9:
            score += 10
        elif nps_score >= 7:
            score += 7
        elif nps_score >= 5:
            score += 4

        overall_score = min(int(score), 100)

        # Determine readiness level
        readiness_level = "not_ready"
        for level, config in sorted(
            self.READINESS_THRESHOLDS.items(),
            key=lambda x: x[1]["score_min"],
            reverse=True
        ):
            if overall_score >= config["score_min"]:
                readiness_level = level
                break

        # Calculate conversion probability
        conversion_probability = self.READINESS_THRESHOLDS[readiness_level]["conversion_rate"]

        # Identify readiness factors
        readiness_factors = []
        blockers = []

        if usage_analysis["total_signal_score"] >= 30:
            readiness_factors.append("Strong usage signals indicating need for upgrade")
        if health_score >= 75:
            readiness_factors.append("Excellent customer health")
        if months_as_customer >= 6:
            readiness_factors.append("Established customer relationship")
        if nps_score >= 9:
            readiness_factors.append("High customer satisfaction")

        if health_score < 50:
            blockers.append("Low customer health - address issues before upsell")
        if payment_status != "current":
            blockers.append("Payment issues must be resolved first")
        if months_as_customer < 3:
            blockers.append("Customer too new - allow time for value realization")

        return {
            "overall_score": overall_score,
            "readiness_level": readiness_level,
            "conversion_probability": conversion_probability,
            "readiness_factors": readiness_factors,
            "blockers": blockers,
            "recommended_timing": self._recommend_timing(readiness_level, usage_analysis)
        }

    def _recommend_timing(self, readiness_level: str, usage_analysis: Dict[str, Any]) -> str:
        """Recommend optimal timing for upsell approach."""
        if readiness_level == "high":
            return "Immediate - customer is ready for upsell conversation"
        elif readiness_level == "medium":
            if usage_analysis["feature_ceiling_reached"]:
                return "Within 2 weeks - feature limitations creating urgency"
            return "Within 30 days - build case and warm up conversation"
        elif readiness_level == "low":
            return "60-90 days - nurture and develop readiness signals"
        else:
            return "Not recommended - focus on adoption and health improvement"

    def _identify_upsell_opportunities(
        self,
        usage_analysis: Dict[str, Any],
        readiness_score: Dict[str, Any],
        contract_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify specific upsell opportunities.

        Args:
            usage_analysis: Usage pattern analysis
            readiness_score: Upsell readiness assessment
            contract_data: Contract information
            customer_metadata: Customer profile

        Returns:
            List of upsell opportunities
        """
        opportunities = []
        current_tier = contract_data.get("tier", "basic")

        # Tier upgrade opportunity
        if current_tier in self.TIER_UPGRADES:
            tier_info = self.TIER_UPGRADES[current_tier]

            # Calculate tier upgrade value
            current_value = contract_data.get("contract_value", 10000)
            projected_value = int(current_value * (tier_info["avg_uplift_pct"] / 100))

            opportunity = {
                "opportunity_type": "tier_upgrade",
                "from_tier": current_tier,
                "to_tier": tier_info["next_tier"],
                "current_value": current_value,
                "projected_value": projected_value,
                "incremental_revenue": projected_value - current_value,
                "key_features": tier_info["key_features"],
                "priority": "high" if readiness_score["readiness_level"] == "high" else "medium",
                "business_case": self._build_tier_upgrade_case(usage_analysis, tier_info, customer_metadata)
            }
            opportunities.append(opportunity)

        # Seat expansion opportunity
        if usage_analysis["user_growth_pct"] > 15 or usage_analysis["usage_rate"] > 85:
            current_seats = contract_data.get("contracted_users", 10)
            recommended_seats = int(current_seats * 1.25)  # 25% expansion
            seat_price = contract_data.get("per_seat_price", 100)

            opportunities.append({
                "opportunity_type": "seat_expansion",
                "current_seats": current_seats,
                "recommended_seats": recommended_seats,
                "additional_seats": recommended_seats - current_seats,
                "incremental_revenue": (recommended_seats - current_seats) * seat_price,
                "priority": "high" if usage_analysis["usage_rate"] > 90 else "medium",
                "business_case": f"Current usage at {usage_analysis['usage_rate']}% - proactive expansion recommended"
            })

        # Premium features add-on
        signals = usage_analysis.get("signals_detected", [])
        if "requesting_advanced_features" in signals or "power_user_behavior" in signals:
            opportunities.append({
                "opportunity_type": "premium_add_ons",
                "recommended_add_ons": ["advanced_analytics", "api_access", "custom_integrations"],
                "estimated_value": 5000,
                "incremental_revenue": 5000,
                "priority": "medium",
                "business_case": "Power users requesting advanced capabilities"
            })

        # Professional services
        if usage_analysis["engagement_score"] >= 70 and readiness_score["overall_score"] >= 60:
            opportunities.append({
                "opportunity_type": "professional_services",
                "services": ["custom_implementation", "advanced_training", "dedicated_csm"],
                "estimated_value": 10000,
                "incremental_revenue": 10000,
                "priority": "low",
                "business_case": "High engagement suggests readiness for enhanced support"
            })

        # Sort by priority and incremental revenue
        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(
            key=lambda x: (priority_order.get(x.get("priority", "low"), 3), -x.get("incremental_revenue", 0))
        )

        return opportunities

    def _build_tier_upgrade_case(
        self,
        usage_analysis: Dict[str, Any],
        tier_info: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> str:
        """Build business case for tier upgrade."""
        signals = usage_analysis.get("signals_detected", [])

        if "feature_ceiling_reached" in signals:
            return f"Customer maximizing {tier_info['next_tier']} features - upgrade removes limitations"
        elif "power_user_behavior" in signals:
            return f"{usage_analysis['power_user_pct']:.0f}% power users need {tier_info['next_tier']} capabilities"
        elif "rapid_team_growth" in signals:
            return f"Team growing {usage_analysis['user_growth_pct']:.0f}% - {tier_info['next_tier']} tier scales better"
        else:
            return f"Usage patterns indicate need for {tier_info['next_tier']} features"

    def _calculate_revenue_potential(
        self,
        opportunities: List[Dict[str, Any]],
        contract_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate total revenue potential from opportunities.

        Args:
            opportunities: List of identified opportunities
            contract_data: Contract information

        Returns:
            Revenue potential analysis
        """
        total_potential = sum(opp.get("incremental_revenue", 0) for opp in opportunities)
        current_arr = contract_data.get("contract_value", 0)

        if current_arr > 0:
            expansion_percentage = (total_potential / current_arr) * 100
        else:
            expansion_percentage = 0

        # Calculate weighted potential (by priority)
        priority_weights = {"high": 1.0, "medium": 0.6, "low": 0.3}
        weighted_potential = sum(
            opp.get("incremental_revenue", 0) * priority_weights.get(opp.get("priority", "low"), 0.3)
            for opp in opportunities
        )

        return {
            "total_potential": total_potential,
            "weighted_potential": int(weighted_potential),
            "current_arr": current_arr,
            "expansion_percentage": round(expansion_percentage, 1),
            "opportunity_breakdown": [
                {
                    "type": opp["opportunity_type"],
                    "value": opp.get("incremental_revenue", 0),
                    "priority": opp.get("priority", "medium")
                }
                for opp in opportunities[:5]
            ]
        }

    def _generate_upsell_strategy(
        self,
        opportunities: List[Dict[str, Any]],
        readiness_score: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate strategic approach for upsell.

        Args:
            opportunities: Identified opportunities
            readiness_score: Readiness assessment
            customer_metadata: Customer profile

        Returns:
            Upsell strategy and tactics
        """
        if not opportunities:
            return {
                "strategy": "nurture",
                "approach": "Focus on adoption and value realization",
                "tactics": ["Monitor usage patterns", "Provide training resources"],
                "timeline": "ongoing"
            }

        top_opportunity = opportunities[0]
        readiness_level = readiness_score["readiness_level"]

        strategy = {
            "primary_opportunity": top_opportunity["opportunity_type"],
            "approach": "",
            "tactics": [],
            "timeline": readiness_score["recommended_timing"],
            "key_message": "",
            "stakeholders": []
        }

        # Define approach based on readiness
        if readiness_level == "high":
            strategy["approach"] = "Direct upsell conversation"
            strategy["tactics"] = [
                "Schedule business review with decision maker",
                "Present ROI analysis and expansion proposal",
                "Demonstrate premium features addressing current limitations",
                "Offer limited-time incentive for commitment"
            ]
            strategy["stakeholders"] = ["CSM", "Account Executive", "VP Customer Success"]
        elif readiness_level == "medium":
            strategy["approach"] = "Value-building campaign"
            strategy["tactics"] = [
                "Share case studies of similar customers who upgraded",
                "Provide trial access to premium features",
                "Host demo of advanced capabilities",
                "Gather feedback on feature needs"
            ]
            strategy["stakeholders"] = ["CSM", "Account Executive"]
        else:
            strategy["approach"] = "Long-term nurture"
            strategy["tactics"] = [
                "Focus on driving adoption of current features",
                "Schedule regular success reviews",
                "Monitor for readiness signals",
                "Educate on product roadmap"
            ]
            strategy["stakeholders"] = ["CSM"]

        # Set key message based on opportunity
        if top_opportunity["opportunity_type"] == "tier_upgrade":
            strategy["key_message"] = f"Unlock {top_opportunity['to_tier']} capabilities to support your growth"
        elif top_opportunity["opportunity_type"] == "seat_expansion":
            strategy["key_message"] = f"Expand from {top_opportunity['current_seats']} to {top_opportunity['recommended_seats']} seats for growing team"
        else:
            strategy["key_message"] = "Enhance your capabilities with advanced features"

        return strategy

    def _format_upsell_report(
        self,
        usage_analysis: Dict[str, Any],
        readiness_score: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        revenue_potential: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> str:
        """Format upsell identification report."""
        readiness_level = readiness_score["readiness_level"]

        readiness_emoji = {
            "high": "????",
            "medium": "????",
            "low": "????",
            "not_ready": "????"
        }

        report = f"""**???? Upsell Opportunity Analysis**

**Upsell Readiness:** {readiness_level.upper().replace('_', ' ')} {readiness_emoji.get(readiness_level, '???')}
**Readiness Score:** {readiness_score['overall_score']}/100
**Conversion Probability:** {readiness_score['conversion_probability']}%
**Recommended Timing:** {readiness_score['recommended_timing']}

**Usage Analysis:**
- Active Users: {usage_analysis['active_users']} (Growth: {usage_analysis['user_growth_pct']:+.1f}%)
- Usage Rate: {usage_analysis['usage_rate']}%
- Power Users: {usage_analysis['power_users_count']} ({usage_analysis['power_user_pct']:.0f}%)
- Engagement Score: {usage_analysis['engagement_score']}/100
- Premium Features Used: {usage_analysis['premium_features_used']}

**Upsell Signals Detected:**
"""

        for signal in usage_analysis["signals_detected"]:
            report += f"- {signal.replace('_', ' ').title()}\n"

        if not usage_analysis["signals_detected"]:
            report += "- No strong upsell signals detected\n"

        # Readiness factors
        if readiness_score["readiness_factors"]:
            report += "\n**??? Readiness Factors:**\n"
            for factor in readiness_score["readiness_factors"]:
                report += f"- {factor}\n"

        # Blockers
        if readiness_score["blockers"]:
            report += "\n**???? Blockers:**\n"
            for blocker in readiness_score["blockers"]:
                report += f"- {blocker}\n"

        # Opportunities
        if opportunities:
            report += f"\n**???? Upsell Opportunities ({len(opportunities)} identified):**\n"
            for i, opp in enumerate(opportunities[:3], 1):
                priority_icon = "????" if opp["priority"] == "high" else "????" if opp["priority"] == "medium" else "????"
                report += f"\n{i}. **{opp['opportunity_type'].replace('_', ' ').title()}** {priority_icon}\n"
                report += f"   - Incremental Revenue: ${opp.get('incremental_revenue', 0):,}\n"
                report += f"   - Business Case: {opp.get('business_case', 'N/A')}\n"

        # Revenue potential
        report += f"\n**???? Revenue Potential:**\n"
        report += f"- Total Potential: ${revenue_potential['total_potential']:,}\n"
        report += f"- Weighted Potential: ${revenue_potential['weighted_potential']:,}\n"
        report += f"- Current ARR: ${revenue_potential['current_arr']:,}\n"
        report += f"- Potential Expansion: {revenue_potential['expansion_percentage']:.1f}%\n"

        # Strategy
        report += f"\n**???? Recommended Strategy:**\n"
        report += f"**Approach:** {strategy['approach']}\n"
        report += f"**Primary Focus:** {strategy['primary_opportunity'].replace('_', ' ').title()}\n"
        report += f"**Key Message:** {strategy['key_message']}\n\n"
        report += "**Tactics:**\n"
        for tactic in strategy["tactics"][:4]:
            report += f"- {tactic}\n"

        report += f"\n**Stakeholders:** {', '.join(strategy['stakeholders'])}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Upsell Identifier Agent (TASK-2051)")
        print("=" * 70)

        agent = UpsellIdentifierAgent()

        # Test 1: High readiness scenario
        print("\n\nTest 1: High Upsell Readiness")
        print("-" * 70)

        state1 = create_initial_state(
            "Identify upsell opportunities",
            context={
                "customer_id": "cust_high_readiness",
                "customer_metadata": {
                    "plan": "professional",
                    "industry": "technology",
                    "health_score": 85,
                    "nps_score": 9
                }
            }
        )
        state1["entities"] = {
            "usage_data": {
                "usage_rate": 92,
                "active_users": 45,
                "previous_month_users": 35,
                "power_user_threshold": 100,
                "feature_usage_frequency": {
                    "feature_1": 120, "feature_2": 150, "feature_3": 110,
                    "feature_4": 95, "feature_5": 88
                },
                "premium_features_used": ["analytics", "automation", "api"],
                "features_used": ["analytics", "automation", "api", "basic"],
                "login_frequency_score": 85,
                "avg_session_duration_minutes": 45,
                "advanced_feature_support_tickets": 6
            },
            "contract_data": {
                "tier": "professional",
                "contract_value": 50000,
                "contracted_users": 40,
                "per_seat_price": 1250,
                "months_as_customer": 14,
                "payment_status": "current"
            }
        }

        result1 = await agent.process(state1)

        print(f"Readiness Level: {result1['upsell_readiness']}")
        print(f"Upsell Score: {result1['upsell_score']}/100")
        print(f"Opportunities Found: {result1['upsell_opportunities_count']}")
        print(f"Revenue Potential: ${result1['expansion_revenue_potential']:,}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Low readiness scenario
        print("\n\n" + "=" * 70)
        print("Test 2: Low Upsell Readiness")
        print("-" * 70)

        state2 = create_initial_state(
            "Check upsell potential",
            context={
                "customer_id": "cust_low_readiness",
                "customer_metadata": {
                    "plan": "basic",
                    "industry": "retail",
                    "health_score": 45,
                    "nps_score": 5
                }
            }
        )
        state2["entities"] = {
            "usage_data": {
                "usage_rate": 35,
                "active_users": 5,
                "previous_month_users": 6,
                "feature_usage_frequency": {"feature_1": 12, "feature_2": 8},
                "premium_features_used": [],
                "features_used": ["feature_1", "feature_2"],
                "login_frequency_score": 30,
                "avg_session_duration_minutes": 15,
                "advanced_feature_support_tickets": 0
            },
            "contract_data": {
                "tier": "basic",
                "contract_value": 12000,
                "contracted_users": 10,
                "per_seat_price": 1200,
                "months_as_customer": 2,
                "payment_status": "current"
            }
        }

        result2 = await agent.process(state2)

        print(f"Readiness Level: {result2['upsell_readiness']}")
        print(f"Upsell Score: {result2['upsell_score']}/100")
        print(f"Opportunities Found: {result2['upsell_opportunities_count']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
