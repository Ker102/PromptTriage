"""
RAG Service - Uses LangChain with Redis Vector Store.
Supports semantic caching via Redis LangCache.
"""

import uuid
import httpx
from typing import Optional, List
from langchain_community.vectorstores import Redis
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

from app.config import settings


class RAGService:
    """
    RAG service using LangChain + Redis Vector Store.
    
    Features:
    - Vector storage and similarity search via Redis
    - Semantic caching via LangCache (optional)
    - Sentence-transformers embeddings
    """
    
    def __init__(self):
        """Initialize embeddings and Redis connection."""
        self._embeddings = None
        self._vectorstore = None
        self._langcache_client = None
    
    @property
    def embeddings(self):
        """Lazy initialization of embedding model."""
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embeddings
    
    @property
    def vectorstore(self):
        """Get or create Redis vector store."""
        if self._vectorstore is None:
            if not settings.redis_url:
                raise ValueError("REDIS_URL environment variable is required")
            
            # Try to connect to existing index, create if not exists
            try:
                self._vectorstore = Redis.from_existing_index(
                    embedding=self.embeddings,
                    index_name=settings.redis_index_name,
                    redis_url=settings.redis_url,
                    schema="app/redis_schema.yaml",
                )
            except Exception:
                # Index doesn't exist yet, will be created on first ingest
                self._vectorstore = None
        
        return self._vectorstore
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[dict]:
        """
        Query for similar prompts using Redis vector search.
        
        Args:
            query: The search query text
            top_k: Number of results to return
            category: Optional category filter
            
        Returns:
            List of matching prompts with similarity scores
        """
        if self.vectorstore is None:
            return []
        
        # Build filter if category specified
        filter_dict = {"category": category} if category else None
        
        # Perform similarity search
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=filter_dict,
        )
        
        # Format results
        formatted = []
        for doc, score in results:
            formatted.append({
                "id": doc.metadata.get("id", str(uuid.uuid4())),
                "content": doc.page_content,
                "similarity": 1 - score,  # Convert distance to similarity
                "metadata": doc.metadata,
            })
        
        return formatted
    
    async def ingest(
        self,
        content: str,
        metadata: dict = None,
    ) -> str:
        """
        Ingest a new prompt into Redis vector store.
        
        Args:
            content: The prompt content
            metadata: Optional metadata (category, source, etc.)
            
        Returns:
            The document ID
        """
        if not settings.redis_url:
            raise ValueError("REDIS_URL environment variable is required")
        
        doc_id = str(uuid.uuid4())
        
        # Create document with metadata
        doc_metadata = metadata or {}
        doc_metadata["id"] = doc_id
        
        document = Document(
            page_content=content,
            metadata=doc_metadata,
        )
        
        # Add to Redis
        if self._vectorstore is None:
            # First document - create the index
            self._vectorstore = Redis.from_documents(
                documents=[document],
                embedding=self.embeddings,
                index_name=settings.redis_index_name,
                redis_url=settings.redis_url,
            )
        else:
            # Add to existing index
            self._vectorstore.add_documents([document])
        
        return doc_id
    
    async def ingest_batch(
        self,
        documents: List[dict],
    ) -> List[str]:
        """
        Batch ingest multiple prompts.
        
        Args:
            documents: List of {"content": str, "metadata": dict}
            
        Returns:
            List of document IDs
        """
        if not settings.redis_url:
            raise ValueError("REDIS_URL environment variable is required")
        
        doc_ids = []
        langchain_docs = []
        
        for doc in documents:
            doc_id = str(uuid.uuid4())
            doc_ids.append(doc_id)
            
            metadata = doc.get("metadata", {})
            metadata["id"] = doc_id
            
            langchain_docs.append(Document(
                page_content=doc["content"],
                metadata=metadata,
            ))
        
        # Batch add to Redis
        if self._vectorstore is None:
            self._vectorstore = Redis.from_documents(
                documents=langchain_docs,
                embedding=self.embeddings,
                index_name=settings.redis_index_name,
                redis_url=settings.redis_url,
            )
        else:
            self._vectorstore.add_documents(langchain_docs)
        
        return doc_ids
    
    async def get_stats(self) -> dict:
        """Get Redis vector store statistics."""
        stats = {
            "index_name": settings.redis_index_name,
            "embedding_model": settings.embedding_model,
            "redis_connected": bool(settings.redis_url),
            "langcache_enabled": bool(settings.langcache_url),
        }
        
        # Try to get document count
        if self.vectorstore:
            try:
                # Redis doesn't have a direct count, estimate from info
                stats["status"] = "connected"
            except Exception:
                stats["status"] = "no_index"
        else:
            stats["status"] = "not_initialized"
        
        return stats
    
    async def cache_llm_response(
        self,
        prompt: str,
        response: str,
    ) -> bool:
        """
        Cache an LLM response using LangCache for semantic retrieval.
        
        Args:
            prompt: The input prompt
            response: The LLM response to cache
            
        Returns:
            Success status
        """
        if not settings.langcache_url or not settings.langcache_api_key:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(
                    f"{settings.langcache_url}/v1/caches/default/entries",
                    headers={
                        "Authorization": f"Bearer {settings.langcache_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": prompt,
                        "response": response,
                    },
                )
                return result.status_code == 200
        except Exception:
            return False
    
    async def get_cached_response(
        self,
        prompt: str,
        threshold: float = 0.9,
    ) -> Optional[str]:
        """
        Check LangCache for a semantically similar cached response.
        
        Args:
            prompt: The input prompt to search for
            threshold: Similarity threshold (0-1)
            
        Returns:
            Cached response if found, None otherwise
        """
        if not settings.langcache_url or not settings.langcache_api_key:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                result = await client.post(
                    f"{settings.langcache_url}/v1/caches/default/entries/search",
                    headers={
                        "Authorization": f"Bearer {settings.langcache_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": prompt,
                        "threshold": threshold,
                    },
                )
                
                if result.status_code == 200:
                    data = result.json()
                    if data.get("entries"):
                        return data["entries"][0].get("response")
                
                return None
        except Exception:
            return None
