"""
Study B Phase 2 — Benchmark proprietary models on the same 30 test prompts.

Compares: Gemini 3.1 Pro, Claude Sonnet 4.5 (Vertex AI), Qwen3-72B base (Together AI)
against our fine-tuned qwen3_14b (26.4/50 from Phase 1).

Usage:
  python study_b_proprietary.py              # Run all models
  python study_b_proprietary.py --model gemini  # Run single model
  python study_b_proprietary.py --model claude
  python study_b_proprietary.py --model qwen72b
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import asdict

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Load .env
from dotenv import load_dotenv
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
load_dotenv(os.path.join(project_root, 'backend', '.env'))

# ── Same 30 test prompts as Phase 1 ──
TEST_PROMPTS = [
    # Coding (10)
    {"id": "code-01", "category": "coding", "vendor": "anthropic", "prompt": "Build me a Python debugging assistant that helps find and fix bugs in my code", "model": "Claude Sonnet 4", "context": ""},
    {"id": "code-02", "category": "coding", "vendor": "openai", "prompt": "I need a code reviewer that checks for security vulnerabilities and suggests fixes", "model": "GPT-5.2", "context": ""},
    {"id": "code-03", "category": "coding", "vendor": "google", "prompt": "Create an AI pair programmer that helps me write TypeScript React components", "model": "Gemini 3 Pro", "context": ""},
    {"id": "code-04", "category": "coding", "vendor": "anthropic", "prompt": "Design a CI/CD pipeline assistant that writes GitHub Actions workflows and troubleshoots deployment failures", "model": "Claude Sonnet 4", "context": "We use a monorepo with Next.js frontend and FastAPI backend"},
    {"id": "code-05", "category": "coding", "vendor": "openai", "prompt": "Make a SQL query optimizer that rewrites slow queries and explains the optimization", "model": "GPT-5.2", "context": ""},
    {"id": "code-06", "category": "coding", "vendor": "google", "prompt": "Build a documentation generator that reads code and creates API docs", "model": "Gemini 3 Flash", "context": ""},
    {"id": "code-07", "category": "coding", "vendor": "anthropic", "prompt": "Create an AI that converts legacy Python 2 code to modern Python 3.12+", "model": "Claude Opus 4.6", "context": "The codebase is 50K lines with heavy use of print statements and old-style string formatting"},
    {"id": "code-08", "category": "coding", "vendor": "openai", "prompt": "Design a terminal command assistant that helps with complex bash/powershell operations", "model": "GPT-4.1", "context": ""},
    {"id": "code-09", "category": "coding", "vendor": "google", "prompt": "Build me a test writing assistant that generates unit tests for existing functions", "model": "Gemini 3 Pro", "context": "We use pytest with fixtures and mocks extensively"},
    {"id": "code-10", "category": "coding", "vendor": "anthropic", "prompt": "Create an architecture advisor that reviews system design documents and suggests improvements", "model": "Claude Sonnet 4", "context": "Microservices on Kubernetes, event-driven with Kafka"},
    # Business (10)
    {"id": "biz-01", "category": "business", "vendor": "anthropic", "prompt": "Build a customer support chatbot for a SaaS product that handles billing questions and feature requests", "model": "Claude Sonnet 4", "context": "Product is a project management tool, 10K users, Stripe billing"},
    {"id": "biz-02", "category": "business", "vendor": "openai", "prompt": "Create a sales email generator that writes personalized outreach based on prospect data", "model": "GPT-5.2", "context": ""},
    {"id": "biz-03", "category": "business", "vendor": "google", "prompt": "Design a data analysis agent that generates insights from CSV files and creates summary reports", "model": "Gemini 3 Pro", "context": ""},
    {"id": "biz-04", "category": "business", "vendor": "anthropic", "prompt": "Build a legal document reviewer that identifies risks and compliance issues in contracts", "model": "Claude Opus 4.6", "context": "Focus on EU GDPR and US data privacy regulations"},
    {"id": "biz-05", "category": "business", "vendor": "openai", "prompt": "Create a meeting summarizer that extracts action items, decisions, and follow-ups", "model": "GPT-4.1", "context": ""},
    {"id": "biz-06", "category": "business", "vendor": "google", "prompt": "Design an HR onboarding assistant that guides new employees through company processes", "model": "Gemini 3 Flash", "context": "For a 200-person tech startup with remote-first culture"},
    {"id": "biz-07", "category": "business", "vendor": "anthropic", "prompt": "Build a competitive intelligence agent that monitors and analyzes competitor product launches", "model": "Claude Sonnet 4", "context": ""},
    {"id": "biz-08", "category": "business", "vendor": "openai", "prompt": "Create a financial planning assistant that helps small businesses with budgeting and forecasting", "model": "GPT-5.2", "context": ""},
    {"id": "biz-09", "category": "business", "vendor": "google", "prompt": "Design a recruitment screening assistant that evaluates resumes against job descriptions", "model": "Gemini 3 Pro", "context": "Must avoid bias and comply with equal opportunity regulations"},
    {"id": "biz-10", "category": "business", "vendor": "anthropic", "prompt": "Build a project status reporter that creates weekly updates from Jira, GitHub, and Slack data", "model": "Claude Sonnet 4", "context": ""},
    # Creative (10)
    {"id": "creative-01", "category": "creative", "vendor": "anthropic", "prompt": "Build a blog content writer that matches my brand voice and optimizes for SEO", "model": "Claude Sonnet 4", "context": "Tech blog about AI and machine learning, casual but authoritative tone"},
    {"id": "creative-02", "category": "creative", "vendor": "openai", "prompt": "Create an image prompt generator for product photography using DALL-E and Midjourney", "model": "GPT-5.2", "context": ""},
    {"id": "creative-03", "category": "creative", "vendor": "google", "prompt": "Design an AI tutor that teaches programming through interactive exercises", "model": "Gemini 3 Pro", "context": "Target audience: complete beginners learning Python"},
    {"id": "creative-04", "category": "creative", "vendor": "anthropic", "prompt": "Build a creative writing assistant that helps with novel plotting, character development, and dialogue", "model": "Claude Opus 4.6", "context": ""},
    {"id": "creative-05", "category": "creative", "vendor": "openai", "prompt": "Create a social media content planner that generates posts for LinkedIn, Twitter, and Instagram", "model": "GPT-4.1", "context": ""},
    {"id": "creative-06", "category": "creative", "vendor": "google", "prompt": "Design a video script writer for YouTube tech tutorials", "model": "Gemini 3 Pro", "context": "10-15 minute videos, educational but entertaining, similar to Fireship style"},
    {"id": "creative-07", "category": "creative", "vendor": "anthropic", "prompt": "Build an email newsletter writer that creates engaging weekly digests from source material", "model": "Claude Sonnet 4", "context": ""},
    {"id": "creative-08", "category": "creative", "vendor": "openai", "prompt": "Create a brand naming assistant that generates creative product names with trademark availability checks", "model": "GPT-5.2", "context": ""},
    {"id": "creative-09", "category": "creative", "vendor": "google", "prompt": "Design a presentation builder that creates slide outlines and speaker notes from rough topics", "model": "Gemini 3 Flash", "context": ""},
    {"id": "creative-10", "category": "creative", "vendor": "anthropic", "prompt": "Build a UX copywriter that generates microcopy for web apps — buttons, tooltips, error messages, onboarding flows", "model": "Claude Sonnet 4", "context": "Product is a developer tool, tone should be friendly but professional"},
]

# The same system instruction the fine-tuned models were implicitly trained with
GENERATION_SYSTEM = """You are an expert system prompt engineer. Given a user's request for an AI assistant, generate a complete, production-ready system prompt for the specified target vendor and model.

