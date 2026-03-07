#!/usr/bin/env python3
"""
LLM-as-Judge Evaluation Framework

Uses Gemini 3 Pro to score generated system prompts on 5 dimensions:
  1. Structure      — XML/Markdown organization, section hierarchy
  2. Completeness   — Identity, safety, tools, thinking, output sections
  3. Vendor Fidelity — Target vendor convention alignment
  4. Conciseness    — Right-sized for vendor (Anthropic≈8K, OpenAI≈1.4K)
  5. Actionability  — Production-ready? Would a dev actually use it?

Returns structured JSON scores for quantitative comparison.
"""

import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class JudgeScore:
    """Structured evaluation score for a single generated system prompt."""
    structure: int         # 1-10
    completeness: int      # 1-10
    vendor_fidelity: int   # 1-10
    conciseness: int       # 1-10
    actionability: int     # 1-10
    total: int             # Sum of all dimensions (5-50)
    reasoning: str         # Brief justification (2-3 sentences)
    word_count: int        # Actual word count of the generated prompt


@dataclass
class BenchmarkResult:
    """Complete result for one test prompt × one method."""
    prompt_id: str
    method: str           # e.g., "naive_rag", "crag", "qwen_7b_qlora"
    target_vendor: str    # anthropic, openai, google
    category: str         # coding, business, creative
    generated_prompt: str # The actual generated system prompt
    score: JudgeScore     # LLM-as-judge evaluation
    latency_ms: int       # End-to-end generation time
    cost_usd: float       # Estimated API cost for this call
    metadata: dict = None # Any extra info

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Judge prompt template
# ---------------------------------------------------------------------------

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator of AI system prompts. You have deep knowledge of how Anthropic, OpenAI, and Google structure their production system prompts based on analysis of 106 real prompts.

Your task: Score a generated system prompt on 5 dimensions, each 1-10.

VENDOR CONVENTIONS (from our corpus analysis of 106 production prompts):

<anthropic_conventions>
- Heavy XML tag usage (73% of prompts): <identity>, <rules>, <thinking>, <output_format>, <safety>
- Long prompts averaging ~8,021 words (range: 3K-19K words)
- Detailed identity blocks with personality traits
- Chain-of-thought sections with explicit reasoning instructions
- Safety/guardrail sections in 65% of prompts
- Code blocks and JSON examples in 77% of prompts
- Numbered lists in 85% of prompts
</anthropic_conventions>

<openai_conventions>
- Markdown headers (73% of prompts): ## sections for organization
- Concise prompts averaging ~1,435 words (range: 200-14K words)
- Tool definitions via function schemas in 27% of prompts
- Safety sections in 24% of prompts
- Minimal XML usage (14%)
- Bullet points and numbered lists
- Identity established in opening paragraph, not a dedicated section
</openai_conventions>

<google_conventions>
- Hybrid XML/Markdown format (38% XML, 54% Markdown)
- Moderate length averaging ~1,325 words
- Grounding instructions for factual accuracy
- Multimodal considerations when relevant
- Identity sections in 92% of prompts
- Tool code blocks in some prompts
</google_conventions>

SCORING DIMENSIONS:

1. **Structure** (1-10): Is the prompt well-organized? Does it use the appropriate formatting (XML for Anthropic, Markdown for OpenAI, hybrid for Google)? Are sections logically ordered?

2. **Completeness** (1-10): Does it include all essential sections? Check for: identity/role, behavioral rules, safety guardrails, output format, tool definitions (if applicable), thinking/reasoning instructions, edge case handling.

3. **Vendor Fidelity** (1-10): How well does it match the target vendor's conventions? An Anthropic prompt should use XML tags and be detailed (~8K words). An OpenAI prompt should use Markdown and be concise (~1.4K words).

4. **Conciseness** (1-10): Is it appropriately sized? Not padding for length, not cutting corners. Score relative to vendor expectations — a 2K-word Anthropic prompt is too short (low score), a 10K-word OpenAI prompt is too long (low score).

5. **Actionability** (1-10): Would a developer actually use this in production? Is it specific enough? Does it avoid vague platitudes? Does it provide concrete behavioral guidance?

You MUST respond with valid JSON only. No markdown fences, no explanation outside the JSON."""

JUDGE_USER_TEMPLATE = """Evaluate this generated system prompt.

<target_vendor>{vendor}</target_vendor>
<target_model>{model}</target_model>
<user_request>{user_prompt}</user_request>
<user_context>{context}</user_context>

<generated_system_prompt>
{generated_prompt}
</generated_system_prompt>

