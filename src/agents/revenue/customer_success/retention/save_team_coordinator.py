"""
Save Team Coordinator Agent - TASK-2043

Coordinates "save team" interventions for at-risk renewals, assembles cross-functional
teams, and executes comprehensive save plans to prevent high-value churn.
"""

from datetime import UTC, datetime
from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("save_team_coordinator", tier="revenue", category="customer_success")
class SaveTeamCoordinatorAgent(BaseAgent):
    """
    Save Team Coordinator Agent.

    Orchestrates save team interventions for at-risk customers:
    - Identifies customers requiring save team mobilization
    - Assembles appropriate cross-functional team
    - Creates comprehensive save plan with tactics
    - Coordinates execution across teams
    - Tracks save team progress and outcomes
    - Manages executive escalation when needed
    """

    # Save team urgency levels
    URGENCY_LEVELS = {
        "critical": {
            "mobilization_sla_hours": 4,
            "exec_involvement": "required",
            "team_size": "full",
        },
        "high": {
            "mobilization_sla_hours": 24,
            "exec_involvement": "recommended",
            "team_size": "full",
        },
        "medium": {
            "mobilization_sla_hours": 48,
            "exec_involvement": "optional",
            "team_size": "core",
        },
    }

    # Save team roles and responsibilities
    SAVE_TEAM_ROLES = {
        "csm": {"name": "Customer Success Manager", "required": True},
        "cs_manager": {"name": "CS Manager", "required": True},
        "account_exec": {"name": "Account Executive", "required": True},
        "solutions_engineer": {"name": "Solutions Engineer", "required": False},
        "product_manager": {"name": "Product Manager", "required": False},
        "support_lead": {"name": "Support Team Lead", "required": False},
        "exec_sponsor": {"name": "Executive Sponsor", "required": False},
        "finance": {"name": "Finance/Billing", "required": False},
    }

    def __init__(self):
        config = AgentConfig(
            name="save_team_coordinator",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=850,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="customer_success",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Coordinate save team mobilization and execution.

        Args:
            state: Current agent state with at-risk customer data

        Returns:
            Updated state with save team plan and coordination details
        """
        self.logger.info("save_team_coordination_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        risk_data = state.get("entities", {}).get("risk_data", {})
        contract_data = state.get("entities", {}).get("contract_data", {})
        customer_metadata = state.get("customer_metadata", {})
        churn_indicators = state.get("entities", {}).get("churn_indicators", [])

        self.logger.debug(
            "save_team_coordination_details",
            customer_id=customer_id,
            risk_level=risk_data.get("risk_level"),
            contract_value=contract_data.get("contract_value"),
        )

        # Assess save team need
        save_assessment = self._assess_save_team_need(risk_data, contract_data, churn_indicators)

        # Assemble save team
        save_team = self._assemble_save_team(save_assessment, customer_metadata, contract_data)

        # Create save plan
        save_plan = self._create_save_plan(
            save_assessment, risk_data, churn_indicators, customer_metadata
        )

        # Generate execution timeline
        execution_timeline = self._generate_execution_timeline(save_assessment, save_plan)

        # Define success metrics
        success_metrics = self._define_success_metrics(save_assessment, contract_data)

        # Format response
        response = self._format_save_team_report(
            save_assessment, save_team, save_plan, execution_timeline, success_metrics
        )

        state["agent_response"] = response
        state["save_team_urgency"] = save_assessment["urgency_level"]
        state["save_team_mobilized"] = save_assessment["requires_save_team"]
        state["save_success_probability"] = save_assessment["save_success_probability"]
        state["team_members"] = [member["role"] for member in save_team["team_members"]]
        state["save_assessment"] = save_assessment
        state["response_confidence"] = 0.93
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "save_team_coordination_completed",
            customer_id=customer_id,
            urgency=save_assessment["urgency_level"],
            team_size=len(save_team["team_members"]),
            success_probability=save_assessment["save_success_probability"],
        )

        return state

    def _assess_save_team_need(
        self,
        risk_data: dict[str, Any],
        contract_data: dict[str, Any],
        churn_indicators: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Assess whether save team mobilization is needed.

        Args:
            risk_data: Customer risk metrics
            contract_data: Contract and renewal information
            churn_indicators: List of churn risk indicators

        Returns:
            Save team assessment
        """
        contract_value = contract_data.get("contract_value", 0)
        risk_level = risk_data.get("risk_level", "medium")
        churn_probability = risk_data.get("churn_probability", 30)
        days_to_renewal = contract_data.get("days_to_renewal", 90)

        # Determine if save team is needed
        requires_save_team = self._determine_save_team_requirement(
            risk_level, contract_value, churn_probability, days_to_renewal
        )

        # Determine urgency
        urgency_level = self._determine_urgency_level(
            risk_level, days_to_renewal, churn_probability
        )

        # Calculate save success probability
        save_success_probability = self._calculate_save_probability(
            risk_data, contract_data, len(churn_indicators)
        )

        # Categorize churn indicators
        categorized_indicators = self._categorize_churn_indicators(churn_indicators)

        # Determine at-risk value
        at_risk_value = contract_value if requires_save_team else 0

        return {
            "requires_save_team": requires_save_team,
            "urgency_level": urgency_level,
            "save_success_probability": save_success_probability,
            "at_risk_value": at_risk_value,
            "churn_probability": churn_probability,
            "days_to_renewal": days_to_renewal,
            "categorized_indicators": categorized_indicators,
            "mobilization_sla_hours": self.URGENCY_LEVELS[urgency_level]["mobilization_sla_hours"],
            "exec_involvement": self.URGENCY_LEVELS[urgency_level]["exec_involvement"],
            "assessed_at": datetime.now(UTC).isoformat(),
        }

    def _determine_save_team_requirement(
        self, risk_level: str, contract_value: float, churn_probability: int, days_to_renewal: int
    ) -> bool:
        """Determine if save team mobilization is required."""
        # Critical risk always requires save team
        if risk_level in ["critical", "red"]:
            return True

        # High risk with significant value
        if risk_level in ["high", "orange"] and contract_value >= 50000:
            return True

        # High churn probability regardless of risk level
        if churn_probability >= 70:
            return True

        # Urgent timeline with medium+ risk
        return bool(days_to_renewal <= 14 and risk_level != "low")

    def _determine_urgency_level(
        self, risk_level: str, days_to_renewal: int, churn_probability: int
    ) -> str:
        """Determine urgency level for save team."""
        if risk_level == "critical" or days_to_renewal <= 7 or churn_probability >= 80:
            return "critical"
        elif risk_level == "high" or days_to_renewal <= 30 or churn_probability >= 60:
            return "high"
        else:
            return "medium"

    def _calculate_save_probability(
        self, risk_data: dict[str, Any], contract_data: dict[str, Any], indicator_count: int
    ) -> int:
        """Calculate probability of successfully saving the customer."""
        # Start with base probability
        churn_probability = risk_data.get("churn_probability", 50)
        base_save_probability = 100 - churn_probability

        # Adjust based on health score
        health_score = risk_data.get("health_score", 50)
        if health_score >= 60:
            base_save_probability += 15
        elif health_score >= 40:
            base_save_probability += 5
        elif health_score < 30:
            base_save_probability -= 10

        # Adjust based on contract history
        if contract_data.get("renewals_completed", 0) >= 2:
            base_save_probability += 10  # Loyal customer

        # Adjust based on number of issues
        if indicator_count >= 5:
            base_save_probability -= 15  # Many issues harder to resolve
        elif indicator_count <= 2:
            base_save_probability += 10  # Fewer issues easier to address

        # Adjust based on engagement
        if risk_data.get("customer_responsive", True):
            base_save_probability += 10
        else:
            base_save_probability -= 20  # Unresponsive customers harder to save

        return min(max(int(base_save_probability), 10), 90)

    def _categorize_churn_indicators(
        self, churn_indicators: list[dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Categorize churn indicators by type."""
        categorized = {
            "product": [],
            "support": [],
            "financial": [],
            "engagement": [],
            "competitive": [],
        }

        for indicator in churn_indicators:
            indicator_type = indicator.get("type", "unknown")
            indicator_desc = indicator.get("description", indicator_type)

            if (
                "feature" in indicator_type
                or "product" in indicator_type
                or "bug" in indicator_type
            ):
                categorized["product"].append(indicator_desc)
            elif "support" in indicator_type or "ticket" in indicator_type:
                categorized["support"].append(indicator_desc)
            elif (
                "payment" in indicator_type
                or "price" in indicator_type
                or "billing" in indicator_type
            ):
                categorized["financial"].append(indicator_desc)
            elif (
                "usage" in indicator_type
                or "login" in indicator_type
                or "engagement" in indicator_type
            ):
                categorized["engagement"].append(indicator_desc)
            elif "competitor" in indicator_type or "alternative" in indicator_type:
                categorized["competitive"].append(indicator_desc)
            else:
                categorized["engagement"].append(indicator_desc)

        return {k: v for k, v in categorized.items() if v}  # Remove empty categories

    def _assemble_save_team(
        self,
        save_assessment: dict[str, Any],
        customer_metadata: dict[str, Any],
        contract_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Assemble appropriate save team based on situation."""
        urgency = save_assessment["urgency_level"]
        categorized_indicators = save_assessment["categorized_indicators"]
        self.URGENCY_LEVELS[urgency]["team_size"]
        exec_involvement = self.URGENCY_LEVELS[urgency]["exec_involvement"]

        team_members = []

        # Core team (always included)
        team_members.extend(
            [
                {
                    "role": "csm",
                    "name": "Customer Success Manager",
                    "responsibilities": ["Lead save team", "Customer relationship"],
                },
                {
                    "role": "cs_manager",
                    "name": "CS Manager",
                    "responsibilities": ["Strategic oversight", "Escalation support"],
                },
                {
                    "role": "account_exec",
                    "name": "Account Executive",
                    "responsibilities": ["Contract negotiation", "Commercial terms"],
                },
            ]
        )

        # Add specialists based on issue categories
        if "product" in categorized_indicators:
            team_members.append(
                {
                    "role": "product_manager",
                    "name": "Product Manager",
                    "responsibilities": ["Address product gaps", "Roadmap discussion"],
                }
            )
            team_members.append(
                {
                    "role": "solutions_engineer",
                    "name": "Solutions Engineer",
                    "responsibilities": ["Technical solutions", "Custom implementations"],
                }
            )

        if "support" in categorized_indicators:
            team_members.append(
                {
                    "role": "support_lead",
                    "name": "Support Team Lead",
                    "responsibilities": ["Resolve support issues", "Service improvement plan"],
                }
            )

        if "financial" in categorized_indicators:
            team_members.append(
                {
                    "role": "finance",
                    "name": "Finance/Billing",
                    "responsibilities": ["Payment resolution", "Flexible terms"],
                }
            )

        # Add executive sponsor if needed
        if exec_involvement == "required" or (
            exec_involvement == "recommended" and contract_data.get("contract_value", 0) > 75000
        ):
            team_members.append(
                {
                    "role": "exec_sponsor",
                    "name": "Executive Sponsor (VP/C-level)",
                    "responsibilities": ["Executive alignment", "Strategic commitment"],
                }
            )

        return {
            "team_size": len(team_members),
            "team_members": team_members,
            "team_lead": "csm",
            "exec_involved": any(m["role"] == "exec_sponsor" for m in team_members),
        }

    def _create_save_plan(
        self,
        save_assessment: dict[str, Any],
        risk_data: dict[str, Any],
        churn_indicators: list[dict[str, Any]],
        customer_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Create comprehensive save plan."""
        categorized_indicators = save_assessment["categorized_indicators"]

        tactics = []

        # Immediate actions
        tactics.append(
            {
                "tactic": "Emergency customer call",
                "phase": "immediate",
                "owner": "csm + exec_sponsor",
                "objective": "Understand issues, show commitment",
                "timeline": "Within 24 hours",
            }
        )

        # Issue-specific tactics
        if "product" in categorized_indicators:
            tactics.append(
                {
                    "tactic": "Product roadmap discussion and gap analysis",
                    "phase": "discovery",
                    "owner": "product_manager",
                    "objective": "Address product concerns with future commitments",
                    "timeline": "Within 3 days",
                }
            )

        if "support" in categorized_indicators:
            tactics.append(
                {
                    "tactic": "White-glove support package implementation",
                    "phase": "immediate",
                    "owner": "support_lead",
                    "objective": "Demonstrate improved support experience",
                    "timeline": "Immediately",
                }
            )

        if "financial" in categorized_indicators:
            tactics.append(
                {
                    "tactic": "Flexible payment and pricing discussion",
                    "phase": "negotiation",
                    "owner": "finance + account_exec",
                    "objective": "Find financially viable path forward",
                    "timeline": "Within 5 days",
                }
            )

        if "engagement" in categorized_indicators:
            tactics.append(
                {
                    "tactic": "Adoption acceleration program",
                    "phase": "enablement",
                    "owner": "solutions_engineer",
                    "objective": "Drive usage and value realization",
                    "timeline": "Ongoing - 30 days",
                }
            )

        # Always include these
        tactics.extend(
            [
                {
                    "tactic": "Success plan co-creation",
                    "phase": "planning",
                    "owner": "csm",
                    "objective": "Align on mutual success criteria",
                    "timeline": "Within 7 days",
                },
                {
                    "tactic": "Executive Business Review (EBR)",
                    "phase": "alignment",
                    "owner": "exec_sponsor",
                    "objective": "Strategic alignment at executive level",
                    "timeline": "Within 10 days",
                },
                {
                    "tactic": "Weekly check-in cadence",
                    "phase": "monitoring",
                    "owner": "csm",
                    "objective": "Track progress and maintain momentum",
                    "timeline": "Ongoing",
                },
            ]
        )

        return {
            "plan_name": f"Save Plan - {customer_metadata.get('company_name', 'Customer')}",
            "tactics": tactics[:10],  # Top 10 tactics
            "total_tactics": len(tactics),
            "estimated_duration_days": 30,
        }

    def _generate_execution_timeline(
        self, save_assessment: dict[str, Any], save_plan: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate execution timeline for save plan."""
        timeline = []

        # Phase 1: Immediate (Days 1-2)
        timeline.append(
            {
                "phase": "Immediate Response",
                "days": "1-2",
                "milestones": [
                    "Save team mobilized",
                    "Emergency customer call completed",
                    "Issues documented and acknowledged",
                ],
            }
        )

        # Phase 2: Discovery (Days 3-7)
        timeline.append(
            {
                "phase": "Discovery & Analysis",
                "days": "3-7",
                "milestones": [
                    "Root cause analysis completed",
                    "Solution options identified",
                    "Success plan drafted",
                ],
            }
        )

        # Phase 3: Solution (Days 8-14)
        timeline.append(
            {
                "phase": "Solution Implementation",
                "days": "8-14",
                "milestones": [
                    "Key issues being addressed",
                    "Executive Business Review held",
                    "Renewal terms discussed",
                ],
            }
        )

        # Phase 4: Validation (Days 15-21)
        timeline.append(
            {
                "phase": "Validation & Commitment",
                "days": "15-21",
                "milestones": [
                    "Solution effectiveness validated",
                    "Customer satisfaction improved",
                    "Renewal commitment secured",
                ],
            }
        )

        # Phase 5: Transition (Days 22-30)
        timeline.append(
            {
                "phase": "Transition to BAU",
                "days": "22-30",
                "milestones": [
                    "Contract renewed",
                    "Ongoing support plan in place",
                    "Lessons learned documented",
                ],
            }
        )

        return timeline

    def _define_success_metrics(
        self, save_assessment: dict[str, Any], contract_data: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Define success metrics for save team effort."""
        metrics = [
            {
                "metric": "Customer retention",
                "target": "100% - customer renews contract",
                "measurement": "Contract signed",
            },
            {
                "metric": "Health score improvement",
                "target": "Increase by 20+ points",
                "measurement": "Health score tracking",
            },
            {
                "metric": "Issue resolution",
                "target": "90%+ of identified issues resolved",
                "measurement": "Issue tracker completion",
            },
            {
                "metric": "Customer satisfaction",
                "target": "NPS 7+ or improvement of 2+ points",
                "measurement": "Post-intervention survey",
            },
            {
                "metric": "Engagement improvement",
                "target": "Weekly engagement with product",
                "measurement": "Usage analytics",
            },
        ]

        return metrics

    def _format_save_team_report(
        self,
        save_assessment: dict[str, Any],
        save_team: dict[str, Any],
        save_plan: dict[str, Any],
        execution_timeline: list[dict[str, Any]],
        success_metrics: list[dict[str, str]],
    ) -> str:
        """Format save team coordination report."""
        urgency = save_assessment["urgency_level"]

        urgency_emoji = {"critical": "????", "high": "????", "medium": "??????"}

        report = f"""**{urgency_emoji.get(urgency, "????")} Save Team Coordination Report**

**Urgency Level:** {urgency.upper()}
**Save Success Probability:** {save_assessment["save_success_probability"]}%
**At-Risk Value:** ${save_assessment["at_risk_value"]:,}
**Mobilization SLA:** {save_assessment["mobilization_sla_hours"]} hours
**Executive Involvement:** {save_assessment["exec_involvement"].title()}

**???? Situation Analysis:**
- Churn Probability: {save_assessment["churn_probability"]}%
- Days to Renewal: {save_assessment["days_to_renewal"]}
- Issue Categories: {", ".join(save_assessment["categorized_indicators"].keys())}

**???? Save Team Composition ({save_team["team_size"]} members):**
"""

        for member in save_team["team_members"]:
            report += f"\n**{member['name']}** ({member['role']})\n"
            for resp in member["responsibilities"]:
                report += f"  - {resp}\n"

        # Save plan tactics
        report += f"\n**???? Save Plan ({save_plan['total_tactics']} tactics):**\n"

        # Group tactics by phase
        phases = {}
        for tactic in save_plan["tactics"]:
            phase = tactic["phase"]
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(tactic)

        for phase, phase_tactics in phases.items():
            if phase_tactics:
                report += f"\n**{phase.title()} Phase:**\n"
                for tactic in phase_tactics[:3]:  # Top 3 per phase
                    report += f"- **{tactic['tactic']}**\n"
                    report += f"  Owner: {tactic['owner']} | Timeline: {tactic['timeline']}\n"
                    report += f"  Objective: {tactic['objective']}\n"

        # Execution timeline
        report += "\n**???? Execution Timeline:**\n"
        for phase in execution_timeline[:3]:  # Show first 3 phases
            report += f"\n**{phase['phase']}** (Days {phase['days']})\n"
            for milestone in phase["milestones"]:
                report += f"  ??? {milestone}\n"

        # Success metrics
        report += "\n**???? Success Metrics:**\n"
        for metric in success_metrics[:4]:  # Top 4 metrics
            report += f"- **{metric['metric']}:** {metric['target']}\n"

        return report


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Save Team Coordinator Agent (TASK-2043)")
        print("=" * 70)

        agent = SaveTeamCoordinatorAgent()

        # Test 1: Critical save situation
        print("\n\nTest 1: Critical Save Team Mobilization")
        print("-" * 70)

        state1 = create_initial_state(
            "Mobilize save team for at-risk customer",
            context={
                "customer_id": "cust_critical_123",
                "customer_metadata": {"plan": "enterprise", "company_name": "Acme Corp"},
            },
        )
        state1["entities"] = {
            "risk_data": {
                "risk_level": "critical",
                "churn_probability": 85,
                "health_score": 28,
                "customer_responsive": True,
            },
            "contract_data": {
                "contract_value": 150000,
                "days_to_renewal": 12,
                "renewals_completed": 1,
            },
            "churn_indicators": [
                {
                    "type": "product_feature_gap",
                    "description": "Missing critical analytics features",
                },
                {"type": "support_issues", "description": "Multiple unresolved technical issues"},
                {"type": "usage_decline", "description": "40% drop in active users"},
                {"type": "competitor_evaluation", "description": "Evaluating competitor solutions"},
                {"type": "executive_dissatisfaction", "description": "CEO expressing concerns"},
            ],
        }

        result1 = await agent.process(state1)

        print(f"Urgency: {result1['save_team_urgency']}")
        print(f"Team Mobilized: {result1['save_team_mobilized']}")
        print(f"Success Probability: {result1['save_success_probability']}%")
        print(f"Team Size: {len(result1['team_members'])}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Medium urgency save
        print("\n\n" + "=" * 70)
        print("Test 2: Medium Urgency Save Team")
        print("-" * 70)

        state2 = create_initial_state(
            "Assess save team need",
            context={
                "customer_id": "cust_medium_456",
                "customer_metadata": {"plan": "premium", "company_name": "Beta Inc"},
            },
        )
        state2["entities"] = {
            "risk_data": {
                "risk_level": "high",
                "churn_probability": 55,
                "health_score": 48,
                "customer_responsive": True,
            },
            "contract_data": {
                "contract_value": 60000,
                "days_to_renewal": 45,
                "renewals_completed": 2,
            },
            "churn_indicators": [
                {"type": "usage_low", "description": "Low product adoption"},
                {"type": "price_concerns", "description": "Questioning ROI"},
            ],
        }

        result2 = await agent.process(state2)

        print(f"Urgency: {result2['save_team_urgency']}")
        print(f"Success Probability: {result2['save_success_probability']}%")
        print(f"\nResponse preview:\n{result2['agent_response'][:650]}...")

    asyncio.run(test())