The system prompt you generate should include:
- Identity/role definition
- Behavioral rules and constraints
- Output format specifications
- Safety guardrails where appropriate
- Domain-specific knowledge relevant to the task

Format the system prompt according to the target vendor's conventions:
- Anthropic: Use XML tags (<identity>, <rules>, <safety>, etc.), detailed (~5000-8000 words)
- OpenAI: Use Markdown headers, concise (~1000-2000 words)
- Google: Hybrid format, moderate length (~1000-2000 words)

Return ONLY the system prompt, no explanations or commentary."""


def format_user_message(test: dict) -> str:
    """Same format as the fine-tuned model benchmark."""
    msg = f"User request: {test['prompt']}"
    if test.get("context"):
        msg += f"\nAdditional context: {test['context']}"
    msg += f"\nTarget vendor: {test['vendor']}"
    msg += f"\nTarget model: {test.get('model', 'Not specified')}"
    return msg


# ── Provider clients ──

class GeminiProvider:
    """Gemini 3.1 Pro via Google GenAI SDK."""
    name = "gemini_3.1_pro"
    
    def __init__(self):
        from google import genai
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = "gemini-3.1-pro-preview"
    
    def generate(self, user_msg: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_msg,
            config={
                "system_instruction": GENERATION_SYSTEM,
                "temperature": 0.7,
                "max_output_tokens": 16384,
            },
        )
        return response.text


class ClaudeVertexProvider:
    """Claude Sonnet 4.5 via Vertex AI (Anthropic partner API)."""
    name = "claude_sonnet_4.5"
    
    def __init__(self):
        from anthropic import AnthropicVertex
        self.client = AnthropicVertex(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "modelsandtraining"),
            region="global",
        )
        self.model = "claude-sonnet-4-5@20250929"
    
    def generate(self, user_msg: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16384,
            temperature=0.7,
            system=GENERATION_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text


class TogetherProvider:
    """Qwen3-235B-A22B MoE (base, no fine-tuning) via Together AI."""
    name = "qwen3_235b_a22b_base"
    
    def __init__(self):
        import requests as _requests
        self._requests = _requests
        self.api_key = os.getenv("TOGETHER_API_KEY")
        self.model = "Qwen/Qwen3-235B-A22B-Instruct-2507-tput"
        self.base_url = "https://api.together.xyz/v1/chat/completions"
    
    def generate(self, user_msg: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 16384,
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": GENERATION_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        }
        resp = self._requests.post(self.base_url, headers=headers, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# ── Main ──

PROVIDERS = {
    "gemini": GeminiProvider,
    "claude": ClaudeVertexProvider,
    "qwen72b": TogetherProvider,
}


def run_benchmark(provider_key: str, output_dir: Path):
    """Run all 30 test prompts through a proprietary model."""
    provider = PROVIDERS[provider_key]()
    model_name = provider.name
    
    output_file = output_dir / f"proprietary_{model_name}.json"
    
    # Resume support: skip already-generated prompts
    existing_results = []
    if output_file.exists():
        existing_results = json.load(open(output_file))
        print(f"Found {len(existing_results)} existing results for {model_name}.")
    
    done_ids = {r["prompt_id"] for r in existing_results}
    to_run = [t for t in TEST_PROMPTS if t["id"] not in done_ids]
    
    if not to_run:
        print(f"All 30 prompts already completed for {model_name}.")
        return existing_results
    
    print(f"\n{'='*60}")
    print(f"BENCHMARK: {model_name} ({len(to_run)} remaining)")
    print(f"{'='*60}")
    
    results = list(existing_results)
    
    for i, test in enumerate(to_run):
        print(f"  [{i+1}/{len(to_run)}] {test['id']} ({test['vendor']})", end="", flush=True)
        user_msg = format_user_message(test)
        
        start = time.time()
        try:
            generated = provider.generate(user_msg)
            latency_ms = int((time.time() - start) * 1000)
            
            # Strip thinking tags if any
            if "<think>" in generated:
                import re
                generated = re.sub(r"<think>.*?</think>", "", generated, flags=re.DOTALL).strip()
            
            char_count = len(generated)
            print(f" -> {char_count} chars, {latency_ms}ms")
            
            results.append({
                "model": model_name,
                "prompt_id": test["id"],
                "category": test["category"],
                "target_vendor": test["vendor"],
                "target_model": test.get("model", ""),
                "user_prompt": test["prompt"],
                "generated_prompt": generated,
                "char_count": char_count,
                "latency_ms": latency_ms,
            })
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            print(f" -> ERROR: {e} ({latency_ms}ms)")
            results.append({
                "model": model_name,
                "prompt_id": test["id"],
                "category": test["category"],
                "target_vendor": test["vendor"],
                "target_model": test.get("model", ""),
                "user_prompt": test["prompt"],
                "generated_prompt": f"[ERROR: {str(e)[:200]}]",
                "char_count": 0,
                "latency_ms": latency_ms,
            })
        
        # Save after every prompt for resumability
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    
    print(f"\n✅ {model_name}: {len(results)} results saved to {output_file}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Study B Phase 2: Proprietary Model Benchmark")
    parser.add_argument("--model", choices=list(PROVIDERS.keys()) + ["all"], default="all",
                       help="Which model to benchmark (default: all)")
    args = parser.parse_args()
    
    output_dir = Path("named-outputs/benchmark_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    models_to_run = list(PROVIDERS.keys()) if args.model == "all" else [args.model]
    
    all_results = []
    for model_key in models_to_run:
        try:
            results = run_benchmark(model_key, output_dir)
            all_results.extend(results)
        except Exception as e:
            print(f"\n❌ Failed to benchmark {model_key}: {e}")
            import traceback
            traceback.print_exc()
    
    # Merge all proprietary results into one file
    if all_results:
        merged_file = output_dir / "proprietary_benchmark_outputs.json"
        json.dump(all_results, open(merged_file, "w"), indent=2)
        print(f"\n📊 Merged {len(all_results)} results to {merged_file}")
    
    print("\nDone! Run 'python study_b_judge.py' to score these outputs.")


if __name__ == "__main__":
    main()
