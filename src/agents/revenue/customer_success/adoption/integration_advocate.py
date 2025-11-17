"""
Integration Advocate Agent - TASK-2035

Recommends relevant integrations, helps configure connections, demonstrates integration value,
and measures ecosystem impact to increase product stickiness.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, UTC

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("integration_advocate", tier="revenue", category="customer_success")
class IntegrationAdvocateAgent(BaseAgent):
    """
    Integration Advocate Agent.

    Drives integration adoption by:
    - Identifying relevant integration opportunities
    - Recommending integrations based on tech stack
    - Providing integration setup guidance
    - Measuring integration ROI and value
    - Tracking integration health and usage
    - Demonstrating ecosystem benefits
    """

    # Integration categories
    INTEGRATION_CATEGORIES = {
        "communication": {
            "value_tier": "high",
            "stickiness": 90,
            "common_tools": ["Slack", "Microsoft Teams", "Gmail", "Outlook"]
        },
        "crm": {
            "value_tier": "critical",
            "stickiness": 95,
            "common_tools": ["Salesforce", "HubSpot", "Pipedrive", "Zoho CRM"]
        },
        "project_management": {
            "value_tier": "high",
            "stickiness": 85,
            "common_tools": ["Jira", "Asana", "Monday.com", "Trello"]
        },
        "storage": {
            "value_tier": "medium",
            "stickiness": 70,
            "common_tools": ["Google Drive", "Dropbox", "OneDrive", "Box"]
        },
        "analytics": {
            "value_tier": "medium",
            "stickiness": 75,
            "common_tools": ["Google Analytics", "Mixpanel", "Amplitude", "Segment"]
        },
        "customer_support": {
            "value_tier": "high",
            "stickiness": 88,
            "common_tools": ["Zendesk", "Intercom", "Freshdesk", "Help Scout"]
        },
        "marketing": {
            "value_tier": "medium",
            "stickiness": 72,
            "common_tools": ["Mailchimp", "Marketo", "Pardot", "ActiveCampaign"]
        },
        "development": {
            "value_tier": "medium",
            "stickiness": 80,
            "common_tools": ["GitHub", "GitLab", "Bitbucket", "Azure DevOps"]
        },
        "accounting": {
            "value_tier": "high",
            "stickiness": 85,
            "common_tools": ["QuickBooks", "Xero", "NetSuite", "Sage"]
        }
    }

    # Integration maturity levels
    MATURITY_LEVELS = {
        "isolated": {"score_range": (0, 20), "integration_count": 0},
        "basic": {"score_range": (21, 40), "integration_count": 2},
        "connected": {"score_range": (41, 65), "integration_count": 5},
        "integrated": {"score_range": (66, 85), "integration_count": 10},
        "ecosystem": {"score_range": (86, 100), "integration_count": 15}
    }

    def __init__(self):
        config = AgentConfig(
            name="integration_advocate",
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
        Analyze integration opportunities and provide recommendations.

        Args:
            state: Current agent state with integration data

        Returns:
            Updated state with integration recommendations
        """
        self.logger.info("integration_advocacy_started")

        state = self.update_state(state)

        customer_id = state.get("customer_id")
        tech_stack = state.get("entities", {}).get("tech_stack", {})
        current_integrations = state.get("entities", {}).get("current_integrations", [])
        customer_metadata = state.get("customer_metadata", {})
        integration_usage = state.get("entities", {}).get("integration_usage", {})

        self.logger.debug(
            "integration_advocacy_details",
            customer_id=customer_id,
            integrations_active=len(current_integrations),
            tools_in_stack=len(tech_stack.get("tools", []))
        )

        # Analyze current integration state
        integration_analysis = self._analyze_integration_state(
            current_integrations,
            integration_usage,
            tech_stack
        )

        # Identify integration opportunities
        opportunities = self._identify_integration_opportunities(
            tech_stack,
            current_integrations,
            customer_metadata
        )

        # Calculate integration value
        value_analysis = self._calculate_integration_value(
            opportunities,
            integration_analysis,
            customer_metadata
        )

        # Generate recommendations
        recommendations = self._generate_integration_recommendations(
            opportunities,
            integration_analysis,
            customer_metadata
        )

        # Create integration roadmap
        roadmap = self._create_integration_roadmap(
            recommendations,
            integration_analysis
        )

        # Format response
        response = self._format_integration_report(
            integration_analysis,
            opportunities,
            value_analysis,
            recommendations,
            roadmap
        )

        state["agent_response"] = response
        state["integration_maturity"] = integration_analysis["maturity_level"]
        state["integration_score"] = integration_analysis["integration_score"]
        state["integration_opportunities"] = len(opportunities)
        state["ecosystem_value_score"] = value_analysis["ecosystem_value_score"]
        state["integration_analysis"] = integration_analysis
        state["response_confidence"] = 0.87
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "integration_advocacy_completed",
            customer_id=customer_id,
            maturity=integration_analysis["maturity_level"],
            opportunities=len(opportunities),
            ecosystem_value=value_analysis["ecosystem_value_score"]
        )

        return state

    def _analyze_integration_state(
        self,
        current_integrations: List[Dict[str, Any]],
        integration_usage: Dict[str, Any],
        tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze current integration state.

        Args:
            current_integrations: List of active integrations
            integration_usage: Integration usage metrics
            tech_stack: Customer's technology stack

        Returns:
            Comprehensive integration analysis
        """
        integration_count = len(current_integrations)

        # Categorize integrations
        integrations_by_category = self._categorize_integrations(current_integrations)

        # Calculate integration health
        active_integrations = sum(
            1 for integration in current_integrations
            if integration.get("status") == "active" and integration.get("sync_errors", 0) == 0
        )

        integration_health_pct = (active_integrations / integration_count * 100) if integration_count > 0 else 0

        # Calculate usage metrics
        avg_syncs_per_day = integration_usage.get("avg_syncs_per_day", 0)
        data_flowing = integration_usage.get("data_flowing", False)

        # Calculate integration score
        integration_score = self._calculate_integration_score(
            integration_count,
            integrations_by_category,
            integration_health_pct,
            avg_syncs_per_day
        )

        # Determine maturity level
        maturity_level = self._determine_maturity_level(integration_score, integration_count)

        # Identify gaps
        integration_gaps = self._identify_integration_gaps(
            integrations_by_category,
            tech_stack
        )

        # Calculate stickiness contribution
        stickiness_score = self._calculate_stickiness(integrations_by_category)

        return {
            "integration_score": round(integration_score, 1),
            "maturity_level": maturity_level,
            "integration_count": integration_count,
            "active_integrations": active_integrations,
            "integration_health": round(integration_health_pct, 1),
            "integrations_by_category": integrations_by_category,
            "avg_syncs_per_day": avg_syncs_per_day,
            "data_flowing": data_flowing,
            "integration_gaps": integration_gaps,
            "stickiness_score": stickiness_score,
            "analyzed_at": datetime.now(UTC).isoformat()
        }

    def _categorize_integrations(
        self,
        current_integrations: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Categorize existing integrations."""
        categorized = {category: [] for category in self.INTEGRATION_CATEGORIES.keys()}

        for integration in current_integrations:
            tool_name = integration.get("tool_name", "")

            # Find matching category
            for category, info in self.INTEGRATION_CATEGORIES.items():
                if any(tool.lower() in tool_name.lower() for tool in info["common_tools"]):
                    categorized[category].append(tool_name)
                    break

        return categorized

    def _calculate_integration_score(
        self,
        integration_count: int,
        integrations_by_category: Dict[str, List[str]],
        health_pct: float,
        avg_syncs: float
    ) -> float:
        """Calculate overall integration score (0-100)."""
        # Count score (max at 15 integrations)
        count_score = min(integration_count / 15 * 100, 100)

        # Diversity score (reward using multiple categories)
        categories_used = sum(1 for integrations in integrations_by_category.values() if integrations)
        diversity_score = (categories_used / len(self.INTEGRATION_CATEGORIES)) * 100

        # Health score
        health_score = health_pct

        # Activity score (max at 100 syncs/day)
        activity_score = min(avg_syncs / 100 * 100, 100)

        # Weighted average
        score = (count_score * 0.3) + (diversity_score * 0.3) + (health_score * 0.25) + (activity_score * 0.15)

        return min(score, 100)

    def _determine_maturity_level(self, score: float, integration_count: int) -> str:
        """Determine integration maturity level."""
        for level, criteria in self.MATURITY_LEVELS.items():
            score_min, score_max = criteria["score_range"]
            if score_min <= score <= score_max:
                return level
        return "isolated"

    def _identify_integration_gaps(
        self,
        integrations_by_category: Dict[str, List[str]],
        tech_stack: Dict[str, Any]
    ) -> List[str]:
        """Identify gaps in integration coverage."""
        gaps = []

        # Check for missing critical integrations
        if not integrations_by_category.get("crm"):
            gaps.append("No CRM integration - missing critical revenue data sync")

        if not integrations_by_category.get("communication"):
            gaps.append("No communication tool integration - limited team collaboration")

        # Check if they have tools but no integrations
        tools = tech_stack.get("tools", [])

        for tool in tools:
            tool_lower = tool.lower()
            is_integrated = any(
                tool_lower in integrated_tool.lower()
                for integrations in integrations_by_category.values()
                for integrated_tool in integrations
            )

            if not is_integrated and len(gaps) < 5:
                gaps.append(f"{tool} in tech stack but not integrated - potential data silos")

        if not gaps:
            gaps.append("No major integration gaps identified")

        return gaps[:5]

    def _calculate_stickiness(self, integrations_by_category: Dict[str, List[str]]) -> int:
        """Calculate stickiness contribution from integrations."""
        total_stickiness = 0

        for category, integrations in integrations_by_category.items():
            if integrations:
                category_info = self.INTEGRATION_CATEGORIES.get(category, {})
                stickiness = category_info.get("stickiness", 50)
                # Each integration in category contributes (diminishing returns)
                contribution = stickiness * (1 - (0.2 * (len(integrations) - 1)))
                total_stickiness += contribution

        # Normalize to 0-100
        return min(int(total_stickiness / 5), 100)

    def _identify_integration_opportunities(
        self,
        tech_stack: Dict[str, Any],
        current_integrations: List[Dict[str, Any]],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify integration opportunities based on tech stack."""
        opportunities = []
        industry = customer_metadata.get("industry", "general")
        tools = tech_stack.get("tools", [])

        integrated_tools = {
            integration.get("tool_name", "").lower()
            for integration in current_integrations
        }

        # Check each tool in their stack
        for tool in tools:
            tool_lower = tool.lower()

            if tool_lower in integrated_tools:
                continue  # Already integrated

            # Find category for this tool
            for category, info in self.INTEGRATION_CATEGORIES.items():
                if any(common_tool.lower() in tool_lower for common_tool in info["common_tools"]):
                    opportunities.append({
                        "tool": tool,
                        "category": category,
                        "value_tier": info["value_tier"],
                        "stickiness": info["stickiness"],
                        "priority": self._determine_priority(info["value_tier"]),
                        "use_case": self._generate_use_case(category, industry, tool),
                        "setup_complexity": self._estimate_complexity(category),
                        "business_impact": self._estimate_impact(category)
                    })
                    break

        # Add recommended integrations even if not in tech stack
        if not any(opp["category"] == "crm" for opp in opportunities):
            # Recommend popular CRM if none integrated
            recommended_crm = "Salesforce" if customer_metadata.get("plan") == "enterprise" else "HubSpot"
            if recommended_crm.lower() not in integrated_tools:
                opportunities.append({
                    "tool": recommended_crm,
                    "category": "crm",
                    "value_tier": "critical",
                    "stickiness": 95,
                    "priority": "critical",
                    "use_case": f"Sync {industry} customer data and pipeline for unified view",
                    "setup_complexity": "medium",
                    "business_impact": "High - centralized customer data"
                })

        # Sort by priority and value
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        opportunities.sort(
            key=lambda x: (priority_order.get(x["priority"], 3), -x["stickiness"])
        )

        return opportunities[:8]

    def _determine_priority(self, value_tier: str) -> str:
        """Determine priority from value tier."""
        tier_map = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        return tier_map.get(value_tier, "medium")

    def _generate_use_case(self, category: str, industry: str, tool: str) -> str:
        """Generate specific use case for integration."""
        use_cases = {
            "crm": f"Automatically sync {industry} customer data and deal stages",
            "communication": f"Send notifications and updates directly to team channels",
            "project_management": f"Create and update {industry} tasks from workflow events",
            "storage": f"Attach files and documents seamlessly to records",
            "analytics": f"Track {industry} metrics and user behavior",
            "customer_support": f"Link support tickets to customer records",
            "marketing": f"Sync {industry} leads and campaign data",
            "development": f"Link code commits and deployments to projects",
            "accounting": f"Sync {industry} invoices and payment data"
        }

        return use_cases.get(category, f"Integrate {tool} for seamless data flow")

    def _estimate_complexity(self, category: str) -> str:
        """Estimate integration setup complexity."""
        complexity_map = {
            "communication": "low",
            "storage": "low",
            "project_management": "medium",
            "crm": "medium",
            "customer_support": "medium",
            "marketing": "medium",
            "analytics": "high",
            "development": "medium",
            "accounting": "high"
        }
        return complexity_map.get(category, "medium")

    def _estimate_impact(self, category: str) -> str:
        """Estimate business impact of integration."""
        impact_map = {
            "crm": "High - Unified customer view and revenue insights",
            "communication": "High - Improved team collaboration and visibility",
            "project_management": "Medium - Streamlined workflow coordination",
            "storage": "Medium - Easier file access and sharing",
            "analytics": "Medium - Better data-driven decisions",
            "customer_support": "High - Faster issue resolution",
            "marketing": "Medium - Improved lead management",
            "development": "Medium - Better release tracking",
            "accounting": "High - Accurate financial data"
        }
        return impact_map.get(category, "Medium - Improved efficiency")

    def _calculate_integration_value(
        self,
        opportunities: List[Dict[str, Any]],
        integration_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate value from integration opportunities."""
        # Calculate potential stickiness increase
        current_stickiness = integration_analysis["stickiness_score"]

        potential_stickiness_gain = sum(
            opp["stickiness"] * 0.3  # 30% of max contribution per integration
            for opp in opportunities[:5]
        ) / 5

        target_stickiness = min(current_stickiness + potential_stickiness_gain, 100)

        # Calculate ecosystem value score
        critical_count = sum(1 for opp in opportunities if opp["value_tier"] == "critical")
        high_count = sum(1 for opp in opportunities if opp["value_tier"] == "high")

        ecosystem_value_score = min(
            (critical_count * 20) + (high_count * 10) + (integration_analysis["integration_count"] * 5),
            100
        )

        # Estimate efficiency gains
        time_savings_per_integration = 5  # hours per month per integration
        potential_time_savings = len(opportunities[:5]) * time_savings_per_integration

        return {
            "ecosystem_value_score": ecosystem_value_score,
            "current_stickiness": current_stickiness,
            "potential_stickiness": round(target_stickiness, 1),
            "stickiness_gain": round(potential_stickiness_gain, 1),
            "critical_integrations": critical_count,
            "high_value_integrations": high_count,
            "potential_time_savings_hours": potential_time_savings
        }

    def _generate_integration_recommendations(
        self,
        opportunities: List[Dict[str, Any]],
        integration_analysis: Dict[str, Any],
        customer_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized integration recommendations."""
        recommendations = []

        for opp in opportunities[:6]:
            recommendation = {
                "tool": opp["tool"],
                "category": opp["category"],
                "priority": opp["priority"],
                "value_tier": opp["value_tier"],
                "use_case": opp["use_case"],
                "business_impact": opp["business_impact"],
                "setup_steps": self._get_setup_steps(opp["category"], opp["tool"]),
                "setup_complexity": opp["setup_complexity"],
                "estimated_setup_time": self._estimate_setup_time(opp["setup_complexity"]),
                "stickiness_contribution": f"+{int(opp['stickiness'] * 0.3)} points"
            }

            recommendations.append(recommendation)

        return recommendations

    def _get_setup_steps(self, category: str, tool: str) -> List[str]:
        """Get setup steps for integration."""
        generic_steps = [
            f"Connect {tool} account via OAuth",
            "Configure sync settings and field mappings",
            "Test data flow with sample records",
            "Enable two-way sync if needed",
            "Monitor initial sync and resolve any errors"
        ]

        specific_steps = {
            "crm": [
                f"Authenticate {tool} account",
                "Map CRM fields to product fields",
                "Configure sync frequency (real-time or scheduled)",
                "Set up contact and deal synchronization",
                "Test with sample customer records"
            ],
            "communication": [
                f"Install {tool} app from marketplace",
                "Authorize workspace access",
                "Configure notification preferences",
                "Set up channel routing rules",
                "Test with sample notification"
            ]
        }

        return specific_steps.get(category, generic_steps)

    def _estimate_setup_time(self, complexity: str) -> str:
        """Estimate setup time based on complexity."""
        time_map = {
            "low": "15-30 minutes",
            "medium": "1-2 hours",
            "high": "3-5 hours"
        }
        return time_map.get(complexity, "1-2 hours")

    def _create_integration_roadmap(
        self,
        recommendations: List[Dict[str, Any]],
        integration_analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Create phased integration implementation roadmap."""
        roadmap = {
            "week_1": [],
            "week_2_4": [],
            "month_2_3": []
        }

        # Week 1: Critical and low complexity
        for rec in recommendations:
            if rec["priority"] == "critical" or (rec["priority"] == "high" and rec["setup_complexity"] == "low"):
                roadmap["week_1"].append(
                    f"Integrate {rec['tool']} ({rec['category']})"
                )

        # Weeks 2-4: High priority and medium complexity
        for rec in recommendations:
            if rec["priority"] == "high" and rec["setup_complexity"] == "medium":
                roadmap["week_2_4"].append(
                    f"Integrate {rec['tool']} ({rec['category']})"
                )

        # Months 2-3: Remaining and high complexity
        for rec in recommendations:
            if rec["priority"] in ["medium", "low"] or rec["setup_complexity"] == "high":
                roadmap["month_2_3"].append(
                    f"Integrate {rec['tool']} ({rec['category']})"
                )

        # Limit items
        roadmap["week_1"] = roadmap["week_1"][:2]
        roadmap["week_2_4"] = roadmap["week_2_4"][:3]
        roadmap["month_2_3"] = roadmap["month_2_3"][:3]

        return roadmap

    def _format_integration_report(
        self,
        integration_analysis: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        value_analysis: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        roadmap: Dict[str, List[str]]
    ) -> str:
        """Format integration advocacy report."""
        maturity = integration_analysis["maturity_level"]
        score = integration_analysis["integration_score"]

        maturity_emoji = {
            "isolated": "????",
            "basic": "????",
            "connected": "????",
            "integrated": "????",
            "ecosystem": "????"
        }

        report = f"""**{maturity_emoji.get(maturity, '????')} Integration Advocacy Report**

**Maturity Level:** {maturity.upper()}
**Integration Score:** {score}/100
**Active Integrations:** {integration_analysis['active_integrations']}/{integration_analysis['integration_count']}
**Integration Health:** {integration_analysis['integration_health']}%
**Stickiness Score:** {integration_analysis['stickiness_score']}/100

**Current Integrations by Category:**
"""

        for category, tools in integration_analysis["integrations_by_category"].items():
            if tools:
                report += f"- {category.replace('_', ' ').title()}: {', '.join(tools)}\n"

        # Integration gaps
        if integration_analysis["integration_gaps"]:
            report += "\n**?????? Integration Gaps:**\n"
            for gap in integration_analysis["integration_gaps"][:4]:
                report += f"- {gap}\n"

        # Value analysis
        report += f"\n**???? Ecosystem Value Analysis:**\n"
        report += f"- Current Stickiness: {value_analysis['current_stickiness']}/100\n"
        report += f"- Potential Stickiness: {value_analysis['potential_stickiness']}/100 (+{value_analysis['stickiness_gain']})\n"
        report += f"- Ecosystem Value Score: {value_analysis['ecosystem_value_score']}/100\n"
        report += f"- Critical Integrations Available: {value_analysis['critical_integrations']}\n"
        report += f"- Potential Time Savings: {value_analysis['potential_time_savings_hours']} hours/month\n"

        # Top opportunities
        if opportunities:
            report += "\n**???? Top Integration Opportunities:**\n"
            for i, opp in enumerate(opportunities[:5], 1):
                priority_icon = "????" if opp["priority"] == "critical" else "????" if opp["priority"] == "high" else "????"
                report += f"\n{i}. **{opp['tool']}** ({opp['category']}) {priority_icon}\n"
                report += f"   - Value Tier: {opp['value_tier'].title()}\n"
                report += f"   - Use Case: {opp['use_case']}\n"
                report += f"   - Impact: {opp['business_impact']}\n"
                report += f"   - Stickiness: +{opp['stickiness']} points\n"

        # Implementation guide
        if recommendations:
            report += "\n**???? Integration Setup Guide:**\n"
            for i, rec in enumerate(recommendations[:3], 1):
                report += f"\n**{i}. {rec['tool']}** ({rec['setup_complexity']} complexity)\n"
                report += f"- Setup Time: {rec['estimated_setup_time']}\n"
                report += f"- Steps:\n"
                for step in rec["setup_steps"][:3]:
                    report += f"  ??? {step}\n"

        # Roadmap
        report += "\n**??????? Integration Roadmap:**\n"
        for phase, items in roadmap.items():
            if items:
                phase_label = phase.replace('_', ' ').title().replace('Week', 'Week').replace('Month', 'Months')
                report += f"\n**{phase_label}:**\n"
                for item in items:
                    report += f"- {item}\n"

        return report


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 70)
        print("Testing Integration Advocate Agent (TASK-2035)")
        print("=" * 70)

        agent = IntegrationAdvocateAgent()

        # Test 1: Low integration maturity
        print("\n\nTest 1: Isolated/Basic Integration")
        print("-" * 70)

        state1 = create_initial_state(
            "Analyze integration opportunities",
            context={
                "customer_id": "cust_isolated",
                "customer_metadata": {
                    "plan": "premium",
                    "industry": "healthcare"
                }
            }
        )
        state1["entities"] = {
            "tech_stack": {
                "tools": ["Salesforce", "Slack", "Google Drive", "Jira", "Zendesk"]
            },
            "current_integrations": [
                {"tool_name": "Slack", "status": "active", "sync_errors": 0}
            ],
            "integration_usage": {
                "avg_syncs_per_day": 15,
                "data_flowing": True
            }
        }

        result1 = await agent.process(state1)

        print(f"Maturity: {result1['integration_maturity']}")
        print(f"Score: {result1['integration_score']}/100")
        print(f"Opportunities: {result1['integration_opportunities']}")
        print(f"Ecosystem Value: {result1['ecosystem_value_score']}/100")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Advanced integration
        print("\n\n" + "=" * 70)
        print("Test 2: Integrated/Ecosystem Level")
        print("-" * 70)

        state2 = create_initial_state(
            "Review integration status",
            context={
                "customer_id": "cust_integrated",
                "customer_metadata": {
                    "plan": "enterprise",
                    "industry": "technology"
                }
            }
        )
        state2["entities"] = {
            "tech_stack": {
                "tools": ["Salesforce", "Slack", "GitHub", "Jira", "Zendesk",
                         "Google Analytics", "HubSpot", "Mailchimp"]
            },
            "current_integrations": [
                {"tool_name": "Salesforce", "status": "active", "sync_errors": 0},
                {"tool_name": "Slack", "status": "active", "sync_errors": 0},
                {"tool_name": "GitHub", "status": "active", "sync_errors": 0},
                {"tool_name": "Jira", "status": "active", "sync_errors": 0},
                {"tool_name": "Zendesk", "status": "active", "sync_errors": 0},
                {"tool_name": "Google Analytics", "status": "active", "sync_errors": 0},
                {"tool_name": "HubSpot", "status": "active", "sync_errors": 1}
            ],
            "integration_usage": {
                "avg_syncs_per_day": 250,
                "data_flowing": True
            }
        }

        result2 = await agent.process(state2)

        print(f"Maturity: {result2['integration_maturity']}")
        print(f"Score: {result2['integration_score']}/100")
        print(f"\nResponse preview:\n{result2['agent_response'][:500]}...")

    asyncio.run(test())
