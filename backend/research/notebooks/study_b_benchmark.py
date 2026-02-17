# %% [markdown]
# # Study B Part 2: Progressive Benchmark
#
# Serves fine-tuned models via vLLM and runs the dense vs MoE
# breaking point analysis.
#
# **Prerequisites**: Run `study_b_training.py` for each model first.
# **Hardware**: Azure ML `Standard_NC24ads_A100_v4` (A100 80GB)

# %% [markdown]
# ## 1. Setup

# %%
import subprocess, sys, os, json, time
from pathlib import Path

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

install("vllm")
install("openai")
install("matplotlib")
install("pinecone")
install("google-genai")

# %%
import torch
import matplotlib.pyplot as plt
import numpy as np
from openai import OpenAI

print(f"PyTorch: {torch.__version__}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# %% [markdown]
# ## 2. Serve Fine-Tuned Model via vLLM
#
# vLLM serves the base model + LoRA adapter using the OpenAI-compatible
# API. Launch in a separate terminal with:
#
# ```bash
# vllm serve unsloth/Qwen3-8B \
#     --enable-lora \
#     --lora-modules qwen3_8b_qlora=./outputs/qwen3_8b_qlora/adapter \
#     --port 8001 \
#     --max-model-len 8192 \
#     --gpu-memory-utilization 0.85 \
#     --trust-remote-code
# ```
#
# For the MoE model:
# ```bash
# vllm serve unsloth/Qwen3-30B-A3B \
#     --enable-lora \
#     --lora-modules qwen3_30b_a3b_qlora=./outputs/qwen3_30b_a3b_qlora/adapter \
#     --port 8004 \
#     --max-model-len 8192 \
#     --gpu-memory-utilization 0.85 \
#     --trust-remote-code
# ```

# %%
# ══════════════════════════════════════════════════════════
# MODEL PORT CONFIGURATION
# ══════════════════════════════════════════════════════════
VLLM_MODELS = {
    "qwen3_8b_qlora":      {"port": 8001, "base": "unsloth/Qwen3-8B"},
    "qwen3_14b_qlora":     {"port": 8002, "base": "unsloth/Qwen3-14B"},
    "qwen3_32b_qlora":     {"port": 8003, "base": "unsloth/Qwen3-32B"},
    "qwen3_30b_a3b_qlora": {"port": 8004, "base": "unsloth/Qwen3-30B-A3B"},
}

# %% [markdown]
# ## 3. vLLM Client Helpers

# %%
def get_vllm_client(port: int) -> OpenAI:
    """Create OpenAI client pointing at local vLLM server."""
    return OpenAI(base_url=f"http://localhost:{port}/v1", api_key="dummy")


def generate_with_vllm(client, model_name, messages, max_tokens=4096):
    """Generate via vLLM OpenAI-compatible endpoint."""
    t0 = time.time()
    resp = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    latency = int((time.time() - t0) * 1000)
    return resp.choices[0].message.content, latency


def test_vllm_connection(model_name: str, port: int) -> bool:
    """Quick test that vLLM server is responding."""
    try:
        client = get_vllm_client(port)
        result, ms = generate_with_vllm(
            client, model_name,
            [{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=50,
        )
        print(f"✅ {model_name} on port {port} responding ({ms}ms): {result[:80]}")
        return True
    except Exception as e:
        print(f"❌ {model_name} on port {port} failed: {e}")
        return False

# %% [markdown]
# ## 4. Load Research Framework

# %%
sys.path.insert(0, str(Path("..").resolve()))
from research.test_suite import ALL_TEST_PROMPTS
from research.llm_judge import LLMJudge, BenchmarkResult, aggregate_scores, format_summary_table
from research.rag_methods import RAG_METHODS, run_rag_method

judge = LLMJudge()
print(f"Loaded {len(ALL_TEST_PROMPTS)} test prompts")
print(f"Loaded {len(RAG_METHODS)} RAG methods")

# %% [markdown]
# ## 5. Benchmark Function

# %%
PROMPTS_TO_USE = ALL_TEST_PROMPTS[:10]  # Use 10 for quick test, all 30 for full
RAG_METHOD = "L2_rerank_rag"


def benchmark_one_model(model_name, port, prompts, rag_method="L2_rerank_rag"):
    """Run full benchmark for a single vLLM-served model."""
    client = get_vllm_client(port)
    results = []

    for i, test in enumerate(prompts):
        print(f"  [{i+1}/{len(prompts)}] {test.id}: {test.user_prompt[:40]}...")

        # Get RAG context
        rag_result = run_rag_method(
            rag_method, query=test.user_prompt,
            vendor=test.target_vendor, top_k=3,
        )
        context = "\n---\n".join(d["content"][:1000] for d in rag_result.documents)

        # Build messages
        sys_msg = (
            "You are an expert system prompt engineer. Generate production-quality "
            "system prompts matching the target vendor's conventions."
        )
        user_msg = f"{test.user_prompt}\nTarget vendor: {test.target_vendor}"
        if context:
            user_msg += f"\n\n<reference_examples>\n{context}\n</reference_examples>"

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg},
        ]

        # Generate
        output, latency = generate_with_vllm(client, model_name, messages)

        # Judge
        score = judge.score(
            generated_prompt=output,
            target_vendor=test.target_vendor,
            target_model=test.target_model,
            user_prompt=test.user_prompt,
            context=test.context,
        )

        results.append(BenchmarkResult(
            prompt_id=test.id, method=f"model_{model_name}",
            target_vendor=test.target_vendor, category=test.category,
            generated_prompt=output, score=score,
            latency_ms=latency + rag_result.retrieval_ms,
            cost_usd=0.0,
            metadata={"rag_method": rag_method, "rag_ms": rag_result.retrieval_ms},
        ))
        time.sleep(0.5)

    return results

# %% [markdown]
# ## 6. Round 1: Qwen3-8B (8B active) vs Qwen3-30B-A3B (3B active)
#
# **Before running**: Start vLLM servers for both models in separate terminals.

# %%
# Test connections first
print("Testing vLLM connections...")
assert test_vllm_connection("qwen3_8b_qlora", 8001), "Start vLLM for 8B first!"
assert test_vllm_connection("qwen3_30b_a3b_qlora", 8004), "Start vLLM for 30B-A3B first!"

# %%
round1_results = {}

print("=== ROUND 1: 8B Dense vs 30B-A3B MoE ===\n")

print("--- Dense: qwen3_8b_qlora ---")
round1_results["dense"] = benchmark_one_model(
    "qwen3_8b_qlora", 8001, PROMPTS_TO_USE, RAG_METHOD)

print("\n--- MoE: qwen3_30b_a3b_qlora ---")
round1_results["moe"] = benchmark_one_model(
    "qwen3_30b_a3b_qlora", 8004, PROMPTS_TO_USE, RAG_METHOD)

# Score comparison
dense_avg = np.mean([r.score.total for r in round1_results["dense"]])
moe_avg = np.mean([r.score.total for r in round1_results["moe"]])
r1_winner = "Dense (8B)" if dense_avg > moe_avg else "MoE (30B-A3B)"

print(f"\n🏆 Round 1 Winner: {r1_winner}")
print(f"   Dense avg: {dense_avg:.1f}/50 | MoE avg: {moe_avg:.1f}/50")

# %% [markdown]
# ## 7. Round 2: Qwen3-14B (if MoE won Round 1)

# %%
# Only run if MoE won Round 1
if moe_avg >= dense_avg:
    print("=== ROUND 2: 14B Dense vs 30B-A3B MoE ===\n")
    assert test_vllm_connection("qwen3_14b_qlora", 8002), "Start vLLM for 14B first!"

    print("--- Dense: qwen3_14b_qlora ---")
    round2_dense = benchmark_one_model(
        "qwen3_14b_qlora", 8002, PROMPTS_TO_USE, RAG_METHOD)

    dense_avg_r2 = np.mean([r.score.total for r in round2_dense])
    r2_winner = "Dense (14B)" if dense_avg_r2 > moe_avg else "MoE (30B-A3B)"
    print(f"\n🏆 Round 2 Winner: {r2_winner}")
    print(f"   Dense 14B avg: {dense_avg_r2:.1f}/50 | MoE avg: {moe_avg:.1f}/50")
else:
    print("⏭️ Dense won Round 1 — skipping Round 2")

# %% [markdown]
# ## 8. Visualization

# %%
def plot_round_comparison(all_results: dict, title="Dense vs MoE"):
    """Bar chart comparing model scores across dimensions."""
    dims = ["structure", "completeness", "vendor_fidelity", "conciseness", "actionability"]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(dims))
    width = 0.35

    colors = {"dense": "#4A90D9", "moe": "#E8655A"}

    for i, (arch, results) in enumerate(all_results.items()):
        avgs = [np.mean([getattr(r.score, d) for r in results]) for d in dims]
        bars = ax.bar(x + (i - 0.5) * width, avgs, width,
                      label=arch.upper(), color=colors.get(arch, "#999"))
        for bar, v in zip(bars, avgs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f"{v:.1f}", ha="center", fontsize=9)

    ax.set_ylabel("Score (1-10)")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace("_", "\n") for d in dims])
    ax.legend()
    ax.set_ylim(0, 10.5)
    plt.tight_layout()
    plt.savefig(f"./outputs/{title.lower().replace(' ', '_')}.png", dpi=150)
    plt.show()

plot_round_comparison(round1_results, "Round 1: 8B Dense vs 30B-A3B MoE")

# %% [markdown]
# ## 9. Export Results

# %%
from datetime import datetime

all_results_flat = []
for arch, results in round1_results.items():
    all_results_flat.extend(results)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"./outputs/study_b_results_{ts}.json"
with open(output_path, "w") as f:
    json.dump([r.to_dict() for r in all_results_flat], f, indent=2, default=str)

print(f"Results saved: {output_path}")
print(f"\n{format_summary_table(aggregate_scores(all_results_flat))}")
