"""
Score benchmark outputs locally using Gemini 3.1 Pro via LLMJudge.
"""
import json
import os
import sys
from pathlib import Path
from dataclasses import asdict

# Add project root to path so we can import backend correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Load the backend .env for GOOGLE_API_KEY
from dotenv import load_dotenv
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
load_dotenv(os.path.join(project_root, 'backend', '.env'))

from backend.research.llm_judge import LLMJudge, aggregate_scores, format_summary_table, BenchmarkResult, JudgeScore

def main():
    input_file = Path("named-outputs/benchmark_output/benchmark_outputs.json")
    output_file = Path("named-outputs/benchmark_output/judged_outputs.json")
    
    if not input_file.exists():
        print(f"Error: Could not find {input_file}")
        return
        
    print(f"Loading results from {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    print(f"Loaded {len(results)} results to judge.")
    
    judge = LLMJudge()
    
    # Check if we already have some judged results to resume
    judged_results = []
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            judged_results = json.load(f)
            print(f"Found {len(judged_results)} already judged results. Resuming...")
            
    # Keep track of IDs we already judged
    judged_ids = {r["prompt_id"] + r.get("model", r.get("method", "")) for r in judged_results}
    
    # Filter results that need judging
    to_judge = [r for r in results if r["prompt_id"] + r.get("model", r.get("method", "")) not in judged_ids]
    
    print(f"Need to judge {len(to_judge)} results.")
    
    for i, res in enumerate(to_judge):
        method_name = res.get("model", res.get("method", "unknown"))
        print(f"Judging {i+1}/{len(to_judge)}: {method_name} - {res.get('prompt_id', '?')}")
        score = judge.score(
            generated_prompt=res["generated_prompt"],
            target_vendor=res["target_vendor"],
            target_model="Claude 3.5 Sonnet" if res["target_vendor"] == "anthropic" else "GPT-4o",
            user_prompt=res["user_prompt"],
            context=res.get("context", "")
        )
        
        # Merge score into result
        res["score"] = asdict(score) if hasattr(score, "__dataclass_fields__") else score.__dict__
        judged_results.append(res)
        
        # Save after every judgement to prevent loss
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(judged_results, f, indent=2)
            
    print("\n" + "="*60)
    print("ALL JUDGING COMPLETE")
    print("="*60)
    
    show_summary()

def show_summary():
    output_file = Path("named-outputs/benchmark_output/judged_outputs.json")
    if not output_file.exists():
        print("No judged outputs found.")
        return
        
    with open(output_file, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    # Convert dicts back to objects for aggregate_scores
    objects = []
    for r in results:
        try:
            score_dict = r.get("score")
            if not score_dict:
                continue
            
            score_obj = JudgeScore(**score_dict)
            
            # Create BenchmarkResult
            r_obj = BenchmarkResult(
                prompt_id=r.get("prompt_id", "unknown"),
                method=r.get("model", r.get("method", "unknown")),
                target_vendor=r.get("target_vendor", "unknown"),
                category=r.get("category", "unknown"),
                generated_prompt=r.get("generated_prompt", ""),
                score=score_obj,
                latency_ms=r.get("latency_ms", 0),
                cost_usd=r.get("cost_usd", 0.0),
                metadata=r.get("metadata", {})
            )
            objects.append(r_obj)
        except Exception as e:
            print(f"Error parsing result: {e}")
            
    summary = aggregate_scores(objects)
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(format_summary_table(summary))
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        show_summary()
    else:
        main()
