#!/usr/bin/env python3
"""
Study D v3: Behavioral Quality Benchmark

Measures how system prompts improve domain expertise, boundary handling, and specificity
across 9 professional scenarios (27 tasks). Uses a new 5-dimension LLM judge.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Import providers from the main script
# Ensure we're running from the right directory
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from study_d_prompt_delta import (
    GeminiProvider, 
    ClaudeProvider, 
    OUTPUT_DIR,
    SIMPLE_PROMPT,
    METAPROMPT_SYSTEM
)

PROVIDERS = {"gemini": GeminiProvider, "claude": ClaudeProvider}

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: BEHAVIORAL TASKS & PROMPTS
# ═══════════════════════════════════════════════════════════════════

BEHAVIORAL_TASKS = [
    # 1. Fintech Support (escalation, boundaries)
    {"id": "b_fin_1", "category": "fintech_support", "task": "I was charged $49.99 by a company I don't recognize on my debit card. What should I do?"},
    {"id": "b_fin_2", "category": "fintech_support", "task": "I want to close my account immediately and transfer everything to Chase. How?"},
    {"id": "b_fin_3", "category": "fintech_support", "task": "Can you help me set up a savings goal for a vacation next summer? I need $3000 by June."},
    
    # 2. Code Review (OWASP, severity, specifics)
    {"id": "b_sec_1", "category": "sec_code_review", "task": "Review this Flask endpoint:\n@app.route('/user')\ndef get_user():\n    username = request.args.get('name')\n    db.execute(f\"SELECT * FROM users WHERE name = '{username}'\")\n    return db.fetchone()"},
    {"id": "b_sec_2", "category": "sec_code_review", "task": "Review this Node API:\napp.post('/api/keys', (req, res) => {\n  const key = req.body.key || 'sk_live_12345default';\n  processCharge(key, req.body.amount);\n});"},
    {"id": "b_sec_3", "category": "sec_code_review", "task": "Review this React snippet:\nfunction Profile({ bio }) {\n  return <div dangerouslySetInnerHTML={{ __html: bio }} />\n}"},
    
    # 3. Medical Triage (disclaimers, escalation)
    {"id": "b_med_1", "category": "medical_triage", "task": "I've had a persistent headache for 3 days and some blurred vision today."},
    {"id": "b_med_2", "category": "medical_triage", "task": "My 6-year-old fell off the swing and their arm looks a bit swollen, but they can move it."},
    {"id": "b_med_3", "category": "medical_triage", "task": "I've been feeling extremely tired lately, could it be my thyroid?"},
    
    # 4. Tech Docs (Diátaxis, consistency)
    {"id": "b_doc_1", "category": "tech_docs", "task": "Write API reference documentation for this endpoint: POST /api/v2/users with body {name, email, role}. Returns 201 or 400."},
    {"id": "b_doc_2", "category": "tech_docs", "task": "Write a step-by-step 'Getting Started' tutorial for initializing our OAuth2 authentication flow in a React app."},
    {"id": "b_doc_3", "category": "tech_docs", "task": "Write an 'Explanation' guide detailing the theoretical difference between our synchronous and asynchronous webhook delivery modes."},
    
    # 5. Legal Review (terms, nuance, disclaimers)
    {"id": "b_leg_1", "category": "legal_review", "task": "Review this contract clause: 'Employee agrees not to work for any competitor globally for a period of 3 years following termination.'"},
    {"id": "b_leg_2", "category": "legal_review", "task": "Review this clause: 'Client shall indemnify Vendor for any claims arising from Vendor's own negligence or breach of contract.'"},
    {"id": "b_leg_3", "category": "legal_review", "task": "Review this SaaS term: 'Subscription auto-renews annually unless cancelled with 90 days prior written notice via certified mail.'"},
    
    # 6. E-commerce Copy (brand voice, target audience)
    {"id": "b_com_1", "category": "ecommerce_copy", "task": "Write a product description for our new ultralight 2-person tent, 3.2 lbs, 4-season rated. Target: hardcore backpackers."},
    {"id": "b_com_2", "category": "ecommerce_copy", "task": "Write copy for a titanium camping mug, double-walled insulation, 450ml volume, matte finish. Target: luxury campers."},
    {"id": "b_com_3", "category": "ecommerce_copy", "task": "Describe our waterproof hiking pants with articulated knees, DWR finish, and zip-off legs. Target: weekend warriors."},
    
    # 7. Data Narration (stats to business logic)
    {"id": "b_dat_1", "category": "data_narration", "task": "Our A/B test shows variant B has 3.2% higher conversion (p=0.04, n=12,000, baseline 1.5%). What should we do?"},
    {"id": "b_dat_2", "category": "data_narration", "task": "Customer churn increased 18% QoQ, but NPS dropped only 2 points. Subscription revenue is flat. Analyze this."},
    {"id": "b_dat_3", "category": "data_narration", "task": "We see a correlation of 0.72 between support ticket volume and feature adoption rate. What does this mean?"},
    
    # 8. DevOps Incident (SEV, runbook logic)
    {"id": "b_ops_1", "category": "devops_incident", "task": "Our main API is returning 503 errors for ~30% of requests since 14:22 UTC. Start an incident response."},
    {"id": "b_ops_2", "category": "devops_incident", "task": "Database replica lag is at 45 seconds and growing, primary CPU is at 92%. We use Postgres on AWS RDS."},
    {"id": "b_ops_3", "category": "devops_incident", "task": "A customer just reported seeing another customer's billing data in their dashboard. Urgent."},
    
    # 9. Code Generation (architecture, robustness, idioms)
    {"id": "b_cod_1", "category": "code_generation", "task": "Write a Python function to retry an async API call with exponential backoff and jitter. It should handle rate limits specifically."},
    {"id": "b_cod_2", "category": "code_generation", "task": "Create a React context provider for user authentication state that persists across page reloads using localStorage, avoiding hydration mismatches in Next.js."},
    {"id": "b_cod_3", "category": "code_generation", "task": "Write a Postgres SQL query to find the top 3 users by revenue in each country, but only include countries with at least 10 active users."},
]

EXPERT_COT_BEHAVIORAL = (
    "You are a highly skilled domain expert. For every task:\n\n"
    "1. ADOPT the specified role completely — think, reason, and respond as that professional would\n"
    "2. Demonstrate deep domain knowledge — use correct terminology, cite relevant standards\n"
    "3. Handle edge cases proactively — flag risks, caveats, and boundary conditions\n"
    "4. Know your boundaries — escalate, disclaim, or refuse when appropriate\n"
    "5. Use professional output formats — structure your response as a domain expert would\n"
    "6. Be specific and actionable — give concrete steps, exact commands, real examples\n\n"
    "Before writing, mentally plan your approach, considering the audience, the risks, and "
    "the exact standards of your profession. Never give generic, surface-level advice."
)

PT_BEHAVIORAL_USE_CASE = (
    "A multi-domain expert assistant that must deeply adopt specific professional "
    "roles (fintech support agent, security-focused code reviewer, medical triage "
    "assistant, technical documentation writer, legal contract reviewer, e-commerce "
    "copywriter, data analysis narrator, DevOps incident responder, senior software engineer). "
    "Each role requires demonstrating deep domain expertise, handling edge cases appropriately, "
    "knowing when to escalate or add disclaimers, providing specific actionable guidance "
    "rather than generic advice, and structuring output as a domain professional would. "
    "The assistant must behave as if it has years of experience in each domain, not as a "
    "general-purpose chatbot."
)

# ═══════════════════════════════════════════════════════════════════
# SECTION 2: PROMPTTRIAGE GENERATION
# ═══════════════════════════════════════════════════════════════════

def get_prompttriage_behavioral_prompt() -> str:
    """Generate the behavioral system prompt using Pinecone RAG."""
    cache_path = OUTPUT_DIR / "prompttriage_behavioral.txt"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
        
    print("\n🧠 Generating PromptTriage Behavioral prompt...")
    
    # Pinecone
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "prompttriage-prompts"))
    
    # Embedding
    from google import genai
    embed_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Getting similar
    embed_res = embed_client.models.embed_content(
        model="gemini-embedding-001",
        contents=PT_BEHAVIORAL_USE_CASE,
        config={"task_type": "RETRIEVAL_QUERY", "output_dimensionality": 768},
    )
    vector = embed_res.embeddings[0].values
    
    similar = index.query(
        vector=vector, top_k=3, include_metadata=True,
        namespace="system-prompts",
    )
    rag_context = "\n\n---\n\n".join(m.metadata.get("text", "")[:1000] for m in similar.matches)
    
    user_msg = (
        f"USE CASE:\n{PT_BEHAVIORAL_USE_CASE}\n\n"
        f"SIMILAR PROMPTS FROM DATABASE:\n{rag_context}\n\n"
        f"Generate the optimal system prompt for this use case."
    )
    
    provider = GeminiProvider()
    generated = provider.generate(user_msg, system_prompt=METAPROMPT_SYSTEM).strip()
    
    cache_path.write_text(generated, encoding="utf-8")
    return generated


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: BEHAVIORAL LLM-AS-JUDGE
# ═══════════════════════════════════════════════════════════════════

BEHAVIORAL_JUDGE_SYSTEM = """You are an expert evaluator of AI domain expertise and behavioral quality.
Score the response on 5 dimensions, each 1-10.

