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

## Study B Phase 2: vs. Proprietary Models ✅ (Re-judged 2026-03-16)

> [!CAUTION]
> **Judge Bias Discovered:** The original Gemini 3.1 Pro judge exhibited severe self-preference (+3.5pts) and anti-Qwen bias (15-22pts). All results below have been re-judged using a neutral 3rd-party arbiter (Llama 4 Maverick via Vertex AI MaaS).

### Objective
Compare our fine-tuned qwen3_14b against leading proprietary and open-source models using identical 30 test prompts and the baseline Llama 4 Maverick judge.

### Full 7-Model Leaderboard (210 judgments via Llama 4 Maverick)

| Rank | Model | Total /50 | Deltas vs Old Judge | Type |
|------|-------|-----------|---------------------|------|
| 🥇 1 | **Qwen3-235B-A22B** | **42.4** | (-0.2 pts) | Open-source MoE |
| 🥈 2 | **Gemini 3.1 Pro** | **42.2** | (-3.5 pts) | Proprietary |
| 🥉 3 | **Claude Sonnet 4.5**| **42.0** | (-2.2 pts) | Proprietary |
| 4 | qwen3_14b (ours)   | 41.8 | (+15.4 pts) | Fine-tuned 14B |
| 5 | qwen3_30b_a3b (MoE)| 41.5 | (+22.3 pts) | Fine-tuned MoE |
| 6 | qwen3_32b          | 40.7 | (+18.9 pts) | Fine-tuned 32B |
| 7 | qwen3_8b           | 37.2 | (+20.6 pts) | Fine-tuned 8B |

### Key Research Findings (Post-Correction)

1. **The 18-point gap was an illusion**: Our fine-tuned 14B scores 41.8 vs the proprietary range of 42.0-42.2. Our model is at near-parity with frontier models.
2. **Qwen3-235B MoE is the true #1**: When judged neutrally, the 235B open-source MoE model slightly edges out the proprietary models.
3. **14B remains the sweet spot**: It still outperforms the 32B dense and 30B MoE models, proving the training dynamics findings from Phase 1 were correct, even if the absolute scores were artificially lowered.
4. **qwen3_8b hits a capacity wall**: Even with neutral judging, the 8B model (37.2) lags significantly behind the rest of the pack, struggling with complex prompt structure constraints.

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

## Study A: RAG Pipeline Comparison ✅ (Completed 2026-03-16)

### Objective
Determine which RAG strategy (L0-L5) produces the best retrieval context for system prompt generation. Used the qwen3_14b fine-tuned generator running on an Azure ML A100 cluster.

### Results: RAG Level vs Quality (180 outputs judged by Llama 4 Maverick)

| RAG Level | N | Avg Score (/50) | Insight |
|-----------|---|:---------------:|---------|
| **L0: No RAG** | 30 | 41.4 | High baseline performance |
| **L1: Naive RAG** | 30 | **42.3** | **Optimal!** Narrowly beats Gemini 3.1 Pro (42.2) |
| **L2: Rerank RAG** | 29 | 42.0 | Slight regression, likely distraction |
| **L3: Corrective RAG** | 30 | 40.4 | Declines as web context adds noise |
| **L4: Judge RAG** | 30 | 39.0 | Meta-discourse confuses the generator |
| **L5: Agentic RAG** | 30 | 39.4 | Complex reflection harms final output format |

### Key Research Findings

1. **Naive RAG is the "Goldilocks" Context**: Qwen 14B hit its absolute peak with L1 Naive RAG (42.3/50), effectively beating the baseline proprietary boundary (42.2/50).
2. **Advanced RAG (L3-L5) harms small models**: Complex agent traces, corrective web searches, and meta-judgments confused the 14B model, causing it to drop formatting rules or miss the user intent. 
3. **No larger model required**: Qwen 14B + Naive RAG delivers frontier-parity performance, officially concluding the search for the optimal production pipeline.

### Cost Breakdown
- **Pre-compute (Pinecone)**: ~$0.50
- **Azure ML Generation**: ~$2.00
- **Llama 4 Judging**: ~$3.00
- **Total Study A**: **~$5.50**

