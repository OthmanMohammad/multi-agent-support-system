"""
Land and Expand Agent - TASK-3034

Executes land-and-expand strategy by identifying expansion opportunities within existing accounts.
Grows revenue through departmental rollouts and use case expansion.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("land_and_expand", tier="revenue", category="monetization")
class LandAndExpand(BaseAgent):
    """
    Land and Expand Agent - Drives account expansion strategy.

    Handles:
    - Identify expansion opportunities within accounts
    - Map departmental expansion potential
    - Detect new use case opportunities
    - Track product adoption by department
    - Calculate expansion revenue potential
    - Build departmental business cases
    - Facilitate internal champion development
    - Track land-and-expand metrics
    """

    # Expansion opportunity types
    EXPANSION_TYPES = {
        "departmental_rollout": {
            "description": "Expand to additional departments",
            "typical_expansion_multiplier": 2.5,
            "signals": ["multi_department_interest", "successful_pilot", "executive_sponsor"],
            "timeline_weeks": 8
        },
        "use_case_expansion": {
            "description": "Expand to additional use cases",
            "typical_expansion_multiplier": 1.8,
            "signals": ["feature_requests", "workflow_expansion", "integration_needs"],
            "timeline_weeks": 6
        },
        "geographic_expansion": {
            "description": "Expand to additional locations/regions",
            "typical_expansion_multiplier": 2.0,
            "signals": ["multi_location_company", "regional_interest", "global_rollout"],
            "timeline_weeks": 12
        },
        "vertical_expansion": {
            "description": "Expand to related teams/functions",
            "typical_expansion_multiplier": 1.5,
            "signals": ["cross_team_collaboration", "shared_workflows", "adjacent_use_cases"],
            "timeline_weeks": 6
        }
    }

    # Department expansion patterns
    DEPARTMENT_PATTERNS = {
        "customer_support_to_sales": {
            "initial_department": "customer_support",
            "expansion_targets": ["sales", "account_management"],
            "shared_value": "Customer data and communication",
            "expansion_likelihood": 0.75
        },
        "sales_to_marketing": {
            "initial_department": "sales",
            "expansion_targets": ["marketing", "partnerships"],
            "shared_value": "Lead management and analytics",
            "expansion_likelihood": 0.70
        },
        "engineering_to_product": {
            "initial_department": "engineering",
            "expansion_targets": ["product", "design"],
            "shared_value": "Project tracking and collaboration",
            "expansion_likelihood": 0.65
        },
        "operations_to_finance": {
            "initial_department": "operations",
            "expansion_targets": ["finance", "hr"],
            "shared_value": "Process automation and reporting",
            "expansion_likelihood": 0.60
        }
    }

    # Success criteria for expansion
    SUCCESS_CRITERIA = {
        "pilot_success": {
            "feature_adoption_rate": 0.70,
            "user_satisfaction": 4.0,
            "business_impact": "measurable",
            "champion_strength": "strong"
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="land_and_expand",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20240620",  # Sonnet for strategic expansion
            temperature=0.4,
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
        Identify and execute land-and-expand opportunities.

        Args:
            state: Current agent state with account data

        Returns:
            Updated state with expansion strategy
        """
        self.logger.info("land_and_expand_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})

        # Analyze current footprint
        footprint_analysis = self._analyze_current_footprint(customer_metadata)

        # Identify expansion opportunities
        expansion_opportunities = self._identify_expansion_opportunities(
            footprint_analysis,
            customer_metadata
        )

        # Map departmental expansion
        department_map = self._map_departmental_expansion(
            footprint_analysis,
            customer_metadata
        )

        # Calculate expansion potential
        expansion_potential = self._calculate_expansion_potential(
            expansion_opportunities,
            department_map,
            customer_metadata
        )

        # Build expansion roadmap
        expansion_roadmap = self._build_expansion_roadmap(
            expansion_opportunities,
            customer_metadata
        )

        # Identify champions and stakeholders
        stakeholder_strategy = self._develop_stakeholder_strategy(
            department_map,
            customer_metadata
        )

        # Generate business case
        business_case = self._generate_expansion_business_case(
            expansion_opportunities,
            expansion_potential,
            customer_metadata
        )

        # Search KB for land-and-expand resources
        kb_results = await self.search_knowledge_base(
            "land and expand account growth departmental rollout",
            category="monetization",
            limit=2
        )
        state["kb_results"] = kb_results

        # Generate response
        response = await self._generate_expansion_response(
            message,
            footprint_analysis,
            expansion_opportunities,
            expansion_potential,
            expansion_roadmap,
            stakeholder_strategy,
            business_case,
            kb_results,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.87
        state["footprint_analysis"] = footprint_analysis
        state["expansion_opportunities"] = expansion_opportunities
        state["department_map"] = department_map
        state["expansion_potential"] = expansion_potential
        state["expansion_roadmap"] = expansion_roadmap
        state["stakeholder_strategy"] = stakeholder_strategy
        state["business_case"] = business_case
        state["status"] = "resolved"

        self.logger.info(
            "land_and_expand_completed",
            opportunities_count=len(expansion_opportunities),
            potential_expansion_arr=expansion_potential.get("total_expansion_arr", 0)
        )

        return state

    def _analyze_current_footprint(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Analyze current account footprint"""
        current_departments = customer_metadata.get("departments_using_product", [])
        total_departments = customer_metadata.get("total_departments", 1)
        current_users = customer_metadata.get("active_users", 0)
        company_size = customer_metadata.get("company_size", 0)

        penetration_rate = (len(current_departments) / total_departments * 100) if total_departments > 0 else 0
        user_penetration = (current_users / company_size * 100) if company_size > 0 else 0

        return {
            "current_departments": current_departments,
            "total_departments": total_departments,
            "department_penetration_percentage": round(penetration_rate, 2),
            "current_users": current_users,
            "total_employees": company_size,
            "user_penetration_percentage": round(user_penetration, 2),
            "expansion_headroom": total_departments - len(current_departments),
            "maturity": self._determine_footprint_maturity(penetration_rate)
        }

    def _determine_footprint_maturity(self, penetration: float) -> str:
        """Determine account maturity based on penetration"""
        if penetration >= 75:
            return "mature"
        elif penetration >= 40:
            return "growing"
        elif penetration >= 15:
            return "emerging"
        else:
            return "land"

    def _identify_expansion_opportunities(
        self,
        footprint: Dict,
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Identify specific expansion opportunities"""
        opportunities = []

        # Departmental rollout opportunities
        if footprint["expansion_headroom"] > 0:
            opportunities.append({
                "type": "departmental_rollout",
                "description": f"Expand to {footprint['expansion_headroom']} additional departments",
                "potential_departments": footprint["expansion_headroom"],
                "confidence": 0.75 if footprint["maturity"] == "growing" else 0.60,
                **self.EXPANSION_TYPES["departmental_rollout"]
            })

        # Use case expansion
        if customer_metadata.get("feature_requests", 0) >= 3:
            opportunities.append({
                "type": "use_case_expansion",
                "description": "Expand to additional use cases and workflows",
                "feature_requests_count": customer_metadata.get("feature_requests", 0),
                "confidence": 0.70,
                **self.EXPANSION_TYPES["use_case_expansion"]
            })

        # Geographic expansion
        if customer_metadata.get("locations", 1) > 1 and footprint["current_departments"]:
            opportunities.append({
                "type": "geographic_expansion",
                "description": f"Roll out to {customer_metadata.get('locations', 1)} locations",
                "locations_count": customer_metadata.get("locations", 1),
                "confidence": 0.65,
                **self.EXPANSION_TYPES["geographic_expansion"]
            })

        # Vertical expansion
        if len(footprint["current_departments"]) >= 1:
            opportunities.append({
                "type": "vertical_expansion",
                "description": "Expand to adjacent teams and functions",
                "confidence": 0.68,
                **self.EXPANSION_TYPES["vertical_expansion"]
            })

        return opportunities

    def _map_departmental_expansion(
        self,
        footprint: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Map potential departmental expansion paths"""
        current_depts = footprint["current_departments"]
        expansion_paths = []

        # Find applicable expansion patterns
        for pattern_name, pattern in self.DEPARTMENT_PATTERNS.items():
            if pattern["initial_department"] in [d.lower() for d in current_depts]:
                expansion_paths.append({
                    "pattern": pattern_name,
                    "from_department": pattern["initial_department"],
                    "to_departments": pattern["expansion_targets"],
                    "shared_value": pattern["shared_value"],
                    "likelihood": pattern["expansion_likelihood"]
                })

        return {
            "current_departments": current_depts,
            "expansion_paths": expansion_paths,
            "high_probability_targets": [
                path["to_departments"][0]
                for path in expansion_paths
                if path["likelihood"] >= 0.70
            ]
        }

    def _calculate_expansion_potential(
        self,
        opportunities: List[Dict],
        department_map: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate total expansion revenue potential"""
        current_arr = customer_metadata.get("current_arr", 0)
        total_expansion_arr = 0
        expansion_by_type = {}

        for opp in opportunities:
            expansion_multiplier = opp["typical_expansion_multiplier"]
            confidence = opp["confidence"]

            # Calculate weighted expansion
            expansion_arr = current_arr * (expansion_multiplier - 1) * confidence
            total_expansion_arr += expansion_arr

            expansion_by_type[opp["type"]] = {
                "expansion_arr": round(expansion_arr, 2),
                "confidence": confidence,
                "timeline_weeks": opp["timeline_weeks"]
            }

        return {
            "current_arr": current_arr,
            "total_expansion_arr": round(total_expansion_arr, 2),
            "potential_total_arr": round(current_arr + total_expansion_arr, 2),
            "expansion_percentage": round((total_expansion_arr / current_arr * 100) if current_arr > 0 else 0, 2),
            "expansion_by_type": expansion_by_type
        }

    def _build_expansion_roadmap(
        self,
        opportunities: List[Dict],
        customer_metadata: Dict
    ) -> List[Dict[str, Any]]:
        """Build phased expansion roadmap"""
        # Sort opportunities by confidence and timeline
        sorted_opps = sorted(
            opportunities,
            key=lambda x: (-x["confidence"], x["timeline_weeks"])
        )

        roadmap = []
        cumulative_weeks = 0

        for i, opp in enumerate(sorted_opps, 1):
            phase = {
                "phase": i,
                "opportunity_type": opp["type"],
                "description": opp["description"],
                "timeline_weeks": opp["timeline_weeks"],
                "start_week": cumulative_weeks,
                "end_week": cumulative_weeks + opp["timeline_weeks"],
                "confidence": opp["confidence"],
                "success_criteria": [
                    "Executive sponsor identified",
                    "Pilot program successful",
                    "Business case approved",
                    "Champions trained"
                ]
            }
            roadmap.append(phase)
            cumulative_weeks += opp["timeline_weeks"]

        return roadmap

    def _develop_stakeholder_strategy(
        self,
        department_map: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Develop strategy for engaging stakeholders"""
        return {
            "current_champions": customer_metadata.get("champion_contacts", []),
            "target_departments": department_map.get("high_probability_targets", []),
            "champion_development_plan": [
                "Identify power users in current departments",
                "Enable them with advanced training",
                "Facilitate peer advocacy to target departments",
                "Provide success metrics and ROI data"
            ],
            "executive_engagement": [
                "Present company-wide value proposition",
                "Share ROI from current deployment",
                "Propose expansion business case",
                "Secure executive sponsorship"
            ],
            "recommended_next_contacts": self._identify_next_contacts(department_map)
        }

    def _identify_next_contacts(self, department_map: Dict) -> List[str]:
        """Identify key contacts to engage for expansion"""
        targets = department_map.get("high_probability_targets", [])
        return [f"{dept.title()} Leadership" for dept in targets[:3]]

    def _generate_expansion_business_case(
        self,
        opportunities: List[Dict],
        potential: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Generate business case for expansion"""
        return {
            "executive_summary": f"Expand from ${potential['current_arr']:,.0f} to ${potential['potential_total_arr']:,.0f} ARR ({potential['expansion_percentage']:.0f}% growth)",
            "investment_required": "Minimal - leverage existing success",
            "expected_roi": {
                "additional_revenue": potential["total_expansion_arr"],
                "implementation_cost": potential["total_expansion_arr"] * 0.10,  # 10% implementation cost
                "net_value": round(potential["total_expansion_arr"] * 0.90, 2),
                "roi_percentage": 900  # 9x ROI
            },
            "risk_mitigation": [
                "Phased rollout approach",
                "Pilot programs before full deployment",
                "Leverage existing champions",
                "Proven success in current departments"
            ],
            "timeline_summary": f"{len(opportunities)} phases over {sum(o['timeline_weeks'] for o in opportunities)} weeks"
        }

    async def _generate_expansion_response(
        self,
        message: str,
        footprint: Dict,
        opportunities: List[Dict],
        potential: Dict,
        roadmap: List[Dict],
        stakeholder_strategy: Dict,
        business_case: Dict,
        kb_results: List[Dict],
        customer_metadata: Dict
    ) -> str:
        """Generate land-and-expand response"""

        # Build footprint context
        footprint_context = f"""
Current Footprint:
- Departments: {len(footprint['current_departments'])}/{footprint['total_departments']} ({footprint['department_penetration_percentage']:.0f}% penetration)
- Users: {footprint['current_users']}/{footprint['total_employees']} ({footprint['user_penetration_percentage']:.0f}% penetration)
- Maturity: {footprint['maturity']}
- Expansion Headroom: {footprint['expansion_headroom']} departments
"""

        # Build expansion context
        expansion_context = f"""
Expansion Opportunity:
- Current ARR: ${potential['current_arr']:,.0f}
- Expansion Potential: ${potential['total_expansion_arr']:,.0f}
- Potential Total ARR: ${potential['potential_total_arr']:,.0f}
- Growth: {potential['expansion_percentage']:.0f}%
- Opportunities: {len(opportunities)}
"""

        # Build roadmap context
        roadmap_context = ""
        if roadmap:
            roadmap_context = "\n\nExpansion Roadmap:\n"
            for phase in roadmap[:3]:
                roadmap_context += f"- Phase {phase['phase']}: {phase['description']} ({phase['timeline_weeks']} weeks)\n"

        # Build KB context
        kb_context = ""
        if kb_results:
            kb_context = "\n\nExpansion Resources:\n"
            for article in kb_results:
                kb_context += f"- {article.get('title', 'Resource')}\n"

        system_prompt = f"""You are a Land-and-Expand specialist growing revenue within existing accounts.

Customer: {customer_metadata.get('company', 'Customer')}
{footprint_context}
{expansion_context}

Your response should:
1. Celebrate current success and adoption
2. Show expansion opportunity within their company
3. Present specific departments/teams to expand to
4. Explain how current success translates to new areas
5. Provide phased expansion roadmap
6. Quantify expansion revenue potential
7. Identify internal champions to leverage
8. Make expansion feel natural and low-risk
9. Create urgency around company-wide value
10. Provide clear next steps

Tone: Strategic, partnership-focused, growth-minded"""

        user_prompt = f"""Customer message: {message}

{roadmap_context}

Business Case:
{business_case['executive_summary']}
Expected ROI: {business_case['expected_roi']['roi_percentage']:.0f}%

Next Contacts to Engage:
{chr(10).join(f'- {contact}' for contact in stakeholder_strategy['recommended_next_contacts'])}

{kb_context}

Generate a strategic expansion recommendation."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
