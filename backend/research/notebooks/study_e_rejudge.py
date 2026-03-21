#!/usr/bin/env python3
"""
Study E — Re-judge & Retry Script

Fixes two issues from the initial run:
1. Re-judges all 90 Gemini outputs using Llama 4 Maverick (Qwen judge returned empty)
2. Re-generates and re-judges the 4 failed Llama outputs
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
RESULTS_FILE = OUTPUT_DIR / "study_e_results.json"

DOWNSTREAM_TASKS = {
    "e-code-01": "Write a Python function to merge two sorted lists efficiently. It should handle empty lists and duplicates.",
    "e-write-01": "Draft a 3-paragraph product description for a smart home security camera. Focus on night vision, AI alerts, and privacy.",
    "e-analy-01": "Summarize the pros and cons of microservices architecture compared to a monolithic approach.",
    "e-code-02": "Create a SQL query to find the top 10 customers by total revenue. You have two tables: `customers` (id, name) and `orders` (id, customer_id, amount).",
    "e-qa-01": "Write test cases for a login form. Include both the happy path and critical security edge cases."
}

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

def get_vertex_token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

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
    return {"parse_error": raw[:200]}

def judge_with_llama(task_text: str, generated_output: str, access_token: str) -> dict:
    prompt = RUBRIC.format(task_text=task_text, generated_output=generated_output[:6000])
    url = "https://us-east5-aiplatform.googleapis.com/v1/projects/modelsandtraining/locations/us-east5/endpoints/openapi/chat/completions"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "model": "meta/llama-4-maverick-17b-128e-instruct-maas",
        "max_tokens": 150,
        "temperature": 0.0,
        "messages": [
            {"role": "system", "content": "You are a JSON-only scoring API. Respond ONLY with exactly 4 integer scores in JSON format."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        return parse_judge_json(raw)
    except Exception as e:
        return {"parse_error": str(e)}

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

def judge_with_gemini(task_text: str, generated_output: str) -> dict:
    prompt = RUBRIC.format(task_text=task_text, generated_output=generated_output[:6000])
    from google import genai
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


def main():
    data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    prompts = get_study_e_prompts()
    
    print("Getting GCP token...")
    token = get_vertex_token()
    
    # --- Fix 1: Re-judge Gemini outputs with Llama 4 Maverick ---
    gemini_errs = [i for i, r in enumerate(data) if r['model'] == 'gemini_3.1_pro' and 'parse_error' in r.get('scores', {})]
    print(f"\n=== RE-JUDGING {len(gemini_errs)} GEMINI OUTPUTS WITH LLAMA 4 MAVERICK ===")
    
    fixed_judge = 0
    for idx in gemini_errs:
        r = data[idx]
        task_text = DOWNSTREAM_TASKS.get(r['task_id'], '')
        output = r.get('downstream_output', '')
        
        if not output or output.startswith('[ERROR:'):
            continue
            
        print(f"  [{r['task_id']}] {r['length']}/{r['format']}... ", end="", flush=True)
        scores = judge_with_llama(task_text, output, token)
        
        if 'parse_error' not in scores:
            total = sum(scores.values())
            data[idx]['scores'] = scores
            data[idx]['total_score'] = total
            data[idx]['judge'] = 'llama_4_maverick'  # Track which judge was used
            fixed_judge += 1
            print(f"Score: {total}/40")
        else:
            print(f"Still failed: {str(scores)[:60]}")
        
        time.sleep(0.5)
    
    print(f"\nFixed {fixed_judge}/{len(gemini_errs)} Gemini judge errors")
    
    # --- Fix 2: Re-generate failed Llama outputs ---
    llama_fails = [i for i, r in enumerate(data) if r['model'] == 'llama_4_maverick' and (r.get('error') or r.get('word_count', 0) < 20)]
    print(f"\n=== RE-GENERATING {len(llama_fails)} FAILED LLAMA OUTPUTS ===")
    
    fixed_gen = 0
    for idx in llama_fails:
        r = data[idx]
        task_text = DOWNSTREAM_TASKS.get(r['task_id'], '')
        sys_prompt = prompts[r['length']][r['format']]
        
        print(f"  [{r['task_id']}] {r['length']}/{r['format']}... ", end="", flush=True)
        generated = run_llama_vertex(sys_prompt, task_text, token)
        words = len(generated.split())
        
        if generated.startswith('[ERROR:') or words < 20:
            print(f"Still failed ({words}w)")
            continue
        
        print(f"Gen: {words}w... ", end="", flush=True)
        
        # Judge with Gemini (since it's Llama output)
        scores = judge_with_gemini(task_text, generated)
        
        if 'parse_error' not in scores:
            total = sum(scores.values())
            data[idx]['downstream_output'] = generated
            data[idx]['word_count'] = words
            data[idx]['scores'] = scores
            data[idx]['total_score'] = total
            data[idx].pop('error', None)
            fixed_gen += 1
            print(f"Score: {total}/40")
        else:
            print(f"Judge failed: {str(scores)[:60]}")
        
        time.sleep(1)
    
    print(f"\nFixed {fixed_gen}/{len(llama_fails)} Llama gen failures")
    
    # Save
    RESULTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults saved to {RESULTS_FILE}")
    
    # Quick summary
    valid = [r for r in data if r.get('total_score', 0) > 0]
    print(f"\nFinal: {len(valid)}/360 valid scores")

if __name__ == "__main__":
    main()
