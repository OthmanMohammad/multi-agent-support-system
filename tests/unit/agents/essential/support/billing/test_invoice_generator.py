"""
Unit tests for Invoice Generator Agent.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.agents.essential.support.billing.invoice_generator import InvoiceGenerator
from src.workflow.state import create_initial_state


class TestInvoiceGenerator:
    """Test suite for Invoice Generator."""

    @pytest.fixture
    def generator(self):
        """Create generator instance for testing."""
        return InvoiceGenerator()

    @pytest.fixture
    def base_state(self):
        """Create base state for testing."""
        return create_initial_state(
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

    # Initialization Tests
    def test_initialization(self, generator):
        """Test agent initializes correctly."""
        assert generator.config.name == "invoice_generator"
        assert generator.config.type.value == "specialist"
        assert generator.config.tier == "essential"
        assert len(generator.INVOICE_TYPES) == 5

    # Invoice Type Detection Tests
    def test_determine_invoice_type_monthly(self, generator, base_state):
        """Test detecting monthly invoice request."""
        invoice_type = generator._determine_invoice_type(
            "I need my monthly invoice",
            base_state
        )
        assert invoice_type == "monthly"

    def test_determine_invoice_type_tax(self, generator, base_state):
        """Test detecting tax document request."""
        invoice_type = generator._determine_invoice_type(
            "I need a tax receipt",
            base_state
        )
        assert invoice_type == "tax_document"

    def test_determine_invoice_type_year_end(self, generator, base_state):
        """Test detecting year-end summary request."""
        invoice_type = generator._determine_invoice_type(
            "Can I get a year end summary?",
            base_state
        )
        assert invoice_type == "year_end_summary"

    def test_determine_invoice_type_resend(self, generator, base_state):
        """Test detecting resend request."""
        invoice_type = generator._determine_invoice_type(
            "I didn't receive my invoice, can you resend it?",
            base_state
        )
        assert invoice_type == "resend"

    def test_determine_invoice_type_custom(self, generator, base_state):
        """Test detecting custom invoice request."""
        invoice_type = generator._determine_invoice_type(
            "I need an invoice for a specific date range",
            base_state
        )
        assert invoice_type == "custom"

    # Monthly Invoice Tests
    @pytest.mark.asyncio
    async def test_generate_monthly_invoice(self, generator, base_state):
        """Test generating monthly invoice."""
        result = await generator._generate_monthly_invoice(
            base_state["customer_metadata"],
            base_state
        )

        assert "invoice" in result
        assert "message" in result
        assert result["invoice"]["amount"] == 100
        assert "invoice_number" in result["invoice"]
        assert result["invoice"]["invoice_number"].startswith("INV-")

    @pytest.mark.asyncio
    async def test_monthly_invoice_structure(self, generator, base_state):
        """Test monthly invoice has correct structure."""
        result = await generator._generate_monthly_invoice(
            base_state["customer_metadata"],
            base_state
        )

        invoice = result["invoice"]
        assert "invoice_date" in invoice
        assert "due_date" in invoice
        assert "period_start" in invoice
        assert "period_end" in invoice
        assert "items" in invoice
        assert len(invoice["items"]) > 0

    # Custom Invoice Tests
    @pytest.mark.asyncio
    async def test_generate_custom_invoice(self, generator, base_state):
        """Test generating custom date range invoice."""
        base_state["entities"] = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }

        result = await generator._generate_custom_invoice(
            base_state["customer_metadata"],
            base_state
        )

        assert "invoice" in result
        assert result["invoice"]["invoice_number"].startswith("INV-CUSTOM-")
        assert result["invoice"]["period_start"] == "2024-01-01"
        assert result["invoice"]["period_end"] == "2024-01-31"

    # Tax Document Tests
    @pytest.mark.asyncio
    async def test_generate_tax_document(self, generator, base_state):
        """Test generating tax document."""
        base_state["entities"] = {"year": 2024}

        result = await generator._generate_tax_document(
            base_state["customer_metadata"],
            base_state
        )

        assert "invoice" in result
        assert result["invoice"]["document_type"] == "tax_document"
        assert result["invoice"]["tax_year"] == 2024
        assert result["invoice"]["invoice_number"].startswith("TAX-")

    # Year-End Summary Tests
    @pytest.mark.asyncio
    async def test_generate_year_end_summary(self, generator, base_state):
        """Test generating year-end summary."""
        result = await generator._generate_year_end_summary(
            base_state["customer_metadata"],
            base_state
        )

        assert "invoice" in result
        assert result["invoice"]["document_type"] == "year_end_summary"
        assert "monthly_breakdown" in result["invoice"]
        assert len(result["invoice"]["monthly_breakdown"]) == 12

    # Resend Invoice Tests
    @pytest.mark.asyncio
    async def test_resend_invoice(self, generator, base_state):
        """Test resending existing invoice."""
        result = await generator._resend_invoice(
            base_state["customer_metadata"],
            base_state
        )

        assert "invoice" in result
        assert result["invoice"]["status"] == "resent"
        assert "resent" in result["message"].lower()

    # Main Processing Tests
    @pytest.mark.asyncio
    async def test_process_monthly_invoice_request(self, generator, base_state):
        """Test processing monthly invoice request."""
        result = await generator.process(base_state)

        assert result["invoice_generated"] is True
        assert "invoice_number" in result
        assert result["status"] == "resolved"
        assert ("sent to" in result["agent_response"].lower() or "sent it to" in result["agent_response"].lower())

    @pytest.mark.asyncio
    async def test_process_tax_document_request(self, generator):
        """Test processing tax document request."""
        state = create_initial_state(
            "I need a tax receipt for 2024",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 100,
                    "email": "test@example.com"
                }
            }
        )
        state["entities"] = {"year": 2024}

        result = await generator.process(state)

        assert result["invoice_generated"] is True
        assert "TAX-" in result["invoice_number"]

    # Email Sending Tests
    @pytest.mark.asyncio
    async def test_send_invoice_email(self, generator, base_state):
        """Test invoice email sending (mocked)."""
        invoice = {"invoice_number": "INV-123456", "amount": 100}

        # Should not raise exception
        await generator._send_invoice_email(
            "test@example.com",
            invoice,
            base_state
        )

    # Edge Cases
    @pytest.mark.asyncio
    async def test_missing_email_address(self, generator):
        """Test handling missing email address."""
        state = create_initial_state(
            "I need my invoice",
            context={
                "customer_metadata": {
                    "plan": "basic",
                    "mrr": 50,
                    "billing_cycle": "monthly"
                }
            }
        )

        result = await generator.process(state)

        # Should handle gracefully with default email
        assert "agent_response" in result
        assert result["invoice_generated"] is True

    @pytest.mark.asyncio
    async def test_zero_mrr_invoice(self, generator):
        """Test invoice generation with zero MRR (free plan)."""
        state = create_initial_state(
            "I need an invoice",
            context={
                "customer_metadata": {
                    "plan": "free",
                    "mrr": 0,
                    "email": "free@example.com"
                }
            }
        )

        result = await generator.process(state)

        assert result["invoice_generated"] is True
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_invalid_date_format_in_custom_invoice(self, generator, base_state):
        """Test custom invoice with invalid date format."""
        base_state["entities"] = {
            "start_date": "invalid-date",
            "end_date": "also-invalid"
        }

        # Should fall back to defaults without raising exception
        result = await generator._generate_custom_invoice(
            base_state["customer_metadata"],
            base_state
        )

        assert "invoice" in result
        assert "amount" in result["invoice"]

    # Integration Tests
    @pytest.mark.asyncio
    async def test_annual_plan_invoice(self, generator):
        """Test invoice for annual billing plan."""
        state = create_initial_state(
            "I need my invoice",
            context={
                "customer_metadata": {
                    "plan": "premium",
                    "mrr": 200,
                    "billing_cycle": "annual",
                    "email": "annual@example.com"
                }
            }
        )

        result = await generator.process(state)

        assert result["invoice_generated"] is True
        assert result["status"] == "resolved"
