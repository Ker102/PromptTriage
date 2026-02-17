# %% [markdown]
# # Study C: System Prompt Impact
# 
# Tests how system prompt complexity affects generation quality.
# 
# | Level | Description | ~Words |
# |-------|-------------|--------|
# | L0 | No system prompt | 0 |
# | L1 | Minimal | 10 |
# | L2 | Basic | 50 |
# | L3 | Standard (full spec) | 500 |
# | L4 | Production Anthropic | 8,000+ |

# %% [markdown]
# ## 1. Setup

# %%
import subprocess, sys, os, json
from pathlib import Path
from datetime import datetime

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

install("google-genai")
install("python-dotenv")
install("matplotlib")

from dotenv import load_dotenv
load_dotenv()

# %%
sys.path.insert(0, str(Path("..").resolve()))
from research.test_suite import ALL_TEST_PROMPTS
from research.llm_judge import LLMJudge, aggregate_scores, format_summary_table
from research.benchmark_runner import run_study_c, PROMPT_LEVELS

print(f"Test prompts: {len(ALL_TEST_PROMPTS)}")
print(f"Prompt levels: {list(PROMPT_LEVELS.keys())}")

# %% [markdown]
# ## 2. Run Study C

# %%
PROMPTS = ALL_TEST_PROMPTS[:10]  # ← Change to ALL_TEST_PROMPTS for full run
MODEL = "gemini-2.5-pro-preview-05-06"

# Optional: path to a real production Anthropic prompt for L4
L4_PROMPT_PATH = None  # e.g., "../system-prompts-reference/anthropic/claude_code.md"

results = run_study_c(prompts=PROMPTS, model=MODEL, l4_prompt_path=L4_PROMPT_PATH)
print(f"\nStudy C complete: {len(results)} results")

# %% [markdown]
# ## 3. Results

# %%
import matplotlib.pyplot as plt
import numpy as np

summary = aggregate_scores(results)
print(format_summary_table(summary))

# %%
# Complexity vs Quality curve
levels = sorted(summary.keys())
totals = [summary[l]["avg_total"] for l in levels]
words = [summary[l]["avg_word_count"] for l in levels]

fig, ax1 = plt.subplots(figsize=(10, 5))
color1 = "#4A90D9"
color2 = "#E8655A"

ax1.plot(range(len(levels)), totals, "o-", color=color1, linewidth=2, markersize=8)
ax1.set_ylabel("Avg Quality Score (/50)", color=color1)
ax1.set_xlabel("System Prompt Complexity Level")
ax1.set_xticks(range(len(levels)))
ax1.set_xticklabels([l.replace("impact_", "") for l in levels], rotation=30)

ax2 = ax1.twinx()
ax2.bar(range(len(levels)), words, alpha=0.3, color=color2)
ax2.set_ylabel("Avg Output Word Count", color=color2)

plt.title("System Prompt Complexity vs Output Quality")
plt.tight_layout()
plt.savefig("./outputs/study_c_complexity_curve.png", dpi=150)
plt.show()

# %% [markdown]
# ## 4. Dimension Breakdown

# %%
dims = ["avg_structure", "avg_completeness", "avg_vendor_fidelity", 
        "avg_conciseness", "avg_actionability"]
dim_labels = ["Structure", "Complete", "Vendor\nFidelity", "Concise", "Action"]

fig, axes = plt.subplots(1, len(dims), figsize=(18, 4), sharey=True)
for ax, dim, label in zip(axes, dims, dim_labels):
    vals = [summary[l][dim] for l in levels]
    ax.bar(range(len(levels)), vals, color=plt.cm.coolwarm(np.linspace(0.2, 0.8, len(levels))))
    ax.set_title(label)
    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels([l.split("_")[-1] for l in levels], fontsize=8)
    ax.set_ylim(0, 10.5)

axes[0].set_ylabel("Score (1-10)")
plt.suptitle("Dimension Scores by Prompt Complexity", y=1.02)
plt.tight_layout()
plt.savefig("./outputs/study_c_dimensions.png", dpi=150)
plt.show()

# %% [markdown]
# ## 5. Save Results

# %%
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"./outputs/study_c_results_{ts}.json"
with open(output_path, "w") as f:
    json.dump([r.to_dict() for r in results], f, indent=2, default=str)
print(f"Results saved: {output_path}")
