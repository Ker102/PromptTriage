"""
RAG Service - Handles prompt retrieval and storage.
Uses ChromaDB for vector storage and similarity search.
"""

import uuid
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


class RAGService:
    """
    RAG service for prompt retrieval and storage.
    
    Uses ChromaDB as the vector database with sentence-transformers
    for embedding generation.
    """
    
    def __init__(self):
        """Initialize ChromaDB client and collection."""
        self._client: Optional[chromadb.Client] = None
        self._collection = None
    
    @property
    def client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            self._client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.chroma_persist_dir,
                anonymized_telemetry=False,
            ))
        return self._client
    
    @property
    def collection(self):
        """Get or create the prompts collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="prompts",
                metadata={"description": "Production prompt examples for RAG"},
            )
        return self._collection
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> list[dict]:
        """
        Query for similar prompts.
        
        Args:
            query: The search query text
            top_k: Number of results to return
            category: Optional category filter
            
        Returns:
            List of matching prompts with similarity scores
        """
        where_filter = {"category": category} if category else None
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )
        
        # Format results
        formatted = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "similarity": 1 - (results["distances"][0][i] if results["distances"] else 0),
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })
        
        return formatted
    
    async def ingest(
        self,
        content: str,
        metadata: dict = None,
    ) -> str:
        """
        Ingest a new prompt into the vector store.
        
        Args:
            content: The prompt content
            metadata: Optional metadata (category, source, etc.)
            
        Returns:
            The document ID
        """
        doc_id = str(uuid.uuid4())
        
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {}],
        )
        
        return doc_id
    
    async def get_stats(self) -> dict:
        """Get collection statistics."""
        count = self.collection.count()
        
        return {
            "total_prompts": count,
            "collection_name": "prompts",
            "persist_directory": settings.chroma_persist_dir,
        }
