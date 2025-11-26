"""
Champion Cultivator Agent - TASK-2063

Identifies and cultivates internal champions within customer organizations,
empowers them with resources, and builds champion networks to drive adoption.
"""

from typing import Any

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("champion_cultivator", tier="revenue", category="customer_success")
class ChampionCultivatorAgent(BaseAgent):
    """
    Champion Cultivator Agent.

    Builds and nurtures customer champions by:
    - Identifying potential internal champions
    - Assessing champion engagement and influence
    - Empowering champions with resources and training
    - Building champion networks and communities
    - Tracking champion advocacy activities
    - Leveraging champions for adoption and expansion
    """

    # Champion characteristics and scoring
    CHAMPION_TRAITS = {
        "product_expertise": {"weight": 25, "threshold": 70},
        "organizational_influence": {"weight": 25, "threshold": 60},
        "engagement_level": {"weight": 20, "threshold": 75},
        "advocacy_activity": {"weight": 20, "threshold": 50},
        "peer_training": {"weight": 10, "threshold": 40},
    }

    # Champion tiers
    CHAMPION_TIERS = {
        "superstar": {
            "score_min": 85,
            "benefits": "Premium support, early access, speaking opportunities",
        },
        "active": {"score_min": 70, "benefits": "Advanced training, community leadership"},
        "emerging": {"score_min": 50, "benefits": "Champion enablement program"},
        "potential": {"score_min": 30, "benefits": "Basic resources and support"},
    }

    # Champion activities
    CHAMPION_ACTIVITIES = [
        "peer_training",
        "use_case_documentation",
        "best_practice_sharing",
        "feature_evangelism",
        "new_user_onboarding",
        "feedback_provision",
    ]

    def __init__(self):
        config = AgentConfig(
            name="champion_cultivator",
            type=AgentType.SPECIALIST,
            temperature=0.4,
            max_tokens=700,
            capabilities=[AgentCapability.CONTEXT_AWARE, AgentCapability.KB_SEARCH],
            kb_category="customer_success",
            tier="revenue",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Identify and cultivate customer champions.

        Args:
            state: Current agent state with user data

        Returns:
            Updated state with champion analysis and cultivation plan
        """
        self.logger.info("champion_cultivation_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        customer_metadata = state.get("customer_metadata", {})
        user_data = state.get("entities", {}).get("user_data", {})
        engagement_data = state.get("entities", {}).get("engagement_data", {})
        usage_data = state.get("entities", {}).get("usage_data", {})

        self.logger.debug(
            "champion_cultivation_details",
            customer_id=customer_id,
            total_users=len(user_data.get("users", [])),
        )

        # Identify champions
        champion_analysis = self._identify_champions(user_data, engagement_data, usage_data)

        # Assess champion network strength
        network_strength = self._assess_champion_network(champion_analysis, customer_metadata)

        # Create cultivation plan
        cultivation_plan = self._create_cultivation_plan(champion_analysis, network_strength)

        # Generate empowerment resources
        empowerment_resources = self._generate_empowerment_resources(champion_analysis)

        # Create action plan
        action_plan = self._create_champion_action_plan(champion_analysis, network_strength)

        # Format response
        response = self._format_champion_report(
            champion_analysis,
            network_strength,
            cultivation_plan,
            empowerment_resources,
            action_plan,
        )

        state["agent_response"] = response
        state["champion_count"] = champion_analysis["total_champions"]
        state["superstar_champion_count"] = champion_analysis.get("superstar_count", 0)
        state["network_strength"] = network_strength["overall_strength"]
        state["champion_coverage"] = network_strength.get("coverage_percentage", 0)
        state["response_confidence"] = 0.85
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "champion_cultivation_completed",
            customer_id=customer_id,
            total_champions=champion_analysis["total_champions"],
            network_strength=network_strength["overall_strength"],
        )

        return state

    def _identify_champions(
        self, user_data: dict[str, Any], engagement_data: dict[str, Any], usage_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Identify potential and active champions.

        Args:
            user_data: Individual user information
            engagement_data: User engagement metrics
            usage_data: Product usage data

        Returns:
            Champion identification analysis
        """
        users = user_data.get("users", [])
        champions = []
        champions_by_tier = {tier: [] for tier in self.CHAMPION_TIERS}
        champions_by_tier["none"] = []

        for user in users:
            champion_score = self._calculate_champion_score(user, engagement_data, usage_data)
            champion_tier = self._determine_champion_tier(champion_score)

            champion_data = {
                "name": user.get("name", "Unknown"),
                "email": user.get("email", ""),
                "department": user.get("department", "Unknown"),
                "title": user.get("title", "User"),
                "champion_score": champion_score,
                "champion_tier": champion_tier,
                "strengths": self._identify_champion_strengths(user, champion_score),
                "activities": self._track_champion_activities(user),
            }

            if champion_tier != "none":
                champions.append(champion_data)
                champions_by_tier[champion_tier].append(champion_data)

        # Sort champions by score
        champions.sort(key=lambda x: x["champion_score"], reverse=True)

        return {
            "total_champions": len(champions),
            "champions": champions[:10],  # Top 10
            "champions_by_tier": champions_by_tier,
            "superstar_count": len(champions_by_tier["superstar"]),
            "active_count": len(champions_by_tier["active"]),
            "emerging_count": len(champions_by_tier["emerging"]),
            "potential_count": len(champions_by_tier["potential"]),
            "total_users": len(users),
            "champion_percentage": int(len(champions) / len(users) * 100) if users else 0,
        }

    def _calculate_champion_score(
        self, user: dict[str, Any], engagement_data: dict[str, Any], usage_data: dict[str, Any]
    ) -> int:
        """Calculate champion score for a user (0-100)."""
        score = 0

        # Product expertise (0-25)
        login_frequency = user.get("login_frequency_per_week", 0)
        features_used = len(user.get("features_used", []))
        expertise_score = min((login_frequency / 5) * 15 + (features_used / 8) * 10, 25)
        score += expertise_score

        # Organizational influence (0-25)
        is_manager = any(
            term in user.get("title", "").lower() for term in ["manager", "director", "vp", "lead"]
        )
        has_team = user.get("team_size", 0) > 3
        influence_score = 15 if is_manager else 5
        influence_score += 10 if has_team else 0
        score += min(influence_score, 25)

        # Engagement level (0-20)
        support_interactions = user.get("support_interactions", 0)
        feature_requests = user.get("feature_requests", 0)
        engagement_score = min(support_interactions * 2 + feature_requests * 3, 20)
        score += engagement_score

        # Advocacy activity (0-20)
        peer_assists = user.get("peer_assists", 0)
        training_delivered = user.get("training_sessions_delivered", 0)
        advocacy_score = min(peer_assists * 2 + training_delivered * 5, 20)
        score += advocacy_score

        # Peer training (0-10)
        training_score = min(user.get("peer_training_hours", 0) * 2, 10)
        score += training_score

        return min(int(score), 100)

    def _determine_champion_tier(self, score: int) -> str:
        """Determine champion tier from score."""
        for tier, config in sorted(
            self.CHAMPION_TIERS.items(), key=lambda x: x[1]["score_min"], reverse=True
        ):
            if score >= config["score_min"]:
                return tier
        return "none"

    def _identify_champion_strengths(self, user: dict[str, Any], score: int) -> list[str]:
        """Identify specific strengths of a champion."""
        strengths = []

        if user.get("login_frequency_per_week", 0) >= 4:
            strengths.append("High product engagement")

        if len(user.get("features_used", [])) >= 7:
            strengths.append("Broad feature knowledge")

        if user.get("peer_assists", 0) >= 5:
            strengths.append("Active peer helper")

        if any(term in user.get("title", "").lower() for term in ["manager", "director", "vp"]):
            strengths.append("Organizational influence")

        if user.get("training_sessions_delivered", 0) > 0:
            strengths.append("Training delivery experience")

        return strengths[:3]

    def _track_champion_activities(self, user: dict[str, Any]) -> list[str]:
        """Track champion activities."""
        activities = []

        if user.get("peer_assists", 0) > 0:
            activities.append("peer_training")

        if user.get("feature_requests", 0) > 0:
            activities.append("feedback_provision")

        if user.get("training_sessions_delivered", 0) > 0:
            activities.append("new_user_onboarding")

        return activities

    def _assess_champion_network(
        self, champion_analysis: dict[str, Any], customer_metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess strength of champion network."""
        total_users = champion_analysis["total_users"]
        total_champions = champion_analysis["total_champions"]
        superstar_count = champion_analysis["superstar_count"]

        # Calculate coverage
        coverage_percentage = (total_champions / total_users * 100) if total_users > 0 else 0

        # Assess department coverage
        champions = champion_analysis["champions"]
        departments_covered = len({c["department"] for c in champions})

        # Determine overall network strength
        if superstar_count >= 2 and coverage_percentage >= 15:
            overall_strength = "excellent"
        elif total_champions >= 3 and coverage_percentage >= 10:
            overall_strength = "good"
        elif total_champions >= 1:
            overall_strength = "developing"
        else:
            overall_strength = "weak"

        # Identify gaps
        gaps = []
        if superstar_count == 0:
            gaps.append("No superstar champions - need to elevate top performers")

        if coverage_percentage < 10:
            gaps.append(f"Low champion coverage ({int(coverage_percentage)}%) - expand network")

        if departments_covered < 2:
            gaps.append("Limited department coverage - recruit cross-functional champions")

        return {
            "overall_strength": overall_strength,
            "coverage_percentage": int(coverage_percentage),
            "departments_covered": departments_covered,
            "network_gaps": gaps,
            "growth_potential": "high" if coverage_percentage < 20 else "medium",
        }

    def _create_cultivation_plan(
        self, champion_analysis: dict[str, Any], network_strength: dict[str, Any]
    ) -> dict[str, Any]:
        """Create champion cultivation plan."""
        champion_analysis["champions"]

        plan = {
            "focus_areas": [],
            "recruitment_targets": 0,
            "development_programs": [],
            "recognition_opportunities": [],
        }

        # Determine focus areas
        if champion_analysis["superstar_count"] > 0:
            plan["focus_areas"].append("Leverage superstar champions for speaking and advocacy")

        if champion_analysis["emerging_count"] >= 3:
            plan["focus_areas"].append("Develop emerging champions through advanced training")

        if network_strength["overall_strength"] in ["weak", "developing"]:
            plan["focus_areas"].append(
                "Expand champion network through identification and recruitment"
            )

        # Recruitment targets
        target_coverage = 15  # Target 15% champion coverage
        current_coverage = network_strength["coverage_percentage"]
        if current_coverage < target_coverage:
            gap_champions = int(
                (target_coverage - current_coverage) / 100 * champion_analysis["total_users"]
            )
            plan["recruitment_targets"] = max(gap_champions, 2)

        # Development programs
        if champion_analysis["active_count"] + champion_analysis["emerging_count"] >= 3:
            plan["development_programs"].append("Monthly champion office hours")
            plan["development_programs"].append("Advanced feature certification program")

        # Recognition opportunities
        if champion_analysis["superstar_count"] > 0:
            plan["recognition_opportunities"].append("Customer spotlight in newsletter")
            plan["recognition_opportunities"].append("Invite to speak at user conference")

        return plan

    def _generate_empowerment_resources(
        self, champion_analysis: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Generate resources to empower champions."""
        resources = {
            "training_materials": [
                "Advanced feature training videos",
                "Best practices playbook",
                "Use case library and templates",
                "Admin certification program",
            ],
            "advocacy_tools": [
                "Peer training presentation deck",
                "ROI calculator and templates",
                "Feature demonstration scripts",
                "Success story examples",
            ],
            "recognition_benefits": [
                "Champion badge and certificate",
                "Early access to new features",
                "Direct line to product team",
                "Quarterly champion webinars",
            ],
            "community_access": [
                "Private champion Slack channel",
                "Monthly champion roundtables",
                "Exclusive product roadmap previews",
                "Champion-only events",
            ],
        }

        return resources

    def _create_champion_action_plan(
        self, champion_analysis: dict[str, Any], network_strength: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Create action plan for champion cultivation."""
        actions = []

        # Recruit new champions
        if champion_analysis["champion_percentage"] < 15:
            actions.append(
                {
                    "action": "Identify and recruit 3-5 new champion candidates",
                    "owner": "CSM",
                    "timeline": "Next 30 days",
                    "priority": "high",
                }
            )

        # Engage existing champions
        if champion_analysis["total_champions"] > 0:
            actions.append(
                {
                    "action": "Send champion enablement resources to active champions",
                    "owner": "CSM",
                    "timeline": "This week",
                    "priority": "medium",
                }
            )

        # Recognize superstar champions
        if champion_analysis["superstar_count"] > 0:
            actions.append(
                {
                    "action": "Schedule 1:1 with superstar champions for strategic partnership",
                    "owner": "CSM + CS Manager",
                    "timeline": "Next 2 weeks",
                    "priority": "high",
                }
            )

        # Build community
        if champion_analysis["total_champions"] >= 3:
            actions.append(
                {
                    "action": "Launch champion community channel or group",
                    "owner": "CSM",
                    "timeline": "Next 30 days",
                    "priority": "medium",
                }
            )

        # Training and development
        if champion_analysis["emerging_count"] >= 2:
            actions.append(
                {
                    "action": "Invite emerging champions to advanced training session",
                    "owner": "CSM + Training Team",
                    "timeline": "Next quarter",
                    "priority": "medium",
                }
            )

        return actions[:5]

    def _format_champion_report(
        self,
        champion_analysis: dict[str, Any],
        network_strength: dict[str, Any],
        cultivation_plan: dict[str, Any],
        empowerment_resources: dict[str, list[str]],
        action_plan: list[dict[str, str]],
    ) -> str:
        """Format champion cultivation report."""
        strength_emoji = {
            "excellent": "????",
            "good": "???",
            "developing": "????",
            "weak": "??????",
        }

        report = f"""**???? Champion Cultivation Analysis**

**Network Strength:** {network_strength["overall_strength"].title()} {strength_emoji.get(network_strength["overall_strength"], "???")}
**Total Champions:** {champion_analysis["total_champions"]} ({champion_analysis["champion_percentage"]}% of users)
**Champion Coverage:** {network_strength["coverage_percentage"]}% across {network_strength["departments_covered"]} departments

**Champions by Tier:**
- ???? Superstar: {champion_analysis["superstar_count"]}
- ??? Active: {champion_analysis["active_count"]}
- ???? Emerging: {champion_analysis["emerging_count"]}
- ???? Potential: {champion_analysis["potential_count"]}
"""

        # Top champions
        if champion_analysis["champions"]:
            report += "\n**???? Top Champions:**\n"
            for i, champion in enumerate(champion_analysis["champions"][:5], 1):
                tier_emoji = (
                    "????"
                    if champion["champion_tier"] == "superstar"
                    else "???"
                    if champion["champion_tier"] == "active"
                    else "????"
                )
                report += f"{i}. **{champion['name']}** {tier_emoji}\n"
                report += f"   - {champion['title']}, {champion['department']}\n"
                report += f"   - Score: {champion['champion_score']}/100\n"
                if champion.get("strengths"):
                    report += f"   - Strengths: {', '.join(champion['strengths'])}\n"

        # Network gaps
        if network_strength.get("network_gaps"):
            report += "\n**?????? Network Gaps:**\n"
            for gap in network_strength["network_gaps"]:
                report += f"- {gap}\n"

        # Cultivation plan
        report += "\n**???? Cultivation Focus:**\n"
        for focus in cultivation_plan["focus_areas"][:3]:
            report += f"- {focus}\n"

        if cultivation_plan["recruitment_targets"] > 0:
            report += f"\n**???? Recruitment Target:** Identify {cultivation_plan['recruitment_targets']} additional champions\n"

        # Empowerment resources
        report += "\n**???? Champion Empowerment Resources:**\n"
        report += "**Training:** "
        report += ", ".join(empowerment_resources["training_materials"][:3])
        report += "\n**Advocacy Tools:** "
        report += ", ".join(empowerment_resources["advocacy_tools"][:3])

        # Action plan
        if action_plan:
            report += "\n\n**??? Action Plan:**\n"
            for i, action in enumerate(action_plan, 1):
                priority_icon = (
                    "????"
                    if action["priority"] == "critical"
                    else "????"
                    if action["priority"] == "high"
                    else "????"
                )
                report += f"{i}. **{action['action']}** {priority_icon}\n"
                report += f"   - Owner: {action['owner']}\n"
                report += f"   - Timeline: {action['timeline']}\n"

        return report


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Champion Cultivator Agent (TASK-2063)")
        print("=" * 70)

        agent = ChampionCultivatorAgent()

        # Test 1: Strong champion network
        print("\n\nTest 1: Strong Champion Network")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze champion network",
            context={
                "customer_id": "cust_enterprise_001",
                "customer_metadata": {"tier": "enterprise"},
            },
        )
        state1["entities"] = {
            "user_data": {
                "users": [
                    {
                        "name": "Alice Champion",
                        "email": "alice@example.com",
                        "department": "Engineering",
                        "title": "Engineering Manager",
                        "login_frequency_per_week": 5,
                        "features_used": [
                            "analytics",
                            "automation",
                            "api",
                            "reporting",
                            "dashboards",
                            "integrations",
                            "workflows",
                            "collaboration",
                        ],
                        "team_size": 8,
                        "peer_assists": 12,
                        "training_sessions_delivered": 3,
                        "feature_requests": 5,
                        "support_interactions": 8,
                        "peer_training_hours": 6,
                    },
                    {
                        "name": "Bob Helper",
                        "email": "bob@example.com",
                        "department": "Sales",
                        "title": "Sales Operations Lead",
                        "login_frequency_per_week": 4,
                        "features_used": [
                            "reporting",
                            "dashboards",
                            "analytics",
                            "automation",
                            "api",
                        ],
                        "team_size": 5,
                        "peer_assists": 8,
                        "training_sessions_delivered": 1,
                        "feature_requests": 3,
                        "support_interactions": 5,
                        "peer_training_hours": 3,
                    },
                    {
                        "name": "Carol User",
                        "email": "carol@example.com",
                        "department": "Marketing",
                        "title": "Marketing Coordinator",
                        "login_frequency_per_week": 2,
                        "features_used": ["reporting", "dashboards"],
                        "team_size": 0,
                        "peer_assists": 0,
                        "training_sessions_delivered": 0,
                        "feature_requests": 0,
                        "support_interactions": 2,
                        "peer_training_hours": 0,
                    },
                ]
            },
            "engagement_data": {},
            "usage_data": {},
        }

        result1 = await agent.process(state1)

        print(f"Champion Count: {result1['champion_count']}")
        print(f"Superstar Champions: {result1['superstar_champion_count']}")
        print(f"Network Strength: {result1['network_strength']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Weak champion network
        print("\n\n" + "=" * 70)
        print("Test 2: Weak Champion Network")
        print("-" * 70)

        state2 = create_initial_state(
            "Build champion network",
            context={"customer_id": "cust_growth_002", "customer_metadata": {"tier": "growth"}},
        )
        state2["entities"] = {
            "user_data": {
                "users": [
                    {
                        "name": "Dave User",
                        "email": "dave@example.com",
                        "department": "Operations",
                        "title": "Operations Analyst",
                        "login_frequency_per_week": 1,
                        "features_used": ["reporting"],
                        "team_size": 0,
                        "peer_assists": 0,
                        "training_sessions_delivered": 0,
                        "feature_requests": 0,
                        "support_interactions": 1,
                        "peer_training_hours": 0,
                    }
                ]
            },
            "engagement_data": {},
            "usage_data": {},
        }

        result2 = await agent.process(state2)

        print(f"Champion Count: {result2['champion_count']}")
        print(f"Network Strength: {result2['network_strength']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
