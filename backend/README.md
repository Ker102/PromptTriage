# PromptTriage Backend (FastAPI + LangChain + Redis)

Python backend for RAG-powered prompt generation with semantic caching.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Backend                       │
├─────────────────────────────────────────────────────────┤
│  RAG Endpoints          │  LangCache Endpoints          │
│  • /api/rag/query       │  • /api/rag/cache             │
│  • /api/rag/ingest      │  • /api/rag/cache/search      │
│  • /api/rag/ingest/batch│                               │
│  • /api/rag/stats       │                               │
├─────────────────────────────────────────────────────────┤
│  LangChain + Redis Vector Store                         │
│  • Sentence-transformers embeddings                     │
│  • Redis Cloud for vector storage                       │
│  • LangCache for semantic response caching              │
└─────────────────────────────────────────────────────────┘
```

## Local Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your Redis Cloud credentials

uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### RAG Operations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rag/query` | POST | Semantic search for similar prompts |
| `/api/rag/ingest` | POST | Add single prompt to vector store |
| `/api/rag/ingest/batch` | POST | Batch add prompts (for datasets) |
| `/api/rag/stats` | GET | Vector store statistics |

### Semantic Caching (LangCache)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/rag/cache` | POST | Cache an LLM response |
| `/api/rag/cache/search` | POST | Search for cached response |

## Cloud Run Deployment

Auto-deploys via Cloud Build on push to `main`.

```bash
# Manual deploy
gcloud run deploy prompttriage-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "REDIS_URL=redis://..."
```

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `REDIS_URL` | Redis Cloud connection URL |
| `LANGCACHE_URL` | *(Optional)* LangCache endpoint |
| `LANGCACHE_API_KEY` | *(Optional)* LangCache API key |
