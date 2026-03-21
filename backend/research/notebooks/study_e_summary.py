#!/usr/bin/env python3
"""
Study E — Summary Analyzer

Parses the JSON results from study_e_run.py and generates
analytical tables to prove/disprove the format and length hypotheses.
"""
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "named-outputs" / "study_e"
RESULTS_FILE = OUTPUT_DIR / "study_e_results.json"

def main():
    if not RESULTS_FILE.exists():
        print(f"No results found at {RESULTS_FILE}")
        return
        
    results = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    
    # Filter out failures
    valid = [r for r in results if r.get("total_score", 0) > 0]
    failed = len(results) - len(valid)
    
    print(f"=== STUDY E RESULTS SUMMARY ===")
    print(f"Total Evaluations: {len(results)}")
    print(f"Valid Scores:      {len(valid)}")
    print(f"Failed Generations:{failed}")
    
    if not valid:
        return
        
    models = sorted(list(set(r["model"] for r in valid)))
    lengths = ["short", "medium", "long"]
    formats = ["text", "markdown", "xml", "json", "yaml", "hybrid"]
    
    # --- 1. Average by Format ---
    print("\n\n--- 1. IMPACT OF FORMAT (Averaged across Lengths & Models) ---")
    print(f"{'Format':<15} | {'Avg Score (/40)':<15} | {'N':<5}")
    print("-" * 40)
    for f in formats:
        subset = [r for r in valid if r["format"] == f]
        if subset:
            avg = sum(r["total_score"] for r in subset) / len(subset)
            print(f"{f:<15} | {avg:<15.2f} | {len(subset):<5}")
            
    # --- 2. Average by Length ---
    print("\n\n--- 2. IMPACT OF LENGTH (Averaged across Formats & Models) ---")
    print(f"{'Length':<15} | {'Avg Score (/40)':<15} | {'Avg Words':<10} | {'N':<5}")
    print("-" * 50)
    for l in lengths:
        subset = [r for r in valid if r["length"] == l]
        if subset:
            avg = sum(r["total_score"] for r in subset) / len(subset)
            avg_words = sum(r["word_count"] for r in subset) / len(subset)
            print(f"{l:<15} | {avg:<15.2f} | {avg_words:<10.0f} | {len(subset):<5}")
            
    # --- 3. Model x Format Matrix ---
    print("\n\n--- 3. MODEL PREFERENCES (Format scores per Model) ---")
    header = f"{'Model':<18} | " + " | ".join(f"{f:<8}" for f in formats)
    print(header)
    print("-" * len(header))
    for m in models:
        row = f"{m:<18} | "
        for f in formats:
            subset = [r for r in valid if r["model"] == m and r["format"] == f]
            if subset:
                avg = sum(r["total_score"] for r in subset) / len(subset)
                row += f"{avg:<8.1f} | "
            else:
                row += f"{'--':<8} | "
        print(row)
        
    # --- 4. Deep Dive: Format Adherence ---
    print("\n\n--- 4. FORMAT ADHERENCE DIMENSION ONLY (/10) ---")
    print("Does the XML system prompt make them format their *output* better?")
    header = f"{'Model':<18} | " + " | ".join(f"{f:<8}" for f in formats)
    print(header)
    print("-" * len(header))
    for m in models:
        row = f"{m:<18} | "
        for f in formats:
            subset = [r for r in valid if r["model"] == m and r["format"] == f]
            if subset:
                avg = sum(r["scores"].get("format_adherence", 0) for r in subset) / len(subset)
                row += f"{avg:<8.1f} | "
            else:
                row += f"{'--':<8} | "
        print(row)
        
    print("\n\nNOTE: Cross-Model Judging Used:")
    print("  - Qwen/Llama/Claude evaluated by Gemini 3.1 Pro")
    print("  - Gemini evaluated by Qwen 3.5 397B")

if __name__ == "__main__":
    main()