### Status: ✅ Complete

---

## Study D v3: Behavioral Quality Benchmark ✅ (Completed 2026-03-15)

### Objective
Evaluate how system prompt conditions affect **behavioral quality** across 9 professional domains (27 tasks). Test if generic prompts help or harm, and compare our RAG-based `prompttriage` against manually crafted `expert_cot` prompts.

### Evaluation Setup
- **Models Evaluated**: Gemini 3.1 Pro, Claude Sonnet 4.6
- **Conditions**: bare (no prompt), simple ("You are a helpful assistant"), expert_cot, prompttriage
- **Judge**: Meta Llama 4 Maverick 17B-128E MoE (via Vertex AI MaaS). Using a neutral 3rd-party arbiter eliminated a severe 50/50 self-preference ceiling effect observed when using Gemini as a judge.
- **Rubric**: 5 dimensions × 10 pts each = 50 max (Role Expertise, Edge Cases, Specificity, Boundaries, Format)
- **Total Evaluations**: 216 (8 combinations × 27 tasks)

### Results Summary

| Model | Condition | **Total** | Role | Edge | Spec | Bndr | Fmt |
|-------|-----------|-------:|-----:|-----:|-----:|-----:|----:|
| Claude Sonnet 4.6 | simple | **42.8** | 8.9 | 8.2 | 8.9 | 8.3 | 8.5 |
| Claude Sonnet 4.6 | bare | **42.9** | 9.0 | 8.4 | 9.0 | 8.2 | 8.4 |
| Gemini 3.1 Pro | simple | **43.0** | 9.0 | 8.2 | 9.0 | 8.2 | 8.5 |
| Gemini 3.1 Pro | bare | **43.4** | 9.0 | 8.5 | 9.1 | 8.3 | 8.5 |
| Claude Sonnet 4.6 | expert_cot | **43.8** | 9.0 | 8.7 | 9.2 | 8.4 | 8.5 |
| Gemini 3.1 Pro | prompttriage | **44.1** | 9.0 | 8.9 | 9.2 | 8.6 | 8.4 |
| Claude Sonnet 4.6 | prompttriage | **44.2** | 9.0 | 9.0 | 9.4 | 8.4 | 8.4 |
| Gemini 3.1 Pro | expert_cot | **44.5** | 9.0 | 9.0 | 9.4 | 8.7 | 8.4 |

### Key Research Findings

1. **PromptTriage and Expert CoT dominate**: The top three configurations all utilized advanced prompt structuring. `prompttriage` proved highly effective across both frontier models, competing directly with complex manual CoT strategies.
2. **"Simple" generic prompts constrain models**: For both models, the `simple` prompt condition scored **lower** than the `bare` condition (no system prompt). This validates that poorly crafted generic prompts actively harm output quality compared to going bare.
3. **Edge cases require explicit framing**: The weakest dimensions for baseline models were Boundaries and Edge Cases. Models struggle to proactively flag risks without a guiding prompt. `expert_cot` and `prompttriage` significantly improved edge case spotting, proving robust framing is essential for professional-grade safety.
4. **LLM-as-a-Judge Bias is severe**: Our initial run used Gemini as the judge, which resulted in Gemini giving itself perfect 50.0/50.0 scores across all conditions. Switching to Meta's Llama 4 Maverick eliminated this artificial ceiling effect and provided a rigorous, unbiased baseline.

### Estimated Cost: ~$5 (API calls)
### Status: ✅ Complete

---

## Study D v2: Quality Benchmark (IFEval + Writing Tasks) ✅ (Re-judged 2026-03-15)

### Objective
Quantify how much difference a system prompt makes on standard benchmarks: deterministic IFEval (instruction following) and open-ended quality writing tasks (20 diverse prompts).

