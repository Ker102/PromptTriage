#!/usr/bin/env python3
"""
Re-judge Study D v2 Quality benchmark results using Llama 4 Maverick (neutral judge).
Reads the existing quality JSON files (which contain raw model outputs), 
re-scores them with Llama 4, and overwrites the score fields.
"""
import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

current_dir = Path(r"c:\Users\krist\Desktop\Cursor-Projects\Projects\Systempromptfactory\PromptTriage\backend\research\notebooks")
sys.path.append(str(current_dir))

from study_d_prompt_delta import QUALITY_JUDGE_SYSTEM, QUALITY_JUDGE_USER, QUALITY_TASKS, OUTPUT_DIR

# Quality tasks lookup
TASK_LOOKUP = {t["id"]: t["task"] for t in QUALITY_TASKS}


class Llama4JudgeProvider:
    """Llama 4 Maverick (17B-128E MoE) via Vertex AI MaaS HTTP."""
    NAME = "llama_4_maverick"

    def __init__(self):
        self.project_id = os.getenv("VERTEX_PROJECT_ID", "modelsandtraining")
        self.region = "us-east5"
        self.model_name = "meta/llama-4-maverick-17b-128e-instruct-maas"
        self._refresh_token()
        self.url = (
            f"https://{self.region}-aiplatform.googleapis.com/v1beta1/"
            f"projects/{self.project_id}/locations/{self.region}/"
            f"endpoints/openapi/chat/completions"
        )

    def _refresh_token(self):
        result = subprocess.run(
            "gcloud auth print-access-token",
            shell=True, capture_output=True, text=True, check=True
        )
        self.token = result.stdout.strip()

    def generate_json(self, user_msg, system_prompt=None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_msg})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
            "stream": False,
        }

        for attempt in range(3):
            try:
                resp = requests.post(self.url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"]
                elif resp.status_code == 401:
                    print("  [Token expired, refreshing...]")
                    self._refresh_token()
                    headers["Authorization"] = f"Bearer {self.token}"
                else:
                    print(f"    [API Error {attempt+1}]: {resp.status_code} - {resp.text[:120]}")
            except Exception as e:
                print(f"    [Request Error {attempt+1}]: {e}")
            time.sleep(2 ** attempt)
        raise Exception("Llama 4 API failed after 3 attempts")


def parse_scores(raw_text):
    """Parse JSON scores from raw LLM judge output (handling markdown fences)."""
    import re
    text = raw_text.strip()
    # Strip markdown code block if present
    m = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def rejudge_file(judge, filepath):
    """Re-judge a single quality file."""
    print(f"\n{'=' * 60}")
    print(f"  Re-judging: {filepath.name}")
    print(f"{'=' * 60}")

    data = json.loads(filepath.read_text(encoding="utf-8"))

    for idx, item in enumerate(data, 1):
        task_id = item.get("task_id", f"q{item['problem_idx']+1:02d}")
        model_output = item["output"]
        task_text = TASK_LOOKUP.get(task_id, "")

        if not task_text:
            print(f"  [{idx}/{len(data)}] Skipping {task_id} (task not found)")
            continue

        user_msg = QUALITY_JUDGE_USER.format(task=task_text, response=model_output)
        print(f"  [{idx}/{len(data)}] {task_id}...", end="", flush=True)

        try:
            raw_json = judge.generate_json(user_msg, system_prompt=QUALITY_JUDGE_SYSTEM)
            scores = parse_scores(raw_json)

            dims = ["instruction_adherence", "content_quality", "organization", "conciseness"]
            for d in dims:
                scores[d] = max(1, min(10, int(scores.get(d, 5))))
            scores["total"] = sum(scores[d] for d in dims)

            print(f" {scores['total']}/40")

        except Exception as e:
            print(f" ERROR: {e}")
            scores = {
                "instruction_adherence": 0, "content_quality": 0,
                "organization": 0, "conciseness": 0, "total": 0,
                "reasoning": f"Llama judge error: {e}"
            }

        item["scores"] = scores
        item["judge_model"] = "llama_4_maverick"

    # Save the file once all items are done (avoid partial save issues)
    json_str = json.dumps(data, indent=2, ensure_ascii=True)
    with open(str(filepath), "w", encoding="utf-8") as f:
        f.write(json_str)
    print(f"  Saved {filepath.name}")
    return data


def main():
    judge = Llama4JudgeProvider()

    quality_files = sorted(OUTPUT_DIR.glob("study_d_*_quality_*.json"))
    print(f"Found {len(quality_files)} quality files to re-judge.\n")

    all_results = {}
    for qf in quality_files:
        data = rejudge_file(judge, qf)
        all_results[qf.name] = data

    # Print summary
    print("\n\n" + "=" * 60)
    print("  QUALITY RE-JUDGE SUMMARY (Llama 4 Maverick)")
    print("=" * 60)
    print(f"  {'Model':<22} {'Cond':<15} {'Total':>6}  Instr  Qual   Org  Conc")
    print(f"  {'─'*22} {'─'*15} {'─'*6}  {'─'*5} {'─'*5} {'─'*5} {'─'*5}")

    for qf in quality_files:
        parts = qf.stem.replace("study_d_", "").split("_quality_")
        if len(parts) != 2:
            continue
        model_name, condition = parts
        data = json.loads(qf.read_text(encoding="utf-8"))
        dims = ["instruction_adherence", "content_quality", "organization", "conciseness"]
        avgs = {}
        for d in dims:
            vals = [r["scores"].get(d, 0) for r in data if "scores" in r]
            avgs[d] = sum(vals) / len(vals) if vals else 0
        avg_total = sum(avgs.values())
        print(f"  {model_name:<22} {condition:<15} {avg_total:>5.1f}  "
              f"{avgs['instruction_adherence']:>5.1f} {avgs['content_quality']:>5.1f} "
              f"{avgs['organization']:>5.1f} {avgs['conciseness']:>5.1f}")

    print()


if __name__ == "__main__":
    main()
