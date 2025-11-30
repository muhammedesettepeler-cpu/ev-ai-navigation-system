"""
Qdrant Service - Vector database for semantic search
"""
import logging
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter
import openai

load_dotenv()
logger = logging.getLogger(__name__)

class QdrantService:
    """Qdrant vector database service for semantic search"""
    
    def __init__(self):
        """Initialize Qdrant client and OpenAI for embeddings"""
        
        # Qdrant configuration
        self.qdrant_cloud_url = os.getenv("QDRANT_CLOUD_URL")
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        # Prioritize cloud URL if available
        if self.qdrant_cloud_url:
            self.qdrant_url = self.qdrant_cloud_url
            self.use_cloud = True
        else:
            self.qdrant_url = f"http://{self.qdrant_host}:{self.qdrant_port}"
            self.use_cloud = False
        
        # OpenAI for embeddings
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
        
        # Collection names
        self.knowledge_collection = "ev_knowledge_base"
        self.tips_collection = "ev_tips_and_guides"
        
        # Initialize client
        self.client: Optional[QdrantClient] = None
        self.is_connected = False
        # Connect lazily when needed
        self._connection_attempted = False
    
    def ensure_connection(self):
        """Ensure connection is established"""
        if not self.is_connected and not self._connection_attempted:
            self.connect()

    def connect(self):
        """Connect to Qdrant server"""
        self._connection_attempted = True
        try:
            if self.use_cloud and self.qdrant_cloud_url:
                # Connect to Qdrant Cloud
                self.client = QdrantClient(
                    url=self.qdrant_cloud_url,
                    api_key=self.qdrant_api_key,
                    timeout=15
                )
                logger.info("Trying Qdrant Cloud connection...")
            else:
                # Connect to local Qdrant
                if self.qdrant_api_key:
                    self.client = QdrantClient(
                        host=self.qdrant_host,
                        port=self.qdrant_port,
                        api_key=self.qdrant_api_key,
                        timeout=10
                    )
                else:
                    self.client = QdrantClient(
                        host=self.qdrant_host,
                        port=self.qdrant_port,
                        timeout=10
                    )
                logger.info("Trying local Qdrant connection...")
            
            # Test connection
            collections = self.client.get_collections()
            self.is_connected = True
            connection_type = "Qdrant Cloud" if self.use_cloud else "Local Qdrant"
            logger.info(f"{connection_type} connected: {self.qdrant_url}")
            
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}")
            
            # If cloud failed, try local fallback
            if self.use_cloud:
                logger.info("Trying local Qdrant fallback...")
                try:
                    self.client = QdrantClient(
                        host=self.qdrant_host,
                        port=self.qdrant_port,
                        timeout=10
                    )
                    collections = self.client.get_collections()
                    self.is_connected = True
                    self.use_cloud = False
                    logger.info(f"Local Qdrant fallback connected: http://{self.qdrant_host}:{self.qdrant_port}")
                    return
                except Exception as fallback_error:
                    logger.error(f"Local Qdrant fallback also failed: {fallback_error}")
            
            self.client = None
            self.is_connected = False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get Qdrant connection status"""
        if not self.is_connected or self.client is None:
            return {
                "connected": False,
                "url": self.qdrant_url,
                "type": "Qdrant Cloud" if self.use_cloud else "Local Qdrant",
                "error": "Not connected"
            }
        
        try:
            collections = self.client.get_collections()
            return {
                "connected": True,
                "url": self.qdrant_url,
                "type": "Qdrant Cloud" if self.use_cloud else "Local Qdrant",
                "api_key_configured": bool(self.qdrant_api_key),
                "collections_count": len(collections.collections),
                "collections": [c.name for c in collections.collections]
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            return []
    
    def create_knowledge_collection(self):
        """Create collection for EV knowledge embeddings"""
        if not self.is_connected or self.client is None:
            return False
        
        try:
            collections = self.client.get_collections()
            existing_names = [c.name for c in collections.collections]
            
            if self.knowledge_collection not in existing_names:
                self.client.create_collection(
                    collection_name=self.knowledge_collection,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI text-embedding-3-small dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created knowledge collection: {self.knowledge_collection}")
            else:
                logger.info(f"Knowledge collection exists: {self.knowledge_collection}")
            
            return True
            
        except Exception as e:
            logger.error(f"Knowledge collection creation failed: {e}")
            return False
    
    def create_tips_collection(self):
        """Create collection for EV tips and guides embeddings"""
        if not self.is_connected or self.client is None:
            return False
        
        try:
            collections = self.client.get_collections()
            existing_names = [c.name for c in collections.collections]
            
            if self.tips_collection not in existing_names:
                self.client.create_collection(
                    collection_name=self.tips_collection,
                    vectors_config=VectorParams(
                        size=1536,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created tips collection: {self.tips_collection}")
            else:
                logger.info(f"Tips collection exists: {self.tips_collection}")
            
            return True
            
        except Exception as e:
            logger.error(f"Tips collection creation failed: {e}")
            return False
    
    def index_ev_knowledge(self, knowledge_data: List[Dict[str, Any]]) -> bool:
        """Index EV knowledge base with embeddings"""
        self.ensure_connection()
        if not self.is_connected or self.client is None or not self.create_knowledge_collection():
            return False
        
        try:
            points = []
            
            for i, knowledge in enumerate(knowledge_data):
                # Create embedding from content
                content = knowledge.get('content', '')
                embedding = self.create_embedding(content)
                if not embedding:
                    continue
                
                # Create point
                point = PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "title": knowledge.get('title', ''),
                        "content": content,
                        "category": knowledge.get('category', ''),
                        "tags": knowledge.get('tags', []),
                        "source": knowledge.get('source', 'manual')
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.knowledge_collection,
                points=points
            )
            
            logger.info(f"Indexed {len(points)} knowledge items to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Knowledge indexing failed: {e}")
            return False
    
    def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search for EV knowledge"""
        self.ensure_connection()
        if not self.is_connected or self.client is None:
            return []
        
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.knowledge_collection,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "knowledge": result.payload,
                    "similarity_score": result.score,
                    "relevance": min(100, int(result.score * 100))
                })
            
            logger.info(f"Found {len(results)} knowledge items for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about Qdrant collections"""
        self.ensure_connection()
        if not self.is_connected or self.client is None:
            return {"error": "Not connected"}
        
        try:
            stats = {}
            
            # Knowledge collection stats
            try:
                knowledge_info = self.client.get_collection(self.knowledge_collection)
                stats["knowledge_base"] = {
                    "points_count": knowledge_info.points_count,
                    "vectors_count": knowledge_info.vectors_count,
                    "status": knowledge_info.status
                }
            except:
                stats["knowledge_base"] = {"status": "not_found"}
            
            # Tips collection stats
            try:
                tips_info = self.client.get_collection(self.tips_collection)
                stats["tips_and_guides"] = {
                    "points_count": tips_info.points_count,
                    "vectors_count": tips_info.vectors_count,
                    "status": tips_info.status
                }
            except:
                stats["tips_and_guides"] = {"status": "not_found"}
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def clear_all_collections(self) -> bool:
        """Clear all collections (development only)"""
        if not self.is_connected or self.client is None:
            return False
        
        try:
            collections = self.client.get_collections()
            
            for collection in collections.collections:
                self.client.delete_collection(collection.name)
                logger.warning(f"Deleted collection: {collection.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Collection clearing failed: {e}")
            return False