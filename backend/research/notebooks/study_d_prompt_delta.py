"""
Study D: The Prompt Delta — Classic Benchmarks

Quantifies how much difference a prompt makes on standard AI benchmarks.
Tests 4 prompt conditions × 2 models × 3 benchmarks.

Models: Gemini 3.1 Pro, Claude Sonnet 4.6 (Vertex AI)
Benchmarks: HumanEval-Hard (coding 100-130), MATH (competition math), MMLU-Hard (knowledge)
Conditions: bare, simple, prompttriage (with RAG), expert_cot

Usage:
  python study_d_prompt_delta.py                             # Run all
  python study_d_prompt_delta.py --model gemini              # Single model
  python study_d_prompt_delta.py --benchmark gsm8k           # Single bench
  python study_d_prompt_delta.py --condition prompttriage    # Single condition
  python study_d_prompt_delta.py --generate-prompts          # Gen PT prompts only
"""
import os, sys, json, time, re, argparse, subprocess, tempfile
from pathlib import Path
from typing import Optional

# Add project root + load .env
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from dotenv import load_dotenv
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
load_dotenv(os.path.join(project_root, 'backend', '.env'))


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: MODEL PROVIDERS
# ═══════════════════════════════════════════════════════════════════

class GeminiProvider:
    """Gemini 3.1 Pro via Google GenAI SDK."""
    name = "gemini_3.1_pro"

    def __init__(self):
        from google import genai
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = "gemini-3.1-pro-preview"

    def generate(self, user_msg: str, system_prompt: Optional[str] = None) -> str:
        config = {"temperature": 0.0, "max_output_tokens": 4096}
        if system_prompt:
            config["system_instruction"] = system_prompt
        response = self.client.models.generate_content(
            model=self.model, contents=user_msg, config=config,
        )
        return response.text


class ClaudeVertexProvider:
    """Claude Sonnet 4.6 via Vertex AI."""
    name = "claude_sonnet_4.6"

    def __init__(self):
        from anthropic import AnthropicVertex
        self.client = AnthropicVertex(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "modelsandtraining"),
            region="global",
        )
        self.model = "claude-sonnet-4-6@default"

    def generate(self, user_msg: str, system_prompt: Optional[str] = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": user_msg}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = self.client.messages.create(**kwargs)
        return response.content[0].text


PROVIDERS = {
    "gemini": GeminiProvider,
    "claude": ClaudeVertexProvider,
}


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: PROMPTTRIAGE RAG + PROMPT GENERATION
# ═══════════════════════════════════════════════════════════════════

def query_pinecone_rag(query: str, top_k: int = 3) -> list[dict]:
    """Query Pinecone system-prompts namespace using Gemini embeddings."""
    from google import genai
    from pinecone import Pinecone

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config={"task_type": "RETRIEVAL_QUERY", "output_dimensionality": 768},
    )
    query_embedding = result.embeddings[0].values

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME", "prompttriage")
    index = pc.Index(index_name)

    results = index.query(
        vector=query_embedding, top_k=top_k,
        include_metadata=True, namespace="system-prompts",
    )

    formatted = []
    for match in results.matches:
        formatted.append({
            "content": match.metadata.get("content", ""),
            "similarity": match.score,
            "source": match.metadata.get("source", "unknown"),
        })
    return formatted


def format_rag_context(results: list[dict]) -> str:
    """Format RAG results same as frontend formatRAGContext()."""
    if not results:
        return ""
    parts = []
    for i, r in enumerate(results):
        parts.append(
            f"Example {i+1} ({r['source']}, similarity: {r['similarity']*100:.1f}%):\n"
            f"{r['content']}"
        )
    return f"<similar_prompts>\nHigh-quality prompts similar to the request:\n\n" + \
           "\n\n".join(parts) + "\n</similar_prompts>"


# PromptTriage metaprompt — same as systemPromptGenerator.ts
PROMPTTRIAGE_METAPROMPT = """You are PromptTriage's System Prompt Generator. You specialize in creating production-grade system prompts that define AI assistant and agent behavior.

<identity>
You are a master architect of AI behavior. You design system prompts that transform base models into specialized assistants with well-defined capabilities, constraints, and personalities.
</identity>

<core_distinction>
CRITICAL: You generate SYSTEM PROMPTS, not task prompts.
- System Prompts define WHO the AI is, set persistent behavior, establish constraints
- Task Prompts define WHAT to do, set one-time instructions
Your output will be used as the system message/instruction for an AI model.
</core_distinction>

<workflow>
1. Analyze the requirements and identify core purpose
2. Structure the prompt with appropriate sections
3. Generate each section with precise, actionable language
4. Optimize for the target model's conventions
</workflow>

<rules>
- Always wrap the system prompt in proper formatting
- Use XML tags for structure (Anthropic best practice)
- Be comprehensive but avoid unnecessary repetition
- Tailor complexity to the use case
- Never include placeholder text
</rules>

Respond with ONLY the system prompt text. No JSON wrapping, no explanations."""


