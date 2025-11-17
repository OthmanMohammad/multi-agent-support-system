"""
Power User Enablement Agent - TASK-2036

Identifies power users, provides advanced training, builds product champions,
and leverages advocates to drive broader adoption and expansion.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("power_user_enablement", tier="revenue", category="customer_success")
class PowerUserEnablementAgent(BaseAgent):
    """
    Power User Enablement Agent.

    Enables power users and champions by:
    - Identifying power users and high-potential users
    - Creating advanced training programs
    - Building product champion network
    - Leveraging advocates for case studies
    - Enabling peer-to-peer training
    - Measuring champion impact on adoption
    """

    # User engagement tiers
    USER_TIERS = {
        "power_user": {
            "min_login_days": 20,
            "min_features_used": 10,
            "min_actions_per_day": 20,
            "advanced_features": 3
        },
        "advanced": {
            "min_login_days": 15,
            "min_features_used": 7,
            "min_actions_per_day": 10,
            "advanced_features": 1
        },
        "regular": {
            "min_login_days": 10,
            "min_features_used": 5,
            "min_actions_per_day": 5,
            "advanced_features": 0
        },
        "casual": {
            "min_login_days": 5,
            "min_features_used": 3,
            "min_actions_per_day": 2,
            "advanced_features": 0
        }
    }

    # Champion program maturity
    CHAMPION_MATURITY = {
        "none": {"score_range": (0, 20), "champion_count": 0},
        "emerging": {"score_range": (21, 40), "champion_count": 2},
        "developing": {"score_range": (41, 65), "champion_count": 5},
        "established": {"score_range": (66, 85), "champion_count": 10},
        "thriving": {"score_range": (86, 100), "champion_count": 15}
    }

    # Champion activities
    CHAMPION_ACTIVITIES = [
        "Host internal training sessions",
        "Create and share templates",
        "Provide peer support and mentoring",
        "Beta test new features",
        "Participate in customer advisory board",
        "Contribute to case studies",
        "Speak at events or webinars",
        "Share best practices in community"
    ]

    def __init__(self):
        config = AgentConfig(
            name="power_user_enablement",
            type=AgentType.SPECIALIST,
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
        Analyze power user landscape and create enablement strategy.

        Args:
            state: Current agent state with user activity data

        Returns:
            Updated state with power user enablement plan
        """
        self.logger.info("power_user_enablement_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        user_data = state.get("entities", {}).get("user_data", {})
        customer_metadata = state.get("customer_metadata", {})
        current_champions = state.get("entities", {}).get("current_champions", [])

        self.logger.debug(
            "power_user_enablement_details",
            customer_id=customer_id,
            total_users=len(user_data.get("users", [])),
            current_champions=len(current_champions)
        )

        # Identify and segment users
        user_analysis = self._analyze_user_segments(
            user_data,
            current_champions
        )

        # Identify champion candidates
        champion_candidates = self._identify_champion_candidates(
            user_analysis,
            customer_metadata
        )

        # Create enablement strategy
        enablement_strategy = self._create_enablement_strategy(
            user_analysis,
            champion_candidates,
            customer_metadata
        )

        # Develop champion program
        champion_program = self._develop_champion_program(
            user_analysis,
            champion_candidates
        )

        # Calculate impact metrics
        impact_metrics = self._calculate_champion_impact(
            user_analysis,
            champion_candidates
        )

        # Format response
        response = self._format_enablement_report(
            user_analysis,
            champion_candidates,
            enablement_strategy,
            champion_program,
            impact_metrics
        )

        state["agent_response"] = response
        state["champion_maturity"] = user_analysis["champion_maturity"]
        state["power_user_count"] = user_analysis["power_user_count"]
        state["champion_candidates"] = len(champion_candidates)
        state["potential_adoption_impact"] = impact_metrics["potential_adoption_increase"]
        state["user_analysis"] = user_analysis
        state["response_confidence"] = 0.88
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "power_user_enablement_completed",
            customer_id=customer_id,
            maturity=user_analysis["champion_maturity"],
            power_users=user_analysis["power_user_count"],
            candidates=len(champion_candidates)
        )

        return state

    def _analyze_user_segments(
        self,
        user_data: Dict[str, Any],
        current_champions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze and segment users by engagement level.

        Args:
            user_data: User activity and engagement data
            current_champions: List of current product champions

        Returns:
            Comprehensive user segment analysis
        """
        users = user_data.get("users", [])
        total_users = len(users)

        # Segment users
        segmented_users = {
            "power_user": [],
            "advanced": [],
            "regular": [],
            "casual": [],
            "inactive": []
        }

        for user in users:
            tier = self._classify_user(user)
            segmented_users[tier].append(user)

        # Count by segment
        power_user_count = len(segmented_users["power_user"])
        advanced_count = len(segmented_users["advanced"])

        # Calculate champion program maturity
        champion_count = len(current_champions)
        champion_score = self._calculate_champion_score(
            champion_count,
            power_user_count,
            current_champions
        )

        champion_maturity = self._determine_champion_maturity(champion_score, champion_count)

        # Analyze champion effectiveness
        champion_effectiveness = self._analyze_champion_effectiveness(
            current_champions,
            segmented_users
        )

        # Calculate power user ratio
        power_user_ratio = (power_user_count / total_users * 100) if total_users > 0 else 0

        return {
            "total_users": total_users,
            "segmented_users": segmented_users,
            "power_user_count": power_user_count,
            "advanced_count": advanced_count,
            "power_user_ratio": round(power_user_ratio, 1),
            "champion_count": champion_count,
            "champion_score": round(champion_score, 1),
            "champion_maturity": champion_maturity,
            "champion_effectiveness": champion_effectiveness,
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _classify_user(self, user: Dict[str, Any]) -> str:
        """Classify user into engagement tier."""
        login_days = user.get("login_days_last_30", 0)
        features_used = user.get("features_used_count", 0)
        actions_per_day = user.get("avg_actions_per_day", 0)
        advanced_features = user.get("advanced_features_used", 0)

        # Check each tier from highest to lowest
        for tier, criteria in self.USER_TIERS.items():
            if (login_days >= criteria["min_login_days"] and
                features_used >= criteria["min_features_used"] and
                actions_per_day >= criteria["min_actions_per_day"] and
                advanced_features >= criteria["advanced_features"]):
                return tier

        return "inactive"

    def _calculate_champion_score(
        self,
        champion_count: int,
        power_user_count: int,
        current_champions: List[Dict[str, Any]]
    ) -> float:
        """Calculate champion program score (0-100)."""
        # Count score (max at 15 champions)
        count_score = min(champion_count / 15 * 100, 100)

        # Coverage score (ratio of champions to power users)
        target_ratio = 0.3  # 30% of power users should be champions
        if power_user_count > 0:
            actual_ratio = champion_count / power_user_count
            coverage_score = min(actual_ratio / target_ratio * 100, 100)
        else:
            coverage_score = 0

        # Activity score (based on champion engagement)
        active_champions = sum(
            1 for champ in current_champions
            if champ.get("activities_completed", 0) > 0
        )
        activity_score = (active_champions / champion_count * 100) if champion_count > 0 else 0

        # Weighted average
        score = (count_score * 0.4) + (coverage_score * 0.3) + (activity_score * 0.3)

        return min(score, 100)

    def _determine_champion_maturity(self, score: float, champion_count: int) -> str:
        """Determine champion program maturity level."""
        for level, criteria in self.CHAMPION_MATURITY.items():
            score_min, score_max = criteria["score_range"]
            if score_min <= score <= score_max:
                return level
        return "none"

    def _analyze_champion_effectiveness(
        self,
        current_champions: List[Dict[str, Any]],
        segmented_users: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze effectiveness of current champions."""
        if not current_champions:
            return {
                "avg_activities": 0,
                "avg_impact_score": 0,
                "total_users_helped": 0
            }

        total_activities = sum(champ.get("activities_completed", 0) for champ in current_champions)
        total_users_helped = sum(champ.get("users_helped", 0) for champ in current_champions)
        total_impact = sum(champ.get("impact_score", 0) for champ in current_champions)

        return {
            "avg_activities": round(total_activities / len(current_champions), 1),
            "avg_impact_score": round(total_impact / len(current_champions), 1),
            "total_users_helped": total_users_helped
        }

    def _identify_champion_candidates(
        self,
        user_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify users who would make good product champions."""
        candidates = []

        power_users = user_analysis["segmented_users"]["power_user"]
        advanced_users = user_analysis["segmented_users"]["advanced"]

        # Power users are primary candidates
        for user in power_users[:10]:  # Top 10 power users
            candidate_score = self._calculate_candidate_score(user, "power_user")

            candidates.append({
                "user_id": user.get("user_id"),
                "user_name": user.get("user_name", "User"),
                "user_email": user.get("user_email", ""),
                "current_tier": "power_user",
                "candidate_score": candidate_score,
                "strengths": self._identify_user_strengths(user),
                "recommended_activities": self._recommend_champion_activities(user),
                "potential_impact": "High - Can influence team adoption"
            })

        # Advanced users with high potential
        for user in advanced_users[:5]:
            candidate_score = self._calculate_candidate_score(user, "advanced")

            if candidate_score >= 60:  # Only high-scoring advanced users
                candidates.append({
                    "user_id": user.get("user_id"),
                    "user_name": user.get("user_name", "User"),
                    "user_email": user.get("user_email", ""),
                    "current_tier": "advanced",
                    "candidate_score": candidate_score,
                    "strengths": self._identify_user_strengths(user),
                    "recommended_activities": self._recommend_champion_activities(user),
                    "potential_impact": "Medium - Can mentor peers"
                })

        # Sort by candidate score
        candidates.sort(key=lambda x: x["candidate_score"], reverse=True)

        return candidates[:12]

    def _calculate_candidate_score(self, user: Dict[str, Any], tier: str) -> int:
        """Calculate champion candidate score (0-100)."""
        base_score = 80 if tier == "power_user" else 60

        # Bonus for tenure
        account_age_days = user.get("account_age_days", 0)
        tenure_bonus = min(account_age_days / 180 * 10, 10)  # Max 10 points for 6+ months

        # Bonus for help/collaboration
        collaboration_score = user.get("collaboration_score", 0)
        collab_bonus = min(collaboration_score / 10, 10)  # Max 10 points

        total_score = base_score + tenure_bonus + collab_bonus

        return int(min(total_score, 100))

    def _identify_user_strengths(self, user: Dict[str, Any]) -> List[str]:
        """Identify specific strengths of a user."""
        strengths = []

        if user.get("features_used_count", 0) >= 12:
            strengths.append("Broad feature knowledge")

        if user.get("advanced_features_used", 0) >= 5:
            strengths.append("Advanced feature expertise")

        if user.get("login_days_last_30", 0) >= 25:
            strengths.append("Highly engaged - daily user")

        if user.get("collaboration_score", 0) >= 7:
            strengths.append("Strong collaborator - helps teammates")

        if user.get("account_age_days", 0) >= 180:
            strengths.append("Experienced user - 6+ months tenure")

        if not strengths:
            strengths.append("Active and engaged user")

        return strengths[:3]

    def _recommend_champion_activities(self, user: Dict[str, Any]) -> List[str]:
        """Recommend champion activities based on user profile."""
        activities = []

        # Based on user strengths
        if user.get("advanced_features_used", 0) >= 5:
            activities.append("Lead advanced feature training")

        if user.get("collaboration_score", 0) >= 7:
            activities.append("Mentor new users")

        if user.get("account_age_days", 0) >= 365:
            activities.append("Contribute to case study")

        # Default activities
        activities.extend([
            "Share best practices in team meetings",
            "Test and provide feedback on new features"
        ])

        return activities[:4]

    def _create_enablement_strategy(
        self,
        user_analysis: Dict[str, Any],
        champion_candidates: List[Dict[str, Any]],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create power user enablement strategy."""
        maturity = user_analysis["champion_maturity"]
        power_user_count = user_analysis["power_user_count"]

        strategy = {
            "focus_area": "",
            "target_champion_count": 0,
            "recruitment_tactics": [],
            "enablement_tactics": [],
            "success_metrics": []
        }

        # Determine focus based on maturity
        if maturity in ["none", "emerging"]:
            strategy["focus_area"] = "Champion recruitment and program launch"
            strategy["target_champion_count"] = min(5, power_user_count)
            strategy["recruitment_tactics"] = [
                "Identify and reach out to top 5 power users",
                "Pitch champion program benefits (early access, recognition, etc.)",
                "Start with low-commitment activities"
            ]

        elif maturity == "developing":
            strategy["focus_area"] = "Champion activation and engagement"
            strategy["target_champion_count"] = min(10, int(power_user_count * 0.4))
            strategy["recruitment_tactics"] = [
                "Expand champion network by 50%",
                "Recruit from advanced user tier",
                "Create champion application process"
            ]

        else:  # established or thriving
            strategy["focus_area"] = "Champion impact maximization"
            strategy["target_champion_count"] = min(15, int(power_user_count * 0.5))
            strategy["recruitment_tactics"] = [
                "Maintain steady champion pipeline",
                "Graduate top performers to advisory board",
                "Focus on champion retention"
            ]

        # Enablement tactics (common to all)
        strategy["enablement_tactics"] = [
            "Provide exclusive advanced training sessions",
            "Grant early access to beta features",
            "Create champion-only Slack channel or community",
            "Recognize champions publicly (badges, certificates, etc.)",
            "Offer direct line to product team"
        ]

        # Success metrics
        strategy["success_metrics"] = [
            f"Recruit {strategy['target_champion_count']} active champions",
            "Each champion completes 2+ activities per quarter",
            "Champions help train 50+ other users",
            "Measure 15%+ adoption increase in champion's teams"
        ]

        return strategy

    def _develop_champion_program(
        self,
        user_analysis: Dict[str, Any],
        champion_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Develop champion program structure."""
        program = {
            "program_name": "Product Champions",
            "tiers": [],
            "benefits": [],
            "responsibilities": [],
            "quarterly_activities": []
        }

        # Program tiers
        program["tiers"] = [
            {
                "name": "Champion",
                "requirements": "Active power user, completes 2+ activities/quarter",
                "benefits": "Early access to features, exclusive training"
            },
            {
                "name": "Senior Champion",
                "requirements": "6+ months as Champion, exceptional impact",
                "benefits": "All Champion benefits + advisory board seat"
            }
        ]

        # Benefits
        program["benefits"] = [
            "Exclusive access to beta features and roadmap previews",
            "Direct communication channel with product team",
            "Recognition badges and certificates",
            "Invitations to customer advisory board",
            "Speaking opportunities at events",
            "Feature in customer success stories"
        ]

        # Responsibilities
        program["responsibilities"] = [
            "Complete minimum 2 champion activities per quarter",
            "Provide feedback on new features and improvements",
            "Help onboard and train team members",
            "Share best practices and use cases",
            "Participate in monthly champion calls"
        ]

        # Quarterly activities
        program["quarterly_activities"] = [
            "Host 1-2 internal training sessions",
            "Create 1 template or workflow to share",
            "Test 1-2 beta features and provide feedback",
            "Mentor 3-5 newer or struggling users"
        ]

        return program

    def _calculate_champion_impact(
        self,
        user_analysis: Dict[str, Any],
        champion_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate potential impact of champion program."""
        total_users = user_analysis["total_users"]
        current_champions = user_analysis["champion_count"]
        target_champions = len(champion_candidates)

        # Estimate users each champion can influence (avg 10 users)
        users_per_champion = 10
        potential_reach = target_champions * users_per_champion

        # Estimate adoption improvement (15% average)
        adoption_multiplier = 0.15
        potential_adoption_increase = min(potential_reach * adoption_multiplier, total_users * 0.3)

        # Calculate expansion potential
        expansion_likelihood = "high" if target_champions >= 5 else "medium" if target_champions >= 3 else "low"

        # NPS impact (champions typically increase NPS by 10-20 points)
        nps_impact = "+10-20 points from champion advocacy"

        return {
            "target_champion_count": target_champions,
            "potential_user_reach": int(potential_reach),
            "potential_adoption_increase": int(potential_adoption_increase),
            "expansion_likelihood": expansion_likelihood,
            "nps_impact": nps_impact,
            "reference_potential": "High" if target_champions >= 5 else "Medium"
        }

    def _format_enablement_report(
        self,
        user_analysis: Dict[str, Any],
        champion_candidates: List[Dict[str, Any]],
        enablement_strategy: Dict[str, Any],
        champion_program: Dict[str, Any],
        impact_metrics: Dict[str, Any]
    ) -> str:
        """Format power user enablement report."""
        maturity = user_analysis["champion_maturity"]

        maturity_emoji = {
            "none": "????",
            "emerging": "????",
            "developing": "????",
            "established": "????",
            "thriving": "????"
        }

        report = f"""**{maturity_emoji.get(maturity, '????')} Power User Enablement Report**

**Champion Program Maturity:** {maturity.upper()}
**Champion Score:** {user_analysis['champion_score']}/100
**Current Champions:** {user_analysis['champion_count']}
**Power Users:** {user_analysis['power_user_count']} ({user_analysis['power_user_ratio']}% of users)

**User Segmentation:**
"""

        # User segments
        for tier in ["power_user", "advanced", "regular", "casual"]:
            count = len(user_analysis["segmented_users"].get(tier, []))
            if count > 0:
                tier_icon = "???" if tier == "power_user" else "????" if tier == "advanced" else "???" if tier == "regular" else "????"
                report += f"- {tier_icon} {tier.replace('_', ' ').title()}: {count} users\n"

        # Champion effectiveness
        if user_analysis["champion_count"] > 0:
            effectiveness = user_analysis["champion_effectiveness"]
            report += f"\n**Current Champion Effectiveness:**\n"
            report += f"- Avg Activities: {effectiveness['avg_activities']}/quarter\n"
            report += f"- Avg Impact Score: {effectiveness['avg_impact_score']}/10\n"
            report += f"- Total Users Helped: {effectiveness['total_users_helped']}\n"

        # Top champion candidates
        if champion_candidates:
            report += "\n**???? Top Champion Candidates:**\n"
            for i, candidate in enumerate(champion_candidates[:5], 1):
                score_bar = "???" * (candidate["candidate_score"] // 10)
                report += f"\n{i}. **{candidate['user_name']}** ({candidate['current_tier'].replace('_', ' ').title()})\n"
                report += f"   - Score: {score_bar} {candidate['candidate_score']}/100\n"
                report += f"   - Strengths: {', '.join(candidate['strengths'])}\n"
                report += f"   - Impact: {candidate['potential_impact']}\n"

        # Enablement strategy
        report += f"\n**???? Enablement Strategy**\n"
        report += f"**Focus:** {enablement_strategy['focus_area']}\n"
        report += f"**Target Champions:** {enablement_strategy['target_champion_count']}\n\n"

        report += "**Recruitment Tactics:**\n"
        for tactic in enablement_strategy["recruitment_tactics"]:
            report += f"- {tactic}\n"

        report += "\n**Enablement Tactics:**\n"
        for tactic in enablement_strategy["enablement_tactics"][:4]:
            report += f"- {tactic}\n"

        # Champion program structure
        report += f"\n**???? {champion_program['program_name']} Program**\n"

        report += "\n**Champion Benefits:**\n"
        for benefit in champion_program["benefits"][:4]:
            report += f"- {benefit}\n"

        report += "\n**Champion Responsibilities:**\n"
        for responsibility in champion_program["responsibilities"][:3]:
            report += f"- {responsibility}\n"

        # Impact metrics
        report += "\n**???? Projected Impact:**\n"
        report += f"- Target Champions: {impact_metrics['target_champion_count']}\n"
        report += f"- Potential User Reach: {impact_metrics['potential_user_reach']} users\n"
        report += f"- Adoption Increase: +{impact_metrics['potential_adoption_increase']} users\n"
        report += f"- Expansion Likelihood: {impact_metrics['expansion_likelihood'].title()}\n"
        report += f"- NPS Impact: {impact_metrics['nps_impact']}\n"
        report += f"- Reference/Case Study Potential: {impact_metrics['reference_potential']}\n"

        # Success metrics
        report += "\n**Success Metrics:**\n"
        for metric in enablement_strategy["success_metrics"]:
            report += f"- {metric}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Power User Enablement Agent (TASK-2036)")
        print("=" * 70)

        agent = PowerUserEnablementAgent()

        # Test 1: No champion program
        print("\n\nTest 1: No Champion Program")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze power user landscape",
            context={
                "customer_id": "cust_no_champions",
                "customer_metadata": {
                    "plan": "premium",
                    "industry": "healthcare"
                }
            }
        )
        state1["entities"] = {
            "user_data": {
                "users": [
                    {
                        "user_id": f"user_{i}",
                        "user_name": f"User {i}",
                        "user_email": f"user{i}@example.com",
                        "login_days_last_30": 25 if i <= 3 else 15 if i <= 8 else 5,
                        "features_used_count": 12 if i <= 3 else 7 if i <= 8 else 3,
                        "avg_actions_per_day": 25 if i <= 3 else 12 if i <= 8 else 3,
                        "advanced_features_used": 4 if i <= 3 else 1 if i <= 8 else 0,
                        "collaboration_score": 8 if i <= 3 else 5 if i <= 8 else 2,
                        "account_age_days": 200 if i <= 5 else 90
                    }
                    for i in range(1, 31)
                ]
            },
            "current_champions": []
        }

        result1 = await agent.process(state1)

        print(f"Maturity: {result1['champion_maturity']}")
        print(f"Power Users: {result1['power_user_count']}")
        print(f"Champion Candidates: {result1['champion_candidates']}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Established champion program
        print("\n\n" + "=" * 70)
        print("Test 2: Established Champion Program")
        print("-" * 70)

        state2 = create_initial_state(
            "Review champion program",
            context={
                "customer_id": "cust_champions",
                "customer_metadata": {
                    "plan": "enterprise",
                    "industry": "technology"
                }
            }
        )
        state2["entities"] = {
            "user_data": {
                "users": [
                    {
                        "user_id": f"user_{i}",
                        "user_name": f"User {i}",
                        "user_email": f"user{i}@example.com",
                        "login_days_last_30": 28 if i <= 15 else 18 if i <= 35 else 8,
                        "features_used_count": 15 if i <= 15 else 9 if i <= 35 else 4,
                        "avg_actions_per_day": 30 if i <= 15 else 15 if i <= 35 else 5,
                        "advanced_features_used": 5 if i <= 15 else 2 if i <= 35 else 0,
                        "collaboration_score": 9 if i <= 15 else 6 if i <= 35 else 3,
                        "account_age_days": 365 if i <= 20 else 180
                    }
                    for i in range(1, 61)
                ]
            },
            "current_champions": [
                {
                    "user_id": f"user_{i}",
                    "activities_completed": 3,
                    "impact_score": 8,
                    "users_helped": 12
                }
                for i in range(1, 11)
            ]
        }

        result2 = await agent.process(state2)

        print(f"Maturity: {result2['champion_maturity']}")
        print(f"Power Users: {result2['power_user_count']}")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
