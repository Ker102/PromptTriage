#!/usr/bin/env python3
"""
Study E v2 — Format Wars Expanded

Evaluates 5 test models against 12 diverse tasks using 18 prompt variants.
All outputs are judged by a 3-Model Jury (Llama 4 Maverick, Claude Opus 4.6, Atla Selene Mini)
with zero overlap between test models and judge models.
"""
import os, sys, json, time, re, requests
import statistics
from pathlib import Path
import google.auth
import google.auth.transport.requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dotenv import load_dotenv
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
load_dotenv(os.path.join(project_root, 'backend', '.env'))

from study_e_prompts import get_study_e_prompts

OUTPUT_DIR = Path(__file__).parent / "named-outputs" / "study_e_v2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. The 12 Diverse Tasks ──
DOWNSTREAM_TASKS = [
    {"id": "e-code-01", "domain": "code", "task": "Write a Python function to merge two sorted lists efficiently. It should handle empty lists and duplicates."},
    {"id": "e-code-02", "domain": "code", "task": "Create a SQL query to find the top 10 customers by total revenue. You have two tables: `customers` (id, name) and `orders` (id, customer_id, amount)."},
    {"id": "e-code-03", "domain": "code", "task": "I have a recursive flatten logic that is throwing maximum recursion depth exceeded. Write a robust iterative `flatten(nested_list)` function in Python."},
    {"id": "e-write-01", "domain": "writing", "task": "Draft a 3-paragraph product description for a smart home security camera. Focus on night vision, AI alerts, and privacy."},
    {"id": "e-write-02", "domain": "writing", "task": "Write a professional email to a client explaining that their project delivery will be delayed by one week due to unexpected API integration issues."},
    {"id": "e-write-03", "domain": "writing", "task": "Write a creative 200-word opening scene for a sci-fi novel where characters discover a frozen ocean on a desert planet."},
    {"id": "e-analy-01", "domain": "analysis", "task": "Summarize the pros and cons of microservices architecture compared to a monolithic approach."},
    {"id": "e-analy-02", "domain": "analysis", "task": "Provide a brief quarterly business review summary based on these data points: Q1 Revenue $1.2M (up 15%), Churn 2% (down from 4%), CAC $400 (up 10%)."},
    {"id": "e-qa-01", "domain": "qa", "task": "Write test cases for a login form. Include both the happy path and critical security edge cases."},
    {"id": "e-extract-01", "domain": "extraction", "task": "Extract the names, roles, and companies from this text into JSON: 'Jane Doe is the CTO at Innotech. She recently hired John Smith, a brilliant Lead Engineer from GlobalCorp.'"},
    {"id": "e-math-01", "domain": "math", "task": "A store offers a 20% discount on a $150 item. After the discount, a 5% tax is applied. Later, the customer uses a $10 coupon. What is the final price? Show your work step-by-step."},
    {"id": "e-instruct-01", "domain": "instruction", "task": "List exactly 4 tips for better sleep. Use bullet points. Each bullet point MUST start with a strong verb. Do not include any introductory or concluding text."}
]

# ── 2. Test Model Generators ──

def run_gemini(system: str, user: str) -> str:
    from google import genai
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    config = {"temperature": 0.3, "max_output_tokens": 4000}
    if system: config["system_instruction"] = system
    try:
        resp = client.models.generate_content(model="gemini-3.1-pro-preview", contents=user, config=config)
        return resp.text
    except Exception as e: return f"[ERROR: {e}]"

def run_claude_sonnet(system: str, user: str) -> str:
    from anthropic import AnthropicVertex
    try:
        client = AnthropicVertex(project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "modelsandtraining"), region="us-east5")
        kwargs = {"model": "claude-sonnet-4-6@default", "max_tokens": 4000, "temperature": 0.3, "messages": [{"role": "user", "content": user}]}
        if system: kwargs["system"] = system
        return client.messages.create(**kwargs).content[0].text
    except Exception as e: return f"[ERROR: {e}]"

def run_qwen(system: str, user: str) -> str:
    headers = {"Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}", "Content-Type": "application/json"}
    messages = []
    if system: messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    try:
        r = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json={"model": "Qwen/Qwen3.5-397B-A17B", "messages": messages, "max_tokens": 4000, "temperature": 0.3}, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e: return f"[ERROR: {e}]"

def run_nemotron(system: str, user: str) -> str:
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    messages = []
    if system: messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                          json={"model": "nvidia/nemotron-3-super-120b-a12b", "messages": messages, "max_tokens": 4000, "temperature": 0.3}, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e: return f"[ERROR: {e}]"

def run_gpt54(system: str, user: str) -> str:
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    messages = []
    if system: messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                          json={"model": "openai/gpt-5.4", "messages": messages, "max_tokens": 4000, "temperature": 0.3}, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e: return f"[ERROR: {e}]"


# ── 3. The 3-Model Jury ──
def get_gcp_token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

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

