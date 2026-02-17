# PromptTriage Research Experiment

> "How much do retrieval strategy, model tuning, and system prompt complexity actually matter?"

## 3 Studies

| Study | Question | Variables |
|-------|----------|-----------|
| **A** | Which RAG pipeline + model combo produces the best context? | 6 RAG methods × N models |
| **B** | Dense vs MoE: Where's the breaking point? | 8B→14B→32B dense vs 30B-A3B MoE |
| **C** | Does system prompt complexity help? | 5 prompt levels × best models |

## Study A: RAG Architecture × Model Quality Matrix

Tests 6 RAG strategies with both baseline (Gemini Pro) and fine-tuned models:

| RAG Level | Method | Description |
|-----------|--------|-------------|
| L0 | No RAG | Direct LLM, no retrieval |
| L1 | Naive RAG | Embed → top-K Pinecone |
| L2 | Rerank RAG | L1 + LLM reranker (top-20 → top-3) |
| L3 | CRAG | L2 + relevance check + web fallback |
| L4 | Judge RAG | L3 + LLM grades each doc |
| L5 | Agentic RAG | L4 + query decomposition + reflection |

**Phase 1**: Run with Gemini Pro (baseline)
**Phase 2**: Re-run with best fine-tuned Qwen3 models from Study B

## Study B: Progressive Dense vs MoE Breaking Point

Fine-tune and compare in progressive rounds:

| Round | Dense Model | MoE Model | Question |
|-------|------------|-----------|----------|
| 1 | Qwen3-8B (8B active) | Qwen3-30B-A3B (3B active) | Does 3B active beat 8B dense? |
| 2 | Qwen3-14B (14B active) | Qwen3-30B-A3B (3B active) | What about 14B? |
| 3 | Qwen3-32B (32B active) | Qwen3-30B-A3B (3B active) | Breaking point? |
| Ceiling | — | Qwen3-235B-A22B (no fine-tune) | Upper bound |

**Hardware**: Azure ML `Standard_NC24ads_A100_v4`
**Training**: QLoRA (r=16, 4-bit) via Unsloth, 155 training pairs

## Study C: System Prompt Impact

| Level | Description | ~Words |
|-------|-------------|--------|
| L0 | No system prompt | 0 |
| L1 | Minimal ("You are helpful...") | 10 |
| L2 | Basic (structure + rules) | 50 |
| L3 | Standard (full spec) | 500 |
| L4 | Production Anthropic prompt | 8,000+ |

## Files

| File | Purpose |
|------|---------|
| `test_suite.py` | 30 test prompts (coding, business, creative) |
| `llm_judge.py` | LLM-as-judge scoring (5 dimensions) |
| `rag_methods.py` | 6 RAG strategies (L0-L5) |
| `benchmark_runner.py` | Orchestrator for all 3 studies |
| `generate_training_pairs.py` | Training data for QLoRA |
| `combine_training_data.py` | Merge + split train/val |

## Notebooks (Azure ML)

| Notebook | Study | Purpose |
|----------|-------|---------|
| `study_a_rag_benchmark.ipynb` | A | Run 6 RAG methods × models |
| `study_b_training.ipynb` | B | QLoRA fine-tuning (8B/14B/32B/30B-A3B) |
| `study_b_benchmark.ipynb` | B | Progressive benchmark + ceiling |
| `study_c_prompt_impact.ipynb` | C | Prompt complexity vs quality |

## Evaluation (5 Dimensions, 1-10 each)

1. **Structure** — XML/Markdown hierarchy
2. **Completeness** — All sections present
3. **Vendor Fidelity** — Matches target conventions
4. **Conciseness** — Right-sized for vendor
5. **Actionability** — Production-ready?

## Quick Start

```bash
export GOOGLE_API_KEY=...
export PINECONE_API_KEY=...

# Quick test (3 prompts, Study A only)
cd backend
python -m research.benchmark_runner --study A --prompts 3

# Generate training data
python -m research.generate_training_pairs --approach both --max-pairs 100

# Full benchmark
python -m research.benchmark_runner --study all
```
