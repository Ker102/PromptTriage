"""
Study C v2 — The Complex Task Frontier
Evaluates prompt engineering ROI on routine vs complex/biased tasks.

Pipeline:
1. Generate conditions (bare, simple, expert, prompttriage)
2. Run downstream on Gemini 3.1 Pro & Nemotron 3 Super
3. Judge via Llama 4 Maverick + Claude Opus + GPT-5.4 (Median of 3)
"""
import os, sys, json, time, re, requests, statistics
from pathlib import Path
import google.auth
import google.auth.transport.requests
from google import genai

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dotenv import load_dotenv
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
load_dotenv(os.path.join(project_root, 'backend', '.env'))

OUTPUT_DIR = Path(__file__).parent / "named-outputs" / "study_c_v2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 1. The 13 Hard Downstream Tasks ──
DOWNSTREAM_TASKS = [
    # Category 1: Formatting/Constraints
    {
        "id": "c2-fmt-01", "domain": "formatting",
        "task": "Extract all dates and events from this text into a strict JSON array. Format: [{'date': 'YYYY-MM-DD', 'event': 'string'}]. Text: 'On Jan 5, 2024, the rocket launched. Two weeks later on January 19th, it reached orbit.' Output ONLY valid JSON, no markdown fences, no conversational text.",
        "expert_prompt": "You are a rigid data pipeline extraction bot. You output pure, raw JSON that is strictly parsable by json.loads(). You never use markdown code blocks (```). You never add conversational filler."
    },
    {
        "id": "c2-fmt-02", "domain": "formatting",
        "task": "Write a poem about the ocean in exactly 14 lines, where every line has exactly 8 syllables. Do not output anything else.",
        "expert_prompt": "You are a master poet specializing in strict meter and constrained writing. You meticulously count syllables to ensure perfect adherence to structural constraints."
    },
    {
        "id": "c2-fmt-03", "domain": "formatting",
        "task": "Summarize the history of Rome in exactly three sentences, no more, no less. Each sentence must start with the letter 'R'.",
        "expert_prompt": "You are a constrained writing assistant. You follow exact instructions regarding sentence counts, word counts, and starting letters. You verify your output before responding."
    },
    # Category 2: Reasoning/Logic
    {
        "id": "c2-rsn-01", "domain": "reasoning",
        "task": "A farmer has 17 sheep, and all but 9 die. How many are left? Think step by step, but the final answer must be a single number on the final line.",
        "expert_prompt": "You are an expert logician. You recognize common trick questions and semantic traps. You methodically break down the logic step by step, never jumping to conclusions, and format your final answer precisely as requested."
    },
    {
        "id": "c2-rsn-02", "domain": "reasoning",
        "task": "Solve this scheduling problem: Alice can't meet on Mondays. Bob is only free after 2 PM. Charlie is in GMT+8 and can't meet past 5 PM his time. Alice and Bob are in EST (GMT-5). What's the earliest 1-hour slot next week they can all meet? Provide the final answer in EST.",
        "expert_prompt": "You are an executive assistant AI specialized in complex timezone logistics. You meticulously convert all constraints into a single timezone baseline, check overlap conditions, and find the optimal solution without making assumptions."
    },
    {
        "id": "c2-rsn-03", "domain": "reasoning",
        "task": "There are three boxes: Red, Green, and Blue. One contains gold. The Red box says 'Gold is not here'. The Green box says 'Gold is here'. The Blue box says 'Gold is not in the Red box'. Only one statement is true. Where is the gold?",
        "expert_prompt": "You are a master of discrete mathematics and boolean logic. You test every possible hypothesis systematically against the constraints to prove which configuration is valid."
    },
    {
        "id": "c2-rsn-04", "domain": "reasoning",
        "task": "Plan a 3-day itinerary in Tokyo. Constraint: You cannot suggest any location that contains the letter 'a' (case-insensitive) in its English name.",
        "expert_prompt": "You are a highly capable travel planner capable of operating under bizarre constraints. You verify every single recommendation against the negative constraints before writing it."
    },
    # Category 3: Persona/Context
    {
        "id": "c2-per-01", "domain": "persona",
        "task": "Explain quantum computing to a 5-year-old, but you are a disgruntled pirate who hates modern technology.",
        "expert_prompt": "You fully embody requested personas, no matter how contradictory or strange. You never break character. Your tone, vocabulary, and analogies stem purely from the persona's worldview."
    },
    {
        "id": "c2-per-02", "domain": "persona",
        "task": "Write an email to an employee terminating their contract. You are a highly empathetic but strictly legally compliant HR director.",
        "expert_prompt": "You are a veteran HR professional. You write termination copy that carefully balances legal risk mitigation (no admitting fault, clear terms) with profound human empathy and dignity."
    },
    {
        "id": "c2-per-03", "domain": "persona",
        "task": "Critique the design of a modern smartphone. You are a 19th-century Victorian clockmaker obsessed with gears and physical mechanics.",
        "expert_prompt": "Adopt the persona flawlessly. View the modern world entirely through the paradigm of mechanical engineering, brass, gears, and craftsmanship. Ignore modern concepts you wouldn't understand."
    },
    # Category 4: Code Defaults (testing if they can escape bias)
    {
        "id": "c2-def-01", "domain": "code_defaults",
        "task": "Write HTML/CSS for a pricing dashboard. Do NOT use dark mode. Use a stark white background. Do NOT use gradients, rounded corners, or drop shadows. Use harsh black borders and monospaced fonts. Do NOT use any external CSS frameworks.",
        "expert_prompt": "You are a brutalist web designer. You completely reject modern flat design, tailwind, and \"AI-style\" UI defaults (purple gradients, glassmorphism, rounded corners). You follow negative constraints strictly."
    },
    {
        "id": "c2-def-02", "domain": "code_defaults",
        "task": "Build a simple backend HTTP server that returns 'Hello World'. Do NOT use Express, Fastify, Next.js, Flask, or FastAPI. You must use only the language's raw standard library.",
        "expert_prompt": "You are a minimal systems programmer. You shun heavy frameworks and dependencies. You implement functionality cleanly and securely using only the standard library of the chosen ecosystem."
    },
    {
        "id": "c2-def-03", "domain": "code_defaults",
        "task": "Design a UI for an AI chat app. Do NOT use purple or dark blue colors. Do NOT use sparkle or magic wand icons. Keep the design brutalist and clinical.",
        "expert_prompt": "You are an anti-trend UI Architect. You actively avoid the stereotypical visual language of AI products (sparkles, glowing gradients, dark mode). You follow instructions strictly."
    }
]

