"""
Executive Sponsor Agent - TASK-2062

Manages executive sponsor relationships, schedules executive check-ins,
and shares strategic updates to maintain C-level engagement and alignment.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("executive_sponsor", tier="revenue", category="customer_success")
class ExecutiveSponsorAgent(BaseAgent):
    """
    Executive Sponsor Agent.

    Manages executive-level relationships by:
    - Identifying and engaging executive sponsors
    - Scheduling regular executive check-ins
    - Preparing strategic business updates
    - Aligning on business objectives and outcomes
    - Escalating strategic opportunities
    - Building executive-to-executive relationships
    """

    # Executive engagement cadence by customer tier
    ENGAGEMENT_CADENCE = {
        "enterprise": {"frequency_days": 30, "format": "video_call", "duration_minutes": 30},
        "premium": {"frequency_days": 60, "format": "video_call", "duration_minutes": 20},
        "growth": {"frequency_days": 90, "format": "email_update", "duration_minutes": 0},
        "standard": {"frequency_days": 180, "format": "email_update", "duration_minutes": 0}
    }

    # Executive sponsor levels
    SPONSOR_LEVELS = {
        "c_suite": {"priority": 1, "influence": "very_high"},
        "vp_level": {"priority": 2, "influence": "high"},
        "director": {"priority": 3, "influence": "medium"},
        "manager": {"priority": 4, "influence": "low"}
    }

    # Communication topics
    STRATEGIC_TOPICS = [
        "Business value & ROI realization",
        "Strategic roadmap alignment",
        "Executive success stories",
        "Industry trends & insights",
        "Partnership opportunities",
        "Innovation & future capabilities"
    ]

    def __init__(self):
        config = AgentConfig(
            name="executive_sponsor",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.3,
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
        Manage executive sponsor relationship.

        Args:
            state: Current agent state with customer data

        Returns:
            Updated state with executive engagement plan
        """
        self.logger.info("executive_sponsor_management_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        business_data = state.get("entities", {}).get("business_data", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})
        contact_data = state.get("entities", {}).get("contact_data", {})

        self.logger.debug(
            "executive_sponsor_details",
            customer_id=customer_id,
            tier=customer_metadata.get("tier", "standard"),
            has_sponsor=bool(contact_data.get("executive_sponsor"))
        )

        # Identify or validate executive sponsor
        sponsor_analysis = self._analyze_executive_sponsor(
            contact_data,
            customer_metadata,
            business_data
        )

        # Plan executive engagement
        engagement_plan = self._plan_executive_engagement(
            sponsor_analysis,
            customer_metadata,
            engagement_data
        )

        # Prepare strategic update
        strategic_update = self._prepare_strategic_update(
            business_data,
            engagement_data,
            customer_metadata
        )

        # Generate action plan
        action_plan = self._generate_engagement_action_plan(
            sponsor_analysis,
            engagement_plan
        )

        # Format response
        response = self._format_executive_sponsor_report(
            sponsor_analysis,
            engagement_plan,
            strategic_update,
            action_plan
        )

        state["agent_response"] = response
        state["has_executive_sponsor"] = sponsor_analysis.get("sponsor_identified", False)
        state["sponsor_level"] = sponsor_analysis.get("sponsor_level", "none")
        state["executive_engagement_status"] = engagement_plan["status"]
        state["days_since_exec_contact"] = engagement_plan.get("days_since_last_contact", 999)
        state["response_confidence"] = 0.84
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "executive_sponsor_management_completed",
            customer_id=customer_id,
            sponsor_identified=sponsor_analysis.get("sponsor_identified", False),
            engagement_status=engagement_plan["status"]
        )

        return state

    def _analyze_executive_sponsor(
        self,
        contact_data: Dict[str, Any],
        customer_metadata: Dict[str, Any],
        business_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze executive sponsor relationship.

        Args:
            contact_data: Contact information including sponsors
            customer_metadata: Customer profile data
            business_data: Business and contract data

        Returns:
            Executive sponsor analysis
        """
        # Check if executive sponsor is identified
        sponsor = contact_data.get("executive_sponsor", {})
        sponsor_identified = bool(sponsor.get("name"))

        if sponsor_identified:
            sponsor_level = self._determine_sponsor_level(sponsor.get("title", ""))
            sponsor_tenure_days = self._calculate_sponsor_tenure(sponsor.get("start_date"))
            sponsor_engagement = sponsor.get("engagement_level", "low")
            last_contact = sponsor.get("last_contact_date")
        else:
            sponsor_level = "none"
            sponsor_tenure_days = 0
            sponsor_engagement = "none"
            last_contact = None

        # Assess sponsor relationship health
        relationship_health = self._assess_sponsor_relationship_health(
            sponsor_identified,
            sponsor_engagement,
            last_contact,
            business_data
        )

        # Identify potential sponsors if none exists
        potential_sponsors = []
        if not sponsor_identified:
            potential_sponsors = self._identify_potential_sponsors(contact_data)

        return {
            "sponsor_identified": sponsor_identified,
            "sponsor_name": sponsor.get("name", "Not identified"),
            "sponsor_title": sponsor.get("title", "N/A"),
            "sponsor_level": sponsor_level,
            "sponsor_tenure_days": sponsor_tenure_days,
            "sponsor_engagement": sponsor_engagement,
            "last_contact_date": last_contact,
            "relationship_health": relationship_health,
            "potential_sponsors": potential_sponsors,
            "requires_identification": not sponsor_identified
        }

    def _determine_sponsor_level(self, title: str) -> str:
        """Determine executive sponsor level from title."""
        title_lower = title.lower()

        if any(term in title_lower for term in ["ceo", "cto", "cfo", "coo", "chief", "president"]):
            return "c_suite"
        elif any(term in title_lower for term in ["vp", "vice president"]):
            return "vp_level"
        elif "director" in title_lower:
            return "director"
        elif "manager" in title_lower:
            return "manager"
        else:
            return "director"  # Default assumption

    def _calculate_sponsor_tenure(self, start_date: Optional[str]) -> int:
        """Calculate days since sponsor relationship started."""
        if not start_date:
            return 0

        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            return (datetime.utcnow() - start).days
        except:
            return 0

    def _assess_sponsor_relationship_health(
        self,
        sponsor_identified: bool,
        engagement_level: str,
        last_contact: Optional[str],
        business_data: Dict[str, Any]
    ) -> str:
        """Assess health of executive sponsor relationship."""
        if not sponsor_identified:
            return "missing"

        # Calculate days since last contact
        if last_contact:
            try:
                last_contact_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                days_since_contact = (datetime.utcnow() - last_contact_date).days
            except:
                days_since_contact = 999
        else:
            days_since_contact = 999

        # Assess health based on engagement and recency
        if engagement_level == "high" and days_since_contact < 30:
            return "excellent"
        elif engagement_level in ["medium", "high"] and days_since_contact < 60:
            return "good"
        elif days_since_contact < 90:
            return "needs_attention"
        else:
            return "at_risk"

    def _identify_potential_sponsors(self, contact_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify potential executive sponsors from contacts."""
        contacts = contact_data.get("all_contacts", [])
        potential = []

        for contact in contacts:
            title = contact.get("title", "")
            level = self._determine_sponsor_level(title)

            if level in ["c_suite", "vp_level"]:
                potential.append({
                    "name": contact.get("name", "Unknown"),
                    "title": title,
                    "level": level,
                    "department": contact.get("department", "Unknown"),
                    "priority": self.SPONSOR_LEVELS[level]["priority"]
                })

        # Sort by priority
        potential.sort(key=lambda x: x["priority"])
        return potential[:3]

    def _plan_executive_engagement(
        self,
        sponsor_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any],
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Plan executive engagement strategy."""
        tier = customer_metadata.get("tier", "standard")
        cadence_config = self.ENGAGEMENT_CADENCE.get(tier, self.ENGAGEMENT_CADENCE["standard"])

        last_contact = sponsor_analysis.get("last_contact_date")
        if last_contact:
            try:
                last_contact_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                days_since_last_contact = (datetime.utcnow() - last_contact_date).days
            except:
                days_since_last_contact = cadence_config["frequency_days"] + 1
        else:
            days_since_last_contact = cadence_config["frequency_days"] + 1

        # Determine next contact date
        if last_contact:
            try:
                next_contact = last_contact_date + timedelta(days=cadence_config["frequency_days"])
            except:
                next_contact = datetime.utcnow() + timedelta(days=cadence_config["frequency_days"])
        else:
            next_contact = datetime.utcnow() + timedelta(days=7)  # Schedule soon if new

        days_until_next_contact = (next_contact - datetime.utcnow()).days

        # Determine status
        if not sponsor_analysis["sponsor_identified"]:
            status = "needs_identification"
        elif days_since_last_contact > cadence_config["frequency_days"] * 1.5:
            status = "overdue"
        elif days_until_next_contact <= 7:
            status = "upcoming"
        else:
            status = "scheduled"

        return {
            "status": status,
            "next_contact_date": next_contact.isoformat(),
            "days_until_next_contact": days_until_next_contact,
            "days_since_last_contact": days_since_last_contact,
            "recommended_format": cadence_config["format"],
            "recommended_duration": cadence_config["duration_minutes"],
            "cadence_days": cadence_config["frequency_days"]
        }

    def _prepare_strategic_update(
        self,
        business_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare strategic update for executive."""
        # Business value metrics
        contract_value = business_data.get("contract_value", 0)
        roi_realized = business_data.get("roi_realized_percentage", 0)

        # Key talking points
        talking_points = []

        if roi_realized > 100:
            talking_points.append(f"ROI Achievement: {roi_realized}% return on investment realized")

        nps = engagement_data.get("nps_score", 0)
        if nps >= 8:
            talking_points.append(f"Strong satisfaction: NPS score of {nps}/10")

        talking_points.append("Platform adoption progressing across departments")

        # Strategic initiatives
        initiatives = [
            "Expanding platform usage to additional teams",
            "Exploring advanced feature adoption opportunities",
            "Aligning on strategic roadmap priorities"
        ]

        return {
            "talking_points": talking_points,
            "strategic_initiatives": initiatives[:3],
            "business_value_focus": f"${contract_value:,} investment delivering measurable results",
            "recommended_topics": self.STRATEGIC_TOPICS[:4]
        }

    def _generate_engagement_action_plan(
        self,
        sponsor_analysis: Dict[str, Any],
        engagement_plan: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate action plan for executive engagement."""
        actions = []

        if sponsor_analysis["requires_identification"]:
            actions.append({
                "action": "Identify and engage executive sponsor",
                "owner": "VP Customer Success",
                "timeline": "Within 2 weeks",
                "priority": "critical"
            })

            if sponsor_analysis.get("potential_sponsors"):
                potential = sponsor_analysis["potential_sponsors"][0]
                actions.append({
                    "action": f"Reach out to {potential['name']} ({potential['title']}) as potential sponsor",
                    "owner": "CSM + Account Executive",
                    "timeline": "This week",
                    "priority": "high"
                })

        status = engagement_plan["status"]

        if status == "overdue":
            actions.append({
                "action": "Schedule urgent executive check-in call",
                "owner": "CSM",
                "timeline": "Within 3 days",
                "priority": "high"
            })

        if status == "upcoming":
            actions.append({
                "action": "Prepare and send executive update",
                "owner": "CSM",
                "timeline": "Before next contact date",
                "priority": "medium"
            })

        actions.append({
            "action": "Share relevant industry insights and success stories",
            "owner": "CSM",
            "timeline": "Quarterly",
            "priority": "medium"
        })

        if sponsor_analysis.get("relationship_health") in ["needs_attention", "at_risk"]:
            actions.append({
                "action": "Strengthen executive relationship through strategic value discussion",
                "owner": "VP Customer Success + Exec Sponsor",
                "timeline": "Within 30 days",
                "priority": "high"
            })

        return actions[:5]

    def _format_executive_sponsor_report(
        self,
        sponsor_analysis: Dict[str, Any],
        engagement_plan: Dict[str, Any],
        strategic_update: Dict[str, Any],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format executive sponsor management report."""
        health_emoji = {
            "excellent": "????",
            "good": "???",
            "needs_attention": "??????",
            "at_risk": "????",
            "missing": "???"
        }

        status_emoji = {
            "needs_identification": "????",
            "overdue": "????",
            "upcoming": "????",
            "scheduled": "???"
        }

        report = f"""**???? Executive Sponsor Relationship Management**

**Sponsor Status:** {sponsor_analysis['sponsor_name']}
**Title:** {sponsor_analysis['sponsor_title']}
**Level:** {sponsor_analysis['sponsor_level'].replace('_', ' ').title()}
**Relationship Health:** {sponsor_analysis['relationship_health'].replace('_', ' ').title()} {health_emoji.get(sponsor_analysis['relationship_health'], '???')}

**???? Engagement Status:** {engagement_plan['status'].replace('_', ' ').title()} {status_emoji.get(engagement_plan['status'], '???')}
"""

        if engagement_plan.get("days_since_last_contact", 999) < 999:
            report += f"**Last Contact:** {engagement_plan['days_since_last_contact']} days ago\n"

        report += f"**Next Contact:** {engagement_plan['days_until_next_contact']} days\n"
        report += f"**Format:** {engagement_plan['recommended_format'].replace('_', ' ').title()}\n"

        if engagement_plan["recommended_duration"] > 0:
            report += f"**Duration:** {engagement_plan['recommended_duration']} minutes\n"

        # Potential sponsors if needed
        if sponsor_analysis.get("potential_sponsors"):
            report += "\n**???? Potential Executive Sponsors:**\n"
            for i, potential in enumerate(sponsor_analysis["potential_sponsors"], 1):
                report += f"{i}. **{potential['name']}** - {potential['title']}\n"
                report += f"   Level: {potential['level'].replace('_', ' ').title()}, "
                report += f"Department: {potential['department']}\n"

        # Strategic update
        report += "\n**???? Strategic Update Topics:**\n"
        for point in strategic_update["talking_points"]:
            report += f"- {point}\n"

        report += "\n**???? Strategic Discussion Areas:**\n"
        for i, topic in enumerate(strategic_update["recommended_topics"][:4], 1):
            report += f"{i}. {topic}\n"

        # Action plan
        if action_plan:
            report += "\n**??? Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        if sponsor_analysis.get("sponsor_tenure_days", 0) > 365:
            report += f"\n**???? Note:** Long-standing executive relationship ({sponsor_analysis['sponsor_tenure_days']} days) - maintain strategic value focus"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Executive Sponsor Agent (TASK-2062)")
        print("=" * 70)

        agent = ExecutiveSponsorAgent()

        # Test 1: Active executive sponsor relationship
        print("\n\nTest 1: Active Executive Sponsor")
        print("-" * 70)

        state1 = create_initial_state(
            "Manage executive sponsor relationship",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {
                    "tier": "enterprise",
                    "company_name": "TechCorp Inc"
                }
            }
        )
        state1["entities"] = {
            "contact_data": {
                "executive_sponsor": {
                    "name": "Sarah Johnson",
                    "title": "Chief Technology Officer",
                    "start_date": (datetime.utcnow() - timedelta(days=400)).isoformat(),
                    "engagement_level": "high",
                    "last_contact_date": (datetime.utcnow() - timedelta(days=20)).isoformat()
                },
                "all_contacts": []
            },
            "business_data": {
                "contract_value": 120000,
                "roi_realized_percentage": 150
            },
            "engagement_data": {
                "nps_score": 9
            }
        }

        result1 = await agent.process(state1)

        print(f"Has Executive Sponsor: {result1['has_executive_sponsor']}")
        print(f"Sponsor Level: {result1['sponsor_level']}")
        print(f"Engagement Status: {result1['executive_engagement_status']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Missing executive sponsor
        print("\n\n" + "=" * 70)
        print("Test 2: Missing Executive Sponsor")
        print("-" * 70)

        state2 = create_initial_state(
            "Identify executive sponsor",
            context={
                "customer_id": "cust_growth_002",
                "customer_metadata": {
                    "tier": "growth",
                    "company_name": "StartupCo"
                }
            }
        )
        state2["entities"] = {
            "contact_data": {
                "executive_sponsor": {},
                "all_contacts": [
                    {"name": "Mike Chen", "title": "VP of Engineering", "department": "Engineering"},
                    {"name": "Lisa Park", "title": "Director of Operations", "department": "Operations"},
                    {"name": "John Smith", "title": "CEO", "department": "Executive"}
                ]
            },
            "business_data": {
                "contract_value": 35000,
                "roi_realized_percentage": 80
            },
            "engagement_data": {
                "nps_score": 7
            }
        }

        result2 = await agent.process(state2)

        print(f"Has Executive Sponsor: {result2['has_executive_sponsor']}")
        print(f"Engagement Status: {result2['executive_engagement_status']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:600]}...")

    asyncio.run(test())