def parse_judge(raw: str) -> dict:
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
    try:
        d = json.loads(raw)
        if all(k in d for k in ['task_completion', 'quality', 'format_adherence', 'conciseness']): return d
    except: pass
    m = re.search(r'\{[^{}]*"task_completion"[^{}]*\}', raw, re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
    return {"parse_error": raw[:100]}

def judge_llama_maverick(prompt: str, token: str) -> dict:
    url = "https://us-east5-aiplatform.googleapis.com/v1/projects/modelsandtraining/locations/us-east5/endpoints/openapi/chat/completions"
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                          json={"model": "meta/llama-4-maverick-17b-128e-instruct-maas", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}, timeout=60)
        return parse_judge(r.json()["choices"][0]["message"]["content"])
    except Exception as e: return {"parse_error": f"Llama Error: {e}"}

def judge_claude_opus(prompt: str) -> dict:
    from anthropic import AnthropicVertex
    try:
        client = AnthropicVertex(project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "modelsandtraining"), region="us-east5")
        raw = client.messages.create(model="claude-opus-4-6@default", max_tokens=200, temperature=0.0, messages=[{"role": "user", "content": prompt}]).content[0].text
        return parse_judge(raw)
    except Exception as e: return {"parse_error": f"Opus Error: {e}"}

def judge_atla_selene(prompt: str) -> dict:
    # Use HF Inference endpoint
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}", "Content-Type": "application/json"}
    try:
        r = requests.post("https://api-inference.huggingface.co/models/AtlaAI/Selene-1-Mini-Llama-3.1-8B", 
                          headers=headers, json={"inputs": prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.01}}, timeout=60)
        # Handle HF weirdness
        if r.status_code == 200:
            raw = r.json()[0].get('generated_text', '').replace(prompt, '')
            return parse_judge(raw)
        return {"parse_error": f"Selene HTTP {r.status_code}"}
    except Exception as e: return {"parse_error": f"Selene Error: {e}"}

def run_jury(task_text: str, generated_output: str, gcp_token: str) -> dict:
    prompt = RUBRIC.format(task_text=task_text, generated_output=generated_output[:6000])
    
    # 3 Judges
    j1 = judge_llama_maverick(prompt, gcp_token)
    j2 = judge_claude_opus(prompt)
    j3 = judge_atla_selene(prompt)
    
    # Median scoring logic
    final_scores = {}
    dims = ['task_completion', 'quality', 'format_adherence', 'conciseness']
    
    for d in dims:
        vals = []
        for j in [j1, j2, j3]:
            if d in j and isinstance(j[d], (int, float)):
                vals.append(j[d])
        if len(vals) > 0:
            final_scores[d] = statistics.median(vals)
        else:
            final_scores[d] = 0
            
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


# ── Main Loop ──
def main():
    out_file = OUTPUT_DIR / "study_e_v2_results.json"
    existing = []
    done_keys = set()
    if out_file.exists():
        existing = json.loads(out_file.read_text(encoding="utf-8"))
        done_keys = {(r["task_id"], r["model"], r["length"], r["format"]) for r in existing}
        print(f"Resuming {len(existing)} completed evals")
        
    results = list(existing)
    prompts = get_study_e_prompts() # Using the 18 variants
    
    print("Getting GCP token...")
    token = get_gcp_token()
    token_last_refresh = time.time()
    
    # Starting Phase 1 models
    models = ["qwen_397b", "gemini_3.1_pro", "claude_sonnet_4.6", "nemotron_120b", "gpt_5.4"]
    
    lengths = ["short", "medium", "long"]
    formats = ["text", "markdown", "xml", "json", "yaml", "hybrid"]
    
    total_evals = len(DOWNSTREAM_TASKS) * len(models) * len(lengths) * len(formats)
    completed = sum(1 for (t_id, m, l, f) in done_keys if m in models)
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
                        token = get_gcp_token()
                        token_last_refresh = time.time()
                    
                    # 1. Generate
                    t0 = time.time()
                    generated = ""
                    if m == "gemini_3.1_pro": generated = run_gemini(sys_prompt, task["task"])
                    elif m == "claude_sonnet_4.6": generated = run_claude_sonnet(sys_prompt, task["task"])
                    elif m == "qwen_397b": generated = run_qwen(sys_prompt, task["task"])
                    elif m == "nemotron_120b": generated = run_nemotron(sys_prompt, task["task"])
                    elif m == "gpt_5.4": generated = run_gpt54(sys_prompt, task["task"])
                        
                    lat = time.time() - t0
                    words = len(generated.split())
                    print(f"Gen: {words}w ({lat:.1f}s)... ", end="", flush=True)
                    
                    if generated.startswith("[ERROR:"):
                        print("Failed.")
                        results.append({
                            "task_id": task["id"], "domain": task["domain"], "model": m, "length": l, "format": f,
                            "downstream_output": generated, "latency_s": round(lat, 1),
                            "word_count": words, "jury": {}, "total_score": 0, "error": generated
                        })
                        continue
                        
                    # 2. Jury Judging
                    jury_result = run_jury(task["task"], generated, token)
                    print(f"Jury Score: {jury_result['total_median_score']:.1f}/40")
                        
                    # 3. Save
                    results.append({
                        "task_id": task["id"], "domain": task["domain"],
                        "model": m, "length": l, "format": f,
                        "downstream_output": generated, "latency_s": round(lat, 1),
                        "word_count": words, 
                        "jury": jury_result, 
                        "total_score": jury_result['total_median_score']
                    })
                    
                    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
                    time.sleep(1)
                    
    print("\n\nAll generation complete!")

if __name__ == "__main__":
    main()