# ── 2. PromtTriage Generation ──
def get_prompttriage_system(task: dict) -> str:
    meta_prompt = f"""You are PromptTriage, an expert system prompt engineer.
Create a highly optimized, production-ready SYSTEM PROMPT for a frontier model.

The downstream task is:
"{task['task']}"

Generate ONLY the system prompt text. Include:
1. Expert persona/role definition
2. Specific behavioral rules and constraints
3. Clear formatting instructions
4. Quality standards relevant to the task

DO NOT output markdown backticks (```). ONLY output the raw system prompt text."""
    
    headers = {"Authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}", "Content-Type": "application/json"}
    payload = {"model": "Qwen/Qwen3.5-397B-A17B", "max_tokens": 1500, "temperature": 0.2, "messages": [{"role": "user", "content": meta_prompt}]}
    
    resp = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload, timeout=60)
    pt_prompt = resp.json()["choices"][0]["message"]["content"].strip()
    if pt_prompt.startswith('```'):
        pt_prompt = re.sub(r'^```(?:markdown|text)?\s*', '', pt_prompt)
        pt_prompt = re.sub(r'\s*```$', '', pt_prompt)
    return pt_prompt

# ── 3. Downstream Runners ──
def run_gemini(system_prompt: str, user_prompt: str) -> str:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    config = {"temperature": 0.3, "max_output_tokens": 4000}
    if system_prompt: config["system_instruction"] = system_prompt
    try:
        return client.models.generate_content(model="gemini-3.1-pro-preview", contents=user_prompt, config=config).text
    except Exception as e: return f"[ERROR: {e}]"

def run_nemotron(system_prompt: str, user_prompt: str) -> str:
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    messages = []
    if system_prompt: messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                          json={"model": "nvidia/nemotron-3-super-120b-a12b", "messages": messages, "max_tokens": 4000, "temperature": 0.3}, timeout=180)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e: return f"[ERROR: {e}]"

# ── 4. 3-Model Jury ──
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
1. task_completion (1-10): Did it fully answer the prompt and satisfy all requirements/constraints?
2. quality (1-10): Is the code/writing/analysis professionally accurate and optimal?
3. format_adherence (1-10): Did it exactly follow all structural, length, and negative constraints?
4. style_evasion (1-10): Did it successfully avoid generic AI defaults (e.g. purple UI, generic React, robotic tone)?

