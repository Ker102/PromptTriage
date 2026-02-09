# PromptTriage Research Experiment

> "How much do retrieval strategy, model tuning, and system prompt complexity actually matter?"

## 3 Studies

| Study | Script | Question |
|-------|--------|----------|
| **A** | `benchmark_runner.py --study A` | Which RAG method produces best context? |
| **B** | `benchmark_runner.py --study B` | Can QLoRA Qwen3-30B-A3B match GPT-5.2? |
| **C** | `benchmark_runner.py --study C` | Does a complex system prompt help? |

## Files

| File | Purpose |
|------|---------|
| `test_suite.py` | 30 test prompts (coding, business, creative) |
| `llm_judge.py` | LLM-as-judge scoring (5 dimensions, Gemini 3 Pro) |
| `rag_methods.py` | 6 RAG strategies (L0-L5) |
| `benchmark_runner.py` | Orchestrator for all 3 studies |
| `generate_training_pairs.py` | Training data for QLoRA (corpus + distillation) |

## Quick Start

```bash
# Set env vars
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

## Evaluation Dimensions (1-10 each)

1. **Structure** — XML/Markdown hierarchy
2. **Completeness** — All sections present
3. **Vendor Fidelity** — Matches target conventions
4. **Conciseness** — Right-sized for vendor
5. **Actionability** — Production-ready?
