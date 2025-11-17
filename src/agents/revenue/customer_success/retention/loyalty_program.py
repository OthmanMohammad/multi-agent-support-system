"""
Loyalty Program Agent - TASK-2045

Manages customer loyalty programs, tracks loyalty points, offers rewards,
and recognizes customer milestones to drive retention and engagement.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("loyalty_program", tier="revenue", category="customer_success")
class LoyaltyProgramAgent(BaseAgent):
    """
    Loyalty Program Agent.

    Manages customer loyalty and rewards:
    - Tracks loyalty points and tier status
    - Awards points for positive behaviors
    - Offers rewards and benefits
    - Recognizes customer milestones
    - Manages tier upgrades/downgrades
    - Drives referrals and advocacy
    """

    # Loyalty tiers
    LOYALTY_TIERS = {
        "bronze": {"points_min": 0, "points_max": 999, "multiplier": 1.0},
        "silver": {"points_min": 1000, "points_max": 4999, "multiplier": 1.25},
        "gold": {"points_min": 5000, "points_max": 14999, "multiplier": 1.5},
        "platinum": {"points_min": 15000, "points_max": 49999, "multiplier": 2.0},
        "diamond": {"points_min": 50000, "points_max": 999999, "multiplier": 2.5}
    }

    # Point earning activities
    POINT_ACTIVITIES = {
        "monthly_renewal": 100,
        "referral_signup": 500,
        "case_study_participation": 1000,
        "product_review": 200,
        "feature_adoption": 50,
        "training_completion": 150,
        "community_contribution": 75,
        "nps_promoter": 300,
        "social_media_mention": 100,
        "beta_testing": 250
    }

    # Rewards catalog
    REWARDS_CATALOG = {
        "account_credit": {"points": 1000, "value": "$100 account credit"},
        "premium_support": {"points": 2500, "value": "1 month premium support"},
        "feature_unlock": {"points": 1500, "value": "Unlock premium feature"},
        "swag_package": {"points": 500, "value": "Company swag package"},
        "executive_meeting": {"points": 5000, "value": "1-on-1 with executive"},
        "custom_training": {"points": 3000, "value": "Custom training session"},
        "early_access": {"points": 2000, "value": "Early access to new features"},
        "discount_renewal": {"points": 4000, "value": "10% renewal discount"}
    }

    def __init__(self):
        config = AgentConfig(
            name="loyalty_program",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            max_tokens=550,
            capabilities=[AgentCapability.CONTEXT_AWARE],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Manage customer loyalty program status and rewards.

        Args:
            state: Current agent state with loyalty data

        Returns:
            Updated state with loyalty analysis and recommendations
        """
        self.logger.info("loyalty_program_processing_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        loyalty_data = state.get("entities", {}).get("loyalty_data", {})
        customer_metadata = state.get("customer_metadata", {})
        recent_activities = state.get("entities", {}).get("recent_activities", [])

        self.logger.debug(
            "loyalty_program_details",
            customer_id=customer_id,
            current_points=loyalty_data.get("points", 0),
            current_tier=loyalty_data.get("tier", "bronze")
        )

        # Calculate loyalty status
        loyalty_status = self._calculate_loyalty_status(
            loyalty_data,
            customer_metadata
        )

        # Process point activities
        points_update = self._process_point_activities(
            recent_activities,
            loyalty_status
        )

        # Check for milestones
        milestones = self._check_milestones(
            loyalty_data,
            customer_metadata,
            points_update
        )

        # Recommend rewards
        reward_recommendations = self._recommend_rewards(
            loyalty_status,
            customer_metadata
        )

        # Format response
        response = self._format_loyalty_report(
            loyalty_status,
            points_update,
            milestones,
            reward_recommendations
        )

        state["agent_response"] = response
        state["loyalty_tier"] = loyalty_status["current_tier"]
        state["loyalty_points"] = loyalty_status["total_points"]
        state["points_to_next_tier"] = loyalty_status.get("points_to_next_tier", 0)
        state["available_rewards"] = [r["reward"] for r in reward_recommendations[:3]]
        state["loyalty_status"] = loyalty_status
        state["response_confidence"] = 0.85
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "loyalty_program_processed",
            customer_id=customer_id,
            tier=loyalty_status["current_tier"],
            points=loyalty_status["total_points"],
            milestones=len(milestones)
        )

        return state

    def _calculate_loyalty_status(
        self,
        loyalty_data: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate current loyalty status."""
        current_points = loyalty_data.get("points", 0)

        # Determine current tier
        current_tier = self._determine_tier(current_points)

        # Get tier config
        tier_config = self.LOYALTY_TIERS[current_tier]

        # Calculate points to next tier
        next_tier = self._get_next_tier(current_tier)
        if next_tier:
            points_to_next_tier = self.LOYALTY_TIERS[next_tier]["points_min"] - current_points
        else:
            points_to_next_tier = 0

        # Calculate point multiplier
        point_multiplier = tier_config["multiplier"]

        # Calculate lifetime stats
        lifetime_points_earned = loyalty_data.get("lifetime_points_earned", current_points)
        lifetime_points_redeemed = loyalty_data.get("lifetime_points_redeemed", 0)

        # Member since
        member_since = loyalty_data.get("member_since")
        if member_since:
            member_date = datetime.fromisoformat(member_since.replace('Z', '+00:00'))
            membership_days = (datetime.utcnow() - member_date).days
        else:
            membership_days = 0

        return {
            "total_points": current_points,
            "current_tier": current_tier,
            "point_multiplier": point_multiplier,
            "points_to_next_tier": points_to_next_tier,
            "next_tier": next_tier,
            "lifetime_points_earned": lifetime_points_earned,
            "lifetime_points_redeemed": lifetime_points_redeemed,
            "membership_days": membership_days,
            "tier_benefits": self._get_tier_benefits(current_tier)
        }

    def _determine_tier(self, points: int) -> str:
        """Determine loyalty tier based on points."""
        for tier, config in sorted(
            self.LOYALTY_TIERS.items(),
            key=lambda x: x[1]["points_min"],
            reverse=True
        ):
            if points >= config["points_min"]:
                return tier
        return "bronze"

    def _get_next_tier(self, current_tier: str) -> Optional[str]:
        """Get next tier above current."""
        tier_order = ["bronze", "silver", "gold", "platinum", "diamond"]
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass
        return None

    def _get_tier_benefits(self, tier: str) -> List[str]:
        """Get benefits for a tier."""
        benefits = {
            "bronze": [
                "Earn 1x points on activities",
                "Access to rewards catalog"
            ],
            "silver": [
                "Earn 1.25x points on activities",
                "Priority email support",
                "Quarterly swag item"
            ],
            "gold": [
                "Earn 1.5x points on activities",
                "Priority support with 12-hour SLA",
                "Early access to new features",
                "Bi-annual executive check-in"
            ],
            "platinum": [
                "Earn 2x points on activities",
                "24/7 premium support",
                "Dedicated CSM",
                "Quarterly executive business review",
                "Beta program access"
            ],
            "diamond": [
                "Earn 2.5x points on activities",
                "White-glove concierge support",
                "Executive sponsor",
                "Product roadmap influence",
                "VIP event invitations",
                "Custom feature development consideration"
            ]
        }
        return benefits.get(tier, [])

    def _process_point_activities(
        self,
        recent_activities: List[Dict[str, Any]],
        loyalty_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process recent activities and calculate points earned."""
        total_points_earned = 0
        activities_processed = []

        multiplier = loyalty_status["point_multiplier"]

        for activity in recent_activities:
            activity_type = activity.get("type")
            base_points = self.POINT_ACTIVITIES.get(activity_type, 0)

            if base_points > 0:
                points_earned = int(base_points * multiplier)
                total_points_earned += points_earned

                activities_processed.append({
                    "activity": activity_type.replace("_", " ").title(),
                    "base_points": base_points,
                    "multiplier": multiplier,
                    "points_earned": points_earned,
                    "date": activity.get("date", datetime.utcnow().isoformat())
                })

        return {
            "total_points_earned": total_points_earned,
            "activities_count": len(activities_processed),
            "activities_processed": activities_processed[:10]  # Top 10
        }

    def _check_milestones(
        self,
        loyalty_data: Dict[str, Any],
        customer_metadata: Dict[str, Any],
        points_update: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Check for loyalty milestones achieved."""
        milestones = []

        current_points = loyalty_data.get("points", 0)
        new_total = current_points + points_update["total_points_earned"]

        # Tier upgrade milestone
        old_tier = self._determine_tier(current_points)
        new_tier = self._determine_tier(new_total)

        if new_tier != old_tier:
            tier_order = ["bronze", "silver", "gold", "platinum", "diamond"]
            if tier_order.index(new_tier) > tier_order.index(old_tier):
                milestones.append({
                    "milestone": f"Tier Upgrade: {old_tier.title()} ??? {new_tier.title()}",
                    "achievement": f"Reached {new_tier.title()} tier",
                    "reward": "Tier upgrade benefits unlocked"
                })

        # Point milestones
        point_milestones = [1000, 5000, 10000, 25000, 50000]
        for milestone_points in point_milestones:
            if current_points < milestone_points <= new_total:
                milestones.append({
                    "milestone": f"{milestone_points:,} Points Milestone",
                    "achievement": f"Accumulated {milestone_points:,} loyalty points",
                    "reward": "Bonus 500 points"
                })

        # Tenure milestones (if customer data available)
        customer_tenure_months = customer_metadata.get("customer_tenure_months", 0)
        tenure_milestones = {12: "1 Year", 24: "2 Years", 36: "3 Years", 60: "5 Years"}

        for months, label in tenure_milestones.items():
            if customer_tenure_months == months:
                milestones.append({
                    "milestone": f"{label} Anniversary",
                    "achievement": f"Loyal customer for {label.lower()}",
                    "reward": "1000 bonus points + special gift"
                })

        return milestones

    def _recommend_rewards(
        self,
        loyalty_status: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Recommend available rewards for customer."""
        current_points = loyalty_status["total_points"]
        recommendations = []

        for reward_id, reward_data in self.REWARDS_CATALOG.items():
            required_points = reward_data["points"]

            if current_points >= required_points:
                recommendations.append({
                    "reward": reward_id.replace("_", " ").title(),
                    "points_cost": required_points,
                    "value": reward_data["value"],
                    "affordable": True,
                    "points_remaining_after": current_points - required_points
                })
            elif current_points >= required_points * 0.8:  # Within 80%
                recommendations.append({
                    "reward": reward_id.replace("_", " ").title(),
                    "points_cost": required_points,
                    "value": reward_data["value"],
                    "affordable": False,
                    "points_needed": required_points - current_points
                })

        # Sort: affordable first, then by value
        recommendations.sort(key=lambda x: (not x["affordable"], x["points_cost"]))

        return recommendations[:6]

    def _format_loyalty_report(
        self,
        loyalty_status: Dict[str, Any],
        points_update: Dict[str, Any],
        milestones: List[Dict[str, str]],
        reward_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Format loyalty program report."""
        tier = loyalty_status["current_tier"]

        tier_emoji = {
            "bronze": "????",
            "silver": "????",
            "gold": "????",
            "platinum": "????",
            "diamond": "????"
        }

        report = f"""**{tier_emoji.get(tier, '???')} Loyalty Program Status**

**Current Tier:** {tier.upper()}
**Total Points:** {loyalty_status['total_points']:,}
**Point Multiplier:** {loyalty_status['point_multiplier']}x
"""

        if loyalty_status.get("next_tier"):
            report += f"**Points to {loyalty_status['next_tier'].title()}:** {loyalty_status['points_to_next_tier']:,}\n"

        report += f"**Membership:** {loyalty_status['membership_days']} days\n"

        # Recent activity
        if points_update["activities_count"] > 0:
            report += f"\n**???? Recent Activity ({points_update['activities_count']} activities):**\n"
            report += f"**Points Earned:** +{points_update['total_points_earned']:,}\n\n"

            for activity in points_update["activities_processed"][:5]:
                report += f"- {activity['activity']}: +{activity['points_earned']} pts "
                report += f"({activity['base_points']} ?? {activity['multiplier']}x)\n"

        # Milestones
        if milestones:
            report += "\n**???? Milestones Achieved:**\n"
            for milestone in milestones[:3]:
                report += f"\n**{milestone['milestone']}**\n"
                report += f"  Achievement: {milestone['achievement']}\n"
                report += f"  Reward: {milestone['reward']}\n"

        # Tier benefits
        report += f"\n**??? {tier.title()} Tier Benefits:**\n"
        for benefit in loyalty_status["tier_benefits"][:4]:
            report += f"- {benefit}\n"

        # Rewards
        affordable_rewards = [r for r in reward_recommendations if r.get("affordable")]
        if affordable_rewards:
            report += "\n**???? Available Rewards (You Can Redeem):**\n"
            for reward in affordable_rewards[:3]:
                report += f"- **{reward['reward']}** - {reward['points_cost']:,} pts ({reward['value']})\n"

        # Almost affordable
        almost_rewards = [r for r in reward_recommendations if not r.get("affordable")]
        if almost_rewards:
            report += "\n**???? Coming Soon (Almost There):**\n"
            for reward in almost_rewards[:2]:
                report += f"- **{reward['reward']}** - Need {reward['points_needed']:,} more pts ({reward['value']})\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Loyalty Program Agent (TASK-2045)")
        print("=" * 70)

        agent = LoyaltyProgramAgent()

        # Test 1: Active loyalty member with recent activities
        print("\n\nTest 1: Gold Tier Member with Recent Activities")
        print("-" * 70)

        state1 = create_initial_state(
            "Check loyalty program status",
            context={
                "customer_id": "cust_loyal_123",
                "customer_metadata": {
                    "plan": "premium",
                    "customer_tenure_months": 24
                }
            }
        )
        state1["entities"] = {
            "loyalty_data": {
                "points": 8500,
                "tier": "gold",
                "member_since": (datetime.utcnow() - timedelta(days=730)).isoformat(),
                "lifetime_points_earned": 12000,
                "lifetime_points_redeemed": 3500
            },
            "recent_activities": [
                {"type": "monthly_renewal", "date": datetime.utcnow().isoformat()},
                {"type": "referral_signup", "date": (datetime.utcnow() - timedelta(days=5)).isoformat()},
                {"type": "product_review", "date": (datetime.utcnow() - timedelta(days=10)).isoformat()},
                {"type": "nps_promoter", "date": (datetime.utcnow() - timedelta(days=15)).isoformat()}
            ]
        }

        result1 = await agent.process(state1)

        print(f"Tier: {result1['loyalty_tier']}")
        print(f"Points: {result1['loyalty_points']:,}")
        print(f"Points to Next Tier: {result1['points_to_next_tier']:,}")
        print(f"Available Rewards: {len(result1['available_rewards'])}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: New member, low tier
        print("\n\n" + "=" * 70)
        print("Test 2: Bronze Tier New Member")
        print("-" * 70)

        state2 = create_initial_state(
            "Process loyalty points",
            context={
                "customer_id": "cust_new_456",
                "customer_metadata": {
                    "plan": "basic",
                    "customer_tenure_months": 2
                }
            }
        )
        state2["entities"] = {
            "loyalty_data": {
                "points": 250,
                "tier": "bronze",
                "member_since": (datetime.utcnow() - timedelta(days=60)).isoformat(),
                "lifetime_points_earned": 250,
                "lifetime_points_redeemed": 0
            },
            "recent_activities": [
                {"type": "training_completion", "date": datetime.utcnow().isoformat()},
                {"type": "feature_adoption", "date": (datetime.utcnow() - timedelta(days=3)).isoformat()}
            ]
        }

        result2 = await agent.process(state2)

        print(f"Tier: {result2['loyalty_tier']}")
        print(f"Points: {result2['loyalty_points']:,}")
        print(f"\nResponse:\n{result2['agent_response']}")

    asyncio.run(test())
