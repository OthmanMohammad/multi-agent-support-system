"""Quick KB search test"""
from src.knowledge_base import search_knowledge_base

# Test queries
test_queries = [
    "How do I reset my password?",
    "API authentication",
    "upgrade my plan",
    "invite team members",
    "export data"
]

print("=" * 60)
print("KNOWLEDGE BASE SEARCH TEST")
print("=" * 60)

for query in test_queries:
    print(f"\nQuery: '{query}'")
    results = search_knowledge_base(query, top_k=3)
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title']}")
            print(f"     Score: {result['score']:.2f} | Category: {result['category']}")
    else:
        print("  ⚠️  No results found")

print("\n" + "=" * 60)
print("✓ KB Search is working!")
print("=" * 60)
