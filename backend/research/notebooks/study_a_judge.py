#!/usr/bin/env python3
"""
Study A — Stage 3: Judge all generated outputs with Llama 4 Maverick.

Runs LOCALLY after downloading study_a_outputs.json from Azure ML.
Uses the same 5-dimension rubric and Llama 4 Maverick judge as Study D.

Usage:
    python study_a_judge.py [--input path/to/study_a_outputs.json]
"""
import json
import os
import re
import sys
import time
from pathlib import Path

# ── Config ──
VERTEX_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "modelsandtraining")
VERTEX_REGION = "us-east5"  # Only region with Llama 4 Maverick
LLAMA4_MODEL = "meta/llama-4-maverick-17b-128e-instruct-maas"

JUDGE_RUBRIC = """You are an expert evaluator of AI system prompts. Score the following generated system prompt on 5 dimensions, each from 1-10.

USER REQUEST: "{user_prompt}"
TARGET VENDOR: {vendor}
TARGET MODEL: {target_model}

GENERATED SYSTEM PROMPT:
---
{generated_prompt}
---

Score each dimension 1-10:
1. **Structure** (1-10): Is the prompt well-organized with proper formatting for the target vendor? (XML tags for Anthropic, Markdown for OpenAI, hybrid for Google)
2. **Completeness** (1-10): Does it cover all aspects of the user's request — role, rules, output format, guardrails, domain knowledge?
3. **Vendor Fidelity** (1-10): Does it follow the conventions and best practices of the target vendor/model?
4. **Conciseness** (1-10): Is it efficient? Good ratio of useful content to token count? No unnecessary filler?
5. **Actionability** (1-10): Could this prompt be used immediately in production? Is it specific and practical?

Respond ONLY with valid JSON:
{{"structure": N, "completeness": N, "vendor_fidelity": N, "conciseness": N, "actionability": N}}"""


def get_access_token():
    """Get GCP access token via google.auth library."""
    import google.auth
    import google.auth.transport.requests

    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials.token


def judge_with_llama4(prompt_text: str, access_token: str) -> dict:
    """Call Llama 4 Maverick via Vertex AI MaaS endpoint."""
    import requests

    endpoint = f"https://{VERTEX_REGION}-aiplatform.googleapis.com"
    url = (
        f"{endpoint}/v1/projects/{VERTEX_PROJECT}/locations/{VERTEX_REGION}"
        f"/endpoints/openapi/chat/completions"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLAMA4_MODEL,
        "max_tokens": 200,
        "temperature": 0.1,
        "messages": [
            {"role": "user", "content": prompt_text},
        ],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_scores(raw_text: str) -> dict:
    """Parse JSON scores from judge response."""
    # Try direct JSON parse
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass
    # Extract JSON block from markdown
    m = re.search(r'\{[^{}]+\}', raw_text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Study A Stage 3: Judge with Llama 4 Maverick")
    parser.add_argument("--input", default=None,
                        help="Path to study_a_outputs.json (default: named-outputs/study_a/)")
    args = parser.parse_args()

    # Find input file
    if args.input:
        input_file = Path(args.input)
    else:
        input_file = Path(__file__).parent / "named-outputs" / "study_a" / "study_a_outputs.json"

    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("  Download from Azure ML first, or specify --input path")
        sys.exit(1)

    outputs = json.loads(input_file.read_text(encoding="utf-8"))
    print(f"Loaded {len(outputs)} outputs from {input_file}")

    # Output file (scored)
    scored_file = input_file.parent / "study_a_scored.json"

    # Resume support
    existing = []
    done_keys = set()
    if scored_file.exists():
        existing = json.loads(scored_file.read_text(encoding="utf-8"))
        done_keys = {(r["prompt_id"], r["rag_level"]) for r in existing}
        print(f"Resuming: {len(existing)} already scored")

    scored = list(existing)
    remaining = [o for o in outputs if (o["prompt_id"], o["rag_level"]) not in done_keys]
    print(f"Remaining to score: {len(remaining)}")

    if not remaining:
        print("All outputs already scored!")
        _print_summary(scored)
        return

    # Get access token
    print("Getting GCP access token...")
    access_token = get_access_token()

    errors = 0
    for i, output in enumerate(remaining, 1):
        key = f"{output['prompt_id']}/{output['rag_level']}"
        print(f"  [{i}/{len(remaining)}] {key}...", end="", flush=True)

        if output["char_count"] == 0 or "[GENERATION FAILED" in output.get("generated_prompt", ""):
            print(" SKIPPED (generation failed)")
            scored.append({**output, "scores": None, "total_score": 0, "judge_error": "generation_failed"})
            continue

        prompt = JUDGE_RUBRIC.format(
            user_prompt=output["user_prompt"],
            vendor=output["vendor"],
            target_model=output["target_model"],
            generated_prompt=output["generated_prompt"][:8000],  # Cap to avoid huge payloads
        )

        try:
            raw = judge_with_llama4(prompt, access_token)
            scores = parse_scores(raw)

            if scores:
                total = sum(scores.values())
                print(f" {total}/50")
                scored.append({**output, "scores": scores, "total_score": total})
            else:
                print(f" PARSE FAILED: {raw[:100]}")
                scored.append({**output, "scores": None, "total_score": 0, "judge_error": f"parse_failed: {raw[:200]}"})
                errors += 1

        except Exception as e:
            print(f" ERROR: {e}")
            scored.append({**output, "scores": None, "total_score": 0, "judge_error": str(e)})
            errors += 1

            # Refresh token on auth errors
            if "401" in str(e) or "403" in str(e):
                print("  Refreshing access token...")
                try:
                    access_token = get_access_token()
                except Exception:
                    pass

        # Save progressively
        scored_file.write_text(json.dumps(scored, indent=2, ensure_ascii=True), encoding="utf-8")

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    print(f"\n✅ Scored {len(scored)} outputs ({errors} errors) -> {scored_file}")
    _print_summary(scored)


def _print_summary(scored: list):
    """Print summary table."""
    print(f"\n{'='*60}")
    print("STUDY A RESULTS: RAG Level vs Quality")
    print(f"{'='*60}")
    print(f"{'RAG Level':<25} {'N':>4} {'Avg Score':>10} {'Avg /50':>8}")
    print("-" * 50)

    levels = ["L0_no_rag", "L1_naive_rag", "L2_rerank_rag", "L3_corrective_rag", "L4_judge_rag", "L5_agentic_rag"]
    for level in levels:
        level_results = [r for r in scored if r["rag_level"] == level and r.get("total_score", 0) > 0]
        if level_results:
            avg = sum(r["total_score"] for r in level_results) / len(level_results)
            print(f"  {level:<25} {len(level_results):>3}  {avg:>8.1f}/50")
        else:
            print(f"  {level:<25}   0    N/A")

    # Comparison with proprietary baselines
    print(f"\n{'─'*50}")
    print("Proprietary Baselines (Study B/D):")
    print("  Gemini 3.1 Pro:       ~43-44/50")
    print("  Claude Sonnet 4.5:    ~43-44/50")
    print("  Qwen3-235B base:      ~42/50")
    print("  Qwen3-14B (no RAG):   ~26/50")


if __name__ == "__main__":
    main()
