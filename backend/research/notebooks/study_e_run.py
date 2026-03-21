#!/usr/bin/env python3
"""
Study E — Format Wars

Determines whether system prompt format, length, and structure genuinely affect 
model output quality across 4 different models.
"""
import os
import sys
import json
import time
from pathlib import Path
import re
import requests
import google.auth
import google.auth.transport.requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dotenv import load_dotenv
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
load_dotenv(os.path.join(project_root, 'backend', '.env'))

from study_e_prompts import get_study_e_prompts

OUTPUT_DIR = Path(__file__).parent / "named-outputs" / "study_e"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. The 5 Downstream Tasks ──
DOWNSTREAM_TASKS = [
    {
        "id": "e-code-01", "domain": "code",
        "task": "Write a Python function to merge two sorted lists efficiently. It should handle empty lists and duplicates."
    },
    {
        "id": "e-write-01", "domain": "writing",
        "task": "Draft a 3-paragraph product description for a smart home security camera. Focus on night vision, AI alerts, and privacy."
    },
    {
        "id": "e-analy-01", "domain": "analysis",
        "task": "Summarize the pros and cons of microservices architecture compared to a monolithic approach."
    },
    {
        "id": "e-code-02", "domain": "code",
        "task": "Create a SQL query to find the top 10 customers by total revenue. You have two tables: `customers` (id, name) and `orders` (id, customer_id, amount)."
    },
    {
        "id": "e-qa-01", "domain": "qa",
        "task": "Write test cases for a login form. Include both the happy path and critical security edge cases."
    }
]

# ── 2. Model Runners ──

def run_gemini(system_prompt: str, user_prompt: str) -> str:
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    config = {"temperature": 0.3, "max_output_tokens": 4000}
    if system_prompt:
        config["system_instruction"] = system_prompt
        
    try:
        resp = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=user_prompt,
            config=config
        )
        return resp.text
    except Exception as e:
        return f"[ERROR: {e}]"

