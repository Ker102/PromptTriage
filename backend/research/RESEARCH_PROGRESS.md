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

## Study B Phase 2: vs. Proprietary Models ✅ (Completed 2026-03-12)

### Objective
Compare our fine-tuned qwen3_14b against leading proprietary and open-source models at the *same task* using identical 30 test prompts and LLM-as-judge rubric.

### Full 7-Model Leaderboard (210 judgments via Gemini 3.1 Pro LLM-as-Judge)

| Rank | Model | Total /50 | Struct | Compl | Vendor | Conc | Action | Avg Words | Latency | Type |
|------|-------|-----------|--------|-------|--------|------|--------|-----------|---------|------|
| 🥇 1 | **Gemini 3.1 Pro** | **45.7** | 9.5 | 9.6 | 7.9 | 8.7 | 10.0 | 1,280 | 35s | Proprietary |
| 🥈 2 | **Claude Sonnet 4.5** | **44.2** | 9.2 | 9.0 | 7.5 | 8.6 | 9.9 | 1,578 | 62s | Proprietary |
| 🥉 3 | **Qwen3-235B-A22B** | **42.6** | 9.3 | 8.8 | 7.5 | 7.5 | 9.6 | 1,054 | 42s | Open-source MoE |
| 4 | qwen3_14b (ours) | 26.4 | 5.0 | 6.1 | 3.9 | 5.0 | 6.4 | 720 | 71s | Fine-tuned 14B |
| 5 | qwen3_32b | 21.2 | 3.8 | 5.0 | 3.1 | 4.0 | 5.3 | 980 | 170s | Fine-tuned 32B |
| 6 | qwen3_30b_a3b (MoE) | 19.2 | 3.6 | 4.6 | 2.8 | 4.0 | 4.2 | 1,055 | 4,556s | Fine-tuned MoE |
| 7 | qwen3_8b | 16.6 | 3.0 | 4.1 | 2.4 | 3.6 | 3.5 | 2,232 | 231s | Fine-tuned 8B |

### Key Research Findings

1. **18-point gap to proprietary**: Our fine-tuned 14B scores 26.4 vs proprietary range 42-46. The gap is real but explainable — proprietary models have 10-20× more parameters and far more training data.

2. **14B still beats all other fine-tuned models**: Confirms Phase 1 finding — the 14B sweet spot holds. Our best fine-tuned model (26.4) scores 5+ points above the 32B fine-tuned model (21.2).

3. **Vendor fidelity is the weakest dimension across ALL models**: Even proprietary models only score 7.5-7.9/10 on vendor fidelity. Our 14B scores 3.9. This is the highest-impact dimension to improve.

4. **Output length correlates with quality**: Proprietary models average 1,000-1,600 words. Our 14B averages only 720 words. The completeness gap (6.1 vs 9.0+) is partly a length issue.

5. **Actionability nearly maxed by proprietary**: Gemini scores 10.0/10 on actionability. Our 14B scores 6.4. Structured output quality needs work.

6. **Open-source 235B MoE is competitive**: Qwen3-235B-A22B (42.6) is only 2-3 points behind proprietary flagships, showing that scale matters more than vendor-specific training for this task.

### Gap Analysis: How to Close the 18-Point Gap

| Dimension | Our 14B | Proprietary Avg | Gap | Strategy |
|-----------|---------|-----------------|-----|----------|
| Structure | 5.0 | 9.3 | -4.3 | More training data with well-structured examples |
| Completeness | 6.1 | 9.1 | -3.0 | Train on longer outputs, increase min output length |
| Vendor Fidelity | 3.9 | 7.6 | -3.7 | RAG with vendor-specific corpus (Study A) |
| Conciseness | 5.0 | 8.3 | -3.3 | Better training examples, length calibration |
| Actionability | 6.4 | 9.8 | -3.4 | Include more production-grade examples |

**Top 3 strategies to close the gap:**
1. **10× training data** (~1,500+ examples vs current 155) with curated, production-grade system prompts
2. **RAG augmentation** (Study A) to inject vendor-specific conventions at inference time
3. **Output length calibration** — train model to produce 1,000-1,500 word outputs instead of 720

### Cost Breakdown

| Item | Cost |
|------|------|
| Gemini 3.1 Pro generation (30 prompts) | ~$0.30 |
| Claude Sonnet 4.5 generation (30 prompts) | ~$1.20 |
| Qwen3-235B-A22B generation (30 prompts) | ~$0.10 |
| Gemini judge (90 API calls) | ~$2.00 |
| **Total Study B Phase 2** | **~$3.60** |

### Status: ✅ Complete

---

## Study A: RAG Pipeline Comparison (Planned)

### Objective
Determine which RAG strategy (L0-L5) produces the best retrieval context for system prompt generation. Uses qwen3_14b as the fixed generator.

### RAG Levels to Test

| Level | Method | Description |
|-------|--------|-------------|
| L0 | No RAG | Baseline zero-shot (already have from Study B) |
| L1 | Naive RAG | Semantic search via `gemini-embedding-001` from Pinecone |
| L2 | Rerank RAG | L1 + Cross-Encoder reranker for precision |
| L3 | CRAG | Corrective RAG: relevance evaluator + Brave Search web fallback |
| L4 | Judge RAG | L3 + LLM summarization of retrieved docs before injection |
| L5 | Agentic RAG | L4 + Multi-hop query decomposition and reasoning |

### Key Questions
- Does vendor-specific context retrieval (from `system-prompts-anthropic` etc.) improve vendor fidelity scores?
- At what RAG level do returns diminish?
- What is the latency vs. quality tradeoff per level?

### Estimated Cost: ~$10 (API calls, no GPU needed)
### Status: Not started

