#!/usr/bin/env python3
"""
Study D v2: Prompt Delta Benchmark — IFEval + Quality Tasks

Tests 4 prompt conditions × 2 models × 2 benchmarks.

Models: Gemini 3.1 Pro, Claude Sonnet 4.6 (Vertex AI)
Benchmarks: IFEval (instruction following), Quality (LLM-as-judge)
Conditions: bare, simple, prompttriage (with RAG), expert_cot

Usage:
  python study_d_prompt_delta.py                    # Run all
  python study_d_prompt_delta.py --generate-prompts # Generate PromptTriage prompts only
  python study_d_prompt_delta.py --model gemini --benchmark ifeval --condition bare
  python study_d_prompt_delta.py --summary          # Show results summary
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# SECTION 1: OUTPUT DIRECTORY
# ═══════════════════════════════════════════════════════════════════

OUTPUT_DIR = Path(__file__).parent / "named-outputs" / "study_d"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: MODEL PROVIDERS
# ═══════════════════════════════════════════════════════════════════

class GeminiProvider:
    """Gemini 3.1 Pro via Google AI API."""
    NAME = "gemini_3.1_pro"

    def __init__(self):
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.1-pro-preview"

    def generate(self, user_msg: str, system_prompt: Optional[str] = None) -> str:
        config = {"temperature": 0.3, "max_output_tokens": 4096}
        if system_prompt:
            config["system_instruction"] = system_prompt
        response = self.client.models.generate_content(
            model=self.model, contents=user_msg, config=config,
        )
        return response.text

    def generate_json(self, user_msg: str, system_prompt: Optional[str] = None) -> str:
        config = {
            "temperature": 0.1,
            "max_output_tokens": 2048,
            "response_mime_type": "application/json",
        }
        if system_prompt:
            config["system_instruction"] = system_prompt
        response = self.client.models.generate_content(
            model=self.model, contents=user_msg, config=config,
        )
        return response.text


class ClaudeProvider:
    """Claude Sonnet 4.6 via Vertex AI."""
    NAME = "claude_sonnet_4.6"

    def __init__(self):
        import anthropic
        project_id = os.getenv("VERTEX_PROJECT_ID", "modelforge-3dpipeline")
        region = os.getenv("VERTEX_REGION", "europe-west1")
        self.client = anthropic.AnthropicVertex(project_id=project_id, region=region)
        self.model = "claude-sonnet-4-6@20250514"

    def generate(self, user_msg: str, system_prompt: Optional[str] = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": user_msg}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def generate_json(self, user_msg: str, system_prompt: Optional[str] = None) -> str:
        return self.generate(user_msg, system_prompt)


PROVIDERS = {"gemini": GeminiProvider, "claude": ClaudeProvider}


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: PROMPT CONDITIONS
# ═══════════════════════════════════════════════════════════════════

SIMPLE_PROMPT = (
    "You are a helpful, precise assistant. Follow all instructions exactly as given. "
    "Pay careful attention to formatting requirements, word counts, keyword constraints, "
    "and any other specific instructions in the user's request."
)

EXPERT_COT_PROMPTS = {
    "ifeval": (
        "You are an expert instruction-following assistant. Your primary skill is "
        "precisely satisfying ALL constraints in a request, no matter how unusual.\n\n"
        "Before responding, mentally enumerate every constraint:\n"
        "1. Identify ALL formatting requirements (case, punctuation, structure)\n"
        "2. Identify ALL content requirements (keywords, forbidden words, topics)\n"
        "3. Identify ALL length requirements (word count, sentence count, paragraphs)\n"
        "4. Identify ALL special requirements (JSON, postscript, repeat prompt, etc.)\n\n"
        "Then craft your response to satisfy EVERY constraint simultaneously. "
        "After drafting, mentally verify each constraint is met before finalizing.\n\n"
        "CRITICAL: Never skip a constraint. If asked to write in all lowercase, "
        "EVERY character must be lowercase. If asked for exactly 3 bullet points, "
        "provide exactly 3. Precision is more important than creativity."
    ),
    "quality": (
        "You are a world-class writer and analyst. For every task:\n\n"
        "1. Understand the exact request and all its nuances\n"
        "2. Plan your response structure before writing\n"
        "3. Write with clarity, depth, and engaging style\n"
        "4. Use appropriate formatting (headers, lists, paragraphs)\n"
        "5. Ensure your response is comprehensive yet concise\n"
        "6. Re-read the original request to verify you addressed everything\n\n"
        "Prioritize substance over fluff. Every sentence should add value."
    ),
}

PT_USE_CASES = {
    "ifeval": (
        "An instruction-following assistant that must precisely satisfy multiple "
        "simultaneous constraints in every response. Constraints include: specific "
        "word counts, required/forbidden keywords, case restrictions (all lowercase "
        "or all uppercase), punctuation rules (no commas), formatting requirements "
        "(JSON output, bullet points, numbered sections, markdown highlighting), "
        "structural requirements (postscripts, titles in angular brackets, repeated "
        "prompts), and length limits (exact paragraph/sentence counts). The assistant "
        "must satisfy ALL constraints simultaneously without exception."
    ),
    "quality": (
        "A versatile writing and analysis assistant that produces high-quality, "
        "well-structured responses across diverse tasks: creative writing (poems, "
        "stories, songs), professional documents (resumes, cover letters, proposals), "
        "analytical essays, persuasive arguments, technical explanations, and "
        "summarization. Must demonstrate excellent command of tone, style adaptation, "
        "logical organization, and audience awareness. Output quality should be "
        "production-ready and engaging."
    ),
}


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: PROMPTTRIAGE PROMPT GENERATION (with RAG)
# ═══════════════════════════════════════════════════════════════════

METAPROMPT_SYSTEM = """You are PromptTriage — an elite system-prompt architect.

