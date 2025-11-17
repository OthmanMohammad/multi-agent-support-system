"""
Integration Objection Handler Agent - TASK-1035

Handles "doesn't integrate with Z" objections by providing API documentation,
integration examples, and custom integration support.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("integration_objection_handler", tier="revenue", category="sales")
class IntegrationObjectionHandler(BaseAgent):
    """
    Integration Objection Handler Agent - Specialist in integration concerns.

    Handles:
    - "Doesn't integrate with Z" objections
    - API documentation and capabilities
    - Integration examples and tutorials
    - Custom integration support
    - Third-party integration platforms (Zapier, Make)
    """

    # Response strategies for different integration scenarios
    RESPONSE_STRATEGIES = {
        "native_integration_exists": {
            "approach": "showcase_integration",
            "tactics": ["demo_integration", "setup_guide", "success_stories"],
            "supporting_materials": ["integration_guide", "video_tutorial", "api_docs"]
        },
        "api_available": {
            "approach": "api_capabilities",
            "tactics": ["api_documentation", "code_examples", "developer_support"],
            "supporting_materials": ["api_reference", "sdk_docs", "code_samples"]
        },
        "zapier_make_available": {
            "approach": "third_party_integration",
            "tactics": ["zapier_guide", "make_guide", "middleware_options"],
            "supporting_materials": ["zapier_integration_guide", "make_templates", "middleware_docs"]
        },
        "webhook_solution": {
            "approach": "webhook_integration",
            "tactics": ["webhook_setup", "event_documentation", "integration_examples"],
            "supporting_materials": ["webhook_guide", "event_reference", "sample_code"]
        },
        "custom_integration": {
            "approach": "enterprise_services",
            "tactics": ["custom_development", "professional_services", "integration_consultation"],
            "supporting_materials": ["services_overview", "engagement_model", "success_stories"]
        }
    }

    # Native integrations catalog
    NATIVE_INTEGRATIONS = {
        # CRM Systems
        "salesforce": {
            "name": "Salesforce",
            "category": "CRM",
            "status": "available",
            "sync_type": "bi-directional",
            "features": ["contact_sync", "deal_sync", "activity_logging", "custom_fields"],
            "setup_time": "15 minutes",
            "documentation": "salesforce_integration_guide.pdf"
        },
        "hubspot": {
            "name": "HubSpot",
            "category": "CRM",
            "status": "available",
            "sync_type": "bi-directional",
            "features": ["contact_sync", "company_sync", "deal_tracking", "email_integration"],
            "setup_time": "10 minutes",
            "documentation": "hubspot_integration_guide.pdf"
        },
        "pipedrive": {
            "name": "Pipedrive",
            "category": "CRM",
            "status": "available",
            "sync_type": "bi-directional",
            "features": ["deal_sync", "contact_sync", "activity_sync"],
            "setup_time": "10 minutes",
            "documentation": "pipedrive_integration_guide.pdf"
        },

        # Communication Tools
        "slack": {
            "name": "Slack",
            "category": "Communication",
            "status": "available",
            "sync_type": "real-time",
            "features": ["notifications", "commands", "channel_integration", "bot_support"],
            "setup_time": "5 minutes",
            "documentation": "slack_integration_guide.pdf"
        },
        "microsoft_teams": {
            "name": "Microsoft Teams",
            "category": "Communication",
            "status": "available",
            "sync_type": "real-time",
            "features": ["notifications", "bot_commands", "channel_posting"],
            "setup_time": "10 minutes",
            "documentation": "teams_integration_guide.pdf"
        },

        # Email & Calendar
        "gmail": {
            "name": "Gmail",
            "category": "Email",
            "status": "available",
            "sync_type": "real-time",
            "features": ["email_sync", "contact_sync", "calendar_integration"],
            "setup_time": "5 minutes",
            "documentation": "gmail_integration_guide.pdf"
        },
        "outlook": {
            "name": "Outlook",
            "category": "Email",
            "status": "available",
            "sync_type": "real-time",
            "features": ["email_sync", "calendar_sync", "contact_sync"],
            "setup_time": "5 minutes",
            "documentation": "outlook_integration_guide.pdf"
        },
        "google_calendar": {
            "name": "Google Calendar",
            "category": "Calendar",
            "status": "available",
            "sync_type": "bi-directional",
            "features": ["event_sync", "scheduling", "availability"],
            "setup_time": "5 minutes",
            "documentation": "gcal_integration_guide.pdf"
        },

        # Project Management
        "jira": {
            "name": "Jira",
            "category": "Project Management",
            "status": "available",
            "sync_type": "bi-directional",
            "features": ["ticket_sync", "issue_tracking", "custom_fields", "webhooks"],
            "setup_time": "15 minutes",
            "documentation": "jira_integration_guide.pdf"
        },
        "asana": {
            "name": "Asana",
            "category": "Project Management",
            "status": "available",
            "sync_type": "bi-directional",
            "features": ["task_sync", "project_sync", "comment_sync"],
            "setup_time": "10 minutes",
            "documentation": "asana_integration_guide.pdf"
        },

        # Storage & Files
        "google_drive": {
            "name": "Google Drive",
            "category": "Storage",
            "status": "available",
            "sync_type": "real-time",
            "features": ["file_storage", "document_sharing", "folder_sync"],
            "setup_time": "5 minutes",
            "documentation": "gdrive_integration_guide.pdf"
        },
        "dropbox": {
            "name": "Dropbox",
            "category": "Storage",
            "status": "available",
            "sync_type": "real-time",
            "features": ["file_storage", "sharing", "folder_sync"],
            "setup_time": "5 minutes",
            "documentation": "dropbox_integration_guide.pdf"
        },

        # Analytics & BI
        "google_analytics": {
            "name": "Google Analytics",
            "category": "Analytics",
            "status": "available",
            "sync_type": "one-way",
            "features": ["event_tracking", "conversion_tracking", "user_analytics"],
            "setup_time": "10 minutes",
            "documentation": "ga_integration_guide.pdf"
        },
        "tableau": {
            "name": "Tableau",
            "category": "BI",
            "status": "available",
            "sync_type": "data_connector",
            "features": ["data_export", "real-time_dashboards", "custom_reports"],
            "setup_time": "20 minutes",
            "documentation": "tableau_integration_guide.pdf"
        }
    }

    # API capabilities
    API_CAPABILITIES = {
        "rest_api": {
            "version": "v2",
            "authentication": ["oauth2", "api_key", "jwt"],
            "rate_limits": "1000 requests/hour (Enterprise: 10,000/hour)",
            "endpoints": "200+ endpoints covering all features",
            "documentation": "Complete OpenAPI/Swagger documentation",
            "sdks": ["Python", "JavaScript", "Ruby", "PHP", "Java", ".NET"]
        },
        "webhooks": {
            "events": "50+ event types",
            "delivery": "Real-time with retry logic",
            "security": "HMAC signature verification",
            "documentation": "Comprehensive webhook guide",
            "filtering": "Custom event filters and routing"
        },
        "graphql": {
            "available": True,
            "version": "GraphQL",
            "features": ["flexible_queries", "real-time_subscriptions", "batching"],
            "playground": "Interactive GraphQL playground",
            "documentation": "Full GraphQL schema documentation"
        }
    }

    # Third-party integration platforms
    THIRD_PARTY_PLATFORMS = {
        "zapier": {
            "name": "Zapier",
            "available": True,
            "triggers": 25,
            "actions": 30,
            "integration_count": "5000+ apps connectable",
            "templates": "100+ pre-built Zap templates",
            "setup_difficulty": "easy",
            "documentation": "zapier_integration_guide.pdf"
        },
        "make": {
            "name": "Make (formerly Integromat)",
            "available": True,
            "modules": 40,
            "integration_count": "1500+ apps connectable",
            "templates": "50+ pre-built scenarios",
            "setup_difficulty": "medium",
            "documentation": "make_integration_guide.pdf"
        },
        "n8n": {
            "name": "n8n",
            "available": True,
            "nodes": 35,
            "integration_count": "400+ apps connectable",
            "self_hosted": True,
            "setup_difficulty": "medium",
            "documentation": "n8n_integration_guide.pdf"
        }
    }

    # Custom integration support
    CUSTOM_INTEGRATION_SERVICES = {
        "professional_services": {
            "service": "Professional Services Team",
            "description": "Dedicated team for custom integrations",
            "availability": "Enterprise plan",
            "typical_timeline": "2-6 weeks",
            "includes": ["requirements_analysis", "development", "testing", "documentation"]
        },
        "integration_consultation": {
            "service": "Integration Consultation",
            "description": "Architecture review and integration guidance",
            "availability": "Growth and Enterprise plans",
            "typical_timeline": "1-2 weeks",
            "includes": ["architecture_review", "best_practices", "code_review"]
        },
        "developer_support": {
            "service": "Priority Developer Support",
            "description": "Dedicated support for integration development",
            "availability": "All plans",
            "typical_timeline": "Ongoing",
            "includes": ["email_support", "slack_channel", "documentation_access"]
        }
    }

    # Severity indicators
    SEVERITY_INDICATORS = {
        "blocker": ["must integrate", "deal breaker", "cannot proceed without", "critical requirement"],
        "major": ["need to integrate", "important integration", "required for us", "key integration"],
        "minor": ["would like to integrate", "interested in", "nice to have", "wondering about"]
    }

    def __init__(self):
        config = AgentConfig(
            name="integration_objection_handler",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            max_tokens=1000,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.ENTITY_EXTRACTION
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process integration objection handling.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with integration response
        """
        self.logger.info("integration_objection_handler_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "integration_objection_details",
            message_preview=message[:100],
            turn_count=state["turn_count"]
        )

        # Identify requested integrations
        requested_integrations = self._identify_integrations(message)

        # Assess objection severity
        objection_severity = self._assess_severity(message)

        # Analyze integration availability
        integration_analysis = self._analyze_integration_availability(requested_integrations)

        # Determine response strategy
        strategy = self._determine_strategy(integration_analysis)

        # Get API capabilities if relevant
        api_info = self._get_api_info(integration_analysis)

        # Get third-party platform options
        third_party_options = self._get_third_party_options(integration_analysis)

        # Get custom integration services
        custom_services = self._get_custom_services(objection_severity, customer_metadata)

        # Search knowledge base
        kb_results = await self.search_knowledge_base(
            message,
            category="sales",
            limit=4
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_integration_response(
            message,
            requested_integrations,
            objection_severity,
            integration_analysis,
            strategy,
            api_info,
            third_party_options,
            custom_services,
            kb_results,
            customer_metadata
        )

        # Calculate resolution confidence
        resolution_confidence = self._calculate_resolution_confidence(
            integration_analysis,
            objection_severity,
            api_info
        )

        # Determine escalation need
        needs_escalation = self._check_escalation_needed(
            objection_severity,
            integration_analysis,
            resolution_confidence
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = resolution_confidence
        state["requested_integrations"] = requested_integrations
        state["integration_analysis"] = integration_analysis
        state["objection_severity"] = objection_severity
        state["response_strategy"] = strategy
        state["api_info"] = api_info
        state["third_party_options"] = third_party_options
        state["custom_services"] = custom_services
        state["needs_escalation"] = needs_escalation
        state["status"] = "escalated" if needs_escalation else "resolved"

        self.logger.info(
            "integration_objection_handler_completed",
            integrations_count=len(requested_integrations),
            severity=objection_severity,
            confidence=resolution_confidence,
            escalated=needs_escalation
        )

        return state

    def _identify_integrations(self, message: str) -> List[str]:
        """Identify which integrations are mentioned in the message"""
        message_lower = message.lower()
        mentioned = []

        # Check native integrations
        for integration_key, integration_data in self.NATIVE_INTEGRATIONS.items():
            if integration_key in message_lower or integration_data["name"].lower() in message_lower:
                mentioned.append(integration_key)

        # Check for generic integration terms
        if not mentioned:
            if any(term in message_lower for term in ["integrate", "integration", "connect", "api"]):
                mentioned.append("generic_integration")

        return mentioned if mentioned else ["unspecified_integration"]

    def _assess_severity(self, message: str) -> str:
        """Assess the severity of the integration objection"""
        message_lower = message.lower()

        for severity, indicators in self.SEVERITY_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                return severity

        return "minor"

    def _analyze_integration_availability(self, requested_integrations: List[str]) -> Dict[str, Any]:
        """Analyze availability of requested integrations"""
        analysis = {
            "native_available": [],
            "api_possible": [],
            "zapier_available": [],
            "custom_needed": []
        }

        for integration in requested_integrations:
            if integration in self.NATIVE_INTEGRATIONS:
                analysis["native_available"].append({
                    "name": integration,
                    "data": self.NATIVE_INTEGRATIONS[integration]
                })
            elif integration in ["generic_integration", "unspecified_integration"]:
                # Show API capabilities for generic requests
                analysis["api_possible"].append(integration)
            else:
                # Not in native integrations - suggest alternatives
                analysis["zapier_available"].append(integration)
                analysis["custom_needed"].append(integration)

        return analysis

    def _determine_strategy(self, integration_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best response strategy"""
        if integration_analysis["native_available"]:
            return self.RESPONSE_STRATEGIES["native_integration_exists"]
        elif integration_analysis["api_possible"]:
            return self.RESPONSE_STRATEGIES["api_available"]
        elif integration_analysis["zapier_available"]:
            return self.RESPONSE_STRATEGIES["zapier_make_available"]
        else:
            return self.RESPONSE_STRATEGIES["custom_integration"]

    def _get_api_info(self, integration_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get API information if relevant"""
        if integration_analysis["api_possible"] or integration_analysis["custom_needed"]:
            return self.API_CAPABILITIES
        return None

    def _get_third_party_options(self, integration_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get third-party integration platform options"""
        if integration_analysis["zapier_available"] or integration_analysis["custom_needed"]:
            return [
                self.THIRD_PARTY_PLATFORMS["zapier"],
                self.THIRD_PARTY_PLATFORMS["make"]
            ]
        return []

    def _get_custom_services(self, severity: str, customer_metadata: Dict) -> List[Dict[str, Any]]:
        """Get custom integration services based on severity and customer profile"""
        services = []
        company_size = customer_metadata.get("company_size", 0)

        if severity in ["blocker", "major"]:
            if company_size >= 100:
                services.append(self.CUSTOM_INTEGRATION_SERVICES["professional_services"])
            services.append(self.CUSTOM_INTEGRATION_SERVICES["integration_consultation"])

        # Always offer developer support
        services.append(self.CUSTOM_INTEGRATION_SERVICES["developer_support"])

        return services

    def _calculate_resolution_confidence(
        self,
        integration_analysis: Dict[str, Any],
        severity: str,
        api_info: Optional[Dict]
    ) -> float:
        """Calculate confidence in resolving the integration objection"""
        base_confidence = 0.70

        # Boost for native integrations
        if integration_analysis["native_available"]:
            base_confidence += 0.20

        # Boost for API availability
        if api_info:
            base_confidence += 0.10

        # Adjust for severity
        severity_adjustments = {
            "minor": 0.10,
            "major": 0.0,
            "blocker": -0.10
        }
        base_confidence += severity_adjustments.get(severity, 0.0)

        return min(max(base_confidence, 0.0), 1.0)

    def _check_escalation_needed(
        self,
        severity: str,
        integration_analysis: Dict[str, Any],
        confidence: float
    ) -> bool:
        """Determine if escalation is needed"""
        # Escalate if blocker and no native integration
        if severity == "blocker" and not integration_analysis["native_available"]:
            return True

        # Escalate if low confidence
        if confidence < 0.60:
            return True

        return False

    async def _generate_integration_response(
        self,
        message: str,
        requested_integrations: List[str],
        severity: str,
        integration_analysis: Dict[str, Any],
        strategy: Dict,
        api_info: Optional[Dict],
        third_party_options: List[Dict],
        custom_services: List[Dict],
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate personalized integration response"""

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant documentation:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        # Build integration availability context
        integration_context = "\n\nIntegration Availability:\n"

        if integration_analysis["native_available"]:
            integration_context += "\n✓ Native Integrations Available:\n"
            for item in integration_analysis["native_available"]:
                data = item["data"]
                integration_context += f"\n  {data['name']} ({data['category']}):\n"
                integration_context += f"  - Status: {data['status'].title()}\n"
                integration_context += f"  - Sync: {data['sync_type'].replace('_', ' ').title()}\n"
                integration_context += f"  - Features: {', '.join(data['features'])}\n"
                integration_context += f"  - Setup Time: {data['setup_time']}\n"

        # Build API context
        api_context = ""
        if api_info:
            api_context = "\n\nAPI Capabilities:\n"
            api_context += f"REST API: {api_info['rest_api']['version']}\n"
            api_context += f"  - Authentication: {', '.join(api_info['rest_api']['authentication'])}\n"
            api_context += f"  - Rate Limits: {api_info['rest_api']['rate_limits']}\n"
            api_context += f"  - Endpoints: {api_info['rest_api']['endpoints']}\n"
            api_context += f"  - SDKs: {', '.join(api_info['rest_api']['sdks'])}\n"
            api_context += f"\nWebhooks:\n"
            api_context += f"  - Events: {api_info['webhooks']['events']}\n"
            api_context += f"  - Delivery: {api_info['webhooks']['delivery']}\n"

        # Build third-party options context
        third_party_context = ""
        if third_party_options:
            third_party_context = "\n\nThird-Party Integration Platforms:\n"
            for platform in third_party_options:
                third_party_context += f"\n{platform['name']}:\n"
                third_party_context += f"  - Available: {platform['available']}\n"
                third_party_context += f"  - Connectable Apps: {platform['integration_count']}\n"
                third_party_context += f"  - Templates: {platform['templates']}\n"
                third_party_context += f"  - Setup: {platform['setup_difficulty'].title()}\n"

        # Build custom services context
        custom_context = ""
        if custom_services:
            custom_context = "\n\nCustom Integration Support:\n"
            for service in custom_services:
                custom_context += f"\n{service['service']}:\n"
                custom_context += f"  - {service['description']}\n"
                custom_context += f"  - Availability: {service['availability']}\n"
                if 'typical_timeline' in service:
                    custom_context += f"  - Timeline: {service['typical_timeline']}\n"

        system_prompt = f"""You are an Integration Objection Handler specialist addressing integration concerns.

Objection Analysis:
- Requested Integrations: {', '.join(requested_integrations)}
- Severity: {severity.upper()}
- Response Strategy: {strategy['approach'].replace('_', ' ').title()}

Customer Profile:
- Company: {customer_metadata.get('company', 'Unknown')}
- Industry: {customer_metadata.get('industry', 'Unknown')}
- Company Size: {customer_metadata.get('company_size', 'Unknown')}

Your response should:
1. Address their specific integration needs directly
2. Highlight native integrations if available
3. Explain API capabilities and flexibility
4. Suggest third-party platforms (Zapier, Make) as alternatives
5. Offer custom integration support for enterprise needs
6. Provide clear documentation and setup guides
7. Make integration seem easy and well-supported

Key Tactics: {', '.join(strategy['tactics'])}
Supporting Materials: {', '.join(strategy['supporting_materials'])}"""

        user_prompt = f"""Customer message: {message}

{integration_context}
{api_context}
{third_party_context}
{custom_context}
{kb_context}

Generate a helpful, solutions-focused response that addresses their integration needs."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing IntegrationObjectionHandler Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Native integration exists (Salesforce)
        state1 = create_initial_state(
            "Does this integrate with Salesforce? We need bi-directional sync.",
            context={
                "customer_metadata": {
                    "company": "SalesPro Inc",
                    "title": "Sales Operations Manager",
                    "company_size": 200,
                    "industry": "technology"
                }
            }
        )

        agent = IntegrationObjectionHandler()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Salesforce Integration (Native Available)")
        print(f"Requested Integrations: {result1['requested_integrations']}")
        print(f"Severity: {result1['objection_severity']}")
        print(f"Native Integrations: {len(result1['integration_analysis']['native_available'])}")
        print(f"Resolution Confidence: {result1['response_confidence']:.2f}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Custom integration needed
        state2 = create_initial_state(
            "We use a custom CRM system. Can you integrate with that? It's critical for us.",
            context={
                "customer_metadata": {
                    "company": "Enterprise Corp",
                    "title": "CTO",
                    "company_size": 500,
                    "industry": "finance"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Custom CRM Integration (Blocker)")
        print(f"Requested Integrations: {result2['requested_integrations']}")
        print(f"Severity: {result2['objection_severity']}")
        print(f"Resolution Confidence: {result2['response_confidence']:.2f}")
        print(f"Custom Services Available: {len(result2['custom_services'])}")
        print(f"Needs Escalation: {result2['needs_escalation']}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: General API question
        state3 = create_initial_state(
            "Do you have an API we can use to build custom integrations?",
            context={
                "customer_metadata": {
                    "company": "DevShop",
                    "title": "Software Engineer",
                    "company_size": 75,
                    "industry": "technology"
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - API Capabilities Question")
        print(f"Requested Integrations: {result3['requested_integrations']}")
        print(f"Severity: {result3['objection_severity']}")
        print(f"Resolution Confidence: {result3['response_confidence']:.2f}")
        print(f"API Info Provided: {result3['api_info'] is not None}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
