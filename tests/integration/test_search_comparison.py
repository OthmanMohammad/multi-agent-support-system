"""
Compare keyword search vs vector search quality
"""
import sys
from pathlib import Path

# Add src to path (works for both pytest and direct python execution)
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from knowledge_base import search_articles_keyword, search_articles_vector


def test_search_comparison():
    """Compare keyword vs vector search on various queries"""
    
    test_cases = [
        # (query, expected_category, description)
        ("upgrade my billing plan", "billing", "Straightforward billing query"),
        ("want to pay more money", "billing", "Indirect billing intent"),
        ("sync not working", "technical", "Technical problem"),
        ("data not updating", "technical", "Indirect technical issue"),
        ("invite colleagues", "usage", "Feature usage - synonyms"),
        ("add more users", "usage", "Feature usage - different wording"),
        ("cancel subscription", "billing", "Billing action"),
        ("keyboard tips", "usage", "Feature help - casual language"),
    ]
    
    print("=" * 80)
    print("KEYWORD vs VECTOR SEARCH COMPARISON")
    print("=" * 80)
    
    vector_wins = 0
    keyword_wins = 0
    ties = 0
    
    for query, expected_category, description in test_cases:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"Description: {description}")
        print(f"Expected Category: {expected_category}")
        print(f"{'='*80}")
        
        # Keyword search
        print("\n📝 KEYWORD SEARCH:")
        keyword_results = search_articles_keyword(query, limit=3)
        if keyword_results:
            for i, r in enumerate(keyword_results, 1):
                print(f"  {i}. {r['title']}")
                print(f"     Category: {r['category']} | Score: {r['similarity_score']:.3f}")
            keyword_correct = keyword_results[0]['category'] == expected_category
        else:
            print("  No results")
            keyword_correct = False
        
        # Vector search
        print("\n🔍 VECTOR SEARCH:")
        vector_results = search_articles_vector(query, limit=3)
        if vector_results:
            for i, r in enumerate(vector_results, 1):
                print(f"  {i}. {r['title']}")
                print(f"     Category: {r['category']} | Score: {r['similarity_score']:.3f}")
            vector_correct = vector_results[0]['category'] == expected_category
        else:
            print("  No results")
            vector_correct = False
        
        # Determine winner
        print("\n📊 RESULT:")
        if vector_correct and not keyword_correct:
            print("  ✓ Vector search wins (found correct category)")
            vector_wins += 1
        elif keyword_correct and not vector_correct:
            print("  ✓ Keyword search wins (found correct category)")
            keyword_wins += 1
        elif vector_correct and keyword_correct:
            print("  = Tie (both found correct category)")
            ties += 1
        else:
            print("  ✗ Both missed the correct category")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SCORE")
    print("=" * 80)
    print(f"Vector Search Wins: {vector_wins}")
    print(f"Keyword Search Wins: {keyword_wins}")
    print(f"Ties: {ties}")
    print(f"Total Tests: {len(test_cases)}")
    print(f"\nVector Search Win Rate: {vector_wins/len(test_cases)*100:.1f}%")
    print(f"Keyword Search Win Rate: {keyword_wins/len(test_cases)*100:.1f}%")
    
    if vector_wins > keyword_wins:
        print("\n🏆 Vector search is superior for semantic understanding!")
    elif keyword_wins > vector_wins:
        print("\n🏆 Keyword search performed better on these queries")
    else:
        print("\n🤝 Both methods performed equally well")


if __name__ == "__main__":
    test_search_comparison()