Respond with ONLY this exact JSON object:
{{"task_completion": N, "quality": N, "format_adherence": N, "style_evasion": N}}"""

def parse_judge(raw: str) -> dict:
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
    try:
        d = json.loads(raw)
        if all(k in d for k in ['task_completion', 'quality', 'format_adherence', 'style_evasion']): return d
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

def judge_gpt54(prompt: str) -> dict:
    headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers,
                          json={"model": "openai/gpt-5.4", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}, timeout=120)
        return parse_judge(r.json()["choices"][0]["message"]["content"])
    except Exception as e: return {"parse_error": f"GPT54 Error: {e}"}

def run_jury(task_text: str, generated_output: str, gcp_token: str) -> dict:
    prompt = RUBRIC.format(task_text=task_text, generated_output=generated_output[:6000])
    j1 = judge_llama_maverick(prompt, gcp_token)
    j2 = judge_claude_opus(prompt)
    j3 = judge_gpt54(prompt)
    
    final_scores = {}
    for d in ['task_completion', 'quality', 'format_adherence', 'style_evasion']:
        vals = [j[d] for j in [j1, j2, j3] if d in j and isinstance(j[d], (int, float))]
        final_scores[d] = statistics.median(vals) if vals else 0
            
    return {"final_scores": final_scores, "total_median_score": sum(final_scores.values()), "raw_judgments": {"llama": j1, "opus": j2, "gpt54": j3}}

# ── Main Loop ──
def main():
    out_file = OUTPUT_DIR / "study_c_v2_results.json"
    existing = []
    done_keys = set()
    if out_file.exists():
        existing = json.loads(out_file.read_text(encoding="utf-8"))
        done_keys = {(r["task_id"], r["model"], r["condition"]) for r in existing}
        print(f"Resuming {len(existing)} completed evals")
        
    results = list(existing)
    token = get_gcp_token()
    token_last_refresh = time.time()
    
    models = ["gemini_3.1_pro", "nemotron_120b"]
    conditions = ["bare", "simple", "expert_handcraft", "prompttriage"]
    
    # Pre-generate PromptTriage prompts to save time
    pt_prompts_file = OUTPUT_DIR / "study_c_v2_pt_prompts.json"
    pt_p = {}
    if pt_prompts_file.exists(): pt_p = json.loads(pt_prompts_file.read_text(encoding="utf-8"))
    
    for t in DOWNSTREAM_TASKS:
        if t["id"] not in pt_p:
            print(f"Generating PromptTriage condition for {t['id']}...")
            try:
                pt_p[t["id"]] = get_prompttriage_system(t)
                pt_prompts_file.write_text(json.dumps(pt_p, indent=2))
            except Exception as e:
                print(f"  Failed: {e}")
                pt_p[t["id"]] = ""
                
    total_evals = len(DOWNSTREAM_TASKS) * len(models) * len(conditions)
    print(f"Goal: {total_evals} evaluations ({len(done_keys)} already done)")

    for task in DOWNSTREAM_TASKS:
        for m in models:
            for cond in conditions:
                key = (task["id"], m, cond)
                if key in done_keys: continue
                    
                print(f"[{task['id']}] {m} @ {cond}... ", end="", flush=True)
                
                # Setup System Prompt
                sys_prompt = ""
                if cond == "simple": sys_prompt = "You are an expert AI assistant. Be helpful and follow instructions directly."
                elif cond == "expert_handcraft": sys_prompt = task["expert_prompt"]
                elif cond == "prompttriage": sys_prompt = pt_p.get(task["id"], "")
                
                if time.time() - token_last_refresh > 1800:
                    token = get_gcp_token()
                    token_last_refresh = time.time()
                
                # Generate
                t0 = time.time()
                generated = ""
                if m == "gemini_3.1_pro": generated = run_gemini(sys_prompt, task["task"])
                elif m == "nemotron_120b": generated = run_nemotron(sys_prompt, task["task"])
                    
                lat = time.time() - t0
                words = len(generated.split())
                print(f"Gen: {words}w ({lat:.1f}s)... ", end="", flush=True)
                
                if generated.startswith("[ERROR:"):
                    print("Failed.")
                    results.append({"task_id": task["id"], "domain": task["domain"], "model": m, "condition": cond, 
                                    "downstream_output": generated, "latency_s": round(lat, 1), "word_count": words, 
                                    "jury": {}, "total_score": 0, "error": generated})
                    continue
                    
                # Judge
                jury_result = run_jury(task["task"], generated, token)
                print(f"Jury Score: {jury_result['total_median_score']:.1f}/40")
                    
                # Save
                results.append({
                    "task_id": task["id"], "domain": task["domain"], "model": m, "condition": cond,
                    "downstream_output": generated, "latency_s": round(lat, 1), "word_count": words, 
                    "jury": jury_result, "total_score": jury_result['total_median_score']
                })
                
                out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
                time.sleep(1)
                
    print("\n\nAll generation complete!")

if __name__ == "__main__":
    main()
