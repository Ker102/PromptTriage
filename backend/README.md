# PromptTriage Backend (FastAPI)

Python backend for RAG-powered prompt generation and heavy ML processing.

## Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI application
│   ├── config.py         # Environment config
│   ├── routers/
│   │   ├── rag.py        # RAG query endpoints
│   │   └── health.py     # Health check
│   └── services/
│       ├── embeddings.py # Vector operations
│       └── rag.py        # RAG pipeline
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Local Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Cloud Run Deployment

Deployed via Cloud Build trigger on push to `main`.

```bash
# Manual deploy
gcloud run deploy prompttriage-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment Variables

See `.env.example` for required variables.
