"""
Vector Store - Qdrant integration for vector database operations
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import os

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store implementation using Qdrant
    """
    
    def __init__(self, client: QdrantClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name
        self.vector_size = 1536  # OpenAI text-embedding-3-small dimension
        
    async def initialize_collection(self) -> bool:
        """Initialize Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = await asyncio.to_thread(self.client.get_collections)
            
            collection_exists = any(
                col.name == self.collection_name 
                for col in collections.collections
            )
            
            if not collection_exists:
                # Create collection
                await asyncio.to_thread(
                    self.client.create_collection,
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {self.collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {e}")
            return False
    
    async def add_vector(
        self, 
        vector_id: str, 
        vector: List[float], 
        payload: Dict[str, Any]
    ) -> bool:
        """
        Add a vector to the collection
        
        Args:
            vector_id: Unique identifier for the vector
            vector: Vector embeddings
            payload: Metadata associated with the vector
            
        Returns:
            Success status
        """
        try:
            point = PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload
            )
            
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Added vector {vector_id} to collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vector {vector_id}: {e}")
            return False
    
    async def add_vectors_batch(
        self, 
        vectors: List[Dict[str, Any]]
    ) -> int:
        """
        Add multiple vectors in batch
        
        Args:
            vectors: List of vector data with id, vector, and payload
            
        Returns:
            Number of successfully added vectors
        """
        try:
            points = []
            for vec_data in vectors:
                point = PointStruct(
                    id=vec_data["id"],
                    vector=vec_data["vector"],
                    payload=vec_data.get("payload", {})
                )
                points.append(point)
            
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} vectors to collection")
            return len(points)
            
        except Exception as e:
            logger.error(f"Batch vector addition failed: {e}")
            return 0
    
    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[models.ScoredPoint]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query vector for similarity search
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            filters: Additional filters for search
            
        Returns:
            List of similar vectors with scores
        """
        try:
            # Build filter conditions
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchAny(any=value)
                            )
                        )
                    else:
                        conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    search_filter = models.Filter(
                        must=conditions
                    )
            
            # Perform search
            results = await asyncio.to_thread(
                self.client.search,
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=threshold,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )
            
            logger.debug(f"Found {len(results)} similar vectors")
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def get_vector(self, vector_id: str) -> Optional[models.Record]:
        """
        Get a specific vector by ID
        
        Args:
            vector_id: Vector identifier
            
        Returns:
            Vector record or None
        """
        try:
            result = await asyncio.to_thread(
                self.client.retrieve,
                collection_name=self.collection_name,
                ids=[vector_id],
                with_payload=True,
                with_vectors=True
            )
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to get vector {vector_id}: {e}")
            return None
    
    async def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector by ID
        
        Args:
            vector_id: Vector identifier
            
        Returns:
            Success status
        """
        try:
            await asyncio.to_thread(
                self.client.delete,
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[vector_id]
                )
            )
            
            logger.debug(f"Deleted vector {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector {vector_id}: {e}")
            return False
    
    async def update_vector_payload(
        self, 
        vector_id: str, 
        payload: Dict[str, Any]
    ) -> bool:
        """
        Update vector payload/metadata
        
        Args:
            vector_id: Vector identifier
            payload: New payload data
            
        Returns:
            Success status
        """
        try:
            await asyncio.to_thread(
                self.client.set_payload,
                collection_name=self.collection_name,
                payload=payload,
                points=[vector_id]
            )
            
            logger.debug(f"Updated payload for vector {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update payload for {vector_id}: {e}")
            return False
    
    async def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """
        Get collection information and statistics
        
        Returns:
            Collection info dictionary
        """
        try:
            info = await asyncio.to_thread(
                self.client.get_collection,
                collection_name=self.collection_name
            )
            
            # Safe vector config access
            vector_config = info.config.params.vectors if info.config and info.config.params else None
            vector_size = 0
            distance = "Unknown"
            
            if vector_config:
                if isinstance(vector_config, dict):
                    # vectors is a dict, get first value
                    first_config = next(iter(vector_config.values()), None)
                    if first_config:
                        vector_size = getattr(first_config, 'size', 0)
                        distance = str(getattr(first_config, 'distance', 'Unknown'))
                else:
                    # vectors is VectorParams object
                    vector_size = getattr(vector_config, 'size', 0)
                    distance = str(getattr(vector_config, 'distance', 'Unknown'))
            
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "config": {
                    "vector_size": vector_size,
                    "distance": distance
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None
    
    async def search_by_text_filter(
        self,
        text_query: str,
        field_name: str = "text",
        limit: int = 10
    ) -> List[models.Record]:
        """
        Search vectors by text content using filtering
        
        Args:
            text_query: Text to search for
            field_name: Field name containing text
            limit: Maximum results
            
        Returns:
            List of matching records
        """
        try:
            # Use scroll to get all points with text filter
            points, _ = await asyncio.to_thread(
                self.client.scroll,
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key=field_name,
                            match=models.MatchText(text=text_query)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            return points
            
        except Exception as e:
            logger.error(f"Text filter search failed: {e}")
            return []
    
    async def count_vectors(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count vectors in collection with optional filters
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            Number of vectors
        """
        try:
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                
                if conditions:
                    search_filter = models.Filter(must=conditions)
            
            result = await asyncio.to_thread(
                self.client.count,
                collection_name=self.collection_name,
                count_filter=search_filter,
                exact=True
            )
            
            return result.count
            
        except Exception as e:
            logger.error(f"Count vectors failed: {e}")
            return 0


async def init_qdrant() -> bool:
    """Initialize Qdrant connection and collections"""
    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "ev_knowledge")
        
        client = QdrantClient(url=qdrant_url)
        vector_store = VectorStore(client, collection_name)
        
        # Test connection
        await asyncio.to_thread(client.get_collections)
        logger.info("Connected to Qdrant successfully")
        
        # Initialize collection
        success = await vector_store.initialize_collection()
        if success:
            logger.info("Qdrant collection initialized")
            return True
        else:
            logger.error("Failed to initialize Qdrant collection")
            return False
            
    except Exception as e:
        logger.error(f"Qdrant initialization failed: {e}")
        return False