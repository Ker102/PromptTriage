"""
Study C Rejudge Script — 3-Model Jury (same as Study E v2)

Judges: Llama 4 Maverick (GCP), Claude Opus 4.6 (Anthropic Vertex), Atla Selene Mini (HuggingFace)
Scoring: Median across 3 judges on 4 dimensions (task_completion, quality, format_adherence, conciseness)

This reads the existing study_c_results.json, rejudges only entries with valid downstream_output,
and writes results to study_c_rejudged.json.
"""
import json, os, re, sys, time, statistics
from pathlib import Path
import requests
import google.auth
import google.auth.transport.requests
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent / "../../backend/.env")

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE = Path(__file__).parent / "named-outputs/study_c"
INPUT_FILE = BASE / "study_c_results.json"
OUTPUT_FILE = BASE / "study_c_rejudged.json"

# ── Rubric (same as Study E v2) ──
RUBRIC = """Score this AI-generated response on 4 dimensions (1-10 each).

DOWNSTREAM TASK: "{task_text}"

AI GENERATED OUTPUT:
---
{generated_output}
---

Dimensions:
1. task_completion (1-10): Did it fully answer the prompt and satisfy all requirements?
2. quality (1-10): Is the code/writing/analysis professionally accurate and optimal?
3. format_adherence (1-10): Did it follow structural/formatting instructions naturally?
4. conciseness (1-10): Is it appropriately concise without losing substance?

Respond with ONLY this exact JSON object:
{{"task_completion": N, "quality": N, "format_adherence": N, "conciseness": N}}"""


# ── Parse Helper ──
def parse_judge(raw: str) -> dict:
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
    try:
        d = json.loads(raw)
        if all(k in d for k in ['task_completion', 'quality', 'format_adherence', 'conciseness']):
            return d
    except:
        pass
    m = re.search(r'\{[^{}]*"task_completion"[^{}]*\}', raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    return {"parse_error": raw[:100]}


# ── Judge 1: Llama 4 Maverick (GCP Vertex) ──
def get_gcp_token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

def judge_llama_maverick(prompt: str, token: str) -> dict:
    url = "https://us-east5-aiplatform.googleapis.com/v1/projects/modelsandtraining/locations/us-east5/endpoints/openapi/chat/completions"
    try:
        r = requests.post(url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"model": "meta/llama-4-maverick-17b-128e-instruct-maas",
                  "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.0},
            timeout=60)
        return parse_judge(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return {"parse_error": f"Llama Error: {e}"}


# ── Judge 2: Claude Opus 4.6 (Anthropic Vertex) ──
def judge_claude_opus(prompt: str) -> dict:
    from anthropic import AnthropicVertex
    try:
        client = AnthropicVertex(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "modelsandtraining"),
            region="us-east5"
        )
        raw = client.messages.create(
            model="claude-opus-4-6@default",
            max_tokens=200, temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text
        return parse_judge(raw)
    except Exception as e:
        return {"parse_error": f"Opus Error: {e}"}


# ── Judge 3: Atla Selene Mini (HuggingFace) ──
def judge_atla_selene(prompt: str) -> dict:
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}", "Content-Type": "application/json"}
    try:
        r = requests.post(
            "https://api-inference.huggingface.co/models/AtlaAI/Selene-1-Mini-Llama-3.1-8B",
            headers=headers,
            json={"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.01}},
            timeout=60)
        if r.status_code == 200:
            raw = r.json()[0].get('generated_text', '').replace(prompt, '')
            return parse_judge(raw)
        return {"parse_error": f"Selene HTTP {r.status_code}"}
    except Exception as e:
        return {"parse_error": f"Selene Error: {e}"}


# ── 3-Judge Jury ──
def run_jury(task_text: str, generated_output: str, gcp_token: str) -> dict:
    prompt = RUBRIC.format(task_text=task_text, generated_output=generated_output[:6000])

    j1 = judge_llama_maverick(prompt, gcp_token)
    j2 = judge_claude_opus(prompt)
    j3 = judge_atla_selene(prompt)

    final_scores = {}
    dims = ['task_completion', 'quality', 'format_adherence', 'conciseness']

    for d in dims:
        vals = []
        for j in [j1, j2, j3]:
            if d in j and isinstance(j[d], (int, float)):
                vals.append(j[d])
        final_scores[d] = statistics.median(vals) if vals else 0

    total = sum(final_scores.values())

    return {
        "final_scores": final_scores,
        "total_median_score": total,
        "raw_judgments": {
            "llama": j1,
            "opus": j2,
            "selene": j3
        }
    }


# ── Main ──
def main():
    print("=" * 60)
    print("STUDY C REJUDGE — 3 Model Jury")
    print("=" * 60)

    data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    valid = [r for r in data if r.get('downstream_output', '').strip()
             and not r.get('downstream_output', '').startswith('[ERROR')]

    print(f"Total entries: {len(data)}")
    print(f"Valid outputs to rejudge: {len(valid)}")
    print()

    # Load existing rejudged results for resume
    done_keys = set()
    results = []
    if OUTPUT_FILE.exists():
        results = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        done_keys = {(r["task_id"], r["model"], r["condition"]) for r in results}
        print(f"Resuming: {len(results)} already rejudged")

    # Get GCP token
    print("Getting GCP token...")
    token = get_gcp_token()
    token_refresh = time.time()

    errors = 0
    for i, entry in enumerate(valid):
        key = (entry["task_id"], entry["model"], entry["condition"])
        if key in done_keys:
            continue

        # Refresh GCP token every 45 minutes
        if time.time() - token_refresh > 2700:
            print("  Refreshing GCP token...")
            token = get_gcp_token()
            token_refresh = time.time()

        task_text = entry.get("task_id", "Unknown task")
        output = entry["downstream_output"]

        print(f"[{len(results)+1}/{len(valid)}] {entry['task_id']} | {entry['condition']} | {entry['model']}", end="  ")

        try:
            jury = run_jury(task_text, output, token)
            print(f"Score: {jury['total_median_score']:.1f}/40")

            result = {
                "task_id": entry["task_id"],
                "domain": entry.get("domain", "unknown"),
                "model": entry["model"],
                "condition": entry["condition"],
                "latency_s": entry.get("latency_s", 0),
                "word_count": entry.get("word_count", 0),
                "jury": jury,
                "total_score": jury["total_median_score"],
                "scores": jury["final_scores"],
                "downstream_output": output[:2000],  # Keep truncated for reference
            }
            results.append(result)
            done_keys.add(key)

            # Save after every entry
            OUTPUT_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

        except Exception as e:
            print(f"ERROR: {e}")
            errors += 1

        time.sleep(1)  # Rate limiting

    print(f"\n{'=' * 60}")
    print(f"DONE: {len(results)}/{len(valid)} rejudged, {errors} errors")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
