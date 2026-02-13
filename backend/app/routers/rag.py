"""
RAG (Retrieval Augmented Generation) endpoints.
Uses Pinecone vector store for prompt retrieval.
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
    include_metadata: bool = True
    modality: str = "text"  # text, image, video
    namespace: Optional[str] = None  # Direct namespace override
    target_vendor: Optional[str] = None  # anthropic, openai, google — maps to vendor namespace

# Vendor to Pinecone namespace mapping
VENDOR_NAMESPACE_MAP = {
    "anthropic": "system-prompts-anthropic",
    "openai": "system-prompts-openai",
    "google": "system-prompts-google",
}


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


class IngestRequest(BaseModel):
    """Request model for ingesting new prompts."""
    content: str
    metadata: dict = {}


class BatchIngestRequest(BaseModel):
    """Request model for batch ingestion."""
    documents: List[IngestRequest]


class IngestResponse(BaseModel):
    """Response for ingestion."""
    id: str
    message: str


class BatchIngestResponse(BaseModel):
    """Response for batch ingestion."""
    ids: List[str]
    count: int
    message: str


@router.post("/query", response_model=QueryResponse)
async def query_prompts(request: QueryRequest):
    """
    Query Pinecone for similar prompts.
    
    Supports vendor-specific namespace routing and modality-based defaults.
    """
    try:
        # Resolve namespace: target_vendor takes priority, then explicit namespace, then modality default
        resolved_namespace = request.namespace
        if request.target_vendor and request.target_vendor in VENDOR_NAMESPACE_MAP:
            resolved_namespace = VENDOR_NAMESPACE_MAP[request.target_vendor]

        results = await rag_service.query(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            modality=request.modality,
            namespace=resolved_namespace,
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
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_prompt(request: IngestRequest):
    """Ingest a new prompt to Pinecone."""
    try:
        doc_id = await rag_service.ingest_to_pinecone(
            content=request.content,
            metadata=request.metadata,
        )
        
        return IngestResponse(
            id=doc_id,
            message="Prompt ingested successfully",
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
    """Get RAG system statistics."""
    try:
        stats = await rag_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")
