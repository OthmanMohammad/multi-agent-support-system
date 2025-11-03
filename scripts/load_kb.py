"""
Load embedded articles into Qdrant Cloud vector database
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector_store import VectorStore


def load_kb_to_qdrant(
    input_file: str = "data/articles_embedded.json",
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
    
    # Initialize vector store
    print("\n1. Initializing vector store...")
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
        "how to upgrade my plan",
        "project is not syncing",
        "invite team members"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        results = vs.search(query, limit=2)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['title']} (score: {result['similarity_score']})")
    
    print("\n" + "=" * 60)
    print("✓ KNOWLEDGE BASE LOADED TO QDRANT CLOUD!")
    print("=" * 60)
    print("\nYou can view your data at:")
    print("https://cloud.qdrant.io/ → Your cluster → Collections")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load KB to Qdrant Cloud")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection (deletes existing data)"
    )
    args = parser.parse_args()
    
    try:
        load_kb_to_qdrant(recreate=args.recreate)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()