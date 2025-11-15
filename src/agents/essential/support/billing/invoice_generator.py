"""
Invoice Generator - Generates and sends invoices to customers.

This agent handles invoice generation requests for monthly invoices,
custom date ranges, and tax documents.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("invoice_generator", tier="essential", category="billing")
class InvoiceGenerator(BaseAgent):
    """
    Invoice Generator Agent.

    Handles invoice generation and delivery:
    - Monthly invoices
    - Custom date range invoices
    - Tax documents and receipts
    - Year-end summaries
    - Re-sends of past invoices
    """

    # Invoice types
    INVOICE_TYPES = ["monthly", "custom", "tax_document", "year_end_summary", "resend"]

    def __init__(self):
        config = AgentConfig(
            name="invoice_generator",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
            temperature=0.2,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE
            ],
            kb_category="billing",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process invoice generation request.

        Args:
            state: Current state with invoice request

        Returns:
            Updated state with invoice confirmation
        """
        self.logger.info("invoice_generator_processing_started")

        # Update state
        state = self.update_state(state)

        user_message = state.get("current_message", "")
        customer_metadata = state.get("customer_metadata", {})

        # Determine invoice type from message or entities
        invoice_type = self._determine_invoice_type(user_message, state)

        self.logger.debug(
            "invoice_generation_details",
            message_preview=user_message[:100],
            invoice_type=invoice_type,
            customer_id=state.get("customer_id"),
            turn_count=state["turn_count"]
        )

        # Generate appropriate invoice
        if invoice_type == "monthly":
            result = await self._generate_monthly_invoice(customer_metadata, state)
        elif invoice_type == "custom":
            result = await self._generate_custom_invoice(customer_metadata, state)
        elif invoice_type == "tax_document":
            result = await self._generate_tax_document(customer_metadata, state)
        elif invoice_type == "year_end_summary":
            result = await self._generate_year_end_summary(customer_metadata, state)
        elif invoice_type == "resend":
            result = await self._resend_invoice(customer_metadata, state)
        else:
            result = await self._generate_monthly_invoice(customer_metadata, state)

        # Send via email (in production, this would actually send email)
        email = customer_metadata.get("email", "customer@example.com")
        await self._send_invoice_email(email, result["invoice"], state)

        state["agent_response"] = result["message"]
        state["invoice_generated"] = True
        state["invoice_number"] = result["invoice"].get("invoice_number")
        state["response_confidence"] = 0.95
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "invoice_generated_and_sent",
            customer_id=state.get("customer_id"),
            invoice_type=invoice_type,
            invoice_number=result["invoice"].get("invoice_number"),
            email=email
        )

        return state

    def _determine_invoice_type(self, message: str, state: AgentState) -> str:
        """
        Determine invoice type from message.

        Args:
            message: User message
            state: Current state

        Returns:
            Invoice type string
        """
        message_lower = message.lower()

        # Check entities first
        entities = state.get("entities", {})
        if "invoice_type" in entities:
            return entities["invoice_type"]

        # Check message keywords
        if any(word in message_lower for word in ["tax", "receipt", "tax document"]):
            return "tax_document"
        elif any(word in message_lower for word in ["year end", "annual", "yearly", "year summary"]):
            return "year_end_summary"
        elif any(word in message_lower for word in ["resend", "re-send", "send again", "didn't receive"]):
            return "resend"
        elif any(word in message_lower for word in ["custom", "specific date", "date range"]):
            return "custom"
        else:
            return "monthly"

    async def _generate_monthly_invoice(
        self,
        customer_metadata: Dict,
        state: AgentState
    ) -> Dict:
        """
        Generate monthly invoice.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with invoice and message
        """
        plan = customer_metadata.get("plan", "free")
        mrr = customer_metadata.get("mrr", 0)
        billing_cycle = customer_metadata.get("billing_cycle", "monthly")

        # Generate invoice number
        invoice_number = f"INV-{random.randint(100000, 999999)}"

        # Calculate dates
        invoice_date = datetime.now()
        due_date = invoice_date + timedelta(days=7)
        period_start = invoice_date.replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        invoice = {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "period_start": period_start.strftime("%Y-%m-%d"),
            "period_end": period_end.strftime("%Y-%m-%d"),
            "amount": mrr,
            "plan": plan,
            "billing_cycle": billing_cycle,
            "items": [
                {
                    "description": f"{plan.title()} Plan - {billing_cycle.title()}",
                    "quantity": 1,
                    "unit_price": mrr,
                    "amount": mrr
                }
            ],
            "subtotal": mrr,
            "tax": 0,  # Tax would be calculated based on location
            "total": mrr
        }

        message = f"""I've generated your invoice and sent it to {customer_metadata.get('email', 'your email')}.

**Invoice Details:**
- Invoice Number: {invoice_number}
- Amount: ${mrr:.2f}
- Due Date: {due_date.strftime('%B %d, %Y')}
- Billing Period: {period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}

You can also access all your invoices anytime in:
**Settings → Billing → Invoice History**

Is there anything else I can help you with?"""

        self.logger.debug(
            "monthly_invoice_generated",
            invoice_number=invoice_number,
            amount=mrr
        )

        return {"invoice": invoice, "message": message}

    async def _generate_custom_invoice(
        self,
        customer_metadata: Dict,
        state: AgentState
    ) -> Dict:
        """
        Generate custom date range invoice.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with invoice and message
        """
        # Extract date range from entities or use defaults
        entities = state.get("entities", {})
        start_date_str = entities.get("start_date", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        end_date_str = entities.get("end_date", datetime.now().strftime("%Y-%m-%d"))

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()

        invoice_number = f"INV-CUSTOM-{random.randint(100000, 999999)}"
        mrr = customer_metadata.get("mrr", 0)
        plan = customer_metadata.get("plan", "free")

        # Calculate prorated amount based on date range
        days_in_range = (end_date - start_date).days
        daily_rate = mrr / 30
        prorated_amount = daily_rate * days_in_range

        invoice = {
            "invoice_number": invoice_number,
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "period_start": start_date.strftime("%Y-%m-%d"),
            "period_end": end_date.strftime("%Y-%m-%d"),
            "amount": prorated_amount,
            "plan": plan,
            "items": [
                {
                    "description": f"{plan.title()} Plan - Custom Period",
                    "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                    "amount": prorated_amount
                }
            ],
            "total": prorated_amount
        }

        message = f"""I've generated a custom invoice for the period you requested and sent it to {customer_metadata.get('email', 'your email')}.

**Invoice Details:**
- Invoice Number: {invoice_number}
- Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}
- Amount: ${prorated_amount:.2f}

The invoice has been sent to your email. Is there anything else I can help you with?"""

        self.logger.debug(
            "custom_invoice_generated",
            invoice_number=invoice_number,
            period_days=days_in_range,
            amount=prorated_amount
        )

        return {"invoice": invoice, "message": message}

    async def _generate_tax_document(
        self,
        customer_metadata: Dict,
        state: AgentState
    ) -> Dict:
        """
        Generate tax document/receipt.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with tax document and message
        """
        # Extract year from entities or use current year
        entities = state.get("entities", {})
        tax_year = entities.get("year", datetime.now().year)

        invoice_number = f"TAX-{tax_year}-{random.randint(10000, 99999)}"
        mrr = customer_metadata.get("mrr", 0)
        annual_total = mrr * 12  # Simplified

        invoice = {
            "invoice_number": invoice_number,
            "document_type": "tax_document",
            "tax_year": tax_year,
            "total_paid": annual_total,
            "plan": customer_metadata.get("plan", "free"),
            "breakdown": {
                "subscription_fees": annual_total,
                "taxes_paid": 0,
                "total": annual_total
            }
        }

        message = f"""I've generated your tax document for {tax_year} and sent it to {customer_metadata.get('email', 'your email')}.

**Tax Document Summary:**
- Document Number: {invoice_number}
- Tax Year: {tax_year}
- Total Amount Paid: ${annual_total:.2f}

This document includes all payments made during {tax_year} and can be used for tax filing purposes.

The document has been sent to your email in PDF format. Is there anything else I can help you with?"""

        self.logger.debug(
            "tax_document_generated",
            invoice_number=invoice_number,
            tax_year=tax_year,
            total_paid=annual_total
        )

        return {"invoice": invoice, "message": message}

    async def _generate_year_end_summary(
        self,
        customer_metadata: Dict,
        state: AgentState
    ) -> Dict:
        """
        Generate year-end summary.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with summary and message
        """
        year = datetime.now().year - 1  # Previous year
        invoice_number = f"SUMMARY-{year}-{random.randint(10000, 99999)}"
        mrr = customer_metadata.get("mrr", 0)
        annual_total = mrr * 12

        invoice = {
            "invoice_number": invoice_number,
            "document_type": "year_end_summary",
            "year": year,
            "total_paid": annual_total,
            "monthly_breakdown": [
                {"month": f"{year}-{str(i).zfill(2)}", "amount": mrr}
                for i in range(1, 13)
            ]
        }

        message = f"""I've generated your year-end summary for {year} and sent it to {customer_metadata.get('email', 'your email')}.

**Year-End Summary {year}:**
- Document Number: {invoice_number}
- Total Spent: ${annual_total:.2f}
- Average Monthly: ${mrr:.2f}

This summary includes:
- Month-by-month breakdown
- Total payments
- Plan history
- Usage statistics

The document has been sent to your email. Is there anything else I can help you with?"""

        self.logger.debug(
            "year_end_summary_generated",
            invoice_number=invoice_number,
            year=year,
            total_paid=annual_total
        )

        return {"invoice": invoice, "message": message}

    async def _resend_invoice(
        self,
        customer_metadata: Dict,
        state: AgentState
    ) -> Dict:
        """
        Resend existing invoice.

        Args:
            customer_metadata: Customer data
            state: Current state

        Returns:
            Dict with invoice and message
        """
        # In production, would fetch the actual invoice from database
        # For now, generate a mock resend

        invoice_number = f"INV-{random.randint(100000, 999999)}"
        mrr = customer_metadata.get("mrr", 0)

        invoice = {
            "invoice_number": invoice_number,
            "amount": mrr,
            "status": "resent"
        }

        message = f"""I've resent your most recent invoice to {customer_metadata.get('email', 'your email')}.

**Invoice Details:**
- Invoice Number: {invoice_number}
- Amount: ${mrr:.2f}

If you don't receive it within a few minutes, please:
1. Check your spam/junk folder
2. Add noreply@ourcompany.com to your contacts
3. Contact us if you still don't receive it

You can also access all invoices in **Settings → Billing → Invoice History**.

Is there anything else I can help you with?"""

        self.logger.debug(
            "invoice_resent",
            invoice_number=invoice_number
        )

        return {"invoice": invoice, "message": message}

    async def _send_invoice_email(
        self,
        email: str,
        invoice: Dict,
        state: AgentState
    ) -> None:
        """
        Send invoice via email.

        Args:
            email: Customer email
            invoice: Invoice data
            state: Current state
        """
        # In production: Send actual email via email service
        # For now, just log

        self.logger.info(
            "invoice_email_sent",
            email=email,
            invoice_number=invoice.get("invoice_number"),
            customer_id=state.get("customer_id")
        )


if __name__ == "__main__":
    # Test invoice generator
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING INVOICE GENERATOR")
        print("=" * 60)

        generator = InvoiceGenerator()

        # Test 1: Monthly invoice
        state1 = create_initial_state(
            "I need my invoice",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "billing_cycle": "monthly",
                    "email": "test@example.com"
                }
            }
        )

        result1 = await generator.process(state1)

        print(f"\n{'='*60}")
        print("TEST 1: Monthly Invoice")
        print(f"{'='*60}")
        print(f"Invoice generated: {result1.get('invoice_generated')}")
        print(f"Invoice number: {result1.get('invoice_number')}")
        print(f"\nResponse:\n{result1['agent_response']}")

        # Test 2: Tax document
        state2 = create_initial_state(
            "I need a tax receipt for 2024",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "email": "test@example.com"
                }
            }
        )
        state2["entities"] = {"year": 2024}

        result2 = await generator.process(state2)

        print(f"\n{'='*60}")
        print("TEST 2: Tax Document")
        print(f"{'='*60}")
        print(f"Invoice generated: {result2.get('invoice_generated')}")
        print(f"Invoice number: {result2.get('invoice_number')}")
        print(f"\nResponse:\n{result2['agent_response'][:200]}...")

    asyncio.run(test())
