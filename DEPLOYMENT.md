# PromptTriage — GCP Cloud Run Deployment Guide

> Deploy both frontend and backend to Cloud Run with custom subdomains on `kaelux.dev`.

---

## Prerequisites

1. [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed (`gcloud`)
2. A GCP project with billing enabled
3. Docker installed locally (for testing)
4. DNS access for `kaelux.dev`

---

## One-Time GCP Setup

```bash
# Set your project
export PROJECT_ID=your-gcp-project-id
export REGION=europe-west1   # or us-central1, etc.

gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

# Create Artifact Registry repo for Docker images
gcloud artifacts repositories create prompttriage \
  --repository-format=docker \
  --location=$REGION
```

---

## Deploy Backend (FastAPI)

```bash
# From repo root
cd backend

# Build & push via Cloud Build
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/prompttriage/api:latest

# Deploy to Cloud Run
gcloud run deploy prompttriage-api \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/prompttriage/api:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "PINECONE_API_KEY=<your-key>" \
  --set-env-vars "PINECONE_INDEX_NAME=system-prompts" \
  --set-env-vars "GOOGLE_GEMINI_API_KEY=<your-key>" \
  --set-env-vars "FRONTEND_URL=https://prompttriage.kaelux.dev"
```

> **Tip**: Use `gcloud run services update` to change env vars without redeploying the image.

---

## Deploy Frontend (Next.js)

```bash
# From repo root
cd promptrefiner-ui

# Build & push — Supabase keys needed at build time (NEXT_PUBLIC_*)
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/prompttriage/ui:latest \
  --build-arg NEXT_PUBLIC_SUPABASE_URL=https://drayjtbfdtadsbtwitls.supabase.co \
  --build-arg NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<your-publishable-key>

# Deploy to Cloud Run
gcloud run deploy prompttriage-ui \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/prompttriage/ui:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars "GOOGLE_GEMINI_API_KEY=<your-key>" \
  --set-env-vars "SUPABASE_SECRET_KEY=<your-secret-key>" \
  --set-env-vars "RAG_API_URL=https://api.prompttriage.kaelux.dev"
```

---

## Custom Domain Setup

### 1. Map domains in Cloud Run

```bash
# Frontend
gcloud run domain-mappings create \
  --service prompttriage-ui \
  --domain prompttriage.kaelux.dev \
  --region $REGION

# Backend API
gcloud run domain-mappings create \
  --service prompttriage-api \
  --domain api.prompttriage.kaelux.dev \
  --region $REGION
```

### 2. Add DNS records

Cloud Run will give you the CNAME target. Add these in your DNS provider:

| Type | Name | Value |
|------|------|-------|
| CNAME | `prompttriage` | `ghs.googlehosted.com` |
| CNAME | `api.prompttriage` | `ghs.googlehosted.com` |

SSL certificates are provisioned automatically by Google (takes ~15 min).

---

## Supabase Configuration

Add these to **Auth → URL Configuration → Redirect URLs**:

```
https://prompttriage.kaelux.dev/**
http://localhost:8081/**
http://localhost:3000/**
```

Set **Site URL** to: `https://prompttriage.kaelux.dev`

---

## Environment Variables Reference

### Frontend (`prompttriage-ui`)

| Variable | Build/Runtime | Description |
|----------|---------------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | **Build** | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | **Build** | Supabase publishable (anon) key |
| `SUPABASE_SECRET_KEY` | Runtime | Supabase secret key (server only) |
| `GOOGLE_GEMINI_API_KEY` | Runtime | Gemini API key |
| `RAG_API_URL` | Runtime | Backend URL (`https://api.prompttriage.kaelux.dev`) |
| `FIRECRAWL_API_KEY` | Runtime | Optional — for web search feature |

### Backend (`prompttriage-api`)

| Variable | Description |
|----------|-------------|
| `GOOGLE_GEMINI_API_KEY` | Gemini API key |
| `PINECONE_API_KEY` | Pinecone vector store key |
| `PINECONE_INDEX_NAME` | Pinecone index name (`system-prompts`) |
| `FRONTEND_URL` | Frontend URL (for CORS) |

---

## CI/CD (Optional — GitHub Auto-Deploy)

To auto-deploy on `git push`, connect Cloud Run to your GitHub repo:

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Select a service → **Edit & Deploy** → **Continuous Deployment**
3. Connect your GitHub repo
4. Set the **Dockerfile path** and **build context**
5. Every push to `main` triggers a new deployment

---

## Migrating to Another Provider

Since both services are standard Docker containers, migration is simple:

```bash
# DigitalOcean App Platform
doctl apps create --spec .do/app.yaml

# Azure Container Apps
az containerapp up --name prompttriage-api --image <img> --env-vars "..."

# AWS App Runner
aws apprunner create-service --service-name prompttriage-api --source-configuration ...
```

Same Docker images, different deploy command.