Respond with this exact JSON structure:
{{
  "structure": <1-10>,
  "completeness": <1-10>,
  "vendor_fidelity": <1-10>,
  "conciseness": <1-10>,
  "actionability": <1-10>,
  "total": <sum of above>,
  "reasoning": "<2-3 sentence justification>"
}}"""


# ---------------------------------------------------------------------------
# Judge implementation
# ---------------------------------------------------------------------------

class LLMJudge:
    """Evaluates generated system prompts using Gemini 3 Pro."""

    def __init__(self, model_name: str = "gemini-3.1-pro-preview"):
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def score(
        self,
        generated_prompt: str,
        target_vendor: str,
        target_model: str,
        user_prompt: str,
        context: str = "",
        retries: int = 3,
    ) -> JudgeScore:
        """Score a single generated system prompt."""
        user_msg = JUDGE_USER_TEMPLATE.format(
            vendor=target_vendor,
            model=target_model or "Not specified",
            user_prompt=user_prompt,
            context=context or "None provided",
            generated_prompt=generated_prompt,
        )

        for attempt in range(retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_msg,
                    config={
                        "system_instruction": JUDGE_SYSTEM_PROMPT,
                        "temperature": 0.1,  # Low temp for consistent scoring
                        "response_mime_type": "application/json",
                    },
                )

                raw_text = response.text.strip()
                # Parse JSON response
                scores = json.loads(raw_text)

                # Validate all fields present
                required = ["structure", "completeness", "vendor_fidelity", "conciseness", "actionability"]
                for field in required:
                    if field not in scores:
                        raise ValueError(f"Missing field: {field}")
                    scores[field] = max(1, min(10, int(scores[field])))

                # Recompute total to ensure consistency
                total = sum(scores[f] for f in required)

                word_count = len(generated_prompt.split())

                return JudgeScore(
                    structure=scores["structure"],
                    completeness=scores["completeness"],
                    vendor_fidelity=scores["vendor_fidelity"],
                    conciseness=scores["conciseness"],
                    actionability=scores["actionability"],
                    total=total,
                    reasoning=scores.get("reasoning", ""),
                    word_count=word_count,
                )

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"  [Judge] Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                continue

        # Fallback: return zeros if all retries fail
        print("  [Judge] All retries failed, returning zero scores")
        return JudgeScore(
            structure=0, completeness=0, vendor_fidelity=0,
            conciseness=0, actionability=0, total=0,
            reasoning="Evaluation failed after all retries",
            word_count=len(generated_prompt.split()),
        )

    def score_batch(
        self,
        results: list[dict],
        delay_seconds: float = 1.0,
    ) -> list[JudgeScore]:
        """Score a batch of results with rate limiting."""
        scores = []
        for i, result in enumerate(results):
            print(f"  [Judge] Scoring {i + 1}/{len(results)}: {result.get('prompt_id', '?')}")
            score = self.score(
                generated_prompt=result["generated_prompt"],
                target_vendor=result["target_vendor"],
                target_model=result.get("target_model", ""),
                user_prompt=result["user_prompt"],
                context=result.get("context", ""),
            )
            scores.append(score)
            if i < len(results) - 1:
                time.sleep(delay_seconds)
        return scores


# ---------------------------------------------------------------------------
# Results aggregation
# ---------------------------------------------------------------------------

def aggregate_scores(results: list[BenchmarkResult]) -> dict:
    """Aggregate scores across multiple results for summary statistics."""
    if not results:
        return {}

    by_method: dict[str, list[BenchmarkResult]] = {}
    for r in results:
        by_method.setdefault(r.method, []).append(r)

    summary = {}
    for method, method_results in by_method.items():
        scores = [r.score for r in method_results]
        n = len(scores)
        summary[method] = {
            "count": n,
            "avg_total": round(sum(s.total for s in scores) / n, 2),
            "avg_structure": round(sum(s.structure for s in scores) / n, 2),
            "avg_completeness": round(sum(s.completeness for s in scores) / n, 2),
            "avg_vendor_fidelity": round(sum(s.vendor_fidelity for s in scores) / n, 2),
            "avg_conciseness": round(sum(s.conciseness for s in scores) / n, 2),
            "avg_actionability": round(sum(s.actionability for s in scores) / n, 2),
            "avg_word_count": round(sum(s.word_count for s in scores) / n, 0),
            "avg_latency_ms": round(sum(r.latency_ms for r in method_results) / n, 0),
        }

    return summary


def format_summary_table(summary: dict) -> str:
    """Format aggregated scores as a readable table."""
    if not summary:
        return "No results to display."

    header = f"{'Method':<25} {'Total':<7} {'Struct':<7} {'Compl':<7} {'Vendor':<7} {'Conc':<7} {'Action':<7} {'Words':<7} {'ms':<7}"
    separator = "-" * len(header)
    lines = [header, separator]

    for method, stats in sorted(summary.items(), key=lambda x: -x[1]["avg_total"]):
        lines.append(
            f"{method:<25} "
            f"{stats['avg_total']:<7.1f} "
            f"{stats['avg_structure']:<7.1f} "
            f"{stats['avg_completeness']:<7.1f} "
            f"{stats['avg_vendor_fidelity']:<7.1f} "
            f"{stats['avg_conciseness']:<7.1f} "
            f"{stats['avg_actionability']:<7.1f} "
            f"{stats['avg_word_count']:<7.0f} "
            f"{stats['avg_latency_ms']:<7.0f}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== LLM Judge Test ===\n")

    # Quick test with a sample prompt
    test_prompt = """<identity>
You are a Python debugging assistant. You help developers find and fix bugs in their Python code.
</identity>

<rules>
1. Always ask for the full error traceback before suggesting fixes
2. Explain the root cause before providing the solution
3. Suggest preventive measures to avoid similar bugs
</rules>

<output_format>
Respond with:
1. Bug identification
2. Root cause analysis
3. Fix with code example
4. Prevention tips
</output_format>"""

    judge = LLMJudge()
    score = judge.score(
        generated_prompt=test_prompt,
        target_vendor="anthropic",
        target_model="Claude Sonnet 4",
        user_prompt="Build me a Python debugging assistant",
    )

    print(f"Structure:       {score.structure}/10")
    print(f"Completeness:    {score.completeness}/10")
    print(f"Vendor Fidelity: {score.vendor_fidelity}/10")
    print(f"Conciseness:     {score.conciseness}/10")
    print(f"Actionability:   {score.actionability}/10")
    print(f"Total:           {score.total}/50")
    print(f"Word count:      {score.word_count}")
    print(f"Reasoning:       {score.reasoning}")
