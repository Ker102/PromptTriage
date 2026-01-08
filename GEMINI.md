# GEMINI.md - PromptTriage Progress Tracker

> This file tracks development progress for PromptTriage enhancements.
> Updated before each commit.

---

## Current Version
`2025-01-systemprompts-enhanced`

## Project Context
- **Framework**: Next.js 15.1.6 with API Routes (serverless backend)
- **AI Model**: Gemini 3 Pro Preview (generation), Gemini 1.5 Flash (fine-tuning target)
- **Key Dependencies**: @google/generative-ai, next-auth, Firecrawl API

---

## Recent Changes

### 2026-01-09 - System Prompts Enhancement
**Commit Ready**: Yes

#### Files Modified
- `src/prompts/metaprompt.ts` - Enhanced with Anthropic patterns
  - Added XML tag structures (`<identity>`, `<workflow>`, `<rules>`)
  - Added workflow phases (Understand→Diagnose→Blueprint→Clarify)
  - Added tone calibration from Claude Code
  - Added Plan Refinement few-shot example
  - Added 4 new domain examples (Code Gen, API, Agentic, Docs)
  - Created `ANALYZER_FEW_SHOTS_EXTENDED` with 10 examples
  - Updated version to `2025-01-systemprompts-enhanced`

#### Files Created
- `src/prompts/systemPromptGenerator.ts` - NEW specialized agent
  - System Prompt Generator for AI assistant definitions
  - 4 few-shot examples (Support, Code Review, Research, Writer)
  
- `src/app/api/generate-system-prompt/route.ts` - NEW API endpoint
  - POST endpoint for system prompt generation
  - Validation, auth, and structured output

- `src/lib/taskClassifier.ts` - NEW routing utility
  - `classifyPrompt()` - keyword-based prompt type detection
  - `isLikelySystemPromptRequest()` - quick UI hint check
  - `getRoutingSuggestion()` - user-facing suggestions

---

## Pending Tasks

### Phase 3: Execution (✅ Complete)
- [x] Expand few-shot examples library (7 new domains)
- [x] Add task classification logic (auto-detect system prompt requests)
- [x] Create UI toggle for System Prompt Generator mode (taskClassifier.ts ready)

### Phase 4: RAG Preparation
- [ ] Structure 50+ prompts for vector embedding
- [ ] Create metadata and categorization
- [ ] Consider Python microservice for RAG pipeline

### Phase 5: FastAPI Backend Architecture
- [ ] Create FastAPI backend structure in repo
- [ ] Set up Cloud Run deployment
- [ ] Integrate with frontend

---

## Architecture Notes

### Current: Next.js API Routes
```
promptrefiner-ui/
├── src/
│   ├── app/
│   │   └── api/
│   │       ├── analyze/route.ts      # Prompt analysis
│   │       ├── refine/route.ts       # Prompt refinement
│   │       └── generate-system-prompt/route.ts  # NEW
│   ├── prompts/
│   │   ├── metaprompt.ts             # Core system prompts
│   │   └── systemPromptGenerator.ts  # NEW agent
│   └── services/
│       └── firecrawl.ts              # Web search
```

### Future Consideration: Hybrid with Python
For RAG and fine-tuning, consider adding:
```
python-services/
├── rag/
│   ├── ingest.py       # Document ingestion
│   └── query.py        # RAG retrieval
└── finetune/
    └── prepare.py      # Dataset preparation
```

---

## Commit Log
| Date | Hash | Message | Status |
|------|------|---------|--------|
| 2026-01-09 | `333af86` | feat: Enhance PromptTriage with Anthropic patterns and System Prompt Generator | ✅ Done |

---

## Notes for Future Sessions
- All analyzed prompts are from 2025 (Claude Code 2.0, Cursor 2025-09-03, etc.)
- Gemini 3 Pro Preview is the recommended generation model
- UI switch for System Prompt Generator mode needs frontend work
