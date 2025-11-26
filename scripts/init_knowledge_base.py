"""
Initialize Knowledge Base System

This script:
1. Creates Qdrant collection if it doesn't exist
2. Loads seed articles from JSON
3. Inserts articles into PostgreSQL database
4. Indexes articles in Qdrant for semantic search
5. Verifies the setup

Usage:
    python scripts/init_knowledge_base.py [--reset]

    --reset: Delete existing collection and recreate (WARNING: deletes all KB data)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.application.kb_article_service import KBArticleService
from src.services.infrastructure.knowledge_base_service import KnowledgeBaseService
from src.vector_store import VectorStore
from src.core.config import get_settings
from src.utils.logging.setup import setup_logging, get_logger


def load_seed_data(file_path: str) -> List[Dict]:
    """Load seed articles from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Support multiple formats: {"articles": [...]}, {"records": [...]}, or [...]
    if isinstance(data, list):
        return data
    elif 'articles' in data:
        return data['articles']
    elif 'records' in data:
        return data['records']
    else:
        # Try first key that contains a list
        for key, value in data.items():
            if isinstance(value, list):
                return value
        raise ValueError("Could not find articles array in JSON file")


async def init_knowledge_base(reset: bool = False):
    """
    Initialize the knowledge base system

    Args:
        reset: If True, delete and recreate everything
    """
    setup_logging()
    logger = get_logger(__name__)

    print("=" * 70)
    print("KNOWLEDGE BASE INITIALIZATION")
    print("=" * 70)

    settings = get_settings()

    # Step 1: Initialize Vector Store (Qdrant)
    print("\n[1/5] Initializing Vector Store (Qdrant)...")
    try:
        vector_store = VectorStore()
        print(f"✓ Connected to Qdrant at {settings.qdrant.url}")

        # Create or verify collection
        print(f"\n[2/5] Setting up collection '{vector_store.collection_name}'...")
        vector_store.create_collection(recreate=reset)

        # Get collection info
        info = vector_store.get_collection_info()
        print(f"✓ Collection ready:")
        print(f"  - Name: {info['name']}")
        print(f"  - Vector size: {info['vector_size']}")
        print(f"  - Existing points: {info['points_count']}")

    except Exception as e:
        print(f"✗ Failed to initialize vector store: {e}")
        logger.error("vector_store_init_failed", error=str(e), exc_info=True)
        sys.exit(1)

    # Step 2: Load seed data
    print("\n[3/5] Loading seed articles...")
    seed_file = Path(__file__).parent.parent / "data" / "kb_articles" / "seed_articles.json"

    if not seed_file.exists():
        print(f"✗ Seed file not found: {seed_file}")
        sys.exit(1)

    try:
        articles = load_seed_data(str(seed_file))
        print(f"✓ Loaded {len(articles)} articles from seed data")

        # Show category breakdown
        categories = {}
        for article in articles:
            cat = article['category']
            categories[cat] = categories.get(cat, 0) + 1

        print("\n  Category breakdown:")
        for cat, count in sorted(categories.items()):
            print(f"    - {cat}: {count} articles")

    except Exception as e:
        print(f"✗ Failed to load seed data: {e}")
        sys.exit(1)

    # Step 3: Initialize services
    print("\n[4/5] Initializing application services...")
    try:
        kb_infra_service = KnowledgeBaseService()
        kb_article_service = KBArticleService(kb_infra_service)

        print("✓ Services initialized")

    except Exception as e:
        print(f"✗ Failed to initialize services: {e}")
        logger.error("service_init_failed", error=str(e), exc_info=True)
        sys.exit(1)

    # Step 4: Import articles
    print("\n[5/5] Importing articles into database and vector store...")
    print("  This may take a few minutes...\n")

    try:
        result = await kb_article_service.bulk_import_articles(articles)

        if result.is_success:
            stats = result.value
            print(f"✓ Import completed:")
            print(f"  - Total: {stats['total']}")
            print(f"  - Success: {stats['success_count']}")
            print(f"  - Failures: {stats['failure_count']}")

            if stats['failure_count'] > 0:
                print(f"\n  Errors (first 10):")
                for error in stats['errors']:
                    print(f"    - Index {error['index']}: {error['title']}")
                    print(f"      Error: {error['error']}")
        else:
            print(f"✗ Import failed: {result.error}")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Import failed with exception: {e}")
        logger.error("import_failed", error=str(e), exc_info=True)
        sys.exit(1)

    # Step 5: Verify setup
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # Test vector search
    print("\n[Test 1] Testing vector search...")
    test_query = "how do I upgrade my plan?"

    try:
        search_result = await kb_article_service.search_articles(
            query=test_query,
            limit=3
        )

        if search_result.is_success and len(search_result.value) > 0:
            print(f"✓ Vector search working! Query: '{test_query}'")
            print(f"  Found {len(search_result.value)} results:")
            for i, article in enumerate(search_result.value[:3], 1):
                print(f"    {i}. {article['title']} (score: {article['similarity_score']:.3f})")
        else:
            print("⚠ Vector search returned no results (may need data)")

    except Exception as e:
        print(f"✗ Vector search test failed: {e}")

    # Test category search
    print("\n[Test 2] Testing category filter...")
    try:
        search_result = await kb_article_service.search_articles(
            query="payment issues",
            category="billing",
            limit=2
        )

        if search_result.is_success:
            print(f"✓ Category search working! Found {len(search_result.value)} billing articles")
            for article in search_result.value:
                print(f"    - {article['title']}")
        else:
            print(f"⚠ Category search returned no results")

    except Exception as e:
        print(f"✗ Category search test failed: {e}")

    # Get collection stats
    print("\n[Test 3] Final collection stats...")
    try:
        info_result = await kb_infra_service.get_collection_info()
        if info_result.is_success:
            info = info_result.value
            print(f"✓ Qdrant collection status:")
            print(f"    - Total vectors: {info['points_count']}")
            print(f"    - Status: {info['status']}")
        else:
            print(f"⚠ Could not get collection info")
    except Exception as e:
        print(f"✗ Collection info failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("INITIALIZATION COMPLETE!")
    print("=" * 70)
    print(f"\n✓ Knowledge base is ready with {stats['success_count']} articles")
    print(f"✓ Vector search is operational")
    print(f"✓ Agents can now search and recommend articles\n")

    print("Next steps:")
    print("  1. Test the API: python scripts/test_kb_search.py")
    print("  2. Run the app: python -m uvicorn src.api.main:app --reload")
    print("  3. Add more articles: Use KBArticleService.create_article()")
    print("\nFor management:")
    print("  - View articles in database: kb_articles table")
    print("  - Qdrant dashboard: " + settings.qdrant.url)
    print("  - Resync vector store: python scripts/init_knowledge_base.py --reset")
    print()


async def reset_knowledge_base():
    """Completely reset the knowledge base (WARNING: Destructive)"""
    print("\n" + "!" * 70)
    print("WARNING: This will DELETE all existing KB articles and vectors!")
    print("!" * 70)

    response = input("\nType 'YES' to confirm deletion: ")
    if response != "YES":
        print("Cancelled.")
        sys.exit(0)

    print("\nProceeding with reset...\n")
    await init_knowledge_base(reset=True)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Initialize Knowledge Base system"
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Delete and recreate collection (WARNING: Deletes all data)'
    )

    args = parser.parse_args()

    if args.reset:
        asyncio.run(reset_knowledge_base())
    else:
        asyncio.run(init_knowledge_base(reset=False))


if __name__ == "__main__":
    main()