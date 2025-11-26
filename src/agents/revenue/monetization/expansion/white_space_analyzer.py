"""
White Space Analyzer Agent - TASK-3035

Analyzes untapped potential within accounts to identify expansion white space.
Maps product fit across company divisions and identifies growth opportunities.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("white_space_analyzer", tier="revenue", category="monetization")
class WhiteSpaceAnalyzer(BaseAgent):
    """
    White Space Analyzer Agent - Identifies untapped account potential.

    Handles:
    - Map company organizational structure
    - Identify departments not using product
    - Analyze product-market fit by division
    - Calculate white space opportunity size
    - Prioritize white space targets
    - Generate white space penetration strategies
    - Track white space conversion
    - Measure account penetration rates
    """

    # White space opportunity categories
    WHITE_SPACE_CATEGORIES = {
        "departmental": {
            "description": "Departments not currently using product",
            "opportunity_score_weight": 0.35,
            "typical_conversion_rate": 0.60,
        },
        "functional": {
            "description": "Functions/roles that would benefit",
            "opportunity_score_weight": 0.25,
            "typical_conversion_rate": 0.50,
        },
        "geographic": {
            "description": "Locations/regions not deployed",
            "opportunity_score_weight": 0.20,
            "typical_conversion_rate": 0.55,
        },
        "use_case": {
            "description": "Additional workflows and use cases",
            "opportunity_score_weight": 0.20,
            "typical_conversion_rate": 0.45,
        },
    }

    # Department product-fit scoring
    DEPARTMENT_FIT_MATRIX = {
        "customer_support": {"fit_score": 0.95, "avg_seats": 15, "avg_arr_per_seat": 40},
        "sales": {"fit_score": 0.90, "avg_seats": 20, "avg_arr_per_seat": 50},
        "marketing": {"fit_score": 0.85, "avg_seats": 10, "avg_arr_per_seat": 45},
        "product": {"fit_score": 0.80, "avg_seats": 12, "avg_arr_per_seat": 50},
        "engineering": {"fit_score": 0.75, "avg_seats": 25, "avg_arr_per_seat": 40},
        "operations": {"fit_score": 0.85, "avg_seats": 15, "avg_arr_per_seat": 40},
        "hr": {"fit_score": 0.70, "avg_seats": 8, "avg_arr_per_seat": 35},
        "finance": {"fit_score": 0.65, "avg_seats": 10, "avg_arr_per_seat": 45},
        "legal": {"fit_score": 0.60, "avg_seats": 5, "avg_arr_per_seat": 50},
    }

    # Penetration maturity levels
    PENETRATION_LEVELS = {
        "land": (0, 15),  # 0-15% penetration
        "emerging": (15, 40),  # 15-40% penetration
        "growing": (40, 75),  # 40-75% penetration
        "mature": (75, 100),  # 75-100% penetration
    }

    def __init__(self):
        config = AgentConfig(
            name="white_space_analyzer",
            type=AgentType.SPECIALIST,
            # Sonnet for strategic analysis
            temperature=0.3,
            max_tokens=700,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="monetization",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Analyze white space and identify expansion opportunities.

        Args:
            state: Current agent state with account structure data

        Returns:
            Updated state with white space analysis
        """
        self.logger.info("white_space_analyzer_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Map current coverage
        coverage_map = self._map_current_coverage(customer_metadata)

        # Identify white space
        white_space = self._identify_white_space(coverage_map, customer_metadata)

        # Score white space opportunities
        scored_opportunities = self._score_opportunities(white_space, customer_metadata)

        # Prioritize targets
        prioritized_targets = self._prioritize_targets(scored_opportunities)

        # Calculate white space value
        white_space_value = self._calculate_white_space_value(
            prioritized_targets, customer_metadata
        )

        # Generate penetration strategy
        penetration_strategy = self._generate_penetration_strategy(
            prioritized_targets, coverage_map, customer_metadata
        )

        # Build account map
        account_map = self._build_account_map(coverage_map, white_space, customer_metadata)

        # Search KB for white space resources
        kb_results = await self.search_knowledge_base(
            "white space analysis account mapping expansion", category="monetization", limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_analysis_response(
            message,
            coverage_map,
            white_space,
            prioritized_targets,
            white_space_value,
            penetration_strategy,
            account_map,
            kb_results,
            customer_metadata,
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.86
        state["coverage_map"] = coverage_map
        state["white_space"] = white_space
        state["prioritized_targets"] = prioritized_targets
        state["white_space_value"] = white_space_value
        state["penetration_strategy"] = penetration_strategy
        state["account_map"] = account_map
        state["status"] = "resolved"

        self.logger.info(
            "white_space_analyzer_completed",
            white_space_opportunities=len(prioritized_targets),
            total_white_space_value=white_space_value.get("total_white_space_arr", 0),
        )

        return state

    def _map_current_coverage(self, customer_metadata: dict) -> dict[str, Any]:
        """Map current product coverage across account"""
        current_departments = customer_metadata.get("departments_using_product", [])
        current_locations = customer_metadata.get("locations_deployed", [])
        current_use_cases = customer_metadata.get("active_use_cases", [])
        current_users = customer_metadata.get("active_users", 0)
        total_employees = customer_metadata.get("company_size", 0)

        # Calculate penetration metrics
        total_departments = customer_metadata.get("total_departments", 1)
        total_locations = customer_metadata.get("total_locations", 1)

        dept_penetration = (
            (len(current_departments) / total_departments * 100) if total_departments > 0 else 0
        )
        user_penetration = (current_users / total_employees * 100) if total_employees > 0 else 0
        location_penetration = (
            (len(current_locations) / total_locations * 100) if total_locations > 0 else 0
        )

        return {
            "departments_covered": current_departments,
            "total_departments": total_departments,
            "department_penetration": round(dept_penetration, 2),
            "locations_covered": current_locations,
            "total_locations": total_locations,
            "location_penetration": round(location_penetration, 2),
            "users_covered": current_users,
            "total_users": total_employees,
            "user_penetration": round(user_penetration, 2),
            "use_cases_active": current_use_cases,
            "penetration_level": self._determine_penetration_level(user_penetration),
        }

    def _determine_penetration_level(self, penetration: float) -> str:
        """Determine penetration maturity level"""
        for level, (min_p, max_p) in self.PENETRATION_LEVELS.items():
            if min_p <= penetration < max_p:
                return level
        return "mature"

    def _identify_white_space(
        self, coverage_map: dict, customer_metadata: dict
    ) -> dict[str, list[dict[str, Any]]]:
        """Identify white space across different dimensions"""
        white_space = {"departmental": [], "geographic": [], "functional": [], "use_case": []}

        # Departmental white space
        covered_depts = [d.lower() for d in coverage_map["departments_covered"]]
        for dept, fit_data in self.DEPARTMENT_FIT_MATRIX.items():
            if dept not in covered_depts:
                white_space["departmental"].append(
                    {
                        "department": dept,
                        "fit_score": fit_data["fit_score"],
                        "estimated_seats": fit_data["avg_seats"],
                        "estimated_arr_per_seat": fit_data["avg_arr_per_seat"],
                    }
                )

        # Geographic white space
        total_locations = coverage_map["total_locations"]
        covered_locations = len(coverage_map["locations_covered"])
        if covered_locations < total_locations:
            white_space["geographic"].append(
                {
                    "uncovered_locations": total_locations - covered_locations,
                    "opportunity": "Multi-location rollout",
                }
            )

        # Use case white space
        potential_use_cases = [
            "Customer Support Management",
            "Sales Pipeline Tracking",
            "Project Management",
            "Knowledge Base",
            "Reporting & Analytics",
        ]
        active_use_cases = coverage_map["use_cases_active"]
        for use_case in potential_use_cases:
            if use_case not in active_use_cases:
                white_space["use_case"].append(
                    {"use_case": use_case, "opportunity": f"Expand to {use_case}"}
                )

        return white_space

    def _score_opportunities(
        self, white_space: dict, customer_metadata: dict
    ) -> list[dict[str, Any]]:
        """Score each white space opportunity"""
        scored = []

        # Score departmental opportunities
        for dept_opp in white_space["departmental"]:
            category = "departmental"
            base_score = dept_opp["fit_score"] * 100

            # Adjust for company context
            company_size = customer_metadata.get("company_size", 0)
            if company_size >= 500:
                context_multiplier = 1.2
            elif company_size >= 100:
                context_multiplier = 1.1
            else:
                context_multiplier = 1.0

            final_score = base_score * context_multiplier

            scored.append(
                {
                    "category": category,
                    "target": dept_opp["department"],
                    "opportunity_score": round(final_score, 2),
                    "estimated_arr": round(
                        dept_opp["estimated_seats"] * dept_opp["estimated_arr_per_seat"] * 12, 2
                    ),
                    "estimated_seats": dept_opp["estimated_seats"],
                    "confidence": self.WHITE_SPACE_CATEGORIES[category]["typical_conversion_rate"],
                }
            )

        # Score geographic opportunities
        for geo_opp in white_space["geographic"]:
            category = "geographic"
            current_arr = customer_metadata.get("current_arr", 0)
            locations_multiplier = geo_opp["uncovered_locations"]

            scored.append(
                {
                    "category": category,
                    "target": f"{geo_opp['uncovered_locations']} locations",
                    "opportunity_score": 70.0,  # Base score for geographic
                    "estimated_arr": round(current_arr * locations_multiplier * 0.8, 2),
                    "confidence": self.WHITE_SPACE_CATEGORIES[category]["typical_conversion_rate"],
                }
            )

        # Score use case opportunities
        for uc_opp in white_space["use_case"]:
            category = "use_case"
            current_arr = customer_metadata.get("current_arr", 0)

            scored.append(
                {
                    "category": category,
                    "target": uc_opp["use_case"],
                    "opportunity_score": 60.0,  # Base score for use cases
                    "estimated_arr": round(current_arr * 0.3, 2),  # 30% of current ARR
                    "confidence": self.WHITE_SPACE_CATEGORIES[category]["typical_conversion_rate"],
                }
            )

        return scored

    def _prioritize_targets(self, opportunities: list[dict]) -> list[dict[str, Any]]:
        """Prioritize white space targets"""
        # Calculate priority score
        for opp in opportunities:
            priority_score = (
                opp["opportunity_score"] * 0.5
                + (opp["estimated_arr"] / 1000) * 0.3  # ARR impact
                + opp["confidence"] * 100 * 0.2  # Confidence
            )
            opp["priority_score"] = round(priority_score, 2)

        # Sort by priority score
        return sorted(opportunities, key=lambda x: x["priority_score"], reverse=True)

    def _calculate_white_space_value(
        self, targets: list[dict], customer_metadata: dict
    ) -> dict[str, Any]:
        """Calculate total white space opportunity value"""
        total_arr = 0
        weighted_arr = 0
        by_category = {}

        for target in targets:
            arr = target["estimated_arr"]
            weighted = arr * target["confidence"]

            total_arr += arr
            weighted_arr += weighted

            category = target["category"]
            if category not in by_category:
                by_category[category] = {"count": 0, "total_arr": 0, "weighted_arr": 0}

            by_category[category]["count"] += 1
            by_category[category]["total_arr"] += arr
            by_category[category]["weighted_arr"] += weighted

        current_arr = customer_metadata.get("current_arr", 0)
        potential_total_arr = current_arr + weighted_arr

        return {
            "current_arr": current_arr,
            "total_white_space_arr": round(total_arr, 2),
            "weighted_white_space_arr": round(weighted_arr, 2),
            "potential_total_arr": round(potential_total_arr, 2),
            "expansion_multiple": round(potential_total_arr / current_arr, 2)
            if current_arr > 0
            else 0,
            "by_category": by_category,
            "top_opportunities_count": len(targets),
        }

    def _generate_penetration_strategy(
        self, targets: list[dict], coverage_map: dict, customer_metadata: dict
    ) -> dict[str, Any]:
        """Generate strategy to penetrate white space"""
        # Get top 3 targets
        top_targets = targets[:3]

        strategies = []
        for target in top_targets:
            if target["category"] == "departmental":
                strategy = {
                    "target": target["target"],
                    "approach": "Department-specific pilot program",
                    "timeline": "6-8 weeks",
                    "tactics": [
                        f"Identify {target['target']} pain points",
                        "Leverage adjacent department success stories",
                        "Offer pilot with 5-10 users",
                        "Demonstrate ROI within 30 days",
                    ],
                }
            elif target["category"] == "geographic":
                strategy = {
                    "target": target["target"],
                    "approach": "Regional rollout playbook",
                    "timeline": "8-12 weeks",
                    "tactics": [
                        "Replicate successful location setup",
                        "Train local champions",
                        "Provide regional support",
                        "Phase rollout by location",
                    ],
                }
            else:
                strategy = {
                    "target": target["target"],
                    "approach": "Use case expansion",
                    "timeline": "4-6 weeks",
                    "tactics": [
                        "Demo additional capabilities",
                        "Provide use case templates",
                        "Train on new workflows",
                        "Show quick wins",
                    ],
                }

            strategies.append(strategy)

        return {
            "penetration_level": coverage_map["penetration_level"],
            "strategies": strategies,
            "success_metrics": [
                "Increase department penetration by 25%",
                "Add 50+ new users in 90 days",
                f"Grow ARR by ${sum(t['estimated_arr'] for t in top_targets[:3]):,.0f}",
            ],
        }

    def _build_account_map(
        self, coverage_map: dict, white_space: dict, customer_metadata: dict
    ) -> dict[str, Any]:
        """Build visual account map"""
        return {
            "company": customer_metadata.get("company", "Customer"),
            "total_addressable_users": customer_metadata.get("company_size", 0),
            "current_users": coverage_map["users_covered"],
            "penetration": coverage_map["user_penetration"],
            "covered_areas": {
                "departments": coverage_map["departments_covered"],
                "locations": coverage_map["locations_covered"],
                "use_cases": coverage_map["use_cases_active"],
            },
            "white_space_areas": {
                "departments": len(white_space["departmental"]),
                "locations": len(white_space["geographic"]),
                "use_cases": len(white_space["use_case"]),
            },
        }

    async def _generate_analysis_response(
        self,
        message: str,
        coverage_map: dict,
        white_space: dict,
        targets: list[dict],
        white_space_value: dict,
        strategy: dict,
        account_map: dict,
        kb_results: list[dict],
        customer_metadata: dict,
    ) -> str:
        """Generate white space analysis response"""

        # Build coverage context
        coverage_context = f"""
Current Coverage:
- Department Penetration: {coverage_map["department_penetration"]:.0f}%
- User Penetration: {coverage_map["user_penetration"]:.0f}%
- Location Penetration: {coverage_map["location_penetration"]:.0f}%
- Maturity Level: {coverage_map["penetration_level"]}
"""

        # Build white space context
        white_space_context = f"""
White Space Opportunity:
- Current ARR: ${white_space_value["current_arr"]:,.0f}
- White Space Potential: ${white_space_value["weighted_white_space_arr"]:,.0f}
- Potential Total ARR: ${white_space_value["potential_total_arr"]:,.0f}
- Expansion Multiple: {white_space_value["expansion_multiple"]:.1f}x
- Top Opportunities: {len(targets[:5])}
"""

        # Build top targets context
        targets_context = ""
        if targets:
            targets_context = "\n\nTop White Space Targets:\n"
            for target in targets[:3]:
                targets_context += f"- {target['target']}: ${target['estimated_arr']:,.0f} potential ({target['confidence'] * 100:.0f}% confidence)\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nWhite Space Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a White Space Analyzer identifying untapped potential within accounts.

Customer: {customer_metadata.get("company", "Customer")}
{coverage_context}
{white_space_context}

Your response should:
1. Show comprehensive account coverage map
2. Highlight white space opportunities
3. Prioritize highest-value targets
4. Explain why each target is a good fit
5. Present phased penetration strategy
6. Quantify expansion potential
7. Provide specific tactics for each target
8. Show path from current to full potential
9. Make expansion feel achievable
10. Provide clear next steps

Tone: Strategic, data-driven, opportunity-focused"""

        user_prompt = f"""Customer message: {message}

{targets_context}

Penetration Strategy:
{chr(10).join(f"- {s['target']}: {s['approach']}" for s in strategy["strategies"])}

Success Metrics:
{chr(10).join(f"- {metric}" for metric in strategy["success_metrics"])}

{kb_context}

Generate a comprehensive white space analysis."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[],  # White space analysis uses account data
        )
        return response
