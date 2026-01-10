"""
RAG (Retrieval Augmented Generation) endpoints.
Uses hybrid Redis (cache) + Pinecone (corpus) architecture.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.services.rag import RAGService

router = APIRouter()
rag_service = RAGService()


class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: str
    top_k: int = 5
    category: Optional[str] = None
    use_cache: bool = True
    include_metadata: bool = True


class QueryResult(BaseModel):
    """Single query result."""
    id: str
    content: str
    similarity: float
    metadata: dict


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    results: List[QueryResult]
    query: str
    total_results: int
    cache_hit: bool = False


class IngestRequest(BaseModel):
    """Request model for ingesting new prompts."""
    content: str
    metadata: dict = {}
    add_to_hot_cache: bool = False


class BatchIngestRequest(BaseModel):
    """Request model for batch ingestion."""
    documents: List[IngestRequest]


class IngestResponse(BaseModel):
    """Response for ingestion."""
    id: str
    message: str
    storage: str  # "pinecone" or "redis+pinecone"


class BatchIngestResponse(BaseModel):
    """Response for batch ingestion."""
    ids: List[str]
    count: int
    message: str


class CacheRequest(BaseModel):
    """Request for caching LLM response."""
    prompt: str
    response: str


class CacheSearchRequest(BaseModel):
    """Request for searching cached responses."""
    prompt: str
    threshold: float = 0.9


@router.post("/query", response_model=QueryResponse)
async def query_prompts(request: QueryRequest):
    """
    Query the hybrid RAG system for similar prompts.
    
    Flow:
    1. Check Redis cache (fast)
    2. On miss, query Pinecone (full corpus)
    3. Cache results for next time
    """
    try:
        results = await rag_service.query(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            use_cache=request.use_cache,
        )
        
        return QueryResponse(
            results=[
                QueryResult(
                    id=r["id"],
                    content=r["content"],
                    similarity=r["similarity"],
                    metadata=r.get("metadata", {}) if request.include_metadata else {},
                )
                for r in results
            ],
            query=request.query,
            total_results=len(results),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_prompt(request: IngestRequest):
    """
    Ingest a new prompt to Pinecone.
    Optionally add to Redis hot cache for frequently accessed prompts.
    """
    try:
        doc_id = await rag_service.ingest_to_pinecone(
            content=request.content,
            metadata=request.metadata,
        )
        
        storage = "pinecone"
        
        if request.add_to_hot_cache:
            await rag_service.add_to_hot_cache(
                doc_id=doc_id,
                content=request.content,
                metadata=request.metadata,
            )
            storage = "redis+pinecone"
        
        return IngestResponse(
            id=doc_id,
            message="Prompt ingested successfully",
            storage=storage,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/batch", response_model=BatchIngestResponse)
async def batch_ingest_prompts(request: BatchIngestRequest):
    """
    Batch ingest prompts to Pinecone.
    More efficient than individual ingestion for large datasets.
    """
    try:
        documents = [
            {"content": doc.content, "metadata": doc.metadata}
            for doc in request.documents
        ]
        
        doc_ids = await rag_service.ingest_batch_to_pinecone(documents)
        
        return BatchIngestResponse(
            ids=doc_ids,
            count=len(doc_ids),
            message=f"Successfully ingested {len(doc_ids)} prompts to Pinecone",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch ingestion failed: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get hybrid RAG system statistics."""
    try:
        stats = await rag_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


# LangCache endpoints

@router.post("/cache")
async def cache_response(request: CacheRequest):
    """Cache an LLM response for semantic retrieval via LangCache."""
    try:
        success = await rag_service.cache_llm_response(
            prompt=request.prompt,
            response=request.response,
        )
        
        if success:
            return {"status": "cached", "message": "Response cached in LangCache"}
        else:
            return {"status": "skipped", "message": "LangCache not configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Caching failed: {str(e)}")


@router.post("/cache/search")
async def search_cache(request: CacheSearchRequest):
    """Search LangCache for semantically similar cached response."""
    try:
        cached_response = await rag_service.get_cached_response(
            prompt=request.prompt,
            threshold=request.threshold,
        )
        
        if cached_response:
            return {"hit": True, "response": cached_response}
        else:
            return {"hit": False, "response": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache search failed: {str(e)}")
