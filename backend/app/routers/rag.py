"""
RAG (Retrieval Augmented Generation) endpoints.
Handles prompt retrieval and similarity search.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.rag import RAGService

router = APIRouter()
rag_service = RAGService()


class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    query: str
    top_k: int = 5
    category: Optional[str] = None
    include_metadata: bool = True


class QueryResult(BaseModel):
    """Single query result."""
    id: str
    content: str
    similarity: float
    metadata: dict


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    results: list[QueryResult]
    query: str
    total_results: int


class IngestRequest(BaseModel):
    """Request model for ingesting new prompts."""
    content: str
    metadata: dict = {}


class IngestResponse(BaseModel):
    """Response for ingestion."""
    id: str
    message: str


@router.post("/query", response_model=QueryResponse)
async def query_prompts(request: QueryRequest):
    """
    Query the RAG system for similar prompts.
    
    Returns top-k most similar prompts based on semantic similarity.
    """
    try:
        results = await rag_service.query(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_prompt(request: IngestRequest):
    """
    Ingest a new prompt into the RAG system.
    
    Embeds and stores the prompt for future retrieval.
    """
    try:
        doc_id = await rag_service.ingest(
            content=request.content,
            metadata=request.metadata,
        )
        
        return IngestResponse(
            id=doc_id,
            message="Prompt ingested successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get RAG system statistics."""
    try:
        stats = await rag_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")