def generate_prompttriage_system_prompt(
    use_case: str, target_model: str = "Any AI model"
) -> str:
    """Generate a system prompt using PromptTriage's full pipeline (metaprompt + RAG)."""
    from google import genai

    print(f"  [RAG] Querying Pinecone for: {use_case[:60]}...")
    rag_results = query_pinecone_rag(use_case, top_k=3)
    rag_context = format_rag_context(rag_results)
    if rag_results:
        print(f"  [RAG] Found {len(rag_results)} similar prompts "
              f"(top: {rag_results[0]['similarity']:.3f})")
    else:
        print("  [RAG] No similar prompts found, proceeding without RAG")

    user_prompt = f"<target_model>{target_model}</target_model>\n"
    user_prompt += f"<use_case>{use_case}</use_case>\n"
    if rag_context:
        user_prompt += f"\n{rag_context}\n"

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=user_prompt,
        config={
            "system_instruction": PROMPTTRIAGE_METAPROMPT,
            "temperature": 0.5,
            "max_output_tokens": 8192,
        },
    )
    return response.text


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: PROMPT CONDITIONS
# ═══════════════════════════════════════════════════════════════════

SIMPLE_SYSTEM_PROMPT = "You are a helpful assistant."

EXPERT_COT_PROMPTS = {
    "humaneval": (
        "You are an expert Python programmer solving challenging algorithmic problems. "
        "When given a function signature and docstring, complete ONLY the function body.\n\n"
        "Think step by step:\n"
        "1. Carefully analyze the expected inputs, outputs, and ALL edge cases\n"
        "2. Consider algorithmic complexity — choose the right data structures\n"
        "3. Plan your approach before writing code\n"
        "4. Handle edge cases thoroughly (empty inputs, zero, negative, large inputs)\n"
        "5. Write clean, correct Python code\n\n"
        "CRITICAL: Return ONLY the function body code. No explanation, no signature, "
        "no docstring, no markdown code blocks. Just the raw Python code that goes "
        "inside the function."
    ),
    "math": (
        "You are an expert mathematician solving competition-level math problems.\n\n"
        "For each problem:\n"
        "1. Carefully read and understand what is being asked\n"
        "2. Identify the mathematical domain (algebra, geometry, number theory, etc.)\n"
        "3. Break the problem into sub-steps\n"
        "4. Show your work clearly with equations\n"
        "5. Double-check your computation at each step\n"
        "6. Simplify your final answer completely\n\n"
        "IMPORTANT: Put your final answer inside \\boxed{} notation on the last line. "
        "Example: \\boxed{42}"
    ),
    "mmlu": (
        "You are a domain expert answering challenging academic questions across "
        "abstract algebra, formal logic, electrical engineering, and clinical medicine.\n\n"
        "For each question:\n"
        "1. Read the question and all options carefully\n"
        "2. Apply domain-specific knowledge and reasoning\n"
        "3. Eliminate clearly wrong answers\n"
        "4. Reason through remaining options using first principles\n"
        "5. Select the best answer\n\n"
        "IMPORTANT: State your final answer as a single letter (A, B, C, or D) on "
        "the last line of your response."
    ),
}

# Cached PromptTriage-generated prompts (generated on first run)
_pt_prompts_cache = {}

def get_system_prompt(condition: str, benchmark: str) -> Optional[str]:
    """Get the system prompt for a given condition and benchmark type."""
    if condition == "bare":
        return None
    elif condition == "simple":
        return SIMPLE_SYSTEM_PROMPT
    elif condition == "expert_cot":
        return EXPERT_COT_PROMPTS[benchmark]
    elif condition == "prompttriage":
        return _pt_prompts_cache.get(benchmark)
    return None


