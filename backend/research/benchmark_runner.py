"""
Benchmark Runner — Orchestrates all 3 studies.

Study A: RAG Architecture (6 methods × 30 prompts × N models)
  - Phase 1: Gemini Pro baseline
  - Phase 2: Re-run with best fine-tuned Qwen3 models from Study B
Study B: Dense vs MoE Breaking Point (progressive rounds)
  - Round 1: Qwen3-8B vs Qwen3-30B-A3B
  - Round 2: Qwen3-14B vs Qwen3-30B-A3B (if MoE won R1)
  - Round 3: Qwen3-32B vs Qwen3-30B-A3B (if MoE won R2)
  - Ceiling: Qwen3-235B-A22B (inference only, no fine-tuning)
Study C: System Prompt Impact (5 complexity levels × best models)

Hardware: Azure ML Standard_NC24ads_A100_v4 (A100 80GB)

Usage:
    python -m research.benchmark_runner --study A
    python -m research.benchmark_runner --study B --round 1
    python -m research.benchmark_runner --study B --round all
    python -m research.benchmark_runner --study C
    python -m research.benchmark_runner --study all
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from research.test_suite import ALL_TEST_PROMPTS, TestPrompt
from research.llm_judge import LLMJudge, BenchmarkResult, JudgeScore
from research.llm_judge import aggregate_scores, format_summary_table
from research.rag_methods import RAG_METHODS, run_rag_method

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ── System Prompt Generation ────────────────────────────────────────────

GENERATOR_SYSTEM_PROMPT = """You are an expert system prompt engineer. Given a user's description of what they need, generate a production-quality system prompt optimized for the specified vendor and model.

