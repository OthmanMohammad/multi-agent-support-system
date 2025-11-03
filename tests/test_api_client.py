"""
Test client for API - demonstrates usage
"""
import requests
import json
import sys
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n1. Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")


def test_chat(message: str):
    """Test chat endpoint"""
    print(f"\n2. Testing Chat: '{message}'")
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "customer_id": "test_user_123"
        }
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Conversation ID: {data['conversation_id']}")
        print(f"   Intent: {data['intent']} ({data['confidence']:.0%})")
        print(f"   Agent Path: {' → '.join(data['agent_path'])}")
        print(f"   Response: {data['message'][:100]}...")
        return data['conversation_id']
    else:
        print(f"   Error: {response.text}")
        return None


def test_get_conversation(conversation_id: str):
    """Test get conversation endpoint"""
    print(f"\n3. Getting Conversation History...")
    
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Messages: {len(data['messages'])}")
        print(f"   Agents: {', '.join(data['agent_history'])}")
        print(f"   Status: {data['status']}")
    else:
        print(f"   Error: {response.text}")


def test_streaming(message: str):
    """Test streaming endpoint"""
    print(f"\n4. Testing Streaming: '{message}'")
    
    response = requests.post(
        f"{BASE_URL}/chat/stream",
        json={
            "message": message,
            "customer_id": "test_user_streaming"
        },
        stream=True
    )
    
    print("   Stream output:")
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                print(f"   {decoded}")


def test_metrics():
    """Test metrics endpoint"""
    print(f"\n5. Getting Metrics...")
    
    response = requests.get(f"{BASE_URL}/metrics")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Conversations: {data['total_conversations']}")
        print(f"   Messages: {data['total_messages']}")
        print(f"   Agent Usage: {data['agent_usage']}")
        print(f"   Uptime: {data['uptime_seconds']:.1f}s")


if __name__ == "__main__":
    print("=" * 70)
    print("API CLIENT TEST SUITE")
    print("=" * 70)
    print("Make sure API is running: python src/api/main.py")
    print("=" * 70)
    
    try:
        # Test suite
        test_health()
        
        # Test chat
        conv_id = test_chat("I want to upgrade to premium")
        
        if conv_id:
            # Test history
            test_get_conversation(conv_id)
        
        # Test streaming
        test_streaming("How do I add team members?")
        
        # Test metrics
        test_metrics()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS COMPLETE")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API")
        print("Make sure the API is running on http://localhost:8000")
        print("Run: python src/api/main.py")