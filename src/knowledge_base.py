"""
Knowledge Base - Search and retrieve articles
"""
import json
from typing import List, Dict


def load_articles() -> List[Dict]:
    """Load articles from JSON file"""
    try:
        with open('data/articles.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['articles']
    except FileNotFoundError:
        print("Warning: articles.json not found")
        return []
    except json.JSONDecodeError:
        print("Warning: articles.json is invalid")
        return []


def search_articles(query: str, category: str = None, limit: int = 3) -> List[Dict]:
    """
    Search articles by keyword matching
    
    Args:
        query: Search query (user's question)
        category: Filter by category (billing, technical, usage)
        limit: Maximum number of results
        
    Returns:
        List of matching articles, sorted by relevance
    """
    articles = load_articles()
    
    if not articles:
        return []
    
    # Filter by category if provided
    if category:
        articles = [a for a in articles if a['category'] == category]
    
    # Convert query to lowercase for matching
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Score each article
    results = []
    for article in articles:
        score = 0
        
        # Check title (highest weight)
        if query_lower in article['title'].lower():
            score += 10
        
        # Check content
        if query_lower in article['content'].lower():
            score += 5
        
        # Check tags
        for tag in article['tags']:
            if tag.lower() in query_lower or query_lower in tag.lower():
                score += 3
        
        # Check individual words
        content_lower = (article['title'] + ' ' + article['content']).lower()
        for word in query_words:
            if len(word) > 2 and word in content_lower:  # Skip short words
                score += 1
        
        if score > 0:
            results.append({
                'article': article,
                'score': score
            })
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top results
    return [r['article'] for r in results[:limit]]


if __name__ == "__main__":
    # Test the search function
    print("Testing Knowledge Base Search")
    print("=" * 50)
    
    # Test 1: Search for "create project"
    print("\nTest 1: Search 'create project'")
    results = search_articles("create project")
    for i, article in enumerate(results, 1):
        print(f"{i}. {article['title']} ({article['category']})")
    
    # Test 2: Search for "billing"
    print("\nTest 2: Search 'upgrade plan'")
    results = search_articles("upgrade plan")
    for i, article in enumerate(results, 1):
        print(f"{i}. {article['title']} ({article['category']})")
    
    # Test 3: Search with category filter
    print("\nTest 3: Search 'sync' in technical category")
    results = search_articles("sync", category="technical")
    for i, article in enumerate(results, 1):
        print(f"{i}. {article['title']} ({article['category']})")
    
    # Test 4: No results
    print("\nTest 4: Search 'xyz123' (should be empty)")
    results = search_articles("xyz123")
    print(f"Results: {len(results)}")