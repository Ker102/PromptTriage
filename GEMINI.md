# GEMINI.md - PromptTriage Progress Tracker

> This file tracks development progress for PromptTriage enhancements.
> Updated before each commit.

---

## Current Version
`2026-02-phase10-production-polish`

## Project Context
- **Framework**: Next.js 15.1.6 (Frontend) + FastAPI (Backend)
- **AI Model**: Gemini 3 Pro Preview (generation), Gemini 1.5 Flash (fine-tuning)
- **RAG**: Pinecone (Vector Store) with Gemini Embeddings (gemini-embedding-001, 768d)
- **Key Dependencies**: @google/generative-ai, next-auth, Firecrawl, LangChain

---

## Recent Changes

### 2026-02-13 - Phase 10.1: Remove Redis — Pinecone-Only Architecture

**Commit Ready**: Yes

#### Redis & LangCache Removal
- **Backend `rag.py`**: Removed all Redis cache logic (check/write), `add_to_hot_cache()`, LangCache methods (`cache_llm_response`, `get_cached_response`)
- **Backend `config.py`**: Removed 6 settings (`redis_url`, `redis_index_name`, `langcache_url`, `langcache_api_key`, `cache_top_k`, `cache_ttl_seconds`)
- **Backend `rag.py` router**: Removed `/cache` and `/cache/search` endpoints, `use_cache` param, `cache_hit` response field, `storage` field
- **Frontend `rag.ts`**: Removed `use_cache` param, `cache_hit` from response type
- **`requirements.txt`**: Removed `redis>=5.2.0` and `redisvl>=0.3.0`
- **Rationale**: Redis Cloud free tier was dormant, adding 2s timeout per request before fallback. Pinecone-only is simpler and sufficient.

### 2026-02-12 - Phase 9.4b: Research Pause & Documentation

**Commit Ready**: Yes

#### Research Status: ⏸️ PAUSED
- **Reason**: GPU quota = 0 on both GCP and Azure
- **GCP**: `GPUS_ALL_REGIONS` quota increase requested
- **Azure**: $1000 credits available, NCASv3_T4/NCSv3/NCADSA100v4 quota requested
- **Colab Enterprise**: Org policies fixed (domain restriction, internet access)
- **Notebook**: Updated for Qwen3-8B vs Qwen3-235B-A22B MoE size comparison
- **Next**: Resume when GPU quota approved → train 8B → benchmark → 235B

### 2026-02-10 - Phase 9.4: Training Data Generation

**Commit Ready**: Yes

#### Distillation Data Generation
- **60 distillation pairs** generated using `gemini-3-pro-preview` as teacher model
- **100% success rate** — all 60 pairs generated without errors or rate limits
- **Output quality**: Avg 8,107 chars/response (range 4,854 – 14,141 chars)
- **Vendor balanced**: 20 Anthropic, 20 OpenAI, 20 Google pairs
- **Script**: `generate_training_pairs.py` updated to support 3 teacher backends (gemini, gradient, vertex)

#### Combined Training Dataset
- **155 total pairs**: 95 corpus-direct + 60 distillation
- **train.jsonl**: 139 pairs (90%), **val.jsonl**: 16 pairs (10%)
- **Total assistant content**: 998,601 chars, avg 6,443 chars/response
- **Script**: `combine_training_data.py` (combine, validate, split)
- **NOTE**: Training data ONLY — NOT for RAG pipeline or Pinecone

#### Colab Notebook Updates
- Added **Colab Enterprise** support (GCS bucket, A100 GPU via GCP credits)
- Added **train/val split** loading and validation evaluation
- Updated runtime description and data loading options

### 2026-02-09 - Phase 9.3: Research Experiment Framework

**Commit Ready**: Yes

#### Research Framework (`backend/research/`)
- **7 files** created for 3-study benchmark experiment
- **`test_suite.py`**: 30 test prompts across 3 categories (coding, business, creative) × 3 vendors
- **`llm_judge.py`**: LLM-as-judge scoring on 5 dimensions (structure, completeness, vendor fidelity, conciseness, actionability)
- **`rag_methods.py`**: 6 RAG strategies (L0: No RAG → L5: Agentic RAG with query decomposition)
- **`benchmark_runner.py`**: CLI orchestrator for Study A (RAG), Study B (Fine-Tuning), Study C (System Prompt Impact)
- **`generate_training_pairs.py`**: Training data gen for QLoRA (corpus-direct + distillation)
- **Target model**: Qwen 2.5 7B/14B via Google Colab + Unsloth
- **Infrastructure**: Vertex AI (free via GCP credits) for baselines (Claude, Gemini, Llama)

### 2026-01-22 - Phase 9: System Prompts Corpus Enhancement

**Commit Ready**: Yes

#### 9.1 RAG Corpus Enhancement
- **99 prompts** ingested from `system-prompts-reference/` (Ker102/system_prompts_leaks)
- **4 vendor namespaces**: `system-prompts-anthropic` (23), `system-prompts-openai` (42), `system-prompts-google` (13), `system-prompts-misc` (18)
- **Embedding model**: `gemini-embedding-001` with 768-dim output (Pinecone index compat)
- **Script**: `ingest_system_prompts_reference.py` (google.genai SDK)

