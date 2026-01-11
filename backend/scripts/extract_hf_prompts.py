#!/usr/bin/env python3
"""
HuggingFace Prompt Extractor

Extracts only the prompt column from HuggingFace datasets
without downloading images or other large binary data.

Usage:
    py scripts/extract_hf_prompts.py [--dataset NAME] [--output FILE]
"""

import argparse
import json
from pathlib import Path

# Use streaming to avoid downloading full dataset
from datasets import load_dataset

# Dataset configurations
DATASETS = {
    "open-image-preferences": {
        "name": "data-is-better-together/open-image-preferences-v1-binarized",
        "prompt_column": "prompt",
        "split": "train",
        "description": "High-quality text-to-image prompts with preference annotations",
    },
    "imgsys-results": {
        "name": "fal/imgsys-results",
        "prompt_column": "prompt",
        "split": "train",
        "description": "Image generation prompts evolved by complexity",
    },
}


def extract_prompts(dataset_key: str, output_path: Path, limit: int = 0) -> int:
    """
    Stream dataset and extract only prompts to a JSON file.
    
    Args:
        dataset_key: Key from DATASETS config
        output_path: Path to save extracted prompts
        limit: Max prompts to extract (0 = all)
        
    Returns:
        Number of prompts extracted
    """
    config = DATASETS[dataset_key]
    
    print(f"Streaming dataset: {config['name']}")
    print(f"Split: {config['split']}")
    print(f"Prompt column: {config['prompt_column']}")
    print()
    
    # Stream the dataset (doesn't download images)
    dataset = load_dataset(
        config["name"],
        split=config["split"],
        streaming=True,
    )
    
    prompts = []
    seen = set()  # Deduplicate
    
    for i, row in enumerate(dataset):
        prompt = row.get(config["prompt_column"], "")
        
        if not prompt or prompt in seen:
            continue
        
        seen.add(prompt)
        prompts.append({
            "content": prompt,
            "metadata": {
                "source": dataset_key,
                "dataset": config["name"],
            }
        })
        
        if (i + 1) % 500 == 0:
            print(f"  Processed {i + 1} rows, extracted {len(prompts)} unique prompts")
        
        if limit > 0 and len(prompts) >= limit:
            break
    
    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    print(f"\nExtracted {len(prompts)} unique prompts to {output_path}")
    return len(prompts)


def main():
    parser = argparse.ArgumentParser(description="Extract prompts from HuggingFace datasets")
    parser.add_argument(
        "--dataset",
        choices=list(DATASETS.keys()),
        default="open-image-preferences",
        help="Dataset to extract from",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max prompts to extract (0 = all)",
    )
    args = parser.parse_args()
    
    # Default output path
    if args.output is None:
        args.output = Path(f"datasets/{args.dataset}_prompts.json")
    
    extract_prompts(args.dataset, args.output, args.limit)
    
    print("\nTo ingest these prompts to Pinecone, run:")
    print(f"  py scripts/ingest_json_prompts.py --input {args.output}")


if __name__ == "__main__":
    main()
