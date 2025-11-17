"""
Email Sender Agent - TASK-2203

Auto-sends templated emails for common scenarios: welcome emails, follow-ups,
escalation notifications, and customer communications.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
import json

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("email_sender", tier="operational", category="automation")
class EmailSenderAgent(BaseAgent):
    """
    Email Sender Agent - Auto-sends templated emails.

    Handles:
    - Template-based email composition
    - Dynamic variable substitution
    - Email personalization using customer data
    - Multi-recipient handling (To, CC, BCC)
    - Attachment management
    - Email scheduling and delayed sending
    - Tracking email opens and clicks
    - A/B testing for email variations
    """

    # Email templates by category
    EMAIL_TEMPLATES = {
        "welcome": {
            "subject": "Welcome to {company_name}, {customer_name}!",
            "body": """Hi {customer_name},

Welcome to {company_name}! We're excited to have you on board.

Your account has been successfully created and you're all set to get started.

Here's what you can do next:
1. Complete your profile setup
2. Explore our key features
3. Check out our getting started guide

If you have any questions, our support team is here to help.

Best regards,
The {company_name} Team""",
            "category": "onboarding"
        },
        "followup": {
            "subject": "Following up: {topic}",
            "body": """Hi {customer_name},

I wanted to follow up on {topic}.

{custom_message}

Let me know if you have any questions or need any assistance.

Best regards,
{sender_name}""",
            "category": "engagement"
        },
        "escalation": {
            "subject": "URGENT: {issue_type} - Action Required",
            "body": """Hi {customer_name},

We've detected a {issue_type} that requires immediate attention:

Issue: {issue_description}
Severity: {severity}
Ticket ID: {ticket_id}

Our team is actively working on this and will keep you updated.

Current Status: {status}

Best regards,
{company_name} Support Team""",
            "category": "support"
        },
        "feedback_request": {
            "subject": "How was your experience with {company_name}?",
            "body": """Hi {customer_name},

We'd love to hear about your recent experience with {company_name}.

Your feedback helps us improve and serve you better.

Please take a moment to share your thoughts: {survey_link}

Thank you!
The {company_name} Team""",
            "category": "feedback"
        },
        "renewal_reminder": {
            "subject": "Your {plan_name} subscription renews in {days_until_renewal} days",
            "body": """Hi {customer_name},

This is a friendly reminder that your {plan_name} subscription will renew on {renewal_date}.

Renewal Amount: {renewal_amount}
Payment Method: {payment_method}

No action is needed - your subscription will automatically renew.

If you have any questions or want to make changes, please contact us.

