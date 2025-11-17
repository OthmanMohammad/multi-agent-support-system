"""
Vector Store - Qdrant Cloud client wrapper for semantic search
Uses sentence-transformers for local embeddings (no OpenAI needed)
Uses centralized configuration for Qdrant connection
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType
)
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

from src.core.config import get_settings


class VectorStore:
    """Wrapper for Qdrant Cloud vector database with local embeddings"""
    
    def __init__(
        self, 
        collection_name: str = "kb_articles",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize vector store with Qdrant Cloud
        
        Args:
            collection_name: Qdrant collection name
            embedding_model: sentence-transformers model name
                - all-MiniLM-L6-v2: 384 dim, fast, good quality (RECOMMENDED)
        """
        self.collection_name = collection_name
        
        # Get configuration
        settings = get_settings()
        
        # Connect to Qdrant Cloud
        print(f"Connecting to Qdrant Cloud...")
        self.client = QdrantClient(
            url=settings.qdrant.url,
            api_key=settings.qdrant.api_key,
            timeout=settings.qdrant.timeout
        )
        print("✓ Connected to Qdrant Cloud")
        
        # Load embedding model (downloads ~80MB first time)
        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
        print(f"✓ Model loaded (vector size: {self.vector_size})")
        
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (384-dim for all-MiniLM-L6-v2)
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
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
                
                # Create index for category field (for filtering)
                print("Creating index for category field...")
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="category",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print("✓ Category index created")
            else:
                print(f"✓ Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            print(f"❌ Error creating collection: {e}")
            raise
    
    def upsert_documents(self, documents: List[Dict]):
        """
        Upload documents to Qdrant Cloud
        
        Args:
            documents: List of dicts with keys:
                - id: unique identifier (can be string)
                - embedding: vector (list of floats)
                - title: article title
                - content: article content
                - category: billing/technical/usage/api
                - tags: list of tags
        """
        try:
            points = []
            for i, doc in enumerate(documents):
                point = PointStruct(
                    id=i,  # Use index as integer ID
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
            batch_size = 50  # Smaller batches for cloud
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                print(f"  Uploaded {min(i + len(batch), len(points))}/{len(points)} documents...")
            
            print(f"✓ Uploaded {len(points)} documents to Qdrant Cloud")
            
        except Exception as e:
            print(f"❌ Error uploading documents: {e}")
            raise
    
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Semantic search using query text
        
        Args:
            query: Search query (plain text)
            category: Filter by category (billing, technical, usage, api)
            limit: Max results
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of matched documents with scores
        """
        try:
            # Generate query embedding
            query_vector = self.generate_embedding(query)
            
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
            
            # Search (using query_points instead of deprecated search method)
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            ).points
            
            # Format results
            documents = []
            for hit in results:
                documents.append({
                    "doc_id": hit.payload["doc_id"],
                    "title": hit.payload["title"],
                    "content": hit.payload["content"],
                    "category": hit.payload["category"],
                    "tags": hit.payload.get("tags", []),
                    "similarity_score": round(hit.score, 3)
                })
            
            return documents
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def get_collection_info(self) -> Dict:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vector_size": self.vector_size,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            print(f"❌ Error getting collection info: {e}")
            return {}
    
    def delete_collection(self):
        """Delete the collection (use with caution!)"""
        try:
            self.client.delete_collection(self.collection_name)
            print(f"✓ Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")


if __name__ == "__main__":
    # Test the vector store
    print("=" * 60)
    print("TESTING QDRANT CLOUD CONNECTION")
    print("=" * 60)
    
    try:
        # Initialize (this will test connection)
        vs = VectorStore()
        
        # Create collection
        print("\n1. Creating collection...")
        vs.create_collection(recreate=False)
        
        # Get info
        print("\n2. Collection info:")
        info = vs.get_collection_info()
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        # Test embedding
        print("\n3. Testing embedding generation...")
        test_text = "How do I upgrade my billing plan?"
        embedding = vs.generate_embedding(test_text)
        print(f"   Text: {test_text}")
        print(f"   Embedding dim: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        
        print("\n✓ Qdrant Cloud is working perfectly!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your configuration in Doppler or .env")
        print("2. Verify the URL starts with https://")
        print("3. Make sure API key is correct")
        print("4. Check your cluster is running in Qdrant Cloud dashboard")