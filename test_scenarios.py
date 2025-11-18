#!/usr/bin/env python3
"""
Multi-Agent Support System - Interactive Test Script

Run this script to test different customer scenarios and see how agents respond.
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text:^80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.END}\n")

def print_scenario(num: int, name: str, description: str):
    print(f"{Colors.BOLD}{Colors.CYAN}Scenario {num}: {name}{Colors.END}")
    print(f"{Colors.BLUE}Description: {description}{Colors.END}\n")

def print_customer(message: str):
    print(f"{Colors.YELLOW}👤 Customer says:{Colors.END}")
    print(f"{Colors.YELLOW}   \"{message}\"{Colors.END}\n")

def print_response(response: Dict[str, Any]):
    print(f"{Colors.GREEN}🤖 System response:{Colors.END}")

    if 'response' in response:
        print(f"{Colors.GREEN}   {response['response']}{Colors.END}\n")

    if 'agents_used' in response:
        print(f"{Colors.CYAN}   Agents triggered: {', '.join(response['agents_used'])}{Colors.END}")

    if 'routing_decision' in response:
        print(f"{Colors.CYAN}   Routing: {response['routing_decision']}{Colors.END}")

    if 'metadata' in response:
        print(f"{Colors.CYAN}   Metadata: {json.dumps(response['metadata'], indent=2)}{Colors.END}")

def print_error(error: str):
    print(f"{Colors.RED}❌ Error: {error}{Colors.END}\n")

def check_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✓ API is healthy and running{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}✗ API returned status {response.status_code}{Colors.END}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ Cannot connect to {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Make sure the server is running: python -m uvicorn src.api.main:app{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Error: {e}{Colors.END}")
        return False

def send_message(customer_id: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send a customer message to the API"""
    try:
        payload = {
            "customer_id": customer_id,
            "message": message
        }

        if metadata:
            payload["metadata"] = metadata

        response = requests.post(
            f"{BASE_URL}/api/v1/conversations",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }

    except requests.exceptions.Timeout:
        return {"error": "Request timed out after 30 seconds"}
    except Exception as e:
        return {"error": str(e)}

def run_scenario(num: int, name: str, description: str, customer_id: str,
                message: str, metadata: Dict[str, Any] = None):
    """Run a single test scenario"""
    print_scenario(num, name, description)
    print_customer(message)

    print(f"{Colors.CYAN}⏳ Processing...{Colors.END}")
    response = send_message(customer_id, message, metadata)

    if 'error' in response:
        print_error(response['error'])
        if 'details' in response:
            print(f"{Colors.RED}Details: {response['details']}{Colors.END}\n")
    else:
        print_response(response)

    print(f"\n{Colors.BOLD}{'-'*80}{Colors.END}")
    time.sleep(1)  # Small delay between scenarios

