"""
Vector Store - Qdrant client wrapper for semantic search
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    """Wrapper for Qdrant vector database operations"""
    
    def __init__(self, collection_name: str = "kb_articles"):
        self.collection_name = collection_name
        self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.vector_size = 1536  # OpenAI text-embedding-3-large
        
    def create_collection(self, recreate: bool = False):
        """Create collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if exists and recreate:
                print(f"Deleting existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
                exists = False
            
            if not exists:
                print(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print("✓ Collection created successfully")
            else:
                print(f"✓ Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    def upsert_documents(self, documents: List[Dict]):
        """
        Upload documents to Qdrant
        
        Args:
            documents: List of dicts with keys: id, embedding, title, content, category, tags
        """
        try:
            points = []
            for doc in documents:
                point = PointStruct(
                    id=doc["id"],
                    vector=doc["embedding"],
                    payload={
                        "doc_id": doc.get("doc_id", str(doc["id"])),
                        "title": doc["title"],
                        "content": doc["content"],
                        "category": doc["category"],
                        "tags": doc.get("tags", [])
                    }
                )
                points.append(point)
            
            # Upload in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            print(f"✓ Uploaded {len(points)} documents to Qdrant")
            
        except Exception as e:
            print(f"Error uploading documents: {e}")
            raise
    
    def search(
        self,
        query_vector: List[float],
        category: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Semantic search using query vector
        
        Args:
            query_vector: Query embedding (1536-dim)
            category: Filter by category (billing, technical, usage)
            limit: Max results
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matched documents with scores
        """
        try:
            # Build filter if category provided
            query_filter = None
            if category:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="category",
                            match=MatchValue(value=category)
                        )
                    ]
                )
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            documents = []
            for hit in results:
                documents.append({
                    "doc_id": hit.payload["doc_id"],
                    "title": hit.payload["title"],
                    "content": hit.payload["content"],
                    "category": hit.payload["category"],
                    "tags": hit.payload.get("tags", []),
                    "similarity_score": hit.score
                })
            
            return documents
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def get_collection_info(self):
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {}


if __name__ == "__main__":
    # Test the vector store
    print("Testing Vector Store")
    print("=" * 50)
    
    vs = VectorStore()
    
    # Create collection
    vs.create_collection(recreate=False)
    
    # Get info
    info = vs.get_collection_info()
    print(f"\nCollection Info: {info}")