Best regards,
{company_name} Billing Team""",
            "category": "billing"
        }
    }

    # Email priority levels
    PRIORITY_LEVELS = {
        "urgent": {"importance": "high", "send_immediately": True},
        "high": {"importance": "high", "send_immediately": False},
        "normal": {"importance": "normal", "send_immediately": False},
        "low": {"importance": "low", "send_immediately": False}
    }

    def __init__(self):
        config = AgentConfig(
            name="email_sender",
            type=AgentType.AUTOMATOR,
            model="claude-3-haiku-20240307",
            temperature=0.1,
            max_tokens=1000,
            capabilities=[AgentCapability.DATABASE_WRITE],
            tier="operational"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Auto-send templated emails.

        Args:
            state: Current agent state with email request

        Returns:
            Updated state with sent email details
        """
        self.logger.info("email_sender_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        entities = state.get("entities", {})

        # Extract email parameters
        template_type = entities.get("email_template", "followup")
        priority = entities.get("priority", "normal")
        schedule_time = entities.get("schedule_time", None)

        self.logger.debug(
            "email_sending_details",
            template=template_type,
            priority=priority,
            scheduled=schedule_time is not None
        )

        # Get email template
        template = self.EMAIL_TEMPLATES.get(
            template_type,
            self.EMAIL_TEMPLATES["followup"]
        )

        # Extract custom parameters from message
        custom_params = await self._extract_email_parameters(
            message,
            template_type,
            customer_metadata
        )

        # Prepare email content
        email_content = self._prepare_email_content(
            template,
            custom_params,
            customer_metadata
        )

        # Personalize email
        personalized_email = self._personalize_email(
            email_content,
            customer_metadata
        )

        # Validate email
        validation = self._validate_email(personalized_email, customer_metadata)

        # Send email (or schedule if requested)
        if schedule_time:
            sent_email = await self._schedule_email(
                personalized_email,
                schedule_time,
                priority
            )
        else:
            sent_email = await self._send_email_external(
                personalized_email,
                priority,
                validation
            )

        # Track email
        tracking_info = self._setup_email_tracking(sent_email)

        # Log automation action
        automation_log = self._log_automation_action(
            "email_sent" if not schedule_time else "email_scheduled",
            sent_email,
            customer_metadata
        )

        # Generate response
        response = self._format_email_response(
            sent_email,
            tracking_info,
            schedule_time
        )

        state["agent_response"] = response
        state["sent_email"] = sent_email
        state["email_content"] = personalized_email
        state["tracking_info"] = tracking_info
        state["validation"] = validation
        state["automation_log"] = automation_log
        state["response_confidence"] = 0.96
        state["status"] = "resolved"
        state["next_agent"] = None

        self.logger.info(
            "email_sent_successfully",
            email_id=sent_email.get("id"),
            template=template_type,
            recipient=sent_email.get("to"),
            scheduled=schedule_time is not None
        )

        return state

    async def _extract_email_parameters(
        self,
        message: str,
        template_type: str,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Extract email parameters from message using LLM.

        Args:
            message: Customer message or trigger
            template_type: Email template type
            customer_metadata: Customer metadata

        Returns:
            Extracted parameters for email template
        """
        system_prompt = f"""You are an email composition specialist. Extract parameters needed for a {template_type} email.

Extract relevant information like:
- Custom message content
- Topic/subject details
- Any specific details mentioned
- Urgency indicators
- Action items

Be concise and professional."""

        user_prompt = f"""Extract email parameters from this context:

Message: {message}

Template Type: {template_type}
Customer: {customer_metadata.get('customer_name', 'Unknown')}

Return JSON with extracted parameters relevant to the email template."""

        response = await self.call_llm(system_prompt, user_prompt)

        # Parse LLM response
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                params = json.loads(json_match.group())
            else:
                params = {"custom_message": message}
        except:
            params = {"custom_message": message}

        return params

    def _prepare_email_content(
        self,
        template: Dict,
        custom_params: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Prepare email content from template and parameters.

        Args:
            template: Email template
            custom_params: Custom parameters
            customer_metadata: Customer metadata

        Returns:
            Prepared email content
        """
        # Merge template variables with custom params and customer metadata
        template_vars = {
            "company_name": "Acme Corp",
            "customer_name": customer_metadata.get("customer_name", "Valued Customer"),
            "sender_name": "Support Team",
            "plan_name": customer_metadata.get("plan_name", "Standard Plan"),
            **custom_params
        }

        # Fill in template
        subject = template["subject"].format(**{k: v for k, v in template_vars.items() if k in template["subject"]})
        body = template["body"].format(**{k: v for k, v in template_vars.items() if k in template["body"]})

        return {
            "subject": subject,
            "body": body,
            "category": template["category"],
            "template_vars": template_vars
        }

    def _personalize_email(
        self,
        email_content: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Personalize email based on customer data.

        Args:
            email_content: Base email content
            customer_metadata: Customer metadata

        Returns:
            Personalized email
        """
        # Add personalization elements
        personalized = email_content.copy()

        # Add customer-specific greeting based on tier/plan
        tier = customer_metadata.get("tier", "standard")
        if tier == "enterprise":
            personalized["body"] = f"[Enterprise Customer]\n\n{personalized['body']}"

        # Add signature
        personalized["signature"] = f"""
--
Best regards,
The Support Team
Email: support@acme-corp.com
Help Center: https://help.acme-corp.com
"""

        personalized["from_name"] = "Acme Corp Support"
        personalized["from_email"] = "support@acme-corp.com"
        personalized["reply_to"] = "support@acme-corp.com"

        return personalized

    def _validate_email(
        self,
        email: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """
        Validate email before sending.

        Args:
            email: Email to validate
            customer_metadata: Customer metadata

        Returns:
            Validation results
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }

        # Validate recipient
        if not customer_metadata.get("email"):
            validation["is_valid"] = False
            validation["errors"].append("No recipient email address")

        # Validate subject
        if not email.get("subject") or len(email["subject"]) < 5:
            validation["warnings"].append("Subject line is very short")

        # Validate body
        if not email.get("body") or len(email["body"]) < 20:
            validation["warnings"].append("Email body is very short")

        # Check for missing template variables
        if "{" in email["subject"] or "{" in email["body"]:
            validation["warnings"].append("Some template variables were not replaced")

        return validation

    async def _send_email_external(
        self,
        email: Dict,
        priority: str,
        validation: Dict
    ) -> Dict[str, Any]:
        """
        Send email via external email service (mocked).

        Args:
            email: Email content
            priority: Priority level
            validation: Validation results

        Returns:
            Sent email details
        """
        # In production, integrate with SendGrid, AWS SES, etc.
        # For now, return mock sent email

        if not validation.get("is_valid"):
            raise ValueError(f"Email validation failed: {validation['errors']}")

        import hashlib
        email_id = hashlib.md5(
            f"{email['subject']}{datetime.now(UTC)}".encode()
        ).hexdigest()[:16]

        priority_config = self.PRIORITY_LEVELS.get(priority, self.PRIORITY_LEVELS["normal"])

        sent_email = {
            "id": email_id,
            "subject": email["subject"],
            "body": email["body"] + email.get("signature", ""),
            "from": email.get("from_email", "support@acme-corp.com"),
            "from_name": email.get("from_name", "Support Team"),
            "to": email.get("to", "customer@example.com"),
            "reply_to": email.get("reply_to"),
            "priority": priority,
            "importance": priority_config["importance"],
            "status": "sent",
            "sent_at": datetime.now(UTC).isoformat(),
            "category": email.get("category", "general")
        }

        self.logger.info(
            "email_sent_via_external_service",
            email_id=email_id,
            priority=priority,
            category=email["category"]
        )

        return sent_email

    async def _schedule_email(
        self,
        email: Dict,
        schedule_time: str,
        priority: str
    ) -> Dict[str, Any]:
        """
        Schedule email for later sending.

        Args:
            email: Email content
            schedule_time: When to send
            priority: Priority level

        Returns:
            Scheduled email details
        """
        import hashlib
        email_id = hashlib.md5(
            f"{email['subject']}{schedule_time}".encode()
        ).hexdigest()[:16]

        scheduled_email = {
            "id": email_id,
            "subject": email["subject"],
            "body": email["body"] + email.get("signature", ""),
            "from": email.get("from_email", "support@acme-corp.com"),
            "to": email.get("to", "customer@example.com"),
            "priority": priority,
            "status": "scheduled",
            "scheduled_for": schedule_time,
            "created_at": datetime.now(UTC).isoformat()
        }

        return scheduled_email

    def _setup_email_tracking(self, sent_email: Dict) -> Dict[str, Any]:
        """
        Setup email tracking (opens, clicks).

        Args:
            sent_email: Sent email details

        Returns:
            Tracking configuration
        """
        return {
            "tracking_id": sent_email["id"],
            "track_opens": True,
            "track_clicks": True,
            "tracking_pixel_url": f"https://tracking.acme-corp.com/pixel/{sent_email['id']}",
            "click_tracking_enabled": True,
            "tracking_created_at": datetime.now(UTC).isoformat()
        }

    def _log_automation_action(
        self,
        action_type: str,
        sent_email: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Log automated action for audit trail."""
        return {
            "action_type": action_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "email_id": sent_email.get("id"),
            "customer_id": customer_metadata.get("customer_id"),
            "success": True,
            "details": {
                "subject": sent_email.get("subject"),
                "recipient": sent_email.get("to"),
                "category": sent_email.get("category"),
                "priority": sent_email.get("priority")
            }
        }

    def _format_email_response(
        self,
        sent_email: Dict,
        tracking_info: Dict,
        schedule_time: Optional[str]
    ) -> str:
        """Format email sending response."""
        if schedule_time:
            response = f"""**Email Scheduled Successfully**

Email ID: {sent_email['id']}
Status: Scheduled
Scheduled For: {sent_email['scheduled_for']}

Subject: {sent_email['subject']}
To: {sent_email['to']}
From: {sent_email['from']}
Priority: {sent_email['priority'].title()}

The email will be automatically sent at the scheduled time.
"""
        else:
            response = f"""**Email Sent Successfully**

Email ID: {sent_email['id']}
Status: Sent
Sent At: {sent_email['sent_at']}

Subject: {sent_email['subject']}
To: {sent_email['to']}
From: {sent_email['from']}
Priority: {sent_email['priority'].title()}
Category: {sent_email['category'].title()}

**Tracking:**
- Opens: Enabled
- Clicks: Enabled
- Tracking ID: {tracking_info['tracking_id']}
"""

        return response