DIMENSIONS:
1. **Role Expertise** (1-10): deep domain knowledge, terminology, persona consistency vs generic advice.
2. **Edge Cases** (1-10): proactively addresses risks, nuances, and tricky caveats vs taking prompt at face value.
3. **Specificity** (1-10): provides concrete, actionable steps, commands, or details vs vague generalities.
4. **Boundaries** (1-10): knows what to escalate, decline, or disclaim vs blindly answering everything recklessly.
5. **Format** (1-10): uses professional output structures appropriate for the domain vs wall of text.

You MUST respond with valid JSON only. No markdown fences.
"""

BEHAVIORAL_JUDGE_USER = """Evaluate how well the AI acted as a true domain expert.

<category>{category}</category>
<task>{task}</task>

<response>
{response}
</response>

Respond with this exact JSON:
{{
  "role_expertise": <1-10>,
  "edge_cases": <1-10>,
  "specificity": <1-10>,
  "boundaries": <1-10>,
  "format": <1-10>,
  "total": <sum of above>,
  "reasoning": "<1-2 sentence justification emphasizing WHY this felt like an expert vs amateur>"
}}"""

def score_behavioral(category: str, task: str, model_output: str, judge_provider) -> dict:
    """Score a behavioral task using LLM-as-judge."""
    user_msg = BEHAVIORAL_JUDGE_USER.format(category=category, task=task, response=model_output)
    try:
        raw = judge_provider.generate_json(user_msg, system_prompt=BEHAVIORAL_JUDGE_SYSTEM)
        scores = json.loads(raw.strip())
        dims = ["role_expertise", "edge_cases", "specificity", "boundaries", "format"]
        for d in dims:
            scores[d] = max(1, min(10, int(scores.get(d, 5))))
        scores["total"] = sum(scores[d] for d in dims)
        return scores
    except Exception as e:
        print(f"  [Judge] Error: {e}")
        return {
            "role_expertise": 0, "edge_cases": 0, "specificity": 0, "boundaries": 0, "format": 0,
            "total": 0, "reasoning": f"Judge error: {e}",
        }


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: RUNNER & SUMMARY
# ═══════════════════════════════════════════════════════════════════

def run_behavioral_slice(model_key: str, condition: str, pt_prompt: str, judge_provider) -> list[dict]:
    provider = PROVIDERS[model_key]()
    
    if condition == "bare":
        sys_prompt = None
    elif condition == "simple":
        sys_prompt = SIMPLE_PROMPT
    elif condition == "prompttriage":
        sys_prompt = pt_prompt
    elif condition == "expert_cot":
        sys_prompt = EXPERT_COT_BEHAVIORAL
    else:
        sys_prompt = None
        
    result_file = OUTPUT_DIR / f"study_d_behavioral_{provider.NAME}_{condition}.json"
    existing = []
    done_ids = set()
    if result_file.exists():
        existing = json.loads(result_file.read_text(encoding="utf-8"))
        done_ids = {r["task_id"] for r in existing}
        
    remaining = [t for t in BEHAVIORAL_TASKS if t["id"] not in done_ids]
    
    if len(remaining) == 0:
        return existing

    print(f"\n{'=' * 60}")
    print(f"  {provider.NAME} | BEHAVIORAL | {condition}")
    print(f"  System prompt: {len(sys_prompt) if sys_prompt else 'None'} chars")
    print(f"  Problems: {len(remaining)} remaining of {len(BEHAVIORAL_TASKS)}")
    print(f"{'=' * 60}")
    
    results = list(existing)
    
    for count, task in enumerate(remaining, 1):
        print(f"  [{count}/{len(remaining)}] {task['id']}...", end="", flush=True)
        t0 = time.time()
        
        try:
            output = provider.generate(task["task"], system_prompt=sys_prompt)
        except Exception as e:
            print(f" ERROR: {e}")
            output = f"[ERROR: {e}]"
            
        elapsed = time.time() - t0
        
        # Score
        score_detail = score_behavioral(task["category"], task["task"], output, judge_provider)
        status = f"score={score_detail['total']}/50"
        
        result = {
            "task_id": task["id"],
            "category": task["category"],
            "output": output,
            "scores": score_detail,
            "latency": round(elapsed, 1),
        }
        
        print(f" {status} ({elapsed:.1f}s)")
        results.append(result)
        result_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        
    return results

def show_summary():
    """Show summary of all completed benchmark results."""
    print("\n" + "=" * 80)
    print("  STUDY D v3 BEHAVIORAL RESULTS SUMMARY")
    print("=" * 80)

    result_files = sorted(OUTPUT_DIR.glob("study_d_behavioral_*.json"))
    if not result_files:
        print("  No results found.")
        return

    print(f"\n  {'Model':<20} {'Condition':<15} {'Total':>6} {'Role':>6} {'Edge':>6} {'Spec':>6} {'Bndr':>6} {'Fmt':>6}")
    print(f"  {'─'*20} {'─'*15} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*6}")

    for f in result_files:
        parts = f.stem.replace("study_d_behavioral_", "").split("_")
        
        # Ensure we parse the filename correctly to extract model and condition
        if len(parts) >= 3 and "gemini" in parts[0]:
            model_name = "_".join(parts[:3])  # gemini_3.1_pro
            condition = "_".join(parts[3:])
        elif len(parts) >= 3 and "claude" in parts[0]:
            model_name = "_".join(parts[:3])  # claude_sonnet_4.6
            condition = "_".join(parts[3:])
        else:
            condition = parts[-1].replace(".json", "")
            model_name = "_".join(parts[:-1])
            
        condition = condition.replace(".json", "")
            
        data = json.loads(f.read_text(encoding="utf-8"))
        n = len(data)
        if n == 0:
            continue
            
        dims = ["role_expertise", "edge_cases", "specificity", "boundaries", "format"]
        avgs = {}
        for d in dims:
            vals = [r["scores"].get(d, 0) for r in data if "scores" in r]
            avgs[d] = sum(vals) / len(vals) if vals else 0
            
        avg_total = sum(avgs.values())
        print(f"  {model_name:<20} {condition:<15} {avg_total:>5.1f} "
              f"{avgs['role_expertise']:>5.1f} {avgs['edge_cases']:>5.1f} "
              f"{avgs['specificity']:>5.1f} {avgs['boundaries']:>5.1f} {avgs['format']:>5.1f}")


def main():
    parser = argparse.ArgumentParser(description="Study D v3: Behavioral Quality Benchmark")
    parser.add_argument("--model", choices=["gemini", "claude"], help="Run only this model")
    parser.add_argument("--condition", choices=["bare", "simple", "prompttriage", "expert_cot"], help="Run only this condition")
    parser.add_argument("--summary", action="store_true", help="Show results summary")
    args = parser.parse_args()

    if args.summary:
        show_summary()
        return

    pt_prompt = get_prompttriage_behavioral_prompt()
    judge = GeminiProvider()

    models = [args.model] if args.model else list(PROVIDERS.keys())
    conditions = [args.condition] if args.condition else ["bare", "simple", "prompttriage", "expert_cot"]
    
    total = len(models) * len(conditions)
    count = 0

    for model_key in models:
        for condition in conditions:
            count += 1
            print(f"\n[{count}/{total}] Running Behavioral Task: {model_key} / {condition}")
            try:
                run_behavioral_slice(model_key, condition, pt_prompt, judge)
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()

    show_summary()

if __name__ == "__main__":
    main()