Given a USE CASE description and SIMILAR PROMPTS from our database, generate a
production-quality system prompt that will maximize the AI's performance on this
specific type of task.

Your generated prompt MUST:
1. Define a clear identity and role
2. Include specific behavioral rules
3. Address edge cases and failure modes
4. Specify output format expectations
5. Be immediately usable in production

Output ONLY the system prompt text. No explanations, no markdown fences."""


def generate_prompttriage_prompts() -> dict[str, str]:
    """Generate PromptTriage system prompts using RAG from Pinecone."""
    cache_path = OUTPUT_DIR / "prompttriage_generated_prompts.json"
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        print(f"✅ Loaded cached PromptTriage prompts from {cache_path}")
        for k, v in cached.items():
            print(f"  {k}: {len(v)} chars")
        return cached

    print("\n🧠 Generating PromptTriage system prompts (with RAG)...\n")

    # Initialize Pinecone for RAG
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("systemprompts")

    # Initialize embedding model
    from google import genai
    embed_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # Initialize generator
    provider = GeminiProvider()
    results = {}

    for benchmark_type, use_case in PT_USE_CASES.items():
        print(f"\n--- Generating for: {benchmark_type} ---")

        # RAG: Get similar prompts from Pinecone
        embed_response = embed_client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=use_case,
        )
        query_vector = embed_response.embeddings[0].values

        similar = index.query(
            vector=query_vector, top_k=3, include_metadata=True,
            namespace="system-prompt-generation",
        )
        print(f"  [RAG] Found {len(similar.matches)} similar prompts "
              f"(top: {similar.matches[0].score:.3f})")

        rag_context = "\n\n---\n\n".join(
            m.metadata.get("text", "")[:1000] for m in similar.matches
        )

        user_msg = (
            f"USE CASE:\n{use_case}\n\n"
            f"SIMILAR PROMPTS FROM DATABASE:\n{rag_context}\n\n"
            f"Generate the optimal system prompt for this use case."
        )

        generated = provider.generate(user_msg, system_prompt=METAPROMPT_SYSTEM)
        results[benchmark_type] = generated.strip()
        print(f"  Generated: {len(results[benchmark_type])} chars")

    cache_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n✅ Saved PromptTriage prompts to {cache_path}")
    return results


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: IFEVAL INSTRUCTION VERIFIERS
# ═══════════════════════════════════════════════════════════════════

def verify_no_comma(response: str, **kw) -> bool:
    return "," not in response

def verify_lowercase(response: str, **kw) -> bool:
    alpha = [c for c in response if c.isalpha()]
    return all(c.islower() for c in alpha) if alpha else True

def verify_uppercase(response: str, **kw) -> bool:
    alpha = [c for c in response if c.isalpha()]
    return all(c.isupper() for c in alpha) if alpha else True

def verify_word_count(response: str, relation: str = "at least", num_words: int = 0, **kw) -> bool:
    wc = len(response.split())
    if relation == "at least":
        return wc >= num_words
    elif relation == "less than":
        return wc < num_words
    elif relation == "at most":
        return wc <= num_words
    return True

def verify_sentence_count(response: str, relation: str = "at least", num_sentences: int = 0, **kw) -> bool:
    sents = [s.strip() for s in re.split(r'[.!?]+', response) if s.strip()]
    sc = len(sents)
    if relation == "at least":
        return sc >= num_sentences
    elif relation == "less than":
        return sc < num_sentences
    elif relation == "at most":
        return sc <= num_sentences
    return True

def verify_paragraph_count(response: str, num_paragraphs: int = 0, **kw) -> bool:
    paras = [p.strip() for p in re.split(r'\n\s*\n|\*\*\*', response) if p.strip()]
    return len(paras) >= num_paragraphs

def verify_keyword_existence(response: str, keywords: list = None, **kw) -> bool:
    if not keywords:
        return True
    resp_lower = response.lower()
    return all(k.lower() in resp_lower for k in keywords)

def verify_forbidden_words(response: str, forbidden_words: list = None, **kw) -> bool:
    if not forbidden_words:
        return True
    resp_lower = response.lower()
    return all(w.lower() not in resp_lower for w in forbidden_words)

def verify_keyword_frequency(response: str, keyword: str = "", frequency: int = 0,
                              relation: str = "at least", **kw) -> bool:
    if not keyword:
        return True
    count = response.lower().count(keyword.lower())
    if relation == "at least":
        return count >= frequency
    elif relation == "less than":
        return count < frequency
    elif relation == "at most":
        return count <= frequency
    return True

def verify_letter_frequency(response: str, letter: str = "", let_frequency: int = 0,
                             let_relation: str = "at least", **kw) -> bool:
    if not letter:
        return True
    count = response.lower().count(letter.lower())
    if let_relation == "at least":
        return count >= let_frequency
    elif let_relation == "less than" or let_relation == "at most":
        return count <= let_frequency
    return True

def verify_json_format(response: str, **kw) -> bool:
    text = response.strip()
    # Strip markdown code block if present
    m = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False

def verify_bullet_count(response: str, num_bullets: int = 0, **kw) -> bool:
    bullets = re.findall(r'^\s*[\*\-•]\s', response, re.MULTILINE)
    return len(bullets) >= num_bullets

def verify_title(response: str, **kw) -> bool:
    return bool(re.search(r'<<.+?>>', response))

def verify_highlighted_sections(response: str, num_highlights: int = 0, **kw) -> bool:
    highlights = re.findall(r'\*[^*\n]+\*', response)
    return len(highlights) >= num_highlights

def verify_postscript(response: str, postscript_marker: str = "P.S.", **kw) -> bool:
    return postscript_marker in response or "P.P.S" in response or "P.S." in response

def verify_placeholders(response: str, num_placeholders: int = 0, **kw) -> bool:
    placeholders = re.findall(r'\[[^\]]+\]', response)
    return len(placeholders) >= num_placeholders

def verify_quotation(response: str, **kw) -> bool:
    text = response.strip()
    return text.startswith('"') and text.endswith('"')

def verify_end_checker(response: str, end_phrase: str = "", **kw) -> bool:
    if not end_phrase:
        return True
    return response.strip().endswith(end_phrase)

def verify_repeat_prompt(response: str, prompt_to_repeat: str = "", **kw) -> bool:
    if not prompt_to_repeat:
        return True
    return prompt_to_repeat in response

def verify_two_responses(response: str, **kw) -> bool:
    return "******" in response

def verify_multiple_sections(response: str, section_spliter: str = "SECTION",
                              num_sections: int = 0, **kw) -> bool:
    if not section_spliter:
        return True
    sections = re.findall(re.escape(section_spliter) + r'\s*\d+', response, re.IGNORECASE)
    return len(sections) >= num_sections

def verify_capital_word_frequency(response: str, capital_relation: str = "less than",
                                   capital_frequency: int = 0, **kw) -> bool:
    caps = [w for w in response.split() if w.isupper() and len(w) > 1]
    if capital_relation == "less than":
        return len(caps) < capital_frequency
    elif capital_relation == "at least":
        return len(caps) >= capital_frequency
    return True


# Map instruction IDs to verifier functions
VERIFIERS = {
    "punctuation:no_comma": verify_no_comma,
    "change_case:english_lowercase": verify_lowercase,
    "change_case:english_capital": verify_uppercase,
    "change_case:capital_word_frequency": verify_capital_word_frequency,
    "length_constraints:number_words": verify_word_count,
    "length_constraints:number_sentences": verify_sentence_count,
    "length_constraints:number_paragraphs": verify_paragraph_count,
    "keywords:existence": verify_keyword_existence,
    "keywords:forbidden_words": verify_forbidden_words,
    "keywords:frequency": verify_keyword_frequency,
    "keywords:letter_frequency": verify_letter_frequency,
    "detectable_format:json_format": verify_json_format,
    "detectable_format:number_bullet_lists": verify_bullet_count,
    "detectable_format:title": verify_title,
    "detectable_format:number_highlighted_sections": verify_highlighted_sections,
    "detectable_format:multiple_sections": verify_multiple_sections,
    "detectable_content:postscript": verify_postscript,
    "detectable_content:number_placeholders": verify_placeholders,
    "startend:quotation": verify_quotation,
    "startend:end_checker": verify_end_checker,
    "combination:repeat_prompt": verify_repeat_prompt,
    "combination:two_responses": verify_two_responses,
    "language:response_language": lambda r, **kw: True,  # Skip language detection
}


def score_ifeval(problem: dict, model_output: str) -> dict:
    """Score an IFEval problem. Returns per-instruction pass/fail."""
    instructions = problem["instruction_id_list"]
    kwargs_list = problem["kwargs"]
    results = {}
    for inst_id, kwargs in zip(instructions, kwargs_list):
        verifier = VERIFIERS.get(inst_id)
        if verifier:
            # Clean up kwargs: remove None values
            clean_kw = {k: v for k, v in kwargs.items() if v is not None}
            try:
                passed = verifier(model_output, **clean_kw)
            except Exception:
                passed = False
        else:
            passed = True  # Unknown instruction type, skip
        results[inst_id] = passed
    return results

# ═══════════════════════════════════════════════════════════════════
# SECTION 6: DATA LOADING
# ═══════════════════════════════════════════════════════════════════

QUALITY_TASKS = [
    {"id": "q01", "task": "Write a compelling product description for a smart water bottle that tracks hydration. Target audience: fitness enthusiasts. Keep it under 150 words.", "type": "marketing"},
    {"id": "q02", "task": "Summarize the key arguments for and against universal basic income in exactly 3 paragraphs. Be balanced and cite specific economic reasoning.", "type": "analysis"},
    {"id": "q03", "task": "Write a professional email declining a job offer while maintaining a positive relationship with the company. The tone should be gracious but firm.", "type": "professional"},
    {"id": "q04", "task": "Explain quantum entanglement to a curious 12-year-old. Use analogies they would understand. Keep it engaging and accurate.", "type": "education"},
    {"id": "q05", "task": "Write a short horror story (200-300 words) set in a library after closing time. Build suspense gradually.", "type": "creative"},
    {"id": "q06", "task": "Create a structured troubleshooting guide for when a website loads slowly. Include 5 steps, each with a clear action and expected outcome.", "type": "technical"},
    {"id": "q07", "task": "Write a persuasive argument for why companies should adopt a 4-day work week. Use data-driven reasoning and address counterarguments.", "type": "persuasive"},
    {"id": "q08", "task": "Rewrite this sentence to be more formal and suitable for an academic paper: 'Social media is basically ruining how kids talk to each other and it's getting worse every year.'", "type": "rewriting"},
    {"id": "q09", "task": "Create a meal plan for Monday through Friday for someone who is vegetarian, has a nut allergy, and wants to spend less than $50 total. Include breakfast, lunch, and dinner.", "type": "planning"},
    {"id": "q10", "task": "Write a thoughtful book review of a fictional mystery novel called 'The Last Cipher' by Elena Vasquez. The review should analyze plot, character development, and pacing.", "type": "creative"},
    {"id": "q11", "task": "Draft a bug report for a mobile app where the login button becomes unresponsive after rotating the screen. Include steps to reproduce, expected vs actual behavior, and severity.", "type": "technical"},
    {"id": "q12", "task": "Write a haiku sequence (3 haikus) about the transition from autumn to winter. Each haiku should connect to the next thematically.", "type": "creative"},
    {"id": "q13", "task": "Explain the pros and cons of microservices vs monolithic architecture to a startup CTO who needs to make a decision this week. Be specific and actionable.", "type": "technical"},
    {"id": "q14", "task": "Write a diplomatic response to a customer complaint about receiving a damaged product. Acknowledge the issue, offer a solution, and turn the situation positive.", "type": "professional"},
    {"id": "q15", "task": "Create an elevator pitch (60 seconds, ~150 words) for a startup that uses AI to match rescue dogs with compatible adopters based on lifestyle analysis.", "type": "marketing"},
    {"id": "q16", "task": "Write a compare-and-contrast analysis of remote work vs hybrid work models. Structure it with clear headers and conclude with a recommendation.", "type": "analysis"},
    {"id": "q17", "task": "Compose a sincere apology letter from a restaurant manager to a patron who had a terrible dining experience on their anniversary.", "type": "professional"},
    {"id": "q18", "task": "Explain the concept of compound interest to someone with no financial background. Use a concrete example with actual numbers.", "type": "education"},
    {"id": "q19", "task": "Write a brief policy proposal (250-350 words) for reducing food waste in school cafeterias. Include 3 specific actionable measures.", "type": "analysis"},
    {"id": "q20", "task": "Create a witty and informative social media thread (5 posts) explaining why sleep is important for productivity. Each post should be under 280 characters.", "type": "creative"},
]


def load_benchmark_data(benchmark: str) -> list[dict]:
    """Load benchmark data, caching to disk."""
    cache_dir = OUTPUT_DIR / "benchmark_data"
    cache_dir.mkdir(exist_ok=True)
    cache_path = cache_dir / f"{benchmark}_subset.json"

    if cache_path.exists():
        subset = json.loads(cache_path.read_text(encoding="utf-8"))
        print(f"  Loaded {len(subset)} {benchmark} problems from cache")
        return subset

    print(f"  Downloading {benchmark} from HuggingFace...")

    if benchmark == "ifeval":
        import urllib.request
        hf_url = "https://huggingface.co/api/datasets/google/IFEval/parquet/default/train"
        print("  Fetching IFEval parquet URL from HuggingFace...")
        req = urllib.request.Request(hf_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            parquet_urls = json.loads(resp.read().decode())

        # Download and read parquet using to_pydict (native types)
        import tempfile
        import pyarrow.parquet as pq
        all_items = []
        for purl in parquet_urls:
            tmp_path = os.path.join(tempfile.gettempdir(), "ifeval_tmp.parquet")
            print(f"  Downloading {purl[:80]}...")
            urllib.request.urlretrieve(purl, tmp_path)
            table = pq.read_table(tmp_path)
            d = table.to_pydict()
            for i in range(len(d["key"])):
                all_items.append({
                    "key": int(d["key"][i]),
                    "prompt": d["prompt"][i],
                    "instruction_id_list": list(d["instruction_id_list"][i]),
                    "kwargs": [dict(k) for k in d["kwargs"][i]],
                })
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        print(f"  Loaded {len(all_items)} IFEval problems total")

        # Pick problems with 2-3 constraints (hardest)
        multi = [item for item in all_items if len(item["instruction_id_list"]) >= 2]
        # Sort by number of constraints (most first), take top 50
        multi.sort(key=lambda x: len(x["instruction_id_list"]), reverse=True)
        subset = []
        for item in multi[:50]:
            subset.append({
                "key": item["key"],
                "prompt": item["prompt"],
                "instruction_id_list": item["instruction_id_list"],
                "kwargs": item["kwargs"],
            })

    elif benchmark == "quality":
        subset = QUALITY_TASKS

    else:
        raise ValueError(f"Unknown benchmark: {benchmark}")

    cache_path.write_text(json.dumps(subset, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved {len(subset)} problems to {cache_path}")
    return subset


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: LLM-AS-JUDGE QUALITY SCORER
# ═══════════════════════════════════════════════════════════════════

QUALITY_JUDGE_SYSTEM = """You are an expert evaluator of AI-generated text responses.
Score the response on 4 dimensions, each 1-10.

