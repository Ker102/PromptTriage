# Deployment Guide

PromptTriage is a two-service application: **Next.js frontend** + **FastAPI backend**.

---

## Quick Start (Docker Compose)

```bash
# 1. Create env files from examples
cp backend/.env.example backend/.env
cp promptrefiner-ui/.env.local.example promptrefiner-ui/.env.local

# 2. Fill in your API keys in both files

# 3. Build and run
docker-compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ | Gemini API key for embeddings |
| `PINECONE_API_KEY` | ✅ | Pinecone vector database key |
| `PINECONE_INDEX_NAME` | ✅ | Pinecone index name (default: `prompttriage-prompts`) |
| `PINECONE_ENVIRONMENT` | ✅ | Pinecone region (default: `us-east-1`) |
| `FRONTEND_URL` | ❌ | CORS allowed origin (default: `http://localhost:3000`) |

### Frontend (`promptrefiner-ui/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Gemini API key for generation |
| `GOOGLE_CLIENT_ID` | ✅ | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth client secret |
| `NEXTAUTH_SECRET` | ✅ | Random secret for session encryption |
| `NEXTAUTH_URL` | ✅ | Public URL (e.g., `https://prompttriage.dev`) |
| `RAG_API_URL` | ✅ | Backend URL (e.g., `http://backend:8080` in Docker) |
| `FIRECRAWL_API_KEY` | ❌ | Optional web search enrichment |
| `FEEDBACK_WEBHOOK_URL` | ❌ | Optional error report webhook |

---

## GCP Cloud Run

The project includes `cloudbuild.yaml` for the backend. To deploy both services:

### Backend

```bash
# Deploy backend to Cloud Run
gcloud builds submit --config cloudbuild.yaml

# Set env vars
gcloud run services update prompttriage-api \
  --set-env-vars "GOOGLE_API_KEY=xxx,PINECONE_API_KEY=xxx,PINECONE_INDEX_NAME=prompttriage-prompts"
```

### Frontend

```bash
# Build and push frontend image
docker build -t gcr.io/YOUR_PROJECT/prompttriage-web ./promptrefiner-ui
docker push gcr.io/YOUR_PROJECT/prompttriage-web

# Deploy to Cloud Run
gcloud run deploy prompttriage-web \
  --image gcr.io/YOUR_PROJECT/prompttriage-web \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "GEMINI_API_KEY=xxx,RAG_API_URL=https://prompttriage-api-xxxx.run.app,NEXTAUTH_SECRET=xxx,NEXTAUTH_URL=https://your-domain.com"
```

---

## DigitalOcean App Platform

### Option A: App Platform (Recommended)

1. Connect your GitHub repo at [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps)
2. Add two components:
   - **Web Service** → `promptrefiner-ui/` with Dockerfile
   - **Web Service** → `backend/` with Dockerfile
3. Set environment variables for each component
4. Deploy

### Option B: Droplet

```bash
# On your droplet
git clone https://github.com/Ker102/PromptTriage.git
cd PromptTriage

# Set up env files
cp backend/.env.example backend/.env
cp promptrefiner-ui/.env.local.example promptrefiner-ui/.env.local
# Edit both files with your API keys

# Run with Docker Compose
docker-compose up -d --build
```

Configure Nginx or Caddy as a reverse proxy for HTTPS.

---

## Production Checklist

- [ ] Set `NEXTAUTH_URL` to your production domain
- [ ] Configure Google OAuth redirect URI in Google Console
- [ ] Set `FRONTEND_URL` in backend to match your frontend domain
- [ ] Enable HTTPS (Cloud Run handles this; for DO Droplet, use Caddy/Nginx)
- [ ] Set strong `NEXTAUTH_SECRET` (use `openssl rand -base64 32`)
- [ ] Remove `ALLOW_DEV_BYPASS` and `NEXT_PUBLIC_DEV_SUPERUSER` in production
