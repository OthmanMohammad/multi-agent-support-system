"""
Department Expansion Agent - TASK-2054

Identifies opportunities to expand product adoption to new departments, teams,
and business units within the existing customer organization.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("department_expansion", tier="revenue", category="customer_success")
class DepartmentExpansionAgent(BaseAgent):
    """
    Department Expansion Agent.

    Identifies departmental expansion by:
    - Mapping current product usage by department
    - Identifying untapped departments and business units
    - Analyzing use case fit for other departments
    - Calculating land-and-expand potential
    - Scoring expansion readiness per department
    - Generating multi-department expansion strategies
    """

    # Department categories and typical use cases
    DEPARTMENT_USE_CASES = {
        "sales": {
            "use_cases": ["pipeline_tracking", "forecasting", "customer_data", "reporting"],
            "typical_seat_count": 25,
            "avg_arr_per_seat": 1200,
            "adoption_likelihood": "high",
        },
        "marketing": {
            "use_cases": [
                "campaign_analytics",
                "customer_segmentation",
                "reporting",
                "collaboration",
            ],
            "typical_seat_count": 15,
            "avg_arr_per_seat": 1000,
            "adoption_likelihood": "high",
        },
        "customer_support": {
            "use_cases": ["ticket_tracking", "customer_data", "reporting", "knowledge_base"],
            "typical_seat_count": 30,
            "avg_arr_per_seat": 800,
            "adoption_likelihood": "medium",
        },
        "product": {
            "use_cases": ["analytics", "user_feedback", "roadmap_planning", "collaboration"],
            "typical_seat_count": 20,
            "avg_arr_per_seat": 1500,
            "adoption_likelihood": "high",
        },
        "engineering": {
            "use_cases": ["api_access", "automation", "monitoring", "collaboration"],
            "typical_seat_count": 40,
            "avg_arr_per_seat": 1800,
            "adoption_likelihood": "medium",
        },
        "finance": {
            "use_cases": ["reporting", "analytics", "forecasting", "compliance"],
            "typical_seat_count": 12,
            "avg_arr_per_seat": 1400,
            "adoption_likelihood": "medium",
        },
        "operations": {
            "use_cases": ["process_automation", "reporting", "workflow_management", "analytics"],
            "typical_seat_count": 20,
            "avg_arr_per_seat": 1100,
            "adoption_likelihood": "medium",
        },
        "hr": {
            "use_cases": ["employee_data", "reporting", "workflow_automation", "collaboration"],
            "typical_seat_count": 10,
            "avg_arr_per_seat": 900,
            "adoption_likelihood": "low",
        },
        "executive": {
            "use_cases": ["executive_dashboards", "strategic_analytics", "reporting"],
            "typical_seat_count": 5,
            "avg_arr_per_seat": 2000,
            "adoption_likelihood": "low",
        },
    }

    # Expansion signals
    EXPANSION_SIGNALS = {
        "cross_department_sharing": {"weight": 25, "indicator": "Users sharing across departments"},
        "department_inquiries": {"weight": 20, "indicator": "Support tickets from new departments"},
        "champion_advocacy": {"weight": 20, "indicator": "Power users recommending to peers"},
        "company_growth": {"weight": 15, "indicator": "Organization expanding headcount"},
        "budget_approval": {"weight": 10, "indicator": "Budget allocated for expansion"},
        "pilot_interest": {"weight": 10, "indicator": "Other teams requesting trials"},
    }

    def __init__(self):
        config = AgentConfig(
            name="department_expansion",
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
        Identify and analyze department expansion opportunities.

        Args:
            state: Current agent state with organizational data

        Returns:
            Updated state with department expansion analysis
        """
        self.logger.info("department_expansion_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        organization_data = state.get("entities", {}).get("organization_data", {})
        usage_data = state.get("entities", {}).get("usage_data", {})
        contract_data = state.get("entities", {}).get("contract_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "department_expansion_details",
            customer_id=customer_id,
            departments_using=len(usage_data.get("departments_using", [])),
            total_departments=organization_data.get("total_departments", 0),
        )

        # Analyze current department coverage
        coverage_analysis = self._analyze_department_coverage(organization_data, usage_data)

        # Identify untapped departments
        untapped_departments = self._identify_untapped_departments(
            coverage_analysis, organization_data, usage_data
        )

        # Score expansion potential per department
        department_scores = self._score_department_expansion(
            untapped_departments, organization_data, usage_data, customer_metadata
        )

        # Calculate expansion revenue potential
        revenue_potential = self._calculate_department_revenue(
            department_scores, contract_data, organization_data
        )

        # Generate expansion strategy
        expansion_strategy = self._generate_expansion_strategy(
            department_scores, coverage_analysis, customer_metadata
        )

        # Format response
        response = self._format_expansion_report(
            coverage_analysis, department_scores, revenue_potential, expansion_strategy
        )

        state["agent_response"] = response
        state["department_coverage_pct"] = coverage_analysis["coverage_percentage"]
        state["untapped_departments"] = len(department_scores)
        state["department_expansion_revenue"] = revenue_potential["total_potential"]
        state["top_expansion_department"] = (
            department_scores[0]["department"] if department_scores else None
        )
        state["expansion_analysis"] = coverage_analysis
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "department_expansion_completed",
            customer_id=customer_id,
            coverage_pct=coverage_analysis["coverage_percentage"],
            untapped_count=len(department_scores),
            revenue_potential=revenue_potential["total_potential"],
        )

        return state

    def _analyze_department_coverage(
        self, organization_data: dict[str, Any], usage_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze current department coverage.

        Args:
            organization_data: Organization structure and departments
            usage_data: Current usage by department

        Returns:
            Department coverage analysis
        """
        total_departments = organization_data.get("total_departments", 0)
        departments_in_org = set(organization_data.get("departments", []))
        departments_using = set(usage_data.get("departments_using", []))

        # Calculate coverage
        if total_departments > 0:
            coverage_pct = (len(departments_using) / total_departments) * 100
        else:
            coverage_pct = 0

        # Analyze usage by department
        department_usage = usage_data.get("usage_by_department", {})
        active_departments = []
        underutilized_departments = []

        for dept in departments_using:
            dept_data = department_usage.get(dept, {})
            users = dept_data.get("users", 0)
            usage_rate = dept_data.get("usage_rate", 0)

            dept_info = {
                "department": dept,
                "users": users,
                "usage_rate": usage_rate,
                "status": "active" if usage_rate >= 70 else "underutilized",
            }

            if usage_rate >= 70:
                active_departments.append(dept_info)
            else:
                underutilized_departments.append(dept_info)

        # Identify expansion signals
        expansion_signals = self._detect_expansion_signals(usage_data, organization_data)

        return {
            "total_departments": total_departments,
            "departments_using": len(departments_using),
            "departments_not_using": total_departments - len(departments_using),
            "coverage_percentage": round(coverage_pct, 1),
            "active_departments": active_departments,
            "underutilized_departments": underutilized_departments,
            "departments_in_org": list(departments_in_org),
            "expansion_signals": expansion_signals,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    def _detect_expansion_signals(
        self, usage_data: dict[str, Any], organization_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Detect signals indicating readiness for department expansion."""
        signals = {}
        total_signal_score = 0

        # Cross-department sharing
        if usage_data.get("cross_department_shares", 0) > 5:
            signals["cross_department_sharing"] = True
            total_signal_score += self.EXPANSION_SIGNALS["cross_department_sharing"]["weight"]

        # Department inquiries
        if usage_data.get("new_department_inquiries", 0) > 3:
            signals["department_inquiries"] = True
            total_signal_score += self.EXPANSION_SIGNALS["department_inquiries"]["weight"]

        # Champion advocacy
        if usage_data.get("internal_referrals", 0) > 2:
            signals["champion_advocacy"] = True
            total_signal_score += self.EXPANSION_SIGNALS["champion_advocacy"]["weight"]

        # Company growth
        if organization_data.get("headcount_growth_pct", 0) > 20:
            signals["company_growth"] = True
            total_signal_score += self.EXPANSION_SIGNALS["company_growth"]["weight"]

        # Budget approval
        if organization_data.get("expansion_budget_approved", False):
            signals["budget_approval"] = True
            total_signal_score += self.EXPANSION_SIGNALS["budget_approval"]["weight"]

        # Pilot interest
        if usage_data.get("pilot_requests", 0) > 0:
            signals["pilot_interest"] = True
            total_signal_score += self.EXPANSION_SIGNALS["pilot_interest"]["weight"]

        return {
            "signals_detected": list(signals.keys()),
            "signal_count": len(signals),
            "total_signal_score": total_signal_score,
        }

    def _identify_untapped_departments(
        self,
        coverage_analysis: dict[str, Any],
        organization_data: dict[str, Any],
        usage_data: dict[str, Any],
    ) -> list[str]:
        """Identify departments not currently using the product."""
        departments_in_org = set(coverage_analysis["departments_in_org"])
        departments_using = {dept["department"] for dept in coverage_analysis["active_departments"]}
        departments_using.update(
            dept["department"] for dept in coverage_analysis["underutilized_departments"]
        )

        untapped = list(departments_in_org - departments_using)

        # Add any standard departments not in org data but in our catalog
        for dept in self.DEPARTMENT_USE_CASES:
            if dept not in departments_in_org and dept not in departments_using:
                # Only add if company size suggests they likely have this department
                company_size = organization_data.get("company_size", "medium")
                if company_size in ["large", "enterprise"] or dept in [
                    "sales",
                    "marketing",
                    "customer_support",
                ]:
                    untapped.append(dept)

        return untapped

    def _score_department_expansion(
        self,
        untapped_departments: list[str],
        organization_data: dict[str, Any],
        usage_data: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Score expansion potential for each untapped department.

        Args:
            untapped_departments: Departments not using product
            organization_data: Organization data
            usage_data: Usage patterns
            customer_metadata: Customer profile

        Returns:
            Scored department expansion opportunities
        """
        scored_departments = []

        for department in untapped_departments:
            if department not in self.DEPARTMENT_USE_CASES:
                continue

            dept_config = self.DEPARTMENT_USE_CASES[department]

            # Calculate expansion score (0-100)
            score = self._calculate_department_score(
                department, dept_config, organization_data, usage_data, customer_metadata
            )

            # Calculate potential revenue
            estimated_seats = self._estimate_department_seats(
                department, dept_config, organization_data
            )

            potential_arr = estimated_seats * dept_config["avg_arr_per_seat"]

            # Identify use case alignment
            use_case_fit = self._assess_use_case_fit(department, dept_config, usage_data)

            scored_departments.append(
                {
                    "department": department,
                    "expansion_score": score,
                    "estimated_seats": estimated_seats,
                    "potential_arr": potential_arr,
                    "adoption_likelihood": dept_config["adoption_likelihood"],
                    "use_cases": dept_config["use_cases"],
                    "use_case_fit": use_case_fit,
                    "expansion_rationale": self._build_expansion_rationale(
                        department, use_case_fit, organization_data
                    ),
                }
            )

        # Sort by expansion score and potential
        scored_departments.sort(
            key=lambda x: (x["expansion_score"], x["potential_arr"]), reverse=True
        )

        return scored_departments[:6]

    def _calculate_department_score(
        self,
        department: str,
        dept_config: dict[str, Any],
        organization_data: dict[str, Any],
        usage_data: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> int:
        """Calculate expansion score for a department (0-100)."""
        score = 0

        # Adoption likelihood (0-30 points)
        likelihood_scores = {"high": 30, "medium": 20, "low": 10}
        score += likelihood_scores.get(dept_config["adoption_likelihood"], 15)

        # Expansion signals (0-25 points)
        signal_score = usage_data.get("expansion_signals", {}).get("total_signal_score", 0)
        score += min(signal_score, 25)

        # Customer health (0-20 points)
        health_score = customer_metadata.get("health_score", 50)
        score += (health_score / 100) * 20

        # Use case alignment (0-15 points)
        current_features = set(usage_data.get("features_used", []))
        dept_use_cases = set(dept_config["use_cases"])

        # Check overlap with features
        alignment_score = 0
        if any(uc in str(current_features).lower() for uc in dept_use_cases):
            alignment_score = 15
        elif len(dept_use_cases) <= 3:
            alignment_score = 10
        else:
            alignment_score = 5

        score += alignment_score

        # Company size fit (0-10 points)
        company_size = organization_data.get("company_size", "medium")
        size_scores = {"enterprise": 10, "large": 8, "medium": 6, "small": 4}
        score += size_scores.get(company_size, 5)

        return min(int(score), 100)

    def _estimate_department_seats(
        self, department: str, dept_config: dict[str, Any], organization_data: dict[str, Any]
    ) -> int:
        """Estimate seat count for a department."""
        # Start with typical seat count
        base_seats = dept_config["typical_seat_count"]

        # Adjust based on company size
        company_size = organization_data.get("company_size", "medium")
        size_multipliers = {"enterprise": 2.0, "large": 1.5, "medium": 1.0, "small": 0.5}
        multiplier = size_multipliers.get(company_size, 1.0)

        estimated = int(base_seats * multiplier)

        # Check if we have actual department size data
        dept_sizes = organization_data.get("department_sizes", {})
        if department in dept_sizes:
            actual_dept_size = dept_sizes[department]
            # Use 60% of department size as typical adoption rate
            estimated = max(int(actual_dept_size * 0.6), estimated)

        return estimated

    def _assess_use_case_fit(
        self, department: str, dept_config: dict[str, Any], usage_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess how well product features fit department use cases."""
        use_cases = dept_config["use_cases"]
        current_features = usage_data.get("features_used", [])

        matched_use_cases = []
        for use_case in use_cases:
            # Simple matching - in production would use more sophisticated matching
            if any(use_case.replace("_", " ") in feature.lower() for feature in current_features):
                matched_use_cases.append(use_case)

        fit_percentage = (len(matched_use_cases) / len(use_cases) * 100) if use_cases else 0

        return {
            "matched_use_cases": matched_use_cases,
            "total_use_cases": len(use_cases),
            "fit_percentage": round(fit_percentage, 1),
            "fit_level": "high"
            if fit_percentage >= 75
            else "medium"
            if fit_percentage >= 40
            else "low",
        }

    def _build_expansion_rationale(
        self, department: str, use_case_fit: dict[str, Any], organization_data: dict[str, Any]
    ) -> str:
        """Build rationale for department expansion."""
        dept_name = department.replace("_", " ").title()

        if use_case_fit["fit_percentage"] >= 75:
            return f"{dept_name} team can leverage existing {', '.join(use_case_fit['matched_use_cases'][:2])} capabilities"
        elif use_case_fit["fit_percentage"] >= 40:
            return f"{dept_name} has complementary needs - moderate feature alignment"
        else:
            return f"{dept_name} expansion would require minimal customization"

    def _calculate_department_revenue(
        self,
        department_scores: list[dict[str, Any]],
        contract_data: dict[str, Any],
        organization_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate total revenue potential from department expansion."""
        total_potential = sum(dept["potential_arr"] for dept in department_scores)
        total_seats = sum(dept["estimated_seats"] for dept in department_scores)

        current_arr = contract_data.get("contract_value", 0)
        expansion_pct = total_potential / current_arr * 100 if current_arr > 0 else 0

        # Calculate weighted potential (by adoption likelihood)
        likelihood_weights = {"high": 0.7, "medium": 0.4, "low": 0.2}
        weighted_potential = sum(
            dept["potential_arr"] * likelihood_weights.get(dept["adoption_likelihood"], 0.4)
            for dept in department_scores
        )

        # Identify quick wins (high score, high likelihood)
        quick_wins = [
            dept
            for dept in department_scores
            if dept["expansion_score"] >= 70 and dept["adoption_likelihood"] == "high"
        ]

        return {
            "total_potential": total_potential,
            "weighted_potential": int(weighted_potential),
            "total_seats_potential": total_seats,
            "current_arr": current_arr,
            "expansion_percentage": round(expansion_pct, 1),
            "departments_identified": len(department_scores),
            "quick_wins": len(quick_wins),
            "quick_win_potential": sum(dept["potential_arr"] for dept in quick_wins),
        }

    def _generate_expansion_strategy(
        self,
        department_scores: list[dict[str, Any]],
        coverage_analysis: dict[str, Any],
        customer_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate department expansion strategy."""
        if not department_scores:
            return {
                "approach": "maintain",
                "timeline": "ongoing",
                "tactics": ["Continue supporting existing departments"],
            }

        top_department = department_scores[0]

        strategy = {
            "primary_target": top_department["department"],
            "expansion_score": top_department["expansion_score"],
            "approach": "",
            "timeline": "",
            "tactics": [],
            "success_metrics": [],
            "stakeholders": [],
        }

        # Define approach based on expansion signals and readiness
        signal_count = coverage_analysis["expansion_signals"]["signal_count"]

        if signal_count >= 3 and top_department["expansion_score"] >= 70:
            strategy["approach"] = "Aggressive multi-department expansion"
            strategy["timeline"] = "This quarter"
            strategy["tactics"] = [
                f"Launch pilot program in {top_department['department'].replace('_', ' ').title()}",
                "Identify and activate internal champions",
                "Create department-specific onboarding track",
                "Host cross-functional demo showcasing department use cases",
                "Offer expansion incentive pricing",
            ]
            strategy["stakeholders"] = [
                "CSM",
                "Account Executive",
                "Executive Sponsor",
                "Department Heads",
            ]
        elif signal_count >= 2 or top_department["expansion_score"] >= 60:
            strategy["approach"] = "Phased department rollout"
            strategy["timeline"] = "Next 2 quarters"
            strategy["tactics"] = [
                f"Start with {top_department['department'].replace('_', ' ').title()} as pilot",
                "Develop department-specific success stories",
                "Schedule lunch-and-learn sessions",
                "Create use case documentation for each department",
            ]
            strategy["stakeholders"] = ["CSM", "Account Executive", "Department Heads"]
        else:
            strategy["approach"] = "Gradual expansion nurture"
            strategy["timeline"] = "6-12 months"
            strategy["tactics"] = [
                "Build awareness through current users",
                "Share cross-department success stories",
                "Invite department leaders to user group",
                "Monitor for expansion signals",
            ]
            strategy["stakeholders"] = ["CSM"]

        # Success metrics
        strategy["success_metrics"] = [
            f"Expand to {min(3, len(department_scores))} new departments",
            f"Add {sum(dept['estimated_seats'] for dept in department_scores[:3])} seats",
            f"Achieve {strategy['timeline']} revenue target",
        ]

        return strategy

    def _format_expansion_report(
        self,
        coverage_analysis: dict[str, Any],
        department_scores: list[dict[str, Any]],
        revenue_potential: dict[str, Any],
        strategy: dict[str, Any],
    ) -> str:
        """Format department expansion report."""
        report = f"""**???? Department Expansion Analysis**

**Current Department Coverage:**
- Departments Using Product: {coverage_analysis["departments_using"]}/{coverage_analysis["total_departments"]}
- Coverage: {coverage_analysis["coverage_percentage"]:.1f}%
- Active Departments: {len(coverage_analysis["active_departments"])}
- Underutilized Departments: {len(coverage_analysis["underutilized_departments"])}

**Expansion Signals Detected ({coverage_analysis["expansion_signals"]["signal_count"]}):**
"""

        for signal in coverage_analysis["expansion_signals"]["signals_detected"]:
            signal_info = self.EXPANSION_SIGNALS.get(signal, {})
            report += f"- {signal_info.get('indicator', signal.replace('_', ' ').title())}\n"

        if not coverage_analysis["expansion_signals"]["signals_detected"]:
            report += "- No strong expansion signals detected\n"

        # Department opportunities
        if department_scores:
            report += f"\n**???? Department Expansion Opportunities ({len(department_scores)}):**\n"
            for i, dept in enumerate(department_scores[:4], 1):
                likelihood_icon = (
                    "????"
                    if dept["adoption_likelihood"] == "high"
                    else "????"
                    if dept["adoption_likelihood"] == "medium"
                    else "????"
                )
                report += (
                    f"\n{i}. **{dept['department'].replace('_', ' ').title()}** {likelihood_icon}\n"
                )
                report += f"   - Expansion Score: {dept['expansion_score']}/100\n"
                report += f"   - Estimated Seats: {dept['estimated_seats']}\n"
                report += f"   - Potential ARR: ${dept['potential_arr']:,}\n"
                report += f"   - Adoption Likelihood: {dept['adoption_likelihood'].title()}\n"
                report += f"   - Use Case Fit: {dept['use_case_fit']['fit_level'].title()} ({dept['use_case_fit']['fit_percentage']:.0f}%)\n"
                report += f"   - Rationale: {dept['expansion_rationale']}\n"

        # Revenue potential
        report += "\n**???? Revenue Potential:**\n"
        report += f"- Total Potential: ${revenue_potential['total_potential']:,}\n"
        report += f"- Weighted Potential: ${revenue_potential['weighted_potential']:,}\n"
        report += f"- Total Seats: {revenue_potential['total_seats_potential']}\n"
        report += f"- Current ARR: ${revenue_potential['current_arr']:,}\n"
        report += f"- Potential Expansion: {revenue_potential['expansion_percentage']:.1f}%\n"
        report += f"- Quick Win Departments: {revenue_potential['quick_wins']} (${revenue_potential['quick_win_potential']:,})\n"

        # Strategy
        if strategy.get("primary_target"):
            report += "\n**???? Expansion Strategy:**\n"
            report += (
                f"**Primary Target:** {strategy['primary_target'].replace('_', ' ').title()}\n"
            )
            report += f"**Approach:** {strategy['approach']}\n"
            report += f"**Timeline:** {strategy['timeline']}\n\n"
            report += "**Tactics:**\n"
            for tactic in strategy["tactics"][:5]:
                report += f"- {tactic}\n"

            report += "\n**Success Metrics:**\n"
            for metric in strategy["success_metrics"]:
                report += f"- {metric}\n"

            report += f"\n**Key Stakeholders:** {', '.join(strategy['stakeholders'])}\n"
        else:
            report += (
                "\n**???? Recommendation:** Focus on deepening adoption in current departments\n"
            )

        return report


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Department Expansion Agent (TASK-2054)")
        print("=" * 70)

        agent = DepartmentExpansionAgent()

        # Test 1: High expansion potential
        print("\n\nTest 1: High Department Expansion Potential")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze department expansion",
            context={
                "customer_id": "cust_expansion_ready",
                "customer_metadata": {"health_score": 85},
            },
        )
        state1["entities"] = {
            "organization_data": {
                "total_departments": 8,
                "departments": [
                    "sales",
                    "marketing",
                    "customer_support",
                    "product",
                    "engineering",
                    "finance",
                    "operations",
                    "hr",
                ],
                "company_size": "large",
                "headcount_growth_pct": 25,
                "expansion_budget_approved": True,
                "department_sizes": {"marketing": 20, "customer_support": 35, "product": 25},
            },
            "usage_data": {
                "departments_using": ["sales"],
                "usage_by_department": {"sales": {"users": 25, "usage_rate": 85}},
                "features_used": ["pipeline_tracking", "reporting", "analytics", "forecasting"],
                "cross_department_shares": 8,
                "new_department_inquiries": 5,
                "internal_referrals": 4,
                "pilot_requests": 2,
            },
            "contract_data": {"contract_value": 30000, "months_as_customer": 12},
        }

        result1 = await agent.process(state1)

        print(f"Coverage: {result1['department_coverage_pct']:.1f}%")
        print(f"Untapped Departments: {result1['untapped_departments']}")
        print(f"Revenue Potential: ${result1['department_expansion_revenue']:,}")
        print(f"Top Department: {result1['top_expansion_department']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Limited expansion opportunity
        print("\n\n" + "=" * 70)
        print("Test 2: Limited Department Expansion")
        print("-" * 70)

        state2 = create_initial_state(
            "Check department expansion",
            context={
                "customer_id": "cust_limited_expansion",
                "customer_metadata": {"health_score": 65},
            },
        )
        state2["entities"] = {
            "organization_data": {
                "total_departments": 4,
                "departments": ["sales", "marketing", "customer_support", "operations"],
                "company_size": "small",
                "headcount_growth_pct": 5,
            },
            "usage_data": {
                "departments_using": ["sales", "marketing", "customer_support"],
                "usage_by_department": {
                    "sales": {"users": 10, "usage_rate": 75},
                    "marketing": {"users": 8, "usage_rate": 70},
                    "customer_support": {"users": 12, "usage_rate": 65},
                },
                "features_used": ["reporting", "collaboration"],
                "cross_department_shares": 2,
                "new_department_inquiries": 0,
            },
            "contract_data": {"contract_value": 36000, "months_as_customer": 8},
        }

        result2 = await agent.process(state2)

        print(f"Coverage: {result2['department_coverage_pct']:.1f}%")
        print(f"Untapped Departments: {result2['untapped_departments']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