---

## Study C: The Cascade Effect — Prompt Combinations Matrix (Planned)

### Objective
Prove PromptTriage's real-world value by measuring how different **combinations** of system prompts and task-specific prompts change the *downstream output quality* of production models like GPT-4o.

### The Combinations Matrix

PromptTriage generates both **system prompts** and **task-specific prompts**. Test every combination:

| # | System Prompt | User/Task Prompt | What it proves |
|---|--------------|-----------------|----------------|
| 1 | ❌ None | Vague ("write me a function") | Worst-case baseline |
| 2 | ❌ None | Detailed human-written | Human effort baseline |
| 3 | ❌ None | PromptTriage task prompt | Task prompt value alone |
| 4 | Simple 1-liner | Vague | Minimal system prompt impact |
| 5 | Simple 1-liner | PromptTriage task prompt | Combined minimal |
| 6 | PromptTriage system prompt | Vague | System prompt value alone |
| 7 | PromptTriage system prompt | Detailed human-written | System + human effort |
| 8 | PromptTriage system prompt | PromptTriage task prompt | **Full PromptTriage stack** |
| 9 | Expert-crafted (from corpus) | Vague | Expert ceiling |
| 10 | Expert-crafted (from corpus) | PromptTriage task prompt | Expert + PT task prompt |

### Downstream Tasks
Run each combination on GPT-4o and Claude Sonnet 4, measuring the *actual output quality* (not the prompt quality):
- **Coding**: Generate a REST API endpoint, a React component, a Python data pipeline
- **Writing**: Draft a technical blog post, a product spec, a user story
- **Analysis**: Summarize a research paper, compare two architectures, identify bugs in code

### Key Questions
- How much does the full PromptTriage stack (#8) improve over no prompting (#1)?
- Is the system prompt or task-specific prompt more impactful?
- Does PromptTriage match or exceed expert-crafted prompts (#9)?

### Estimated Cost: ~$25 (10 combos × multiple tasks × 2 models)
### Status: Not started

---

## Study D: The Prompt Delta — Classic Benchmarks (Planned)

### Objective
Quantify exactly **how much difference a prompt makes** on standard AI benchmarks. This is the headline finding for PromptTriage's thesis: "Prompts matter, and better prompts produce measurably better outputs."

### Benchmark Tasks (Industry Standard)

Use the same benchmarks that model providers use for launch announcements:

| Benchmark | Category | What it tests |
|-----------|----------|--------------|
| **HumanEval** | Coding | Function completion (pass@1) |
| **MBPP** | Coding | Basic Python programming |
| **MMLU** (subset) | Knowledge | Multi-task language understanding |
| **GSM8K** | Math | Grade school math word problems |
| **MT-Bench** | Conversation | Multi-turn dialogue quality |
| **IFEval** | Instruction | Instruction following accuracy |

### Conditions to Compare

For each benchmark, run with:
1. **No system prompt** (default)
2. **Simple system prompt** ("You are a helpful assistant")
3. **Task-optimized PromptTriage prompt** (generated specifically for each benchmark type)
4. **Expert chain-of-thought prompt** (hand-crafted for max performance)

### Models to Test On
- GPT-4o, Claude Sonnet 4, Gemini 3.1 Pro, Llama 3.1 70B

### Key Questions
- How many percentage points does a PromptTriage prompt add to standard benchmarks?
- Which benchmark categories benefit most from better prompting?
- Can PromptTriage-generated prompts match hand-crafted expert prompts on standard benchmarks?

### Why This Matters
If PromptTriage adds +5-10% on HumanEval or MMLU, that's a publishable, career-defining finding comparable to what model providers report as generational improvements.

### Estimated Cost: ~$50-100 (many API calls across multiple benchmarks)
### Status: Not started

---

## Study E: Format Wars (Planned)

### Objective
Determine whether prompt format (structure/syntax) genuinely affects model performance, or if it's cargo-culting.

### Formats to Test (Same Semantic Content)

| Format | Structure | Example |
|--------|-----------|---------|
| Plain text | Paragraphs | "You are a coding assistant. Always ask for..." |
| Markdown | Headers + lists | "## Role\n- Coding assistant\n## Rules\n1. Always ask..." |
| XML tags | Anthropic-style | `<identity>Coding assistant</identity><rules>...` |
| JSON schema | Structured data | `{"role": "coding_assistant", "rules": [...]}` |
| Hybrid XML+MD | Mixed | `<identity>## Coding Assistant</identity>` |
| YAML | Config-style | `role: coding_assistant\nrules:\n  - always ask...` |

### Test Matrix
Each format × 3 vendors (Anthropic, OpenAI, Google) × 10 tasks. Score downstream output quality.

### Key Questions
- Do Anthropic models genuinely perform better with XML tags?
- Does JSON format improve structured output tasks?
- Is there a universal "best format" or is it vendor-dependent?

### Estimated Cost: ~$15
### Status: Not started

---

## Study Priority & Sequencing

| Order | Study | Est. Cost | Time | Status |
|-------|-------|-----------|------|--------|
| ~~1~~ | ~~**B Phase 2** (vs Proprietary)~~ | ~~$3.60~~ | ~~2 hrs~~ | ✅ **Done** |
| 2 | **D** (Prompt Delta) | ~$50-100 | 2-3 days | 🔜 Next |
| 3 | **A** (RAG Pipeline) | ~$10 | 1 day | Planned |
| 4 | **C** (Cascade Effect) | ~$25 | 1-2 days | Planned |
| 5 | **E** (Format Wars) | ~$15 | 1 day | Planned |

**Completed research cost so far: ~$192 (Study B: $188 + Phase 2: $3.60)**
**Remaining research budget: ~$100-150**

