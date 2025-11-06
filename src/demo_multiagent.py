"""
Interactive demo of multi-agent support system
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from workflow.graph import SupportGraph
from uuid import uuid4


def demo_conversation():
    """Run interactive conversation with multi-agent system"""
    print("=" * 70)
    print("🤖 MULTI-AGENT CUSTOMER SUPPORT SYSTEM")
    print("=" * 70)
    print("Router Agent + Specialist Agents (Billing, Technical, Usage, API, Escalation)")
    print("Type 'quit' to exit, 'new' to start new conversation")
    print("=" * 70)
    
    # Initialize graph
    print("\nInitializing agents...")
    graph = SupportGraph()
    
    # Conversation state
    conversation_id = str(uuid4())
    turn_count = 0
    
    print(f"\n✓ Ready! Conversation ID: {conversation_id[:8]}...")
    print("-" * 70)
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n" + "=" * 70)
            print(f"📊 Session Summary")
            print("=" * 70)
            print(f"Turns: {turn_count}")
            print(f"Conversation ID: {conversation_id}")
            print("=" * 70)
            print("Goodbye! 👋")
            break
        
        if user_input.lower() == 'new':
            conversation_id = str(uuid4())
            turn_count = 0
            print(f"\n🔄 New conversation started: {conversation_id[:8]}...")
            continue
        
        if not user_input:
            continue
        
        try:
            # Run through graph
            result = graph.run(user_input, conversation_id)
            turn_count += 1
            
            # Display agent path
            agent_path = result.get('agent_history', [])
            if agent_path:
                print(f"\n🔀 Agent Path: {' → '.join([a.upper() for a in agent_path])}")
            
            # Display intent
            intent = result.get('primary_intent')
            confidence = result.get('intent_confidence', 0)
            if intent:
                print(f"🎯 Intent: {intent} ({confidence:.0%} confidence)")
            
            # Display KB usage
            kb_results = result.get('kb_results', [])
            if kb_results:
                print(f"📚 Used {len(kb_results)} KB articles:")
                for article in kb_results:
                    print(f"   - {article['title']}")
            
            # Display response
            response = result.get('agent_response', 'No response generated')
            print(f"\nAgent: {response}")
            
            # Display status
            status = result.get('status', 'unknown')
            print(f"\n[Status: {status} | Turn: {turn_count}]")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


def demo_batch_test():
    """Run batch of test queries"""
    print("=" * 70)
    print("📦 BATCH TEST MODE")
    print("=" * 70)
    
    test_queries = [
        # Billing queries
        ("I want to upgrade to premium plan", "billing"),
        ("How much does your software cost?", "billing"),
        ("I need a refund for last month", "billing"),
        ("Can you send me an invoice?", "billing"),
        
        # Technical queries
        ("My tasks are not syncing", "technical"),
        ("I'm getting an error when I login", "technical"),
        
        # Usage queries
        ("How do I create a project?", "usage"),
        ("How do I invite team members?", "usage"),
        
        # API queries
        ("How do I authenticate with the API?", "api"),
        ("Show me a Python example for the API", "api"),
        
        # Will route to END (router answers directly)
        ("What are keyboard shortcuts?", "direct"),
        ("Hello, how are you?", "direct"),
    ]
    
    print(f"\nRunning {len(test_queries)} test queries...")
    print("=" * 70)
    
    # Initialize graph
    graph = SupportGraph()
    
    results = []
    
    for i, (query, expected_type) in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] Testing: {query[:50]}...")
        
        try:
            result = graph.run(query)
            
            # Collect stats
            agent_path = result.get('agent_history', [])
            intent = result.get('primary_intent', 'unknown')
            confidence = result.get('intent_confidence', 0)
            status = result.get('status', 'unknown')
            
            results.append({
                'query': query,
                'expected': expected_type,
                'intent': intent,
                'confidence': confidence,
                'agents': agent_path,
                'status': status,
                'success': (
                    (expected_type in agent_path) or
                    (len(agent_path) == 1 and expected_type == 'direct')
                )
            })
            
            print(f"   ✓ Intent: {intent} ({confidence:.0%})")
            print(f"   ✓ Path: {' → '.join(agent_path)}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'query': query,
                'expected': expected_type,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{'='*70}")
    print("RESULTS SUMMARY")
    print(f"{'='*70}")
    
    success_count = sum(1 for r in results if r.get('success'))
    print(f"Success Rate: {success_count}/{len(results)} ({success_count/len(results)*100:.0f}%)")
    
    print("\nDetails:")
    for i, result in enumerate(results, 1):
        status = "✓" if result.get('success') else "✗"
        print(f"{status} {i}. {result['query'][:50]}")
        if not result.get('success') and 'error' in result:
            print(f"     Error: {result['error']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        demo_batch_test()
    else:
        demo_conversation()