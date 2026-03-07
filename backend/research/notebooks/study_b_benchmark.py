"""
Study B Benchmark — Generate system prompts from all fine-tuned models.

Runs on Azure ML A100 cluster. For each adapter:
1. Loads base model + QLoRA adapter with Unsloth
2. Generates system prompts for all 30 test cases
3. Saves outputs to benchmark_outputs.json

Usage (via submit_job.py --benchmark):
  Env vars: ADAPTER_BASE (path with model subdirs), OUTPUT_DIR
"""
import os
import sys
import json
import time
import torch
from pathlib import Path

# ── Config ──
ADAPTER_BASE = Path(os.environ.get("ADAPTER_BASE", "/mnt/outputs"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./benchmark_output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_NEW_TOKENS = 16384  # Thinking chain (~5K) + long system prompts (10K+)
TEMPERATURE = 0.7

# Model configs
MODELS = {
    "qwen3_8b": "unsloth/Qwen3-8B",
    "qwen3_14b": "unsloth/Qwen3-14B",
    "qwen3_32b": "unsloth/Qwen3-32B",
    "qwen3_30b_a3b": "unsloth/Qwen3-30B-A3B",
}

# ── Test prompts (embedded for cluster portability) ──
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


def log(msg: str):
    """Print with immediate flush for Azure ML log visibility."""
    print(msg, flush=True)


def format_user_message(test: dict) -> str:
    """Format the test prompt as a user message for the model."""
    msg = f"User request: {test['prompt']}"
    if test.get("context"):
        msg += f"\nAdditional context: {test['context']}"
    msg += f"\nTarget vendor: {test['vendor']}"
    msg += f"\nTarget model: {test.get('model', 'Not specified')}"
    return msg


def generate_with_adapter(model_key: str, adapter_dir: str):
    """Load a model + adapter and generate for all test prompts."""
    from unsloth import FastLanguageModel

    base_model_id = MODELS[model_key]
    log(f"\n{'='*60}")
    log(f"BENCHMARK: {model_key} ({base_model_id})")
    log(f"Adapter: {adapter_dir}")
    log(f"{'='*60}")

    # Load model from adapter dir (adapter_config.json points to base model)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_dir,
        max_seq_length=32768,  # High for inference — training was 8192 but generation needs room
        dtype=None,
        load_in_4bit=True,
        fast_inference=False,
    )
    FastLanguageModel.for_inference(model)
    log(f"Model loaded. Starting generation...")

    results = []
    for i, test in enumerate(TEST_PROMPTS):
        log(f"  [{i+1}/{len(TEST_PROMPTS)}] {test['id']} ({test['vendor']})")

        try:
            user_msg = format_user_message(test)
            messages = [{"role": "user", "content": user_msg}]

            # Keep thinking enabled — model was fine-tuned with thinking mode
            input_ids = tokenizer.apply_chat_template(
                messages, tokenize=True, add_generation_prompt=True,
                return_tensors="pt",
            ).to("cuda")

            t0 = time.time()
            with torch.no_grad():
                output_ids = model.generate(
                    input_ids=input_ids,
                    max_new_tokens=MAX_NEW_TOKENS,
                    temperature=TEMPERATURE,
                    do_sample=True,
                    top_p=0.9,
                )
            latency_ms = int((time.time() - t0) * 1000)

            # Decode only new tokens
            new_tokens = output_ids[0][input_ids.shape[1]:]
            output_text = tokenizer.decode(new_tokens, skip_special_tokens=True)

            # Strip <think>...</think> blocks if any leaked through
            if "<think>" in output_text and "</think>" in output_text:
                think_end = output_text.index("</think>") + len("</think>")
                output_text = output_text[think_end:].strip()

            results.append({
                "model": model_key,
                "prompt_id": test["id"],
                "category": test["category"],
                "target_vendor": test["vendor"],
                "target_model": test.get("model", ""),
                "user_prompt": test["prompt"],
                "generated_prompt": output_text,
                "char_count": len(output_text),
                "latency_ms": latency_ms,
            })
            log(f"    -> {len(output_text)} chars, {latency_ms}ms")

        except Exception as e:
            log(f"    !! ERROR: {e}")
            results.append({
                "model": model_key,
                "prompt_id": test["id"],
                "category": test["category"],
                "target_vendor": test["vendor"],
                "target_model": test.get("model", ""),
                "user_prompt": test["prompt"],
                "generated_prompt": f"[GENERATION FAILED: {e}]",
                "char_count": 0,
                "latency_ms": 0,
            })

    # Free GPU memory before loading next model
    log(f"Freeing GPU memory for {model_key}...")
    del model, tokenizer
    torch.cuda.empty_cache()
    return results


def main():
    log(f"PyTorch: {torch.__version__}")
    log(f"CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        gpu_props = torch.cuda.get_device_properties(0)
        log(f"GPU: {torch.cuda.get_device_name(0)}")
        log(f"VRAM: {gpu_props.total_memory / 1e9:.1f} GB")

    log(f"\nTest prompts: {len(TEST_PROMPTS)}")
    log(f"Models: {list(MODELS.keys())}")
    log(f"Adapter base: {ADAPTER_BASE}")

    # List adapter dirs for debugging
    if ADAPTER_BASE.exists():
        for item in sorted(ADAPTER_BASE.iterdir()):
            if item.is_dir():
                files = list(item.iterdir())
                log(f"  {item.name}/: {len(files)} items")
                for f in files[:5]:
                    log(f"    - {f.name}")
    else:
        log(f"  ⚠️  ADAPTER_BASE does not exist!")

    all_results = []
    for model_key in MODELS:
        # Search for adapter_config.json in various layouts
        candidates = [
            ADAPTER_BASE / model_key,  # Direct layout (symlinked)
            ADAPTER_BASE / model_key / "model_output" / "adapter",
            ADAPTER_BASE / model_key / "adapter",
        ]
        adapter_dir = None
        for c in candidates:
            if c.exists() and (c / "adapter_config.json").exists():
                adapter_dir = c
                break

        if not adapter_dir:
            log(f"\n⚠️  Skipping {model_key}: No adapter_config.json found")
            for c in candidates:
                log(f"    Checked: {c} (exists={c.exists()})")
            continue

        try:
            results = generate_with_adapter(model_key, str(adapter_dir))
            all_results.extend(results)
        except Exception as e:
            log(f"\n❌ FATAL ERROR for {model_key}: {e}")
            import traceback
            traceback.print_exc()

        # Save intermediate results after each model
        output_path = OUTPUT_DIR / "benchmark_outputs.json"
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2)
        log(f"  Saved {len(all_results)} results so far")

    # Final save
    output_path = OUTPUT_DIR / "benchmark_outputs.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    log(f"\n✅ Saved {len(all_results)} results to {output_path}")

    # Summary
    log(f"\n{'='*60}")
    log("BENCHMARK SUMMARY")
    log(f"{'='*60}")
    for model_key in MODELS:
        model_results = [r for r in all_results if r["model"] == model_key]
        if model_results:
            avg_chars = sum(r["char_count"] for r in model_results) / len(model_results)
            avg_latency = sum(r["latency_ms"] for r in model_results) / len(model_results)
            log(f"  {model_key}: {len(model_results)} outputs, "
                f"avg {avg_chars:.0f} chars, avg {avg_latency:.0f}ms")
        else:
            log(f"  {model_key}: SKIPPED")


if __name__ == "__main__":
    main()