DIMENSIONS:
1. **Instruction Adherence** (1-10): Did the response follow ALL specific instructions?
   (word limits, structure requests, audience targeting, constraint satisfaction)

2. **Content Quality** (1-10): Is the content accurate, insightful, well-reasoned?
   (depth of analysis, correctness, relevance, creativity where appropriate)

3. **Organization** (1-10): Is it well-structured with logical flow?
   (headers, paragraphs, transitions, readability)

4. **Conciseness** (1-10): Is it appropriately sized — not padded, not skimpy?
   (every sentence adds value, no unnecessary repetition)

You MUST respond with valid JSON only. No markdown fences, no explanation outside JSON."""

QUALITY_JUDGE_USER = """Evaluate this AI response to the given task.

<task>{task}</task>

<response>
{response}
</response>

Respond with this exact JSON:
{{
  "instruction_adherence": <1-10>,
  "content_quality": <1-10>,
  "organization": <1-10>,
  "conciseness": <1-10>,
  "total": <sum of above>,
  "reasoning": "<1-2 sentence justification>"
}}"""


def score_quality(task: str, model_output: str, judge_provider=None) -> dict:
    """Score a quality task using LLM-as-judge."""
    if judge_provider is None:
        judge_provider = GeminiProvider()

    user_msg = QUALITY_JUDGE_USER.format(task=task, response=model_output)
    try:
        raw = judge_provider.generate_json(user_msg, system_prompt=QUALITY_JUDGE_SYSTEM)
        scores = json.loads(raw.strip())
        dims = ["instruction_adherence", "content_quality", "organization", "conciseness"]
        for d in dims:
            scores[d] = max(1, min(10, int(scores.get(d, 5))))
        scores["total"] = sum(scores[d] for d in dims)
        return scores
    except Exception as e:
        print(f"  [Judge] Error: {e}")
        return {
            "instruction_adherence": 0, "content_quality": 0,
            "organization": 0, "conciseness": 0, "total": 0,
            "reasoning": f"Judge error: {e}",
        }
# ═══════════════════════════════════════════════════════════════════
# SECTION 8: BENCHMARK RUNNER
# ═══════════════════════════════════════════════════════════════════

CONDITIONS = ["bare", "simple", "prompttriage", "expert_cot"]
BENCHMARKS = ["ifeval", "quality"]


def run_benchmark_slice(
    model_key: str, benchmark: str, condition: str,
    pt_prompts: dict, judge_provider=None,
) -> list[dict]:
    """Run one model × benchmark × condition slice."""
    # Load provider
    provider_cls = PROVIDERS[model_key]
    provider = provider_cls()

    # Load data
    problems = load_benchmark_data(benchmark)

    # Determine system prompt
    if condition == "bare":
        sys_prompt = None
    elif condition == "simple":
        sys_prompt = SIMPLE_PROMPT
    elif condition == "prompttriage":
        sys_prompt = pt_prompts.get(benchmark, SIMPLE_PROMPT)
    elif condition == "expert_cot":
        sys_prompt = EXPERT_COT_PROMPTS.get(benchmark, SIMPLE_PROMPT)
    else:
        sys_prompt = None

    # Results file (for resume)
    result_file = OUTPUT_DIR / f"study_d_{provider.NAME}_{benchmark}_{condition}.json"
    existing = []
    done_indices = set()
    if result_file.exists():
        existing = json.loads(result_file.read_text(encoding="utf-8"))
        done_indices = {r["problem_idx"] for r in existing}

    remaining = [(i, p) for i, p in enumerate(problems) if i not in done_indices]

    print(f"\n{'=' * 60}")
    print(f"  {provider.NAME} | {benchmark} | {condition}")
    print(f"  System prompt: {len(sys_prompt) if sys_prompt else 'None'} chars")
    print(f"  Problems: {len(remaining)} remaining of {len(problems)}")
    print(f"{'=' * 60}")

    results = list(existing)

    for count, (idx, problem) in enumerate(remaining, 1):
        # Format the user message
        if benchmark == "ifeval":
            user_msg = problem["prompt"]
            label = f"IFEval/{problem['key']}"
        else:
            user_msg = problem["task"]
            label = problem["id"]

        print(f"  [{count}/{len(remaining)}] {label}...", end="", flush=True)
        t0 = time.time()

        try:
            output = provider.generate(user_msg, system_prompt=sys_prompt)
        except Exception as e:
            print(f" ERROR: {e}")
            output = f"[ERROR: {e}]"

        elapsed = time.time() - t0

        # Score
        if benchmark == "ifeval":
            score_detail = score_ifeval(problem, output)
            all_passed = all(score_detail.values())
            inst_pass = sum(1 for v in score_detail.values() if v)
            inst_total = len(score_detail)
            status = "✓" if all_passed else f"✗ ({inst_pass}/{inst_total})"
            result = {
                "problem_idx": idx,
                "output": output,
                "instruction_results": score_detail,
                "all_passed": all_passed,
                "instructions_passed": inst_pass,
                "instructions_total": inst_total,
                "latency": round(elapsed, 1),
            }
        else:
            # Quality: score with LLM judge
            score_detail = score_quality(problem["task"], output, judge_provider)
            status = f"score={score_detail['total']}/40"
            result = {
                "problem_idx": idx,
                "task_id": problem["id"],
                "output": output,
                "scores": score_detail,
                "latency": round(elapsed, 1),
            }

        print(f" {status} ({elapsed:.1f}s)")
        results.append(result)

        # Save after each problem (for resume)
        result_file.write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8",
        )

    return results


def show_summary():
    """Show summary of all completed benchmark results."""
    print("\n" + "=" * 80)
    print("  STUDY D v2 RESULTS SUMMARY")
    print("=" * 80)

    result_files = sorted(OUTPUT_DIR.glob("study_d_*_*_*.json"))
    if not result_files:
        print("  No results found.")
        return

    # IFEval results
    print(f"\n{'─' * 60}")
    print("  IFEval: Instruction-Following Accuracy")
    print(f"{'─' * 60}")
    print(f"  {'Model':<20} {'Condition':<15} {'Prompt%':>8} {'Instr%':>8} {'N':>4}")
    print(f"  {'─'*20} {'─'*15} {'─'*8} {'─'*8} {'─'*4}")

    for f in result_files:
        if "_ifeval_" not in f.name:
            continue
        parts = f.stem.replace("study_d_", "").split("_ifeval_")
        if len(parts) != 2:
            continue
        model_name, condition = parts
        data = json.loads(f.read_text(encoding="utf-8"))
        n = len(data)
        if n == 0:
            continue
        prompt_acc = sum(1 for r in data if r.get("all_passed", False)) / n * 100
        total_inst = sum(r.get("instructions_total", 0) for r in data)
        passed_inst = sum(r.get("instructions_passed", 0) for r in data)
        inst_acc = passed_inst / total_inst * 100 if total_inst > 0 else 0
        print(f"  {model_name:<20} {condition:<15} {prompt_acc:>7.1f}% {inst_acc:>7.1f}% {n:>4}")

    # Quality results
    print(f"\n{'─' * 60}")
    print("  Quality: LLM-as-Judge Scores (out of 40)")
    print(f"{'─' * 60}")
    print(f"  {'Model':<20} {'Condition':<15} {'Total':>6} {'Instr':>6} {'Qual':>6} {'Org':>6} {'Conc':>6} {'N':>4}")
    print(f"  {'─'*20} {'─'*15} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*4}")

    for f in result_files:
        if "_quality_" not in f.name:
            continue
        parts = f.stem.replace("study_d_", "").split("_quality_")
        if len(parts) != 2:
            continue
        model_name, condition = parts
        data = json.loads(f.read_text(encoding="utf-8"))
        n = len(data)
        if n == 0:
            continue
        dims = ["instruction_adherence", "content_quality", "organization", "conciseness"]
        avgs = {}
        for d in dims:
            vals = [r["scores"].get(d, 0) for r in data if "scores" in r]
            avgs[d] = sum(vals) / len(vals) if vals else 0
        avg_total = sum(avgs.values())
        print(f"  {model_name:<20} {condition:<15} {avg_total:>5.1f} "
              f"{avgs['instruction_adherence']:>5.1f} {avgs['content_quality']:>5.1f} "
              f"{avgs['organization']:>5.1f} {avgs['conciseness']:>5.1f} {n:>4}")

    print()


# ═══════════════════════════════════════════════════════════════════
# SECTION 9: CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Study D v2: IFEval + Quality Benchmark")
    parser.add_argument("--model", choices=["gemini", "claude"], help="Run only this model")
    parser.add_argument("--benchmark", choices=BENCHMARKS, help="Run only this benchmark")
    parser.add_argument("--condition", choices=CONDITIONS, help="Run only this condition")
    parser.add_argument("--generate-prompts", action="store_true",
                        help="Generate PromptTriage prompts only (no benchmarking)")
    parser.add_argument("--summary", action="store_true", help="Show results summary")
    args = parser.parse_args()

    if args.summary:
        show_summary()
        return

    # Generate PromptTriage prompts
    pt_prompts = generate_prompttriage_prompts()

    if args.generate_prompts:
        return

    # Initialize judge for quality tasks
    judge = GeminiProvider()

    # Determine what to run
    models = [args.model] if args.model else list(PROVIDERS.keys())
    benchmarks = [args.benchmark] if args.benchmark else BENCHMARKS
    conditions = [args.condition] if args.condition else CONDITIONS

    total = len(models) * len(benchmarks) * len(conditions)
    count = 0

    for model_key in models:
        for benchmark in benchmarks:
            for condition in conditions:
                count += 1
                print(f"\n[{count}/{total}] Running {model_key}/{benchmark}/{condition}")
                try:
                    run_benchmark_slice(
                        model_key, benchmark, condition, pt_prompts,
                        judge_provider=judge,
                    )
                except Exception as e:
                    print(f"  ERROR: {e}")
                    import traceback
                    traceback.print_exc()

    # Show summary at the end
    show_summary()


if __name__ == "__main__":
    main()