PT_USE_CASES = {
    "humaneval": (
        "An advanced Python code completion assistant that solves challenging algorithmic "
        "problems. It receives function signatures with detailed docstrings and must "
        "complete the function body with correct, efficient code. Problems include "
        "complex string manipulation, recursive algorithms, dynamic programming, graph "
        "traversal, mathematical computations, and data structure operations. "
        "Must handle edge cases and produce code that passes rigorous unit tests. "
        "Output must be ONLY the raw function body code — no explanations, no markdown."
    ),
    "math": (
        "A competition-level mathematics solver that handles problems across algebra, "
        "number theory, counting and probability, geometry, intermediate algebra, "
        "and precalculus. Must show clear step-by-step mathematical reasoning, "
        "use proper notation, and arrive at exact answers. Problems require creative "
        "problem-solving approaches, not just formula application. "
        "Final answers must be in \\boxed{} notation."
    ),
    "mmlu": (
        "A domain expert assistant answering challenging multiple-choice questions "
        "across specialized academic subjects including abstract algebra, formal logic, "
        "electrical engineering, and clinical medicine. Must demonstrate deep domain "
        "expertise, careful reasoning under ambiguity, and ability to distinguish "
        "between subtly different answer options. Requires graduate-level knowledge."
    ),
}


def generate_all_pt_prompts(output_dir: Path):
    """Generate and cache PromptTriage prompts for all benchmark types."""
    global _pt_prompts_cache
    cache_file = output_dir / "prompttriage_generated_prompts.json"

    if cache_file.exists():
        _pt_prompts_cache = json.load(open(cache_file))
        print(f"✅ Loaded cached PromptTriage prompts from {cache_file}")
        for k, v in _pt_prompts_cache.items():
            print(f"  {k}: {len(v)} chars")
        return

    print("\n🧠 Generating PromptTriage system prompts (with RAG)...\n")
    for benchmark, use_case in PT_USE_CASES.items():
        print(f"\n--- Generating for: {benchmark} ---")
        prompt = generate_prompttriage_system_prompt(use_case)
        _pt_prompts_cache[benchmark] = prompt
        print(f"  Generated: {len(prompt)} chars")

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(_pt_prompts_cache, f, indent=2)
    print(f"\n✅ Saved PromptTriage prompts to {cache_file}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: BENCHMARK DATA (loaded from files or HuggingFace)
# ═══════════════════════════════════════════════════════════════════

def load_benchmark_data(benchmark: str, data_dir: Path) -> list[dict]:
    """Load benchmark data from cached JSON or download from HuggingFace."""
    cache_file = data_dir / f"{benchmark}_subset.json"

    if cache_file.exists():
        data = json.load(open(cache_file))
        print(f"  Loaded {len(data)} {benchmark} problems from cache")
        return data

    print(f"  Downloading {benchmark} from HuggingFace...")
    try:
        from datasets import load_dataset
    except ImportError:
        print("  ERROR: pip install datasets  (needed for first run)")
        sys.exit(1)

    if benchmark == "humaneval":
        ds = load_dataset("openai/openai_humaneval", split="test")
        all_items = list(ds)
        # Use problems 100-130 (much harder: complex algorithms, edge cases)
        subset = []
        for item in all_items[100:130]:
            subset.append({
                "task_id": item["task_id"],
                "prompt": item["prompt"],
                "canonical_solution": item["canonical_solution"],
                "test": item["test"],
                "entry_point": item["entry_point"],
            })

    elif benchmark == "math":
        # MATH: Competition-level math (models score ~60-80%)
        ds = load_dataset("lighteval/MATH", "all", split="test", trust_remote_code=True)
        subset = []
        count = 0
        for item in ds:
            if count >= 50:
                break
            # Extract answer from \boxed{}
            answer = item.get("answer", "")
            subset.append({
                "problem": item["problem"],
                "solution": item.get("solution", ""),
                "answer": answer,
                "level": item.get("level", ""),
                "type": item.get("type", ""),
            })
            count += 1

    elif benchmark == "mmlu":
        # Use HARDER subjects where models actually struggle
        subjects = [
            "abstract_algebra", "formal_logic",
            "electrical_engineering", "college_chemistry",
            "clinical_knowledge"
        ]
        subset = []
        for subject in subjects:
            try:
                ds = load_dataset("cais/mmlu", subject, split="test")
                for item in list(ds)[:10]:
                    subset.append({
                        "question": item["question"],
                        "choices": item["choices"],
                        "answer": item["answer"],  # 0-3 index
                        "subject": subject,
                    })
            except Exception as e:
                print(f"    Warning: Could not load {subject}: {e}")

    else:
        raise ValueError(f"Unknown benchmark: {benchmark}")

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(subset, f, indent=2)
    print(f"  Saved {len(subset)} {benchmark} problems to {cache_file}")
    return subset


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: OUTPUT EXTRACTION + SCORING
# ═══════════════════════════════════════════════════════════════════

def extract_code_body(raw_output: str, problem_prompt: str = "") -> str:
    """Extract just the function body from model output.
    
    Handles: markdown code blocks, explanations, repeated signatures.
    CRITICAL: Preserves indentation — the body must stay properly indented
    as it will be concatenated directly after the function signature.
    """
    text = raw_output

    # Step 1: If wrapped in markdown code blocks, extract the code
    code_blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if code_blocks:
        text = max(code_blocks, key=len)  # Don't strip — preserve indentation

    # Step 2: If the model repeated the full function (def + body), extract just body
    lines = text.split("\n")
    body_start = 0
    in_docstring = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip def line
        if re.match(r"^\s*def\s+\w+\(", line):
            body_start = i + 1
            continue
        # Skip docstrings that come right after def
        if i == body_start and (stripped.startswith('"""') or stripped.startswith("'''")):
            in_docstring = True
            if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                # Single-line docstring
                in_docstring = False
                body_start = i + 1
            continue
        if in_docstring:
            if '"""' in stripped or "'''" in stripped:
                in_docstring = False
                body_start = i + 1
            continue

    # Only use body_start if we actually found a def
    if body_start > 0:
        text = "\n".join(lines[body_start:])
    else:
        text = "\n".join(lines)

    # Step 3: Ensure indentation — if no leading whitespace, add 4 spaces
    result_lines = text.split("\n")
    if result_lines and result_lines[0] and not result_lines[0][0].isspace():
        # The code has no indentation — add 4 spaces to each non-empty line  
        result_lines = [("    " + line if line.strip() else line) for line in result_lines]

    return "\n".join(result_lines)


def score_humaneval(problem: dict, model_output: str) -> bool:
    """Score HumanEval: extract code, execute function + test assertions."""
    # Extract the code body (strip markdown, handle repeated signatures)
    code_body = extract_code_body(model_output, problem["prompt"])

    # Combine: prompt (signature) + extracted body + test code
    full_code = problem["prompt"] + code_body + "\n\n" + problem["test"]
    full_code += f"\ncheck({problem['entry_point']})"

    tmp_path = Path(tempfile.gettempdir()) / f"study_d_eval_{os.getpid()}.py"
    try:
        tmp_path.write_text(full_code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(tmp_path)],
            capture_output=True, timeout=15, text=True,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False
    finally:
        for _ in range(3):
            try:
                tmp_path.unlink(missing_ok=True)
                break
            except OSError:
                time.sleep(0.1)


def extract_boxed_answer(text: str) -> str:
    """Extract answer from \\boxed{...} notation used in MATH benchmark."""
    # Find the last \boxed{...} in the text
    matches = re.findall(r"\\boxed\{([^{}]*)\}", text)
    if matches:
        return matches[-1].strip()
    # Try nested braces
    matches = re.findall(r"\\boxed\{(.+?)\}", text)
    if matches:
        return matches[-1].strip()
    return ""


def normalize_math_answer(answer: str) -> str:
    """Normalize a math answer for comparison."""
    a = answer.strip()
    # Remove surrounding $ signs
    a = a.strip("$")
    # Remove \text{} wrapping
    a = re.sub(r"\\text\{(.+?)\}", r"\1", a)
    # Remove spaces
    a = a.replace(" ", "")
    # Normalize fractions: \frac{a}{b} -> a/b
    a = re.sub(r"\\frac\{(.+?)\}\{(.+?)\}", r"\1/\2", a)
    return a


def score_math(problem: dict, model_output: str) -> bool:
    """Score MATH: extract \\boxed{} answer, compare to ground truth."""
    expected = normalize_math_answer(problem["answer"])
    predicted_raw = extract_boxed_answer(model_output)

    if not predicted_raw:
        # Fallback: try to find the last number or expression
        numbers = re.findall(r"-?\d+(?:\.\d+)?", model_output)
        predicted_raw = numbers[-1] if numbers else ""

    predicted = normalize_math_answer(predicted_raw)

    # Exact string match after normalization
    if predicted == expected:
        return True

    # Try numeric comparison
    try:
        return abs(float(predicted) - float(expected)) < 0.01
    except (ValueError, TypeError):
        return False


def score_mmlu(problem: dict, model_output: str) -> bool:
    """Score MMLU: extract letter choice, compare to ground truth."""
    expected_idx = problem["answer"]  # 0-3
    expected_letter = "ABCD"[expected_idx]

    output_clean = model_output.strip()

    # Check last line first
    last_line = output_clean.split("\n")[-1].strip()
    match = re.search(r"\b([A-D])\b", last_line)
    if match:
        return match.group(1) == expected_letter

    # Check for "Answer: X" pattern
    match = re.search(r"(?:answer|correct|choose|select)[:\s]*\(?([A-D])\)?",
                      output_clean, re.IGNORECASE)
    if match:
        return match.group(1).upper() == expected_letter

    # Last resort: find any A-D in the response
    letters = re.findall(r"\b([A-D])\b", output_clean)
    if letters:
        return letters[-1] == expected_letter

    return False


SCORERS = {
    "humaneval": score_humaneval,
    "math": score_math,
    "mmlu": score_mmlu,
}


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: BENCHMARK FORMATTING
# ═══════════════════════════════════════════════════════════════════

def format_benchmark_question(benchmark: str, problem: dict) -> str:
    """Format a benchmark problem as a user message."""
    if benchmark == "humaneval":
        return (
            f"Complete the following Python function. Return ONLY the function body "
            f"code (no signature, no docstring, no markdown code blocks). "
            f"Output raw Python code only, nothing else.\n\n{problem['prompt']}"
        )
    elif benchmark == "math":
        return (
            f"Solve this math problem. Show your work step by step. "
            f"Put your final answer in \\boxed{{}} notation.\n\n"
            f"{problem['problem']}"
        )
    elif benchmark == "mmlu":
        choices = problem["choices"]
        options = "\n".join(f"  {chr(65+i)}. {c}" for i, c in enumerate(choices))
        return (
            f"Answer this multiple choice question. State ONLY your final "
            f"answer letter (A, B, C, or D) on the last line.\n\n"
            f"Question: {problem['question']}\n{options}"
        )
    return ""


# ═══════════════════════════════════════════════════════════════════
# SECTION 7: MAIN BENCHMARK RUNNER
# ═══════════════════════════════════════════════════════════════════

CONDITIONS = ["bare", "simple", "prompttriage", "expert_cot"]
BENCHMARKS = ["humaneval", "math", "mmlu"]


def run_benchmark_slice(
    provider_key: str, benchmark: str, condition: str, output_dir: Path
):
    """Run one slice: model × benchmark × condition."""
    provider = PROVIDERS[provider_key]()
    model_name = provider.name
    scorer = SCORERS[benchmark]
    system_prompt = get_system_prompt(condition, benchmark)

    result_file = output_dir / f"study_d_{model_name}_{benchmark}_{condition}.json"

    # Load existing results for resume
    existing = []
    if result_file.exists():
        existing = json.load(open(result_file))

    done_ids = {r.get("problem_idx") for r in existing}

    # Load benchmark data
    data_dir = output_dir / "benchmark_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    problems = load_benchmark_data(benchmark, data_dir)

    to_run = [(i, p) for i, p in enumerate(problems) if i not in done_ids]
    if not to_run:
        correct = sum(1 for r in existing if r.get("correct"))
        print(f"  ✅ Already complete: {model_name}/{benchmark}/{condition} "
              f"({correct}/{len(existing)} correct)")
        return existing

    print(f"\n{'='*60}")
    print(f"  {model_name} | {benchmark} | {condition}")
    print(f"  System prompt: {'None' if not system_prompt else f'{len(system_prompt)} chars'}")
    print(f"  Problems: {len(to_run)} remaining of {len(problems)}")
    print(f"{'='*60}")

    results = list(existing)

    for idx, problem in to_run:
        user_msg = format_benchmark_question(benchmark, problem)
        label = problem.get("task_id", problem.get("question", "")[:40])
        print(f"  [{idx+1}/{len(problems)}] {label}...", end="", flush=True)

        start = time.time()
        try:
            output = provider.generate(user_msg, system_prompt)
            latency = time.time() - start

            # Strip thinking tags if present
            if "<think>" in output:
                output = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()

            correct = scorer(problem, output)
            print(f" {'✓' if correct else '✗'} ({latency:.1f}s)")

            results.append({
                "model": model_name,
                "benchmark": benchmark,
                "condition": condition,
                "problem_idx": idx,
                "correct": correct,
                "output": output[:2000],  # Truncate for storage
                "latency_s": round(latency, 2),
            })
        except Exception as e:
            latency = time.time() - start
            print(f" ERROR: {e} ({latency:.1f}s)")
            results.append({
                "model": model_name,
                "benchmark": benchmark,
                "condition": condition,
                "problem_idx": idx,
                "correct": False,
                "output": f"[ERROR: {str(e)[:200]}]",
                "latency_s": round(latency, 2),
            })

        # Save after every problem
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    correct_count = sum(1 for r in results if r.get("correct"))
    total = len(results)
    pct = correct_count / total * 100 if total else 0
    print(f"\n  Result: {correct_count}/{total} ({pct:.1f}%)")
    return results


def print_summary(output_dir: Path):
    """Print a summary table of all results."""
    print("\n" + "="*80)
    print("STUDY D: PROMPT DELTA — RESULTS SUMMARY")
    print("="*80)

    # Collect all result files
    all_results = {}
    for f in output_dir.glob("study_d_*.json"):
        if "prompttriage_generated" in f.name or "benchmark_data" in str(f):
            continue
        data = json.load(open(f))
        if not data:
            continue
        key = (data[0]["model"], data[0]["benchmark"], data[0]["condition"])
        correct = sum(1 for r in data if r.get("correct"))
        total = len(data)
        all_results[key] = (correct, total)

    if not all_results:
        print("No results found yet.")
        return

    # Print table
    header = f"{'Model':<22} {'Benchmark':<12} {'Condition':<14} {'Score':>10}"
    print(header)
    print("-" * len(header))

    for (model, bench, cond), (correct, total) in sorted(all_results.items()):
        pct = correct / total * 100 if total else 0
        print(f"{model:<22} {bench:<12} {cond:<14} {correct}/{total} ({pct:.1f}%)")

    # Print delta analysis
    print("\n--- PROMPT DELTA (PromptTriage vs Bare) ---")
    for model in set(k[0] for k in all_results):
        for bench in BENCHMARKS:
            bare = all_results.get((model, bench, "bare"))
            pt = all_results.get((model, bench, "prompttriage"))
            if bare and pt:
                bare_pct = bare[0] / bare[1] * 100
                pt_pct = pt[0] / pt[1] * 100
                delta = pt_pct - bare_pct
                print(f"  {model} / {bench}: {delta:+.1f}pp "
                      f"({bare_pct:.1f}% → {pt_pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Study D: Prompt Delta Benchmark")
    parser.add_argument("--model", choices=list(PROVIDERS.keys()) + ["all"],
                        default="all")
    parser.add_argument("--benchmark", choices=BENCHMARKS + ["all"], default="all")
    parser.add_argument("--condition", choices=CONDITIONS + ["all"], default="all")
    parser.add_argument("--generate-prompts", action="store_true",
                        help="Only generate PromptTriage prompts, don't run benchmarks")
    parser.add_argument("--summary", action="store_true",
                        help="Print summary of existing results")
    args = parser.parse_args()

    output_dir = Path("named-outputs/study_d")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.summary:
        print_summary(output_dir)
        return

    # Step 1: Generate PromptTriage prompts if needed
    conditions = CONDITIONS if args.condition == "all" else [args.condition]
    if "prompttriage" in conditions:
        generate_all_pt_prompts(output_dir)

    if args.generate_prompts:
        return

    # Step 2: Run benchmarks
    models = list(PROVIDERS.keys()) if args.model == "all" else [args.model]
    benchmarks = BENCHMARKS if args.benchmark == "all" else [args.benchmark]

    total_slices = len(models) * len(benchmarks) * len(conditions)
    current = 0

    for model_key in models:
        for bench in benchmarks:
            for cond in conditions:
                current += 1
                print(f"\n[{current}/{total_slices}] Running {model_key}/{bench}/{cond}")
                try:
                    run_benchmark_slice(model_key, bench, cond, output_dir)
                except Exception as e:
                    print(f"  ❌ FAILED: {e}")
                    import traceback
                    traceback.print_exc()

    # Step 3: Print summary
    print_summary(output_dir)
    print("\nDone! Results saved to:", output_dir)


if __name__ == "__main__":
    main()
