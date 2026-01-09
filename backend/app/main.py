"""
PromptTriage Backend - FastAPI Application
Provides RAG-powered prompt generation and processing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, rag

app = FastAPI(
    title="PromptTriage API",
    description="RAG-powered prompt generation backend",
    version="1.0.0",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "https://prompttriage.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "PromptTriage API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