#### 9.2 Prompt Pattern Analysis
- **106 files** analyzed via `analyze_prompt_patterns.py`
- **Key findings**: Anthropic uses XML (73%), avg 8,021 words; OpenAI uses Markdown (73%), avg 1,435 words
- **Output**: `prompt_patterns.json` with vendor profiles, XML tags, feature frequencies

#### 9.4 Vendor-Specific RAG Context
- **New Component**: `VendorSelector.tsx` — pill-button UI for Any/Anthropic/OpenAI/Google
- **Full pipeline**: `page.tsx` → `analyze/route.ts` → `rag.ts` → FastAPI `rag.py` → Pinecone namespace
- **Vendor conventions**: Injected as `<vendor_style_guide>` context with structure/style recommendations
- **Type update**: `targetVendor` added to `AnalyzeRequestPayload`


### 2026-01-21 - Modality-Specific Prompts & UI Enhancements

**Commit Ready**: Yes

#### Modality-Specific System Prompts

- **9 new prompts** added to `metaprompt.ts`:
  - Video: `VIDEO_ANALYZER_SYSTEM_PROMPT`, `VIDEO_FAST_MODE_SYSTEM_PROMPT`, `VIDEO_REFINER_SYSTEM_PROMPT`
  - Image: `IMAGE_ANALYZER_SYSTEM_PROMPT`, `IMAGE_FAST_MODE_SYSTEM_PROMPT`, `IMAGE_REFINER_SYSTEM_PROMPT`
  - System: `SYSTEM_PROMPT_ANALYZER`, `SYSTEM_PROMPT_FAST_MODE`, `SYSTEM_PROMPT_REFINER`
- **Routing Logic**: `analyze/route.ts` and `refine/route.ts` now select prompts based on modality

#### Desired Final Output Feature

- **New Component**: `DesiredOutputSelector.tsx` - dropdown for Markdown, Code, JSON, XML, etc.
- **UI Integration**: Only visible for Text/System modalities
- **API Integration**: Passes `desiredOutput` to model prompt as `<desired_output_format>` tag

#### Bug Fixes

- **DOM Nesting Error**: Fixed `<p>` inside `<button>` in `ModalitySelector.tsx`
- **Auth Bypass**: Added dev bypass to `refine/route.ts` for unauthenticated testing
- **Missing API Fields**: Added `thinkingMode`, `modality`, `tone`, `outputFormats` to analyze fetch body
- **isPaidPlan**: Now respects `NEXT_PUBLIC_DEV_SUPERUSER` for UI checkboxes

### 2026-01-20 - Video Prompts RAG & Modify Feature
**Commit Ready**: Yes

#### Video Prompts Dataset
- **86 video prompts** ingested to Pinecone `video-prompts` namespace
- **12 negative prompt categories** ingested to `video-negative-prompts` namespace
- Categories: Marketing, hyper-realistic, skin realism, motion artifacts, etc.

#### RAG Modality Routing
- Backend `rag.py`: Routes `modality="video"` → `video-prompts` namespace
- Frontend `rag.ts`: Passes modality parameter to backend
- Frontend `analyze/route.ts`: Includes modality in RAG query

#### Modify Feature (UI)
- **Modify button**: Cyan button next to "Re-write" in results view
- **Input field**: Collapsible textarea for user modification instructions
- **handleModify()**: Refines prompt based on user input while preserving intent

#### Auth Bypass Fix
- Added `ALLOW_DEV_BYPASS=true` to `.env.local`
- Fixed client-side auth check to respect `NEXT_PUBLIC_DEV_SUPERUSER`

### 2026-01-16 - Context7 Integration & Multimodal Input
**Commit Ready**: Yes

#### Context7 Integration
- **Live Docs Lookup**: Integrated Context7 MCP into `/api/analyze/route.ts`
- **Library Detection**: Detects React, Next.js, LangChain, etc. in prompts
- **Dynamic Docs**: Fetches current documentation when libraries detected

#### Multimodal Input (Phase 6)
- **ImageUploader Component**: Drag-drop, preview thumbnails, base64 conversion
- **Conditional Rendering**: Shows uploader only for Image/Video modalities
- **Type Updates**: Added `images` and `modality` to `AnalyzeRequestPayload`

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

---

## Pending Tasks

### Phase 6: New Features Implementation (✅ Complete)
- [x] Output Requirements Selector
- [x] Model Type Selector
- [x] Multimodal Input (Image upload) - ImageUploader component
- [x] Thinking Mode vs Fast Mode - toggle with enhanced deep analysis

### Phase 7: RAG Enhancement (✅ Complete)
- [x] LLM-assisted labeling of system prompts
- [x] Ingest labeled system prompts to Pinecone
- [x] Context7 MCP integration service
- [x] Integrate Context7 into analyze route

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
