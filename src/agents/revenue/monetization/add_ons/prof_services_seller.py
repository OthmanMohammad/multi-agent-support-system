"""
Professional Services Seller Agent - TASK-3024

Sells professional services for custom development, integrations, and migrations.
Converts complex implementation needs into professional services engagements.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("prof_services_seller", tier="revenue", category="monetization")
class ProfServicesSeller(BaseAgent):
    """
    Professional Services Seller Agent - Sells custom implementation services.

    Handles:
    - Identify complex implementation needs
    - Detect custom integration requirements
    - Assess migration complexity
    - Scope professional services engagements
    - Calculate project estimates and pricing
    - Present PS value proposition
    - Close professional services deals
    - Track services pipeline and delivery
    """

    # Professional services offerings
    SERVICES_CATALOG = {
        "integration_development": {
            "name": "Custom Integration Development",
            "hourly_rate": 250,
            "typical_hours": 40,
            "description": "Custom API integrations with third-party systems",
            "deliverables": [
                "Custom integration code",
                "API documentation",
                "Testing and validation",
                "Deployment support"
            ],
            "ideal_for": ["custom_integrations", "complex_workflows"]
        },
        "data_migration": {
            "name": "Data Migration Services",
            "hourly_rate": 250,
            "typical_hours": 60,
            "description": "Migrate data from legacy systems",
            "deliverables": [
                "Migration strategy and plan",
                "Data mapping and transformation",
                "Migration scripts",
                "Data validation",
                "Rollback procedures"
            ],
            "ideal_for": ["platform_migration", "consolidation"]
        },
        "custom_development": {
            "name": "Custom Feature Development",
            "hourly_rate": 275,
            "typical_hours": 80,
            "description": "Build custom features and extensions",
            "deliverables": [
                "Requirements analysis",
                "Custom feature development",
                "Testing and QA",
                "Documentation",
                "Ongoing support"
            ],
            "ideal_for": ["unique_requirements", "competitive_advantage"]
        },
        "implementation_consulting": {
            "name": "Implementation Consulting",
            "hourly_rate": 225,
            "typical_hours": 24,
            "description": "Expert guidance for complex implementations",
            "deliverables": [
                "Architecture review",
                "Best practices guidance",
                "Implementation roadmap",
                "Hands-on configuration",
                "Knowledge transfer"
            ],
            "ideal_for": ["enterprise_rollout", "complex_setup"]
        },
        "optimization_audit": {
            "name": "Platform Optimization Audit",
            "hourly_rate": 225,
            "typical_hours": 16,
            "description": "Comprehensive platform optimization",
            "deliverables": [
                "Current state assessment",
                "Optimization recommendations",
                "Performance tuning",
                "Workflow improvements",
                "ROI analysis"
            ],
            "ideal_for": ["performance_issues", "scaling_challenges"]
        }
    }

    # Qualification signals for PS needs
    PS_QUALIFICATION_SIGNALS = {
        "custom_integration_requests": {
            "metric": "integration_requests",
            "threshold": 2,
            "weight": 0.30,
            "service": "integration_development"
        },
        "migration_mentioned": {
            "metric": "migration_mentions",
            "threshold": 1,
            "weight": 0.25,
            "service": "data_migration"
        },
        "custom_feature_requests": {
            "metric": "feature_requests_custom",
            "threshold": 3,
            "weight": 0.20,
            "service": "custom_development"
        },
        "complex_implementation": {
            "metric": "team_size",
            "threshold": 50,
            "weight": 0.15,
            "service": "implementation_consulting"
        },
        "performance_issues": {
            "metric": "performance_complaints",
            "threshold": 2,
            "weight": 0.10,
            "service": "optimization_audit"
        }
    }

    # Project scoping factors
    SCOPING_FACTORS = {
        "complexity_low": 1.0,
        "complexity_medium": 1.5,
        "complexity_high": 2.0,
        "urgency_standard": 1.0,
        "urgency_rush": 1.3,
        "scope_creep_buffer": 0.20  # 20% buffer for unknowns
    }

    def __init__(self):
        config = AgentConfig(
            name="prof_services_seller",
            type=AgentType.SPECIALIST,
             # Sonnet for complex scoping
            temperature=0.3,
            max_tokens=700,
            capabilities=[
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.KB_SEARCH
            ],
            kb_category="monetization",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Identify and sell professional services engagements.

        Args:
            state: Current agent state with customer requirements

        Returns:
            Updated state with PS recommendation
        """
        self.logger.info("prof_services_seller_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Qualify for professional services
        qualification = self._qualify_for_services(customer_metadata)

        # Recommend service offerings
        recommended_services = self._recommend_services(
            qualification,
            customer_metadata
        )

        # Scope and estimate projects
        project_estimates = self._scope_projects(
            recommended_services,
            customer_metadata
        )

        # Calculate value and ROI
        value_analysis = self._calculate_services_value(
            project_estimates,
            customer_metadata
        )

        # Build engagement proposal
        proposal = self._build_proposal(
            recommended_services,
            project_estimates,
            value_analysis,
            customer_metadata
        )

        # Generate risk mitigation plan
        risk_mitigation = self._generate_risk_mitigation()

        # Search KB for PS resources
        kb_results = await self.search_knowledge_base(
            "professional services custom integration migration",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_services_response(
            message,
            qualification,
            recommended_services,
            project_estimates,
            value_analysis,
            proposal,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.86
        state["ps_qualification"] = qualification
        state["recommended_services"] = recommended_services
        state["project_estimates"] = project_estimates
        state["value_analysis"] = value_analysis
        state["ps_proposal"] = proposal
        state["status"] = "resolved"

        self.logger.info(
            "prof_services_seller_completed",
            qualified=qualification["is_qualified"],
            services_count=len(recommended_services),
            total_estimate=sum(e["total_cost"] for e in project_estimates)
        )

        return state

    def _qualify_for_services(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Qualify customer for professional services"""
        qualification = {
            "is_qualified": False,
            "qualification_score": 0.0,
            "signals_met": [],
            "recommended_service_types": []
        }

        total_weight = 0
        weighted_score = 0

        for signal_name, config in self.PS_QUALIFICATION_SIGNALS.items():
            metric = config["metric"]
            threshold = config["threshold"]
            weight = config["weight"]
            total_weight += weight

            actual_value = customer_metadata.get(metric, 0)

            if actual_value >= threshold:
                weighted_score += weight
                qualification["signals_met"].append({
                    "signal": signal_name,
                    "metric": metric,
                    "value": actual_value
                })
                qualification["recommended_service_types"].append(config["service"])

        qualification["qualification_score"] = round(
            (weighted_score / total_weight) * 100 if total_weight > 0 else 0,
            2
        )
        qualification["is_qualified"] = qualification["qualification_score"] >= 30

        return qualification

    def _recommend_services(
        self,
        qualification: Dict,
        customer_metadata: Dict
    ) -> List[str]:
        """Recommend specific professional services"""
        services = set(qualification["recommended_service_types"])

        # Add implementation consulting for large teams
        if customer_metadata.get("team_size", 0) >= 50:
            services.add("implementation_consulting")

        # Add optimization for scaling issues
        if customer_metadata.get("scaling_challenges", 0) >= 1:
            services.add("optimization_audit")

        return list(services)

    def _scope_projects(
        self,
        services: List[str],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Scope and estimate each recommended service"""
        estimates = []

        for service_id in services:
            if service_id not in self.SERVICES_CATALOG:
                continue

            service_info = self.SERVICES_CATALOG[service_id]

            # Determine complexity
            complexity = self._assess_complexity(service_id, customer_metadata)
            complexity_multiplier = self.SCOPING_FACTORS.get(
                f"complexity_{complexity}",
                1.0
            )

            # Calculate hours
            base_hours = service_info["typical_hours"]
            estimated_hours = base_hours * complexity_multiplier
            buffered_hours = estimated_hours * (1 + self.SCOPING_FACTORS["scope_creep_buffer"])

            # Calculate cost
            hourly_rate = service_info["hourly_rate"]
            total_cost = buffered_hours * hourly_rate

            # Timeline estimate
            weeks = round(buffered_hours / 40, 1)  # Assume 40-hour weeks

            estimates.append({
                "service_id": service_id,
                "service_name": service_info["name"],
                "complexity": complexity,
                "estimated_hours": round(buffered_hours, 0),
                "hourly_rate": hourly_rate,
                "total_cost": round(total_cost, 2),
                "timeline_weeks": weeks,
                "deliverables": service_info["deliverables"]
            })

        return estimates

    def _assess_complexity(self, service_id: str, customer_metadata: Dict) -> str:
        """Assess project complexity"""
        # Simplified complexity assessment
        team_size = customer_metadata.get("team_size", 0)
        integrations_count = customer_metadata.get("existing_integrations", 0)
        data_volume = customer_metadata.get("data_records", 0)

        if service_id == "integration_development":
            if integrations_count >= 10:
                return "high"
            elif integrations_count >= 5:
                return "medium"
            else:
                return "low"

        elif service_id == "data_migration":
            if data_volume >= 1000000:
                return "high"
            elif data_volume >= 100000:
                return "medium"
            else:
                return "low"

        elif service_id == "implementation_consulting":
            if team_size >= 100:
                return "high"
            elif team_size >= 50:
                return "medium"
            else:
                return "low"

        return "medium"  # Default

    def _calculate_services_value(
        self,
        estimates: List[Dict],
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate value delivered by professional services"""
        total_cost = sum(e["total_cost"] for e in estimates)
        total_hours = sum(e["estimated_hours"] for e in estimates)

        # Calculate value factors
        internal_dev_cost = total_hours * 100  # Internal dev hourly rate
        time_to_market_value = 50000  # Value of faster implementation
        risk_reduction_value = 25000  # Value of expert implementation
        ongoing_efficiency = 10000  # Annual efficiency gains

        total_value = (
            internal_dev_cost +
            time_to_market_value +
            risk_reduction_value +
            ongoing_efficiency
        )

        roi_percentage = ((total_value - total_cost) / total_cost) * 100 if total_cost > 0 else 0

        return {
            "total_cost": round(total_cost, 2),
            "total_hours": round(total_hours, 0),
            "internal_dev_alternative_cost": round(internal_dev_cost, 2),
            "time_to_market_value": time_to_market_value,
            "risk_reduction_value": risk_reduction_value,
            "ongoing_efficiency_value": ongoing_efficiency,
            "total_value": round(total_value, 2),
            "roi_percentage": round(roi_percentage, 2),
            "cost_savings": round(total_value - total_cost, 2)
        }

    def _build_proposal(
        self,
        services: List[str],
        estimates: List[Dict],
        value_analysis: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Build professional services proposal"""
        return {
            "customer": customer_metadata.get("company", "Customer"),
            "services_count": len(estimates),
            "total_investment": value_analysis["total_cost"],
            "total_hours": value_analysis["total_hours"],
            "estimated_timeline_weeks": max([e["timeline_weeks"] for e in estimates]) if estimates else 0,
            "roi": value_analysis["roi_percentage"],
            "projects": estimates,
            "payment_terms": "50% upfront, 50% on completion",
            "guarantee": "100% satisfaction guarantee"
        }

    def _generate_risk_mitigation(self) -> List[str]:
        """Generate risk mitigation strategies"""
        return [
            "Fixed-price proposals with no surprises",
            "Dedicated project manager for communication",
            "Weekly progress updates and demos",
            "Escrow milestone payments",
            "90-day warranty on all deliverables",
            "Knowledge transfer and documentation included"
        ]

    async def _generate_services_response(
        self,
        message: str,
        qualification: Dict,
        services: List[str],
        estimates: List[Dict],
        value_analysis: Dict,
        proposal: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate professional services sales response"""

        # Build qualification context
        qual_context = f"""
PS Qualification Score: {qualification['qualification_score']}/100
Services Recommended: {len(services)}
Total Investment: ${value_analysis['total_cost']:,.0f}
Total Value: ${value_analysis['total_value']:,.0f}
ROI: {value_analysis['roi_percentage']:.0f}%
"""

        # Build project estimates context
        projects_context = ""
        if estimates:
            projects_context = "\n\nProject Estimates:\n"
            for est in estimates:
                projects_context += f"- {est['service_name']}: {est['estimated_hours']}h, ${est['total_cost']:,.0f} ({est['timeline_weeks']} weeks)\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nProfessional Services Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Professional Services Seller helping customers with complex implementations.

Customer: {customer_metadata.get('company', 'Customer')}
{qual_context}
{projects_context}

Your response should:
1. Understand their specific implementation challenges
2. Position PS as the fastest, lowest-risk path to success
3. Present recommended services and deliverables
4. Explain project scope, timeline, and investment
5. Quantify value vs DIY or internal development
6. Address concerns about cost with ROI
7. Highlight expertise and risk mitigation
8. Show success stories and guarantees
9. Make starting easy with clear next steps
10. Be consultative and solution-focused

Tone: Expert, trustworthy, results-oriented"""

        user_prompt = f"""Customer message: {message}

Value Proposition:
- Professional implementation vs {value_analysis['total_hours']:.0f}+ hours of internal development
- ${value_analysis['cost_savings']:,.0f} in total value vs cost
- {max([e['timeline_weeks'] for e in estimates], default=0):.0f} week delivery timeline
- Zero implementation risk with expert delivery

{kb_context}

Generate a compelling professional services proposal."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
