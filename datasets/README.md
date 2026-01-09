# Prompt Datasets for RAG

This directory contains prompt datasets for the PromptTriage RAG system.

## Datasets

| Directory | Source | Rows | Schema |
|-----------|--------|------|--------|
| `ads_corporate/` | HuggingFace | 10,000 | `prompts` (string) |
| `photorealistic/` | HuggingFace | 10,000 | `prompts` (string) |
| `categorized/` | HuggingFace | 800 | `category`, `subcategory`, `prompt`, `tags` |

**Total: ~20,800 image generation prompts**

## Categories (categorized dataset)

- people, animals, food, objects, vehicles, architecture, places
- 32 subcategories including: portrait, beach, cityscape, futuristic building, etc.

## Ingestion

Use the ingestion script to load into Redis:

```bash
cd backend
python scripts/ingest_datasets.py
```

Or via API:
```bash
curl -X POST http://localhost:8000/api/rag/ingest/batch \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"content": "...", "metadata": {"category": "..."}}]}'
```
