"""
Billing Calculator Agent - TASK-3012

Calculates accurate usage-based bills with tiered pricing, discounts, and proration.
Generates detailed invoices with line-item breakdowns.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("billing_calculator", tier="revenue", category="monetization")
class BillingCalculator(BaseAgent):
    """
    Billing Calculator Agent - Calculates accurate usage-based bills.

    Handles:
    - Usage-based billing calculations
    - Tiered pricing application
    - Volume discount calculations
    - Overage charge computation
    - Proration for mid-cycle changes
    - Tax calculation
    - Credit application
    - Invoice generation with line items
    """

    # Pricing tier configurations
    PRICING_TIERS = {
        "api_calls": [
            {"up_to": 100000, "rate": 0.00},      # First 100k free
            {"up_to": 500000, "rate": 0.01},      # $0.01 per call
            {"up_to": 1000000, "rate": 0.008},    # Volume discount
            {"up_to": float('inf'), "rate": 0.005}  # Enterprise rate
        ],
        "storage_gb": [
            {"up_to": 100, "rate": 0.00},         # First 100GB free
            {"up_to": 500, "rate": 10.00},        # $10/GB
            {"up_to": 1000, "rate": 8.00},        # Volume discount
            {"up_to": float('inf'), "rate": 5.00}   # Enterprise rate
        ]
    }

    # Volume discount thresholds
    VOLUME_DISCOUNTS = [
        {"min_total": 10000, "discount_rate": 0.05},   # 5% off $10k+
        {"min_total": 25000, "discount_rate": 0.10},   # 10% off $25k+
        {"min_total": 50000, "discount_rate": 0.15},   # 15% off $50k+
        {"min_total": 100000, "discount_rate": 0.20},  # 20% off $100k+
    ]

    # Tax rates by region
    TAX_RATES = {
        "US_CA": 0.0875,    # California sales tax
        "US_NY": 0.08875,   # New York sales tax
        "US_TX": 0.0825,    # Texas sales tax
        "US": 0.00,         # No sales tax for most states
        "EU": 0.20,         # VAT
        "UK": 0.20,         # VAT
        "CA": 0.05,         # GST
    }

    def __init__(self):
        config = AgentConfig(
            name="billing_calculator",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",  # Fast, accurate calculations
            temperature=0.1,  # Very low for financial accuracy
            max_tokens=600,
            capabilities=[
                AgentCapability.CONTEXT_AWARE
            ],
            tier="revenue"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Calculate usage-based bill for customer.

        Args:
            state: Current agent state with usage and billing data

        Returns:
            Updated state with bill calculation
        """
        self.logger.info("billing_calculator_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_metadata = state.get("customer_metadata", {})
        usage_data = state.get("current_usage", customer_metadata.get("usage_data", {}))

        # Calculate base plan cost
        base_plan_cost = self._calculate_base_plan_cost(customer_metadata)

        # Calculate usage charges (tiered pricing)
        usage_charges = self._calculate_usage_charges(
            usage_data,
            customer_metadata
        )

        # Calculate overage charges
        overage_charges = self._calculate_overage_charges(
            usage_data,
            customer_metadata
        )

        # Apply discounts
        discount_info = self._apply_discounts(
            base_plan_cost,
            usage_charges,
            overage_charges,
            customer_metadata
        )

        # Calculate proration if needed
        proration = self._calculate_proration(customer_metadata)

        # Calculate subtotal
        subtotal = (
            base_plan_cost +
            usage_charges["total"] +
            overage_charges["total"] -
            discount_info["total_discount"] +
            proration["amount"]
        )

        # Apply credits
        credits_applied = self._apply_credits(subtotal, customer_metadata)

        # Calculate tax
        tax_info = self._calculate_tax(subtotal - credits_applied, customer_metadata)

        # Calculate total
        total = subtotal - credits_applied + tax_info["tax_amount"]

        # Generate line items
        line_items = self._generate_line_items(
            base_plan_cost,
            usage_charges,
            overage_charges,
            discount_info,
            proration,
            credits_applied,
            tax_info
        )

        # Generate invoice
        invoice = self._generate_invoice(
            customer_metadata,
            line_items,
            subtotal,
            credits_applied,
            tax_info,
            total
        )

        # Generate response
        response = await self._generate_billing_response(
            message,
            invoice,
            customer_metadata
        )

        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.98  # High confidence for calculations
        state["base_plan_cost"] = base_plan_cost
        state["usage_charges"] = usage_charges
        state["overage_charges"] = overage_charges
        state["discount_info"] = discount_info
        state["proration"] = proration
        state["credits_applied"] = credits_applied
        state["tax_info"] = tax_info
        state["invoice"] = invoice
        state["status"] = "resolved"

        self.logger.info(
            "billing_calculator_completed",
            total_amount=total,
            line_items_count=len(line_items),
            has_overages=overage_charges["total"] > 0
        )

        return state

    def _calculate_base_plan_cost(self, customer_metadata: Dict) -> float:
        """Calculate base plan subscription cost"""
        plan_cost = customer_metadata.get("base_plan_cost", 0)
        return float(plan_cost)

    def _calculate_usage_charges(
        self,
        usage_data: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate tiered usage charges"""
        charges = {
            "by_metric": {},
            "total": 0.0
        }

        for metric, usage_amount in usage_data.items():
            if metric not in self.PRICING_TIERS:
                continue

            tiers = self.PRICING_TIERS[metric]
            metric_charge = 0.0
            remaining_usage = usage_amount
            previous_limit = 0

            for tier in tiers:
                tier_limit = tier["up_to"]
                tier_rate = tier["rate"]

                # Calculate usage in this tier
                if remaining_usage <= 0:
                    break

                tier_usage = min(remaining_usage, tier_limit - previous_limit)
                tier_charge = tier_usage * tier_rate

                metric_charge += tier_charge
                remaining_usage -= tier_usage
                previous_limit = tier_limit

                if tier_limit == float('inf'):
                    break

            charges["by_metric"][metric] = {
                "usage": usage_amount,
                "charge": round(metric_charge, 2)
            }
            charges["total"] += metric_charge

        charges["total"] = round(charges["total"], 2)
        return charges

    def _calculate_overage_charges(
        self,
        usage_data: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Calculate overage charges for usage beyond plan limits"""
        overage = {
            "by_metric": {},
            "total": 0.0
        }

        plan_limits = customer_metadata.get("plan_limits", {})
        overage_pricing = customer_metadata.get("overage_pricing", {})

        for metric, usage_amount in usage_data.items():
            limit_key = f"{metric}_limit"
            limit = plan_limits.get(limit_key, float('inf'))

            if usage_amount > limit and limit != float('inf'):
                overage_amount = usage_amount - limit
                overage_rate = overage_pricing.get(metric, {}).get("rate", 0)
                overage_charge = overage_amount * overage_rate

                overage["by_metric"][metric] = {
                    "overage_amount": overage_amount,
                    "rate": overage_rate,
                    "charge": round(overage_charge, 2)
                }
                overage["total"] += overage_charge

        overage["total"] = round(overage["total"], 2)
        return overage

    def _apply_discounts(
        self,
        base_cost: float,
        usage_charges: Dict,
        overage_charges: Dict,
        customer_metadata: Dict
    ) -> Dict[str, Any]:
        """Apply volume and promotional discounts"""
        discount_info = {
            "discounts_applied": [],
            "total_discount": 0.0
        }

        subtotal_before_discount = base_cost + usage_charges["total"] + overage_charges["total"]

        # Apply volume discounts
        for volume_tier in reversed(self.VOLUME_DISCOUNTS):
            if subtotal_before_discount >= volume_tier["min_total"]:
                volume_discount = subtotal_before_discount * volume_tier["discount_rate"]
                discount_info["discounts_applied"].append({
                    "type": "volume_discount",
                    "rate": volume_tier["discount_rate"],
                    "amount": round(volume_discount, 2)
                })
                discount_info["total_discount"] += volume_discount
                break

        # Apply promotional discounts
        promo_discount = customer_metadata.get("promotional_discount", {})
        if promo_discount:
            if promo_discount.get("type") == "percentage":
                promo_amount = subtotal_before_discount * promo_discount.get("value", 0)
            else:
                promo_amount = promo_discount.get("value", 0)

            if promo_amount > 0:
                discount_info["discounts_applied"].append({
                    "type": "promotional",
                    "description": promo_discount.get("description", "Promotional discount"),
                    "amount": round(promo_amount, 2)
                })
                discount_info["total_discount"] += promo_amount

        discount_info["total_discount"] = round(discount_info["total_discount"], 2)
        return discount_info

    def _calculate_proration(self, customer_metadata: Dict) -> Dict[str, Any]:
        """Calculate proration for mid-cycle plan changes"""
        proration = {
            "applicable": False,
            "amount": 0.0,
            "description": ""
        }

        plan_change = customer_metadata.get("plan_change", {})
        if not plan_change:
            return proration

        old_cost = plan_change.get("old_plan_cost", 0)
        new_cost = plan_change.get("new_plan_cost", 0)
        days_remaining = plan_change.get("days_remaining", 0)
        days_in_period = plan_change.get("days_in_period", 30)

        if days_remaining > 0 and days_remaining < days_in_period:
            # Credit old plan, charge new plan prorated
            old_credit = -(old_cost * days_remaining / days_in_period)
            new_charge = new_cost * days_remaining / days_in_period
            proration_amount = old_credit + new_charge

            proration["applicable"] = True
            proration["amount"] = round(proration_amount, 2)
            proration["description"] = f"Proration for {days_remaining} days remaining"

        return proration

    def _apply_credits(self, subtotal: float, customer_metadata: Dict) -> float:
        """Apply account credits to bill"""
        available_credits = customer_metadata.get("account_credits", 0)
        credits_to_apply = min(available_credits, subtotal)
        return round(credits_to_apply, 2)

    def _calculate_tax(self, taxable_amount: float, customer_metadata: Dict) -> Dict[str, Any]:
        """Calculate applicable taxes"""
        tax_info = {
            "tax_amount": 0.0,
            "tax_rate": 0.0,
            "tax_region": "US"
        }

        tax_region = customer_metadata.get("tax_region", "US")
        tax_rate = self.TAX_RATES.get(tax_region, 0.0)

        tax_amount = taxable_amount * tax_rate

        tax_info["tax_amount"] = round(tax_amount, 2)
        tax_info["tax_rate"] = tax_rate
        tax_info["tax_region"] = tax_region

        return tax_info

    def _generate_line_items(
        self,
        base_cost: float,
        usage_charges: Dict,
        overage_charges: Dict,
        discount_info: Dict,
        proration: Dict,
        credits_applied: float,
        tax_info: Dict
    ) -> List[Dict[str, Any]]:
        """Generate invoice line items"""
        line_items = []

        # Base plan
        if base_cost > 0:
            line_items.append({
                "description": "Base Plan Subscription",
                "quantity": 1,
                "unit_price": base_cost,
                "amount": base_cost
            })

        # Usage charges
        for metric, charge_info in usage_charges.get("by_metric", {}).items():
            if charge_info["charge"] > 0:
                line_items.append({
                    "description": f"{metric.replace('_', ' ').title()} Usage",
                    "quantity": charge_info["usage"],
                    "unit_price": charge_info["charge"] / charge_info["usage"] if charge_info["usage"] > 0 else 0,
                    "amount": charge_info["charge"]
                })

        # Overage charges
        for metric, overage_info in overage_charges.get("by_metric", {}).items():
            if overage_info["charge"] > 0:
                line_items.append({
                    "description": f"{metric.replace('_', ' ').title()} Overage",
                    "quantity": overage_info["overage_amount"],
                    "unit_price": overage_info["rate"],
                    "amount": overage_info["charge"]
                })

        # Discounts
        for discount in discount_info.get("discounts_applied", []):
            line_items.append({
                "description": f"Discount - {discount.get('description', discount['type'])}",
                "quantity": 1,
                "unit_price": -discount["amount"],
                "amount": -discount["amount"]
            })

        # Proration
        if proration["applicable"]:
            line_items.append({
                "description": proration["description"],
                "quantity": 1,
                "unit_price": proration["amount"],
                "amount": proration["amount"]
            })

        # Credits
        if credits_applied > 0:
            line_items.append({
                "description": "Account Credits Applied",
                "quantity": 1,
                "unit_price": -credits_applied,
                "amount": -credits_applied
            })

        # Tax
        if tax_info["tax_amount"] > 0:
            line_items.append({
                "description": f"Tax ({tax_info['tax_region']} - {tax_info['tax_rate'] * 100}%)",
                "quantity": 1,
                "unit_price": tax_info["tax_amount"],
                "amount": tax_info["tax_amount"]
            })

        return line_items

    def _generate_invoice(
        self,
        customer_metadata: Dict,
        line_items: List[Dict],
        subtotal: float,
        credits_applied: float,
        tax_info: Dict,
        total: float
    ) -> Dict[str, Any]:
        """Generate complete invoice"""
        return {
            "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d')}-{customer_metadata.get('customer_id', 'XXXX')[-4:]}",
            "invoice_date": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "customer_id": customer_metadata.get("customer_id"),
            "customer_name": customer_metadata.get("company", "Customer"),
            "line_items": line_items,
            "subtotal": round(subtotal, 2),
            "credits_applied": round(credits_applied, 2),
            "tax": round(tax_info["tax_amount"], 2),
            "total": round(total, 2),
            "currency": "USD",
            "status": "draft"
        }

    async def _generate_billing_response(
        self,
        message: str,
        invoice: Dict,
        customer_metadata: Dict
    ) -> str:
        """Generate billing calculation response"""

        invoice_summary = f"""
Invoice Summary:
- Invoice Number: {invoice['invoice_number']}
- Subtotal: ${invoice['subtotal']:,.2f}
- Credits Applied: ${invoice['credits_applied']:,.2f}
- Tax: ${invoice['tax']:,.2f}
- Total Amount Due: ${invoice['total']:,.2f}
- Line Items: {len(invoice['line_items'])}
"""

        system_prompt = f"""You are a Billing Calculator specialist providing accurate bill calculations.

Customer: {customer_metadata.get('company', 'Customer')}
Plan: {customer_metadata.get('plan_name', 'Unknown')}
{invoice_summary}

Your response should:
1. Explain the bill calculation clearly
2. Break down charges by category (base plan, usage, overages)
3. Highlight any discounts or credits applied
4. Explain any prorated charges
5. Provide payment due date and instructions
6. Be transparent and easy to understand
7. Answer any billing questions accurately"""

        user_prompt = f"""Customer message: {message}

Generate a clear billing calculation explanation."""

        response = await self.call_llm(system_prompt, user_prompt)
        return response
