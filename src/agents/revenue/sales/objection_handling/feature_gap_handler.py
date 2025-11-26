"""
Feature Gap Handler Agent - TASK-1032

Handles "missing feature X" objections by explaining roadmap, workarounds,
alternatives, and providing timelines for feature development.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("feature_gap_handler", tier="revenue", category="sales")
class FeatureGapHandler(BaseAgent):
    """
    Feature Gap Handler Agent - Specialist in handling missing feature objections.

    Handles:
    - "Missing feature X" objections
    - Product roadmap explanations
    - Workaround suggestions
    - Alternative feature recommendations
    - Development timeline communication
    """

    # Response strategies for different feature gap scenarios
    RESPONSE_STRATEGIES = {
        "on_roadmap": {
            "approach": "timeline_sharing",
            "tactics": ["show_roadmap", "provide_eta", "early_access_program"],
            "supporting_materials": ["roadmap_doc", "beta_signup", "release_notes"]
        },
        "workaround_exists": {
            "approach": "alternative_solution",
            "tactics": ["explain_workaround", "api_integration", "manual_process"],
            "supporting_materials": ["workaround_guide", "api_docs", "tutorial_video"]
        },
        "alternative_feature": {
            "approach": "feature_mapping",
            "tactics": ["show_equivalent", "explain_difference", "demo_alternative"],
            "supporting_materials": ["feature_comparison", "use_case_guide", "demo_video"]
        },
        "custom_development": {
            "approach": "partnership_opportunity",
            "tactics": ["enterprise_customization", "api_extensibility", "partnership_program"],
            "supporting_materials": ["enterprise_plan", "api_docs", "partner_program"]
        },
        "not_planned": {
            "approach": "feature_request",
            "tactics": ["gather_requirements", "submit_feature_request", "explore_alternatives"],
            "supporting_materials": ["feature_request_form", "user_community", "alternative_tools"]
        }
    }

    # Feature categories and their development status
    FEATURE_ROADMAP = {
        # Core features - available now
        "core": {
            "automation": {"status": "available", "timeline": "now"},
            "analytics": {"status": "available", "timeline": "now"},
            "reporting": {"status": "available", "timeline": "now"},
            "integrations": {"status": "available", "timeline": "now"},
            "api": {"status": "available", "timeline": "now"}
        },
        # In development - coming soon
        "in_development": {
            "advanced_ai": {"status": "beta", "timeline": "Q1 2026"},
            "mobile_app": {"status": "beta", "timeline": "Q2 2026"},
            "offline_mode": {"status": "development", "timeline": "Q2 2026"},
            "multi_region": {"status": "development", "timeline": "Q3 2026"}
        },
        # On roadmap - planned
        "roadmap": {
            "blockchain_integration": {"status": "planned", "timeline": "Q4 2026"},
            "ar_visualization": {"status": "planned", "timeline": "2027"},
            "voice_commands": {"status": "planned", "timeline": "Q3 2026"}
        }
    }

    # Common workarounds for missing features
    WORKAROUNDS = {
        "advanced_reporting": {
            "workaround": "Export data to Excel/PowerBI for custom reports",
            "difficulty": "easy",
            "documentation": "export_guide.pdf",
            "effectiveness": "high"
        },
        "mobile_app": {
            "workaround": "Use responsive web interface on mobile browser",
            "difficulty": "easy",
            "documentation": "mobile_web_guide.pdf",
            "effectiveness": "medium"
        },
        "custom_workflow": {
            "workaround": "Use API to build custom workflow automation",
            "difficulty": "medium",
            "documentation": "api_workflow_examples.md",
            "effectiveness": "high"
        },
        "specific_integration": {
            "workaround": "Use Zapier/Make.com as middleware",
            "difficulty": "easy",
            "documentation": "zapier_integration_guide.pdf",
            "effectiveness": "high"
        },
        "offline_mode": {
            "workaround": "Use browser caching for limited offline access",
            "difficulty": "medium",
            "documentation": "offline_access_guide.pdf",
            "effectiveness": "medium"
        }
    }

    # Alternative features that solve similar problems
    FEATURE_ALTERNATIVES = {
        "gantt_chart": {
            "alternative": "timeline_view",
            "explanation": "Our Timeline View provides similar project visualization",
            "comparison": "More flexible than traditional Gantt charts"
        },
        "custom_fields": {
            "alternative": "metadata_tags",
            "explanation": "Metadata tags provide flexible custom data",
            "comparison": "More powerful and searchable than custom fields"
        },
        "file_storage": {
            "alternative": "external_storage_integration",
            "explanation": "Integrates with Google Drive, Dropbox, OneDrive",
            "comparison": "Better than built-in storage - use your preferred platform"
        },
        "time_tracking": {
            "alternative": "integration_with_time_trackers",
            "explanation": "Integrates with Toggl, Harvest, Clockify",
            "comparison": "Professional time tracking without reinventing the wheel"
        }
    }

    # Objection severity assessment
    SEVERITY_INDICATORS = {
        "blocker": ["deal breaker", "must have", "can't proceed without", "absolute requirement"],
        "major": ["really need", "critical", "important for us", "key requirement"],
        "minor": ["would be nice", "prefer to have", "interested in", "wondering about"]
    }

    def __init__(self):
        config = AgentConfig(
            name="feature_gap_handler",
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
        Process feature gap objection handling.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with feature gap response
        """
        self.logger.info("feature_gap_handler_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        self.logger.debug(
            "feature_gap_details",
            message_preview=message[:100],
            turn_count=state["turn_count"]
        )

        # Extract requested feature(s)
        requested_features = self._extract_requested_features(message)

        # Assess objection severity
        objection_severity = self._assess_severity(message)

        # Analyze feature availability
        feature_analysis = self._analyze_feature_availability(requested_features)

        # Determine response strategy
        strategy = self._determine_strategy(feature_analysis)

        # Get workarounds if applicable
        workarounds = self._get_workarounds(requested_features, feature_analysis)

        # Get alternatives if applicable
        alternatives = self._get_alternatives(requested_features, feature_analysis)

        # Search knowledge base
        kb_results = await self.search_knowledge_base(
            message,
            category="sales",
            limit=4
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_feature_gap_response(
            message,
            requested_features,
            objection_severity,
            feature_analysis,
            strategy,
            workarounds,
            alternatives,
            kb_results,
            customer_metadata,
            state
        )

        # Calculate resolution confidence
        resolution_confidence = self._calculate_resolution_confidence(
            feature_analysis,
            objection_severity,
            workarounds,
            alternatives
        )

        # Determine escalation need
        needs_escalation = self._check_escalation_needed(
            objection_severity,
            feature_analysis,
            resolution_confidence
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = resolution_confidence
        state["requested_features"] = requested_features
        state["feature_analysis"] = feature_analysis
        state["objection_severity"] = objection_severity
        state["response_strategy"] = strategy
        state["workarounds"] = workarounds
        state["alternatives"] = alternatives
        state["needs_escalation"] = needs_escalation
        state["status"] = "escalated" if needs_escalation else "resolved"

        self.logger.info(
            "feature_gap_handler_completed",
            features_count=len(requested_features),
            severity=objection_severity,
            confidence=resolution_confidence,
            escalated=needs_escalation
        )

        return state

    def _extract_requested_features(self, message: str) -> List[str]:
        """Extract requested features from message"""
        message_lower = message.lower()
        features = []

        # Check all known features across categories
        all_features = {}
        for category, feature_dict in self.FEATURE_ROADMAP.items():
            all_features.update(feature_dict)

        # Also check workarounds and alternatives
        all_features.update(self.WORKAROUNDS)
        all_features.update(self.FEATURE_ALTERNATIVES)

        for feature_name in all_features.keys():
            feature_words = feature_name.replace("_", " ")
            if feature_words in message_lower or feature_name in message_lower:
                features.append(feature_name)

        # If no specific features found, look for generic terms
        if not features:
            generic_features = ["custom feature", "specific integration", "advanced capability"]
            for generic in generic_features:
                if generic in message_lower:
                    features.append("custom_feature")
                    break

        return features if features else ["unspecified_feature"]

    def _assess_severity(self, message: str) -> str:
        """Assess the severity of the feature gap objection"""
        message_lower = message.lower()

        for severity, indicators in self.SEVERITY_INDICATORS.items():
            if any(indicator in message_lower for indicator in indicators):
                return severity

        return "minor"

    def _analyze_feature_availability(self, requested_features: List[str]) -> Dict[str, Any]:
        """Analyze the availability status of requested features"""
        analysis = {
            "available": [],
            "in_development": [],
            "on_roadmap": [],
            "not_planned": [],
            "has_workaround": [],
            "has_alternative": []
        }

        for feature in requested_features:
            feature_found = False

            # Check core features
            if feature in self.FEATURE_ROADMAP["core"]:
                analysis["available"].append({
                    "feature": feature,
                    "details": self.FEATURE_ROADMAP["core"][feature]
                })
                feature_found = True

            # Check in development
            elif feature in self.FEATURE_ROADMAP["in_development"]:
                analysis["in_development"].append({
                    "feature": feature,
                    "details": self.FEATURE_ROADMAP["in_development"][feature]
                })
                feature_found = True

            # Check roadmap
            elif feature in self.FEATURE_ROADMAP["roadmap"]:
                analysis["on_roadmap"].append({
                    "feature": feature,
                    "details": self.FEATURE_ROADMAP["roadmap"][feature]
                })
                feature_found = True

            # Check workarounds
            if feature in self.WORKAROUNDS:
                analysis["has_workaround"].append({
                    "feature": feature,
                    "workaround": self.WORKAROUNDS[feature]
                })

            # Check alternatives
            if feature in self.FEATURE_ALTERNATIVES:
                analysis["has_alternative"].append({
                    "feature": feature,
                    "alternative": self.FEATURE_ALTERNATIVES[feature]
                })

            # If not found anywhere, mark as not planned
            if not feature_found and feature not in self.WORKAROUNDS and feature not in self.FEATURE_ALTERNATIVES:
                analysis["not_planned"].append(feature)

        return analysis

    def _determine_strategy(self, feature_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best response strategy based on feature analysis"""
        # Prioritize strategies based on what's available
        if feature_analysis["available"]:
            return self.RESPONSE_STRATEGIES["alternative_feature"]
        elif feature_analysis["in_development"]:
            return self.RESPONSE_STRATEGIES["on_roadmap"]
        elif feature_analysis["on_roadmap"]:
            return self.RESPONSE_STRATEGIES["on_roadmap"]
        elif feature_analysis["has_workaround"]:
            return self.RESPONSE_STRATEGIES["workaround_exists"]
        elif feature_analysis["has_alternative"]:
            return self.RESPONSE_STRATEGIES["alternative_feature"]
        else:
            return self.RESPONSE_STRATEGIES["not_planned"]

    def _get_workarounds(
        self,
        requested_features: List[str],
        feature_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get applicable workarounds"""
        workarounds = []

        for item in feature_analysis.get("has_workaround", []):
            workarounds.append(item["workaround"])

        return workarounds

    def _get_alternatives(
        self,
        requested_features: List[str],
        feature_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get applicable alternative features"""
        alternatives = []

        for item in feature_analysis.get("has_alternative", []):
            alternatives.append(item["alternative"])

        return alternatives

    def _calculate_resolution_confidence(
        self,
        feature_analysis: Dict[str, Any],
        severity: str,
        workarounds: List,
        alternatives: List
    ) -> float:
        """Calculate confidence in resolving the feature gap objection"""
        base_confidence = 0.70

        # Adjust based on feature availability
        if feature_analysis["available"]:
            base_confidence += 0.20  # Feature already exists!
        elif feature_analysis["in_development"]:
            base_confidence += 0.15  # Coming soon
        elif feature_analysis["on_roadmap"]:
            base_confidence += 0.10  # Planned
        elif workarounds or alternatives:
            base_confidence += 0.05  # Has workaround/alternative

        # Adjust for severity
        severity_adjustments = {
            "minor": 0.10,
            "major": 0.0,
            "blocker": -0.15
        }
        base_confidence += severity_adjustments.get(severity, 0.0)

        return min(max(base_confidence, 0.0), 1.0)

    def _check_escalation_needed(
        self,
        severity: str,
        feature_analysis: Dict[str, Any],
        confidence: float
    ) -> bool:
        """Determine if escalation is needed"""
        # Escalate if blocker and no good solution
        if severity == "blocker":
            if not feature_analysis["available"] and not feature_analysis["in_development"]:
                return True

        # Escalate if low confidence
        if confidence < 0.60:
            return True

        return False

    async def _generate_feature_gap_response(
        self,
        message: str,
        requested_features: List[str],
        severity: str,
        feature_analysis: Dict[str, Any],
        strategy: Dict,
        workarounds: List,
        alternatives: List,
        kb_results: List[Dict],
        customer_metadata: Dict,
        state: AgentState
    ) -> str:
        """Generate personalized response to feature gap objection"""

        # Get conversation history for context continuity
        conversation_history = self.get_conversation_context(state)

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant documentation:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        # Build feature availability context
        feature_context = "\n\nFeature Availability Analysis:\n"

        if feature_analysis["available"]:
            feature_context += "✓ Available Now:\n"
            for item in feature_analysis["available"]:
                feature_context += f"  - {item['feature'].replace('_', ' ').title()}\n"

        if feature_analysis["in_development"]:
            feature_context += "\n🚧 In Development (Beta/Coming Soon):\n"
            for item in feature_analysis["in_development"]:
                timeline = item['details']['timeline']
                status = item['details']['status']
                feature_context += f"  - {item['feature'].replace('_', ' ').title()} ({status}, ETA: {timeline})\n"

        if feature_analysis["on_roadmap"]:
            feature_context += "\n📋 On Roadmap:\n"
            for item in feature_analysis["on_roadmap"]:
                timeline = item['details']['timeline']
                feature_context += f"  - {item['feature'].replace('_', ' ').title()} (Planned: {timeline})\n"

        # Build workarounds context
        workaround_context = ""
        if workarounds:
            workaround_context = "\n\nAvailable Workarounds:\n"
            for wa in workarounds:
                workaround_context += f"- {wa['workaround']} (Difficulty: {wa['difficulty']}, Effectiveness: {wa['effectiveness']})\n"
                workaround_context += f"  Documentation: {wa['documentation']}\n"

        # Build alternatives context
        alternative_context = ""
        if alternatives:
            alternative_context = "\n\nAlternative Features:\n"
            for alt in alternatives:
                alternative_context += f"- {alt['alternative'].replace('_', ' ').title()}\n"
                alternative_context += f"  {alt['explanation']}\n"
                alternative_context += f"  Advantage: {alt['comparison']}\n"

        system_prompt = f"""You are a Feature Gap Handler specialist helping address missing feature concerns.

Objection Analysis:
- Requested Features: {', '.join(f.replace('_', ' ').title() for f in requested_features)}
- Severity: {severity.upper()}
- Response Strategy: {strategy['approach'].replace('_', ' ').title()}

Customer Profile:
- Company: {customer_metadata.get('company', 'Unknown')}
- Industry: {customer_metadata.get('industry', 'Unknown')}
- Role: {customer_metadata.get('title', 'Unknown')}

Your response should:
1. Acknowledge their feature need with empathy
2. Clearly explain the current status of requested features
3. Provide workarounds or alternatives if the feature isn't available yet
4. Share timeline and roadmap information where applicable
5. Offer to gather their detailed requirements for product team
6. Be honest about what's available vs what's planned
7. Focus on solving their underlying business need

Key Tactics: {', '.join(strategy['tactics'])}
Supporting Materials: {', '.join(strategy['supporting_materials'])}"""

        user_prompt = f"""Customer message: {message}

{feature_context}
{workaround_context}
{alternative_context}
{kb_context}

Generate a helpful, honest response that addresses their feature gap concern."""

        response = await self.call_llm(
            system_prompt,
            user_prompt,
            conversation_history=conversation_history
        )
        return response


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing FeatureGapHandler Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case 1: Asking about feature in development
        state1 = create_initial_state(
            "Do you have a mobile app? That's really important for our team",
            context={
                "customer_metadata": {
                    "company": "Mobile First Inc",
                    "title": "Product Manager",
                    "company_size": 75,
                    "industry": "technology"
                }
            }
        )

        agent = FeatureGapHandler()
        result1 = await agent.process(state1)

        print(f"\nTest 1 - Mobile App Feature Request (In Development)")
        print(f"Requested Features: {result1['requested_features']}")
        print(f"Severity: {result1['objection_severity']}")
        print(f"Resolution Confidence: {result1['response_confidence']:.2f}")
        print(f"Needs Escalation: {result1['needs_escalation']}")
        print(f"Strategy: {result1['response_strategy']['approach']}")
        print(f"Response:\n{result1['agent_response']}\n")

        # Test case 2: Blocker - missing critical feature
        state2 = create_initial_state(
            "We absolutely need offline mode - it's a deal breaker for us. Our field team has no connectivity.",
            context={
                "customer_metadata": {
                    "company": "Field Services Co",
                    "title": "CTO",
                    "company_size": 200,
                    "industry": "manufacturing"
                }
            }
        )

        result2 = await agent.process(state2)

        print(f"\nTest 2 - Offline Mode Blocker")
        print(f"Requested Features: {result2['requested_features']}")
        print(f"Severity: {result2['objection_severity']}")
        print(f"Resolution Confidence: {result2['response_confidence']:.2f}")
        print(f"Needs Escalation: {result2['needs_escalation']}")
        print(f"Workarounds Available: {len(result2['workarounds'])}")
        print(f"Response:\n{result2['agent_response']}\n")

        # Test case 3: Feature with alternative solution
        state3 = create_initial_state(
            "We're looking for Gantt chart capabilities for project management",
            context={
                "customer_metadata": {
                    "company": "Project Pros",
                    "title": "Operations Manager",
                    "company_size": 50,
                    "industry": "technology"
                }
            }
        )

        result3 = await agent.process(state3)

        print(f"\nTest 3 - Gantt Chart Request (Has Alternative)")
        print(f"Requested Features: {result3['requested_features']}")
        print(f"Severity: {result3['objection_severity']}")
        print(f"Resolution Confidence: {result3['response_confidence']:.2f}")
        print(f"Alternatives Available: {len(result3['alternatives'])}")
        print(f"Response:\n{result3['agent_response']}\n")

    asyncio.run(test())
