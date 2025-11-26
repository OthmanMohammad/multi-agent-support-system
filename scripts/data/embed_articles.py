"""
Generate embeddings for KB articles using sentence-transformers
Can handle multiple input files
"""
import json
import os
import sys
import argparse
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from src.vector_store import VectorStore
from typing import List, Dict


def prepare_text_for_embedding(article: Dict) -> str:
    """
    Combine article fields for better embeddings
    
    Strategy: title (3x weight) + content + tags
    """
    title = article["title"]
    content = article["content"]
    tags = " ".join(article.get("tags", []))
    
    # Give title more weight by repeating it
    combined = f"{title}. {title}. {title}. {content} Tags: {tags}"
    
    return combined


def load_and_embed_articles(
    input_file: str,
    output_file: str = None
) -> List[Dict]:
    """
    Load articles and generate embeddings
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file (optional)
    
    Returns:
        List of articles with embeddings
    """
    # Initialize vector store (for embedding generation)
    print("Initializing embedding model...")
    vs = VectorStore()
    
    # Load articles
    print(f"\nLoading articles from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        articles = data['articles']
    
    print(f"✓ Loaded {len(articles)} articles")
    
    # Generate embeddings
    print("\nGenerating embeddings...")
    embedded_articles = []
    
    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{len(articles)}] {article['title'][:50]}...")
        
        # Prepare text
        text = prepare_text_for_embedding(article)
        
        # Generate embedding
        embedding = vs.generate_embedding(text)
        
        # Add embedding to article
        embedded_article = article.copy()
        embedded_article["embedding"] = embedding
        embedded_article["doc_id"] = article["id"]
        
        embedded_articles.append(embedded_article)
    
    print(f"\n✓ Generated embeddings for {len(embedded_articles)} articles")
    
    # Save to file if output specified
    if output_file:
        print(f"\nSaving to {output_file}...")
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"articles": embedded_articles}, f, indent=2)
        print(f"✓ Saved embedded articles")
    
    return embedded_articles


def process_all_articles(output_combined: str = "data/all_articles_embedded.json"):
    """
    Process all article files and combine into one
    
    Args:
        output_combined: Path to combined output file
    """
    article_files = [
        "data/articles.json",
        "data/api_articles.json"
    ]
    
    all_embedded = []
    
    for input_file in article_files:
        if os.path.exists(input_file):
            print(f"\n{'='*60}")
            print(f"Processing: {input_file}")
            print(f"{'='*60}")
            
            embedded = load_and_embed_articles(input_file, output_file=None)
            all_embedded.extend(embedded)
        else:
            print(f"⚠ Warning: {input_file} not found, skipping")
    
    if all_embedded:
        print(f"\n{'='*60}")
        print(f"SAVING COMBINED ARTICLES")
        print(f"{'='*60}")
        print(f"Total articles: {len(all_embedded)}")
        print(f"Saving to: {output_combined}")
        
        os.makedirs(os.path.dirname(output_combined) or '.', exist_ok=True)
        with open(output_combined, 'w', encoding='utf-8') as f:
            json.dump({"articles": all_embedded}, f, indent=2)
        
        print(f"✓ Saved combined embedded articles")
        
        return all_embedded
    else:
        print("❌ No articles found to process")
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate embeddings for KB articles")
    parser.add_argument(
        "--input",
        type=str,
        help="Input JSON file (optional, processes all files if not specified)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file (optional, auto-generated if not specified)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all article files and combine"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("EMBEDDING GENERATION FOR KNOWLEDGE BASE")
    print("=" * 60)
    
    try:
        if args.all or (not args.input):
            # Process all files and combine
            print("\nProcessing ALL article files...")
            embedded_articles = process_all_articles()
        else:
            # Process single file
            input_file = args.input
            
            if not args.output:
                # Auto-generate output filename
                base_name = os.path.splitext(input_file)[0]
                output_file = f"{base_name}_embedded.json"
            else:
                output_file = args.output
            
            embedded_articles = load_and_embed_articles(input_file, output_file)
        
        # Show stats
        if embedded_articles:
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Total articles embedded: {len(embedded_articles)}")
            print(f"Embedding dimensions: {len(embedded_articles[0]['embedding'])}")
            print(f"\nCategories:")
            categories = {}
            for article in embedded_articles:
                cat = article['category']
                categories[cat] = categories.get(cat, 0) + 1
            for cat, count in sorted(categories.items()):
                print(f"  - {cat}: {count}")
            
            print("\n✓ Done! Ready to upload to Qdrant Cloud.")
            print("\nNext step: Run 'python scripts/load_kb.py'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()