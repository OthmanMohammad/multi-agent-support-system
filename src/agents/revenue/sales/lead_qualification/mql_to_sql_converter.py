"""
MQL to SQL Converter Agent - TASK-1014

Converts Marketing Qualified Leads to Sales Qualified Leads.
Assigns to appropriate sales rep and generates handoff summary.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("mql_to_sql_converter", tier="revenue", category="sales")
class MQLtoSQLConverter(BaseAgent):
    """
    MQL to SQL Converter Agent - Specialist in converting MQLs to SQLs.

    Handles:
    - MQL to SQL conversion based on criteria
    - Sales rep assignment and routing
    - Handoff summary generation
    - Opportunity record creation
    - SLA tracking
    """

    # Conversion thresholds
    SQL_MINIMUM_SCORE = 70  # Minimum score to convert to SQL
    BANT_MINIMUM_COVERAGE = 3  # At least 3/4 BANT criteria met

    # Sales rep territories
    SALES_TERRITORIES = {
        "enterprise": {
            "min_employees": 1000,
            "min_revenue": 50000000,
            "reps": ["sarah.johnson", "michael.chen"]
        },
        "mid_market": {
            "min_employees": 200,
            "min_revenue": 10000000,
            "reps": ["emily.rodriguez", "david.kim"]
        },
        "smb": {
            "min_employees": 50,
            "min_revenue": 1000000,
            "reps": ["alex.thompson", "lisa.patel"]
        },
        "small_business": {
            "min_employees": 0,
            "min_revenue": 0,
            "reps": ["jordan.white", "taylor.green"]
        }
    }

    # Industry specialization
    INDUSTRY_SPECIALISTS = {
        "healthcare": ["sarah.johnson", "emily.rodriguez"],
        "fintech": ["michael.chen", "david.kim"],
        "saas": ["alex.thompson", "lisa.patel"],
        "ecommerce": ["jordan.white", "taylor.green"]
    }

    # SLA targets (in hours)
    SLA_FIRST_CONTACT = 24  # Contact within 24 hours
    SLA_DEMO_SCHEDULED = 48  # Demo scheduled within 48 hours

    def __init__(self):
        config = AgentConfig(
            name="mql_to_sql_converter",
            type=AgentType.SPECIALIST,
            model="claude-3-5-sonnet-20241022",
            temperature=0.3,
            max_tokens=800,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE,
                AgentCapability.DATABASE_WRITE
            ],
            kb_category="sales",
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process MQL to SQL conversion.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with conversion results
        """
        self.logger.info("mql_to_sql_converter_processing_started")

        state = self.update_state(state)

        customer_metadata = state.get("customer_metadata", {})
        lead_score = state.get("lead_score", 0)
        bant_assessment = state.get("bant_assessment", {})
        qualification_status = state.get("qualification_status", "Unknown")

        # Evaluate conversion eligibility
        conversion_eligible = self._evaluate_conversion_eligibility(
            lead_score,
            bant_assessment,
            qualification_status
        )

        if not conversion_eligible["eligible"]:
            # Not ready for conversion
            state["conversion_status"] = "not_ready"
            state["conversion_reason"] = conversion_eligible["reason"]
            state["next_action"] = "continue_nurture"
            state["status"] = "resolved"
            state["response_confidence"] = 0.85

            self.logger.info(
                "mql_not_ready_for_sql_conversion",
                reason=conversion_eligible["reason"]
            )

            return state

        # Assign sales rep
        assigned_rep = self._assign_sales_rep(customer_metadata)

        # Generate handoff summary
        handoff_summary = await self._generate_handoff_summary(
            customer_metadata,
            lead_score,
            bant_assessment,
            state
        )

        # Create opportunity record
        opportunity = self._create_opportunity_record(
            customer_metadata,
            lead_score,
            assigned_rep,
            state
        )

        # Calculate SLA deadlines
        sla_deadlines = self._calculate_sla_deadlines()

        # Update state
        state["conversion_status"] = "converted"
        state["sql_converted_at"] = datetime.now().isoformat()
        state["assigned_sales_rep"] = assigned_rep
        state["handoff_summary"] = handoff_summary
        state["opportunity_id"] = opportunity["opportunity_id"]
        state["sla_deadlines"] = sla_deadlines
        state["next_action"] = "sales_outreach"
        state["status"] = "resolved"
        state["response_confidence"] = 0.92

        self.logger.info(
            "mql_to_sql_conversion_completed",
            assigned_rep=assigned_rep,
            opportunity_id=opportunity["opportunity_id"]
        )

        return state

    def _evaluate_conversion_eligibility(
        self,
        lead_score: int,
        bant_assessment: Dict,
        qualification_status: str
    ) -> Dict[str, Any]:
        """
        Evaluate if MQL is ready for SQL conversion.

        Returns:
            Dict with 'eligible' (bool) and 'reason' (str)
        """
        # Check minimum score
        if lead_score < self.SQL_MINIMUM_SCORE:
            return {
                "eligible": False,
                "reason": f"Lead score {lead_score} below minimum {self.SQL_MINIMUM_SCORE}"
            }

        # Check qualification status
        if qualification_status != "SQL":
            return {
                "eligible": False,
                "reason": f"Qualification status is {qualification_status}, not SQL"
            }

        # Check BANT coverage
        if bant_assessment:
            bant_scores = [
                bant_assessment.get("budget", {}).get("score", 0),
                bant_assessment.get("authority", {}).get("score", 0),
                bant_assessment.get("need", {}).get("score", 0),
                bant_assessment.get("timeline", {}).get("score", 0)
            ]
            criteria_met = sum(1 for score in bant_scores if score >= 6)

            if criteria_met < self.BANT_MINIMUM_COVERAGE:
                return {
                    "eligible": False,
                    "reason": f"Only {criteria_met}/4 BANT criteria met (need {self.BANT_MINIMUM_COVERAGE})"
                }

        return {
            "eligible": True,
            "reason": "All conversion criteria met"
        }

    def _assign_sales_rep(self, customer_metadata: Dict) -> Dict[str, str]:
        """
        Assign appropriate sales rep based on territory and specialization.

        Returns:
            Dict with rep details
        """
        company_size = customer_metadata.get("company_size", 0)
        revenue = customer_metadata.get("revenue", 0)
        industry = customer_metadata.get("industry", "").lower()

        # Determine territory
        territory = "small_business"
        for territory_name, criteria in self.SALES_TERRITORIES.items():
            if (company_size >= criteria["min_employees"] and
                    revenue >= criteria["min_revenue"]):
                territory = territory_name
                break

        # Check for industry specialist
        assigned_rep = None
        if industry in self.INDUSTRY_SPECIALISTS:
            # Try to assign industry specialist from appropriate territory
            territory_reps = self.SALES_TERRITORIES[territory]["reps"]
            industry_reps = self.INDUSTRY_SPECIALISTS[industry]
            matching_reps = [rep for rep in territory_reps if rep in industry_reps]

            if matching_reps:
                assigned_rep = matching_reps[0]

        # Fall back to territory assignment
        if not assigned_rep:
            assigned_rep = self.SALES_TERRITORIES[territory]["reps"][0]

        return {
            "rep_id": assigned_rep,
            "rep_name": assigned_rep.replace(".", " ").title(),
            "territory": territory,
            "specialization": industry if industry in self.INDUSTRY_SPECIALISTS else "general"
        }

    async def _generate_handoff_summary(
        self,
        customer_metadata: Dict,
        lead_score: int,
        bant_assessment: Dict,
        state: AgentState
    ) -> str:
        """Generate handoff summary for sales rep using Claude"""

        # Extract key information
        company = customer_metadata.get("company", "Unknown")
        contact_name = customer_metadata.get("name", "Unknown")
        title = customer_metadata.get("title", "Unknown")
        company_size = customer_metadata.get("company_size", 0)

        # Build BANT summary
        bant_summary = ""
        if bant_assessment:
            bant_summary = f"""
Budget: {bant_assessment.get('budget', {}).get('score', 0)}/10 - {bant_assessment.get('budget', {}).get('estimated_budget', 'Unknown')}
Authority: {bant_assessment.get('authority', {}).get('score', 0)}/10 - Decision Maker: {bant_assessment.get('authority', {}).get('decision_maker', False)}
Need: {bant_assessment.get('need', {}).get('score', 0)}/10 - Pain Points: {', '.join(bant_assessment.get('need', {}).get('pain_points', []))}
Timeline: {bant_assessment.get('timeline', {}).get('score', 0)}/10 - {bant_assessment.get('timeline', {}).get('timeframe', 'Unknown')}
"""

        system_prompt = """You are creating a handoff summary for a sales representative.
Be concise, actionable, and highlight the most important details.
Focus on what the sales rep needs to know to have a successful first conversation."""

        user_prompt = f"""Generate a handoff summary for this SQL lead:

Company: {company}
Contact: {contact_name}, {title}
Company Size: {company_size} employees
Lead Score: {lead_score}/100

BANT Assessment:
{bant_summary}

Create a brief handoff summary (3-4 sentences) covering:
1. Why this is a good lead
2. Key talking points for first call
3. Recommended next steps"""

        response = await self.call_llm(system_prompt, user_prompt)
        return response

    def _create_opportunity_record(
        self,
        customer_metadata: Dict,
        lead_score: int,
        assigned_rep: Dict,
        state: AgentState
    ) -> Dict[str, Any]:
        """Create opportunity record in CRM"""

        opportunity_id = f"OPP-{datetime.now().strftime('%Y%m%d')}-{customer_metadata.get('email', 'unknown').split('@')[0]}"

        opportunity = {
            "opportunity_id": opportunity_id,
            "company": customer_metadata.get("company", "Unknown"),
            "contact_email": customer_metadata.get("email", ""),
            "contact_name": customer_metadata.get("name", ""),
            "lead_score": lead_score,
            "assigned_rep": assigned_rep["rep_id"],
            "territory": assigned_rep["territory"],
            "stage": "SQL - New",
            "created_at": datetime.now().isoformat(),
            "expected_close_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "estimated_value": self._estimate_deal_value(customer_metadata)
        }

        return opportunity

    def _estimate_deal_value(self, customer_metadata: Dict) -> int:
        """Estimate deal value based on company size and industry"""
        company_size = customer_metadata.get("company_size", 0)

        # Simple estimation model
        if company_size >= 1000:
            return 100000  # $100k ARR for enterprise
        elif company_size >= 200:
            return 50000   # $50k ARR for mid-market
        elif company_size >= 50:
            return 20000   # $20k ARR for SMB
        else:
            return 10000   # $10k ARR for small business

    def _calculate_sla_deadlines(self) -> Dict[str, str]:
        """Calculate SLA deadlines for follow-up actions"""
        now = datetime.now()

        return {
            "first_contact_by": (now + timedelta(hours=self.SLA_FIRST_CONTACT)).isoformat(),
            "demo_scheduled_by": (now + timedelta(hours=self.SLA_DEMO_SCHEDULED)).isoformat(),
            "sla_first_contact_hours": self.SLA_FIRST_CONTACT,
            "sla_demo_scheduled_hours": self.SLA_DEMO_SCHEDULED
        }


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        print("=" * 60)
        print("Testing MQLtoSQLConverter Agent")
        print("=" * 60)

        from src.workflow.state import create_initial_state

        # Test case: High-quality MQL ready for SQL conversion
        state = create_initial_state(
            "I'm ready to move forward with a purchase",
            context={
                "customer_metadata": {
                    "company": "Tech Innovations Inc",
                    "name": "Jane Smith",
                    "title": "VP of Engineering",
                    "email": "jane.smith@techinnovations.com",
                    "company_size": 500,
                    "industry": "saas",
                    "revenue": 25000000
                },
                "lead_score": 85,
                "qualification_status": "SQL",
                "bant_assessment": {
                    "budget": {"score": 8, "estimated_budget": "$25k-$75k/year"},
                    "authority": {"score": 9, "decision_maker": True},
                    "need": {"score": 8, "pain_points": ["Scaling", "Integration"]},
                    "timeline": {"score": 8, "timeframe": "This quarter"}
                }
            }
        )

        agent = MQLtoSQLConverter()
        result = await agent.process(state)

        print(f"\nConversion Status: {result['conversion_status']}")
        if result['conversion_status'] == "converted":
            print(f"Assigned Rep: {result['assigned_sales_rep']['rep_name']}")
            print(f"Territory: {result['assigned_sales_rep']['territory']}")
            print(f"Opportunity ID: {result['opportunity_id']}")
            print(f"\nHandoff Summary:\n{result['handoff_summary']}")
            print(f"\nSLA Deadlines:")
            for key, value in result['sla_deadlines'].items():
                print(f"  {key}: {value}")

    asyncio.run(test())
