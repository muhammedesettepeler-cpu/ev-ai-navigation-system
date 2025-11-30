"""
RAG System - Retrieval Augmented Generation for EV Navigation
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
import openai
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
from sentence_transformers import SentenceTransformer
import os

from rag.semantic_chunker import SemanticChunker
from rag.vector_store import VectorStore
from models.rag_models import Document, QueryResult

logger = logging.getLogger(__name__)

class RAGSystem:
    """
    Retrieval Augmented Generation System for EV Navigation Knowledge
    """
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"))
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "ev_knowledge")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.vector_store = VectorStore(self.qdrant_client, self.collection_name)
        self.semantic_chunker = SemanticChunker()
        
        # Local embedding model for backup/faster processing
        self.local_embedder = None
        self._init_local_embedder()
    
    def _init_local_embedder(self):
        """Initialize local sentence transformer model"""
        try:
            self.local_embedder = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Local embedder initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize local embedder: {e}")
    
    async def create_embeddings(self, texts: List[str], use_openai: bool = True) -> List[List[float]]:
        """
        Create embeddings for given texts
        
        Args:
            texts: List of text strings
            use_openai: Whether to use OpenAI API or local model
        
        Returns:
            List of embedding vectors
        """
        try:
            if use_openai and self.openai_client:
                response = await asyncio.to_thread(
                    self.openai_client.embeddings.create,
                    input=texts,
                    model=self.embedding_model
                )
                return [embedding.embedding for embedding in response.data]
            
            elif self.local_embedder:
                embeddings = await asyncio.to_thread(
                    self.local_embedder.encode,
                    texts
                )
                return embeddings.tolist()
            
            else:
                raise Exception("No embedding model available")
                
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            raise
    
    async def add_document(self, document: Document) -> str:
        """
        Add a document to the RAG system with semantic chunking
        
        Args:
            document: Document object to add
        
        Returns:
            Document ID
        """
        try:
            # Semantic chunking
            chunks = await self.semantic_chunker.chunk_document(document.content)
            logger.info(f"Document chunked into {len(chunks)} semantic chunks")
            
            # Create embeddings for chunks
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await self.create_embeddings(chunk_texts)
            
            # Store chunks in vector database
            chunk_ids = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{document.id}_chunk_{i}"
                
                # Store in Qdrant
                await self.vector_store.add_vector(
                    vector_id=chunk_id,
                    vector=embedding,
                    payload={
                        "document_id": document.id,
                        "chunk_index": i,
                        "text": chunk.text,
                        "metadata": {
                            **document.metadata,
                            "chunk_type": chunk.chunk_type,
                            "confidence": chunk.confidence
                        }
                    }
                )
                chunk_ids.append(chunk_id)
            
            logger.info(f"Document {document.id} added with {len(chunk_ids)} chunks")
            return document.id
            
        except Exception as e:
            logger.error(f"Failed to add document {document.id}: {e}")
            raise
    
    async def search_similar(
        self, 
        query: str, 
        limit: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[QueryResult]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            threshold: Similarity threshold (0-1)
            filters: Additional filters for search
        
        Returns:
            List of similar documents with scores
        """
        try:
            # Create query embedding
            query_embedding = await self.create_embeddings([query])
            query_vector = query_embedding[0]
            
            # Search in Qdrant
            search_results = await self.vector_store.search_similar(
                query_vector=query_vector,
                limit=limit,
                threshold=threshold,
                filters=filters
            )
            
            # Convert to QueryResult objects
            results = []
            for result in search_results:
                # Safe payload access with None check
                payload = result.payload if result.payload else {}
                query_result = QueryResult(
                    document_id=payload.get("document_id", "unknown"),
                    chunk_text=payload.get("text", ""),
                    score=result.score,
                    metadata=payload.get("metadata", {})
                )
                results.append(query_result)
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:100]}...")
            return results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise
    
    async def generate_response(
        self, 
        query: str, 
        context_documents: List[QueryResult],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response using retrieved context
        
        Args:
            query: User query
            context_documents: Retrieved relevant documents
            system_prompt: System prompt for the AI
        
        Returns:
            Generated response
        """
        try:
            # Prepare context from retrieved documents
            context_texts = []
            for doc in context_documents:
                context_texts.append(f"Context: {doc.chunk_text}")
            
            context = "\n\n".join(context_texts)
            
            # Default system prompt for EV navigation
            if not system_prompt:
                system_prompt = """
                You are an expert AI assistant for electric vehicle navigation. 
                You help users plan optimal routes, find charging stations, and provide 
                advice about electric vehicle travel. Use the provided context to give 
                accurate, helpful, and specific answers. If the context doesn't contain 
                relevant information, say so clearly.
                """
            
            # Generate response using OpenAI
            from typing import cast
            from openai.types.chat import ChatCompletionMessageParam
            
            messages: list[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            generated_text = response.choices[0].message.content
            logger.info(f"Generated response for query: {query[:100]}...")
            
            return generated_text or "No response generated"
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise
    
    async def rag_query(
        self, 
        query: str,
        search_limit: int = 5,
        similarity_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve and generate
        
        Args:
            query: User query
            search_limit: Number of documents to retrieve
            similarity_threshold: Minimum similarity score
            filters: Search filters
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # 1. Retrieve relevant documents
            similar_docs = await self.search_similar(
                query=query,
                limit=search_limit,
                threshold=similarity_threshold,
                filters=filters
            )
            
            # 2. Generate response with context
            if similar_docs:
                response = await self.generate_response(
                    query=query,
                    context_documents=similar_docs
                )
            else:
                response = "I couldn't find relevant information to answer your question. Please try rephrasing or ask about electric vehicle navigation topics."
            
            # 3. Return complete result
            return {
                "response": response,
                "sources": [
                    {
                        "document_id": doc.document_id,
                        "score": doc.score,
                        "text_preview": doc.chunk_text[:200] + "..." if len(doc.chunk_text) > 200 else doc.chunk_text
                    }
                    for doc in similar_docs
                ],
                "query": query,
                "total_sources": len(similar_docs)
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            raise
    
    async def bulk_add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add multiple documents in batch
        
        Args:
            documents: List of documents to add
        
        Returns:
            List of document IDs
        """
        document_ids = []
        for document in documents:
            try:
                doc_id = await self.add_document(document)
                document_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Failed to add document {document.id}: {e}")
        
        logger.info(f"Successfully added {len(document_ids)}/{len(documents)} documents")
        return document_ids