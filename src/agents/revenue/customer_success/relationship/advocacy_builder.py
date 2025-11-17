"""
Advocacy Builder Agent - TASK-2066

Builds customer advocacy by requesting testimonials, case studies, and referrals,
and generates opportunities for customers to become brand advocates.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("advocacy_builder", tier="revenue", category="customer_success")
class AdvocacyBuilderAgent(BaseAgent):
    """
    Advocacy Builder Agent.

    Builds customer advocacy by:
    - Identifying advocacy-ready customers
    - Requesting testimonials and reviews
    - Creating case studies and success stories
    - Generating referral opportunities
    - Facilitating speaking engagements
    - Building brand ambassador programs
    """

    # Advocacy readiness criteria
    ADVOCACY_CRITERIA = {
        "nps_score": {"threshold": 9, "weight": 30},
        "tenure_days": {"threshold": 90, "weight": 20},
        "health_score": {"threshold": 80, "weight": 25},
        "engagement_level": {"threshold": 75, "weight": 15},
        "value_realized": {"threshold": 100, "weight": 10}
    }

    # Advocacy types and requirements
    ADVOCACY_TYPES = {
        "testimonial": {"effort": "low", "nps_min": 8, "tenure_min": 30},
        "review": {"effort": "low", "nps_min": 8, "tenure_min": 60},
        "case_study": {"effort": "medium", "nps_min": 9, "tenure_min": 90},
        "referral": {"effort": "low", "nps_min": 9, "tenure_min": 60},
        "speaking": {"effort": "high", "nps_min": 9, "tenure_min": 180},
        "advisory_board": {"effort": "high", "nps_min": 9, "tenure_min": 365}
    }

    # Advocacy benefits/incentives
    ADVOCACY_INCENTIVES = {
        "testimonial": "Featured on website, LinkedIn promotion",
        "review": "Amazon/Visa gift card, early feature access",
        "case_study": "Co-marketing opportunity, industry visibility",
        "referral": "Referral credits or discounts",
        "speaking": "Thought leadership platform, networking",
        "advisory_board": "Product influence, exclusive events"
    }

    def __init__(self):
        config = AgentConfig(
            name="advocacy_builder",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            max_tokens=700,
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
        Build customer advocacy opportunities.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with advocacy plan
        """
        self.logger.info("advocacy_building_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})
        business_data = state.get("entities", {}).get("business_data", {})
        health_data = state.get("entities", {}).get("health_data", {})

        self.logger.debug(
            "advocacy_building_details",
            customer_id=customer_id,
            nps_score=engagement_data.get("nps_score", 0)
        )

        # Assess advocacy readiness
        advocacy_assessment = self._assess_advocacy_readiness(
            engagement_data,
            business_data,
            health_data,
            customer_metadata
        )

        # Identify advocacy opportunities
        advocacy_opportunities = self._identify_advocacy_opportunities(
            advocacy_assessment,
            engagement_data,
            customer_metadata
        )

        # Create advocacy request plan
        request_plan = self._create_advocacy_request_plan(
            advocacy_opportunities,
            customer_metadata
        )

        # Generate success story ideas
        story_ideas = self._generate_success_story_ideas(
            business_data,
            engagement_data,
            customer_metadata
        )

        # Create action plan
        action_plan = self._create_advocacy_action_plan(
            advocacy_assessment,
            advocacy_opportunities
        )

        # Format response
        response = self._format_advocacy_report(
            advocacy_assessment,
            advocacy_opportunities,
            request_plan,
            story_ideas,
            action_plan
        )

        state["agent_response"] = response
        state["advocacy_readiness_score"] = advocacy_assessment["readiness_score"]
        state["advocacy_ready"] = advocacy_assessment["is_advocacy_ready"]
        state["recommended_advocacy_type"] = advocacy_opportunities[0]["type"] if advocacy_opportunities else "none"
        state["advocacy_opportunities_count"] = len(advocacy_opportunities)
        state["response_confidence"] = 0.83
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "advocacy_building_completed",
            customer_id=customer_id,
            readiness_score=advocacy_assessment["readiness_score"],
            advocacy_ready=advocacy_assessment["is_advocacy_ready"]
        )

        return state

    def _assess_advocacy_readiness(
        self,
        engagement_data: Dict[str, Any],
        business_data: Dict[str, Any],
        health_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess customer readiness for advocacy.

        Args:
            engagement_data: Customer engagement metrics
            business_data: Business and contract data
            health_data: Customer health metrics
            customer_metadata: Customer profile data

        Returns:
            Advocacy readiness assessment
        """
        scores = {}

        # NPS score (0-30 points)
        nps = engagement_data.get("nps_score", 0)
        nps_score = (nps / 10) * 30
        scores["nps_score"] = min(nps_score, 30)

        # Customer tenure (0-20 points)
        customer_since = business_data.get("customer_since_date")
        if customer_since:
            try:
                since_date = datetime.fromisoformat(customer_since.replace('Z', '+00:00'))
                tenure_days = (datetime.now(UTC) - since_date).days
            except:
                tenure_days = 0
        else:
            tenure_days = 0

        tenure_score = min((tenure_days / 365) * 20, 20)
        scores["tenure_days"] = tenure_score

        # Health score (0-25 points)
        health_score = health_data.get("health_score", 50)
        health_points = (health_score / 100) * 25
        scores["health_score"] = health_points

        # Engagement level (0-15 points)
        touchpoints = engagement_data.get("touchpoints_last_30d", 0)
        engagement_score = min((touchpoints / 10) * 15, 15)
        scores["engagement_level"] = engagement_score

        # Value realized (0-10 points)
        roi_realized = business_data.get("roi_realized_percentage", 0)
        value_score = min((roi_realized / 200) * 10, 10)
        scores["value_realized"] = value_score

        # Calculate total
        readiness_score = sum(scores.values())
        readiness_score = min(int(readiness_score), 100)

        # Determine if advocacy ready
        is_advocacy_ready = (
            readiness_score >= 70 and
            nps >= 8 and
            tenure_days >= 30
        )

        # Determine readiness tier
        if readiness_score >= 85:
            readiness_tier = "champion"
        elif readiness_score >= 70:
            readiness_tier = "advocate"
        elif readiness_score >= 50:
            readiness_tier = "potential"
        else:
            readiness_tier = "not_ready"

        return {
            "readiness_score": readiness_score,
            "readiness_tier": readiness_tier,
            "is_advocacy_ready": is_advocacy_ready,
            "score_breakdown": {k: int(v) for k, v in scores.items()},
            "tenure_days": tenure_days,
            "nps_score": nps,
            "assessed_at": datetime.now(UTC).isoformat()
        }

    def _identify_advocacy_opportunities(
        self,
        advocacy_assessment: Dict[str, Any],
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify advocacy opportunities for customer."""
        opportunities = []

        if not advocacy_assessment["is_advocacy_ready"]:
            return opportunities

        nps = advocacy_assessment["nps_score"]
        tenure_days = advocacy_assessment["tenure_days"]
        tier = customer_metadata.get("tier", "standard")

        # Check each advocacy type
        for advocacy_type, requirements in self.ADVOCACY_TYPES.items():
            if nps >= requirements["nps_min"] and tenure_days >= requirements["tenure_min"]:
                # Calculate fit score
                fit_score = 100
                if advocacy_type in ["case_study", "speaking"] and tier not in ["enterprise", "premium"]:
                    fit_score -= 20

                opportunity = {
                    "type": advocacy_type,
                    "effort": requirements["effort"],
                    "fit_score": fit_score,
                    "incentive": self.ADVOCACY_INCENTIVES.get(advocacy_type, "Recognition"),
                    "priority": self._determine_advocacy_priority(
                        advocacy_type,
                        advocacy_assessment,
                        tier
                    )
                }

                opportunities.append(opportunity)

        # Sort by priority and fit score
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        opportunities.sort(
            key=lambda x: (priority_order.get(x["priority"], 3), -x["fit_score"])
        )

        return opportunities

    def _determine_advocacy_priority(
        self,
        advocacy_type: str,
        advocacy_assessment: Dict[str, Any],
        tier: str
    ) -> str:
        """Determine priority for advocacy type."""
        readiness_tier = advocacy_assessment["readiness_tier"]

        # High-value advocacy types
        if advocacy_type in ["case_study", "speaking", "advisory_board"]:
            if readiness_tier == "champion" and tier == "enterprise":
                return "high"
            return "medium"

        # Easy wins
        if advocacy_type in ["testimonial", "review", "referral"]:
            if readiness_tier in ["champion", "advocate"]:
                return "high"
            return "medium"

        return "low"

    def _create_advocacy_request_plan(
        self,
        advocacy_opportunities: List[Dict[str, Any]],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create plan for requesting advocacy."""
        if not advocacy_opportunities:
            return {
                "recommended_approach": "Focus on improving customer satisfaction first",
                "timing": "Not ready for advocacy requests",
                "message_template": None
            }

        top_opportunity = advocacy_opportunities[0]
        advocacy_type = top_opportunity["type"]

        # Determine best timing
        timing = self._determine_advocacy_timing(advocacy_type)

        # Create message template
        message_template = self._create_advocacy_message_template(
            advocacy_type,
            top_opportunity["incentive"],
            customer_metadata
        )

        return {
            "recommended_advocacy_type": advocacy_type,
            "recommended_approach": f"Request {advocacy_type} - {top_opportunity['effort']} effort",
            "timing": timing,
            "incentive_offered": top_opportunity["incentive"],
            "message_template": message_template,
            "follow_up_cadence": "1 week if no response"
        }

    def _determine_advocacy_timing(self, advocacy_type: str) -> str:
        """Determine best timing for advocacy request."""
        timing_map = {
            "testimonial": "Within 1 week of positive feedback",
            "review": "After QBR or major success milestone",
            "case_study": "After significant ROI achievement",
            "referral": "After renewal or expansion",
            "speaking": "3-6 months before target event",
            "advisory_board": "During annual planning cycle"
        }

        return timing_map.get(advocacy_type, "When customer shares positive feedback")

    def _create_advocacy_message_template(
        self,
        advocacy_type: str,
        incentive: str,
        customer_metadata: Dict[str, Any]
    ) -> str:
        """Create personalized advocacy request message template."""
        company_name = customer_metadata.get("company_name", "your organization")

        templates = {
            "testimonial": f"Given the great success {company_name} has achieved, would you be willing to provide a brief testimonial? {incentive}",
            "review": f"We'd love to feature {company_name}'s success! Would you consider leaving a review? {incentive}",
            "case_study": f"Your results are impressive! Would you be interested in a co-branded case study? {incentive}",
            "referral": f"Who else do you know who could benefit from similar results? {incentive}",
            "speaking": f"Would you be interested in speaking about {company_name}'s success at our user conference? {incentive}",
            "advisory_board": f"We'd be honored to have you join our customer advisory board. {incentive}"
        }

        return templates.get(advocacy_type, "Would you be willing to share your success story?")

    def _generate_success_story_ideas(
        self,
        business_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[str]:
        """Generate success story angles."""
        story_ideas = []

        industry = customer_metadata.get("industry", "business")
        company_name = customer_metadata.get("company_name", "Customer")

        # ROI-focused story
        roi = business_data.get("roi_realized_percentage", 0)
        if roi > 100:
            story_ideas.append(
                f"How {company_name} achieved {roi}% ROI in {industry}"
            )

        # Adoption success
        story_ideas.append(
            f"{company_name}'s journey to successful platform adoption"
        )

        # Transformation story
        story_ideas.append(
            f"Transforming {industry} operations: {company_name}'s story"
        )

        # Efficiency story
        story_ideas.append(
            f"Streamlining {industry} workflows: A {company_name} case study"
        )

        return story_ideas[:4]

    def _create_advocacy_action_plan(
        self,
        advocacy_assessment: Dict[str, Any],
        advocacy_opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Create action plan for advocacy building."""
        actions = []

        if not advocacy_assessment["is_advocacy_ready"]:
            actions.append({
                "action": "Improve customer satisfaction before requesting advocacy",
                "owner": "CSM",
                "timeline": "Ongoing",
                "priority": "medium"
            })

            actions.append({
                "action": f"Target advocacy readiness score of 70+ (currently {advocacy_assessment['readiness_score']})",
                "owner": "CSM",
                "timeline": "Next quarter",
                "priority": "medium"
            })
        else:
            # Ready for advocacy
            if advocacy_opportunities:
                top_opp = advocacy_opportunities[0]
                actions.append({
                    "action": f"Request {top_opp['type']} from customer",
                    "owner": "CSM",
                    "timeline": "This week",
                    "priority": top_opp["priority"]
                })

            if len(advocacy_opportunities) > 1:
                actions.append({
                    "action": "Plan multi-touch advocacy campaign with various requests",
                    "owner": "CSM + Marketing",
                    "timeline": "Next 30 days",
                    "priority": "medium"
                })

            # Case study development
            if any(opp["type"] == "case_study" for opp in advocacy_opportunities):
                actions.append({
                    "action": "Coordinate with Marketing to develop case study",
                    "owner": "CSM + Marketing",
                    "timeline": "Next 60 days",
                    "priority": "high"
                })

        return actions[:5]

    def _format_advocacy_report(
        self,
        advocacy_assessment: Dict[str, Any],
        advocacy_opportunities: List[Dict[str, Any]],
        request_plan: Dict[str, Any],
        story_ideas: List[str],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format advocacy building report."""
        tier = advocacy_assessment["readiness_tier"]
        score = advocacy_assessment["readiness_score"]
        ready = advocacy_assessment["is_advocacy_ready"]

        tier_emoji = {
            "champion": "????",
            "advocate": "???",
            "potential": "????",
            "not_ready": "???"
        }

        report = f"""**???? Customer Advocacy Assessment**

**Advocacy Readiness:** {tier.title()} {tier_emoji.get(tier, '???')}
**Readiness Score:** {score}/100
**Ready for Advocacy:** {'Yes ???' if ready else 'Not yet ???'}
**NPS Score:** {advocacy_assessment['nps_score']}/10
**Customer Tenure:** {advocacy_assessment['tenure_days']} days

**Readiness Breakdown:**
"""

        for dimension, score_val in advocacy_assessment["score_breakdown"].items():
            max_score = self.ADVOCACY_CRITERIA[dimension]["weight"]
            pct = int((score_val / max_score * 100)) if max_score > 0 else 0
            bar = "???" * int(pct / 10) + "???" * (10 - int(pct / 10))
            report += f"- {dimension.replace('_', ' ').title()}: {int(score_val)}/{max_score} {bar}\n"

        if advocacy_opportunities:
            report += f"\n**???? Advocacy Opportunities ({len(advocacy_opportunities)} identified):**\n"
            for i, opp in enumerate(advocacy_opportunities[:5], 1):
                priority_icon = "????" if opp["priority"] == "high" else "????" if opp["priority"] == "medium" else "????"
                effort_icon = "???" if opp["effort"] == "low" else "??????" if opp["effort"] == "medium" else "???????"
                report += f"{i}. **{opp['type'].title()}** {priority_icon} {effort_icon}\n"
                report += f"   - Effort: {opp['effort'].title()}\n"
                report += f"   - Incentive: {opp['incentive']}\n"

        # Request plan
        if ready:
            report += f"\n**???? Advocacy Request Plan:**\n"
            report += f"**Recommended Ask:** {request_plan['recommended_advocacy_type'].title()}\n"
            report += f"**Timing:** {request_plan['timing']}\n"
            report += f"**Incentive:** {request_plan['incentive_offered']}\n"

            if request_plan.get("message_template"):
                report += f"\n**Message Template:**\n\"{request_plan['message_template']}\"\n"

        # Success story ideas
        if story_ideas:
            report += "\n**???? Success Story Ideas:**\n"
            for i, idea in enumerate(story_ideas, 1):
                report += f"{i}. {idea}\n"

        # Action plan
        if action_plan:
            report += "\n**??? Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        if ready:
            report += "\n**???? Tip:** Strike while the iron is hot - request advocacy shortly after positive interactions!"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Advocacy Builder Agent (TASK-2066)")
        print("=" * 70)

        agent = AdvocacyBuilderAgent()

        # Test 1: Advocacy-ready customer
        print("\n\nTest 1: Advocacy-Ready Customer")
        print("-" * 70)

        state1 = create_initial_state(
            "Assess advocacy opportunities",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {
                    "tier": "enterprise",
                    "company_name": "TechCorp Inc",
                    "industry": "technology"
                }
            }
        )
        state1["entities"] = {
            "engagement_data": {
                "nps_score": 9,
                "touchpoints_last_30d": 12
            },
            "business_data": {
                "customer_since_date": (datetime.now(UTC) - timedelta(days=200)).isoformat(),
                "roi_realized_percentage": 200
            },
            "health_data": {
                "health_score": 92
            }
        }

        result1 = await agent.process(state1)

        print(f"Advocacy Ready: {result1['advocacy_ready']}")
        print(f"Readiness Score: {result1['advocacy_readiness_score']}")
        print(f"Recommended Type: {result1['recommended_advocacy_type']}")
        print(f"Opportunities: {result1['advocacy_opportunities_count']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Not ready for advocacy
        print("\n\n" + "=" * 70)
        print("Test 2: Not Ready for Advocacy")
        print("-" * 70)

        state2 = create_initial_state(
            "Check advocacy readiness",
            context={
                "customer_id": "cust_standard_002",
                "customer_metadata": {
                    "tier": "standard",
                    "company_name": "StartupCo",
                    "industry": "retail"
                }
            }
        )
        state2["entities"] = {
            "engagement_data": {
                "nps_score": 6,
                "touchpoints_last_30d": 2
            },
            "business_data": {
                "customer_since_date": (datetime.now(UTC) - timedelta(days=20)).isoformat(),
                "roi_realized_percentage": 50
            },
            "health_data": {
                "health_score": 55
            }
        }

        result2 = await agent.process(state2)

        print(f"Advocacy Ready: {result2['advocacy_ready']}")
        print(f"Readiness Score: {result2['advocacy_readiness_score']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
