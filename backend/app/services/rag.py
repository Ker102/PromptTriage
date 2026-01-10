"""
Hybrid RAG Service - Gemini Embeddings + Pinecone + Redis Cache

Architecture:
- Gemini: embedding-001 model (768d, high quality)
- Pinecone: Stores all 20,800+ prompts (100K free tier)
- Redis: Caches frequently accessed prompts (~2,000, fits in 30MB)
- LangCache: Semantic caching for LLM responses

Query Flow:
1. Check Redis cache first (fast, <1ms)
2. On miss, query Pinecone (full corpus)
3. Cache top results in Redis for next time
"""

import uuid
import hashlib
import httpx
from typing import Optional, List
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import redis

from app.config import settings


class HybridRAGService:
    """
    Hybrid RAG service using Gemini embeddings + Pinecone + Redis cache.
    
    Gemini: High-quality embeddings (768d)
    Pinecone: Full corpus of all prompts
    Redis: Hot cache for frequently accessed prompts
    """
    
    def __init__(self):
        """Initialize connections."""
        self._pinecone_index = None
        self._redis_client = None
        self._genai_configured = False
    
    def _ensure_genai(self):
        """Ensure Gemini API is configured."""
        if not self._genai_configured and settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self._genai_configured = True
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding using Gemini embedding-001."""
        self._ensure_genai()
        
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        result = genai.embed_content(
            model=settings.embedding_model,
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate query embedding using Gemini."""
        self._ensure_genai()
        
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        result = genai.embed_content(
            model=settings.embedding_model,
            content=text,
            task_type="retrieval_query",
        )
        return result["embedding"]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts using Gemini."""
        self._ensure_genai()
        
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=settings.embedding_model,
                content=text,
                task_type="retrieval_document",
            )
            embeddings.append(result["embedding"])
        return embeddings
    
    @property
    def pinecone_index(self):
        """Get or create Pinecone index."""
        if self._pinecone_index is None:
            if not settings.pinecone_api_key:
                raise ValueError("PINECONE_API_KEY environment variable is required")
            
            pc = Pinecone(api_key=settings.pinecone_api_key)
            
            # Create index if it doesn't exist
            if settings.pinecone_index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=settings.pinecone_index_name,
                    dimension=settings.embedding_dimensions,  # 768 for Gemini
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.pinecone_environment,
                    ),
                )
            
            self._pinecone_index = pc.Index(settings.pinecone_index_name)
        
        return self._pinecone_index
    
    @property
    def redis_client(self):
        """Get Redis client for caching."""
        if self._redis_client is None:
            if settings.redis_url:
                self._redis_client = redis.from_url(settings.redis_url)
        return self._redis_client
    
    def _cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        return f"rag:cache:{hashlib.md5(query.encode()).hexdigest()}"
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[dict]:
        """
        Query for similar prompts using hybrid approach.
        
        1. Check Redis cache first
        2. On miss, query Pinecone
        3. Cache results in Redis
        """
        # Step 1: Check Redis cache
        if use_cache and self.redis_client:
            cache_key = self._cache_key(query)
            cached = self.redis_client.get(cache_key)
            if cached:
                import json
                return json.loads(cached)[:top_k]
        
        # Step 2: Embed query and search Pinecone
        query_embedding = self.embed_query(query)
        
        # Build filter for Pinecone
        filter_dict = {"category": category} if category else None
        
        results = self.pinecone_index.query(
            vector=query_embedding,
            top_k=top_k * 2,  # Get more for caching
            include_metadata=True,
            filter=filter_dict,
        )
        
        # Format results
        formatted = []
        for match in results.matches:
            formatted.append({
                "id": match.id,
                "content": match.metadata.get("content", ""),
                "similarity": match.score,
                "metadata": {k: v for k, v in match.metadata.items() if k != "content"},
            })
        
        # Step 3: Cache in Redis
        if self.redis_client and formatted:
            import json
            cache_key = self._cache_key(query)
            self.redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                json.dumps(formatted),
            )
        
        return formatted[:top_k]
    
    async def ingest_to_pinecone(
        self,
        content: str,
        metadata: dict = None,
    ) -> str:
        """Ingest a single prompt to Pinecone."""
        doc_id = str(uuid.uuid4())
        
        # Generate embedding with Gemini
        embedding = self.embed_text(content)
        
        # Store in Pinecone with content in metadata
        doc_metadata = metadata or {}
        doc_metadata["content"] = content
        
        self.pinecone_index.upsert(
            vectors=[(doc_id, embedding, doc_metadata)]
        )
        
        return doc_id
    
    async def ingest_batch_to_pinecone(
        self,
        documents: List[dict],
        batch_size: int = 100,
    ) -> List[str]:
        """
        Batch ingest prompts to Pinecone.
        Note: Rate-limited by Gemini embedding API.
        """
        doc_ids = []
        vectors = []
        
        for i, doc in enumerate(documents):
            doc_id = str(uuid.uuid4())
            doc_ids.append(doc_id)
            
            # Generate embedding with Gemini
            embedding = self.embed_text(doc["content"])
            
            # Prepare metadata
            metadata = doc.get("metadata", {})
            metadata["content"] = doc["content"]
            
            vectors.append((doc_id, embedding, metadata))
            
            # Batch upsert to Pinecone
            if len(vectors) >= batch_size:
                self.pinecone_index.upsert(vectors=vectors)
                vectors = []
                print(f"  Ingested batch {i // batch_size + 1}")
        
        # Upsert remaining
        if vectors:
            self.pinecone_index.upsert(vectors=vectors)
        
        return doc_ids
    
    async def add_to_hot_cache(
        self,
        doc_id: str,
        content: str,
        metadata: dict = None,
    ) -> bool:
        """Add a prompt to Redis hot cache."""
        if not self.redis_client:
            return False
        
        import json
        key = f"rag:hot:{doc_id}"
        value = json.dumps({
            "id": doc_id,
            "content": content,
            "metadata": metadata or {},
        })
        
        self.redis_client.set(key, value)
        return True
    
    async def get_stats(self) -> dict:
        """Get hybrid RAG statistics."""
        stats = {
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "embedding_provider": "Google Gemini",
            "pinecone": {
                "index_name": settings.pinecone_index_name,
                "connected": bool(settings.pinecone_api_key),
            },
            "redis": {
                "connected": bool(self.redis_client),
                "purpose": "hot_cache",
            },
            "langcache": {
                "enabled": bool(settings.langcache_url),
            },
        }
        
        # Get Pinecone stats
        if settings.pinecone_api_key:
            try:
                index_stats = self.pinecone_index.describe_index_stats()
                stats["pinecone"]["total_vectors"] = index_stats.total_vector_count
            except Exception:
                stats["pinecone"]["total_vectors"] = "unknown"
        
        return stats
    
    # LangCache methods
    async def cache_llm_response(self, prompt: str, response: str) -> bool:
        """Cache an LLM response using LangCache."""
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
                    json={"prompt": prompt, "response": response},
                )
                return result.status_code == 200
        except Exception:
            return False
    
    async def get_cached_response(self, prompt: str, threshold: float = 0.9) -> Optional[str]:
        """Check LangCache for a semantically similar cached response."""
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
                    json={"prompt": prompt, "threshold": threshold},
                )
                
                if result.status_code == 200:
                    data = result.json()
                    if data.get("entries"):
                        return data["entries"][0].get("response")
                return None
        except Exception:
            return None


# Create singleton instance
RAGService = HybridRAGService
