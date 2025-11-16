"""
Knowledge Base - Search and retrieve articles
vector search.. Falls back to keyword search if needed.
"""
import json
from typing import List, Dict, Optional
from src.vector_store import VectorStore


# Global vector store instance (initialized on first use)
_vector_store = None


def get_vector_store() -> VectorStore:
    """Get or initialize vector store singleton"""
    global _vector_store
    if _vector_store is None:
        try:
            _vector_store = VectorStore()
        except Exception as e:
            print(f"Warning: Could not initialize vector store: {e}")
            _vector_store = None
    return _vector_store


def load_articles() -> List[Dict]:
    """Load articles from JSON file (for keyword search fallback)"""
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


def search_articles_vector(
    query: str,
    category: Optional[str] = None,
    limit: int = 3
) -> List[Dict]:
    """
    Search articles using vector similarity (semantic search)
    
    Args:
        query: Search query (user's question)
        category: Filter by category (billing, technical, usage)
        limit: Maximum number of results
        
    Returns:
        List of matching articles with similarity scores
    """
    vs = get_vector_store()
    
    if vs is None:
        print("Vector search not available, falling back to keyword search")
        return search_articles_keyword(query, category, limit)
    
    try:
        # Use lower threshold for better recall
        results = vs.search(
            query=query,
            category=category,
            limit=limit,
            score_threshold=0.3  # Lower = more lenient
        )
        
        # If no results, try without category filter
        if not results and category:
            print(f"No results in '{category}', searching all categories...")
            results = vs.search(
                query=query,
                category=None,
                limit=limit,
                score_threshold=0.3
            )
        
        return results
        
    except Exception as e:
        print(f"Vector search error: {e}, falling back to keyword search")
        return search_articles_keyword(query, category, limit)


def search_articles_keyword(
    query: str,
    category: Optional[str] = None,
    limit: int = 3
) -> List[Dict]:
    """
    Search articles by keyword matching (FALLBACK)
    
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
    
    # Return top results (convert to same format as vector search)
    formatted_results = []
    for r in results[:limit]:
        article = r['article']
        formatted_results.append({
            'doc_id': article['id'],
            'title': article['title'],
            'content': article['content'],
            'category': article['category'],
            'tags': article.get('tags', []),
            'similarity_score': r['score'] / 20  # Normalize to 0-1 range
        })
    
    return formatted_results


# Main search function (use this in your agent)
def search_articles(
    query: str,
    category: Optional[str] = None,
    limit: int = 3,
    use_vector: bool = True
) -> List[Dict]:
    """
    Search articles (automatically chooses best method)

    Args:
        query: Search query
        category: Filter by category
        limit: Max results
        use_vector: Use vector search if available (default: True)

    Returns:
        List of matching articles
    """
    if use_vector:
        return search_articles_vector(query, category, limit)
    else:
        return search_articles_keyword(query, category, limit)


# Alias for backward compatibility
def search_knowledge_base(
    query: str,
    category: Optional[str] = None,
    top_k: int = 3
) -> List[Dict]:
    """
    Search knowledge base (alias for search_articles)

    Args:
        query: Search query
        category: Filter by category
        top_k: Maximum number of results

    Returns:
        List of matching articles with 'score' field
    """
    results = search_articles(query, category, limit=top_k)
    # Rename similarity_score to score for compatibility
    for result in results:
        result['score'] = result.pop('similarity_score', 0.0)
    return results


if __name__ == "__main__":
    # Test both search methods
    print("=" * 60)
    print("TESTING KNOWLEDGE BASE SEARCH")
    print("=" * 60)
    
    test_queries = [
        ("how to upgrade my plan", None),
        ("project not syncing", "technical"),
        ("invite team members", None),
        ("refund", "billing"),
        ("keyboard shortcuts", "usage")
    ]
    
    for query, category in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        if category:
            print(f"Category: {category}")
        print(f"{'='*60}")
        
        # Vector search
        print("\n🔍 VECTOR SEARCH:")
        vector_results = search_articles_vector(query, category, limit=2)
        if vector_results:
            for i, result in enumerate(vector_results, 1):
                print(f"  {i}. {result['title']}")
                print(f"     Category: {result['category']}")
                print(f"     Score: {result['similarity_score']:.3f}")
        else:
            print("  No results")
        
        # Keyword search (for comparison)
        print("\n📝 KEYWORD SEARCH (comparison):")
        keyword_results = search_articles_keyword(query, category, limit=2)
        if keyword_results:
            for i, result in enumerate(keyword_results, 1):
                print(f"  {i}. {result['title']}")
                print(f"     Category: {result['category']}")
                print(f"     Score: {result['similarity_score']:.3f}")
        else:
            print("  No results")