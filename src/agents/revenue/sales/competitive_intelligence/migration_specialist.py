"""
Migration Specialist Agent - TASK-1057

Helps prospects migrate from competitors, provides migration guides,
calculates migration effort, and offers migration support services.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("migration_specialist", tier="revenue", category="sales")
class MigrationSpecialist(BaseAgent):
    """
    Migration Specialist Agent - Specialist in customer migration from competitors.

    Handles:
    - Help prospects migrate from competitors
    - Provide migration guides and playbooks
    - Calculate migration effort and timeline
    - Offer migration support services
    - Address migration concerns and risks
    """

    # Migration playbooks for each competitor
    MIGRATION_PLAYBOOKS = {
        "salesforce": {
            "competitor": "Salesforce",
            "migration_difficulty": "medium_high",
            "typical_timeline_weeks": 4,
            "phases": [
                {
                    "phase": "Discovery & Planning",
                    "duration_weeks": 1,
                    "activities": [
                        "Audit current Salesforce configuration",
                        "Identify custom fields and objects",
                        "Document workflows and automation",
                        "Map user roles and permissions",
                        "Identify integration points"
                    ]
                },
                {
                    "phase": "Data Migration",
                    "duration_weeks": 2,
                    "activities": [
                        "Export data from Salesforce",
                        "Clean and transform data",
                        "Import to our platform",
                        "Validate data integrity",
                        "Migrate attachments and files"
                    ]
                },
                {
                    "phase": "Configuration & Testing",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Recreate workflows in our platform",
                        "Configure automation rules",
                        "Set up integrations",
                        "User acceptance testing",
                        "Train team on new platform"
                    ]
                },
                {
                    "phase": "Cutover & Go-Live",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Final data sync",
                        "Switch DNS/integrations",
                        "Go live with team",
                        "Monitor for issues",
                        "Decommission Salesforce"
                    ]
                }
            ],
            "data_objects": [
                "Accounts", "Contacts", "Leads", "Opportunities", "Cases",
                "Activities", "Tasks", "Events", "Custom Objects"
            ],
            "common_challenges": [
                "Complex custom configurations",
                "Large data volumes",
                "Many integrations to migrate",
                "User adoption and training"
            ]
        },
        "hubspot": {
            "competitor": "HubSpot",
            "migration_difficulty": "easy_medium",
            "typical_timeline_weeks": 2,
            "phases": [
                {
                    "phase": "Discovery & Planning",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Review HubSpot data structure",
                        "Identify marketing automation workflows",
                        "Document contact lists and segments",
                        "Map deal pipeline stages",
                        "Identify key integrations"
                    ]
                },
                {
                    "phase": "Data Migration",
                    "duration_weeks": 1,
                    "activities": [
                        "Export contacts, companies, deals",
                        "Export email templates and sequences",
                        "Import to our platform",
                        "Validate data quality",
                        "Migrate forms and landing pages"
                    ]
                },
                {
                    "phase": "Configuration & Testing",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Recreate workflows and sequences",
                        "Set up email templates",
                        "Configure deal pipeline",
                        "Test automation",
                        "Train team"
                    ]
                }
            ],
            "data_objects": [
                "Contacts", "Companies", "Deals", "Tickets",
                "Email Templates", "Workflows", "Lists", "Forms"
            ],
            "common_challenges": [
                "Marketing automation complexity",
                "Email sequences and templates",
                "Contact list segmentation"
            ]
        },
        "zendesk": {
            "competitor": "Zendesk",
            "migration_difficulty": "easy",
            "typical_timeline_weeks": 2,
            "phases": [
                {
                    "phase": "Discovery & Planning",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Review Zendesk ticket structure",
                        "Document SLA policies",
                        "Identify macros and triggers",
                        "Map agent roles and groups",
                        "Review help center content"
                    ]
                },
                {
                    "phase": "Data Migration",
                    "duration_weeks": 1,
                    "activities": [
                        "Export tickets and conversations",
                        "Export help center articles",
                        "Import tickets to our platform",
                        "Migrate knowledge base content",
                        "Preserve ticket history"
                    ]
                },
                {
                    "phase": "Configuration & Go-Live",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Set up SLA policies",
                        "Configure automation rules",
                        "Set up help center",
                        "Train support team",
                        "Go live"
                    ]
                }
            ],
            "data_objects": [
                "Tickets", "Users", "Organizations", "Help Center Articles",
                "Macros", "Triggers", "Automations", "Views"
            ],
            "common_challenges": [
                "Ticket history preservation",
                "Help center migration",
                "Macro and trigger recreation"
            ]
        },
        "intercom": {
            "competitor": "Intercom",
            "migration_difficulty": "easy",
            "typical_timeline_weeks": 1,
            "phases": [
                {
                    "phase": "Discovery & Planning",
                    "duration_weeks": 0.25,
                    "activities": [
                        "Review Intercom messenger setup",
                        "Document conversation workflows",
                        "Identify bots and automation",
                        "Review help center content"
                    ]
                },
                {
                    "phase": "Data Migration",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Export users and conversations",
                        "Export help center articles",
                        "Import to our platform",
                        "Validate data"
                    ]
                },
                {
                    "phase": "Configuration & Go-Live",
                    "duration_weeks": 0.25,
                    "activities": [
                        "Install our messenger widget",
                        "Recreate automation rules",
                        "Set up help center",
                        "Train team and go live"
                    ]
                }
            ],
            "data_objects": [
                "Users", "Conversations", "Messages", "Help Articles",
                "Bots", "Automation Rules", "Product Tours"
            ],
            "common_challenges": [
                "Conversation history preservation",
                "Bot recreation",
                "Widget installation"
            ]
        },
        "freshdesk": {
            "competitor": "Freshdesk",
            "migration_difficulty": "easy",
            "typical_timeline_weeks": 1,
            "phases": [
                {
                    "phase": "Discovery & Planning",
                    "duration_weeks": 0.25,
                    "activities": [
                        "Review Freshdesk setup",
                        "Document automation rules",
                        "Identify ticket fields and statuses"
                    ]
                },
                {
                    "phase": "Data Migration",
                    "duration_weeks": 0.5,
                    "activities": [
                        "Export tickets and contacts",
                        "Import to our platform",
                        "Validate data integrity"
                    ]
                },
                {
                    "phase": "Configuration & Go-Live",
                    "duration_weeks": 0.25,
                    "activities": [
                        "Configure automation",
                        "Set up email forwarding",
                        "Train team and go live"
                    ]
                }
            ],
            "data_objects": [
                "Tickets", "Contacts", "Companies", "Solutions Articles",
                "Automation Rules", "Email Templates"
            ],
            "common_challenges": [
                "Ticket history preservation",
                "Automation rule recreation"
            ]
        }
    }

    # Migration support services
    MIGRATION_SERVICES = {
        "concierge_migration": {
            "name": "Concierge Migration Service",
            "description": "We handle everything - you focus on your business",
            "included_in": ["enterprise", "growth"],
            "services": [
                "Dedicated migration specialist assigned",
                "Complete data export and import",
                "Configuration matching current setup",
                "Integration setup and testing",
                "Team training sessions",
                "Post-migration support (30 days)"
            ],
            "timeline": "2-4 weeks",
            "customer_effort": "minimal"
        },
        "guided_migration": {
            "name": "Guided Migration",
            "description": "We guide you through each step",
            "included_in": ["startup", "growth"],
            "services": [
                "Step-by-step migration guide",
                "Migration planning session",
                "Data import assistance",
                "Configuration review",
                "Team training webinar",
                "Post-migration support (14 days)"
            ],
            "timeline": "1-3 weeks",
            "customer_effort": "low"
        },
        "self_service": {
            "name": "Self-Service Migration",
            "description": "Comprehensive tools and documentation",
            "included_in": ["all_plans"],
            "services": [
                "Detailed migration documentation",
                "Data import templates",
                "Video tutorials",
                "Email support",
                "Community forum access"
            ],
            "timeline": "1-2 weeks",
            "customer_effort": "medium"
        },
        "parallel_run": {
            "name": "Parallel Run Option",
            "description": "Run both systems during transition",
            "included_in": ["enterprise"],
            "services": [
                "Extended parallel access",
                "Bi-directional sync (if needed)",
                "Flexible cutover timing",
                "Risk mitigation"
            ],
            "timeline": "flexible",
            "customer_effort": "low"
        }
    }

    # Migration success stories
    SUCCESS_STORIES = {
        "salesforce_migration": {
            "from_competitor": "salesforce",
            "company": "TechCorp",
            "company_size": 300,
            "migration_time": "3 weeks",
            "records_migrated": 500000,
            "outcome": "Successful migration with 95% user adoption in first week",
            "quote": "The migration was smoother than we expected. We're now more productive than ever."
        },
        "hubspot_migration": {
            "from_competitor": "hubspot",
            "company": "GrowthCo",
            "company_size": 80,
            "migration_time": "1 week",
            "records_migrated": 100000,
            "outcome": "Zero downtime migration, all automation recreated",
            "quote": "Switching was the best decision. We're saving thousands and getting more features."
        },
        "zendesk_migration": {
            "from_competitor": "zendesk",
            "company": "SupportFirst",
            "company_size": 50,
            "migration_time": "1.5 weeks",
            "records_migrated": 50000,
            "outcome": "Complete ticket history preserved, team trained in 2 days",
            "quote": "Much easier platform to use. Our team was productive immediately."
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="migration_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
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
        """Process migration planning"""
        self.logger.info("migration_specialist_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Identify source competitor
        source_competitor = self._identify_source_competitor(message, state)

        # Generate migration plan
        migration_plan = self._generate_migration_plan(source_competitor, customer_metadata)

        # Calculate effort and timeline
        effort_estimate = self._calculate_effort(source_competitor, customer_metadata)

        # Recommend migration services
        recommended_services = self._recommend_services(customer_metadata)

        # Address migration concerns
        migration_concerns = self._address_concerns(source_competitor)

        # Get success stories
        success_stories = self._get_success_stories(source_competitor)

        # Generate migration checklist
        checklist = self._generate_checklist(source_competitor, customer_metadata)

        # Calculate confidence
        confidence = 0.87

        # Update state
        state["migration_plan"] = migration_plan
        state["migration_effort_estimate"] = effort_estimate
        state["migration_services"] = recommended_services
        state["migration_concerns"] = migration_concerns
        state["migration_success_stories"] = success_stories
        state["migration_checklist"] = checklist
        state["response_confidence"] = confidence
        state["status"] = "resolved"

        self.logger.info(
            "migration_specialist_completed",
            source_competitor=source_competitor,
            estimated_timeline_weeks=effort_estimate.get("timeline_weeks")
        )

        return state

    def _identify_source_competitor(self, message: str, state: AgentState) -> str:
        """Identify which competitor they're migrating from"""
        message_lower = message.lower()

        for competitor in self.MIGRATION_PLAYBOOKS.keys():
            if competitor in message_lower:
                return competitor

        # Check state
        competitors = state.get("mentioned_competitors", [])
        if competitors:
            return competitors[0]

        return "generic"

    def _generate_migration_plan(
        self,
        source_competitor: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate detailed migration plan"""

        if source_competitor not in self.MIGRATION_PLAYBOOKS:
            return self._generic_migration_plan()

        playbook = self.MIGRATION_PLAYBOOKS[source_competitor]

        plan = {
            "from_system": playbook["competitor"],
            "to_system": "Our Platform",
            "difficulty": playbook["migration_difficulty"],
            "estimated_timeline_weeks": playbook["typical_timeline_weeks"],
            "phases": playbook["phases"],
            "data_objects_to_migrate": playbook["data_objects"],
            "common_challenges": playbook["common_challenges"],
            "risk_level": self._assess_risk_level(playbook["migration_difficulty"]),
            "recommended_approach": self._recommend_approach(playbook, customer_metadata)
        }

        return plan

    def _generic_migration_plan(self) -> Dict[str, Any]:
        """Generate generic migration plan"""
        return {
            "from_system": "Current System",
            "to_system": "Our Platform",
            "difficulty": "medium",
            "estimated_timeline_weeks": 2,
            "phases": [
                {
                    "phase": "Discovery",
                    "duration_weeks": 0.5,
                    "activities": ["Audit current system", "Plan migration"]
                },
                {
                    "phase": "Migration",
                    "duration_weeks": 1,
                    "activities": ["Export data", "Import to our platform", "Validate"]
                },
                {
                    "phase": "Go-Live",
                    "duration_weeks": 0.5,
                    "activities": ["Train team", "Go live", "Monitor"]
                }
            ],
            "risk_level": "low_medium"
        }

    def _calculate_effort(
        self,
        source_competitor: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate migration effort and timeline"""

        company_size = customer_metadata.get("company_size", 50)
        data_volume = customer_metadata.get("data_volume", "medium")

        if source_competitor not in self.MIGRATION_PLAYBOOKS:
            playbook = None
            base_weeks = 2
            difficulty = "medium"
        else:
            playbook = self.MIGRATION_PLAYBOOKS[source_competitor]
            base_weeks = playbook["typical_timeline_weeks"]
            difficulty = playbook["migration_difficulty"]

        # Adjust for company size
        if company_size > 200:
            timeline_weeks = base_weeks * 1.5
        elif company_size > 100:
            timeline_weeks = base_weeks * 1.2
        else:
            timeline_weeks = base_weeks

        # Adjust for data volume
        volume_multipliers = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.3,
            "very_high": 1.5
        }
        timeline_weeks *= volume_multipliers.get(data_volume, 1.0)

        estimate = {
            "timeline_weeks": round(timeline_weeks, 1),
            "timeline_range": f"{max(1, int(timeline_weeks - 1))}-{int(timeline_weeks + 1)} weeks",
            "difficulty": difficulty,
            "internal_effort_hours": self._estimate_internal_hours(difficulty, company_size),
            "our_support_hours": self._estimate_support_hours(difficulty, company_size),
            "recommended_resources": self._recommend_resources(company_size)
        }

        return estimate

    def _estimate_internal_hours(self, difficulty: str, company_size: int) -> int:
        """Estimate internal team effort hours"""
        base_hours = {
            "easy": 20,
            "easy_medium": 30,
            "medium": 40,
            "medium_high": 60,
            "high": 80
        }

        hours = base_hours.get(difficulty, 40)

        # Adjust for company size
        if company_size > 200:
            hours *= 2
        elif company_size > 100:
            hours *= 1.5

        return int(hours)

    def _estimate_support_hours(self, difficulty: str, company_size: int) -> int:
        """Estimate our support hours"""
        base_hours = {
            "easy": 10,
            "easy_medium": 15,
            "medium": 20,
            "medium_high": 30,
            "high": 40
        }

        return base_hours.get(difficulty, 20)

    def _recommend_resources(self, company_size: int) -> List[str]:
        """Recommend resources for migration"""
        resources = ["Project manager or migration lead"]

        if company_size > 200:
            resources.extend([
                "Technical lead for integrations",
                "Data analyst for data cleanup",
                "Change management lead"
            ])
        elif company_size > 50:
            resources.extend([
                "Technical contact for integrations",
                "Data quality reviewer"
            ])

        return resources

    def _assess_risk_level(self, difficulty: str) -> str:
        """Assess migration risk level"""
        risk_map = {
            "easy": "low",
            "easy_medium": "low",
            "medium": "low_medium",
            "medium_high": "medium",
            "high": "medium_high"
        }
        return risk_map.get(difficulty, "low_medium")

    def _recommend_approach(self, playbook: Dict, customer_metadata: Dict) -> str:
        """Recommend migration approach"""
        company_size = customer_metadata.get("company_size", 50)

        if company_size >= 200:
            return "Concierge Migration - We'll handle everything for you"
        elif company_size >= 50:
            return "Guided Migration - We'll guide you through each step"
        else:
            return "Guided Migration or Self-Service with our comprehensive tools"

    def _recommend_services(self, customer_metadata: Dict) -> List[Dict[str, Any]]:
        """Recommend migration services"""
        company_size = customer_metadata.get("company_size", 50)
        services = []

        # Determine tier
        if company_size >= 200:
            tier = "enterprise"
        elif company_size >= 50:
            tier = "growth"
        else:
            tier = "startup"

        # Add applicable services
        for service_key, service_data in self.MIGRATION_SERVICES.items():
            if tier in service_data["included_in"] or "all_plans" in service_data["included_in"]:
                services.append({
                    "service": service_data["name"],
                    "description": service_data["description"],
                    "services_included": service_data["services"],
                    "timeline": service_data["timeline"],
                    "customer_effort": service_data["customer_effort"],
                    "recommended": service_key in ["concierge_migration", "guided_migration"]
                })

        return services

    def _address_concerns(self, source_competitor: str) -> List[Dict[str, Any]]:
        """Address common migration concerns"""
        concerns = [
            {
                "concern": "Will we lose data during migration?",
                "response": "No. We have a proven migration process with multiple validation checkpoints. Your data is safe.",
                "mitigation": "Multiple data validation steps, backup of original data"
            },
            {
                "concern": "How long will we be down?",
                "response": "Zero downtime. We can run systems in parallel during transition.",
                "mitigation": "Parallel run option, phased cutover"
            },
            {
                "concern": "What if our team doesn't adopt the new platform?",
                "response": "Our platform is more intuitive. We also provide comprehensive training.",
                "mitigation": "Hands-on training, ongoing support, user-friendly interface"
            },
            {
                "concern": "What about our integrations?",
                "response": "We integrate with all major tools. We'll help set up your integrations.",
                "mitigation": "500+ native integrations, API support, integration assistance"
            },
            {
                "concern": "This seems risky",
                "response": "Hundreds of companies have migrated successfully. We have a proven playbook.",
                "mitigation": "Proven process, dedicated support, success stories"
            }
        ]

        return concerns

    def _get_success_stories(self, source_competitor: str) -> List[Dict[str, Any]]:
        """Get relevant migration success stories"""
        stories = []

        for story_key, story_data in self.SUCCESS_STORIES.items():
            if source_competitor in story_key or source_competitor == "generic":
                stories.append(story_data)

        return stories[:2]  # Top 2 relevant stories

    def _generate_checklist(
        self,
        source_competitor: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate migration checklist"""

        checklist = {
            "pre_migration": [
                "Schedule migration kickoff call",
                "Audit current system configuration",
                "Identify critical workflows and automation",
                "Document integration points",
                "Determine migration timeline",
                "Assign internal migration team"
            ],
            "during_migration": [
                "Export data from current system",
                "Review and clean data",
                "Import data to new platform",
                "Validate data accuracy",
                "Set up integrations",
                "Recreate workflows and automation",
                "Configure user roles and permissions",
                "Test thoroughly"
            ],
            "post_migration": [
                "Train team on new platform",
                "Go live with new system",
                "Monitor for issues",
                "Gather team feedback",
                "Optimize configuration",
                "Decommission old system"
            ]
        }

        return checklist


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing MigrationSpecialist Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Salesforce migration
        state1 = create_initial_state(
            "We want to migrate from Salesforce. How hard is it and how long will it take?",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "company_size": 250,
                    "industry": "technology",
                    "data_volume": "high"
                }
            }
        )

        agent = MigrationSpecialist()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Salesforce Migration (Large Enterprise)")
        plan = result1['migration_plan']
        print(f"From: {plan['from_system']} → To: {plan['to_system']}")
        print(f"Difficulty: {plan['difficulty']}")
        print(f"Timeline: {plan['estimated_timeline_weeks']} weeks")
        print(f"Risk Level: {plan['risk_level']}")
        print(f"\nPhases:")
        for phase in plan['phases']:
            print(f"  {phase['phase']} ({phase['duration_weeks']} weeks)")
            for activity in phase['activities'][:2]:
                print(f"    • {activity}")

        effort = result1['migration_effort_estimate']
        print(f"\nEffort Estimate:")
        print(f"  Timeline Range: {effort['timeline_range']}")
        print(f"  Internal Effort: {effort['internal_effort_hours']} hours")
        print(f"  Our Support: {effort['our_support_hours']} hours")

        # Test case 2: HubSpot migration (smaller company)
        state2 = create_initial_state(
            "We're using HubSpot and want to switch. What's involved?",
            context={
                "customer_metadata": {
                    "company": "StartupCo",
                    "company_size": 30,
                    "industry": "saas",
                    "data_volume": "medium"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\n\nTest 2 - HubSpot Migration (Small Company)")
        print(f"Estimated Timeline: {result2['migration_effort_estimate']['timeline_weeks']} weeks")
        print(f"\nRecommended Services:")
        for service in result2['migration_services'][:2]:
            print(f"\n  {service['service']}")
            print(f"  {service['description']}")
            print(f"  Customer Effort: {service['customer_effort']}")
            print(f"  Services: {len(service['services_included'])} included")

        # Test case 3: Migration concerns
        state3 = create_initial_state(
            "I'm worried about migrating from Zendesk. What could go wrong?",
            context={
                "customer_metadata": {
                    "company": "SupportCo",
                    "company_size": 75
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\n\nTest 3 - Addressing Migration Concerns")
        print(f"Common Concerns & Responses:")
        for concern in result3['migration_concerns'][:3]:
            print(f"\n  Q: {concern['concern']}")
            print(f"  A: {concern['response']}")
            print(f"  Mitigation: {concern['mitigation']}")

        print(f"\nSuccess Stories:")
        for story in result3['migration_success_stories']:
            print(f"\n  {story['company']} ({story['company_size']} employees)")
            print(f"  From: {story['from_competitor'].title()}")
            print(f"  Timeline: {story['migration_time']}")
            print(f"  Result: {story['outcome']}")
            print(f"  Quote: \"{story['quote']}\"")

        print(f"\nConfidence: {result3['response_confidence']:.2f}")

    asyncio.run(test())
