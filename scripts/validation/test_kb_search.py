"""
Test Knowledge Base Search

Quick script to test KB search functionality
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.application.kb_article_service import KBArticleService
from src.services.infrastructure.knowledge_base_service import KnowledgeBaseService
from src.utils.logging.setup import setup_logging


async def test_search(query: str, category: str = None):
    """Test KB search"""
    setup_logging()

    kb_service = KnowledgeBaseService()
    kb_article_service = KBArticleService(kb_service)

    print(f"\nQuery: '{query}'")
    if category:
        print(f"Category: {category}")
    print("-" * 60)

    result = await kb_article_service.search_articles(
        query=query,
        category=category,
        limit=5,
        score_threshold=0.3
    )

    if result.is_success:
        articles = result.value
        if articles:
            print(f"Found {len(articles)} results:\n")
            for i, article in enumerate(articles, 1):
                print(f"{i}. {article['title']}")
                print(f"   Category: {article['category']}")
                print(f"   Score: {article['similarity_score']:.3f}")
                print(f"   Content preview: {article['content'][:100]}...")
                print()
        else:
            print("No results found.")
    else:
        print(f"Error: {result.error}")


async def main():
    """Run test queries"""
    print("=" * 60)
    print("KNOWLEDGE BASE SEARCH TEST")
    print("=" * 60)

    test_queries = [
        ("how to upgrade my billing plan", "billing"),
        ("app keeps crashing on my phone", "technical"),
        ("keyboard shortcuts", "usage"),
        ("api authentication", "api"),
        ("invite team members", None),
        ("refund policy", "billing"),
    ]

    for query, category in test_queries:
        await test_search(query, category)

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
    