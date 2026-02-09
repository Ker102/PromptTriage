"""
Training Pair Generator for Study B (Fine-Tuning).

Creates JSONL datasets for QLoRA fine-tuning of Qwen 3 models:
  - Qwen3-8B (dense, 8B params — fits Colab T4 with 4-bit)
  - Qwen3-30B-A3B (MoE, 30B total / 3B active — runs like 3B, thinks like 30B)

Approaches:
  - Corpus-Direct: Reverse-engineer user prompts from real system prompts
  - Distillation: Use Claude Opus 4.6 (Vertex AI) as teacher to generate ideal outputs

Output format (ChatML / Unsloth-compatible):
{"messages": [
    {"role": "system", "content": "You are a system prompt engineer..."},
    {"role": "user", "content": "Build me a coding assistant for..."},
    {"role": "assistant", "content": "<identity>...</identity>..."}
]}

Usage:
    python -m research.generate_training_pairs --approach corpus
    python -m research.generate_training_pairs --approach distillation
    python -m research.generate_training_pairs --approach both
"""

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path(__file__).parent / "training_data"
DATA_DIR.mkdir(exist_ok=True)

SYSTEM_MSG = (
    "You are an expert system prompt engineer. Generate production-quality "
    "system prompts matching the target vendor's conventions. "
    "Anthropic: XML tags, ~8K words. OpenAI: Markdown, ~1.4K words. "
    "Google: Hybrid, ~1.3K words."
)


def get_client():
    from google import genai
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def get_pinecone_index():
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc.Index(os.getenv("PINECONE_INDEX_NAME", "prompttriage-prompts"))


def get_vertex_claude_client():
    """Create Anthropic client via Vertex AI for Claude Opus 4.6."""
    try:
        from anthropic import AnthropicVertex
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT_ID"))
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east5")
        if not project_id:
            raise ValueError(
                "Set GOOGLE_CLOUD_PROJECT env var for Vertex AI. "
                "Also ensure: gcloud auth application-default login"
            )
        return AnthropicVertex(project_id=project_id, region=location)
    except ImportError:
        raise ImportError("Install anthropic: pip install anthropic[vertex]")


# ── Approach 3: Corpus-Direct ────────────────────────────────────────────

def fetch_corpus_prompts(namespaces=None, limit=200) -> list[dict]:
    """Fetch real system prompts from Pinecone."""
    namespaces = namespaces or [
        "system-prompts-anthropic",
        "system-prompts-openai",
        "system-prompts-google",
        "system-prompts-misc",
    ]
    index = get_pinecone_index()
    all_prompts = []

    for ns in namespaces:
        try:
            # Use a broad query to fetch docs
            from google.genai import types
            client = get_client()
            dummy_emb = client.models.embed_content(
                model="gemini-embedding-001",
                contents="system prompt engineering best practices",
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=768,
                ),
            ).embeddings[0].values

            results = index.query(
                vector=dummy_emb, top_k=limit,
                include_metadata=True, namespace=ns,
            )
            for m in results.matches:
                content = m.metadata.get("content", "")
                if len(content) > 100:
                    vendor = "misc"
                    if "anthropic" in ns:
                        vendor = "anthropic"
                    elif "openai" in ns:
                        vendor = "openai"
                    elif "google" in ns:
                        vendor = "google"
                    all_prompts.append({
                        "id": m.id,
                        "content": content,
                        "vendor": vendor,
                        "metadata": m.metadata,
                    })
            print(f"  Fetched {len(results.matches)} from {ns}")
        except Exception as e:
            print(f"  Error fetching from {ns}: {e}")

    return all_prompts


def reverse_engineer_user_prompt(client, system_prompt: str, vendor: str) -> str:
    """Use LLM to generate a plausible user request that would produce this prompt."""
    snippet = system_prompt[:2000]
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=(
            f"Given this {vendor} system prompt, write a realistic 1-2 sentence "
            f"user request that would have produced it. Be specific about the "
            f"use case and target model.\n\nSystem prompt:\n{snippet}"
        ),
        config={"temperature": 0.7},
    )
    return resp.text.strip()


