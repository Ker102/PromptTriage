"""
Health check endpoints for Cloud Run and monitoring.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check():
    """Readiness check - can add DB/service checks here."""
    return {"status": "ready", "services": {"rag": "available"}}
