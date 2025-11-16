"""
Feature Comparator Agent - TASK-1054

Maintains feature comparison matrices, tracks competitor feature updates,
identifies feature gaps, and generates battle cards.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("feature_comparator", tier="revenue", category="sales")
class FeatureComparator(BaseAgent):
    """
    Feature Comparator Agent - Maintains competitive feature comparisons and battle cards.

    Handles:
    - Maintain feature comparison matrices
    - Track competitor feature updates
    - Identify feature gaps (theirs and ours)
    - Generate battle cards
    - Provide feature-based positioning
    """

    # Feature categories and comparison matrix
    FEATURE_MATRIX = {
        "core_crm": {
            "category_name": "Core CRM",
            "importance": "critical",
            "features": {
                "contact_management": {
                    "name": "Contact Management",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "basic",
                        "intercom": "basic",
                        "freshdesk": "basic"
                    }
                },
                "deal_pipeline": {
                    "name": "Deal Pipeline",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "none",
                        "intercom": "basic",
                        "freshdesk": "none"
                    }
                },
                "activity_tracking": {
                    "name": "Activity Tracking",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "basic",
                        "intercom": "basic",
                        "freshdesk": "basic"
                    }
                }
            }
        },
        "automation": {
            "category_name": "Automation & Workflows",
            "importance": "high",
            "features": {
                "workflow_automation": {
                    "name": "Workflow Automation",
                    "our_status": "full",
                    "our_advantage": "No-code builder with AI suggestions",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "basic",
                        "intercom": "basic",
                        "freshdesk": "basic"
                    }
                },
                "ai_automation": {
                    "name": "AI-Powered Automation",
                    "our_status": "full",
                    "our_advantage": "Built-in, not extra cost",
                    "competitors": {
                        "salesforce": "paid_addon",
                        "hubspot": "limited",
                        "zendesk": "limited",
                        "intercom": "limited",
                        "freshdesk": "none"
                    }
                },
                "email_automation": {
                    "name": "Email Automation",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "basic",
                        "intercom": "basic",
                        "freshdesk": "basic"
                    }
                }
            }
        },
        "analytics": {
            "category_name": "Analytics & Reporting",
            "importance": "high",
            "features": {
                "custom_dashboards": {
                    "name": "Custom Dashboards",
                    "our_status": "full",
                    "our_advantage": "Unlimited dashboards on all plans",
                    "competitors": {
                        "salesforce": "limited_by_plan",
                        "hubspot": "limited_by_plan",
                        "zendesk": "basic",
                        "intercom": "basic",
                        "freshdesk": "basic"
                    }
                },
                "real_time_analytics": {
                    "name": "Real-time Analytics",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "basic",
                        "intercom": "full",
                        "freshdesk": "basic"
                    }
                },
                "predictive_analytics": {
                    "name": "Predictive Analytics",
                    "our_status": "full",
                    "our_advantage": "AI-powered forecasting included",
                    "competitors": {
                        "salesforce": "paid_addon",
                        "hubspot": "limited",
                        "zendesk": "none",
                        "intercom": "none",
                        "freshdesk": "none"
                    }
                }
            }
        },
        "integrations": {
            "category_name": "Integrations & API",
            "importance": "high",
            "features": {
                "native_integrations": {
                    "name": "Native Integrations",
                    "our_status": "full",
                    "our_advantage": "500+ integrations",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "full",
                        "intercom": "full",
                        "freshdesk": "limited"
                    }
                },
                "api_access": {
                    "name": "API Access",
                    "our_status": "full",
                    "our_advantage": "All plans, unlimited calls",
                    "competitors": {
                        "salesforce": "limited_by_plan",
                        "hubspot": "limited_by_plan",
                        "zendesk": "limited_by_plan",
                        "intercom": "limited_by_plan",
                        "freshdesk": "limited_by_plan"
                    }
                },
                "webhooks": {
                    "name": "Webhooks",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "full",
                        "intercom": "full",
                        "freshdesk": "basic"
                    }
                }
            }
        },
        "collaboration": {
            "category_name": "Team Collaboration",
            "importance": "medium",
            "features": {
                "team_inbox": {
                    "name": "Team Inbox",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "basic",
                        "hubspot": "full",
                        "zendesk": "full",
                        "intercom": "full",
                        "freshdesk": "full"
                    }
                },
                "internal_notes": {
                    "name": "Internal Notes & Comments",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "full",
                        "intercom": "full",
                        "freshdesk": "full"
                    }
                },
                "assignment_rules": {
                    "name": "Smart Assignment Rules",
                    "our_status": "full",
                    "our_advantage": "AI-powered routing",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "full",
                        "intercom": "basic",
                        "freshdesk": "basic"
                    }
                }
            }
        },
        "mobile": {
            "category_name": "Mobile Experience",
            "importance": "medium",
            "features": {
                "mobile_app_ios": {
                    "name": "iOS App",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "full",
                        "intercom": "full",
                        "freshdesk": "full"
                    }
                },
                "mobile_app_android": {
                    "name": "Android App",
                    "our_status": "full",
                    "competitors": {
                        "salesforce": "full",
                        "hubspot": "full",
                        "zendesk": "full",
                        "intercom": "full",
                        "freshdesk": "full"
                    }
                },
                "offline_mode": {
                    "name": "Offline Mode",
                    "our_status": "full",
                    "our_advantage": "Full offline capability",
                    "competitors": {
                        "salesforce": "limited",
                        "hubspot": "limited",
                        "zendesk": "none",
                        "intercom": "none",
                        "freshdesk": "none"
                    }
                }
            }
        }
    }

    # Feature status definitions
    FEATURE_STATUS = {
        "full": {"label": "Full Support", "score": 3, "emoji": "✅"},
        "basic": {"label": "Basic Support", "score": 2, "emoji": "⚠️"},
        "limited": {"label": "Limited Support", "score": 1, "emoji": "⚠️"},
        "paid_addon": {"label": "Paid Add-on", "score": 1, "emoji": "💰"},
        "limited_by_plan": {"label": "Limited by Plan", "score": 1, "emoji": "💰"},
        "none": {"label": "Not Available", "score": 0, "emoji": "❌"}
    }

    # Recent competitor feature updates (last 90 days)
    RECENT_UPDATES = {
        "salesforce": [
            {
                "date": "2024-01-05",
                "feature": "Einstein GPT",
                "category": "ai_automation",
                "impact": "high",
                "description": "New AI features but require expensive add-on"
            }
        ],
        "hubspot": [
            {
                "date": "2024-01-10",
                "feature": "Breeze AI",
                "category": "ai_automation",
                "impact": "medium",
                "description": "AI assistant for content and prospecting"
            }
        ],
        "intercom": [
            {
                "date": "2023-12-20",
                "feature": "Fin AI Agent",
                "category": "ai_automation",
                "impact": "high",
                "description": "AI chatbot but expensive add-on"
            }
        ]
    }

    def __init__(self):
        config = AgentConfig(
            name="feature_comparator",
            type=AgentType.ANALYZER,
            model="claude-3-5-sonnet-20241022",
            temperature=0.2,
            max_tokens=1500,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process feature comparison"""
        self.logger.info("feature_comparator_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify competitors to compare
        competitors_to_compare = self._identify_competitors(message, state)

        # Generate feature comparison
        feature_comparison = self._generate_feature_comparison(competitors_to_compare)

        # Identify our advantages
        our_advantages = self._identify_our_advantages(competitors_to_compare)

        # Identify feature gaps (where we're behind)
        feature_gaps = self._identify_feature_gaps(competitors_to_compare)

        # Identify their gaps (where they're behind)
        their_gaps = self._identify_their_gaps(competitors_to_compare)

        # Generate battle cards
        battle_cards = self._generate_battle_cards(
            competitors_to_compare,
            our_advantages,
            their_gaps
        )

        # Get recent competitor updates
        recent_updates = self._get_recent_updates(competitors_to_compare)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            our_advantages,
            feature_gaps,
            their_gaps,
            recent_updates
        )

        # Calculate confidence
        confidence = 0.92  # High confidence - based on known feature matrix

        # Update state
        state["feature_comparison"] = feature_comparison
        state["our_feature_advantages"] = our_advantages
        state["our_feature_gaps"] = feature_gaps
        state["competitor_feature_gaps"] = their_gaps
        state["feature_battle_cards"] = battle_cards
        state["recent_competitor_updates"] = recent_updates
        state["feature_recommendations"] = recommendations
        state["response_confidence"] = confidence
        state["status"] = "resolved"

        self.logger.info(
            "feature_comparator_completed",
            competitors_compared=len(competitors_to_compare),
            advantages_identified=len(our_advantages),
            gaps_identified=len(feature_gaps)
        )

        return state

    def _identify_competitors(self, message: str, state: AgentState) -> List[str]:
        """Identify which competitors to compare"""
        message_lower = message.lower()
        competitors = []

        # Check for specific mentions
        known_competitors = ["salesforce", "hubspot", "zendesk", "intercom", "freshdesk"]
        for competitor in known_competitors:
            if competitor in message_lower:
                competitors.append(competitor)

        # Use from state if available
        if not competitors:
            competitors = state.get("mentioned_competitors", [])

        # Default to top 3 competitors
        if not competitors:
            competitors = ["salesforce", "hubspot", "zendesk"]

        return competitors

    def _generate_feature_comparison(self, competitors: List[str]) -> Dict[str, Any]:
        """Generate comprehensive feature comparison"""
        comparison = {
            "categories": [],
            "summary": {
                "total_categories": len(self.FEATURE_MATRIX),
                "total_features": 0,
                "our_full_support": 0,
                "competitors": {}
            }
        }

        for competitor in competitors:
            comparison["summary"]["competitors"][competitor] = {
                "full_support": 0,
                "basic_support": 0,
                "none": 0,
                "paid_addon": 0
            }

        # Process each category
        for category_key, category_data in self.FEATURE_MATRIX.items():
            category_comparison = {
                "category": category_key,
                "category_name": category_data["category_name"],
                "importance": category_data["importance"],
                "features": []
            }

            for feature_key, feature_data in category_data["features"].items():
                comparison["summary"]["total_features"] += 1

                feature_comp = {
                    "feature": feature_key,
                    "feature_name": feature_data["name"],
                    "our_status": feature_data["our_status"],
                    "our_advantage": feature_data.get("our_advantage"),
                    "competitor_status": {}
                }

                # Track our full support
                if feature_data["our_status"] == "full":
                    comparison["summary"]["our_full_support"] += 1

                # Add competitor statuses
                for competitor in competitors:
                    status = feature_data["competitors"].get(competitor, "none")
                    feature_comp["competitor_status"][competitor] = status

                    # Track competitor stats
                    if status == "full":
                        comparison["summary"]["competitors"][competitor]["full_support"] += 1
                    elif status in ["basic", "limited"]:
                        comparison["summary"]["competitors"][competitor]["basic_support"] += 1
                    elif status in ["paid_addon", "limited_by_plan"]:
                        comparison["summary"]["competitors"][competitor]["paid_addon"] += 1
                    else:
                        comparison["summary"]["competitors"][competitor]["none"] += 1

                category_comparison["features"].append(feature_comp)

            comparison["categories"].append(category_comparison)

        return comparison

    def _identify_our_advantages(self, competitors: List[str]) -> List[Dict[str, Any]]:
        """Identify features where we have clear advantages"""
        advantages = []

        for category_key, category_data in self.FEATURE_MATRIX.items():
            for feature_key, feature_data in category_data["features"].items():
                our_status = feature_data["our_status"]

                # We must have full support to claim advantage
                if our_status != "full":
                    continue

                # Check if we have an explicit advantage note
                if feature_data.get("our_advantage"):
                    advantages.append({
                        "feature": feature_data["name"],
                        "category": category_data["category_name"],
                        "advantage": feature_data["our_advantage"],
                        "advantage_type": "unique_capability",
                        "importance": category_data["importance"],
                        "competitors_behind": []
                    })
                    continue

                # Check if competitors are behind
                competitors_behind = []
                for competitor in competitors:
                    comp_status = feature_data["competitors"].get(competitor, "none")
                    if comp_status in ["basic", "limited", "none", "paid_addon", "limited_by_plan"]:
                        competitors_behind.append({
                            "competitor": competitor,
                            "their_status": comp_status
                        })

                # If most competitors are behind, it's an advantage
                if len(competitors_behind) >= len(competitors) * 0.6:  # 60%+ behind
                    advantages.append({
                        "feature": feature_data["name"],
                        "category": category_data["category_name"],
                        "advantage": f"Superior {feature_data['name'].lower()} compared to competitors",
                        "advantage_type": "competitive_edge",
                        "importance": category_data["importance"],
                        "competitors_behind": competitors_behind
                    })

        return advantages

    def _identify_feature_gaps(self, competitors: List[str]) -> List[Dict[str, Any]]:
        """Identify features where we're behind competitors"""
        gaps = []

        for category_key, category_data in self.FEATURE_MATRIX.items():
            for feature_key, feature_data in category_data["features"].items():
                our_status = feature_data["our_status"]

                # Check if competitors are ahead
                competitors_ahead = []
                for competitor in competitors:
                    comp_status = feature_data["competitors"].get(competitor, "none")
                    our_score = self.FEATURE_STATUS.get(our_status, {}).get("score", 0)
                    comp_score = self.FEATURE_STATUS.get(comp_status, {}).get("score", 0)

                    if comp_score > our_score:
                        competitors_ahead.append({
                            "competitor": competitor,
                            "their_status": comp_status
                        })

                if competitors_ahead:
                    gaps.append({
                        "feature": feature_data["name"],
                        "category": category_data["category_name"],
                        "our_status": our_status,
                        "importance": category_data["importance"],
                        "competitors_ahead": competitors_ahead,
                        "severity": "high" if category_data["importance"] == "critical" else "medium"
                    })

        return gaps

    def _identify_their_gaps(self, competitors: List[str]) -> List[Dict[str, Any]]:
        """Identify features where competitors are behind us"""
        their_gaps = []

        for competitor in competitors:
            competitor_gaps = []

            for category_key, category_data in self.FEATURE_MATRIX.items():
                for feature_key, feature_data in category_data["features"].items():
                    our_status = feature_data["our_status"]
                    comp_status = feature_data["competitors"].get(competitor, "none")

                    our_score = self.FEATURE_STATUS.get(our_status, {}).get("score", 0)
                    comp_score = self.FEATURE_STATUS.get(comp_status, {}).get("score", 0)

                    if our_score > comp_score:
                        competitor_gaps.append({
                            "feature": feature_data["name"],
                            "category": category_data["category_name"],
                            "their_status": comp_status,
                            "our_status": our_status,
                            "our_advantage": feature_data.get("our_advantage"),
                            "importance": category_data["importance"]
                        })

            their_gaps.append({
                "competitor": competitor,
                "gaps": competitor_gaps,
                "total_gaps": len(competitor_gaps)
            })

        return their_gaps

    def _generate_battle_cards(
        self,
        competitors: List[str],
        our_advantages: List[Dict],
        their_gaps: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate battle cards for each competitor"""
        battle_cards = []

        for competitor in competitors:
            # Get gaps for this competitor
            comp_gaps = next((g["gaps"] for g in their_gaps if g["competitor"] == competitor), [])

            # Get high-importance advantages against this competitor
            relevant_advantages = [
                adv for adv in our_advantages
                if any(c["competitor"] == competitor for c in adv.get("competitors_behind", []))
            ]

            battle_card = {
                "competitor": competitor.title(),
                "last_updated": datetime.utcnow().isoformat(),
                "feature_advantages": [
                    {
                        "feature": adv["feature"],
                        "talking_point": adv["advantage"]
                    }
                    for adv in relevant_advantages[:5]  # Top 5
                ],
                "their_limitations": [
                    {
                        "feature": gap["feature"],
                        "their_status": self.FEATURE_STATUS.get(gap["their_status"], {}).get("label", "Limited"),
                        "our_status": "Full Support"
                    }
                    for gap in comp_gaps[:5]  # Top 5
                ],
                "key_talking_points": self._generate_talking_points(competitor, relevant_advantages, comp_gaps)
            }

            battle_cards.append(battle_card)

        return battle_cards

    def _generate_talking_points(
        self,
        competitor: str,
        advantages: List[Dict],
        gaps: List[Dict]
    ) -> List[str]:
        """Generate key talking points for battle card"""
        talking_points = []

        # Based on advantages
        for adv in advantages[:3]:
            if adv.get("our_advantage"):
                talking_points.append(f"✓ {adv['advantage']}")

        # Based on their gaps
        critical_gaps = [g for g in gaps if g["importance"] == "critical"]
        for gap in critical_gaps[:2]:
            status_label = self.FEATURE_STATUS.get(gap["their_status"], {}).get("label", "Limited")
            talking_points.append(f"✗ {competitor.title()}: {status_label} for {gap['feature']}, We: Full Support")

        # Add general positioning
        if len(gaps) >= 5:
            talking_points.append(f"Overall: We offer superior capabilities in {len(gaps)} key features")

        return talking_points

    def _get_recent_updates(self, competitors: List[str]) -> List[Dict[str, Any]]:
        """Get recent competitor feature updates"""
        updates = []

        for competitor in competitors:
            comp_updates = self.RECENT_UPDATES.get(competitor, [])
            for update in comp_updates:
                updates.append({
                    "competitor": competitor.title(),
                    "date": update["date"],
                    "feature": update["feature"],
                    "category": update["category"],
                    "impact": update["impact"],
                    "description": update["description"]
                })

        # Sort by date (most recent first)
        updates.sort(key=lambda x: x["date"], reverse=True)

        return updates

    def _generate_recommendations(
        self,
        our_advantages: List[Dict],
        feature_gaps: List[Dict],
        their_gaps: List[Dict],
        recent_updates: List[Dict]
    ) -> List[str]:
        """Generate feature-based recommendations"""
        recommendations = []

        # Leverage our advantages
        high_importance_advantages = [a for a in our_advantages if a["importance"] in ["critical", "high"]]
        if high_importance_advantages:
            recommendations.append(
                f"Lead with our {len(high_importance_advantages)} high-importance feature advantages"
            )

        # Address our gaps
        critical_gaps = [g for g in feature_gaps if g["importance"] == "critical"]
        if critical_gaps:
            recommendations.append(
                f"Prepare explanations for {len(critical_gaps)} critical feature gaps"
            )

        # Exploit their gaps
        total_competitor_gaps = sum(g["total_gaps"] for g in their_gaps)
        if total_competitor_gaps > 0:
            recommendations.append(
                f"Emphasize competitor limitations in {total_competitor_gaps} features"
            )

        # Recent updates awareness
        if recent_updates:
            recommendations.append(
                f"Be aware of {len(recent_updates)} recent competitor feature updates"
            )

        # General recommendations
        recommendations.append("Use feature comparison matrix in demos to show breadth of capabilities")
        recommendations.append("Highlight features included in base price vs competitor add-ons")

        return recommendations


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing FeatureComparator Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Compare against Salesforce
        state1 = create_initial_state(
            "How do our features compare to Salesforce?",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "industry": "technology"
                }
            }
        )

        agent = FeatureComparator()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Feature Comparison vs Salesforce")
        comparison = result1['feature_comparison']
        print(f"Categories Compared: {comparison['summary']['total_categories']}")
        print(f"Total Features: {comparison['summary']['total_features']}")
        print(f"Our Full Support: {comparison['summary']['our_full_support']}")
        print(f"\nCompetitor Summary:")
        for comp, stats in comparison['summary']['competitors'].items():
            print(f"  {comp.title()}:")
            print(f"    Full Support: {stats['full_support']}")
            print(f"    Basic/Limited: {stats['basic_support']}")
            print(f"    Paid Add-on: {stats['paid_addon']}")
            print(f"    Not Available: {stats['none']}")

        print(f"\nOur Advantages: {len(result1['our_feature_advantages'])}")
        for adv in result1['our_feature_advantages'][:3]:
            print(f"  • {adv['feature']}: {adv['advantage']}")

        # Test case 2: Battle card generation
        state2 = create_initial_state(
            "Generate battle cards for HubSpot and Intercom",
            context={}
        )

        result2 = await agent.process(state2)

        print(f"\n\nTest 2 - Battle Card Generation")
        print(f"Battle Cards Generated: {len(result2['feature_battle_cards'])}")
        for bc in result2['feature_battle_cards']:
            print(f"\n{bc['competitor']} Battle Card:")
            print(f"  Feature Advantages: {len(bc['feature_advantages'])}")
            for adv in bc['feature_advantages'][:2]:
                print(f"    • {adv['feature']}: {adv['talking_point']}")
            print(f"  Their Limitations: {len(bc['their_limitations'])}")
            for lim in bc['their_limitations'][:2]:
                print(f"    • {lim['feature']}: They have {lim['their_status']}, We have {lim['our_status']}")

        # Test case 3: Feature gap analysis
        state3 = create_initial_state(
            "What are our feature gaps compared to competitors?",
            context={}
        )

        result3 = await agent.process(state3)

        print(f"\n\nTest 3 - Feature Gap Analysis")
        print(f"Our Feature Gaps: {len(result3['our_feature_gaps'])}")
        for gap in result3['our_feature_gaps'][:3]:
            print(f"  • {gap['feature']} ({gap['category']})")
            print(f"    Our Status: {gap['our_status']}")
            print(f"    Severity: {gap['severity']}")
            print(f"    Competitors Ahead: {len(gap['competitors_ahead'])}")

        print(f"\nRecommendations:")
        for rec in result3['feature_recommendations']:
            print(f"  • {rec}")

        print(f"\nConfidence: {result3['response_confidence']:.2f}")

    asyncio.run(test())