def generate_corpus_pairs(max_pairs: int = 500) -> list[dict]:
    """Generate training pairs from real corpus prompts."""
    client = get_client()
    prompts = fetch_corpus_prompts()
    print(f"\nGenerating corpus-direct pairs from {len(prompts)} prompts...")

    pairs = []
    for i, p in enumerate(prompts[:max_pairs]):
        if i % 10 == 0:
            print(f"  [{i}/{min(len(prompts), max_pairs)}]")
        try:
            user_msg = reverse_engineer_user_prompt(
                client, p["content"], p["vendor"]
            )
            pair = {
                "messages": [
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": f"{user_msg}\nTarget vendor: {p['vendor']}"},
                    {"role": "assistant", "content": p["content"]},
                ]
            }
            pairs.append(pair)
            time.sleep(0.5)
        except Exception as e:
            print(f"  Skip {p['id']}: {e}")

    return pairs


# ── Approach 4: Distillation ─────────────────────────────────────────────

DISTILLATION_SCENARIOS = [
    "Build a Python debugging assistant",
    "Create a customer support chatbot for a SaaS product",
    "Design a code review bot that catches security issues",
    "Build a blog content writer optimized for SEO",
    "Create an AI tutor for learning data science",
    "Design a legal document reviewer for GDPR compliance",
    "Build a meeting summarizer that extracts action items",
    "Create a SQL query optimizer with explanations",
    "Design an HR onboarding assistant for remote teams",
    "Build a competitive analysis agent for market research",
    "Create a video script writer for YouTube tutorials",
    "Design a project status reporter from Jira and GitHub",
    "Build a resume screening assistant with bias mitigation",
    "Create a financial planning assistant for small businesses",
    "Design a UX copywriter for web application microcopy",
    "Build an API documentation generator from code",
    "Create a test generation assistant for Python pytest",
    "Design a data pipeline debugging assistant",
    "Build a Kubernetes troubleshooting assistant",
    "Create a brand naming and trademark assistant",
]


def generate_distillation_pairs(
    max_pairs: int = 500,
    teacher_model: str = "claude-opus-4-20250514",
) -> list[dict]:
    """Generate pairs using Claude Opus 4.6 via Vertex AI as teacher."""
    vertex_client = get_vertex_claude_client()
    vendors = ["anthropic", "openai", "google"]
    pairs = []

    # Generate variations of base scenarios
    scenarios = []
    for base in DISTILLATION_SCENARIOS:
        for vendor in vendors:
            scenarios.append({"prompt": base, "vendor": vendor})
    # Repeat with variations until we hit max_pairs
    while len(scenarios) < max_pairs:
        for base in DISTILLATION_SCENARIOS:
            for vendor in vendors:
                scenarios.append({
                    "prompt": f"{base} with advanced features",
                    "vendor": vendor,
                })
                if len(scenarios) >= max_pairs:
                    break
            if len(scenarios) >= max_pairs:
                break

    print(f"\nGenerating {len(scenarios[:max_pairs])} distillation pairs ")
    print(f"  Teacher: {teacher_model} (Claude Opus 4.6 via Vertex AI)")

    for i, s in enumerate(scenarios[:max_pairs]):
        if i % 10 == 0:
            print(f"  [{i}/{max_pairs}]")
        try:
            user_msg = f"{s['prompt']}\nTarget vendor: {s['vendor']}"
            resp = vertex_client.messages.create(
                model=teacher_model,
                max_tokens=16384,
                system=SYSTEM_MSG,
                messages=[{"role": "user", "content": user_msg}],
                temperature=0.7,
            )
            assistant_text = resp.content[0].text
            pair = {
                "messages": [
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_text},
                ]
            }
            pairs.append(pair)
            time.sleep(1.5)  # Vertex AI rate limiting
        except Exception as e:
            print(f"  Skip {i}: {e}")

    return pairs


# ── Save ─────────────────────────────────────────────────────────────────

def save_jsonl(pairs: list[dict], filename: str):
    """Save pairs as JSONL (Unsloth-compatible format)."""
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"\nSaved {len(pairs)} pairs to {path}")
    return path


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--approach", choices=["corpus", "distillation", "both"],
                        default="both")
    parser.add_argument("--max-pairs", type=int, default=500)
    args = parser.parse_args()

    if args.approach in ("corpus", "both"):
        pairs = generate_corpus_pairs(args.max_pairs)
        save_jsonl(pairs, "corpus_direct_pairs.jsonl")

    if args.approach in ("distillation", "both"):
        pairs = generate_distillation_pairs(args.max_pairs)
        save_jsonl(pairs, "distillation_pairs.jsonl")


if __name__ == "__main__":
    main()
