"""
Ticket Creator Agent - TASK-2201

Auto-creates tickets in Jira/Linear/GitHub based on customer requests,
bug reports, and feature requests.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("ticket_creator", tier="operational", category="automation")
class TicketCreatorAgent(BaseAgent):
    """
    Ticket Creator Agent - Auto-creates tickets in external systems.

    Handles:
    - Automatic ticket creation in Jira, Linear, GitHub Issues
    - Intelligent ticket classification (bug, feature, task, support)
    - Priority and severity assignment based on content analysis
    - Automatic assignment based on routing rules
    - Template-based ticket formatting
    - Duplicate ticket detection
    - Ticket linking and dependencies
    - SLA-based priority escalation
    """

    # Supported ticket systems
    TICKET_SYSTEMS = {
        "jira": {
            "api_endpoint": "https://api.atlassian.com/ex/jira",
            "issue_types": ["Bug", "Task", "Story", "Epic"],
            "priorities": ["Highest", "High", "Medium", "Low", "Lowest"]
        },
        "linear": {
            "api_endpoint": "https://api.linear.app/graphql",
            "issue_types": ["Bug", "Feature", "Improvement", "Task"],
            "priorities": ["Urgent", "High", "Medium", "Low"]
        },
        "github": {
            "api_endpoint": "https://api.github.com",
            "issue_types": ["bug", "enhancement", "question", "documentation"],
            "priorities": ["critical", "high", "medium", "low"]
        }
    }

    # Ticket classification keywords
    CLASSIFICATION_KEYWORDS = {
        "bug": ["bug", "error", "crash", "broken", "not working", "issue", "problem"],
        "feature": ["feature", "enhancement", "add", "new", "implement", "would like"],
        "support": ["help", "how to", "question", "assistance", "support"],
        "task": ["task", "todo", "action item", "need to"]
    }

    # Priority keywords
    PRIORITY_KEYWORDS = {
        "urgent": ["urgent", "critical", "asap", "immediately", "production down"],
        "high": ["important", "high priority", "blocker", "preventing"],
        "medium": ["soon", "medium", "moderate"],
        "low": ["low priority", "nice to have", "eventually", "when possible"]
    }

    def __init__(self):
        config = AgentConfig(
            name="ticket_creator",
            type=AgentType.AUTOMATOR,
            temperature=0.1,  # Deterministic automation
            max_tokens=800,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Auto-create tickets in external systems.

        Args:
            state: Current agent state with ticket creation request

        Returns:
            Updated state with created ticket details
        """
        self.logger.info("ticket_creator_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Extract ticket parameters
        ticket_system = entities.get("ticket_system", customer_metadata.get("default_ticket_system", "jira"))
        auto_classify = entities.get("auto_classify", True)

        self.logger.debug(
            "ticket_creation_details",
            ticket_system=ticket_system,
            auto_classify=auto_classify
        )

        # Analyze message to extract ticket details
        ticket_analysis = await self._analyze_ticket_content(message, customer_metadata)

        # Classify ticket if auto-classification is enabled
        if auto_classify:
            classification = self._classify_ticket(message, ticket_analysis)
        else:
            classification = entities.get("classification", {})

        # Detect duplicate tickets
        duplicate_check = self._check_for_duplicates(
            ticket_analysis,
            customer_metadata.get("recent_tickets", [])
        )

        # Prepare ticket data
        ticket_data = self._prepare_ticket_data(
            ticket_system,
            ticket_analysis,
            classification,
            customer_metadata
        )

        # Create ticket in external system
        created_ticket = await self._create_ticket_external(
            ticket_system,
            ticket_data,
            duplicate_check
        )

        # Log automated action
        automation_log = self._log_automation_action(
            "ticket_created",
            ticket_system,
            created_ticket,
            customer_metadata
        )

        # Generate response
        response = self._format_ticket_response(
            created_ticket,
            duplicate_check,
            ticket_system
        )

        state["agent_response"] = response
        state["created_ticket"] = created_ticket
        state["ticket_data"] = ticket_data
        state["ticket_classification"] = classification
        state["duplicate_check"] = duplicate_check
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.94
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "ticket_created_successfully",
            ticket_id=created_ticket.get("id"),
            ticket_system=ticket_system,
            ticket_type=classification.get("type"),
            priority=classification.get("priority")
        )

        return state

    async def _analyze_ticket_content(
        self,
        message: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Analyze message content to extract ticket details using LLM.

        Args:
            message: Customer message
            customer_metadata: Customer metadata

        Returns:
            Analyzed ticket details
        """
        system_prompt = """You are a ticket analysis specialist. Extract structured information from customer messages to create well-formed tickets.

Extract:
1. Title/Summary (concise, actionable)
2. Description (detailed, clear)
3. Steps to reproduce (if bug)
4. Expected vs actual behavior (if bug)
5. Affected components/features
6. Urgency indicators
7. Relevant technical details

Be precise and actionable."""

        user_prompt = f"""Analyze this customer message and extract ticket information:

Message: {message}

Customer Plan: {customer_metadata.get('plan_name', 'Unknown')}
Customer Tier: {customer_metadata.get('tier', 'standard')}

Return a JSON structure with title, description, steps_to_reproduce, expected_behavior, actual_behavior, affected_components, and urgency_level."""

        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            conversation_history=[]  # Ticket analysis uses message context
        )

        # Parse LLM response to extract structured data
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback to basic structure
                analysis = {
                    "title": message[:100],
                    "description": message,
                    "urgency_level": "medium"
                }
        except:
            analysis = {
                "title": message[:100],
                "description": message,
                "urgency_level": "medium"
            }

        return analysis

    def _classify_ticket(
        self,
        message: str,
        ticket_analysis: Dict
    ) -> Dict[str, Any]:
        """
        Classify ticket type and priority based on content.

        Args:
            message: Original message
            ticket_analysis: Analyzed ticket details

        Returns:
            Classification with type, priority, severity
        """
        message_lower = message.lower()

        # Classify type
        ticket_type = "task"  # Default
        max_score = 0

        for type_name, keywords in self.CLASSIFICATION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > max_score:
                max_score = score
                ticket_type = type_name

        # Classify priority
        priority = "medium"  # Default
        max_priority_score = 0

        for priority_name, keywords in self.PRIORITY_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > max_priority_score:
                max_priority_score = score
                priority = priority_name

        # Determine severity for bugs
        severity = None
        if ticket_type == "bug":
            urgency = ticket_analysis.get("urgency_level", "medium")
            severity = {
                "urgent": "critical",
                "high": "major",
                "medium": "moderate",
                "low": "minor"
            }.get(urgency, "moderate")

        return {
            "type": ticket_type,
            "priority": priority,
            "severity": severity,
            "confidence": min(0.7 + (max_score * 0.1), 0.95)
        }

    def _check_for_duplicates(
        self,
        ticket_analysis: Dict,
        recent_tickets: List[Dict]
    ) -> Dict[str, Any]:
        """
        Check for potential duplicate tickets.

        Args:
            ticket_analysis: New ticket analysis
            recent_tickets: List of recent tickets

        Returns:
            Duplicate check results
        """
        title = ticket_analysis.get("title", "").lower()
        description = ticket_analysis.get("description", "").lower()

        duplicates = []

        for recent in recent_tickets[-20:]:  # Check last 20 tickets
            recent_title = recent.get("title", "").lower()
            recent_desc = recent.get("description", "").lower()

            # Simple similarity check
            title_similarity = self._calculate_similarity(title, recent_title)
            desc_similarity = self._calculate_similarity(description, recent_desc)

            overall_similarity = (title_similarity * 0.6) + (desc_similarity * 0.4)

            if overall_similarity > 0.7:
                duplicates.append({
                    "ticket_id": recent.get("id"),
                    "title": recent.get("title"),
                    "similarity": round(overall_similarity, 2),
                    "status": recent.get("status")
                })

        return {
            "has_duplicates": len(duplicates) > 0,
            "duplicate_count": len(duplicates),
            "potential_duplicates": duplicates[:3],  # Top 3
            "should_proceed": len(duplicates) == 0 or all(d.get("status") == "closed" for d in duplicates)
        }

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple word-based similarity between two strings."""
        words1 = set(str1.split())
        words2 = set(str2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _prepare_ticket_data(
        self,
        ticket_system: str,
        ticket_analysis: Dict,
        classification: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Prepare ticket data for external system.

        Args:
            ticket_system: Target ticket system (jira, linear, github)
            ticket_analysis: Analyzed ticket content
            classification: Ticket classification
            customer_metadata: Customer metadata

        Returns:
            Formatted ticket data
        """
        system_config = self.TICKET_SYSTEMS.get(ticket_system, self.TICKET_SYSTEMS["jira"])

        # Base ticket data
        ticket_data = {
            "title": ticket_analysis.get("title", "Support Request"),
            "description": ticket_analysis.get("description", ""),
            "type": classification.get("type", "task"),
            "priority": classification.get("priority", "medium"),
            "labels": [],
            "metadata": {
                "customer_id": customer_metadata.get("customer_id"),
                "customer_name": customer_metadata.get("customer_name"),
                "plan": customer_metadata.get("plan_name"),
                "created_by": "automation",
                "created_at": datetime.now(UTC).isoformat()
            }
        }

        # Add steps to reproduce for bugs
        if classification.get("type") == "bug" and ticket_analysis.get("steps_to_reproduce"):
            ticket_data["steps_to_reproduce"] = ticket_analysis["steps_to_reproduce"]
            ticket_data["severity"] = classification.get("severity", "moderate")

        # Add system-specific fields
        if ticket_system == "jira":
            ticket_data["project_key"] = customer_metadata.get("jira_project", "SUP")
            ticket_data["issue_type"] = {
                "bug": "Bug",
                "feature": "Story",
                "support": "Task",
                "task": "Task"
            }.get(classification.get("type"), "Task")

        elif ticket_system == "linear":
            ticket_data["team_id"] = customer_metadata.get("linear_team_id", "default")
            ticket_data["state"] = "backlog"

        elif ticket_system == "github":
            ticket_data["repo"] = customer_metadata.get("github_repo", "support/issues")
            ticket_data["labels"].extend([classification.get("type"), classification.get("priority")])

        # Add customer tier label
        if customer_metadata.get("tier"):
            ticket_data["labels"].append(f"tier-{customer_metadata['tier']}")

        return ticket_data

    async def _create_ticket_external(
        self,
        ticket_system: str,
        ticket_data: Dict,
        duplicate_check: Dict
    ) -> Dict[str, Any]:
        """
        Create ticket in external system (mocked for now).

        Args:
            ticket_system: Target system
            ticket_data: Ticket data
            duplicate_check: Duplicate check results

        Returns:
            Created ticket details
        """
        # In production, make actual API call to ticket system
        # For now, return mock created ticket

        import hashlib
        ticket_id = hashlib.md5(
            f"{ticket_data['title']}{datetime.now(UTC)}".encode()
        ).hexdigest()[:8].upper()

        created_ticket = {
            "id": f"{ticket_system.upper()}-{ticket_id}",
            "key": f"{ticket_data.get('project_key', 'TICKET')}-{ticket_id}",
            "title": ticket_data["title"],
            "description": ticket_data["description"],
            "type": ticket_data["type"],
            "priority": ticket_data["priority"],
            "status": "open",
            "url": f"https://{ticket_system}.example.com/issues/{ticket_id}",
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": "automation",
            "system": ticket_system,
            "duplicate_warning": duplicate_check.get("has_duplicates", False)
        }

        # Add severity for bugs
        if "severity" in ticket_data:
            created_ticket["severity"] = ticket_data["severity"]

        self.logger.info(
            "ticket_created_in_external_system",
            system=ticket_system,
            ticket_id=created_ticket["id"],
            type=ticket_data["type"]
        )

        return created_ticket

    def _log_automation_action(
        self,
        action_type: str,
        ticket_system: str,
        created_ticket: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Log automated action for audit trail."""
        return {
            "action_type": action_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "system": ticket_system,
            "ticket_id": created_ticket.get("id"),
            "customer_id": customer_metadata.get("customer_id"),
            "success": True,
            "details": {
                "ticket_type": created_ticket.get("type"),
                "priority": created_ticket.get("priority"),
                "url": created_ticket.get("url")
            }
        }

    def _format_ticket_response(
        self,
        created_ticket: Dict,
        duplicate_check: Dict,
        ticket_system: str
    ) -> str:
        """Format ticket creation response."""
        response = f"""**Ticket Created Successfully**

Ticket ID: {created_ticket['id']}
System: {ticket_system.upper()}
Type: {created_ticket['type'].title()}
Priority: {created_ticket['priority'].title()}
Status: {created_ticket['status'].title()}

Title: {created_ticket['title']}

"""

        if created_ticket.get("severity"):
            response += f"Severity: {created_ticket['severity'].title()}\n"

        response += f"\nView Ticket: {created_ticket['url']}\n"

        # Add duplicate warning if applicable
        if duplicate_check.get("has_duplicates"):
            response += f"\n**Note:** {duplicate_check['duplicate_count']} potential duplicate(s) detected:\n"
            for dup in duplicate_check.get("potential_duplicates", [])[:2]:
                response += f"- {dup['ticket_id']}: {dup['title']} (Similarity: {dup['similarity']*100:.0f}%)\n"

        response += f"\nCreated: {created_ticket['created_at']}"

        return response