def run_claude(system_prompt: str, user_prompt: str) -> str:
    from anthropic import AnthropicVertex
    region = "us-east5"
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "modelsandtraining")
    
    try:
        client = AnthropicVertex(project_id=project_id, region=region)
        kwargs = {
            "model": "claude-sonnet-4-6@default", # Correct Vertex model name
            "max_tokens": 4000,
            "temperature": 0.3,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        if system_prompt:
            kwargs["system"] = system_prompt
            
        resp = client.messages.create(**kwargs)
        return resp.content[0].text
    except Exception as e:
        return f"[ERROR: {e}]"

def get_vertex_token():
    creds, proj = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

def run_llama_vertex(system_prompt: str, user_prompt: str, access_token: str) -> str:
    url = "https://us-east5-aiplatform.googleapis.com/v1/projects/modelsandtraining/locations/us-east5/endpoints/openapi/chat/completions"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
        
    payload = {
        "model": "meta/llama-4-maverick-17b-128e-instruct-maas",
        "max_tokens": 4000,
        "temperature": 0.3,
        "messages": messages
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[ERROR: {e}]"

def run_qwen_together(system_prompt: str, user_prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}",
        "Content-Type": "application/json",
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
        
    payload = {
        "model": "Qwen/Qwen3.5-397B-A17B",
        "max_tokens": 4000,
        "temperature": 0.3,
        "messages": messages,
    }
    
    try:
        resp = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[ERROR: {e}]"


# ── 3. Cross-Model Judges ──

RUBRIC = """Score this AI-generated response on 4 dimensions (1-10 each).

DOWNSTREAM TASK:
"{task_text}"

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

def parse_judge_json(raw: str) -> dict:
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
    try:
        d = json.loads(raw)
        if all(k in d for k in ['task_completion', 'quality', 'format_adherence', 'conciseness']):
            return d
    except: pass
    
    m = re.search(r'\{[^{}]*"task_completion"[^{}]*\}', raw, re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
            
    return {"parse_error": raw[:100]}

def judge_with_gemini(task_def: dict, generated_output: str) -> dict:
    prompt = RUBRIC.format(task_text=task_def['task'], generated_output=generated_output[:6000])
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    try:
        resp = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            config={"temperature": 0.0, "response_mime_type": "application/json"}
        )
        return parse_judge_json(resp.text)
    except Exception as e:
        return {"parse_error": str(e)}

def judge_with_qwen(task_def: dict, generated_output: str) -> dict:
    prompt = RUBRIC.format(task_text=task_def['task'], generated_output=generated_output[:6000])
    headers = {
        "Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen3.5-397B-A17B",
        "max_tokens": 150,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "You are a JSON-only scoring API. Respond ONLY with exactly 4 integer scores in JSON format."},
            {"role": "user", "content": prompt}
        ],
    }
    try:
        resp = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        return parse_judge_json(raw)
    except Exception as e:
        return {"parse_error": str(e)}


# ── Main Loop ──
def main():
    out_file = OUTPUT_DIR / "study_e_results.json"
    existing = []
    done_keys = set()
    if out_file.exists():
        existing = json.loads(out_file.read_text(encoding="utf-8"))
        done_keys = {(r["task_id"], r["model"], r["length"], r["format"]) for r in existing}
        print(f"Resuming {len(existing)} completed evals")
        
    results = list(existing)
    prompts = get_study_e_prompts()
    
    print("Getting GCP token...")
    token = get_vertex_token()
    token_last_refresh = time.time()
    
    models = ["qwen_397b", "llama_4_maverick", "gemini_3.1_pro", "claude_sonnet_4.6"]
    lengths = ["short", "medium", "long"]
    formats = ["text", "markdown", "xml", "json", "yaml", "hybrid"]
    
    total_evals = len(DOWNSTREAM_TASKS) * len(models) * len(lengths) * len(formats)
    completed = len(done_keys)
    print(f"Goal: {total_evals} evaluations ({completed} already done)")

    for task in DOWNSTREAM_TASKS:
        for m in models:
            for l in lengths:
                for f in formats:
                    key = (task["id"], m, l, f)
                    if key in done_keys:
                        continue
                        
                    print(f"[{task['id']}] {m} @ {l}/{f}... ", end="", flush=True)
                    sys_prompt = prompts[l][f]
                    
                    if time.time() - token_last_refresh > 1800: # 30 mins
                        token = get_vertex_token()
                        token_last_refresh = time.time()
                    
                    # 1. Run Generation
                    t0 = time.time()
                    generated = ""
                    if m == "gemini_3.1_pro":
                        generated = run_gemini(sys_prompt, task["task"])
                    elif m == "claude_sonnet_4.6":
                        generated = run_claude(sys_prompt, task["task"])
                    elif m == "llama_4_maverick":
                        generated = run_llama_vertex(sys_prompt, task["task"], token)
                    elif m == "qwen_397b":
                        generated = run_qwen_together(sys_prompt, task["task"])
                        
                    lat = time.time() - t0
                    words = len(generated.split())
                    print(f"Gen: {words}w ({lat:.1f}s)... ", end="", flush=True)
                    
                    if generated.startswith("[ERROR:"):
                        print("Failed.")
                        results.append({
                            "task_id": task["id"], "model": m, "length": l, "format": f,
                            "downstream_output": generated, "latency_s": round(lat, 1),
                            "word_count": words, "scores": {}, "total_score": 0, "error": generated
                        })
                        continue
                        
                    # 2. Cross-Model Judging
                    # Gemini is judged by Qwen. Everyone else is judged by Gemini.
                    scores = {}
                    if m == "gemini_3.1_pro":
                        scores = judge_with_qwen(task, generated)
                    else:
                        scores = judge_with_gemini(task, generated)
                        
                    total_score = 0
                    if "parse_error" not in scores:
                        total_score = sum(scores.values())
                        print(f"Score: {total_score}/40")
                    else:
                        print("Score: ERROR")
                        
                    # 3. Save
                    results.append({
                        "task_id": task["id"], "domain": task["domain"],
                        "model": m, "length": l, "format": f,
                        "downstream_output": generated, "latency_s": round(lat, 1),
                        "word_count": words, "scores": scores, "total_score": total_score
                    })
                    
                    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
                    time.sleep(1) # General rate limit pacing
                    
    print("\n\nAll generation complete! Run analysis script for final numbers.")

if __name__ == "__main__":
    main()
