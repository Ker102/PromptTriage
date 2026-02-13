"""
RAG Service - Gemini Embeddings + Pinecone

Architecture:
- Gemini: gemini-embedding-001 model (768d, high quality)
- Pinecone: Stores all 20,800+ prompts across vendor/modality namespaces

Query Flow:
1. Embed query with Gemini
2. Search Pinecone (full corpus, namespace-routed)
3. Return top-K results
"""

import uuid
from typing import Optional, List
from google import genai
from pinecone import Pinecone, ServerlessSpec

from app.config import settings


class RAGService:
    """
    RAG service using Gemini embeddings + Pinecone.
    
    Gemini: High-quality embeddings (768d)
    Pinecone: Full corpus of all prompts, organized by namespace
    """
    
    def __init__(self):
        """Initialize connections."""
        self._pinecone_index = None
        self._genai_client = None
    
    def _get_genai_client(self):
        """Get or create Gemini client."""
        if self._genai_client is None and settings.google_api_key:
            self._genai_client = genai.Client(api_key=settings.google_api_key)
        return self._genai_client
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding using Gemini gemini-embedding-001."""
        client = self._get_genai_client()
        
        if not client:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config={"task_type": "RETRIEVAL_DOCUMENT", "output_dimensionality": settings.embedding_dimensions},
        )
        return result.embeddings[0].values
    
    def embed_query(self, text: str) -> List[float]:
        """Generate query embedding using Gemini."""
        client = self._get_genai_client()
        
        if not client:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config={"task_type": "RETRIEVAL_QUERY", "output_dimensionality": settings.embedding_dimensions},
        )
        return result.embeddings[0].values
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts using Gemini."""
        client = self._get_genai_client()
        
        if not client:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        embeddings = []
        for text in texts:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config={"task_type": "RETRIEVAL_DOCUMENT", "output_dimensionality": settings.embedding_dimensions},
            )
            embeddings.append(result.embeddings[0].values)
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
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        modality: str = "text",
        namespace: Optional[str] = None,
    ) -> List[dict]:
        """
        Query Pinecone for similar prompts.
        
        Namespace logic:
        - If 'namespace' is provided explicitly, use it.
        - Else if modality="video", use "video-prompts".
        - Else use default namespace (None).
        """
        # Determine namespace
        target_namespace = namespace
        if not target_namespace:
            if modality == "video":
                target_namespace = "video-prompts"
        
        # Embed query and search Pinecone
        query_embedding = self.embed_query(query)
        
        # Build filter for Pinecone
        filter_dict = {"category": category} if category else None
        
        # Query Pinecone with namespace
        results = self.pinecone_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
            namespace=target_namespace or ""  # Pinecone uses "" for default
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
    
    async def get_stats(self) -> dict:
        """Get RAG system statistics."""
        stats = {
            "embedding_model": "gemini-embedding-001",
            "embedding_dimensions": settings.embedding_dimensions,
            "embedding_provider": "Google Gemini",
            "pinecone": {
                "index_name": settings.pinecone_index_name,
                "connected": bool(settings.pinecone_api_key),
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