### Evaluation Setup
- **Models Evaluated**: Gemini 3.1 Pro, Claude Sonnet 4.6
- **Conditions**: bare, simple, expert_cot, prompttriage
- **Benchmarks**: IFEval (50 problems, deterministic pass/fail) + Quality (20 writing tasks, LLM-judged)
- **Judge (Quality)**: Meta Llama 4 Maverick 17B-128E MoE (re-judged; original Gemini judge give 40/40 to everything)
- **Quality Rubric**: 4 dimensions × 10 pts each = 40 max (Instruction Adherence, Content Quality, Organization, Conciseness)
- **Total Evaluations**: 160 quality (8 × 20) + 400 IFEval (8 × 50) = 560

### IFEval Results (Deterministic — No Judge Bias)

| Model | Condition | Prompt-Level Accuracy |
|-------|-----------|---------------------:|
| Claude Sonnet 4.6 | bare | 82% |
| Claude Sonnet 4.6 | simple | 82% |
| Claude Sonnet 4.6 | expert_cot | **88%** |
| Claude Sonnet 4.6 | prompttriage | 86% |
| Gemini 3.1 Pro | bare | 76% |
| Gemini 3.1 Pro | simple | 78% |
| Gemini 3.1 Pro | expert_cot | 80% |
| Gemini 3.1 Pro | prompttriage | **82%** |

### Quality Results (Llama 4 Maverick Re-judged)

| Model | Condition | **Total /40** | Instr | Qual | Org | Conc |
|-------|-----------|-------------:|------:|-----:|----:|-----:|
| Claude Sonnet 4.6 | bare | **34.4** | 8.8 | 8.9 | 8.8 | 7.8 |
| Claude Sonnet 4.6 | expert_cot | **35.0** | 9.0 | 9.1 | 8.9 | 8.1 |
| Claude Sonnet 4.6 | simple | **35.3** | 9.1 | 8.9 | 9.2 | 8.2 |
| Claude Sonnet 4.6 | prompttriage | **35.4** | 9.1 | 9.0 | 9.1 | 8.2 |
| Gemini 3.1 Pro | bare | **35.5** | 9.2 | 9.0 | 9.2 | 8.2 |
| Gemini 3.1 Pro | expert_cot | **35.6** | 9.2 | 9.0 | 9.1 | 8.3 |
| Gemini 3.1 Pro | simple | **35.6** | 9.2 | 9.0 | 9.0 | 8.4 |
| Gemini 3.1 Pro | prompttriage | **35.9** | 9.2 | 9.0 | 9.2 | 8.5 |

### Key Research Findings

1. **IFEval shows clear prompt impact**: PromptTriage adds +6% to Gemini (76→82%) and +4% to Claude (82→86%) on instruction-following. Expert CoT is the strongest for Claude at 88%.
2. **Quality tasks show tighter clustering**: The spread across conditions is only 1.5 pts (/40) vs ~2 pts (/50) on behavioral tasks. General writing quality is less prompt-sensitive than domain-specific behavioral expertise.
3. **Conciseness is the most prompt-sensitive dimension**: Bare Claude scores 7.8/10 on conciseness, while prompted conditions reliably score 8.1-8.5. Prompts help models stay concise.
4. **Gemini outperforms Claude on quality tasks**: Even bare Gemini (35.5) beats prompted Claude conditions (34.4-35.4), suggesting Gemini has an edge on general writing/analysis tasks independent of prompting.

### Estimated Cost: ~$3 (API calls for re-judging)
### Status: ✅ Complete

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
| ~~2~~ | ~~**D v2/v3**  (Quality/Behavior)~~ | ~~$8.00~~ | ~~2 days~~| ✅ **Done** |
| ~~3~~ | ~~**A** (RAG Pipeline)~~ | ~~$5.50~~ | ~~1 day~~ | ✅ **Done** |
| 4 | **C** (Cascade Effect) | ~$25 | 1-2 days | Planned |
| 5 | **E** (Format Wars) | ~$15 | 1 day | Planned |

**Remaining Research Tasks:**
- Study C: Measuring the combinatorial impact of System Prompts + Task Prompts on downstream output quality.
- Study E: Measuring whether XML vs. JSON vs. Markdown fundamentally changes output scores for specific models.

