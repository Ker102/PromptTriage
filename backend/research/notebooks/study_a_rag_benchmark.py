# %% [markdown]
# # Study A: RAG Architecture × Model Quality Matrix
# 
# Tests 6 RAG strategies (L0-L5) across test prompts.
# 
# **Phase 1**: Gemini Pro baseline (API-only, no GPU needed)
# **Phase 2**: Re-run with fine-tuned Qwen3 models from Study B
# 
# | Level | Method | Description |
# |-------|--------|-------------|
# | L0 | No RAG | Direct LLM generation |
# | L1 | Naive RAG | Embed → top-K Pinecone |
# | L2 | Rerank RAG | L1 + LLM reranker |
# | L3 | CRAG | L2 + relevance check + web fallback |
# | L4 | Judge RAG | L3 + LLM doc grading |
# | L5 | Agentic RAG | L4 + query decomposition |

# %% [markdown]
# ## 1. Setup

# %%
import subprocess, sys, os, json, time
from pathlib import Path
from datetime import datetime

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

install("google-genai")
install("pinecone")
install("python-dotenv")
install("matplotlib")

# %%
# Set API keys (or use .env file)
# os.environ["GOOGLE_API_KEY"] = "..."
# os.environ["PINECONE_API_KEY"] = "..."

from dotenv import load_dotenv
load_dotenv()

print(f"GOOGLE_API_KEY: {'✅' if os.getenv('GOOGLE_API_KEY') else '❌'}")
print(f"PINECONE_API_KEY: {'✅' if os.getenv('PINECONE_API_KEY') else '❌'}")

# %% [markdown]
# ## 2. Load Research Framework

# %%
sys.path.insert(0, str(Path("..").resolve()))
from research.test_suite import ALL_TEST_PROMPTS, BY_CATEGORY, BY_VENDOR
from research.llm_judge import LLMJudge, aggregate_scores, format_summary_table
from research.rag_methods import RAG_METHODS, run_rag_method
from research.benchmark_runner import run_study_a

print(f"Test prompts: {len(ALL_TEST_PROMPTS)}")
print(f"RAG methods: {list(RAG_METHODS.keys())}")

# %% [markdown]
# ## 3. Phase 1: Gemini Pro Baseline

# %%
# Use subset for quick test, or all 30 for full run
PROMPTS = ALL_TEST_PROMPTS[:5]  # ← Change to ALL_TEST_PROMPTS for full
MODEL = "gemini-2.5-pro-preview-05-06"

print(f"Running Phase 1: {len(PROMPTS)} prompts × {len(RAG_METHODS)} methods")
print(f"Generator: {MODEL}")
print(f"Total runs: {len(PROMPTS) * len(RAG_METHODS)}")

results_phase1 = run_study_a(prompts=PROMPTS, model=MODEL)
print(f"\nPhase 1 complete: {len(results_phase1)} results")

# %% [markdown]
# ## 4. Phase 1 Results

# %%
import matplotlib.pyplot as plt
import numpy as np

summary = aggregate_scores(results_phase1)
print(format_summary_table(summary))

# %%
# Plot: RAG method comparison
methods = list(summary.keys())
totals = [summary[m]["avg_total"] for m in methods]
latencies = [summary[m]["avg_latency_ms"] for m in methods]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Quality scores
bars = ax1.barh(methods, totals, color=plt.cm.viridis(np.linspace(0.3, 0.9, len(methods))))
ax1.set_xlabel("Average Total Score (/50)")
ax1.set_title("RAG Method Quality (Gemini Pro)")
for bar, v in zip(bars, totals):
    ax1.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
             f"{v:.1f}", va="center", fontsize=10)

# Latency
bars2 = ax2.barh(methods, latencies, color=plt.cm.magma(np.linspace(0.3, 0.8, len(methods))))
ax2.set_xlabel("Average Latency (ms)")
ax2.set_title("RAG Method Latency")

plt.tight_layout()
plt.savefig("./outputs/study_a_phase1_results.png", dpi=150)
plt.show()

# %% [markdown]
# ## 5. Phase 2: Fine-Tuned Models (after Study B)
# 
# Uncomment and run after completing Study B training + benchmarking.

# %%
# from openai import OpenAI
#
# FINETUNED_MODELS = {
#     "qwen3_8b_qlora": {"port": 8001},
#     "qwen3_30b_a3b_qlora": {"port": 8004},
# }
#
# # Run each fine-tuned model through all RAG methods
# for model_name, config in FINETUNED_MODELS.items():
#     print(f"\n=== Phase 2: {model_name} ===")
#     # Same RAG methods, different generator model
#     # (Requires vLLM server running — see study_b_benchmark.py)

# %% [markdown]
# ## 6. Save Results

# %%
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"./outputs/study_a_results_{ts}.json"
data = [r.to_dict() for r in results_phase1]
with open(output_path, "w") as f:
    json.dump(data, f, indent=2, default=str)
print(f"Results saved: {output_path}")
