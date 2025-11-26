#!/usr/bin/env python3
"""
Performance Test Script - Generate slow requests to trigger Sentry alerts

This script hits your FastAPI endpoints multiple times to generate
slow transactions that will trigger performance alerts in Sentry.

Prerequisites:
1. Add test_performance_endpoints.py routes to your FastAPI app
2. Start your FastAPI server: uvicorn src.api.main:app --reload
3. Run this script to generate slow requests

Usage:
    python test_performance.py
"""

import os
import sys
import time
import asyncio
import httpx
from pathlib import Path

# Add src to path for .env loading
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded environment variables from .env file\n")
except ImportError:
    print("⚠️  python-dotenv not installed\n")


# Configuration
API_BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 15  # Number of slow requests to generate


async def make_request(client: httpx.AsyncClient, endpoint: str, request_num: int):
    """Make a single request and track timing"""
    start = time.time()
    
    try:
        response = await client.get(f"{API_BASE_URL}{endpoint}", timeout=15.0)
        duration = time.time() - start
        
        print(f"   [{request_num:2d}] {endpoint:30s} → {response.status_code} ({duration:.1f}s)")
        return True
    except Exception as e:
        duration = time.time() - start
        print(f"   [{request_num:2d}] {endpoint:30s} → ERROR: {str(e)[:50]} ({duration:.1f}s)")
        return False


async def generate_slow_requests():
    """Generate multiple slow requests to trigger performance alerts"""
    
    print("=" * 70)
    print("SENTRY PERFORMANCE TEST - Generating Slow Requests")
    print("=" * 70)
    print()
    
    # Check if SENTRY_DSN is set
    if not os.getenv("SENTRY_DSN"):
        print("⚠️  WARNING: SENTRY_DSN not set - performance won't be tracked")
        print("   Set it in .env file or continue anyway to test endpoints\n")
    
    # Check if server is running
    print("Checking if FastAPI server is running...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            print(f"✓ Server is running at {API_BASE_URL}\n")
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to {API_BASE_URL}")
        print(f"   {str(e)}")
        print("\n   Start your server first:")
        print("   uvicorn src.api.main:app --reload")
        sys.exit(1)
    
    print(f"Generating {NUM_REQUESTS} slow requests...")
    print("(This will take ~2 minutes - be patient!)\n")
    
    success_count = 0
    
    async with httpx.AsyncClient() as client:
        # Generate slow requests
        for i in range(NUM_REQUESTS):
            # Mix of slow and very slow requests
            if i % 3 == 0:
                endpoint = "/test-performance-very-slow"  # 10 seconds
            else:
                endpoint = "/test-performance-slow"  # 6 seconds
            
            success = await make_request(client, endpoint, i + 1)
            if success:
                success_count += 1
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    print()
    print("=" * 70)
    print(f"✓ COMPLETED: {success_count}/{NUM_REQUESTS} requests successful")
    print("=" * 70)
    print()
    print("What happens next:")
    print("1. Sentry collects transaction data (10% sampling by default)")
    print("2. Alert triggers when p95 > 5000ms for 5+ minutes")
    print("3. Check Sentry → Performance → See your slow transactions")
    print("4. Discord notification arrives after alert threshold is met")
    print()
    print("Timeline:")
    print("- Right now: Transactions appear in Sentry Performance tab")
    print("- After 5 minutes: Alert checks if threshold is exceeded")
    print("- After 5+ mins: Discord notification (if threshold met)")
    print()
    print("Next steps:")
    print("1. Go to https://sentry.io → Your Project → Performance")
    print("2. Look for slow transactions (6s and 10s)")
    print("3. Wait 5-10 minutes for alert to trigger")
    print("4. Check #sentry-performance channel in Discord")
    print()
    print("Note: Performance alerts take longer than error alerts!")


def main():
    """Main entry point"""
    
    # Check if test endpoints are added
    print()
    print("PREREQUISITE CHECK:")
    print("-" * 70)
    print("Have you added the test performance endpoints to your FastAPI app?")
    print()
    print("1. Copy test_performance_endpoints.py routes to:")
    print("   src/api/routes/health.py (add to existing file)")
    print("   OR create: src/api/routes/test_endpoints.py")
    print()
    print("2. Register routes in src/api/main.py:")
    print("   from api.routes import test_endpoints")
    print("   app.include_router(test_endpoints.router, tags=['testing'])")
    print()
    print("3. Start server:")
    print("   uvicorn src.api.main:app --reload")
    print("-" * 70)
    print()
    
    response = input("Ready to continue? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\nSetup the endpoints first, then run this script again!")
        sys.exit(0)
    
    print()
    
    # Run async function
    asyncio.run(generate_slow_requests())


if __name__ == "__main__":
    main()