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

## Study B Phase 2: vs. Proprietary Models (Planned)

### Objective
Compare our fine-tuned qwen3_14b against leading proprietary models at the *same task* (system prompt generation) using the exact same 30 test prompts and the same LLM-as-judge rubric from Phase 1.

### Models to Benchmark

| Model | Provider | Cost/call | Notes |
|-------|----------|-----------|-------|
| qwen3_14b (ours) | Local/Azure | ~$0.002 | Fine-tuned, 4-bit QLoRA |
| GPT-4o | OpenAI | ~$0.01 | Current flagship |
| Claude Sonnet 4 | Anthropic | ~$0.01 | Best code model |
| Gemini 3.1 Pro | Google | ~$0.005 | Same family as judge |
| GPT-4o-mini | OpenAI | ~$0.001 | Cost-competitive baseline |

### Methodology
1. Send same 30 test prompts to each proprietary model via API
2. Each generates system prompts for the same user requests
3. Run same Gemini LLM-as-judge (5 dimensions, 0.1 temp)
4. Head-to-head score comparison with qwen3_14b's 26.4/50

### Key Questions
- Does our fine-tuned 14B model outperform proprietary models on any dimension?
- How does vendor fidelity compare (proprietary models should "know" their own conventions)?
- What's the cost-per-quality-point for each approach?

### Estimated Cost: ~$15 (API calls) + ~$5 (judging) = **~$20**
### Status: Not started

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

| Order | Study | Est. Cost | Time | Career/Product Value |
|-------|-------|-----------|------|---------------------|
| 1 | **B Phase 2** (vs Proprietary) | ~$20 | 2-3 hrs | 🟢 Best headline: "14B beats GPT-4o" |
| 2 | **D** (Prompt Delta) | ~$50-100 | 2-3 days | 🟢 Publishable finding, proves thesis |
| 3 | **A** (RAG Pipeline) | ~$10 | 1 day | 🟡 Directly improves product |
| 4 | **C** (Cascade Effect) | ~$25 | 1-2 days | 🟢 Real-world ROI proof |
| 5 | **E** (Format Wars) | ~$15 | 1 day | 🟡 Novel, publishable |

**Total remaining research budget: ~$120-170**
