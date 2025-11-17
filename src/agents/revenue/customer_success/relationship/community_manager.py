"""
Community Manager Agent - TASK-2067

Manages customer community, facilitates peer discussions, organizes events,
and recognizes active contributors to build customer engagement and loyalty.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("community_manager", tier="revenue", category="customer_success")
class CommunityManagerAgent(BaseAgent):
    """
    Community Manager Agent.

    Manages customer community by:
    - Facilitating peer-to-peer discussions and knowledge sharing
    - Organizing community events and webinars
    - Recognizing and rewarding active contributors
    - Curating community content and best practices
    - Tracking community engagement metrics
    - Building customer connections and networks
    """

    # Community engagement levels
    ENGAGEMENT_LEVELS = {
        "superuser": {"activity_min": 50, "contributions_min": 10},
        "active": {"activity_min": 20, "contributions_min": 5},
        "regular": {"activity_min": 5, "contributions_min": 1},
        "lurker": {"activity_min": 1, "contributions_min": 0},
        "inactive": {"activity_min": 0, "contributions_min": 0}
    }

    # Community activities
    COMMUNITY_ACTIVITIES = [
        "discussion_posts",
        "question_answers",
        "best_practice_shares",
        "event_attendance",
        "content_creation",
        "peer_helping"
    ]

    # Event types
    EVENT_TYPES = {
        "webinar": {"frequency": "monthly", "target_attendance": 50},
        "workshop": {"frequency": "quarterly", "target_attendance": 30},
        "office_hours": {"frequency": "weekly", "target_attendance": 15},
        "user_conference": {"frequency": "annual", "target_attendance": 200},
        "virtual_meetup": {"frequency": "bi_weekly", "target_attendance": 25}
    }

    # Recognition programs
    RECOGNITION_PROGRAMS = [
        "Member of the Month",
        "Top Contributor Award",
        "Community Champion Badge",
        "Early Adopter Recognition",
        "Knowledge Sharer Award"
    ]

    def __init__(self):
        config = AgentConfig(
            name="community_manager",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
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
        Manage community engagement and activities.

        Args:
            state: Current agent state with community data

        Returns:
            Updated state with community management plan
        """
        self.logger.info("community_management_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        community_data = state.get("entities", {}).get("community_data", {})
        user_data = state.get("entities", {}).get("user_data", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})

        self.logger.debug(
            "community_management_details",
            customer_id=customer_id,
            community_active=community_data.get("is_active", False)
        )

        # Analyze community participation
        participation_analysis = self._analyze_community_participation(
            community_data,
            user_data,
            customer_metadata
        )

        # Identify top contributors
        top_contributors = self._identify_top_contributors(
            community_data,
            user_data
        )

        # Plan community events
        event_plan = self._plan_community_events(
            participation_analysis,
            customer_metadata
        )

        # Generate content ideas
        content_ideas = self._generate_community_content_ideas(
            community_data,
            engagement_data,
            customer_metadata
        )

        # Create recognition plan
        recognition_plan = self._create_recognition_plan(
            top_contributors,
            participation_analysis
        )

        # Create action plan
        action_plan = self._create_community_action_plan(
            participation_analysis,
            event_plan
        )

        # Format response
        response = self._format_community_report(
            participation_analysis,
            top_contributors,
            event_plan,
            content_ideas,
            recognition_plan,
            action_plan
        )

        state["agent_response"] = response
        state["community_engagement_level"] = participation_analysis["overall_engagement"]
        state["community_active_members"] = participation_analysis.get("active_members_count", 0)
        state["top_contributors_count"] = len(top_contributors)
        state["upcoming_events_count"] = len(event_plan.get("upcoming_events", []))
        state["response_confidence"] = 0.82
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "community_management_completed",
            customer_id=customer_id,
            engagement_level=participation_analysis["overall_engagement"],
            active_members=participation_analysis.get("active_members_count", 0)
        )

        return state

    def _analyze_community_participation(
        self,
        community_data: Dict[str, Any],
        user_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze community participation levels.

        Args:
            community_data: Community activity metrics
            user_data: User information
            customer_metadata: Customer profile data

        Returns:
            Community participation analysis
        """
        total_users = user_data.get("total_users", 0)
        community_members = community_data.get("community_members", 0)

        # Calculate participation rate
        if total_users > 0:
            participation_rate = int((community_members / total_users) * 100)
        else:
            participation_rate = 0

        # Categorize members by engagement level
        members_by_level = {
            "superuser": community_data.get("superuser_count", 0),
            "active": community_data.get("active_count", 0),
            "regular": community_data.get("regular_count", 0),
            "lurker": community_data.get("lurker_count", 0),
            "inactive": max(0, community_members - sum([
                community_data.get("superuser_count", 0),
                community_data.get("active_count", 0),
                community_data.get("regular_count", 0),
                community_data.get("lurker_count", 0)
            ]))
        }

        # Calculate engagement metrics
        total_posts = community_data.get("total_posts_last_30d", 0)
        total_questions = community_data.get("total_questions_last_30d", 0)
        total_answers = community_data.get("total_answers_last_30d", 0)

        # Determine overall engagement level
        active_members = members_by_level["superuser"] + members_by_level["active"]
        active_members_count = active_members

        if participation_rate >= 40 and active_members >= 5:
            overall_engagement = "thriving"
        elif participation_rate >= 25 and active_members >= 3:
            overall_engagement = "healthy"
        elif participation_rate >= 10 or active_members >= 1:
            overall_engagement = "developing"
        else:
            overall_engagement = "nascent"

        # Calculate growth
        previous_members = community_data.get("community_members_last_month", community_members)
        if previous_members > 0:
            growth_rate = int(((community_members - previous_members) / previous_members) * 100)
        else:
            growth_rate = 0

        return {
            "total_users": total_users,
            "community_members": community_members,
            "participation_rate": participation_rate,
            "active_members_count": active_members_count,
            "members_by_level": members_by_level,
            "overall_engagement": overall_engagement,
            "total_posts": total_posts,
            "total_questions": total_questions,
            "total_answers": total_answers,
            "answer_rate": int((total_answers / total_questions * 100)) if total_questions > 0 else 0,
            "growth_rate": growth_rate
        }

    def _identify_top_contributors(
        self,
        community_data: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify top community contributors."""
        contributors = community_data.get("top_contributors", [])

        if not contributors:
            # Generate mock data if not provided
            return []

        # Enrich with contribution details
        top_contributors = []
        for contributor in contributors[:10]:
            top_contributors.append({
                "name": contributor.get("name", "Unknown"),
                "email": contributor.get("email", ""),
                "activity_score": contributor.get("activity_score", 0),
                "posts": contributor.get("posts", 0),
                "answers": contributor.get("answers", 0),
                "helpful_votes": contributor.get("helpful_votes", 0),
                "engagement_level": self._determine_engagement_level(
                    contributor.get("activity_score", 0),
                    contributor.get("posts", 0) + contributor.get("answers", 0)
                )
            })

        # Sort by activity score
        top_contributors.sort(key=lambda x: x["activity_score"], reverse=True)

        return top_contributors

    def _determine_engagement_level(self, activity_score: int, contributions: int) -> str:
        """Determine engagement level for a user."""
        for level, thresholds in sorted(
            self.ENGAGEMENT_LEVELS.items(),
            key=lambda x: x[1]["activity_min"],
            reverse=True
        ):
            if (activity_score >= thresholds["activity_min"] and
                contributions >= thresholds["contributions_min"]):
                return level

        return "inactive"

    def _plan_community_events(
        self,
        participation_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Plan community events."""
        engagement = participation_analysis["overall_engagement"]
        tier = customer_metadata.get("tier", "standard")

        upcoming_events = []

        # Plan events based on engagement level and tier
        if engagement in ["thriving", "healthy"]:
            upcoming_events.append({
                "type": "webinar",
                "title": "Advanced Features Deep Dive",
                "target_date": (datetime.now(UTC) + timedelta(days=14)).isoformat(),
                "target_attendance": 50,
                "format": "virtual"
            })

            upcoming_events.append({
                "type": "office_hours",
                "title": "Weekly Community Office Hours",
                "target_date": (datetime.now(UTC) + timedelta(days=7)).isoformat(),
                "target_attendance": 15,
                "format": "virtual"
            })

        if tier in ["enterprise", "premium"]:
            upcoming_events.append({
                "type": "workshop",
                "title": "Best Practices Workshop",
                "target_date": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
                "target_attendance": 30,
                "format": "hybrid"
            })

        # Always include a virtual meetup opportunity
        upcoming_events.append({
            "type": "virtual_meetup",
            "title": "Community Connection Session",
            "target_date": (datetime.now(UTC) + timedelta(days=21)).isoformat(),
            "target_attendance": 25,
            "format": "virtual"
        })

        return {
            "upcoming_events": upcoming_events[:4],
            "events_planned": len(upcoming_events),
            "recommended_cadence": "2-3 events per month" if engagement in ["thriving", "healthy"] else "1 event per month"
        }

    def _generate_community_content_ideas(
        self,
        community_data: Dict[str, Any],
        engagement_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate content ideas for community."""
        content_ideas = []

        industry = customer_metadata.get("industry", "business")

        # Best practices content
        content_ideas.append({
            "type": "best_practice",
            "title": f"Top 10 Best Practices for {industry.title()}",
            "format": "guide",
            "author": "Community Contributors"
        })

        # Use case content
        content_ideas.append({
            "type": "use_case",
            "title": "Creative Ways Our Customers Use the Platform",
            "format": "showcase",
            "author": "Community Team"
        })

        # Q&A content
        content_ideas.append({
            "type": "faq",
            "title": "Most Asked Community Questions - Answered",
            "format": "article",
            "author": "Top Contributors"
        })

        # Tips and tricks
        content_ideas.append({
            "type": "tips",
            "title": "Weekly Pro Tips from Power Users",
            "format": "series",
            "author": "Superusers"
        })

        return content_ideas[:5]

    def _create_recognition_plan(
        self,
        top_contributors: List[Dict[str, Any]],
        participation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create recognition plan for contributors."""
        recognition_actions = []

        # Recognize top contributors
        if top_contributors:
            top_contributor = top_contributors[0]
            recognition_actions.append({
                "program": "Member of the Month",
                "recipient": top_contributor["name"],
                "achievement": f"{top_contributor['activity_score']} activity points, {top_contributor['answers']} helpful answers",
                "reward": "Featured spotlight, special badge, gift card"
            })

        # Milestone recognition
        if participation_analysis["community_members"] >= 50:
            recognition_actions.append({
                "program": "Community Milestone",
                "recipient": "All Members",
                "achievement": "Community reached 50+ members!",
                "reward": "Celebration webinar, exclusive content"
            })

        return {
            "recognition_actions": recognition_actions[:3],
            "programs_available": self.RECOGNITION_PROGRAMS,
            "next_recognition_date": (datetime.now(UTC) + timedelta(days=7)).isoformat()
        }

    def _create_community_action_plan(
        self,
        participation_analysis: Dict[str, Any],
        event_plan: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Create action plan for community management."""
        actions = []

        engagement = participation_analysis["overall_engagement"]

        if engagement == "nascent":
            actions.append({
                "action": "Launch community activation campaign to increase membership",
                "owner": "CSM + Community Team",
                "timeline": "Next 2 weeks",
                "priority": "high"
            })

        if participation_analysis["participation_rate"] < 20:
            actions.append({
                "action": "Send community invitation to all users",
                "owner": "CSM",
                "timeline": "This week",
                "priority": "high"
            })

        # Event planning
        if event_plan["upcoming_events"]:
            next_event = event_plan["upcoming_events"][0]
            actions.append({
                "action": f"Organize {next_event['type']}: {next_event['title']}",
                "owner": "Community Team",
                "timeline": f"By {datetime.fromisoformat(next_event['target_date'].replace('Z', '+00:00')).strftime('%b %d')}",
                "priority": "medium"
            })

        # Content creation
        actions.append({
            "action": "Curate and publish best practice content from community",
            "owner": "Community Manager",
            "timeline": "Bi-weekly",
            "priority": "medium"
        })

        # Recognition
        if participation_analysis["active_members_count"] > 0:
            actions.append({
                "action": "Recognize top contributors in next community update",
                "owner": "Community Manager",
                "timeline": "This month",
                "priority": "medium"
            })

        return actions[:5]

    def _format_community_report(
        self,
        participation_analysis: Dict[str, Any],
        top_contributors: List[Dict[str, Any]],
        event_plan: Dict[str, Any],
        content_ideas: List[Dict[str, str]],
        recognition_plan: Dict[str, Any],
        action_plan: List[Dict[str, str]]
    ) -> str:
        """Format community management report."""
        engagement = participation_analysis["overall_engagement"]

        engagement_emoji = {
            "thriving": "????",
            "healthy": "???",
            "developing": "????",
            "nascent": "????"
        }

        report = f"""**???? Community Management Report**

**Engagement Level:** {engagement.title()} {engagement_emoji.get(engagement, '???')}
**Community Members:** {participation_analysis['community_members']} ({participation_analysis['participation_rate']}% of users)
**Active Contributors:** {participation_analysis['active_members_count']}
**Growth Rate:** {participation_analysis['growth_rate']:+d}% vs last month

**Member Distribution:**
"""

        for level, count in participation_analysis["members_by_level"].items():
            if count > 0:
                report += f"- {level.title()}: {count}\n"

        # Activity metrics
        report += f"\n**???? Activity (Last 30 Days):**\n"
        report += f"- Posts: {participation_analysis['total_posts']}\n"
        report += f"- Questions: {participation_analysis['total_questions']}\n"
        report += f"- Answers: {participation_analysis['total_answers']}\n"
        report += f"- Answer Rate: {participation_analysis['answer_rate']}%\n"

        # Top contributors
        if top_contributors:
            report += f"\n**???? Top Contributors:**\n"
            for i, contributor in enumerate(top_contributors[:5], 1):
                level_emoji = "????" if contributor["engagement_level"] == "superuser" else "???"
                report += f"{i}. **{contributor['name']}** {level_emoji}\n"
                report += f"   - Activity Score: {contributor['activity_score']}\n"
                report += f"   - Contributions: {contributor['posts']} posts, {contributor['answers']} answers\n"

        # Upcoming events
        if event_plan["upcoming_events"]:
            report += f"\n**???? Upcoming Events ({event_plan['events_planned']}):**\n"
            for i, event in enumerate(event_plan["upcoming_events"], 1):
                event_date = datetime.fromisoformat(event['target_date'].replace('Z', '+00:00'))
                report += f"{i}. **{event['title']}** ({event['type'].title()})\n"
                report += f"   - Date: {event_date.strftime('%b %d, %Y')}\n"
                report += f"   - Target Attendance: {event['target_attendance']}\n"

        # Content ideas
        if content_ideas:
            report += "\n**???? Content Ideas:**\n"
            for i, idea in enumerate(content_ideas[:4], 1):
                report += f"{i}. {idea['title']} ({idea['format'].title()})\n"

        # Recognition
        if recognition_plan.get("recognition_actions"):
            report += "\n**???? Recognition Plan:**\n"
            for action in recognition_plan["recognition_actions"]:
                report += f"- **{action['program']}:** {action['recipient']}\n"
                report += f"  Achievement: {action['achievement']}\n"

        # Action plan
        if action_plan:
            report += "\n**??? Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = "????" if action["priority"] == "critical" else "????" if action["priority"] == "high" else "????"
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Community Manager Agent (TASK-2067)")
        print("=" * 70)

        agent = CommunityManagerAgent()

        # Test 1: Thriving community
        print("\n\nTest 1: Thriving Community")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze community engagement",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {
                    "tier": "enterprise",
                    "industry": "technology"
                }
            }
        )
        state1["entities"] = {
            "community_data": {
                "community_members": 85,
                "community_members_last_month": 75,
                "superuser_count": 5,
                "active_count": 12,
                "regular_count": 20,
                "lurker_count": 35,
                "total_posts_last_30d": 120,
                "total_questions_last_30d": 45,
                "total_answers_last_30d": 40,
                "top_contributors": [
                    {
                        "name": "Alice Champion",
                        "email": "alice@example.com",
                        "activity_score": 85,
                        "posts": 25,
                        "answers": 30,
                        "helpful_votes": 45
                    },
                    {
                        "name": "Bob Helper",
                        "email": "bob@example.com",
                        "activity_score": 65,
                        "posts": 15,
                        "answers": 20,
                        "helpful_votes": 30
                    }
                ]
            },
            "user_data": {
                "total_users": 100
            },
            "engagement_data": {}
        }

        result1 = await agent.process(state1)

        print(f"Engagement Level: {result1['community_engagement_level']}")
        print(f"Active Members: {result1['community_active_members']}")
        print(f"Top Contributors: {result1['top_contributors_count']}")
        print(f"Upcoming Events: {result1['upcoming_events_count']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Nascent community
        print("\n\n" + "=" * 70)
        print("Test 2: Nascent Community")
        print("-" * 70)

        state2 = create_initial_state(
            "Build community",
            context={
                "customer_id": "cust_growth_002",
                "customer_metadata": {
                    "tier": "growth",
                    "industry": "retail"
                }
            }
        )
        state2["entities"] = {
            "community_data": {
                "community_members": 5,
                "community_members_last_month": 3,
                "superuser_count": 0,
                "active_count": 1,
                "regular_count": 2,
                "lurker_count": 2,
                "total_posts_last_30d": 8,
                "total_questions_last_30d": 3,
                "total_answers_last_30d": 2,
                "top_contributors": []
            },
            "user_data": {
                "total_users": 50
            },
            "engagement_data": {}
        }

        result2 = await agent.process(state2)

        print(f"Engagement Level: {result2['community_engagement_level']}")
        print(f"Active Members: {result2['community_active_members']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
