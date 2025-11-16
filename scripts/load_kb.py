"""
Load embedded articles into Qdrant Cloud vector database
Can accept custom input file or use default
"""
import json
import sys
import argparse
import os
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from src.vector_store import VectorStore


def load_kb_to_qdrant(
    input_file: str = "data/all_articles_embedded.json",
    recreate: bool = False
):
    """
    Load KB articles into Qdrant Cloud
    
    Args:
        input_file: Path to embedded articles JSON
        recreate: If True, delete existing collection first
    """
    print("=" * 60)
    print("LOADING KNOWLEDGE BASE TO QDRANT CLOUD")
    print("=" * 60)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found: {input_file}")
        print("\nAvailable files in data/:")
        data_dir = "data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith("_embedded.json"):
                    print(f"  - {os.path.join(data_dir, file)}")
        print("\nRun: python scripts/embed_articles.py --all")
        return
    
    # Initialize vector store
    print(f"\n1. Initializing vector store...")
    vs = VectorStore()
    
    # Create collection
    print("\n2. Creating collection...")
    vs.create_collection(recreate=recreate)
    
    # Load embedded articles
    print(f"\n3. Loading articles from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        articles = data['articles']
    
    print(f"✓ Loaded {len(articles)} articles")
    
    # Show categories
    categories = {}
    for article in articles:
        cat = article['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nArticles by category:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}")
    
    # Upload to Qdrant
    print("\n4. Uploading to Qdrant Cloud...")
    vs.upsert_documents(articles)
    
    # Verify
    print("\n5. Verifying upload...")
    info = vs.get_collection_info()
    print(f"✓ Collection has {info['points_count']} documents")
    
    # Test search
    print("\n6. Testing search...")
    test_queries = [
        ("how to upgrade my plan", "billing"),
        ("project is not syncing", "technical"),
        ("invite team members", "usage"),
        ("api authentication", "api"),
        ("webhook setup", "api")
    ]
    
    print("\n" + "=" * 60)
    print("SEARCH TESTS")
    print("=" * 60)
    
    for query, expected_category in test_queries:
        print(f"\nQuery: '{query}' (expected: {expected_category})")
        results = vs.search(query, limit=2)
        
        if results:
            for i, result in enumerate(results, 1):
                match = "✓" if result['category'] == expected_category else "✗"
                print(f"  {match} {i}. {result['title']}")
                print(f"      Category: {result['category']} | Score: {result['similarity_score']:.2f}")
        else:
            print("  ⚠ No results found")
    
    print("\n" + "=" * 60)
    print("✓ KNOWLEDGE BASE LOADED TO QDRANT CLOUD!")
    print("=" * 60)
    print(f"\nTotal articles: {info['points_count']}")
    print("\nYou can view your data at:")
    print("https://cloud.qdrant.io/ → Your cluster → Collections")
    print("\n✓ System is ready to use!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load KB to Qdrant Cloud")
    parser.add_argument(
        "--input",
        type=str,
        default="data/all_articles_embedded.json",
        help="Input embedded articles JSON file (default: data/all_articles_embedded.json)"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection (deletes existing data)"
    )
    
    args = parser.parse_args()
    
    try:
        load_kb_to_qdrant(input_file=args.input, recreate=args.recreate)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("TROUBLESHOOTING")
        print("=" * 60)
        print("1. Make sure you ran: python scripts/embed_articles.py --all")
        print("2. Check your .env file has QDRANT_URL and QDRANT_API_KEY")
        print("3. Verify Qdrant Cloud cluster is running")
        print("4. Test connection: python src/vector_store.py")