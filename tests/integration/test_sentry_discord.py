#!/usr/bin/env python3
"""
Test script for Sentry + Discord integration

This script triggers different types of errors to test that:
1. Sentry captures them correctly
2. Discord receives notifications in the right channels

Usage:
    python test_sentry_discord.py [error_type]
    
Error types:
    - critical: Trigger a fatal error
    - error: Trigger a regular error
    - warning: Trigger a warning
    - all: Trigger all types (default)
"""

import os
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

# Now we can import from src
from utils.monitoring import init_sentry, capture_exception, capture_message


def test_critical_error():
    """Test critical error that should go to #sentry-critical"""
    print("\n🔴 Testing CRITICAL error...")
    
    try:
        # Simulate a critical system failure
        raise SystemError("CRITICAL: Database connection pool exhausted - TEST ERROR")
    except SystemError as e:
        capture_exception(
            e,
            error_type="critical",
            test_mode=True,
            customer_id="cust_test_001",
            conversation_id="conv_test_001"
        )
        print("   ✓ Critical error sent to Sentry")
        print("   → Check #sentry-critical channel in Discord")


def test_standard_error():
    """Test standard error that should go to #sentry-errors"""
    print("\n🟡 Testing STANDARD error...")
    
    try:
        # Simulate a validation error
        raise ValueError("Customer email validation failed: invalid@domain - TEST ERROR")
    except ValueError as e:
        capture_exception(
            e,
            error_type="validation",
            test_mode=True,
            field="email",
            customer_id="cust_test_002"
        )
        print("   ✓ Standard error sent to Sentry")
        print("   → Check #sentry-errors channel in Discord")


def test_warning():
    """Test warning message"""
    print("\n🟠 Testing WARNING...")
    
    capture_message(
        "High confidence threshold missed - manual review recommended - TEST WARNING",
        level="warning",
        confidence_score=0.65,
        threshold=0.70,
        agent="RouterAgent",
        test_mode=True
    )
    print("   ✓ Warning sent to Sentry")
    print("   → Check #sentry-errors channel in Discord")


def test_performance_note():
    """Note about performance testing"""
    print("\n⏱️  Testing PERFORMANCE issue...")
    print("   ℹ️  Performance alerts require sustained slow requests")
    print("   ℹ️  Run your actual API with slow endpoints to trigger")
    print("   → Check #sentry-performance channel (takes 5+ minutes)")


def main():
    # Check if running from project root
    if not (project_root / "src").exists():
        print("\n❌ ERROR: Run this script from the project root directory")
        print(f"   Current directory: {Path.cwd()}")
        print(f"   Expected structure: ./src/utils/monitoring/")
        sys.exit(1)
    
    # Initialize Sentry
    print("=" * 70)
    print("SENTRY + DISCORD INTEGRATION TEST")
    print("=" * 70)
    print()
    
    # Check for SENTRY_DSN
    sentry_dsn = os.getenv("SENTRY_DSN")
    if not sentry_dsn:
        print("❌ ERROR: SENTRY_DSN not set in environment")
        print("\n   Option 1 - Set in .env file:")
        print("   SENTRY_DSN=your-dsn-here")
        print("\n   Option 2 - Set temporarily:")
        print("   Windows (PowerShell): $env:SENTRY_DSN='your-dsn-here'")
        print("   Windows (CMD): set SENTRY_DSN=your-dsn-here")
        print("   Linux/Mac: export SENTRY_DSN='your-dsn-here'")
        print("\n   Get your DSN from: https://sentry.io → Settings → Projects → Client Keys")
        sys.exit(1)
    
    print(f"✓ SENTRY_DSN found: {sentry_dsn[:50]}...")
    print()
    print("Initializing Sentry...")
    init_sentry()
    
    # Determine which tests to run
    error_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if error_type == "critical":
        test_critical_error()
    elif error_type == "error":
        test_standard_error()
    elif error_type == "warning":
        test_warning()
    elif error_type == "performance":
        test_performance_note()
    elif error_type == "all":
        test_critical_error()
        test_standard_error()
        test_warning()
        test_performance_note()
    else:
        print(f"\n❌ Unknown error type: {error_type}")
        print("   Valid types: critical, error, warning, performance, all")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✓ TESTS COMPLETED")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Wait 1-2 minutes for Sentry to process")
    print("2. Check your Discord channels for notifications:")
    print("   - #sentry-critical (should have 1 notification)")
    print("   - #sentry-errors (should have 2 notifications)")
    print("3. Check Sentry dashboard: https://sentry.io")
    print("4. If no notifications, verify:")
    print("   ✓ Alert rules are ENABLED in Sentry")
    print("   ✓ Channel IDs are correct")
    print("   ✓ Discord bot has permissions")
    print("\n5. Once verified, you can delete these test errors from Sentry")


if __name__ == "__main__":
    main()