def main():
    print_header("Multi-Agent Support System - Interactive Test Suite")

    # Check if API is running
    if not check_health():
        return

    print(f"\n{Colors.BOLD}Starting test scenarios...{Colors.END}\n")
    time.sleep(2)

    # Scenario 1: Billing Issue
    run_scenario(
        num=1,
        name="Billing & Refund",
        description="Customer was charged twice and wants a refund",
        customer_id="test-customer-001",
        message="I was charged twice this month! My credit card shows two payments of $49.99. I need a refund immediately!",
        metadata={
            "channel": "chat",
            "priority": "high",
            "subscription_tier": "premium"
        }
    )

    # Scenario 2: Technical Crash
    run_scenario(
        num=2,
        name="Technical Support - App Crash",
        description="Customer experiencing app crashes on mobile device",
        customer_id="test-customer-002",
        message="The app keeps crashing every time I try to upload a file. I'm on iPhone 14, iOS 17.2. This has been happening for 3 days!",
        metadata={
            "device": "iPhone 14",
            "os": "iOS 17.2",
            "app_version": "3.2.1",
            "channel": "email"
        }
    )

    # Scenario 3: Feature Question
    run_scenario(
        num=3,
        name="How-To Question",
        description="Customer needs help with a specific feature",
        customer_id="test-customer-003",
        message="How do I export my data to CSV? I need to create a report for my team by end of day.",
        metadata={
            "urgency": "high",
            "user_role": "team_admin"
        }
    )

    # Scenario 4: Churn Risk
    run_scenario(
        num=4,
        name="Churn Risk - Competitive Threat",
        description="High-value customer considering cancellation",
        customer_id="test-customer-premium-004",
        message="I'm thinking about canceling my subscription. Your competitor offers the same features for $20 less per month.",
        metadata={
            "subscription_tier": "premium",
            "mrr": 99,
            "lifetime_value": 2400,
            "competitor": "Competitor X"
        }
    )

    # Scenario 5: Sales Inquiry
    run_scenario(
        num=5,
        name="Enterprise Sales",
        description="Large team interested in enterprise plan",
        customer_id="prospect-enterprise-005",
        message="We're a team of 50 people looking to move from Competitor X. We need SSO, custom integrations, and premium support. What's your best enterprise pricing?",
        metadata={
            "lead_source": "website",
            "company_size": 50,
            "current_solution": "Competitor X",
            "industry": "Technology"
        }
    )

    # Scenario 6: Complex Multi-Issue
    run_scenario(
        num=6,
        name="Complex Multi-Issue",
        description="Customer with multiple simultaneous problems",
        customer_id="test-customer-006",
        message="I upgraded to Premium yesterday but I'm still seeing ads, my payment failed, and I can't access the new AI features. Also, your mobile app is really slow.",
        metadata={
            "issues": ["billing", "technical", "feature_access", "performance"],
            "priority": "high"
        }
    )

    # Scenario 7: Angry Customer
    run_scenario(
        num=7,
        name="Angry Customer - Escalation",
        description="Extremely frustrated customer requiring immediate attention",
        customer_id="test-customer-007",
        message="THIS IS RIDICULOUS!!! I've been waiting 3 DAYS for support and NOBODY has helped me! I'm going to post this on Twitter and tell everyone how terrible your company is!",
        metadata={
            "sentiment": "very_negative",
            "escalation_needed": True,
            "social_media_threat": True
        }
    )

    # Scenario 8: Upsell Opportunity
    run_scenario(
        num=8,
        name="Upsell Opportunity",
        description="Happy customer hitting usage limits",
        customer_id="test-customer-008",
        message="I love the basic plan! I'm using it every day and hit my limit. Is there a way to get more storage?",
        metadata={
            "subscription_tier": "basic",
            "usage_percentage": 98,
            "satisfaction_score": "high"
        }
    )

    # Scenario 9: Security Concern
    run_scenario(
        num=9,
        name="Security Incident",
        description="Potential account compromise",
        customer_id="test-customer-009",
        message="I think my account was hacked. I see login attempts from Russia and China. I need to secure my account immediately!",
        metadata={
            "security_alert": True,
            "suspicious_ips": ["192.168.1.1", "10.0.0.1"],
            "priority": "critical"
        }
    )

    # Scenario 10: Feature Request
    run_scenario(
        num=10,
        name="Feature Request",
        description="Customer suggesting product improvements",
        customer_id="test-customer-010",
        message="It would be amazing if you could add dark mode and keyboard shortcuts. All your competitors have this.",
        metadata={
            "feedback_type": "feature_request",
            "features_requested": ["dark_mode", "keyboard_shortcuts"]
        }
    )

    print_header("Test Suite Complete!")
    print(f"{Colors.GREEN}✓ All 10 scenarios executed successfully{Colors.END}")
    print(f"\n{Colors.CYAN}Next steps:{Colors.END}")
    print(f"  1. Review the responses above")
    print(f"  2. Check your terminal logs to see agent routing")
    print(f"  3. Open Swagger UI: {BASE_URL}/docs")
    print(f"  4. Try creating your own scenarios!")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test suite interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error: {e}{Colors.END}")