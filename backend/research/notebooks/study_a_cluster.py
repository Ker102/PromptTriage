#!/usr/bin/env python3
"""
Study A — Stage 2: Generate system prompts from fine-tuned Qwen 14B on Azure ML A100.

Reads the pre-computed RAG contexts (rag_contexts.json) and generates a system
prompt for each (prompt × RAG level) using the fine-tuned adapter.

Runs on Azure ML GPU cluster. Submitted via submit_job.py --study-a.

Env vars (set by submit_job.py):
    ADAPTER_PATH  — Path to the Qwen 14B adapter dir
    RAG_DATA      — Path to rag_contexts.json  
    OUTPUT_DIR    — Where to write outputs
"""
import json
import os
import re
import sys
import time
import torch
from pathlib import Path


def log(msg: str):
    print(msg, flush=True)


# Config
ADAPTER_PATH = Path(os.environ.get("ADAPTER_PATH", "/mnt/adapters/qwen3_14b"))
RAG_DATA = Path(os.environ.get("RAG_DATA", "rag_contexts.json"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./study_a_output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_NEW_TOKENS = 16384
TEMPERATURE = 0.7


def load_model(adapter_path: str):
    """Load the fine-tuned Qwen 14B with its adapter."""
    from unsloth import FastLanguageModel

    log(f"Loading model from adapter: {adapter_path}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_path,
        max_seq_length=32768,
        dtype=None,
        load_in_4bit=True,
        fast_inference=False,
    )
    FastLanguageModel.for_inference(model)
    log("Model loaded successfully.")
    return model, tokenizer


def generate(model, tokenizer, user_msg: str) -> tuple[str, int]:
    """Generate a system prompt from the user message."""
    messages = [{"role": "user", "content": user_msg}]
    input_ids = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt",
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

    new_tokens = output_ids[0][input_ids.shape[1]:]
    output_text = tokenizer.decode(new_tokens, skip_special_tokens=True)

    # Strip <think>...</think> blocks if present
    if "<think>" in output_text and "</think>" in output_text:
        output_text = re.sub(r"<think>.*?</think>", "", output_text, flags=re.DOTALL).strip()

    return output_text, latency_ms


def main():
    log(f"PyTorch: {torch.__version__}")
    log(f"CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        log(f"GPU: {torch.cuda.get_device_name(0)}")
        gpu_props = torch.cuda.get_device_properties(0)
        log(f"VRAM: {gpu_props.total_memory / 1e9:.1f} GB")

    # Find the RAG data file
    rag_file = RAG_DATA
    if not rag_file.exists():
        # Check if it's nested inside an Azure ML input folder
        candidates = list(Path("/mnt").rglob("rag_contexts.json"))
        if candidates:
            rag_file = candidates[0]
        else:
            log(f"❌ RAG data not found: {RAG_DATA}")
            sys.exit(1)

    log(f"RAG data: {rag_file}")
    rag_entries = json.loads(rag_file.read_text(encoding="utf-8"))
    log(f"  {len(rag_entries)} entries to generate")

    # Find adapter path
    adapter_path = str(ADAPTER_PATH)
    if not Path(adapter_path).exists():
        log(f"  Adapter not at {adapter_path}, searching...")
        candidates = [
            ADAPTER_PATH,
            ADAPTER_PATH / "adapter",
            Path("/mnt/adapters/qwen3_14b"),
        ]
        for c in candidates:
            if c.exists() and (c / "adapter_config.json").exists():
                adapter_path = str(c)
                break
        else:
            log(f"❌ No adapter_config.json found!")
            for c in candidates:
                log(f"  Checked: {c} (exists={c.exists()})")
            sys.exit(1)

    model, tokenizer = load_model(adapter_path)

    # Output file
    output_file = OUTPUT_DIR / "study_a_outputs.json"

    # Resume support
    existing = []
    done_keys = set()
    if output_file.exists():
        existing = json.loads(output_file.read_text(encoding="utf-8"))
        done_keys = {(r["prompt_id"], r["rag_level"]) for r in existing}
        log(f"  Resuming: {len(existing)} already done")

    results = list(existing)

    for i, entry in enumerate(rag_entries, 1):
        key = (entry["prompt_id"], entry["rag_level"])
        if key in done_keys:
            continue

        log(f"  [{i}/{len(rag_entries)}] {entry['prompt_id']} / {entry['rag_level']}...")

        try:
            output_text, latency_ms = generate(model, tokenizer, entry["full_user_message"])
            log(f"    -> {len(output_text)} chars, {latency_ms}ms")
        except Exception as e:
            log(f"    !! ERROR: {e}")
            output_text = f"[GENERATION FAILED: {e}]"
            latency_ms = 0

        results.append({
            "prompt_id": entry["prompt_id"],
            "category": entry["category"],
            "vendor": entry["vendor"],
            "target_model": entry["target_model"],
            "user_prompt": entry["user_prompt"],
            "rag_level": entry["rag_level"],
            "rag_context_chars": entry["rag_context_chars"],
            "rag_num_docs": entry["rag_num_docs"],
            "generated_prompt": output_text,
            "char_count": len(output_text),
            "latency_ms": latency_ms,
        })

        # Save after each generation
        output_file.write_text(json.dumps(results, indent=2, ensure_ascii=True), encoding="utf-8")

    log(f"\n✅ Generated {len(results)} outputs -> {output_file}")

    # Summary by RAG level
    log(f"\n{'='*60}")
    log("STUDY A GENERATION SUMMARY")
    log(f"{'='*60}")
    for level in ["L0_no_rag", "L1_naive_rag", "L2_rerank_rag", "L3_corrective_rag", "L4_judge_rag", "L5_agentic_rag"]:
        level_results = [r for r in results if r["rag_level"] == level]
        if level_results:
            avg_chars = sum(r["char_count"] for r in level_results) / len(level_results)
            avg_latency = sum(r["latency_ms"] for r in level_results) / len(level_results)
            log(f"  {level:<25} {len(level_results):>3} outputs, avg {avg_chars:>6.0f} chars, {avg_latency:>6.0f}ms")

    # Cleanup GPU
    del model, tokenizer
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