Follow the target vendor's conventions:
- Anthropic: Use XML tags (<identity>, <rules>, <thinking>, <output_format>), detailed (~8K words)
- OpenAI: Use Markdown headers (## sections), concise (~1.4K words), tool schemas
- Google: Hybrid XML/Markdown, moderate length (~1.3K words), grounding instructions

Include these sections as appropriate:
1. Identity/Role definition
2. Behavioral rules and constraints
3. Output format specification
4. Safety and guardrails
5. Tool definitions (if applicable)
6. Chain-of-thought / reasoning instructions
7. Edge case handling
8. Examples (if helpful)"""


def generate_system_prompt(
    client, test: TestPrompt,
    rag_context: str = "",
    model: str = "gemini-2.5-pro-preview-05-06",
    system_prompt_override: str = "",
) -> tuple[str, int]:
    """Generate a system prompt and return (output, latency_ms)."""
    user_msg = f"User request: {test.user_prompt}"
    if test.context:
        user_msg += f"\nAdditional context: {test.context}"
    user_msg += f"\nTarget vendor: {test.target_vendor}"
    user_msg += f"\nTarget model: {test.target_model or 'Not specified'}"

    if rag_context:
        user_msg += f"\n\n<reference_examples>\n{rag_context}\n</reference_examples>"

    sys_prompt = system_prompt_override or GENERATOR_SYSTEM_PROMPT

    t0 = time.time()
    try:
        resp = client.models.generate_content(
            model=model,
            contents=user_msg,
            config={
                "system_instruction": sys_prompt,
                "temperature": 0.7,
                "max_output_tokens": 16384,
            },
        )
        output = resp.text
    except Exception as e:
        output = f"[GENERATION FAILED: {e}]"

    latency = int((time.time() - t0) * 1000)
    return output, latency


# ── Study A: RAG Architecture ───────────────────────────────────────────

def run_study_a(
    prompts: list[TestPrompt] = None,
    methods: list[str] = None,
    model: str = "gemini-2.5-pro-preview-05-06",
) -> list[BenchmarkResult]:
    """Run all RAG methods across test prompts."""
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    judge = LLMJudge()

    prompts = prompts or ALL_TEST_PROMPTS
    methods = methods or list(RAG_METHODS.keys())
    results = []

    print(f"\n{'='*60}")
    print(f"STUDY A: RAG Architecture Comparison")
    print(f"Prompts: {len(prompts)} | Methods: {len(methods)}")
    print(f"{'='*60}\n")

    for method_name in methods:
        print(f"\n--- Method: {method_name} ---")
        for i, test in enumerate(prompts):
            print(f"  [{i+1}/{len(prompts)}] {test.id}: {test.user_prompt[:50]}...")

            # Step 1: Retrieve context
            rag_result = run_rag_method(
                method_name, query=test.user_prompt,
                vendor=test.target_vendor, top_k=3,
            )
            context = "\n---\n".join(
                d["content"][:1000] for d in rag_result.documents
            )

            # Step 2: Generate system prompt
            output, latency = generate_system_prompt(
                client, test, rag_context=context, model=model,
            )

            # Step 3: Judge
            score = judge.score(
                generated_prompt=output,
                target_vendor=test.target_vendor,
                target_model=test.target_model,
                user_prompt=test.user_prompt,
                context=test.context,
            )

            results.append(BenchmarkResult(
                prompt_id=test.id, method=method_name,
                target_vendor=test.target_vendor,
                category=test.category,
                generated_prompt=output, score=score,
                latency_ms=latency + rag_result.retrieval_ms,
                cost_usd=0.0,
                metadata={"rag_retrieval_ms": rag_result.retrieval_ms,
                          "rag_docs": rag_result.num_after_filter},
            ))

            time.sleep(1)  # Rate limiting

    return results


# ── Study B: Dense vs MoE Breaking Point ────────────────────────────────

# Progressive rounds: find where dense models overtake MoE
# Each round fine-tunes both models with QLoRA, then benchmarks
STUDY_B_ROUNDS = {
    1: {
        "dense": {"label": "qwen3_8b", "model_id": "Qwen/Qwen3-8B", "active_params": "8B"},
        "moe": {"label": "qwen3_30b_a3b", "model_id": "Qwen/Qwen3-30B-A3B", "active_params": "3B"},
    },
    2: {
        "dense": {"label": "qwen3_14b", "model_id": "Qwen/Qwen3-14B", "active_params": "14B"},
        "moe": {"label": "qwen3_30b_a3b", "model_id": "Qwen/Qwen3-30B-A3B", "active_params": "3B"},
    },
    3: {
        "dense": {"label": "qwen3_32b", "model_id": "Qwen/Qwen3-32B", "active_params": "32B"},
        "moe": {"label": "qwen3_30b_a3b", "model_id": "Qwen/Qwen3-30B-A3B", "active_params": "3B"},
    },
}

# Ceiling benchmark (inference only, no fine-tuning)
STUDY_B_CEILING = {
    "label": "qwen3_235b_a22b",
    "model_id": "Qwen/Qwen3-235B-A22B",
    "active_params": "22B",
}

# Proprietary baselines for context
STUDY_B_BASELINES = {
    "gemini_3_pro": "gemini-2.5-pro-preview-05-06",
    "gemini_3_flash": "gemini-2.0-flash",
    # "claude_sonnet_4": "claude-sonnet-4@vertex",
    # "gpt_5_2": "gpt-5.2",
}

# vLLM endpoint template for fine-tuned models served on Azure ML
VLLM_ENDPOINT_TEMPLATE = "http://localhost:{port}/v1"  # Port set per model


def _benchmark_model(
    client, judge: "LLMJudge", prompts: list[TestPrompt],
    model_label: str, model_id: str,
    rag_method: str = "L2_rerank_rag",
) -> list[BenchmarkResult]:
    """Run benchmark for one model across all prompts."""
    results = []
    for i, test in enumerate(prompts):
        print(f"  [{i+1}/{len(prompts)}] {test.id}")

        rag_result = run_rag_method(
            rag_method, query=test.user_prompt,
            vendor=test.target_vendor, top_k=3,
        )
        context = "\n---\n".join(
            d["content"][:1000] for d in rag_result.documents
        )

        output, latency = generate_system_prompt(
            client, test, rag_context=context, model=model_id,
        )

        score = judge.score(
            generated_prompt=output,
            target_vendor=test.target_vendor,
            target_model=test.target_model,
            user_prompt=test.user_prompt,
            context=test.context,
        )

        results.append(BenchmarkResult(
            prompt_id=test.id, method=f"model_{model_label}",
            target_vendor=test.target_vendor,
            category=test.category,
            generated_prompt=output, score=score,
            latency_ms=latency, cost_usd=0.0,
            metadata={"active_params": model_label},
        ))
        time.sleep(1)
    return results


def run_study_b(
    prompts: list[TestPrompt] = None,
    rounds: list[int] = None,
    rag_method: str = "L2_rerank_rag",
    vllm_base_url: str = None,
) -> list[BenchmarkResult]:
    """Progressive dense vs MoE breaking point analysis.

    Runs rounds sequentially. If MoE wins a round, escalate to next
    dense model size. Stops if dense overtakes MoE.

    Args:
        rounds: Which rounds to run (default: [1, 2, 3] = all).
                 Use [1] for quick test, [1,2,3] for full analysis.
        vllm_base_url: Base URL for vLLM-served fine-tuned models.
                       Format: http://host:port/v1
    """
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    judge = LLMJudge()

    prompts = prompts or ALL_TEST_PROMPTS[:10]
    rounds = rounds or [1, 2, 3]
    all_results = []
    round_winners = {}

    print(f"\n{'='*60}")
    print(f"STUDY B: Dense vs MoE Breaking Point")
    print(f"Prompts: {len(prompts)} | Rounds: {rounds}")
    print(f"RAG Method: {rag_method}")
    print(f"{'='*60}\n")

    # ── Run proprietary baselines first ──
    for label, model_id in STUDY_B_BASELINES.items():
        print(f"\n--- Baseline: {label} ({model_id}) ---")
        results = _benchmark_model(
            client, judge, prompts, label, model_id, rag_method)
        all_results.extend(results)

    # ── Progressive rounds ──
    for rnd in rounds:
        if rnd not in STUDY_B_ROUNDS:
            print(f"\n⚠️ Round {rnd} not configured, skipping")
            continue

        config = STUDY_B_ROUNDS[rnd]
        dense = config["dense"]
        moe = config["moe"]

        print(f"\n{'='*60}")
        print(f"ROUND {rnd}: {dense['label']} ({dense['active_params']} active) "
              f"vs {moe['label']} ({moe['active_params']} active)")
        print(f"{'='*60}")

        # NOTE: In the notebook, models are served via vLLM.
        # Here we use placeholder model IDs — the notebook handles
        # actual vLLM endpoint routing.
        for arch_type, model_info in [("dense", dense), ("moe", moe)]:
            label = f"r{rnd}_{model_info['label']}_qlora"
            # Use vLLM endpoint if available, else use model_id as placeholder
            model_id = model_info["model_id"]
            if vllm_base_url:
                model_id = f"{model_info['label']}-qlora@{vllm_base_url}"

            print(f"\n--- {arch_type.upper()}: {label} ---")
            results = _benchmark_model(
                client, judge, prompts, label, model_id, rag_method)
            all_results.extend(results)

        # Determine round winner
        dense_results = [r for r in all_results
                        if r.method == f"model_r{rnd}_{dense['label']}_qlora"]
        moe_results = [r for r in all_results
                      if r.method == f"model_r{rnd}_{moe['label']}_qlora"]

        if dense_results and moe_results:
            dense_avg = sum(r.score.total for r in dense_results) / len(dense_results)
            moe_avg = sum(r.score.total for r in moe_results) / len(moe_results)
            winner = "dense" if dense_avg > moe_avg else "moe"
            round_winners[rnd] = {
                "winner": winner,
                "dense_avg": round(dense_avg, 2),
                "moe_avg": round(moe_avg, 2),
            }
            print(f"\n🏆 Round {rnd} Winner: {winner.upper()} "
                  f"(dense={dense_avg:.1f} vs moe={moe_avg:.1f})")

            if winner == "dense":
                print(f"\n✅ Breaking point found at Round {rnd}! "
                      f"Dense {dense['active_params']} > MoE {moe['active_params']}")
                break  # No need for more rounds

    # ── Summary ──
    print(f"\n{'='*60}")
    print("ROUND SUMMARY:")
    for rnd, info in round_winners.items():
        print(f"  Round {rnd}: {info['winner'].upper()} "
              f"(dense={info['dense_avg']:.1f}, moe={info['moe_avg']:.1f})")
    print(f"{'='*60}")

    return all_results


# ── Study C: System Prompt Impact ────────────────────────────────────────

# Models to test across all prompt levels
STUDY_C_MODELS = {
    "gemini_3_pro": "gemini-2.5-pro-preview-05-06",
    # "qwen3_30b_a3b_qlora": "qwen3-30b-a3b-qlora@local",  # After fine-tuning
    # "claude_sonnet_4": "claude-sonnet-4@vertex",  # After Vertex AI setup
}

PROMPT_LEVELS = {
    "L0_none": "",
    "L1_minimal": "You are a helpful system prompt engineer.",
    "L2_basic": (
        "You are an expert system prompt engineer. "
        "Generate production-quality system prompts with clear structure, "
        "identity sections, behavioral rules, and output format specifications. "
        "Follow the target vendor's conventions."
    ),
    "L3_standard": GENERATOR_SYSTEM_PROMPT,  # ~500 words
    # L4 is loaded from corpus (the actual Anthropic Claude Code prompt)
}


def run_study_c(
    prompts: list[TestPrompt] = None,
    model: str = "gemini-2.5-pro-preview-05-06",
    l4_prompt_path: str = None,
) -> list[BenchmarkResult]:
    """Test how system prompt complexity affects output quality."""
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    judge = LLMJudge()

    prompts = prompts or ALL_TEST_PROMPTS[:10]
    levels = dict(PROMPT_LEVELS)

    # Load L4 full Anthropic prompt from corpus if available
    if l4_prompt_path and os.path.exists(l4_prompt_path):
        with open(l4_prompt_path, "r", encoding="utf-8") as f:
            levels["L4_full_anthropic"] = f.read()
    else:
        levels["L4_full_anthropic"] = levels["L3_standard"]
        print("  [Warning] L4 prompt not found, using L3 as fallback")

    results = []

    print(f"\n{'='*60}")
    print(f"STUDY C: System Prompt Impact")
    print(f"Prompts: {len(prompts)} | Levels: {len(levels)}")
    print(f"{'='*60}\n")

    for level_name, sys_prompt in levels.items():
        print(f"\n--- Level: {level_name} ---")
        for i, test in enumerate(prompts):
            print(f"  [{i+1}/{len(prompts)}] {test.id}")

            output, latency = generate_system_prompt(
                client, test,
                model=model,
                system_prompt_override=sys_prompt if sys_prompt else None,
            )

            score = judge.score(
                generated_prompt=output,
                target_vendor=test.target_vendor,
                target_model=test.target_model,
                user_prompt=test.user_prompt,
                context=test.context,
            )

            results.append(BenchmarkResult(
                prompt_id=test.id,
                method=f"impact_{level_name}",
                target_vendor=test.target_vendor,
                category=test.category,
                generated_prompt=output, score=score,
                latency_ms=latency, cost_usd=0.0,
                metadata={"system_prompt_words": len(sys_prompt.split())},
            ))
            time.sleep(1)

    return results


# ── Save & Report ────────────────────────────────────────────────────────

def save_results(results: list[BenchmarkResult], study: str):
    """Save results to JSON and print summary."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"study_{study}_{ts}.json"
    data = [r.to_dict() for r in results]
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\nResults saved to: {path}")

    summary = aggregate_scores(results)
    print(f"\n{format_summary_table(summary)}")
    return path


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PromptTriage Benchmark Runner")
    parser.add_argument("--study", choices=["A", "B", "C", "all"], default="A")
    parser.add_argument("--prompts", type=int, default=None,
                        help="Limit number of test prompts (for quick tests)")
    parser.add_argument("--model", default="gemini-2.5-pro-preview-05-06")
    parser.add_argument("--round", type=str, default="all",
                        help="Study B rounds: '1', '1,2', or 'all' (default: all)")
    parser.add_argument("--vllm-url", default=None,
                        help="vLLM base URL for fine-tuned models")
    args = parser.parse_args()

    prompts = ALL_TEST_PROMPTS
    if args.prompts:
        prompts = prompts[:args.prompts]

    # Parse rounds
    if args.round == "all":
        rounds = [1, 2, 3]
    else:
        rounds = [int(r.strip()) for r in args.round.split(",")]

    if args.study in ("A", "all"):
        results = run_study_a(prompts, model=args.model)
        save_results(results, "A")

    if args.study in ("B", "all"):
        results = run_study_b(prompts, rounds=rounds,
                              vllm_base_url=args.vllm_url)
        save_results(results, "B")

    if args.study in ("C", "all"):
        results = run_study_c(prompts, model=args.model)
        save_results(results, "C")


if __name__ == "__main__":
    main()
