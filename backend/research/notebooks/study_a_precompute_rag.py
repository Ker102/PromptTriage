#!/usr/bin/env python3
"""
Study A — Stage 1: Pre-compute RAG contexts for all 30 test prompts × 6 RAG levels.

Runs LOCALLY (needs Pinecone + GOOGLE_API_KEY).
Outputs: named-outputs/study_a/rag_contexts.json — a file listing all 180 
(prompt × RAG level) combinations with the retrieved context pre-filled.

This file is then uploaded to Azure ML as an input for the GPU generation step.

Usage:
    python study_a_precompute_rag.py
"""
import json
import os
import sys
import time
from pathlib import Path

# Add project paths — backend/ is parent of research/
SCRIPT_DIR = Path(__file__).parent.resolve()  # notebooks/
RESEARCH_DIR = SCRIPT_DIR.parent.resolve()    # research/
BACKEND_DIR = RESEARCH_DIR.parent.resolve()   # backend/
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(str(BACKEND_DIR / ".env"))

from research.rag_methods import (
    RAG_METHODS, run_rag_method, no_rag, naive_rag, rerank_rag,
    corrective_rag, judge_rag, agentic_rag,
)

OUTPUT_DIR = Path(__file__).parent / "named-outputs" / "study_a"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Same 30 test prompts as Study B
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

RAG_LEVELS = ["L0_no_rag", "L1_naive_rag", "L2_rerank_rag", "L3_corrective_rag", "L4_judge_rag", "L5_agentic_rag"]


def format_rag_context(docs: list[dict]) -> str:
    """Format retrieved documents into context string for injection."""
    if not docs:
        return ""
    parts = []
    for i, doc in enumerate(docs, 1):
        content = doc.get("content", "")[:2000]  # Cap individual docs
        score = doc.get("score", doc.get("rerank_score", 0))
        parts.append(f"<reference_prompt_{i} relevance=\"{score:.2f}\">\n{content}\n</reference_prompt_{i}>")
    return "\n\n".join(parts)


def main():
    output_file = OUTPUT_DIR / "rag_contexts.json"

    # Resume support
    existing = []
    done_keys = set()
    if output_file.exists():
        existing = json.loads(output_file.read_text(encoding="utf-8"))
        done_keys = {(r["prompt_id"], r["rag_level"]) for r in existing}
        print(f"Loaded {len(existing)} existing entries ({len(done_keys)} unique)")

    results = list(existing)
    total = len(TEST_PROMPTS) * len(RAG_LEVELS)
    completed = len(done_keys)

    print(f"\nPre-computing RAG contexts: {total - completed} remaining of {total}")
    print(f"RAG levels: {RAG_LEVELS}\n")

    for rag_level in RAG_LEVELS:
        print(f"\n{'='*60}")
        print(f"  RAG Level: {rag_level}")
        print(f"{'='*60}")

        for i, test in enumerate(TEST_PROMPTS, 1):
            key = (test["id"], rag_level)
            if key in done_keys:
                continue

            print(f"  [{i}/{len(TEST_PROMPTS)}] {test['id']} ({test['vendor']})...", end="", flush=True)
            t0 = time.time()

            try:
                rag_result = run_rag_method(
                    rag_level, query=test["prompt"], vendor=test["vendor"], top_k=3
                )
                context_str = format_rag_context(rag_result.documents)
                retrieval_ms = rag_result.retrieval_ms
                num_docs = rag_result.num_after_filter
            except Exception as e:
                print(f" ERROR: {e}")
                context_str = ""
                retrieval_ms = 0
                num_docs = 0

            elapsed = time.time() - t0
            print(f" {num_docs} docs, {len(context_str)} chars ({elapsed:.1f}s)")

            # Build the full user message with RAG context injected
            user_msg = f"User request: {test['prompt']}"
            if test.get("context"):
                user_msg += f"\nAdditional context: {test['context']}"
            user_msg += f"\nTarget vendor: {test['vendor']}"
            user_msg += f"\nTarget model: {test.get('model', 'Not specified')}"

            if context_str:
                user_msg += (
                    f"\n\n<reference_prompts>\n"
                    f"The following are high-quality reference system prompts from our database "
                    f"that are relevant to this request. Use them as inspiration for structure, "
                    f"conventions, and best practices — but generate a unique, tailored prompt.\n\n"
                    f"{context_str}\n"
                    f"</reference_prompts>"
                )

            results.append({
                "prompt_id": test["id"],
                "category": test["category"],
                "vendor": test["vendor"],
                "target_model": test.get("model", ""),
                "user_prompt": test["prompt"],
                "rag_level": rag_level,
                "rag_context_chars": len(context_str),
                "rag_num_docs": num_docs,
                "rag_retrieval_ms": retrieval_ms,
                "full_user_message": user_msg,
            })

            # Save progressively
            output_file.write_text(
                json.dumps(results, indent=2, ensure_ascii=True), encoding="utf-8"
            )

    print(f"\n✅ Pre-computed {len(results)} RAG contexts -> {output_file}")


if __name__ == "__main__":
    main()
