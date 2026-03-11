# PromptTriage Research Progress

> Persistent log of key findings, statistics, and decisions from each study phase.
> Updated incrementally as studies complete.

---

## Study B: Model Architecture Benchmark ✅ (Completed 2026-03-11)

### Objective
Compare 4 Qwen3 QLoRA fine-tuned models (3 dense + 1 MoE) for system prompt generation quality.

### Final Rankings (120 judgments via Gemini 3.1 Pro LLM-as-Judge)

| Rank | Model | Total /50 | Struct | Compl | Vendor | Conc | Action | Avg Words | Latency |
|------|-------|-----------|--------|-------|--------|------|--------|-----------|---------|
| 🏆 1 | qwen3_14b | 26.4 | 5.0 | 6.1 | 3.9 | 5.0 | 6.4 | 720 | 71s |
| 2 | qwen3_32b | 21.2 | 3.8 | 5.0 | 3.1 | 4.0 | 5.3 | 980 | 170s |
| 3 | qwen3_30b_a3b (MoE) | 19.2 | 3.6 | 4.6 | 2.8 | 4.0 | 4.2 | 1,055 | 4,556s |
| 4 | qwen3_8b | 16.6 | 3.0 | 4.1 | 2.4 | 3.6 | 3.5 | 2,232 | 231s |

### Training Statistics

| Model | Eval Loss | Train Time | QLoRA Params | Early Stopping |
|-------|-----------|------------|--------------|----------------|
| qwen3_8b | 1.6518 | 245s | — | No |
| qwen3_14b | 1.5598 | 408s | — | No |
| qwen3_32b | 1.4838 🏆 | 887s | — | No |
| qwen3_30b_a3b | 3.5432 ⚠️ | 5,616s | 1.6B | Yes (patience=2) |

### Key Research Findings

1. **Eval loss ≠ downstream quality**: 32B had lowest eval loss (1.48) but scored 5.2 points below 14B (21.2 vs 26.4). The 32B memorized training patterns but generalized worse on unseen prompts.

2. **14B is the "sweet spot"**: Best quality (26.4/50), fastest inference (71s), most concise outputs (720 words). Wins every single dimension.

3. **8B lacks capacity**: Produces "runaway generation" — some outputs hit 86K chars / 16K token limit. Insufficient parameter density for conciseness constraints.

4. **MoE overfits catastrophically on small datasets**: 30B total params but only 155 training examples → eval loss diverged to 3.54. Even with early stopping recovery, downstream quality was 4th worst.

5. **Vendor fidelity is universally low** (2.4–3.9/10): 155 training examples insufficient for models to learn vendor-specific formatting conventions (XML for Anthropic, Markdown for OpenAI). This is the weakest dimension and the most promising target for Study A's RAG augmentation.

6. **MoE inference without vLLM is prohibitively slow**: ~76 min/prompt via Unsloth's naive model.generate(). Total benchmark took 38 hours (~$139). Future runs need vLLM (PagedAttention) for 10-20× speedup.

### Cost Breakdown

| Item | Cost |
|------|------|
| Dense model training (4 jobs) | ~$12 |
| Dense benchmark (90 prompts) | ~$15 |
| MoE retrain with early stopping | ~$20 |
| MoE benchmark (38 hrs A100) | ~$139 |
| Gemini judge (120 API calls) | ~$2 |
| **Total Study B** | **~$188** |

### Decision
**qwen3_14b** selected as production model for PromptTriage.

---

## Study A: RAG Pipeline Comparison (Next)

### Objective
Determine which RAG strategy (L0-L5) produces the best retrieval context for system prompt generation, using the qwen3_14b model as the fixed generator.

### RAG Levels to Test

| Level | Method | Description |
|-------|--------|-------------|
| L0 | No RAG | Baseline zero-shot (already benchmarked in Study B) |
| L1 | Naive RAG | Semantic search via gemini-embedding-001 from Pinecone |
| L2 | Rerank RAG | L1 + Cross-Encoder reranker for precision |
| L3 | CRAG | Corrective RAG: relevance evaluator + Brave Search web fallback |
| L4 | Judge RAG | L3 + LLM summarization of retrieved docs before injection |
| L5 | Agentic RAG | L4 + Multi-hop query decomposition and reasoning |

### Key Questions
- Does vendor-specific context retrieval (from `system-prompts-anthropic` etc.) improve vendor fidelity scores?
- At what RAG level do returns diminish?
- What is the latency vs. quality tradeoff per level?

### Status: Not started

---

## Study C: Prompt Complexity Impact (Future)

### Objective
Evaluate how prompt depth/complexity affects output quality — from minimal 1-line prompts to detailed 8K+ word specifications.

### Key Questions
- Does more context in the user prompt reliably improve output quality?
- Is there an optimal prompt length for each category (coding, business, creative)?
- How do different models respond to prompt complexity (do smaller models benefit more from detailed prompts)?

### Status: Not started
