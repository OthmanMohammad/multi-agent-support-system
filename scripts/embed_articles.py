"""
Generate embeddings for KB articles using sentence-transformers
"""
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    input_file: str = "data/articles.json",
    output_file: str = "data/articles_embedded.json"
) -> List[Dict]:
    """
    Load articles and generate embeddings
    
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
    
    # Save to file
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"articles": embedded_articles}, f, indent=2)
    
    print(f"✓ Saved embedded articles")
    
    return embedded_articles


if __name__ == "__main__":
    print("=" * 60)
    print("EMBEDDING GENERATION FOR KNOWLEDGE BASE")
    print("=" * 60)
    
    try:
        # Generate embeddings
        embedded_articles = load_and_embed_articles()
        
        # Show stats
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
        for cat, count in categories.items():
            print(f"  - {cat}: {count}")
        
        print("\n✓ Done! Ready to upload to Qdrant Cloud.")
        print("\nNext step: Run 'python scripts/load_kb.py'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()