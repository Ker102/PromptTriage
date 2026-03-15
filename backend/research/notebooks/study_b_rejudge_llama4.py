#!/usr/bin/env python3
"""
Re-judge ALL Study B outputs with Llama 4 Maverick (neutral judge).

The original judged_outputs.json used Gemini 3.1 Pro as judge, which has 
severe self-bias (scored itself 45.7/50 vs Claude 44.2/50). 

This script re-scores all 210 entries (7 models × 30 prompts) using 
Llama 4 Maverick via Vertex AI for an unbiased comparison.

Usage:
    python study_b_rejudge_llama4.py
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

INPUT_FILE = Path("named-outputs/benchmark_output/judged_outputs.json")
OUTPUT_FILE = Path("named-outputs/benchmark_output/judged_outputs_llama4.json")

JUDGE_RUBRIC = """Score this system prompt on 5 dimensions (1-10 each).

USER REQUEST: "{user_prompt}"
TARGET VENDOR: {target_vendor}
TARGET MODEL: {target_model}

GENERATED SYSTEM PROMPT:
---
{generated_prompt}
---

Dimensions:
1. Structure (1-10): Well-organized with proper vendor formatting?
2. Completeness (1-10): Covers role, rules, output format, guardrails?
3. Vendor_fidelity (1-10): Follows target vendor conventions?
4. Conciseness (1-10): Efficient content-to-token ratio?
5. Actionability (1-10): Production-ready and specific?

Respond with ONLY this JSON, nothing else:
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


def judge_with_llama4(prompt_text: str, access_token: str) -> str:
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
        "max_tokens": 100,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "You are a JSON-only scoring API. You MUST respond with ONLY a valid JSON object containing exactly 5 integer scores. No explanations, no text, no markdown — ONLY the JSON object."},
            {"role": "user", "content": prompt_text},
        ],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_scores(raw_text: str) -> dict | None:
    """Parse JSON scores from judge response."""
    raw = raw_text.strip()
    # Strip markdown code fences if present
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
    # Try direct JSON parse
    try:
        d = json.loads(raw)
        if all(k in d for k in ['structure', 'completeness', 'vendor_fidelity', 'conciseness', 'actionability']):
            return d
    except json.JSONDecodeError:
        pass
    # Extract JSON block from verbose text
    m = re.search(r'\{[^{}]*"structure"[^{}]*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    # Try to extract individual scores from verbose text
    dims = ['structure', 'completeness', 'vendor_fidelity', 'conciseness', 'actionability']
    scores = {}
    for dim in dims:
        # Match patterns like "Structure: 8", "structure: 8/10", "1. Structure (8)"
        patterns = [
            rf'{dim}["\s:]*\s*(\d+)',
            rf'{dim.replace("_", " ")}["\s:]*\s*(\d+)',
        ]
        for pat in patterns:
            m2 = re.search(pat, raw, re.IGNORECASE)
            if m2:
                val = int(m2.group(1))
                if 1 <= val <= 10:
                    scores[dim] = val
                    break
    if len(scores) == 5:
        return scores
    return None


def main():
    if not INPUT_FILE.exists():
        print(f"❌ Input file not found: {INPUT_FILE}")
        sys.exit(1)

    entries = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(entries)} entries from {INPUT_FILE}")

    # Resume support
    existing = []
    done_keys = set()
    if OUTPUT_FILE.exists():
        existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        done_keys = {(r["prompt_id"], r.get("model", r.get("method", ""))) for r in existing}
        print(f"Resuming: {len(existing)} already scored")

    scored = list(existing)
    remaining = [e for e in entries
                 if (e["prompt_id"], e.get("model", e.get("method", ""))) not in done_keys]
    print(f"Remaining to score: {len(remaining)}")

    if not remaining:
        print("All entries already scored!")
        _print_summary(scored)
        return

    print("Getting GCP access token...")
    access_token = get_access_token()

    errors = 0
    for i, entry in enumerate(remaining, 1):
        model = entry.get("model", entry.get("method", "unknown"))
        pid = entry.get("prompt_id", "?")
        print(f"  [{i}/{len(remaining)}] {model} / {pid}...", end="", flush=True)

        generated = entry.get("generated_prompt", "")
        if not generated or len(generated) < 50:
            print(" SKIPPED (no/short output)")
            result = dict(entry)
            result["llama4_scores"] = None
            result["llama4_total"] = 0
            result["llama4_error"] = "no_output"
            scored.append(result)
            continue

        prompt = JUDGE_RUBRIC.format(
            user_prompt=entry.get("user_prompt", ""),
            target_vendor=entry.get("target_vendor", ""),
            target_model=entry.get("target_model", model),
            generated_prompt=generated[:8000],
        )

        try:
            raw = judge_with_llama4(prompt, access_token)
            scores = parse_scores(raw)

            if scores:
                total = sum(scores.values())
                print(f" {total}/50")
                result = dict(entry)
                result["llama4_scores"] = scores
                result["llama4_total"] = total
                scored.append(result)
            else:
                print(f" PARSE FAILED: {raw[:80]}")
                result = dict(entry)
                result["llama4_scores"] = None
                result["llama4_total"] = 0
                result["llama4_error"] = f"parse_failed: {raw[:200]}"
                scored.append(result)
                errors += 1

        except Exception as e:
            print(f" ERROR: {e}")
            result = dict(entry)
            result["llama4_scores"] = None
            result["llama4_total"] = 0
            result["llama4_error"] = str(e)
            scored.append(result)
            errors += 1

            if "401" in str(e) or "403" in str(e):
                print("  Refreshing access token...")
                try:
                    access_token = get_access_token()
                except Exception:
                    pass

        # Save progressively
        OUTPUT_FILE.write_text(json.dumps(scored, indent=2, ensure_ascii=True), encoding="utf-8")
        time.sleep(0.3)

    print(f"\n✅ Re-judged {len(scored)} entries ({errors} errors) -> {OUTPUT_FILE}")
    _print_summary(scored)


def _print_summary(scored: list):
    """Print comparison: Gemini judge vs Llama 4 Maverick judge."""
    print(f"\n{'='*70}")
    print("STUDY B RESULTS: Gemini Judge vs Llama 4 Maverick Judge")
    print(f"{'='*70}")
    print(f"{'Model':<25} {'Gemini (/50)':>12} {'Llama4 (/50)':>12} {'Delta':>8}")
    print("-" * 60)

    models_order = [
        "gemini_3.1_pro", "claude_sonnet_4.5", "qwen3_235b_a22b_base",
        "qwen3_72b_base", "qwen3_32b", "qwen3_14b", "qwen3_30b_a3b",
        "qwen3_8b",
    ]
    for model in models_order:
        model_results = [r for r in scored
                         if r.get("model", r.get("method", "")) == model
                         and r.get("llama4_total", 0) > 0]
        if not model_results:
            continue

        llama4_avg = sum(r["llama4_total"] for r in model_results) / len(model_results)

        # Get Gemini judge score from old 'score' field
        gemini_scores = [r["score"]["total"] for r in model_results
                         if "score" in r and "total" in r.get("score", {})]
        gemini_avg = sum(gemini_scores) / len(gemini_scores) if gemini_scores else 0

        delta = llama4_avg - gemini_avg
        print(f"  {model:<25} {gemini_avg:>8.1f}    {llama4_avg:>8.1f}   {delta:>+6.1f}")

    print(f"{'='*70}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        _print_summary(json.loads(OUTPUT_FILE.read_text(encoding="utf-8")))
    else:
        main()
