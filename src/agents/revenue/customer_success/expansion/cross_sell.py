"""
Cross-Sell Agent - TASK-2053

Identifies cross-sell opportunities for complementary products, add-ons, and modules
based on customer usage patterns, industry, and business needs.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("cross_sell", tier="revenue", category="customer_success")
class CrossSellAgent(BaseAgent):
    """
    Cross-Sell Agent.

    Identifies cross-sell opportunities by:
    - Analyzing product usage to identify complementary needs
    - Matching customer profile to product catalog
    - Scoring cross-sell fit based on industry and use case
    - Calculating incremental revenue potential
    - Generating product recommendations with business cases
    - Timing cross-sell conversations for maximum success
    """

    # Product catalog with complementary relationships
    PRODUCT_CATALOG = {
        "analytics_platform": {
            "category": "analytics",
            "complements": ["data_warehouse", "business_intelligence", "reporting_suite"],
            "typical_arr": 25000,
            "industries": ["technology", "finance", "healthcare", "retail"],
        },
        "data_warehouse": {
            "category": "data_infrastructure",
            "complements": ["analytics_platform", "etl_tools", "data_governance"],
            "typical_arr": 40000,
            "industries": ["technology", "finance", "healthcare"],
        },
        "business_intelligence": {
            "category": "analytics",
            "complements": ["analytics_platform", "data_warehouse", "predictive_analytics"],
            "typical_arr": 30000,
            "industries": ["retail", "finance", "manufacturing"],
        },
        "collaboration_suite": {
            "category": "productivity",
            "complements": ["project_management", "document_management", "communication_tools"],
            "typical_arr": 15000,
            "industries": ["technology", "professional_services", "education"],
        },
        "security_suite": {
            "category": "security",
            "complements": ["compliance_module", "audit_logging", "identity_management"],
            "typical_arr": 35000,
            "industries": ["finance", "healthcare", "government"],
        },
        "api_gateway": {
            "category": "infrastructure",
            "complements": ["monitoring_suite", "developer_portal", "rate_limiting"],
            "typical_arr": 20000,
            "industries": ["technology", "finance"],
        },
        "mobile_app": {
            "category": "mobile",
            "complements": ["push_notifications", "mobile_analytics", "app_store_optimization"],
            "typical_arr": 18000,
            "industries": ["retail", "media", "education"],
        },
        "compliance_module": {
            "category": "compliance",
            "complements": ["security_suite", "audit_logging", "data_governance"],
            "typical_arr": 28000,
            "industries": ["finance", "healthcare", "government"],
        },
    }

    # Add-on modules
    ADD_ON_MODULES = {
        "premium_support": {
            "value": 12000,
            "signals": ["high_ticket_volume", "complex_use_case", "enterprise_tier"],
        },
        "advanced_training": {
            "value": 8000,
            "signals": ["low_adoption", "new_features", "team_growth"],
        },
        "custom_integration": {
            "value": 15000,
            "signals": ["integration_requests", "api_usage", "workflow_complexity"],
        },
        "dedicated_csm": {
            "value": 25000,
            "signals": ["strategic_account", "high_arr", "executive_engagement"],
        },
        "white_label": {"value": 20000, "signals": ["agency", "reseller", "brand_requirements"]},
    }

    # Cross-sell readiness scoring
    READINESS_FACTORS = {
        "product_fit": 30,
        "customer_health": 25,
        "usage_signals": 20,
        "account_maturity": 15,
        "budget_timing": 10,
    }

    def __init__(self):
        config = AgentConfig(
            name="cross_sell",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            max_tokens=800,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="customer_success",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Identify and analyze cross-sell opportunities.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with cross-sell analysis and recommendations
        """
        self.logger.info("cross_sell_analysis_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        usage_data = state.get("entities", {}).get("usage_data", {})
        contract_data = state.get("entities", {}).get("contract_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "cross_sell_analysis_details",
            customer_id=customer_id,
            current_products=len(contract_data.get("current_products", [])),
            industry=customer_metadata.get("industry", "unknown"),
        )

        # Analyze customer profile for cross-sell fit
        profile_analysis = self._analyze_customer_profile(
            customer_metadata, contract_data, usage_data
        )

        # Identify cross-sell opportunities
        cross_sell_opportunities = self._identify_cross_sell_opportunities(
            profile_analysis, contract_data, customer_metadata
        )

        # Identify add-on opportunities
        add_on_opportunities = self._identify_add_on_opportunities(
            usage_data, contract_data, customer_metadata
        )

        # Calculate cross-sell readiness
        readiness_scores = self._calculate_cross_sell_readiness(
            cross_sell_opportunities, add_on_opportunities, profile_analysis, customer_metadata
        )

        # Calculate revenue potential
        revenue_potential = self._calculate_cross_sell_revenue(
            cross_sell_opportunities, add_on_opportunities, contract_data
        )

        # Generate cross-sell strategy
        cross_sell_strategy = self._generate_cross_sell_strategy(
            cross_sell_opportunities, add_on_opportunities, readiness_scores, customer_metadata
        )

        # Format response
        response = self._format_cross_sell_report(
            profile_analysis,
            cross_sell_opportunities,
            add_on_opportunities,
            readiness_scores,
            revenue_potential,
            cross_sell_strategy,
        )

        state["agent_response"] = response
        state["cross_sell_opportunities_count"] = len(cross_sell_opportunities) + len(
            add_on_opportunities
        )
        state["cross_sell_revenue_potential"] = revenue_potential["total_potential"]
        state["top_cross_sell_readiness"] = (
            readiness_scores[0]["readiness_score"] if readiness_scores else 0
        )
        state["cross_sell_analysis"] = profile_analysis
        state["response_confidence"] = 0.86
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "cross_sell_analysis_completed",
            customer_id=customer_id,
            opportunities_found=len(cross_sell_opportunities) + len(add_on_opportunities),
            revenue_potential=revenue_potential["total_potential"],
        )

        return state

    def _analyze_customer_profile(
        self,
        customer_metadata: dict[str, Any],
        contract_data: dict[str, Any],
        usage_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Analyze customer profile for cross-sell fit.

        Args:
            customer_metadata: Customer profile information
            contract_data: Current contract and products
            usage_data: Usage patterns

        Returns:
            Profile analysis for cross-sell targeting
        """
        industry = customer_metadata.get("industry", "general")
        company_size = customer_metadata.get("company_size", "medium")
        current_products = contract_data.get("current_products", [])

        # Identify product gaps
        product_categories_owned = set()
        for product in current_products:
            if product in self.PRODUCT_CATALOG:
                category = self.PRODUCT_CATALOG[product]["category"]
                product_categories_owned.add(category)

        # Identify usage patterns suggesting cross-sell
        usage_signals = []

        if usage_data.get("api_usage_high", False):
            usage_signals.append("high_api_usage")
        if usage_data.get("data_volume_growing", False):
            usage_signals.append("data_growth")
        if usage_data.get("collaboration_features_used", False):
            usage_signals.append("team_collaboration")
        if usage_data.get("security_inquiries", 0) > 3:
            usage_signals.append("security_interest")
        if usage_data.get("mobile_requests", 0) > 0:
            usage_signals.append("mobile_needs")
        if usage_data.get("integration_attempts", 0) > 5:
            usage_signals.append("integration_needs")

        # Calculate customer health for cross-sell timing
        health_score = customer_metadata.get("health_score", 50)
        health_status = (
            "excellent" if health_score >= 80 else "good" if health_score >= 60 else "fair"
        )

        # Determine account maturity
        months_as_customer = contract_data.get("months_as_customer", 0)
        if months_as_customer >= 12:
            maturity = "established"
        elif months_as_customer >= 6:
            maturity = "growing"
        else:
            maturity = "new"

        return {
            "industry": industry,
            "company_size": company_size,
            "current_products": current_products,
            "product_categories_owned": list(product_categories_owned),
            "usage_signals": usage_signals,
            "health_score": health_score,
            "health_status": health_status,
            "account_maturity": maturity,
            "months_as_customer": months_as_customer,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    def _identify_cross_sell_opportunities(
        self,
        profile_analysis: dict[str, Any],
        contract_data: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Identify product cross-sell opportunities.

        Args:
            profile_analysis: Customer profile analysis
            contract_data: Current contract data
            customer_metadata: Customer metadata

        Returns:
            List of cross-sell product opportunities
        """
        opportunities = []
        current_products = profile_analysis["current_products"]
        industry = profile_analysis["industry"]

        # Analyze complementary products for owned products
        for owned_product in current_products:
            if owned_product in self.PRODUCT_CATALOG:
                product_info = self.PRODUCT_CATALOG[owned_product]

                # Check complementary products
                for complement in product_info["complements"]:
                    if complement not in current_products and complement in self.PRODUCT_CATALOG:
                        complement_info = self.PRODUCT_CATALOG[complement]

                        # Check industry fit
                        industry_fit = industry in complement_info["industries"]

                        # Calculate product fit score
                        fit_score = self._calculate_product_fit_score(
                            complement, complement_info, profile_analysis, industry_fit
                        )

                        if fit_score >= 50:  # Minimum threshold
                            opportunities.append(
                                {
                                    "product": complement,
                                    "category": complement_info["category"],
                                    "typical_arr": complement_info["typical_arr"],
                                    "fit_score": fit_score,
                                    "complements": owned_product,
                                    "industry_fit": industry_fit,
                                    "business_case": self._build_product_business_case(
                                        complement, owned_product, profile_analysis
                                    ),
                                }
                            )

        # Remove duplicates and sort by fit score
        seen_products = set()
        unique_opportunities = []
        for opp in sorted(opportunities, key=lambda x: x["fit_score"], reverse=True):
            if opp["product"] not in seen_products:
                unique_opportunities.append(opp)
                seen_products.add(opp["product"])

        return unique_opportunities[:5]

    def _calculate_product_fit_score(
        self,
        product: str,
        product_info: dict[str, Any],
        profile_analysis: dict[str, Any],
        industry_fit: bool,
    ) -> int:
        """Calculate product fit score (0-100)."""
        score = 0

        # Industry fit (0-30 points)
        if industry_fit:
            score += 30
        else:
            score += 10  # Still some potential

        # Usage signals alignment (0-40 points)
        signal_matches = 0
        if (
            product_info["category"] == "analytics"
            and "data_growth" in profile_analysis["usage_signals"]
        ):
            signal_matches += 1
        if (
            product_info["category"] == "security"
            and "security_interest" in profile_analysis["usage_signals"]
        ):
            signal_matches += 1
        if (
            product_info["category"] == "infrastructure"
            and "high_api_usage" in profile_analysis["usage_signals"]
        ):
            signal_matches += 1
        if (
            product_info["category"] == "mobile"
            and "mobile_needs" in profile_analysis["usage_signals"]
        ):
            signal_matches += 1
        if (
            product_info["category"] == "productivity"
            and "team_collaboration" in profile_analysis["usage_signals"]
        ):
            signal_matches += 1

        score += min(signal_matches * 15, 40)

        # Customer health (0-20 points)
        health_score = profile_analysis["health_score"]
        score += (health_score / 100) * 20

        # Account maturity (0-10 points)
        if profile_analysis["account_maturity"] == "established":
            score += 10
        elif profile_analysis["account_maturity"] == "growing":
            score += 7

        return min(int(score), 100)

    def _build_product_business_case(
        self, product: str, owned_product: str, profile_analysis: dict[str, Any]
    ) -> str:
        """Build business case for cross-sell product."""
        product_name = product.replace("_", " ").title()
        owned_name = owned_product.replace("_", " ").title()

        cases = {
            "analytics": f"Enhance {owned_name} with advanced analytics capabilities",
            "data_infrastructure": f"Scale data operations to support {owned_name} growth",
            "security": f"Protect {owned_name} data with enterprise security",
            "infrastructure": f"Build robust infrastructure for {owned_name}",
            "productivity": f"Improve team efficiency alongside {owned_name}",
            "mobile": f"Extend {owned_name} to mobile users",
            "compliance": f"Meet regulatory requirements for {owned_name}",
        }

        category = self.PRODUCT_CATALOG.get(product, {}).get("category", "general")
        return cases.get(category, f"Complement {owned_name} with {product_name}")

    def _identify_add_on_opportunities(
        self,
        usage_data: dict[str, Any],
        contract_data: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Identify add-on module opportunities.

        Args:
            usage_data: Usage patterns
            contract_data: Contract information
            customer_metadata: Customer profile

        Returns:
            List of add-on opportunities
        """
        opportunities = []
        current_arr = contract_data.get("contract_value", 0)

        # Check signals for each add-on
        for add_on, config in self.ADD_ON_MODULES.items():
            signals_matched = []

            # Check for signal matches
            for signal in config["signals"]:
                if self._check_add_on_signal(
                    signal, usage_data, contract_data, customer_metadata, current_arr
                ):
                    signals_matched.append(signal)

            # If 2 or more signals match, it's a good opportunity
            if len(signals_matched) >= 2:
                opportunities.append(
                    {
                        "add_on": add_on,
                        "value": config["value"],
                        "signals_matched": signals_matched,
                        "fit_score": min(len(signals_matched) * 33, 100),
                        "business_case": self._build_add_on_business_case(add_on, signals_matched),
                    }
                )

        # Sort by value and fit score
        opportunities.sort(key=lambda x: (x["fit_score"], x["value"]), reverse=True)

        return opportunities[:4]

    def _check_add_on_signal(
        self,
        signal: str,
        usage_data: dict[str, Any],
        contract_data: dict[str, Any],
        customer_metadata: dict[str, Any],
        current_arr: int,
    ) -> bool:
        """Check if a specific signal is present."""
        signal_checks = {
            "high_ticket_volume": usage_data.get("support_tickets_last_30d", 0) > 10,
            "complex_use_case": usage_data.get("advanced_features_used", 0) > 5,
            "enterprise_tier": contract_data.get("tier", "") == "enterprise",
            "low_adoption": usage_data.get("adoption_score", 100) < 60,
            "new_features": usage_data.get("new_features_released", 0) > 3,
            "team_growth": usage_data.get("user_growth_pct", 0) > 20,
            "integration_requests": usage_data.get("integration_attempts", 0) > 5,
            "api_usage": usage_data.get("api_calls", 0) > 100000,
            "workflow_complexity": usage_data.get("custom_workflows", 0) > 10,
            "strategic_account": customer_metadata.get("account_tier", "") == "strategic",
            "high_arr": current_arr > 100000,
            "executive_engagement": customer_metadata.get("executive_sponsor", False),
            "agency": customer_metadata.get("company_type", "") == "agency",
            "reseller": customer_metadata.get("company_type", "") == "reseller",
            "brand_requirements": customer_metadata.get("brand_customization_requests", 0) > 2,
        }

        return signal_checks.get(signal, False)

    def _build_add_on_business_case(self, add_on: str, signals: list[str]) -> str:
        """Build business case for add-on."""
        cases = {
            "premium_support": "Reduce ticket resolution time and get dedicated support resources",
            "advanced_training": "Accelerate adoption and maximize product value realization",
            "custom_integration": "Streamline workflows with tailored integrations",
            "dedicated_csm": "Get strategic guidance and proactive account management",
            "white_label": "Deliver branded experience to your customers",
        }

        base_case = cases.get(add_on, f"Enhance capabilities with {add_on.replace('_', ' ')}")
        return f"{base_case} (Based on: {', '.join(s.replace('_', ' ') for s in signals)})"

    def _calculate_cross_sell_readiness(
        self,
        cross_sell_opportunities: list[dict[str, Any]],
        add_on_opportunities: list[dict[str, Any]],
        profile_analysis: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Calculate readiness score for each opportunity."""
        all_opportunities = []

        # Score cross-sell products
        for opp in cross_sell_opportunities:
            readiness_score = self._calculate_readiness_score(
                opp["fit_score"], profile_analysis, customer_metadata
            )

            all_opportunities.append(
                {
                    "opportunity_type": "product",
                    "name": opp["product"],
                    "readiness_score": readiness_score,
                    "fit_score": opp["fit_score"],
                    "potential_value": opp["typical_arr"],
                    "business_case": opp["business_case"],
                }
            )

        # Score add-ons
        for opp in add_on_opportunities:
            readiness_score = self._calculate_readiness_score(
                opp["fit_score"], profile_analysis, customer_metadata
            )

            all_opportunities.append(
                {
                    "opportunity_type": "add_on",
                    "name": opp["add_on"],
                    "readiness_score": readiness_score,
                    "fit_score": opp["fit_score"],
                    "potential_value": opp["value"],
                    "business_case": opp["business_case"],
                }
            )

        # Sort by readiness score
        all_opportunities.sort(key=lambda x: x["readiness_score"], reverse=True)

        return all_opportunities

    def _calculate_readiness_score(
        self, fit_score: int, profile_analysis: dict[str, Any], customer_metadata: dict[str, Any]
    ) -> int:
        """Calculate overall readiness score for cross-sell."""
        score = 0

        # Product fit (30%)
        score += (fit_score / 100) * 30

        # Customer health (25%)
        health_score = profile_analysis["health_score"]
        score += (health_score / 100) * 25

        # Usage signals (20%)
        signal_strength = min(len(profile_analysis["usage_signals"]) * 5, 20)
        score += signal_strength

        # Account maturity (15%)
        maturity = profile_analysis["account_maturity"]
        if maturity == "established":
            score += 15
        elif maturity == "growing":
            score += 10
        else:
            score += 5

        # Budget timing (10%)
        # Simplified - would integrate with fiscal year data in production
        score += 7

        return min(int(score), 100)

    def _calculate_cross_sell_revenue(
        self,
        cross_sell_opportunities: list[dict[str, Any]],
        add_on_opportunities: list[dict[str, Any]],
        contract_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate total cross-sell revenue potential."""
        product_potential = sum(opp["typical_arr"] for opp in cross_sell_opportunities)
        add_on_potential = sum(opp["value"] for opp in add_on_opportunities)
        total_potential = product_potential + add_on_potential

        current_arr = contract_data.get("contract_value", 0)
        expansion_pct = total_potential / current_arr * 100 if current_arr > 0 else 0

        return {
            "total_potential": total_potential,
            "product_potential": product_potential,
            "add_on_potential": add_on_potential,
            "current_arr": current_arr,
            "expansion_percentage": round(expansion_pct, 1),
            "opportunities_count": len(cross_sell_opportunities) + len(add_on_opportunities),
        }

    def _generate_cross_sell_strategy(
        self,
        cross_sell_opportunities: list[dict[str, Any]],
        add_on_opportunities: list[dict[str, Any]],
        readiness_scores: list[dict[str, Any]],
        customer_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate strategic approach for cross-sell."""
        if not readiness_scores:
            return {
                "approach": "nurture",
                "timeline": "future",
                "tactics": ["Monitor for cross-sell signals"],
                "primary_focus": None,
            }

        top_opportunity = readiness_scores[0]

        strategy = {
            "primary_focus": top_opportunity["name"],
            "opportunity_type": top_opportunity["opportunity_type"],
            "readiness_score": top_opportunity["readiness_score"],
            "approach": "",
            "timeline": "",
            "tactics": [],
            "key_stakeholders": [],
        }

        # Define approach based on readiness
        if top_opportunity["readiness_score"] >= 75:
            strategy["approach"] = "Direct cross-sell presentation"
            strategy["timeline"] = "This quarter"
            strategy["tactics"] = [
                f"Present {top_opportunity['name'].replace('_', ' ')} with ROI analysis",
                "Provide product demo focused on complementary value",
                "Share case study from similar customer",
                "Offer trial period or POC",
            ]
            strategy["key_stakeholders"] = ["CSM", "Account Executive", "Sales Engineer"]
        elif top_opportunity["readiness_score"] >= 50:
            strategy["approach"] = "Educational campaign"
            strategy["timeline"] = "Next quarter"
            strategy["tactics"] = [
                "Share thought leadership on complementary solutions",
                "Invite to product webinar or workshop",
                "Provide use case documentation",
                "Gather feedback on needs and gaps",
            ]
            strategy["key_stakeholders"] = ["CSM", "Product Marketing"]
        else:
            strategy["approach"] = "Long-term nurture"
            strategy["timeline"] = "6+ months"
            strategy["tactics"] = [
                "Include in product update communications",
                "Monitor for changing needs",
                "Build relationship with decision makers",
            ]
            strategy["key_stakeholders"] = ["CSM"]

        return strategy

    def _format_cross_sell_report(
        self,
        profile_analysis: dict[str, Any],
        cross_sell_opportunities: list[dict[str, Any]],
        add_on_opportunities: list[dict[str, Any]],
        readiness_scores: list[dict[str, Any]],
        revenue_potential: dict[str, Any],
        strategy: dict[str, Any],
    ) -> str:
        """Format cross-sell analysis report."""
        report = f"""**???? Cross-Sell Opportunity Analysis**

**Customer Profile:**
- Industry: {profile_analysis["industry"].title()}
- Company Size: {profile_analysis["company_size"].title()}
- Account Maturity: {profile_analysis["account_maturity"].title()} ({profile_analysis["months_as_customer"]} months)
- Health Status: {profile_analysis["health_status"].title()} ({profile_analysis["health_score"]}/100)
- Current Products: {len(profile_analysis["current_products"])}

**Usage Signals for Cross-Sell:**
"""

        if profile_analysis["usage_signals"]:
            for signal in profile_analysis["usage_signals"]:
                report += f"- {signal.replace('_', ' ').title()}\n"
        else:
            report += "- No strong cross-sell signals detected\n"

        # Product cross-sell opportunities
        if cross_sell_opportunities:
            report += (
                f"\n**???? Product Cross-Sell Opportunities ({len(cross_sell_opportunities)}):**\n"
            )
            for i, opp in enumerate(cross_sell_opportunities[:3], 1):
                industry_icon = "???" if opp["industry_fit"] else "??????"
                report += f"\n{i}. **{opp['product'].replace('_', ' ').title()}** {industry_icon}\n"
                report += f"   - Category: {opp['category'].title()}\n"
                report += f"   - Typical ARR: ${opp['typical_arr']:,}\n"
                report += f"   - Fit Score: {opp['fit_score']}/100\n"
                report += f"   - Complements: {opp['complements'].replace('_', ' ').title()}\n"
                report += f"   - Business Case: {opp['business_case']}\n"

        # Add-on opportunities
        if add_on_opportunities:
            report += f"\n**???? Add-On Opportunities ({len(add_on_opportunities)}):**\n"
            for i, opp in enumerate(add_on_opportunities[:3], 1):
                report += f"\n{i}. **{opp['add_on'].replace('_', ' ').title()}**\n"
                report += f"   - Value: ${opp['value']:,}\n"
                report += f"   - Fit Score: {opp['fit_score']}/100\n"
                report += f"   - Business Case: {opp['business_case']}\n"

        # Revenue potential
        report += "\n**???? Revenue Potential:**\n"
        report += f"- Total Cross-Sell Potential: ${revenue_potential['total_potential']:,}\n"
        report += f"- Product Opportunities: ${revenue_potential['product_potential']:,}\n"
        report += f"- Add-On Opportunities: ${revenue_potential['add_on_potential']:,}\n"
        report += f"- Current ARR: ${revenue_potential['current_arr']:,}\n"
        report += f"- Potential Expansion: {revenue_potential['expansion_percentage']:.1f}%\n"

        # Top readiness recommendations
        if readiness_scores:
            report += "\n**???? Top Recommendations (by Readiness):**\n"
            for i, opp in enumerate(readiness_scores[:3], 1):
                readiness_icon = (
                    "????"
                    if opp["readiness_score"] >= 75
                    else "????"
                    if opp["readiness_score"] >= 50
                    else "????"
                )
                report += f"\n{i}. **{opp['name'].replace('_', ' ').title()}** {readiness_icon}\n"
                report += f"   - Type: {opp['opportunity_type'].title()}\n"
                report += f"   - Readiness Score: {opp['readiness_score']}/100\n"
                report += f"   - Potential Value: ${opp['potential_value']:,}\n"

        # Strategy
        if strategy.get("primary_focus"):
            report += "\n**???? Recommended Strategy:**\n"
            report += f"**Primary Focus:** {strategy['primary_focus'].replace('_', ' ').title()}\n"
            report += f"**Approach:** {strategy['approach']}\n"
            report += f"**Timeline:** {strategy['timeline']}\n\n"
            report += "**Tactics:**\n"
            for tactic in strategy["tactics"][:4]:
                report += f"- {tactic}\n"
            report += f"\n**Key Stakeholders:** {', '.join(strategy['key_stakeholders'])}\n"
        else:
            report += "\n**???? Recommendation:** Continue nurturing account - no immediate cross-sell opportunities\n"

        return report


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Cross-Sell Agent (TASK-2053)")
        print("=" * 70)

        agent = CrossSellAgent()

        # Test 1: High cross-sell potential
        print("\n\nTest 1: High Cross-Sell Potential")
        print("-" * 70)

        state1 = create_initial_state(
            "Identify cross-sell opportunities",
            context={
                "customer_id": "cust_high_potential",
                "customer_metadata": {
                    "industry": "technology",
                    "company_size": "large",
                    "health_score": 85,
                    "account_tier": "strategic",
                    "executive_sponsor": True,
                },
            },
        )
        state1["entities"] = {
            "usage_data": {
                "api_usage_high": True,
                "data_volume_growing": True,
                "security_inquiries": 5,
                "integration_attempts": 8,
                "support_tickets_last_30d": 12,
                "advanced_features_used": 7,
                "api_calls": 150000,
                "custom_workflows": 15,
            },
            "contract_data": {
                "current_products": ["analytics_platform"],
                "contract_value": 75000,
                "months_as_customer": 18,
                "tier": "enterprise",
            },
        }

        result1 = await agent.process(state1)

        print(f"Opportunities Found: {result1['cross_sell_opportunities_count']}")
        print(f"Revenue Potential: ${result1['cross_sell_revenue_potential']:,}")
        print(f"Top Readiness Score: {result1['top_cross_sell_readiness']}/100")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Limited cross-sell potential
        print("\n\n" + "=" * 70)
        print("Test 2: Limited Cross-Sell Potential")
        print("-" * 70)

        state2 = create_initial_state(
            "Check cross-sell options",
            context={
                "customer_id": "cust_limited",
                "customer_metadata": {
                    "industry": "retail",
                    "company_size": "small",
                    "health_score": 55,
                },
            },
        )
        state2["entities"] = {
            "usage_data": {
                "api_usage_high": False,
                "support_tickets_last_30d": 2,
                "advanced_features_used": 1,
            },
            "contract_data": {
                "current_products": ["collaboration_suite"],
                "contract_value": 18000,
                "months_as_customer": 3,
                "tier": "basic",
            },
        }

        result2 = await agent.process(state2)

        print(f"Opportunities Found: {result2['cross_sell_opportunities_count']}")
        print(f"Revenue Potential: ${result2['cross_sell_revenue_potential']:,}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
