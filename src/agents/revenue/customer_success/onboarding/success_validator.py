"""
Success Validator Agent - TASK-2026

Validates success criteria, signs off on onboarding completion, and manages handoff to CSM.
Ensures all success criteria are met before declaring onboarding complete.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("success_validator", tier="revenue", category="customer_success")
class SuccessValidatorAgent(BaseAgent):
    """
    Success Validator Agent.

    Validates and manages:
    - Success criteria achievement verification
    - Customer acceptance and sign-off
    - Handoff documentation preparation
    - CSM transition and briefing
    - Post-onboarding recommendations
    """

    # Success criteria categories and weights
    SUCCESS_CATEGORIES = {
        "user_adoption": {"weight": 25, "threshold": 80},
        "feature_utilization": {"weight": 20, "threshold": 70},
        "business_outcomes": {"weight": 30, "threshold": 75},
        "technical_integration": {"weight": 15, "threshold": 90},
        "team_proficiency": {"weight": 10, "threshold": 85}
    }

    # Sign-off requirements
    SIGNOFF_REQUIREMENTS = [
        "all_critical_criteria_met",
        "customer_satisfaction_confirmed",
        "technical_validation_complete",
        "documentation_delivered",
        "csm_briefing_complete"
    ]

    def __init__(self):
        config = AgentConfig(
            name="success_validator",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
            max_tokens=500,
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
        Validate success criteria and manage handoff.

        Args:
            state: Current agent state with validation data

        Returns:
            Updated state with validation results and handoff status
        """
        self.logger.info("success_validation_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        validation_data = state.get("entities", {}).get("validation_data", {})
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "success_validation_details",
            customer_id=customer_id,
            criteria_met=len(validation_data.get("criteria_met", [])),
            ready_for_signoff=validation_data.get("ready_for_signoff", False)
        )

        # Validate success criteria
        validation_analysis = self._validate_success_criteria(
            validation_data,
            customer_metadata
        )

        # Check sign-off readiness
        signoff_status = self._check_signoff_readiness(validation_analysis, validation_data)

        # Generate handoff package
        handoff_package = self._generate_handoff_package(
            validation_analysis,
            validation_data,
            customer_metadata
        )

        # Build response
        response = self._format_validation_report(
            validation_analysis,
            signoff_status,
            handoff_package
        )

        state["agent_response"] = response
        state["validation_status"] = validation_analysis["overall_status"]
        state["success_score"] = validation_analysis["overall_success_score"]
        state["ready_for_signoff"] = signoff_status["ready"]
        state["handoff_ready"] = signoff_status.get("handoff_ready", False)
        state["validation_analysis"] = validation_analysis
        state["response_confidence"] = 0.90
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "success_validation_completed",
            customer_id=customer_id,
            validation_status=validation_analysis["overall_status"],
            success_score=validation_analysis["overall_success_score"],
            ready_for_signoff=signoff_status["ready"]
        )

        return state

    def _validate_success_criteria(
        self,
        validation_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate all success criteria categories.

        Args:
            validation_data: Validation metrics and achievements
            customer_metadata: Customer profile data

        Returns:
            Comprehensive validation analysis
        """
        criteria_scores = {}
        criteria_met = {}
        gaps = []

        # Validate each category
        for category, config in self.SUCCESS_CATEGORIES.items():
            score = validation_data.get(f"{category}_score", 0)
            threshold = config["threshold"]

            criteria_scores[category] = score
            criteria_met[category] = score >= threshold

            # Identify gaps
            if score < threshold:
                gap_size = threshold - score
                gaps.append({
                    "category": category,
                    "current_score": score,
                    "required_score": threshold,
                    "gap": gap_size,
                    "severity": "critical" if gap_size > 20 else "high" if gap_size > 10 else "medium"
                })

        # Calculate overall success score (weighted average)
        overall_success_score = sum(
            criteria_scores.get(cat, 0) * config["weight"] / 100
            for cat, config in self.SUCCESS_CATEGORIES.items()
        )

        # Calculate achievement percentage
        categories_met = sum(1 for met in criteria_met.values() if met)
        achievement_percentage = int((categories_met / len(self.SUCCESS_CATEGORIES)) * 100)

        # Determine overall status
        overall_status = self._determine_validation_status(
            overall_success_score,
            achievement_percentage,
            gaps
        )

        return {
            "overall_status": overall_status,
            "overall_success_score": int(overall_success_score),
            "achievement_percentage": achievement_percentage,
            "criteria_scores": criteria_scores,
            "criteria_met": criteria_met,
            "categories_met": categories_met,
            "total_categories": len(self.SUCCESS_CATEGORIES),
            "gaps": gaps,
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _determine_validation_status(
        self,
        success_score: float,
        achievement_pct: int,
        gaps: List[Dict[str, Any]]
    ) -> str:
        """Determine overall validation status."""
        critical_gaps = [g for g in gaps if g["severity"] == "critical"]

        if success_score >= 90 and achievement_pct == 100:
            return "excellent"
        elif success_score >= 80 and achievement_pct >= 80:
            return "passed"
        elif critical_gaps:
            return "failed_critical_gaps"
        elif success_score >= 70:
            return "passed_with_gaps"
        else:
            return "not_ready"

    def _check_signoff_readiness(
        self,
        validation_analysis: Dict[str, Any],
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if ready for customer sign-off."""
        readiness_checks = {}

        # Check critical criteria
        critical_gaps = [g for g in validation_analysis["gaps"] if g["severity"] == "critical"]
        readiness_checks["all_critical_criteria_met"] = len(critical_gaps) == 0

        # Check customer satisfaction
        csat_score = validation_data.get("customer_satisfaction_score", 0)
        readiness_checks["customer_satisfaction_confirmed"] = csat_score >= 7  # 7/10

        # Check technical validation
        technical_validation = validation_data.get("technical_validation_passed", False)
        readiness_checks["technical_validation_complete"] = technical_validation

        # Check documentation
        documentation_delivered = validation_data.get("documentation_delivered", False)
        readiness_checks["documentation_delivered"] = documentation_delivered

        # Check CSM briefing
        csm_briefing = validation_data.get("csm_briefing_complete", False)
        readiness_checks["csm_briefing_complete"] = csm_briefing

        # Overall readiness
        all_requirements_met = all(readiness_checks.values())
        handoff_ready = all_requirements_met and validation_analysis["overall_status"] in ["excellent", "passed", "passed_with_gaps"]

        # Identify missing requirements
        missing_requirements = [
            req for req, met in readiness_checks.items() if not met
        ]

        return {
            "ready": all_requirements_met,
            "handoff_ready": handoff_ready,
            "readiness_checks": readiness_checks,
            "missing_requirements": missing_requirements,
            "checks_passed": sum(1 for met in readiness_checks.values() if met),
            "total_checks": len(self.SIGNOFF_REQUIREMENTS)
        }

    def _generate_handoff_package(
        self,
        validation_analysis: Dict[str, Any],
        validation_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate handoff package for CSM."""
        # Key achievements
        achievements = []
        for category, met in validation_analysis["criteria_met"].items():
            if met:
                score = validation_analysis["criteria_scores"][category]
                achievements.append({
                    "category": category.replace('_', ' ').title(),
                    "score": score,
                    "status": "achieved"
                })

        # Areas for CSM focus
        csm_focus_areas = []
        for gap in validation_analysis["gaps"]:
            csm_focus_areas.append({
                "area": gap["category"].replace('_', ' ').title(),
                "current_state": f"{gap['current_score']}%",
                "target": f"{gap['required_score']}%",
                "priority": gap["severity"]
            })

        # Customer profile summary
        customer_summary = {
            "customer_id": validation_data.get("customer_id", "N/A"),
            "plan": customer_metadata.get("plan", "N/A"),
            "industry": customer_metadata.get("industry", "N/A"),
            "total_users": customer_metadata.get("total_users", 0),
            "key_stakeholders": validation_data.get("key_stakeholders", [])
        }

        # Recommended next steps for CSM
        next_steps = self._generate_csm_next_steps(
            validation_analysis,
            csm_focus_areas
        )

        return {
            "achievements": achievements,
            "csm_focus_areas": csm_focus_areas,
            "customer_summary": customer_summary,
            "next_steps": next_steps,
            "handoff_date": datetime.now(UTC).date().isoformat()
        }

    def _generate_csm_next_steps(
        self,
        validation_analysis: Dict[str, Any],
        focus_areas: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommended next steps for CSM."""
        next_steps = []

        # Always recommend initial check-in
        next_steps.append("Schedule initial CSM check-in within 7 days")

        # Focus area based recommendations
        for area in focus_areas[:2]:
            if "adoption" in area["area"].lower():
                next_steps.append(f"Drive user adoption improvement - currently at {area['current_state']}")
            elif "utilization" in area["area"].lower():
                next_steps.append(f"Encourage advanced feature adoption - target {area['target']}")
            elif "business" in area["area"].lower():
                next_steps.append(f"Review and align on business outcomes achievement")

        # Status-based recommendations
        if validation_analysis["overall_status"] == "excellent":
            next_steps.append("Explore upsell and expansion opportunities")
        elif validation_analysis["overall_status"] in ["passed_with_gaps", "failed_critical_gaps"]:
            next_steps.append("Create improvement plan to address identified gaps")

        # Standard recommendations
        next_steps.append("Schedule first QBR within 60 days")

        return next_steps[:5]

    def _format_validation_report(
        self,
        validation_analysis: Dict[str, Any],
        signoff_status: Dict[str, Any],
        handoff_package: Dict[str, Any]
    ) -> str:
        """Format success validation report."""
        status = validation_analysis["overall_status"]

        status_emoji = {
            "excellent": "????",
            "passed": "???",
            "passed_with_gaps": "??????",
            "failed_critical_gaps": "????",
            "not_ready": "???"
        }

        report = f"""**{status_emoji.get(status, '????')} Success Validation Report**

**Overall Status:** {status.replace('_', ' ').title()}
**Success Score:** {validation_analysis['overall_success_score']}/100
**Achievement:** {validation_analysis['achievement_percentage']}% ({validation_analysis['categories_met']}/{validation_analysis['total_categories']} categories)

**Success Criteria Validation:**
"""
        for category, score in validation_analysis['criteria_scores'].items():
            threshold = self.SUCCESS_CATEGORIES[category]["threshold"]
            met = validation_analysis['criteria_met'][category]
            status_icon = "???" if met else "???"
            report += f"- {category.replace('_', ' ').title()}: {score}% (threshold: {threshold}%) {status_icon}\n"

        # Gaps
        if validation_analysis.get("gaps"):
            report += "\n**?????? Gaps Identified:**\n"
            for gap in validation_analysis["gaps"][:3]:
                report += f"- {gap['category'].replace('_', ' ').title()}: {gap['gap']}% below threshold ({gap['severity']} priority)\n"

        # Sign-off readiness
        report += f"\n**???? Sign-off Readiness:**\n"
        report += f"- Ready for Sign-off: {'Yes ???' if signoff_status['ready'] else 'No ???'}\n"
        report += f"- Handoff Ready: {'Yes ???' if signoff_status['handoff_ready'] else 'No ???'}\n"
        report += f"- Checks Passed: {signoff_status['checks_passed']}/{signoff_status['total_checks']}\n"

        if signoff_status.get("missing_requirements"):
            report += "\n**Missing Requirements:**\n"
            for req in signoff_status["missing_requirements"][:3]:
                report += f"- {req.replace('_', ' ').title()}\n"

        # Handoff package preview
        if signoff_status["handoff_ready"]:
            report += "\n**???? CSM Handoff Package:**\n"
            report += f"- Achievements: {len(handoff_package['achievements'])} categories met\n"
            report += f"- Focus Areas: {len(handoff_package['csm_focus_areas'])} areas for CSM attention\n"

            if handoff_package["next_steps"]:
                report += "\n**Next Steps for CSM:**\n"
                for i, step in enumerate(handoff_package["next_steps"][:3], 1):
                    report += f"{i}. {step}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Success Validator Agent (TASK-2026)")
        print("=" * 70)

        agent = SuccessValidatorAgent()

        # Test 1: Excellent validation - ready for sign-off
        print("\n\nTest 1: Excellent Success - Ready for Sign-off")
        print("-" * 70)

        state1 = create_initial_state(
            "Validate onboarding success",
            context={
                "customer_id": "cust_123",
                "customer_metadata": {
                    "plan": "enterprise",
                    "industry": "fintech",
                    "total_users": 50
                }
            }
        )
        state1["entities"] = {
            "validation_data": {
                "customer_id": "cust_123",
                "user_adoption_score": 88,
                "feature_utilization_score": 82,
                "business_outcomes_score": 85,
                "technical_integration_score": 95,
                "team_proficiency_score": 90,
                "customer_satisfaction_score": 9,
                "technical_validation_passed": True,
                "documentation_delivered": True,
                "csm_briefing_complete": True,
                "key_stakeholders": ["CTO", "VP Operations"]
            }
        }

        result1 = await agent.process(state1)

        print(f"Status: {result1['validation_status']}")
        print(f"Success Score: {result1['success_score']}/100")
        print(f"Ready for Sign-off: {result1['ready_for_signoff']}")
        print(f"Handoff Ready: {result1['handoff_ready']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Gaps identified - not ready
        print("\n\n" + "=" * 70)
        print("Test 2: Gaps Identified - Not Ready for Sign-off")
        print("-" * 70)

        state2 = create_initial_state(
            "Check validation status",
            context={
                "customer_id": "cust_456",
                "customer_metadata": {
                    "plan": "premium",
                    "total_users": 20
                }
            }
        )
        state2["entities"] = {
            "validation_data": {
                "customer_id": "cust_456",
                "user_adoption_score": 65,
                "feature_utilization_score": 55,
                "business_outcomes_score": 70,
                "technical_integration_score": 88,
                "team_proficiency_score": 75,
                "customer_satisfaction_score": 6,
                "technical_validation_passed": True,
                "documentation_delivered": False,
                "csm_briefing_complete": False,
                "key_stakeholders": ["Product Manager"]
            }
        }

        result2 = await agent.process(state2)

        print(f"Status: {result2['validation_status']}")
        print(f"Success Score: {result2['success_score']}/100")
        print(f"Ready for Sign-off: {result2['ready_for_signoff']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
