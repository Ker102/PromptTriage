# GEMINI.md - PromptTriage Progress Tracker

> This file tracks development progress for PromptTriage enhancements.
> Updated before each commit.

---

## Current Version
`2026-01-rag-enhanced`

## Project Context
- **Framework**: Next.js 15.1.6 (Frontend) + FastAPI (Backend)
- **AI Model**: Gemini 3 Pro Preview (generation), Gemini 1.5 Flash (fine-tuning)
- **RAG**: Hybrid Redis (Hot Cache) + Pinecone (Vector Store) with Gemini Embeddings
- **Key Dependencies**: @google/generative-ai, next-auth, Firecrawl, LangChain

---

## Recent Changes

### 2026-01-12 - RAG Enhancement & UI Features
**Commit Ready**: Yes

#### RAG Enhancement (Phase 7)
- **System Prompts Ingestion**: Labeled and ingested 79 high-quality system prompts (Claude, Cursor, v0, etc.) using Gemini 3 Pro.
- **Context7 Service**: Created `context7.ts` for detecting libraries and fetching live documentation.
- **Pinecone Index**: Populated `system-prompts` namespace with 28,384 vectors.

#### UI Features (Phase 6)
- **Modality Selector**: Replaced generic dropdown with Text/Image/Video tabs.
- **Output Format Selector**: Added multi-select for JSON, Markdown, XML, etc.
- **Dynamic Model Selection**: Curated list of 34+ models across modalities.

### 2026-01-09 - System Prompts Enhancement
**Commit Ready**: Yes

#### Files Modified
- `src/prompts/metaprompt.ts` - Enhanced with Anthropic patterns
- `src/prompts/systemPromptGenerator.ts` - NEW specialized agent

---

## Pending Tasks

### Phase 6: New Features Implementation (In Progress)
- [x] Output Requirements Selector
- [x] Model Type Selector
- [ ] Multimodal Input (Image upload)
- [ ] Thinking Mode vs Fast Mode

### Phase 7: RAG Enhancement (✅ Complete)
- [x] LLM-assisted labeling of system prompts
- [x] Ingest labeled system prompts to Pinecone
- [x] Context7 MCP integration service

### Phase 8: Verification
- [ ] Test prompt generation quality
- [ ] Compare outputs before/after enhancements

---

## Architecture Notes

### Current: Hybrid Next.js + FastAPI
```
promptrefiner-ui/ (Next.js)
├── src/services/
│   ├── rag.ts          # RAG Client
│   └── context7.ts     # Live Docs
```
```
backend/ (FastAPI)
├── app/routers/rag.py  # RAG Endpoints
├── scripts/            # Ingestion Pipelines
│   └── label_and_ingest_prompts.py
```

---

## Commit Log
| Date | Hash | Message | Status |
|------|------|---------|--------|
| 2026-01-12 | `cfe2599` | feat: Add Context7 integration service and fix labeling model | ✅ Done |
| 2026-01-12 | `138eb41` | feat(backend): Add LLM-assisted prompt labeling script | ✅ Done |
| 2026-01-12 | `754e314` | feat(ui): Integrate ModalitySelector into page.tsx | ✅ Done |
| 2026-01-12 | `ab1061d` | feat(ui): Add ModalitySelector component | ✅ Done |
| 2026-01-12 | `334c40d` | feat(ui): Integrate OutputFormatSelector into page and API | ✅ Done |
| 2026-01-12 | `a868cd8` | feat(ui): Add OutputFormatSelector component | ✅ Done |


---

## Notes for Future Sessions
- All analyzed prompts are from 2025 (Claude Code 2.0, Cursor 2025-09-03, etc.)
- Gemini 3 Pro Preview is the recommended generation model
- UI switch for System Prompt Generator mode needs frontend work

---

## Future Enhancements Roadmap

### 1. Model Type Selector (High Priority)
Replace specific model dropdown with **modality selector**:
- **Text Generation** - GPT, Claude, Gemini (current default)
- **Image Generation** - DALL-E, Midjourney, Stable Diffusion, Flux
- **Video Generation** - Runway, Pika, Kling, Sora

Each modality has different prompt engineering patterns.

### 2. Multimodal Input (Image Upload)
Allow users to **attach images** when generating prompts for:
- Image-to-Image models (img2img, inpainting)
- Image-to-Video models (Runway Gen-3, Kling)

The analyzer should **analyze the image** and avoid describing details that the model already sees from the input image.

### 3. Dynamic Evaluation (LangGraph Candidate)
Implement **iterative questioning** when the analyzer detects ambiguity:
```
Analyze → Questions → Evaluate Answers → 
    ↑                        │
    └── Need clarity? ───────┘
```
Trade-off: Higher quality prompts vs. longer generation time.

### 4. Video Generation Prompt Dataset
No good HuggingFace datasets exist. Options:
- **Scrape showcases** (Runway, Pika galleries) with Firecrawl
- **Synthetic generation** - Use existing prompts as examples for GPT-4
- **Community sources** - Reddit r/runwayml, Discord servers

### 5. Fine-tuning Dataset Preparation
Prepare datasets for `gemini-1.5-flash-001-tuning`:
- Format: prompt → refined_prompt pairs
- Include modality-specific examples
- Target: 1000+ high-quality pairs

### 6. Output Format Selector (High Priority)
Allow users to choose output format:
- **Text** - Human-readable formatted prompt (current default)
- **JSON** - Structured JSON prompt for programmatic use

JSON format often works better when prompts are used as input to LLMs (structured data parsing).

Example JSON output:
```json
{
  "role": "system",
  "content": "...",
  "parameters": {
    "style": "photorealistic",
    "negative_prompt": "..."
  }
}
```
